# coding=utf-8
#
#  equation_multi.py - Perform equation with multiple measurements
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
from mycodo.utils.influx import write_influxdb_value

measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
        'name': 'Equation Output'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'EQUATION_MULTI',
    'function_name': 'Equation (Multi-Measure)',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': 'This function acquires two measurements and uses them within a user-set equation and stores the '
               'resulting value as the selected measurement and unit.',

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
            'name': lazy_gettext('{} A'.format(lazy_gettext('Measurement'))),
            'phrase': 'Measurement to replace a'
        },
        {
            'id': 'measurement_a_max_age',
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
            'name': lazy_gettext('{} B'.format(lazy_gettext('Measurement'))),
            'phrase': 'Measurement to replace b'
        },
        {
            'id': 'measurement_b_max_age',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': lazy_gettext('{} B {}'.format(lazy_gettext('Measurement'), lazy_gettext('Max Age'))),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'id': 'equation',
            'type': 'text',
            'default_value': 'a*(2+b)',
            'required': True,
            'name': lazy_gettext('Equation'),
            'phrase': 'Equation using measurements a and b'
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
        self.measurement_a_max_age = None
        self.select_measurement_b_device_id = None
        self.select_measurement_b_measurement_id = None
        self.measurement_b_max_age = None
        self.equation = None

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
            "{}, {}, {}, {}, {}".format(
                self.select_measurement_a_device_id,
                self.select_measurement_a_measurement_id,
                self.select_measurement_b_device_id,
                self.select_measurement_b_measurement_id,
                self.equation))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        # Get last measurement for select_measurement_1
        last_measurement_a = self.get_last_measurement(
            self.select_measurement_a_device_id,
            self.select_measurement_a_measurement_id,
            max_age=self.measurement_a_max_age)

        if last_measurement_a:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "Measurement A: {timestamp}, {meas}".format(
                    timestamp=last_measurement_a[0],
                    meas=last_measurement_a[1]))
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "Measurement A device ID {} and measurement "
                "ID {} in the past {} seconds".format(
                    self.select_measurement_a_device_id,
                    self.select_measurement_a_measurement_id,
                    self.measurement_a_max_age))

        last_measurement_b = self.get_last_measurement(
            self.select_measurement_b_device_id,
            self.select_measurement_b_measurement_id,
            max_age=self.measurement_b_max_age)

        if last_measurement_b:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "Measurement B: {timestamp}, {meas}".format(
                    timestamp=last_measurement_b[0],
                    meas=last_measurement_b[1]))
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "Measurement B device ID {} and measurement "
                "ID {} in the past {} seconds".format(
                    self.select_measurement_b_device_id,
                    self.select_measurement_b_measurement_id,
                    self.measurement_b_max_age))

        # Perform equation and save to DB here
        if last_measurement_a and last_measurement_b:
            equation_str = self.equation
            equation_str = equation_str.replace("a", str(last_measurement_a[1]))
            equation_str = equation_str.replace("b", str(last_measurement_b[1]))

            self.logger.debug("Equation: {} = {}".format(self.equation, equation_str))

            equation_output = eval(equation_str)

            self.logger.debug("Output: {}".format(equation_output))

            write_influxdb_value(
                self.unique_id,
                self.channels_measurement[0].unit,
                value=equation_output,
                measure=self.channels_measurement[0].measurement,
                channel=0)
        else:
            self.logger.debug("One more more measurements could not be found within the Max Age. Not calculating.")
