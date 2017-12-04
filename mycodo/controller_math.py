# coding=utf-8
#
# controller_math.py - Math controller that performs math on Inputs and
#                      creates a new value
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
import time as t
import timeit

from databases.models import Math
from utils.database import db_retrieve_table_daemon
from utils.influx import read_last_influxdb
from utils.influx import write_influxdb_value


class MathController(threading.Thread):
    """
    Class to operate discrete PID controller

    """
    def __init__(self, ready, math_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.math_{id}".format(id=math_id))

        self.running = False
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.math_id = math_id

        math = db_retrieve_table_daemon(Math, device_id=self.math_id)
        self.math_unique_id = math.unique_id
        self.name = math.name
        self.math_type = math.math_type
        self.is_activated = math.is_activated
        self.period = math.period
        self.inputs = math.inputs
        self.max_measure_age = math.max_measure_age
        self.measure = math.measure
        self.measure_units = math.measure_units

        self.timer = t.time() + self.period

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            while self.running:

                if self.is_activated and t.time() > self.timer:
                    # Ensure the timer ends in the future
                    while t.time() > self.timer:
                        self.timer = self.timer + self.period

                    # If PID is active, retrieve input measurement and update PID output
                    if self.math_type == 'average' and self.inputs:
                        missing_measure = False
                        measurements = []
                        inputs_list = self.inputs.split(';')
                        for each_input_set in inputs_list:
                            input_id = each_input_set.split(',')[0]
                            input_measure = each_input_set.split(',')[1]
                            last_measurement = read_last_influxdb(
                                input_id,
                                input_measure,
                                self.max_measure_age)
                            if not last_measurement:
                                missing_measure = True
                            else:
                                measurements.append(last_measurement[1])

                        if not missing_measure:
                            average = sum(measurements)/float(len(measurements))
                            write_math_db = threading.Thread(
                                target=write_influxdb_value,
                                args=(self.math_unique_id,
                                      self.measure,
                                      average,))
                            write_math_db.start()

                        else:
                            self.logger.error(
                                "One or more inputs were not within the "
                                "Max Age that has been set. Ensure all "
                                "Inputs are operating properly.")

                t.sleep(0.1)

            self.running = False
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
                self.logger.exception("Run Error: {err}".format(
                    err=except_msg))

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

