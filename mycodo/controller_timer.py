#!/usr/bin/python
# coding=utf-8
#
# controller_timer.py - Timer controller to turn relays on or off
#                       at predefined intervals or at specific times
#                       of the day.
#

import datetime
import logging
import threading
import time
import timeit

from config import SQL_DATABASE_MYCODO
from databases.mycodo_db.models import Timer
from databases.utils import session_scope
from mycodo_client import DaemonControl

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
            self.name = timer.name
            self.relay_id = timer.relay_id
            self.state = timer.state
            self.time = timer.time_on
            self.duration_on = timer.duration_on
            self.duration_off = timer.duration_off

        # Time of day split into hour and minute
        if self.time:
            time_split = self.time.split(":")
            self.hour = time_split[0]
            self.minute = time_split[1]
        else:
            self.hour = None
            self.minute = None

        self.duration_timer = time.time()
        self.date_timer_not_executed = True
        self.running = False


    def run(self):
        self.running = True
        self.logger.info("[Timer {}] Activated in {}ms".format(
            self.timer_id,
            (timeit.default_timer()-self.thread_startup_timer)*1000))
        self.ready.set()
        while (self.running):
            # Timer is a simple on/off duration timer
            if self.duration_on and self.duration_off:
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
            # Timer is set to react at a specific hour and minute of the day
            else:
                if (int(self.hour) == datetime.datetime.now().hour and
                        int(self.minute) == datetime.datetime.now().minute):
                    # Ensure this is triggered only once at this specific time
                    if self.date_timer_not_executed:
                        message = "[Timer {}] At {}, turn relay {} {}".format(
                                self.timer_id,
                                self.time,
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
            time.sleep(1)

        self.control.relay_off(self.relay_id)
        self.running = False
        self.logger.info("[Timer {}] Deactivated in {}ms".format(
            self.timer_id,
            (timeit.default_timer()-self.thread_shutdown_timer)*1000))


    def isRunning(self):
        return self.running


    def stopController(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
