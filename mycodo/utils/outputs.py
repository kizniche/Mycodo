# -*- coding: utf-8 -*-
#
#  outputs.py - Mycodo core utils
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
import logging
import os

from mycodo.config import PATH_OUTPUTS
from mycodo.config import PATH_OUTPUTS_CUSTOM
from mycodo.utils.modules import load_module_from_file

logger = logging.getLogger("mycodo.utils.outputs")


def parse_output_information(exclude_custom=False):
    """Parses the variables assigned in each Output and return a dictionary of IDs and values."""
    def dict_has_value(dict_inp, output_cus, key, force_type=None):
        if (key in output_cus.OUTPUT_INFORMATION and
                (output_cus.OUTPUT_INFORMATION[key] is not None)):
            if force_type == 'list':
                if isinstance(output_cus.OUTPUT_INFORMATION[key], list):
                    dict_inp[output_cus.OUTPUT_INFORMATION['output_name_unique']][key] = \
                        output_cus.OUTPUT_INFORMATION[key]
                else:
                    dict_inp[output_cus.OUTPUT_INFORMATION['output_name_unique']][key] = \
                        [output_cus.OUTPUT_INFORMATION[key]]
            else:
                dict_inp[output_cus.OUTPUT_INFORMATION['output_name_unique']][key] = \
                    output_cus.OUTPUT_INFORMATION[key]
        return dict_inp

    excluded_files = [
        '__init__.py', '__pycache__', 'base_output.py', 'custom_outputs',
        'examples', 'scripts', 'tmp_outputs'
    ]

    output_paths = [PATH_OUTPUTS]

    if not exclude_custom:
        output_paths.append(PATH_OUTPUTS_CUSTOM)

    dict_outputs = {}

    for each_path in output_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            if each_file in excluded_files:
                continue

            full_path = "{}/{}".format(real_path, each_file)
            output_custom, status = load_module_from_file(full_path, 'outputs')

            if not output_custom or not hasattr(output_custom, 'OUTPUT_INFORMATION'):
                continue

            # Populate dictionary of output information
            if output_custom.OUTPUT_INFORMATION['output_name_unique'] in dict_outputs:
                logger.error("Error: Cannot add output modules because it does not have a unique name: {name}".format(
                    name=output_custom.OUTPUT_INFORMATION['output_name_unique']))
            else:
                dict_outputs[output_custom.OUTPUT_INFORMATION['output_name_unique']] = {}

            dict_outputs[output_custom.OUTPUT_INFORMATION['output_name_unique']]['file_path'] = full_path

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'output_name')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'output_manufacturer')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'output_library')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'measurements_dict')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'channels_dict')

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'on_state_internally_handled')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'no_run')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'output_types')

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'execute_at_creation')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'execute_at_modification')

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'message')

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'url_datasheet', force_type='list')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'url_manufacturer', force_type='list')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'url_product_purchase', force_type='list')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'url_additional', force_type='list')

            # Dependencies
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'dependencies_module')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'dependencies_message')

            # Interface
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'interfaces')

            # Nonstandard (I2C, UART, etc.) location
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'location')

            # I2C
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'i2c_location')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'i2c_address_editable')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'i2c_address_default')

            # FTDI
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'ftdi_location')

            # UART
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'uart_location')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'uart_baud_rate')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'pin_cs')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'pin_miso')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'pin_mosi')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'pin_clock')

            # Bluetooth (BT)
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'bt_location')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'bt_adapter')

            # Which form options to display and whether each option is enabled
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'options_enabled')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'options_disabled')

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_options_message')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_options')

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_channel_options_message')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_channel_options')

            dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_commands_message')
            dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_commands')

    return dict_outputs


def outputs_on_off():
    outputs = []
    for each_output_type, output_data in parse_output_information().items():
        if 'output_types' in output_data and 'on_off' in output_data['output_types']:
            outputs.append(each_output_type)
    return outputs


def outputs_pwm():
    outputs = []
    for each_output_type, output_data in parse_output_information().items():
        if 'output_types' in output_data and 'pwm' in output_data['output_types']:
            outputs.append(each_output_type)
    return outputs


def outputs_value():
    outputs = []
    for each_output_type, output_data in parse_output_information().items():
        if 'output_types' in output_data and 'value' in output_data['output_types']:
            outputs.append(each_output_type)
    return outputs


def outputs_volume():
    outputs = []
    for each_output_type, output_data in parse_output_information().items():
        if 'output_types' in output_data and 'volume' in output_data['output_types']:
            outputs.append(each_output_type)
    return outputs


def output_types():
    return {
        'on_off': outputs_on_off(),
        'pwm': outputs_pwm(),
        'value': outputs_value(),
        'volume': outputs_volume()
    }
