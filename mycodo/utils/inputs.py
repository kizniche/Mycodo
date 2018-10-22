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

logger = logging.getLogger("mycodo.input_parser")


def list_devices_using_interface(interface):
    """
    Generates a list of input devices that use a particular interface
    :param interface: string, can be 'GPIO', 'I2C', 'UART', 'BT', '1WIRE', 'Mycodo', 'RPi'
    :return: list of strings
    """
    def check(check_input, dict_all_inputs, check_interface):
        if ('interfaces' in dict_all_inputs[check_input] and
                check_interface in dict_all_inputs[check_input]['interfaces']):
            return True

    list_devices = []
    dict_inputs = parse_input_information()

    for each_input in dict_inputs:
        if (check(each_input, dict_inputs, interface) and
                each_input not in list_devices):
            list_devices.append(each_input)

    return list_devices


def list_analog_to_digital_converters():
    """Generates a list of input devices that are analog-to-digital converters"""
    list_adc = []
    dict_inputs = parse_input_information()
    for each_input in dict_inputs:
        if ('analog_to_digital_converter' in dict_inputs[each_input] and
                dict_inputs[each_input]['analog_to_digital_converter'] and
                each_input not in list_adc):
            list_adc.append(each_input)
    return list_adc


def load_module_from_file(path_file):
    spec = importlib.util.spec_from_file_location('module.name', path_file)
    input_custom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(input_custom)
    return input_custom


def parse_custom_option_values(inputs):
    custom_options_values = {}
    for each_input in inputs:
        custom_options_values[each_input.unique_id] = {}
        if each_input.custom_options:
            for each_option in each_input.custom_options.split(';'):
                option = each_option.split(',')[0]
                value = each_option.split(',')[1]
                custom_options_values[each_input.unique_id][option] = value

    return custom_options_values


def parse_input_information():
    """Parses the variables assigned in each Input and return a dictionary of IDs and values"""
    def dict_has_value(dict_inp, input_cus, key):
        if (key in input_cus.INPUT_INFORMATION and
                (input_cus.INPUT_INFORMATION[key] or
                 input_cus.INPUT_INFORMATION[key] == 0)):
            dict_inp[input_cus.INPUT_INFORMATION['input_name_unique']][key] = \
                input_cus.INPUT_INFORMATION[key]
        return dict_inp

    # Uncomment to enable timer
    # import timeit
    # startup_timer = timeit.default_timer()

    excluded_files = ['__init__.py', '__pycache__', 'base_input.py',
                      'custom_inputs', 'examples', 'tmp_inputs',
                      'sensorutils.py']

    path_inputs = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/inputs')
    path_custom_inputs = "{}/custom_inputs".format(path_inputs)

    input_paths = [path_inputs, path_custom_inputs]

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
                # logger.info("Found input: {}, {}".format(input_custom.INPUT_INFORMATION['input_name_unique'], full_path))

                # Populate dictionary of input information
                if input_custom.INPUT_INFORMATION['input_name_unique'] in dict_inputs:
                    logger.error("Error: Cannot add input modules because it does not have a unique name: {name}".format(
                        name=input_custom.INPUT_INFORMATION['input_name_unique']))
                else:
                    dict_inputs[input_custom.INPUT_INFORMATION['input_name_unique']] = {}

                dict_inputs[input_custom.INPUT_INFORMATION['input_name_unique']]['file_path'] = full_path

                dict_inputs = dict_has_value(dict_inputs, input_custom, 'input_name')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'measurements_name')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'measurements_list')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'input_manufacturer')

                # Dependencies
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'dependencies_module')
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
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_channels')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_channels_selected')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_gain')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_resolution')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_sample_speed')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_volts_min')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_volts_max')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_units_min')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_units_max')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_inverse_unit_scale')

                # Misc
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'period')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'sht_voltage')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'cmd_command')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution_2')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'sensitivity')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'thermocouple_type')
                dict_inputs = dict_has_value(dict_inputs, input_custom, 'ref_ohm')

                dict_inputs = dict_has_value(dict_inputs, input_custom, 'custom_options')

    # Uncomment to enable timer, also uncomment line at start of function
    # run_time = timeit.default_timer() - startup_timer
    # logger.info("Input parse time: {time:.1f} ms".format(time=run_time*1000))

    return dict_inputs
