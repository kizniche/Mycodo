# coding=utf-8
#
# controller_math.py - Math controller that performs math on other controllers
#                      to create new values
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
from statistics import stdev

import urllib3

import mycodo.utils.psypy as SI
from mycodo.databases.models import Conversion
from mycodo.databases.models import InputMeasurements
from mycodo.databases.models import Math
from mycodo.databases.models import MathMeasurements
from mycodo.databases.models import Misc
from mycodo.databases.models import SMTP
from mycodo.inputs.sensorutils import convert_units
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.influx import read_past_influxdb
from mycodo.utils.system_pi import get_input_or_math_measurement


class Measurement:
    """
    Class for holding all measurement values in a dictionary.
    The dictionary is formatted in the following way:

    {'measurement type':measurement value}

    Measurement type: The environmental or physical condition
    being measured, such as 'temperature', or 'pressure'.

    Measurement value: The actual measurement of the condition.
    """

    def __init__(self, raw_data):
        self.rawData = raw_data

    @property
    def values(self):
        return self.rawData


class MathController(threading.Thread):
    """
    Class to operate discrete PID controller

    """
    def __init__(self, ready, math_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.math_{id}".format(id=math_id.split('-')[0]))

        try:
            self.measurements = None
            self.running = False
            self.thread_startup_timer = timeit.default_timer()
            self.thread_shutdown_timer = 0
            self.ready = ready
            self.pause_loop = False
            self.verify_pause_loop = True
            self.control = DaemonControl()

            self.sample_rate = db_retrieve_table_daemon(
                Misc, entry='first').sample_rate_controller_math

            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            self.smtp_max_count = smtp.hourly_max
            self.email_count = 0
            self.allowed_to_send_notice = True

            self.math_id = math_id
            math = db_retrieve_table_daemon(Math, unique_id=self.math_id)

            self.math_measurements = db_retrieve_table_daemon(
                MathMeasurements).filter(
                    MathMeasurements.device_id == self.math_id)

            # General variables
            self.unique_id = math.unique_id
            self.name = math.name
            self.math_type = math.math_type
            self.is_activated = math.is_activated
            self.period = math.period
            self.max_measure_age = math.max_measure_age

            # Inputs to calculate with
            self.inputs = math.inputs

            # Difference variables
            self.difference_reverse_order = math.difference_reverse_order
            self.difference_absolute = math.difference_absolute

            # Equation variables
            self.equation_input = math.equation_input
            self.equation = math.equation

            # Verification variables
            self.max_difference = math.max_difference

            # Humidity variables
            self.dry_bulb_t_id = math.dry_bulb_t_id
            self.dry_bulb_t_measure_id = math.dry_bulb_t_measure_id
            self.wet_bulb_t_id = math.wet_bulb_t_id
            self.wet_bulb_t_measure_id = math.wet_bulb_t_measure_id
            self.pressure_pa_id = math.pressure_pa_id
            self.pressure_pa_measure_id = math.pressure_pa_measure_id

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

                if self.is_activated and time.time() > self.timer:

                    self.calculate_math()

                    # Ensure the next timer ends in the future
                    while time.time() > self.timer:
                        self.timer += self.period

                time.sleep(self.sample_rate)

            self.running = False
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
            self.logger.exception("Run Error: {err}".format(
                err=except_msg))

    def calculate_math(self):
        measurement_dict = {}

        if self.math_type == 'average':

            measurement = self.math_measurements.filter(
                MathMeasurements.channel == 0).first()
            success, measure = self.get_measurements_from_str(self.inputs)
            if success:
                average = float(sum(measure) / float(len(measure)))

                measurement_dict = {
                    measurement.channel: {
                        'measurement': measurement.measurement,
                        'unit': measurement.unit,
                        'value': average
                    }
                }
            elif measure:
                self.logger.error(measure)
            else:
                self.error_not_within_max_age()

        elif self.math_type == 'average_single':

            device_id = self.inputs.split(',')[0]
            device_measurement_id = self.inputs.split(',')[1]
            measurement = get_input_or_math_measurement(
                device_measurement_id)
            try:
                last_measurements = read_past_influxdb(
                    device_id,
                    measurement.unit,
                    measurement.measurement,
                    measurement.channel,
                    self.max_measure_age)

                if last_measurements:
                    measure_list = []
                    for each_set in last_measurements:
                        if len(each_set) == 2:
                            measure_list.append(each_set[1])
                    average = sum(measure_list) / float(len(measure_list))

                    measurement_dict = {
                        measurement.channel: {
                            'measurement': measurement.measurement,
                            'unit': measurement.unit,
                            'value': average
                        }
                    }
                else:
                    self.error_not_within_max_age()
            except Exception as msg:
                self.logger.error("average_single Error: {err}".format(err=msg))

        elif self.math_type == 'difference':

            measurement = self.math_measurements.filter(
                MathMeasurements.channel == 0).first()
            success, measure = self.get_measurements_from_str(self.inputs)
            if success:
                if self.difference_reverse_order:
                    difference = measure[1] - measure[0]
                else:
                    difference = measure[0] - measure[1]
                if self.difference_absolute:
                    difference = abs(difference)

                measurement_dict = {
                    measurement.channel: {
                        'measurement': measurement.measurement,
                        'unit': measurement.unit,
                        'value': difference
                    }
                }
            elif measure:
                self.logger.error(measure)
            else:
                self.error_not_within_max_age()

        elif self.math_type == 'equation':

            measurement = self.math_measurements.filter(
                MathMeasurements.channel == 0).first()
            success, measure = self.get_measurements_from_str(self.inputs)
            if success:
                replaced_str = self.equation.replace('x', str(measure[0]))
                equation_output = eval(replaced_str)

                measurement_dict = {
                    measurement.channel: {
                        'measurement': measurement.measurement,
                        'unit': measurement.unit,
                        'value': float(equation_output)
                    }
                }
            elif measure:
                self.logger.error(measure)
            else:
                self.error_not_within_max_age()

        elif self.math_type == 'statistics':

            success, measure = self.get_measurements_from_str(self.inputs)
            if success:
                # Perform some math
                stat_mean = float(sum(measure) / float(len(measure)))
                stat_median = median(measure)
                stat_minimum = min(measure)
                stat_maximum = max(measure)
                stdev_ = stdev(measure)
                stdev_mean_upper = stat_mean + stdev_
                stdev_mean_lower = stat_mean - stdev_

                list_measurement = [
                    stat_mean,
                    stat_median,
                    stat_minimum,
                    stat_maximum,
                    stdev_,
                    stdev_mean_upper,
                    stdev_mean_lower
                ]

                for each_measurement in self.math_measurements.all():
                    measurement_dict[each_measurement.channel] = {
                            'measurement': each_measurement.measurement,
                            'unit': each_measurement.unit,
                            'value': list_measurement[each_measurement.channel]
                    }

            elif measure:
                self.logger.error(measure)
            else:
                self.error_not_within_max_age()

        elif self.math_type == 'verification':

            measurement = self.math_measurements.filter(
                MathMeasurements.channel == 0).first()
            success, measure = self.get_measurements_from_str(self.inputs)
            if (success and
                    max(measure) - min(measure) <
                    self.max_difference):
                difference = max(measure) - min(measure)

                measurement_dict = {
                    measurement.channel: {
                        'measurement': measurement.measurement,
                        'unit': measurement.unit,
                        'value': difference
                    }
                }
            elif measure:
                self.logger.error(measure)
            else:
                self.error_not_within_max_age()

        elif self.math_type == 'humidity':

            pressure_pa = 101325
            critical_error = False

            if self.pressure_pa_id and self.pressure_pa_measure_id:
                success_pa, pressure = self.get_measurements_from_id(
                    self.pressure_pa_id, self.pressure_pa_measure_id)
                if success_pa:
                    pressure_pa = int(pressure[1])
                    # Pressure must be in Pa, convert if not

                    if db_retrieve_table_daemon(InputMeasurements, unique_id=self.pressure_pa_measure_id):
                        measurement = db_retrieve_table_daemon(InputMeasurements, unique_id=self.pressure_pa_measure_id)
                    elif db_retrieve_table_daemon(MathMeasurements, unique_id=self.pressure_pa_measure_id):
                        measurement = db_retrieve_table_daemon(MathMeasurements, unique_id=self.pressure_pa_measure_id)
                    else:
                        self.logger.error("Could not find pressure measurement")
                        measurement = None
                        critical_error = True

                    if measurement and measurement.unit != 'Pa':
                        for each_conv in db_retrieve_table_daemon(Conversion, entry='all'):
                            if (each_conv.convert_unit_from == measurement.unit and
                                    each_conv.convert_unit_to == 'Pa'):
                                pressure_pa = convert_units(
                                    each_conv.unique_id, pressure_pa)
                            else:
                                self.logger.error(
                                    "Could not find conversion for unit "
                                    "{unit} to Pa (Pascals)".format(
                                        unit=measurement.unit))
                                critical_error = True

            success_dbt, dry_bulb_t = self.get_measurements_from_id(
                self.dry_bulb_t_id, self.dry_bulb_t_measure_id)
            success_wbt, wet_bulb_t = self.get_measurements_from_id(
                self.wet_bulb_t_id, self.wet_bulb_t_measure_id)

            if success_dbt and success_wbt:
                dbt_kelvin = float(dry_bulb_t[1])
                wbt_kelvin = float(wet_bulb_t[1])

                if db_retrieve_table_daemon(InputMeasurements, unique_id=self.dry_bulb_t_measure_id):
                    measurement = db_retrieve_table_daemon(InputMeasurements, unique_id=self.dry_bulb_t_measure_id)
                elif db_retrieve_table_daemon(MathMeasurements, unique_id=self.dry_bulb_t_measure_id):
                    measurement = db_retrieve_table_daemon(MathMeasurements, unique_id=self.dry_bulb_t_measure_id)
                else:
                    self.logger.error("Could not find pressure measurement")
                    measurement = None
                    critical_error = True

                if measurement and measurement.unit != 'K':
                    for each_conv in db_retrieve_table_daemon(Conversion, entry='all'):
                        if (each_conv.convert_unit_from == measurement.unit and
                                each_conv.convert_unit_to == 'K'):
                            dbt_kelvin = convert_units(
                                each_conv.unique_id, dbt_kelvin)
                        else:
                            self.logger.error(
                                "Could not find conversion for unit "
                                "{unit} to K (Kelvin)".format(
                                    unit=measurement.unit))
                            critical_error = True

                    if db_retrieve_table_daemon(InputMeasurements, unique_id=self.dry_bulb_t_measure_id):
                        measurement = db_retrieve_table_daemon(InputMeasurements, unique_id=self.dry_bulb_t_measure_id)
                    elif db_retrieve_table_daemon(MathMeasurements, unique_id=self.dry_bulb_t_measure_id):
                        measurement = db_retrieve_table_daemon(MathMeasurements, unique_id=self.dry_bulb_t_measure_id)
                    else:
                        self.logger.error("Could not find pressure measurement")
                        measurement = None
                        critical_error = True

                    if measurement and measurement.unit != 'K':
                        for each_conv in db_retrieve_table_daemon(Conversion, entry='all'):
                            if (each_conv.convert_unit_from == measurement.unit and
                                    each_conv.convert_unit_to == 'K'):
                                wbt_kelvin = convert_units(
                                    each_conv.unique_id, wbt_kelvin)
                            else:
                                self.logger.error(
                                    "Could not find conversion for unit "
                                    "{unit} to K (Kelvin)".format(
                                        unit=measurement.unit))
                                critical_error = True

                # Convert temperatures to Kelvin (already done above)
                # dbt_kelvin = celsius_to_kelvin(dry_bulb_t_c)
                # wbt_kelvin = celsius_to_kelvin(wet_bulb_t_c)
                psypi = None

                try:
                    if not critical_error:
                        psypi = SI.state(
                            "DBT", dbt_kelvin, "WBT", wbt_kelvin, pressure_pa)
                    else:
                        self.logger.error(
                            "One or more critical errors prevented the "
                            "humidity from being calculated")
                except TypeError as err:
                    self.logger.error("TypeError: {msg}".format(msg=err))

                if psypi:
                    percent_relative_humidity = psypi[2] * 100

                    # Ensure percent humidity stays within 0 - 100 % range
                    if percent_relative_humidity > 100:
                        percent_relative_humidity = 100
                    elif percent_relative_humidity < 0:
                        percent_relative_humidity = 0

                    # Dry bulb temperature: psypi[0])
                    # Wet bulb temperature: psypi[5])

                    specific_enthalpy = float(psypi[1])
                    humidity = float(percent_relative_humidity)
                    specific_volume = float(psypi[3])
                    humidity_ratio = float(psypi[4])

                    list_measurement = [
                        specific_enthalpy,
                        humidity,
                        specific_volume,
                        humidity_ratio
                    ]

                    for each_measurement in self.math_measurements.all():
                        measurement_dict[each_measurement.channel] = {
                            'measurement': each_measurement.measurement,
                            'unit': each_measurement.unit,
                            'value': list_measurement[each_measurement.channel]
                        }
            else:
                self.error_not_within_max_age()

        else:
            self.logger.error("Unknown math type: {type}".format(type=self.math_type))

        # Finally, add measurements to influxdb
        add_measurements_influxdb(self.unique_id, measurement_dict)

    def error_not_within_max_age(self):
        self.logger.error(
            "One or more inputs were not within the Max Age that has been "
            "set. Ensure all Inputs are operating properly.")

    def get_measurements_from_str(self, device):
        try:
            measurements = []
            device_list = device.split(';')
            for each_device_set in device_list:
                device_id = each_device_set.split(',')[0]
                device_measure_id = each_device_set.split(',')[1]

                measurement = get_input_or_math_measurement(
                    device_measure_id)
                if not measurement:
                    return False, None

                last_measurement = read_last_influxdb(
                    device_id,
                    measurement.unit,
                    measurement.measurement,
                    measurement.channel,
                    self.max_measure_age)
                if not last_measurement:
                    return False, None
                else:
                    measurements.append(last_measurement[1])
            return True, measurements
        except urllib3.exceptions.NewConnectionError:
            return False, "Influxdb: urllib3.exceptions.NewConnectionError"
        except Exception as msg:
            return False, "Influxdb: Unknown Error: {err}".format(err=msg)

    def get_measurements_from_id(self, device_id, measure_id):
        measurement = get_input_or_math_measurement(measure_id)

        measurement = read_last_influxdb(
            device_id,
            measurement.unit,
            measurement.measurement,
            measurement.channel,
            self.max_measure_age)
        if not measurement:
            return False, None
        return True, measurement

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
