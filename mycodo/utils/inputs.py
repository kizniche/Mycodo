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

import os


def parse_input_information():
    logger = logging.getLogger("mycodo.input_parser")
    excluded_files = ['__init__.py', 'dummy_input.py', 'parse_inputs.py', '__pycache__']
    input_path = '/var/mycodo-root/mycodo/inputs/custom_inputs'
    real_path = os.path.realpath(input_path)

    dict_inputs = {}

    for each_file in os.listdir(real_path):
        if each_file not in excluded_files:

            full_path = "{}/{}".format(real_path, each_file)


            spec = importlib.util.spec_from_file_location('module.name', full_path)
            input_custom = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(input_custom)

            logger.info("Found input: {}, {}".format(input_custom.INPUT_INFORMATION['unique_name_input'], full_path))

            # Populate dictionary of input information
            if input_custom.INPUT_INFORMATION['unique_name_input'] in dict_inputs:
                logger.error("Error: Cannot add input modules because it does not have a unique name: {name}".format(
                    name=input_custom.INPUT_INFORMATION['unique_name_input']))
            else:
                dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']] = {}

            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['common_name_input'] = \
                input_custom.INPUT_INFORMATION['common_name_input']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['common_name_measurements'] = \
                input_custom.INPUT_INFORMATION['common_name_measurements']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['unique_name_measurements'] = \
                input_custom.INPUT_INFORMATION['unique_name_measurements']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['input_manufacturer'] = \
                input_custom.INPUT_INFORMATION['input_manufacturer']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['input_model'] = \
                input_custom.INPUT_INFORMATION['input_model']

            # Dependencies
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['dependencies_pypi'] = \
                input_custom.INPUT_INFORMATION['dependencies_pypi']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['dependencies_github'] = \
                input_custom.INPUT_INFORMATION['dependencies_github']

            # Interface
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['interfaces'] = \
                input_custom.INPUT_INFORMATION['interfaces']

            # I2C
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['i2c_location'] = \
                input_custom.INPUT_INFORMATION['i2c_location']

            # UART
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['uart_location'] = \
                input_custom.INPUT_INFORMATION['uart_location']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['baud_rate'] = \
                input_custom.INPUT_INFORMATION['baud_rate']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_cs'] = \
                input_custom.INPUT_INFORMATION['pin_cs']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_miso'] = \
                input_custom.INPUT_INFORMATION['pin_miso']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_mosi'] = \
                input_custom.INPUT_INFORMATION['pin_mosi']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['pin_clock'] = \
                input_custom.INPUT_INFORMATION['pin_clock']

            # Analog-to-digital converter
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['adc_measure'] = \
                input_custom.INPUT_INFORMATION['adc_measure']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['adc_measure_units'] = \
                input_custom.INPUT_INFORMATION['adc_measure_units']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['convert_to_unit'] = \
                input_custom.INPUT_INFORMATION['convert_to_unit']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['adc_volts_min'] = \
                input_custom.INPUT_INFORMATION['adc_volts_min']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['adc_volts_max'] = \
                input_custom.INPUT_INFORMATION['adc_volts_max']


            # Misc
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['period'] = \
                input_custom.INPUT_INFORMATION['period']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['cmd_command'] = \
                input_custom.INPUT_INFORMATION['cmd_command']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['cmd_measurement'] = \
                input_custom.INPUT_INFORMATION['cmd_measurement']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['cmd_measurement_units'] = \
                input_custom.INPUT_INFORMATION['cmd_measurement_units']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['resolution'] = \
                input_custom.INPUT_INFORMATION['resolution']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['resolution_2'] = \
                input_custom.INPUT_INFORMATION['resolution_2']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['sensitivity'] = \
                input_custom.INPUT_INFORMATION['sensitivity']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['thermocouple_type'] = \
                input_custom.INPUT_INFORMATION['thermocouple_type']
            dict_inputs[input_custom.INPUT_INFORMATION['unique_name_input']]['ref_ohm'] = \
                input_custom.INPUT_INFORMATION['ref_ohm']


    return dict_inputs
