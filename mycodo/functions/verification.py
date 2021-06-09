# coding=utf-8
#
#  verification.py - Verify the difference of two measurements are not beyond a threshold
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
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb

measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
        'name': 'Verify'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'VERIFICATION',
    'function_name': 'Verification',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': "This function acquires 2 measurements, calculates the difference, and if the difference is not larger than the set threshold, the Measurement A value is stored. This enables verifying one sensor's measurement with another sensor's measurement. Only when they are both in agreement is a measurement stored. This stored measurement can be used in functions such as Conditional Statements that will notify the user if no measurement is avilable to indicate there may be an issue with a sensor.",

    'options_enabled': [
        'measurements_select_measurement_unit',
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
            'id': 'select_measurement_a',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'name': 'Measurement A',
            'phrase': 'Measurement A'
        },
        {
            'id': 'measurement_max_age_a',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': lazy_gettext('{} A {}'.format(lazy_gettext('Measurement'), lazy_gettext('Max Age'))),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'id': 'select_measurement_b',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'name': 'Measurement B',
            'phrase': 'Measurement B'
        },
        {
            'id': 'measurement_max_age_b',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': lazy_gettext('{} A {}'.format(lazy_gettext('Measurement'), lazy_gettext('Max Age'))),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'id': 'max_difference',
            'type': 'float',
            'default_value': 10.0,
            'required': True,
            'name': 'Maximum Difference',
            'phrase': 'The maximum allowed difference between the measurements'
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super(CustomModule, self).__init__(function, testing=testing, name=__name__)

        self.timer_loop = time.time()

        self.control = DaemonControl()

        # Initialize custom options
        self.period = None
        self.select_measurement_a_device_id = None
        self.select_measurement_a_measurement_id = None
        self.measurement_max_age_a = None
        self.select_measurement_b_device_id = None
        self.select_measurement_b_measurement_id = None
        self.measurement_max_age_b = None
        self.max_difference = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.initialize_variables()

    def initialize_variables(self):
        self.logger.debug(
            "Custom controller started with options: "
            "{}, {}, {}, {}, {}, {}, {}".format(
                self.select_measurement_a_device_id,
                self.select_measurement_a_measurement_id,
                self.measurement_max_age_a,
                self.select_measurement_a_device_id,
                self.select_measurement_a_measurement_id,
                self.measurement_max_age_a,
                self.max_difference))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        last_measurement_a = self.get_last_measurement(
            self.select_measurement_a_device_id,
            self.select_measurement_a_measurement_id,
            max_age=self.measurement_max_age_a)

        if last_measurement_a:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "Measurement A: {timestamp}, {meas}".format(
                    timestamp=last_measurement_a[0],
                    meas=last_measurement_a[1]))
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "Measurement A in the past {} seconds".format(
                    self.measurement_max_age_a))

        last_measurement_b = self.get_last_measurement(
            self.select_measurement_b_device_id,
            self.select_measurement_b_measurement_id,
            max_age=self.measurement_max_age_b)

        if last_measurement_b:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "Measurement B: {timestamp}, {meas}".format(
                    timestamp=last_measurement_b[0],
                    meas=last_measurement_b[1]))
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "Measurement B in the past {} seconds".format(
                    self.measurement_max_age_b))

        if last_measurement_a and last_measurement_b:
            list_measures = [last_measurement_a[1], last_measurement_b[1]]
            difference = max(list_measures) - min(list_measures)
            if difference > self.max_difference:
                self.logger.debug(
                    "Measurement difference ({}) greater than max allowed ({}). "
                    "Not storing measurement.".format(difference, self.max_difference))
                return

            measurement_dict = {
                0: {
                    'measurement': self.channels_measurement[0].measurement,
                    'unit': self.channels_measurement[0].unit,
                    'value': last_measurement_a[1]
                }
            }

            if measurement_dict:
                self.logger.debug(
                    "Adding measurements to InfluxDB with ID {}: {}".format(
                        self.unique_id, measurement_dict))
                add_measurements_influxdb(self.unique_id, measurement_dict)
            else:
                self.logger.debug(
                    "No measurements to add to InfluxDB with ID {}".format(
                        self.unique_id))
