# coding=utf-8
#
#  statistics_past_single.py - Calculate statistics for a single measurement
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
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
import threading
import time
from statistics import median
from statistics import stdev

from flask_babel import lazy_gettext

from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_past_influxdb
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info


def constraints_pass_positive_value(mod_controller, value):
    """
    Check if the user controller is acceptable
    :param mod_controller: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_controller


measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
        'name': 'Mean'
    },
    1: {
        'measurement': '',
        'unit': '',
        'name': 'Median'
    },
    2: {
        'measurement': '',
        'unit': '',
        'name': 'Minimum'
    },
    3: {
        'measurement': '',
        'unit': '',
        'name': 'Maximum'
    },
    4: {
        'measurement': '',
        'unit': '',
        'name': 'Standard Deviation'
    },
    5: {
        'measurement': '',
        'unit': '',
        'name': 'St. Dev. of Mean (upper)'
    },
    6: {
        'measurement': '',
        'unit': '',
        'name': 'St. Dev. of Mean (lower)'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'STAT_PAST_SINGLE',
    'function_name': 'Statistics (Past, Single)',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': 'This function acquires multiple values from a single measurement, calculates statistics, and stores '
               'the resulting values as the selected unit.',

    'options_enabled': [
        'measurements_select_measurement_unit',
        'measurements_select',
        'custom_options'
    ],

    'custom_options': [
        {
            'id': 'period',
            'type': 'float',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Period (seconds)'),
            'phrase': lazy_gettext('The duration (seconds) between measurements or actions')
        },
        {
            'id': 'max_measure_age',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': 'Measurement Max Age',
            'phrase': 'The maximum allowed age of the measurements'
        },
        {
            'id': 'select_measurement',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'name': 'Measurement',
            'phrase': 'Measurement to perform statistics on'
        }
    ]
}


class CustomModule(AbstractController, threading.Thread):
    """
    Class to operate custom controller
    """
    def __init__(self, ready, unique_id, testing=False):
        threading.Thread.__init__(self)
        super(CustomModule, self).__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.log_level_debug = None
        self.timer_loop = time.time()

        self.control = DaemonControl()

        # Initialize custom options
        self.period = None
        self.select_measurement_device_id = None
        self.select_measurement_measurement_id = None
        self.max_measure_age = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

    def initialize_variables(self):
        controller = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.log_level_debug = controller.log_level_debug
        self.set_log_level_debug(self.log_level_debug)

    def loop(self):
        if self.timer_loop < time.time():
            while self.timer_loop < time.time():
                self.timer_loop += self.period

            device_measurement = get_measurement(self.select_measurement_measurement_id)

            if not device_measurement:
                self.logger.error("Could not find Device Measurement")
                return

            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)

            last_measurements = read_past_influxdb(
                self.select_measurement_device_id,
                unit,
                channel,
                self.max_measure_age,
                measure=measurement)

            self.logger.debug("Past Measurements returned: {}".format(last_measurements))

            if not last_measurements:
                self.logger.error("Could not find measurements within the set Max Age")
                return False

            measure = []
            for each_measure in last_measurements:
                measure.append(each_measure[1])

            if len(measure) > 1:
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

                for each_channel, each_measurement in self.channels_measurement.items():
                    if each_measurement.is_enabled:
                        channel, unit, measurement = return_measurement_info(
                            each_measurement, self.channels_conversion[each_channel])

                        self.logger.debug("Saving {} to channel {} with measurement {} and unit {}".format(
                            list_measurement[each_channel], each_channel, measurement, unit))

                        write_influxdb_value(
                            self.unique_id,
                            unit,
                            value=list_measurement[each_channel],
                            measure=measurement,
                            channel=each_channel)
            else:
                self.logger.debug("Less than 2 measurements found within Max Age. "
                                  "Calculations need at least 2 measurements. Not calculating.")



