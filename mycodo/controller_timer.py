#!/usr/bin/python
# coding=utf-8
#
# controller_timer.py - Timer controller to turn relays on or off
#                       at predefined intervals or at specific times
#                       of the day.
#

import datetime
import threading
import time
import timeit

from config import SQL_DATABASE_MYCODO
from databases.mycodo_db.models import Timer
from databases.utils import session_scope
from mycodo_client import DaemonControl
from utils.system_pi import time_between_range

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class TimerController(threading.Thread):
    """
    class for controlling timers

    """

    def __init__(self, ready, logger, timer_id):
        threading.Thread.__init__(self)

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.logger = logger
        self.timer_id = timer_id
        self.control = DaemonControl()

        with session_scope(MYCODO_DB_PATH) as new_session:
            timer = new_session.query(Timer).filter(
                Timer.id == self.timer_id).first()
            self.timer_type = timer.timer_type
            self.name = timer.name
            self.relay_id = timer.relay_id
            self.state = timer.state
            self.time_start = timer.time_start
            self.time_end = timer.time_end
            self.duration_on = timer.duration_on
            self.duration_off = timer.duration_off

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
        self.logger.info("[Timer {}] Activated in {:.1f} ms".format(
            self.timer_id,
            (timeit.default_timer()-self.thread_startup_timer)*1000))
        self.ready.set()
        while self.running:
            # Timer is set to react at a specific hour and minute of the day
            if self.timer_type == 'time':
                if (int(self.start_hour) == datetime.datetime.now().hour and    
                        int(self.start_minute) == datetime.datetime.now().minute):
                    # Ensure this is triggered only once at this specific time
                    if self.date_timer_not_executed:
                        message = "[Timer {}] At {}, turn relay {} {}".format(
                            self.timer_id,
                            self.time_start,
                            self.relay_id,
                            self.state)
                        if self.state == 'on' and self.duration_on:
                            message += " for {} seconds".format(
                                self.duration_on)
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
                        message = "[Timer {}] Relay {} should be {}, but is {}. Turning {}.".format(
                            self.timer_id,
                            self.relay_id,
                            self.state,
                            current_relay_state,
                            self.state)
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
                    self.duration_timer = time.time()+self.duration_on+self.duration_off
                    self.logger.debug("[Timer {}] Turn relay {} on "
                                      "for {} seconds, then off for "
                                      "{} seconds".format(self.timer_id,
                                                          self.relay_id,
                                                          self.duration_on,
                                                          self.duration_off))
                    relay_on = threading.Thread(target=self.control.relay_on,
                                                args=(self.relay_id,
                                                      self.duration_on,))
                    relay_on.start()

            time.sleep(0.1)

        self.control.relay_off(self.relay_id)
        self.running = False
        self.logger.info("[Timer {}] Deactivated in {:.1f} ms".format(
            self.timer_id,
            (timeit.default_timer()-self.thread_shutdown_timer)*1000))


    def isRunning(self):
        return self.running


    def stopController(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
