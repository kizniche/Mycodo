# coding=utf-8
#
#  average_past_single.py - Calculates the average of past measurements for a single channel
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

from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import average_past_seconds
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info

measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'AVG_PAST_SINGLE',
    'function_name': 'Average (Past, Single)',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': 'This function acquires the past measurements (within Max Age) for the selected measurement, averages '
               'them, then stores the resulting value as the selected measurement and unit.',

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
            'id': 'start_offset',
            'type': 'integer',
            'default_value': 10,
            'required': True,
            'name': lazy_gettext('Start Offset'),
            'phrase': 'The duration (seconds) to wait before the first operation'
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
            'name': lazy_gettext('Measurement'),
            'phrase': 'Measurement to replace "x" in the equation'
        },
        {
            'id': 'max_measure_age',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': lazy_gettext('Max Age'),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
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
        self.start_offset = None
        self.select_measurement_device_id = None
        self.select_measurement_measurement_id = None
        self.max_measure_age = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.initialize_variables()

    def initialize_variables(self):
        self.timer_loop = time.time() + self.start_offset

    def loop(self):
        if self.timer_loop > time.time():
            return

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

        average = average_past_seconds(
            self.select_measurement_device_id,
            unit,
            channel,
            self.max_measure_age,
            measure=measurement)

        if not average:
            self.logger.error("Could not find measurement within the set Max Age")
            return False

        measurement_dict = {
            0: {
                'measurement': self.channels_measurement[0].measurement,
                'unit': self.channels_measurement[0].unit,
                'value': average
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
