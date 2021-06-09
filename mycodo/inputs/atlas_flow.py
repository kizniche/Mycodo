# coding=utf-8
import time

import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import setup_atlas_device


def constraints_pass_rate(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['h', 'm', 's']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


def constraints_pass_meter_type(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['3/8', '1/4', '1/2', '3/4', 'non-atlas']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


def constraints_pass_resistor(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['atlas', '0', '1', '-1', '10', '-10', '100', '-100']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


def constraints_pass_custom_k_value_time_base(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['disabled', 'h', 'm', 's']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'volume',
        'unit': 'l'
    },
    1: {
        'measurement': 'rate_volume',
        'unit': 'l_min'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_FLOW',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas Flow Meter',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Total Volume, Flow Rate',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/flow/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/flow_EZO_Datasheet.pdf',

    'message': 'Set the Measurement Time Base to a value most appropriate for your anticipated flow (it will affect accuracy). This flow rate time base that is set and returned from the sensor will be converted to liters per minute, which is the default unit for this input module. If you desire a different rate to be stored in the database (such as liters per second or hour), then use the Convert to Unit option.',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'measurements_select',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi==0.19.0')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x68'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0',

    'custom_options': [
        {
            'id': 'flow_meter_type',
            'type': 'select',
            'default_value': '3/8',
            'options_select': [
                ('3/8', 'Atlas Scientific 3/8" Flow Meter'),
                ('1/4', 'Atlas Scientific 1/4" Flow Meter'),
                ('1/2', 'Atlas Scientific 1/2" Flow Meter'),
                ('3/4', 'Atlas Scientific 3/4" Flow Meter'),
                ('non-atlas', 'Non-Atlas Scientific Flow Meter')
            ],
            'constraints_pass': constraints_pass_meter_type,
            'name': 'Flow Meter Type',
            'phrase': 'Set the type of flow meter used'
        },
        {
            'id': 'flow_rate_unit',
            'type': 'select',
            'default_value': 'm',
            'options_select': [
                ('s', 'Liters per Second'),
                ('m', 'Liters per Minute'),
                ('h', 'Liters per Hour')
            ],
            'constraints_pass': constraints_pass_rate,
            'name': 'Atlas Meter Time Base',
            'phrase': 'If using an Atlas Scientific flow meter, set the flow rate/time base'
        },
        {
            'id': 'internal_resistor',
            'type': 'select',
            'default_value': 'atlas',
            'options_select': [
                ('atlas', 'Use Atlas Scientific Flow Meter'),
                ('0', 'Disable Internal Resistor'),
                ('1', '1 K Ω Pull-Up'),
                ('-1', '1 K Ω Pull-Down'),
                ('10', '10 K Ω Pull-Up'),
                ('-10', '10 K Ω Pull-Down'),
                ('100', '100 K Ω Pull-Up'),
                ('-100', '100 K Ω Pull-Down')
            ],
            'constraints_pass': constraints_pass_resistor,
            'name': lazy_gettext('Internal Resistor'),
            'phrase': 'Set an internal resistor for the flow meter'
        },
        {
            'id': 'custom_k_values',
            'type': 'text',
            'default_value': '',
            'name': 'Custom K Value(s)',
            'phrase': "If using a non-Atlas Scientific flow meter, enter the meter's K value(s). For a single K value, enter '[volume per pulse],[number of pulses]'. For multiple K values (up to 16), enter '[volume at frequency],[frequency in Hz];[volume at frequency],[frequency in Hz];...'. Leave blank to disable."
        },
        {
            'id': 'custom_k_value_time_base',
            'type': 'select',
            'default_value': 'disabled',
            'options_select': [
                ('disabled', 'Use Atlas Scientific Flow Meter'),
                ('s', 'Liters per Second'),
                ('m', 'Liters per Minute'),
                ('h', 'Liters per Hour')
            ],
            'constraints_pass': constraints_pass_custom_k_value_time_base,
            'name': 'K Value Time Base',
            'phrase': 'If using a non-Atlas Scientific flow meter, set the flow rate/time base for the custom K values entered.'
        },
    ],

    'custom_actions': [
        {
            'type': 'message',
            'default_value': """The total volume can be cleared with the following button or with a Function Action."""
        },
        {
            'id': 'clear_total_volume',
            'type': 'button',
            'name': lazy_gettext('Clear Total Volume')
        },
        {
            'type': 'message',
            'default_value': """The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address."""
        },
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x68',
            'name': lazy_gettext('New I2C Address'),
            'phrase': lazy_gettext('The new I2C to set the device to')
        },
        {
            'id': 'set_i2c_address',
            'type': 'button',
            'name': lazy_gettext('Set I2C Address')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor ElectricalConductivity"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None
        self.sensor_is_measuring = False
        self.sensor_is_clearing = False

        self.flow_meter_type = None
        self.flow_rate_unit = None
        self.internal_resistor = None
        self.custom_k_values = None
        self.custom_k_value_time_base = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)
            self.set_sensor_settings()
        except Exception:
            self.logger.exception("Exception while initializing sensor")

    def set_sensor_settings(self):
        if self.is_enabled(0):
            self.atlas_device.query('O,TV,1')
            self.logger.debug("Enabling Total Volume measurement")
        else:
            self.atlas_device.query('O,TV,0')
            self.logger.debug("Disabling Total Volume measurement")

        if self.is_enabled(1):
            self.atlas_device.query('O,FR,1')
            self.logger.debug("Enabling Flow Rate measurement")
        else:
            self.atlas_device.query('O,FR,0')
            self.logger.debug("Disabling Flow Rate measurement")

        if self.flow_meter_type:
            if self.flow_meter_type == 'non-atlas':
                if ';' in self.custom_k_values:
                    list_k_values = self.custom_k_values.split(';')
                    self.atlas_device.query('K,clear')
                    self.logger.debug("Cleared K Values")
                    for each_k in list_k_values:
                        if ',' in each_k:
                            self.atlas_device.query('K,{}'.format(each_k))
                            self.logger.debug("Set K Value: {}".format(each_k))
                        else:
                            self.logger.error(
                                "Improperly-formatted K-value: {}".format(each_k))
                elif ',' in self.custom_k_values:
                    self.atlas_device.query('K,clear')
                    self.logger.debug("Cleared K Values")
                    self.atlas_device.query('K,{}'.format(self.custom_k_values))
                    self.logger.debug("Set K Value: {}".format(self.custom_k_values))
                else:
                    self.logger.error(
                        "Improperly-formatted K-value: {}".format(
                            self.custom_k_values))
                self.atlas_device.query('Vp,{}'.format(self.custom_k_value_time_base))
                self.logger.debug("Set Custom Time Base: {}".format(
                    self.custom_k_value_time_base))
            else:
                self.atlas_device.query('Set,{}'.format(self.flow_meter_type))
                self.logger.debug("Set Flow Meter: {}".format(self.flow_meter_type))

        if self.flow_rate_unit:
            self.atlas_device.query('Frp,{}'.format(self.flow_rate_unit))
            self.logger.debug("Set Flow Rate: l/{}".format(self.flow_rate_unit))

        if self.internal_resistor and self.internal_resistor != 'atlas':
            self.atlas_device.query('P,{}'.format(int(self.internal_resistor)))
            if self.internal_resistor == '0':
                self.logger.debug("Internal Resistor disabled")
            else:
                self.logger.debug("Internal Resistor set: {} K".format(self.internal_resistor))

    def get_measurement(self):
        """ Gets the sensor's Electrical Conductivity measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        return_string = None
        self.return_dict = copy.deepcopy(measurements_dict)

        while self.sensor_is_clearing:
            time.sleep(0.1)
        self.sensor_is_measuring = True

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            flow_status, flow_list = self.atlas_device.query('R')
            if flow_list:
                self.logger.debug("Returned list: {lines}".format(lines=flow_list))

                # Check for "check probe"
                for each_split in flow_list:
                    if 'check probe' in each_split:
                        self.logger.error('"check probe" returned from sensor')
                        return

                # Find float value in list
                for each_split in flow_list:
                    if "," in each_split:
                        return_string = each_split
                        break

        # Read sensor via I2C
        elif self.interface == 'I2C':
            return_status, return_string = self.atlas_device.query('R')
            if return_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(
                    err=return_string))
            elif return_status == 'success':
                return_string = return_string

        self.sensor_is_measuring = False

        self.logger.debug("Raw Return String: {}".format(return_string))
        total_volume = None
        flow_rate_raw = None
        flow_rate = None

        if self.is_enabled(0) and self.is_enabled(1):
            return_list = return_string.split(',')
            total_volume = float(return_list[0])
            flow_rate_raw = float(return_list[1])
            flow_rate = self.convert_to_l_m(flow_rate_raw)
            self.value_set(0, total_volume)
            self.value_set(1, flow_rate)
        elif self.is_enabled(0) and not self.is_enabled(1):
            total_volume = float(return_string)
            self.value_set(0, total_volume)
        elif not self.is_enabled(0) and self.is_enabled(1):
            flow_rate_raw = float(return_string)
            flow_rate = self.convert_to_l_m(flow_rate_raw)
            self.value_set(1, flow_rate)

        if total_volume is not None:
            self.logger.debug("Total Volume: {} l".format(total_volume))
        if flow_rate_raw is not None:
            self.logger.debug(
                "Flow Rate (from sensor): {:.5f} l/{}".format(
                    flow_rate_raw, self.flow_rate_unit))
        if flow_rate is not None:
            self.logger.debug(
                "Flow Rate (converted to l/m): {:.5f} l/m".format(flow_rate))

        return self.return_dict

    def convert_to_l_m(self, amount):
        if (self.custom_k_value_time_base and
                self.custom_k_value_time_base != 'disabled'):
            # Custom K values used for non-Atlas Scientific meter
            # use the custom time base
            time_base_unit = self.custom_k_value_time_base
        else:
            # Use time base set for Atlas Scientific meter
            time_base_unit = self.flow_rate_unit

        if time_base_unit == 'h':
            return amount / 60
        elif time_base_unit == 'm':
            return amount
        elif time_base_unit == 's':
            return amount * 60

    def clear_total_volume(self, args_dict):
        while self.sensor_is_measuring:
            time.sleep(0.1)
        self.sensor_is_clearing = True
        self.logger.debug("Clearing total volume")
        return_status, return_string = self.atlas_device.query('Clear')
        self.sensor_is_clearing = False
        if return_status == 'error':
            return 1, "Error: {}".format(return_string)
        elif return_status == 'success':
            return 0, "Success"

    def set_i2c_address(self, args_dict):
        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            write_cmd = "I2C,{}".format(i2c_address)
            self.logger.debug("I2C Change command: {}".format(write_cmd))
            self.atlas_device.write(write_cmd)
        except:
            self.logger.exception("Exception changing I2C address")
