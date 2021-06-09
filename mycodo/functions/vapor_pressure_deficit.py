# coding=utf-8
#
#  vapor_pressure_deficit.py - Calculates vapor pressure deficit from leaf temperature and humidity
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
import copy
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info

measurements_dict = {
    0: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'VAP_PRESS_DEFICIT',
    'function_name': 'Vapor Pressure Deficit',
    'measurements_dict': measurements_dict,

    'message': 'This function calculates the vapor pressure deficit based on leaf temperature and humidity.',

    'options_enabled': [
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
            'name': 'Start Offset',
            'phrase': 'The duration (seconds) to wait before the first operation'
        },
        {
            'id': 'select_measurement_temperature_c',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'required': False,
            'name': 'Temperature',
            'phrase': 'Temperature measurement'
        },
        {
            'id': 'max_measure_age_temperature_c',
            'type': 'integer',
            'default_value': 360,
            'required': False,
            'name': lazy_gettext('{} {}'.format(lazy_gettext('Temperature'), lazy_gettext('Max Age'))),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'id': 'select_measurement_humidity',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'required': False,
            'name': 'Humidity',
            'phrase': 'Humidity measurement'
        },
        {
            'id': 'max_measure_age_humidity',
            'type': 'integer',
            'default_value': 360,
            'required': False,
            'name': lazy_gettext('{} {}'.format(lazy_gettext('Humidity'), lazy_gettext('Max Age'))),
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

        self.select_measurement_temperature_c_device_id = None
        self.select_measurement_temperature_c_measurement_id = None
        self.max_measure_age_temperature_c = None
        self.select_measurement_humidity_device_id = None
        self.select_measurement_humidity_measurement_id = None
        self.max_measure_age_humidity = None

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

        temp_c = None
        hum_percent = None
        vpd_pa = None

        last_measurement_temp = self.get_last_measurement(
            self.select_measurement_temperature_c_device_id,
            self.select_measurement_temperature_c_measurement_id,
            max_age=self.max_measure_age_temperature_c)

        self.logger.debug("Temp: {}".format(last_measurement_temp))

        if last_measurement_temp:
            device_measurement = get_measurement(
                self.select_measurement_temperature_c_measurement_id)
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)
            temp_c = convert_from_x_to_y_unit(unit, 'C', last_measurement_temp[1])

        last_measurement_hum = self.get_last_measurement(
            self.select_measurement_humidity_device_id,
            self.select_measurement_humidity_measurement_id,
            max_age=self.max_measure_age_humidity)

        self.logger.debug("Hum: {}".format(last_measurement_hum))

        if last_measurement_hum:
            device_measurement = get_measurement(
                self.select_measurement_humidity_measurement_id)
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)
            hum_percent = convert_from_x_to_y_unit(unit, 'percent', last_measurement_hum[1])

        if temp_c and hum_percent:
            measurement_dict = copy.deepcopy(measurements_dict)

            try:
                vpd_pa = calculate_vapor_pressure_deficit(temp_c, hum_percent)
            except TypeError as err:
                self.logger.error("Error: {msg}".format(msg=err))

            if vpd_pa:
                dev_measurement = self.channels_measurement[0]
                channel, unit, measurement = return_measurement_info(
                    dev_measurement, self.channels_conversion[0])

                vpd_store = convert_from_x_to_y_unit('Pa', unit, vpd_pa)

                measurement_dict[0] = {
                    'measurement': measurement,
                    'unit': unit,
                    'value': vpd_store
                }

            # Add measurement(s) to influxdb
            if measurement_dict:
                self.logger.debug(
                    "Adding measurements to InfluxDB with ID {}: {}".format(
                        self.unique_id, measurement_dict))
                add_measurements_influxdb(self.unique_id, measurement_dict)
            else:
                self.logger.debug(
                    "No measurements to add to InfluxDB with ID {}".format(
                        self.unique_id))
        else:
            self.logger.debug(
                "Could not acquire both temperature and humidity measurements.")
