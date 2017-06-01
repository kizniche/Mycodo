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
from databases.models import Relay
from databases.models import Timer
from utils.database import db_retrieve_table_daemon
from utils.system_pi import time_between_range


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
        self.date_timer_not_executed = True
        self.running = False

    def run(self):
        self.running = True
        self.logger.info("Activated in {:.1f} ms".format(
            (timeit.default_timer() - self.thread_startup_timer)*1000))
        self.ready.set()
        while self.running:
            # Timer is set to react at a specific hour and minute of the day
            if self.timer_type == 'time':
                if (int(self.start_hour) == datetime.datetime.now().hour and
                        int(self.start_minute) == datetime.datetime.now().minute):
                    # Ensure this is triggered only once at this specific time
                    if self.date_timer_not_executed:
                        message = "At {st}, turn relay {id} {state}".format(
                            st=self.time_start,
                            id=self.relay_unique_id,
                            state=self.state)
                        if self.state == 'on' and self.duration_on:
                            message += " for {sec} seconds".format(
                                sec=self.duration_on)
                        self.logger.debug(message)
                        modulate_relay = threading.Thread(
                            target=self.control.relay_on_off,
                            args=(self.relay_id,
                                  self.state,
                                  self.duration_on,))
                        modulate_relay.start()
                        self.date_timer_not_executed = False
                elif not self.date_timer_not_executed:
                    self.date_timer_not_executed = True

            # Timer is set to react at a specific time duration of the day
            elif self.timer_type == 'timespan':
                if time_between_range(self.time_start, self.time_end):
                    current_relay_state = self.control.relay_state(self.relay_id)
                    if self.state != current_relay_state:
                        message = "Relay {relay} should be {state}, but is " \
                                  "{cstate}. Turning {state}.".format(
                                    relay=self.relay_unique_id,
                                    state=self.state,
                                    cstate=current_relay_state)
                        modulate_relay = threading.Thread(
                            target=self.control.relay_on_off,
                            args=(self.relay_id,
                                  self.state,
                                  0,))
                        modulate_relay.start()
                        self.logger.debug(message)

            # Timer is a simple on/off duration timer
            elif self.timer_type == 'duration':
                if time.time() > self.duration_timer:
                    self.duration_timer = (time.time() +
                                           self.duration_on +
                                           self.duration_off)
                    self.logger.debug("Turn relay {relay} on for {onsec} "
                                      "seconds, then off for {offsec} "
                                      "seconds".format(
                                        relay=self.relay_unique_id,
                                        onsec=self.duration_on,
                                        offsec=self.duration_off))
                    relay_on = threading.Thread(target=self.control.relay_on,
                                                args=(self.relay_id,
                                                      self.duration_on,))
                    relay_on.start()

            time.sleep(0.1)

        self.control.relay_off(self.relay_id)
        self.running = False
        self.logger.info("Deactivated in {:.1f} ms".format(
            (timeit.default_timer() - self.thread_shutdown_timer) * 1000))

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
