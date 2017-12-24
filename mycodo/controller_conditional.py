# coding=utf-8
#
# controller_conditional.py - Conditional controller that checks measurements
#                             and performs functions on at predefined
#                             intervals
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
#

import logging
import threading
import time
import timeit

from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import SMTP
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.conditional import check_conditionals
from mycodo.utils.database import db_retrieve_table_daemon


class ConditionalController(threading.Thread):
    """
    Class to operate discrete PID controller

    """
    def __init__(self):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.conditional")

        self.running = False
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.pause_loop = False
        self.verify_pause_loop = True
        self.control = DaemonControl()

        self.cond_is_activated = {}
        self.cond_period = {}
        self.cond_timer = {}

        self.smtp_max_count = db_retrieve_table_daemon(
            SMTP, entry='first').hourly_max
        self.email_count = 0
        self.allowed_to_send_notice = True
        self.smtp_wait_timer = {}

        self.setup_conditionals()

    def run(self):
        try:
            self.running = True
            self.logger.info("Conditional controller activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))

            while self.running:
                # Pause loop to modify conditional statements.
                # Prevents execution of conditional while variables are
                # being modified.
                if self.pause_loop:
                    self.verify_pause_loop = True
                    while self.pause_loop:
                        time.sleep(0.1)

                # Check each activated conditional if it's timer has elapsed
                for each_cond_id in self.cond_is_activated:
                    if (self.cond_is_activated[each_cond_id] and
                        self.cond_timer[each_cond_id] < time.time()):
                        while self.cond_timer[each_cond_id] < time.time():
                            self.cond_timer[each_cond_id] += self.cond_period[each_cond_id]

                        check_conditionals(
                            self, each_cond_id, self.control,
                            Camera, Conditional, ConditionalActions,
                            Input, Math, Output, PID, SMTP)

                time.sleep(0.1)

            self.running = False
            self.logger.info("Conditional controller deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
            self.logger.exception("Run Error: {err}".format(
                err=except_msg))

    def setup_conditionals(self):
        # Signal to pause the main loop and wait for verification
        self.pause_loop = True
        while not self.verify_pause_loop:
            time.sleep(0.1)

        self.cond_is_activated = {}
        self.cond_period = {}
        self.cond_timer = {}
        self.smtp_wait_timer = {}

        # Only check 'measurement' conditionals
        # 'output' conditionals are checked in the Output Controller
        conditional = db_retrieve_table_daemon(
            Conditional).filter(
            Conditional.conditional_type == 'conditional_measurement').all()

        for each_cond in conditional:
            self.cond_is_activated[each_cond.id] = each_cond.is_activated
            self.cond_period[each_cond.id] = each_cond.if_sensor_period
            self.cond_timer[each_cond.id] = time.time() + self.cond_period[each_cond.id]
            self.smtp_wait_timer[each_cond.id] = time.time() + 3600

        self.logger.info("Conditional settings refreshed")

        self.pause_loop = False
        self.verify_pause_loop = False

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
