# coding=utf-8
#
#  custom_function_multiple_channels.py - Function with multiple channels
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
import random
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import FunctionChannel
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.inputs import parse_measurement

# Measurements
measurements_dict = {
    0: {
        'name': 'a'
    }
}

# Channels
channels_dict = {
    0: {}
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'example_function_multiple_channels',
    'function_name': 'Example: Multiple Channels',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'measurements_variable_amount': True,
    'channel_quantity_same_as_measurements': True,

    'message': 'This is an example Function that allows the user to select a variable number of measurements.',

    'options_enabled': [
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
            'name': "{} ({})".format(lazy_gettext('Period'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The duration between measurements or actions')
        }
    ],

    'custom_channel_options': [
        {
            'id': 'float_input',
            'type': 'float',
            'default_value': 3.5,
            'required': True,
            'name': 'Number',
            'phrase': 'Set a number'
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.options_channels = {}
        self.timer_loop = time.time()

        self.control = DaemonControl()

        # Initialize custom options
        self.period = None
        self.float_input = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.try_initialize()

    def initialize(self):
        function_channels = db_retrieve_table_daemon(
            FunctionChannel).filter(FunctionChannel.function_id == self.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            FUNCTION_INFORMATION['custom_channel_options'], function_channels)

        self.logger.debug(
            "Custom controller started with options: {}".format( self.float_input))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        measurements = {}
        for channel in self.channels_measurement:
            # Original value/unit
            measurements[channel] = {}
            measurements[channel]['measurement'] = self.channels_measurement[channel].measurement
            measurements[channel]['unit'] = self.channels_measurement[channel].unit
            measurements[channel]['value'] = random.randint(1, 100)

            # Convert value/unit is conversion_id present and valid
            if self.channels_conversion[channel]:
                conversion = db_retrieve_table_daemon(
                    Conversion, unique_id=self.channels_measurement[channel].conversion_id)
                if conversion:
                    meas = parse_measurement(
                        self.channels_conversion[channel],
                        self.channels_measurement[channel],
                        measurements,
                        channel,
                        measurements[channel])

                    measurements[channel]['measurement'] = meas[channel]['measurement']
                    measurements[channel]['unit'] = meas[channel]['unit']
                    measurements[channel]['value'] = meas[channel]['value']

        if measurements:
            self.logger.debug("Adding measurements to influxdb: {}".format(measurements))
            add_measurements_influxdb(self.unique_id, measurements)
        else:
            self.logger.debug("No measurements to add to influxdb.")
