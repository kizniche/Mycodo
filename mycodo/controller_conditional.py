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
from statistics import median

import urllib3

import mycodo.utils.psypy as SI
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import PID
from mycodo.databases.models import SMTP
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.conditional import check_conditionals
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measure_influxdb
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import celsius_to_kelvin



class ConditionalController(threading.Thread):
    """
    Class to operate discrete PID controller

    """
    def __init__(self, ready, math_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.conditional_{id}".format(id=math_id))

        try:
            self.measurements = None
            self.running = False
            self.thread_startup_timer = timeit.default_timer()
            self.thread_shutdown_timer = 0
            self.ready = ready
            self.pause_loop = False
            self.verify_pause_loop = True
            self.control = DaemonControl()

            self.cond_id = {}
            self.cond_action_id = {}
            self.cond_name = {}
            self.cond_is_activated = {}
            self.cond_if_input_period = {}
            self.cond_if_input_measurement = {}
            self.cond_if_input_direction = {}
            self.cond_if_input_setpoint = {}
            self.cond_do_output_id = {}
            self.cond_do_output_state = {}
            self.cond_do_output_duration = {}
            self.cond_execute_command = {}
            self.cond_email_notify = {}
            self.cond_do_lcd_id = {}
            self.cond_do_camera_id = {}
            self.cond_timer = {}
            self.smtp_wait_timer = {}

            self.setup_conditionals()

            self.timer = time.time() + self.period
        except Exception as except_msg:
            self.logger.exception("Init Error: {err}".format(
                err=except_msg))

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            while self.running:
                # Pause loop to modify conditional statements.
                # Prevents execution of conditional while variables are
                # being modified.
                if self.pause_loop:
                    self.verify_pause_loop = True
                    while self.pause_loop:
                        time.sleep(0.1)

                for each_cond_id in self.cond_id:
                    if self.cond_is_activated[each_cond_id]:
                        # Check input conditional if it has been activated
                        if time.time() > self.cond_timer[each_cond_id]:

                            # get measurement here

                            self.cond_timer[each_cond_id] = (
                                    time.time() +
                                    self.cond_if_input_period[each_cond_id])
                            check_conditionals(
                                self, each_cond_id, self.measurements, self.control,
                                Camera, Conditional, ConditionalActions,
                                Input, Math, PID, SMTP)

                time.sleep(0.1)

            self.running = False
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
            self.logger.exception("Run Error: {err}".format(
                err=except_msg))

    def error_not_within_max_age(self):
        self.logger.error(
            "One or more measurements were not within the Max Age that has been "
            "set. Ensure all Inputs are operating properly.")

    def get_measurements_from_str(self, inputs):
        try:
            measurements = []
            inputs_list = inputs.split(';')
            for each_input_set in inputs_list:
                input_id = each_input_set.split(',')[0]
                input_measure = each_input_set.split(',')[1]
                last_measurement = read_last_influxdb(
                    input_id,
                    input_measure,
                    self.max_measure_age)
                if not last_measurement:
                    return False, None
                else:
                    measurements.append(last_measurement[1])
            return True, measurements
        except ConnectionRefusedError:
            return False, "Influxdb: ConnectionRefusedError"
        except urllib3.exceptions.NewConnectionError:
            return False, "Influxdb: urllib3.exceptions.NewConnectionError"

    def get_measurements_from_id(self, measure_id, measure_name):
        measurement = read_last_influxdb(
            measure_id,
            measure_name,
            self.max_measure_age)
        if not measurement:
            return False, None
        return True, measurement

    def setup_conditionals(self, cond_mod='setup'):
        # Signal to pause the main loop and wait for verification
        self.pause_loop = True
        while not self.verify_pause_loop:
            time.sleep(0.1)

        self.cond_id = {}
        self.cond_action_id = {}
        self.cond_name = {}
        self.cond_is_activated = {}
        self.cond_if_input_period = {}
        self.cond_if_input_measurement = {}
        self.cond_if_input_direction = {}
        self.cond_if_input_setpoint = {}

        input_conditional = db_retrieve_table_daemon(
            Conditional)
        input_conditional = input_conditional.filter(
            Conditional.math_id == self.math_id)
        input_conditional = input_conditional.filter(
            Conditional.is_activated == True).all()

        if cond_mod == 'setup':
            self.cond_timer = {}
            self.smtp_wait_timer = {}
        elif cond_mod == 'add':
            self.logger.debug("Added Conditional")
        elif cond_mod == 'del':
            self.logger.debug("Deleted Conditional")
        elif cond_mod == 'mod':
            self.logger.debug("Modified Conditional")
        else:
            return 1

        for each_cond in input_conditional:
            if cond_mod == 'setup':
                self.logger.info(
                    "Activated Math Conditional {id}".format(id=each_cond.id))
            self.cond_id[each_cond.id] = each_cond.id
            self.cond_is_activated[each_cond.id] = each_cond.is_activated
            self.cond_if_input_period[each_cond.id] = each_cond.if_sensor_period
            self.cond_if_input_measurement[each_cond.id] = each_cond.if_sensor_measurement
            self.cond_if_input_direction[each_cond.id] = each_cond.if_sensor_direction
            self.cond_if_input_setpoint[each_cond.id] = each_cond.if_sensor_setpoint
            self.cond_timer[each_cond.id] = time.time() + each_cond.if_sensor_period
            self.smtp_wait_timer[each_cond.id] = time.time() + 3600

        self.pause_loop = False
        self.verify_pause_loop = False

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
