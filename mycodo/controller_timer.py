# coding=utf-8
#
# controller_timer.py - Timer controller to turn relays on or off
#                       at predefined intervals or at specific times
#                       of the day.
#
#  Copyright (C) 2017  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

import datetime
import logging
import threading
import time
import timeit

from mycodo_client import DaemonControl
from databases.models import Method
from databases.models import MethodData
from databases.models import Output
from databases.models import Timer
from databases.utils import session_scope
from utils.database import db_retrieve_table_daemon
from utils.method import calculate_method_setpoint
from utils.system_pi import time_between_range

from config import SQL_DATABASE_MYCODO

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class TimerController(threading.Thread):
    """
    class for controlling timers

    """
    def __init__(self, ready, timer_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger(
            "mycodo.timer_{id}".format(id=timer_id))

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.timer_id = timer_id
        self.control = DaemonControl()

        timer = db_retrieve_table_daemon(Timer, device_id=self.timer_id)
        self.timer_type = timer.timer_type
        self.relay_unique_id = timer.relay_id
        self.method_id = timer.method_id
        self.method_period = timer.method_period
        self.state = timer.state
        self.time_start = timer.time_start
        self.time_end = timer.time_end
        self.duration_on = timer.duration_on
        self.duration_off = timer.duration_off

        self.relay_id = db_retrieve_table_daemon(
            Relay, unique_id=self.relay_unique_id).id

        # Time of day split into hour and minute
        if self.time_start:
            time_split = self.time_start.split(":")
            self.start_hour = time_split[0]
            self.start_minute = time_split[1]
        else:
            self.start_hour = None
            self.start_minute = None

        if self.time_end:
            time_split = self.time_end.split(":")
            self.end_hour = time_split[0]
            self.end_minute = time_split[1]
        else:
            self.end_hour = None
            self.end_minute = None

        self.duration_timer = time.time()
        self.pwm_method_timer = time.time()
        self.date_timer_not_executed = True
        self.running = False

        if self.method_id:
            method = db_retrieve_table_daemon(Method, device_id=self.method_id)
            method_data = db_retrieve_table_daemon(MethodData)
            method_data = method_data.filter(MethodData.method_id == self.method_id)
            method_data_repeat = method_data.filter(MethodData.duration_sec == 0).first()
            self.method_type = method.method_type
            self.method_start_act = timer.method_start_time
            self.method_start_time = None
            self.method_end_time = None

            if self.method_type == 'Duration':
                if self.method_start_act == 'Ended':
                    self.stop_controller(ended_normally=False,
                                         deactivate_timer=True)
                    self.logger.warning(
                        "Method has ended. "
                        "Activate the Timer controller to start it again.")
                elif self.method_start_act == 'Ready' or self.method_start_act is None:
                    # Method has been instructed to begin
                    now = datetime.datetime.now()
                    self.method_start_time = now
                    if method_data_repeat and method_data_repeat.duration_end:
                        self.method_end_time = now + datetime.timedelta(
                            seconds=float(method_data_repeat.duration_end))

                    with session_scope(MYCODO_DB_PATH) as db_session:
                        mod_timer = db_session.query(Timer)
                        mod_timer = mod_timer.filter(Timer.id == self.timer_id).first()
                        mod_timer.method_start_time = self.method_start_time
                        mod_timer.method_end_time = self.method_end_time
                        db_session.commit()
            else:
                # Method neither instructed to begin or not to
                # Likely there was a daemon restart ot power failure
                # Resume method with saved start_time
                self.method_start_time = datetime.datetime.strptime(
                    str(timer.method_start_time), '%Y-%m-%d %H:%M:%S.%f')
                if method_data_repeat and method_data_repeat.duration_end:
                    self.method_end_time = datetime.datetime.strptime(
                        str(timer.method_end_time), '%Y-%m-%d %H:%M:%S.%f')
                    if self.method_end_time > datetime.datetime.now():
                        self.logger.warning(
                            "Resuming method {id}: started {start}, "
                            "ends {end}".format(
                                id=self.method_id,
                                start=self.method_start_time,
                                end=self.method_end_time))
                    else:
                        self.method_start_act = 'Ended'
                else:
                    self.method_start_act = 'Ended'

    def run(self):
        self.running = True
        self.logger.info("Activated in {:.1f} ms".format(
            (timeit.default_timer() - self.thread_startup_timer) * 1000))
        self.ready.set()

        while self.running:

            # Timer is set to react at a specific hour and minute of the day
            if self.timer_type == 'time':
                if (int(self.start_hour) == datetime.datetime.now().hour and
                        int(self.start_minute) == datetime.datetime.now().minute):
                    # Ensure this is triggered only once at this specific time
                    if self.date_timer_not_executed:
                        message = "At {st}, turn Output {id} {state}".format(
                            st=self.time_start,
                            id=self.relay_id,
                            state=self.state)
                        if self.state == 'on' and self.duration_on:
                            message += " for {sec} seconds".format(
                                sec=self.duration_on)
                        else:
                            self.duration_on = 0
                        self.logger.debug(message)
                        modulate_relay = threading.Thread(
                            target=self.control.relay_on_off,
                            args=(self.relay_id,
                                  self.state,),
                            kwargs={'duration': self.duration_on})
                        modulate_relay.start()
                        self.date_timer_not_executed = False
                elif not self.date_timer_not_executed:
                    self.date_timer_not_executed = True

            # Timer is set to react at a specific time duration of the day
            elif self.timer_type == 'timespan':
                if time_between_range(self.time_start, self.time_end):
                    current_relay_state = self.control.relay_state(self.relay_id)
                    if self.state != current_relay_state:
                        message = "Output {output} should be {state}, but is " \
                                  "{cstate}. Turning {state}.".format(
                                    output=self.relay_id,
                                    state=self.state,
                                    cstate=current_relay_state)
                        modulate_relay = threading.Thread(
                            target=self.control.relay_on_off,
                            args=(self.relay_id,
                                  self.state,))
                        modulate_relay.start()
                        self.logger.debug(message)

            # Timer is a simple on/off duration timer
            elif self.timer_type == 'duration':
                if time.time() > self.duration_timer:
                    self.duration_timer = (time.time() +
                                           self.duration_on +
                                           self.duration_off)
                    self.logger.debug("Turn Output {output} on for {onsec} "
                                      "seconds, then off for {offsec} "
                                      "seconds".format(
                                        output=self.relay_id,
                                        onsec=self.duration_on,
                                        offsec=self.duration_off))
                    relay_on = threading.Thread(target=self.control.relay_on,
                                                args=(self.relay_id,
                                                      self.duration_on,))
                    relay_on.start()

            # Timer is a PWM Method timer
            elif self.timer_type == 'pwm_method':
                try:
                    if time.time() > self.pwm_method_timer:
                        if self.method_start_act == 'Ended':
                            self.stop_controller(ended_normally=False, deactivate_timer=True)
                            self.logger.info(
                                "Method has ended. "
                                "Activate the Timer controller to start it again.")
                        else:
                            this_controller = db_retrieve_table_daemon(
                                Timer, device_id=self.timer_id)
                            setpoint, ended = calculate_method_setpoint(
                                self.method_id,
                                Timer,
                                this_controller,
                                Method,
                                MethodData,
                                self.logger)
                            if ended:
                                self.method_start_act = 'Ended'
                            if setpoint > 100:
                                setpoint = 100
                            elif setpoint < 0:
                                setpoint = 0
                            self.logger.debug(
                                "Turn Output {output} to a PWM duty cycle of "
                                "{dc:.1f} %".format(
                                    output=self.relay_id,
                                    dc=setpoint))
                            # Activate pwm with calculated duty cycle
                            self.control.relay_on(
                                self.relay_id,
                                duty_cycle=setpoint)
                        self.pwm_method_timer = time.time() + self.method_period
                except Exception:
                    self.logger.exception(1)

            time.sleep(0.1)

        self.control.relay_off(self.relay_id)
        self.running = False
        self.logger.info("Deactivated in {:.1f} ms".format(
            (timeit.default_timer() - self.thread_shutdown_timer) * 1000))

    def is_running(self):
        return self.running

    def stop_controller(self, ended_normally=True, deactivate_timer=False):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
        # Unset method start time
        if self.method_id and ended_normally:
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_timer = db_session.query(Timer).filter(
                    Timer.id == self.timer_id).first()
                mod_timer.method_start_time = 'Ended'
                mod_timer.method_end_time = None
                db_session.commit()

        if deactivate_timer:
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_timer = db_session.query(Timer).filter(
                    Timer.id == self.timer_id).first()
                mod_timer.is_activated = False
                db_session.commit()