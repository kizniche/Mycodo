# coding=utf-8
#
#  humidity_wet_dry_bulb.py - Calculates humidity from wet and dry bulb temperatures
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

import mycodo.utils.psypy as SI
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info

measurements_dict = {
    0: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    1: {
        'measurement': 'humidity_ratio',
        'unit': 'kg_kg'
    },
    2: {
        'measurement': 'specific_enthalpy',
        'unit': 'kJ_kg'
    },
    3: {
        'measurement': 'specific_volume',
        'unit': 'm3_kg'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'HUMIDITY_BULB',
    'function_name': "{} ({})".format(lazy_gettext('Humidity'), lazy_gettext('Wet/Dry-Bulb')),
    'measurements_dict': measurements_dict,

    'message': 'This function calculates the humidity based on wet and dry bulb temperature measurements.',

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
            'id': 'select_measurement_temp_dry_c',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'required': False,
            'name': 'Dry Bulb Temperature',
            'phrase': 'Dry Bulb temperature measurement'
        },
        {
            'id': 'max_measure_age_temp_dry_c',
            'type': 'integer',
            'default_value': 360,
            'required': False,
            'name': lazy_gettext('{} {}'.format(lazy_gettext('Dry Bulb'), lazy_gettext('Max Age'))),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'id': 'select_measurement_temp_wet_c',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'required': False,
            'name': 'Wet Bulb Temperature',
            'phrase': 'Wet Bulb temperature measurement'
        },
        {
            'id': 'max_measure_age_temp_wet_c',
            'type': 'integer',
            'default_value': 360,
            'required': False,
            'name': lazy_gettext('{} {}'.format(lazy_gettext('Wet Bulb'), lazy_gettext('Max Age'))),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'id': 'select_measurement_pressure_pa',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function'
            ],
            'required': False,
            'name': 'Pressure',
            'phrase': 'Pressure measurement'
        },
        {
            'id': 'max_measure_age_pressure_pa',
            'type': 'integer',
            'default_value': 360,
            'required': False,
            'name': lazy_gettext('{} {}'.format(lazy_gettext('Pressure'), lazy_gettext('Max Age'))),
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

        self.select_measurement_temp_dry_c_device_id = None
        self.select_measurement_temp_dry_c_measurement_id = None
        self.max_measure_age_temp_dry_c = None
        self.select_measurement_temp_wet_c_device_id = None
        self.select_measurement_temp_wet_c_measurement_id = None
        self.max_measure_age_temp_wet_c = None
        self.select_measurement_pressure_pa_device_id = None
        self.select_measurement_pressure_pa_measurement_id = None
        self.max_measure_age_pressure_pa = None

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

        temp_wet_k = None
        temp_dry_k = None
        pressure_pa = 101325

        if (self.select_measurement_pressure_pa_device_id and
                self.select_measurement_pressure_pa_measurement_id and
                self.max_measure_age_pressure_pa):

            device_measurement = get_measurement(
                self.select_measurement_pressure_pa_measurement_id)
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)

            last_measurement_pa = self.get_last_measurement(
                self.select_measurement_pressure_pa_device_id,
                self.select_measurement_pressure_pa_measurement_id,
                max_age=self.max_measure_age_pressure_pa)

            if last_measurement_pa:
                pressure_pa = convert_from_x_to_y_unit(unit, 'Pa', last_measurement_pa[1])

        last_measurement_wet = self.get_last_measurement(
            self.select_measurement_temp_wet_c_device_id,
            self.select_measurement_temp_wet_c_measurement_id,
            max_age=self.max_measure_age_temp_wet_c)

        if last_measurement_wet:
            device_measurement = get_measurement(
                self.select_measurement_temp_wet_c_measurement_id)
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)
            temp_wet_k = convert_from_x_to_y_unit(unit, 'K', last_measurement_wet[1])

        last_measurement_dry = self.get_last_measurement(
            self.select_measurement_temp_dry_c_device_id,
            self.select_measurement_temp_dry_c_measurement_id,
            max_age=self.max_measure_age_temp_dry_c)

        if last_measurement_dry:
            device_measurement = get_measurement(
                self.select_measurement_temp_dry_c_measurement_id)
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)
            temp_dry_k = convert_from_x_to_y_unit(unit, 'K', last_measurement_dry[1])

        if temp_wet_k and temp_dry_k:
            measurements = copy.deepcopy(measurements_dict)
            psypi = None

            try:
                psypi = SI.state(
                    "DBT", temp_dry_k, "WBT", temp_wet_k, pressure_pa)
            except TypeError as err:
                self.logger.error("TypeError: {msg}".format(msg=err))

            if not psypi:
                self.logger.error("Could not calculate humidity from wet/dry bulbs")
                return

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

            self.logger.debug(
                "Dry Temp: {dtk}, "
                "Wet Temp: {wtk}, "
                "Pressure: {pres},"
                "Humidity: {rh}".format(
                    dtk=temp_dry_k,
                    wtk=temp_wet_k,
                    pres=pressure_pa,
                    rh=humidity))

            list_measurement = [
                humidity,
                humidity_ratio,
                specific_enthalpy,
                specific_volume
            ]

            for each_channel, each_measurement in self.channels_measurement.items():
                if each_measurement.is_enabled:
                    channel, unit, measurement = return_measurement_info(
                        each_measurement, self.channels_conversion[each_channel])

                    measurements[channel] = {
                        'measurement': measurement,
                        'unit': unit,
                        'value': list_measurement[channel]
                    }

            # Add measurement(s) to influxdb
            if measurements:
                self.logger.debug(
                    "Adding measurements to InfluxDB with ID {}: {}".format(
                        self.unique_id, measurements))
                add_measurements_influxdb(self.unique_id, measurements)
            else:
                self.logger.debug(
                    "No measurements to add to InfluxDB with ID {}".format(
                        self.unique_id))
        else:
            self.logger.debug(
                "One or more temperature measurements could not be found within the Max Age. Not calculating.")
