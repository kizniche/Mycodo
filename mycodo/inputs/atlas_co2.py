# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
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
        'measurement': 'co2',
        'unit': 'ppm'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_CO2',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas CO2',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://atlas-scientific.com/co2/',
    'url_datasheet': 'https://atlas-scientific.com/files/EZO_CO2_Datasheet.pdf',

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
    'i2c_location': ['0x69'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0'
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific CO2 sensor"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)
        except Exception:
            self.logger.exception("Exception while initializing sensor")

    def get_measurement(self):
        """ Gets the sensor's measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        co2 = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            co2_status, co2_list = self.atlas_device.query('R')
            self.logger.debug("Returned: {}".format(co2_list))

            # Find float value in list
            float_value = None
            for each_split in co2_list:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in co2_list:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                co2 = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=co2))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=co2_list))

        # Read sensor via I2C
        elif self.interface == 'I2C':
            co2_status, co2_str = self.atlas_device.query('R')
            self.logger.debug("Returned: {}".format(co2_str))
            if co2_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(err=co2_str))
            elif co2_status == 'success':
                if str_is_float(co2_str):
                    co2 = float(co2_str)
                else:
                    self.logger.error("Could not determine co2 from returned string: '{}'".format(co2_str))

        self.value_set(0, co2)

        return self.return_dict
