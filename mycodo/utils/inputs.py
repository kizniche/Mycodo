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


def load_module_from_file(path_file):
    spec = importlib.util.spec_from_file_location('module.name', path_file)
    input_custom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(input_custom)
    return input_custom


def parse_input_information():
    # Uncomment to enable timer
    # startup_timer = timeit.default_timer()

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
                input_custom = load_module_from_file(full_path)

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

                dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['file_path'] = full_path

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

                # UART
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'uart_location')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'uart_baud_rate')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_cs')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_miso')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_mosi')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'pin_clock')

                # Bluetooth (BT)
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'bt_location')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'bt_adapter')

                # Which form options to display and whether each option is enabled
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'options_enabled')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'options_disabled')

                # Host options
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'times_check')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'deadline')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'port')

                # Signal options
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'weighting')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'sample_time')

                # Analog-to-digital converter
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'analog_to_digital_converter')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_channel')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_gain')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_resolution')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_volts_min')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_volts_max')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_units_min')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_units_max')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_inverse_unit_scale')

                # Misc
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'period')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'convert_to_unit')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'cmd_command')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution_2')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'sensitivity')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'thermocouple_type')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'ref_ohm')

    # Uncomment to enable timer, also uncomment line at start of function
    # run_time = timeit.default_timer() - startup_timer
    # logger.info("Input parse time: {time:.1f} ms".format(time=run_time*1000))

    return dict_inputs
