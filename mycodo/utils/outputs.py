# -*- coding: utf-8 -*-
#
#  outputs.py - Mycodo core utils
#
#  Copyright (C) 2020  Kyle T. Gabriel
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


def parse_output_information():
    """Parses the variables assigned in each Output and return a dictionary of IDs and values"""
    def dict_has_value(dict_inp, output_cus, key, force_type=None):
        if (key in output_cus.OUTPUT_INFORMATION and
                (output_cus.OUTPUT_INFORMATION[key] or
                 output_cus.OUTPUT_INFORMATION[key] == 0)):
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

    output_paths = [PATH_OUTPUTS, PATH_OUTPUTS_CUSTOM]

    dict_outputs = {}

    for each_path in output_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            skip_file = False

            if each_file in excluded_files:
                skip_file = True

            if not skip_file:
                full_path = "{}/{}".format(real_path, each_file)
                output_custom = load_module_from_file(full_path, 'outputs')

                if not hasattr(output_custom, 'OUTPUT_INFORMATION'):
                    skip_file = True

            if not skip_file:
                # logger.info("Found output: {}, {}".format(
                #     output_custom.OUTPUT_INFORMATION['output_name_unique'],
                #     full_path))

                # Populate dictionary of output information
                if output_custom.OUTPUT_INFORMATION['output_name_unique'] in dict_outputs:
                    logger.error("Error: Cannot add output modules because it does not have a unique name: {name}".format(
                        name=output_custom.OUTPUT_INFORMATION['output_name_unique']))
                else:
                    dict_outputs[output_custom.OUTPUT_INFORMATION['output_name_unique']] = {}

                dict_outputs[output_custom.OUTPUT_INFORMATION['output_name_unique']]['file_path'] = full_path

                dict_outputs = dict_has_value(dict_outputs, output_custom, 'output_name')
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'output_library')

                dict_outputs = dict_has_value(dict_outputs, output_custom, 'on_state_internally_handled')
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'output_types')

                dict_outputs = dict_has_value(dict_outputs, output_custom, 'message')

                dict_outputs = dict_has_value(dict_outputs, output_custom, 'url_datasheet', force_type='list')
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'url_manufacturer', force_type='list')
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'url_product_purchase', force_type='list')

                # Dependencies
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'dependencies_module')
                
                # Interface
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'interfaces')

                # Nonstandard (I2C, UART, etc.) location
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'location')

                # I2C
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'i2c_location')
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'i2c_address_editable')

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

                dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_actions_message')
                dict_outputs = dict_has_value(dict_outputs, output_custom, 'custom_actions')

    return dict_outputs


def outputs_pwm():
    outputs_pwm = []
    for each_output_type, output_data in parse_output_information().items():
        if 'output_types' in output_data and 'pwm' in output_data['output_types']:
            outputs_pwm.append(each_output_type)
    return outputs_pwm
