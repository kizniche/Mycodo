# coding=utf-8
#
# controller_math.py - Math controller that performs math on other controllers
#                      and creates a new value
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

import utils.psypy as SI

from databases.models import Math
from utils.database import db_retrieve_table_daemon
from utils.influx import read_last_influxdb
from utils.influx import write_influxdb_value
from utils.system_pi import celsius_to_kelvin


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

        # General variables
        self.math_unique_id = math.unique_id
        self.name = math.name
        self.math_type = math.math_type
        self.is_activated = math.is_activated
        self.period = math.period
        self.max_measure_age = math.max_measure_age
        self.measure = math.measure
        self.measure_units = math.measure_units

        # Average, Maximum, Minimum variables
        self.inputs = math.inputs

        # Verification variables
        self.max_difference = math.max_difference

        # Humidity variables
        self.dry_bulb_t_id = math.dry_bulb_t_id
        self.dry_bulb_t_measure = math.dry_bulb_t_measure
        self.wet_bulb_t_id = math.wet_bulb_t_id
        self.wet_bulb_t_measure = math.wet_bulb_t_measure
        self.pressure_pa_id = math.pressure_pa_id
        self.pressure_pa_measure = math.pressure_pa_measure

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
                    if self.math_type == 'average':
                        success, measurements = self.get_measurements_from_str(self.inputs)
                        if success:
                            average = sum(measurements) / float(len(measurements))
                            self.write_measurement(self.math_unique_id,
                                                   self.measure,
                                                   average)
                        else:
                            self.logger.error(
                                "One or more inputs were not within the "
                                "Max Age that has been set. Ensure all "
                                "Inputs are operating properly.")

                    elif self.math_type == 'largest':
                        success, measurements = self.get_measurements_from_str(self.inputs)
                        if success:
                            self.write_measurement(self.math_unique_id,
                                                   self.measure,
                                                   max(measurements))

                    elif self.math_type == 'smallest':
                        success, measurements = self.get_measurements_from_str(self.inputs)
                        if success:
                            self.write_measurement(self.math_unique_id,
                                                   self.measure,
                                                   min(measurements))

                    elif self.math_type == 'verification':
                        success, measurements = self.get_measurements_from_str(self.inputs)
                        if (success and
                                max(measurements) - min(measurements) <
                                self.max_difference):
                            average = sum(measurements) / float(len(measurements))
                            self.write_measurement(self.math_unique_id,
                                                   self.measure,
                                                   average)

                    elif self.math_type == 'humidity':
                        pressure_pa = 101325
                        success_dbt, dry_bulb_t = self.get_measurements_from_id(
                            self.dry_bulb_t_id, self.dry_bulb_t_measure)
                        success_wbt, wet_bulb_t = self.get_measurements_from_id(
                            self.wet_bulb_t_id, self.wet_bulb_t_measure)
                        if not success_dbt or not success_wbt:
                            break

                        if self.pressure_pa_id and self.pressure_pa_measure:
                            success_pa, pressure = self.get_measurements_from_id(
                                self.pressure_pa_id, self.pressure_pa_measure)
                            pressure_pa = int(pressure[1])
                            if not success_pa:
                                break

                        dbt_kelvin = celsius_to_kelvin(float(dry_bulb_t[1]))
                        wbt_kelvin = celsius_to_kelvin(float(wet_bulb_t[1]))

                        psypi = SI.state("DBT", dbt_kelvin, "WBT", wbt_kelvin, pressure_pa)

                        # print("The dry bulb temperature is ", psypi[0])
                        # print("The specific enthalpy is ", psypi[1])
                        # print("The relative humidity is ", psypi[2])
                        # print("The specific volume is ", psypi[3])
                        # print("The humidity ratio is ", psypi[4])
                        # print("The wet bulb temperature is ", psypi[5])

                        # self.write_measurement(self.math_unique_id,
                        #                        'specific_enthalpy',
                        #                        psypi[1])

                        percent_relative_humidity = psypi[2] * 100
                        self.write_measurement(self.math_unique_id,
                                               'humidity',
                                               percent_relative_humidity)

                        # self.write_measurement(self.math_unique_id,
                        #                        'specific_volume',
                        #                        psypi[3])
                        #
                        # self.write_measurement(self.math_unique_id,
                        #                        'humidity_ratio',
                        #                        psypi[4])

                t.sleep(0.1)

            self.running = False
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
                self.logger.exception("Run Error: {err}".format(
                    err=except_msg))

    def get_measurements_from_str(self, inputs):
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

    def get_measurements_from_id(self, measure_id, measure_name):
        measurement = read_last_influxdb(
            measure_id,
            measure_name,
            self.max_measure_age)
        if not measurement:
            return False, None
        return True, measurement

    @staticmethod
    def write_measurement(unique_id, measurement, value):
        write_math_db = threading.Thread(
            target=write_influxdb_value,
            args=(unique_id,
                  measurement,
                  value,))
        write_math_db.start()

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

