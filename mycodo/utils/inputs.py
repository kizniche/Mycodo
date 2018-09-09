# -*- coding: utf-8 -*-
#
#  inputs.py - Mycodo core utils
#
#  Copyright (C) 2018  Kyle T. Gabriel
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

import importlib.util
import logging
import timeit

import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/../..'))

logger = logging.getLogger("mycodo.input_parser")


def dict_has_value(dict_inputs, input_custom, key):
    if (key in input_custom.INPUT_INFORMATION and
            (input_custom.INPUT_INFORMATION[key] or
             input_custom.INPUT_INFORMATION[key] == 0)):
        dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']][key] = \
            input_custom.INPUT_INFORMATION[key]
    return dict_inputs

# TODO: add alembic revision that sets input.location = input.device_loc, then delete device_loc column


def parse_input_information():
    startup_timer = timeit.default_timer()

    excluded_files = ['__init__.py', '__pycache__', 'base_input.py',
                      'custom_inputs', 'dummy_input.py', 'input_template.py',
                      'parse_inputs.py','sensorutils.py']

    input_paths = ['/var/mycodo-root/mycodo/inputs', '/var/mycodo-root/mycodo/inputs/custom_inputs']

    dict_inputs = {}

    for each_path in input_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            skip_file = False

            if each_file in excluded_files:
                skip_file = True

            if not skip_file:
                full_path = "{}/{}".format(real_path, each_file)

                spec = importlib.util.spec_from_file_location('module.name', full_path)
                input_custom = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(input_custom)

                if not hasattr(input_custom, 'INPUT_INFORMATION'):
                    skip_file = True

            if not skip_file:
                # logger.info("Found input: {}, {}".format(input_custom.INPUT_INFORMATION['unique_name_input'], full_path))

                # Populate dictionary of input information
                if input_custom.INPUT_INFORMATION['unique_name_input'] in dict_inputs:
                    logger.error("Error: Cannot add input modules because it does not have a unique name: {name}".format(
                        name=input_custom.INPUT_INFORMATION['unique_name_input']))
                else:
                    dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']] = {}

                dict_inputs = dict_has_value(dict_inputs, input_custom, 'common_name_input')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'common_name_measurements')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'unique_name_measurements')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'input_manufacturer')

                # Dependencies
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'dependencies_pypi')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'dependencies_github')

                # Interface
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'interfaces')

                # Nonstandard (I2C, UART, etc.) location
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'location')

                # 1WIRE
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'w1thermsensor_detect_1wire')

                # I2C
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'i2c_location')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'i2c_address_editable')

                dict_inputs = dict_has_value(dict_inputs, input_custom, 'options_enabled')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'options_disabled')

                # UART
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'uart_location')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'uart_baud_rate')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_cs')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_miso')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_mosi')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_clock')

                # Analog-to-digital converter
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_measure')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_measure_units')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'convert_to_unit')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_volts_min')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_volts_max')

                # Misc
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'period')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'cmd_command')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'cmd_measurement')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'cmd_measurement_units')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution_2')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'sensitivity')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'thermocouple_type')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'ref_ohm')

    run_time = timeit.default_timer() - startup_timer
    logger.info("Input parse time: {time:.3f} seconds".format(time=run_time))

    return dict_inputs
