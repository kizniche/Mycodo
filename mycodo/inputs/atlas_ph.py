# coding=utf-8
import time

import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import AtlasScientificCommand
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.system_pi import str_is_float


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'ion_concentration',
        'unit': 'pH'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_PH',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas pH',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Ion Concentration',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/ph/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/pH_EZO_Datasheet.pdf',

    'message': 'Calibration Measurement is an optional setting that provides a temperature measurement (in Celsius) of the water that the pH is being measured from.',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x63'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0',

    'custom_options': [
        {
            'id': 'temperature_comp_meas',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math'
            ],
            'name': lazy_gettext('Temperature Compensation Measurement'),
            'phrase': lazy_gettext('Select a measurement for temperature compensation')
        },
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Temperature Compensation Max Age'),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use for temperature compensation')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor pH"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None
        self.atlas_command = None

        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)

            if self.temperature_comp_meas_measurement_id:
                self.atlas_command = AtlasScientificCommand(
                    self.input_dev, sensor=self.atlas_device)
        except Exception:
            self.logger.exception("Exception while initializing sensor")

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def get_measurement(self):
        """ Gets the sensor's pH measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        ph = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Compensate measurement based on a temperature measurement
        if self.temperature_comp_meas_measurement_id and self.atlas_command:
            self.logger.debug("pH sensor set to calibrate temperature")

            last_measurement = self.get_last_measurement(
                self.temperature_comp_meas_device_id,
                self.temperature_comp_meas_measurement_id,
                max_age=self.max_age)

            if last_measurement:
                self.logger.debug("Latest temperature used to calibrate: {temp}".format(temp=last_measurement[1]))
                ret_value, ret_msg = self.atlas_command.calibrate('temperature', set_amount=last_measurement[1])
                time.sleep(0.5)
                self.logger.debug("Calibration returned: {val}, {msg}".format(val=ret_value, msg=ret_msg))
            else:
                self.logger.error("Calibration measurement not found within the past {} seconds".format(self.max_age))

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            ph_status, ph_list = self.atlas_device.query('R')
            if ph_list:
                self.logger.debug("Returned list: {lines}".format(lines=ph_list))

            # Find float value in list
            float_value = None
            for each_split in ph_list:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in ph_list:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                ph = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=ph))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=ph_list))

        # Read sensor via I2C
        elif self.interface == 'I2C':
            ph_status, ph_str = self.atlas_device.query('R')
            if ph_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(err=ph_str))
            elif ph_status == 'success':
                if ',' in ph_str and str_is_float(ph_str.split(',')[2]):
                    ph = float(ph_str.split(',')[2])
                elif str_is_float(ph_str):
                    ph = float(ph_str)
                else:
                    self.logger.error("Could not determine pH from returned string: '{}'".format(ph_str))

        self.value_set(0, ph)

        return self.return_dict
