# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_PT1000',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas PT-1000',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/temperature/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/EZO_RTD_Datasheet.pdf',

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
    'i2c_location': ['0x66'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0'
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the PT1000's temperature """

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

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def get_measurement(self):
        """ Gets the Atlas PT1000's temperature in Celsius """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        temp = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            temp_status, temp_list = self.atlas_device.query('R')
            if temp_list:
                self.logger.debug("Returned list: {lines}".format(lines=temp_list))

            # Find float value in list
            float_value = None
            for each_split in temp_list:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in temp_list:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                temp = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=temp))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=temp_list))

        # Read sensor via I2C
        elif self.interface == 'I2C':
            temp_status, temp_str = self.atlas_device.query('R')
            if temp_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(err=temp_str))
            elif temp_status == 'success':
                temp = float(temp_str)

        if temp == -1023:  # Erroneous measurement
            return

        self.value_set(0, temp)

        return self.return_dict
