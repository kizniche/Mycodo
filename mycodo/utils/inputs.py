# -*- coding: utf-8 -*-
#
#  inputs.py - Mycodo core utils
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

from mycodo.config import PATH_INPUTS
from mycodo.config import PATH_INPUTS_CUSTOM
from mycodo.inputs.sensorutils import convert_units
from mycodo.utils.modules import load_module_from_file

logger = logging.getLogger("mycodo.utils.inputs")


def parse_measurement(
        conversion,
        measurement,
        measurements_record,
        each_channel,
        each_measurement,
        timestamp=None):
    # Unscaled, unconverted measurement
    measurements_record[each_channel] = {
        'measurement': each_measurement['measurement'],
        'unit': each_measurement['unit'],
        'value': each_measurement['value'],
        'timestamp_utc': timestamp
    }

    # Scaling needs to come before conversion
    # Scale measurement
    if (measurement.rescaled_measurement and
            measurement.rescaled_unit):
        scaled_value = measurements_record[each_channel] = rescale_measurements(
            measurement, measurements_record[each_channel]['value'])
        measurements_record[each_channel] = {
            'measurement': measurement.rescaled_measurement,
            'unit': measurement.rescaled_unit,
            'value': scaled_value,
            'timestamp_utc': timestamp
        }

    # Convert measurement
    if measurement.conversion_id not in ['', None] and 'value' in each_measurement:
        converted_value = convert_units(
            measurement.conversion_id,
            measurements_record[each_channel]['value'])
        measurements_record[each_channel] = {
            'measurement': None,
            'unit': conversion.convert_unit_to,
            'value': converted_value,
            'timestamp_utc': timestamp
        }
    return measurements_record


def rescale_measurements(measurement, measurement_value):
    """Rescale measurement."""
    rescaled_measurement = None
    try:
        if measurement.rescale_method == "linear":
            # Get the difference between min and max volts
            diff_voltage = abs(
                float(measurement.scale_from_max) - float(measurement.scale_from_min))

            # Ensure the value stays within the min/max bounds
            if measurement_value < float(measurement.scale_from_min):
                measured_voltage = measurement.scale_from_min
            elif measurement_value > float(measurement.scale_from_max):
                measured_voltage = float(measurement.scale_from_max)
            else:
                measured_voltage = measurement_value

            # Calculate the percentage of the difference
            percent_diff = ((measured_voltage - float(measurement.scale_from_min)) /
                            diff_voltage)

            # Get the units difference between min and max units
            diff_units = abs(float(measurement.scale_to_max) - float(measurement.scale_to_min))

            # Calculate the measured units from the percent difference
            if measurement.invert_scale:
                converted_units = (float(measurement.scale_to_max) -
                                   (diff_units * percent_diff))
            else:
                converted_units = (float(measurement.scale_to_min) +
                                   (diff_units * percent_diff))

            # Ensure the units stay within the min/max bounds
            if converted_units < float(measurement.scale_to_min):
                rescaled_measurement = float(measurement.scale_to_min)
            elif converted_units > float(measurement.scale_to_max):
                rescaled_measurement = float(measurement.scale_to_max)
            else:
                rescaled_measurement = converted_units

        elif measurement.rescale_method == "equation":
            replaced_str = measurement.rescale_equation.replace('x', str(measurement_value))
            rescaled_measurement = eval(replaced_str)

        if rescaled_measurement:
            return rescaled_measurement

    except Exception as except_msg:
        logger.exception(
            "Error while attempting to rescale measurement: {err}".format(
                err=except_msg))


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
    """Generates a list of input devices that are analog-to-digital converters."""
    list_adc = []
    dict_inputs = parse_input_information()
    for each_input in dict_inputs:
        if ('analog_to_digital_converter' in dict_inputs[each_input] and
                dict_inputs[each_input]['analog_to_digital_converter'] and
                each_input not in list_adc):
            list_adc.append(each_input)
    return list_adc


def parse_input_information(exclude_custom=False):
    """Parses the variables assigned in each Input and return a dictionary of IDs and values."""
    def dict_has_value(dict_inp, input_cus, key, force_type=None):
        if (key in input_cus.INPUT_INFORMATION and
                (input_cus.INPUT_INFORMATION[key] or
                 input_cus.INPUT_INFORMATION[key] == 0)):
            if force_type == 'list':
                if isinstance(input_cus.INPUT_INFORMATION[key], list):
                    dict_inp[input_cus.INPUT_INFORMATION['input_name_unique']][key] = \
                        input_cus.INPUT_INFORMATION[key]
                else:
                    dict_inp[input_cus.INPUT_INFORMATION['input_name_unique']][key] = \
                        [input_cus.INPUT_INFORMATION[key]]
            else:
                dict_inp[input_cus.INPUT_INFORMATION['input_name_unique']][key] = \
                    input_cus.INPUT_INFORMATION[key]
        return dict_inp

    excluded_files = [
        '__init__.py', '__pycache__', 'base_input.py', 'custom_inputs',
        'examples', 'scripts', 'tmp_inputs', 'sensorutils.py'
    ]

    input_paths = [PATH_INPUTS]

    if not exclude_custom:
        input_paths.append(PATH_INPUTS_CUSTOM)

    dict_inputs = {}

    for each_path in input_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            if each_file in excluded_files:
                continue

            full_path = "{}/{}".format(real_path, each_file)
            input_custom, status = load_module_from_file(full_path, 'inputs')

            if not input_custom or not hasattr(input_custom, 'INPUT_INFORMATION'):
                continue

            # Populate dictionary of input information
            if input_custom.INPUT_INFORMATION['input_name_unique'] in dict_inputs:
                logger.error("Error: Cannot add input modules because it does not have a unique name: {name}".format(
                    name=input_custom.INPUT_INFORMATION['input_name_unique']))
            else:
                dict_inputs[input_custom.INPUT_INFORMATION['input_name_unique']] = {}

            dict_inputs[input_custom.INPUT_INFORMATION['input_name_unique']]['file_path'] = full_path

            dict_inputs = dict_has_value(dict_inputs, input_custom, 'input_manufacturer')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'input_name')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'input_name_short')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'input_library')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'measurements_name')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'measurements_dict')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'channels_dict')

            dict_inputs = dict_has_value(dict_inputs, input_custom, 'measurements_variable_amount')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'channel_quantity_same_as_measurements')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'measurements_use_same_timestamp')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'measurements_rescale')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'do_not_run_periodically')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'edge_input')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'message')

            dict_inputs = dict_has_value(dict_inputs, input_custom, 'url_datasheet', force_type='list')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'url_manufacturer', force_type='list')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'url_product_purchase', force_type='list')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'url_additional', force_type='list')

            # Dependencies
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'dependencies_module')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'dependencies_message')

            dict_inputs = dict_has_value(dict_inputs, input_custom, 'enable_channel_unit_select')

            # Interfaces
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'interfaces')

            # Nonstandard (I2C, UART, etc.) location
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'location')

            # I2C
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'i2c_location')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'i2c_address_editable')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'i2c_address_default')

            # FTDI
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'ftdi_location')

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
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_gain')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_resolution')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'adc_sample_speed')

            # Misc
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'period')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'sht_voltage')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'cmd_command')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'resolution_2')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'sensitivity')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'thermocouple_type')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'ref_ohm')

            dict_inputs = dict_has_value(dict_inputs, input_custom, 'execute_at_creation')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'execute_at_modification')

            dict_inputs = dict_has_value(dict_inputs, input_custom, 'custom_options_message')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'custom_options')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'custom_channel_options')

            dict_inputs = dict_has_value(dict_inputs, input_custom, 'custom_commands_message')
            dict_inputs = dict_has_value(dict_inputs, input_custom, 'custom_commands')

    return dict_inputs
