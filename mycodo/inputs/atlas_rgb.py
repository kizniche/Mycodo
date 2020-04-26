# coding=utf-8
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.calibration import AtlasScientificCommand
from mycodo.utils.system_pi import str_is_float


def constraints_pass_percentage(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is between 0 - 100
    if value < 0 or value > 100:
        all_passed = False
        errors.append("Must be >= 0 and <= 100")
    return all_passed, errors, mod_input

def constraints_pass_gamma(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is between 0 - 100
    if value > 4.99 or value < 0.01:
        all_passed = False
        errors.append("Must be >= 0.01 and <= 4.99")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'color_red',
        'unit': 'eight_bit_color'
    },
    1: {
        'measurement': 'color_green',
        'unit': 'eight_bit_color'
    },
    2: {
        'measurement': 'color_blue',
        'unit': 'eight_bit_color'
    },
    3: {
        'measurement': 'color_x',
        'unit': 'cie'
    },
    4: {
        'measurement': 'color_y',
        'unit': 'cie'
    },
    5: {
        'measurement': 'color_Y',
        'unit': 'cie'
    },
    6: {
        'measurement': 'light',
        'unit': 'lux'
    },
    7: {
        'measurement': 'length',
        'unit': 'cm'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_RGB',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'RGB Color',
    'measurements_name': 'RGB, CIE, LUX, Proximity',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'measurements_select',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x70'],
    'i2c_address_editable': True,
    'ftdi_location': '/dev/ttyUSB0',
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    
    'custom_options': [
        {
            'id': 'led_only_while_reading',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('LED Only For Measure'),
            'phrase': lazy_gettext('Turn the LED on only during the measurement')
        },
        {
            'id': 'led_percentage',
            'type': 'integer',
            'default_value': 30,
            'constraints_pass': constraints_pass_percentage,
            'name': lazy_gettext('LED Percentage'),
            'phrase': lazy_gettext('What percentage of power to supply to the LEDs during measurement')
        },
        {
            'id': 'gamma_correction',
            'type': 'float',
            'default_value': 1.0,
            'constraints_pass': constraints_pass_gamma,
            'name': lazy_gettext('Gamma Correction'),
            'phrase': lazy_gettext('Gamma correction between 0.01 and 4.99 (default is 1.0)')
        },
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.atlas_sensor = None
        self.enabled_rgb = False

        # Initialize custom option variables to None
        self.led_only_while_reading = None
        self.led_percentage = None
        self.gamma_correction = None

        # Set custom option variables to defaults or user-set values
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.input_dev = input_dev
            self.interface = input_dev.interface

            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

            if self.led_only_while_reading and self.led_percentage:
                self.atlas_sensor.query('L,{},T'.format(self.led_percentage))

            if self.gamma_correction:
                self.atlas_sensor.query('G,{}'.format(self.gamma_correction))

            if self.is_enabled(0) or self.is_enabled(1) or self.is_enabled(2):
                self.enabled_rgb = True
                self.atlas_sensor.query('O,RGB,1')
            else:
                self.atlas_sensor.query('O,RGB,0')

            if self.is_enabled(3) or self.is_enabled(4) or self.is_enabled(5):
                self.atlas_sensor.query('O,CIE,1')
            else:
                self.atlas_sensor.query('O,CIE,0')

            if self.is_enabled(6):
                self.atlas_sensor.query('O,LUX,1')
            else:
                self.atlas_sensor.query('O,LUX,0')

            if self.is_enabled(7):
                self.atlas_sensor.query('O,PROX,1')
            else:
                self.atlas_sensor.query('O,PROX,0')

            # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
            self.get_measurement()

    def initialize_sensor(self):
        from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        if self.interface == 'FTDI':
            self.ftdi_location = self.input_dev.ftdi_location
            self.atlas_sensor = AtlasScientificFTDI(self.ftdi_location)
        elif self.interface == 'UART':
            self.uart_location = self.input_dev.uart_location
            self.atlas_sensor = AtlasScientificUART(self.uart_location)
        elif self.interface == 'I2C':
            self.i2c_address = int(str(self.input_dev.i2c_location), 16)
            self.i2c_bus = self.input_dev.i2c_bus
            self.atlas_sensor = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)

    def get_measurement(self):
        """ Gets the sensor's Electrical Conductivity measurement via UART/I2C """
        return_string = None
        self.return_dict = measurements_dict.copy()

        # Read sensor via FTDI
        if self.interface == 'FTDI':
            if self.atlas_sensor.setup:
                lines = self.atlas_sensor.query('R')
                if lines:
                    self.logger.debug(
                        "All Lines: {lines}".format(lines=lines))

                    # 'check probe' indicates an error reading the sensor
                    if 'check probe' in lines:
                        self.logger.error(
                            '"check probe" returned from sensor')
                    # if a string resembling a float value is returned, this
                    # is out measurement value
                    elif str_is_float(lines[0]):
                        return_string = lines[0]
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=return_string))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            return_string = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            return_string = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=return_string))
            else:
                self.logger.error('FTDI device is not set up.'
                                  'Check the log for errors.')

        # Read sensor via UART
        elif self.interface == 'UART':
            if self.atlas_sensor.setup:
                lines = self.atlas_sensor.query('R')
                if lines:
                    self.logger.debug(
                        "All Lines: {lines}".format(lines=lines))

                    # 'check probe' indicates an error reading the sensor
                    if 'check probe' in lines:
                        self.logger.error(
                            '"check probe" returned from sensor')
                    # if a string resembling a float value is returned, this
                    # is out measurement value
                    elif str_is_float(lines[0]):
                        return_string = lines[0]
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=return_string))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            return_string = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            return_string = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=return_string))
            else:
                self.logger.error('UART device is not set up.'
                                  'Check the log for errors.')

        # Read sensor via I2C
        elif self.interface == 'I2C':
            if self.atlas_sensor.setup:
                ec_status, return_string = self.atlas_sensor.query('R')
                if ec_status == 'error':
                    self.logger.error(
                        "Sensor read unsuccessful: {err}".format(
                            err=return_string))
                elif ec_status == 'success':
                    self.logger.debug(
                        'Value: {val}'.format(val=return_string))
            else:
                self.logger.error(
                    'I2C device is not set up. Check the log for errors.')

        # Parse return string
        if ',' in return_string:
            index_place = 0
            return_list = return_string.split(',')
            if self.enabled_rgb:
                if self.is_enabled(0):
                    self.value_set(0, int(return_list[index_place + 0]))
                if self.is_enabled(1):
                    self.value_set(1, int(return_list[index_place + 1]))
                if self.is_enabled(2):
                    self.value_set(2, int(return_list[index_place + 2]))
                index_place += 3
            if return_list[index_place] == 'P':
                if self.is_enabled(7):
                    self.value_set(7, int(return_list[index_place + 1]))
                index_place += 2
            if return_list[index_place] == 'Lux':
                if self.is_enabled(6):
                    self.value_set(6, int(return_list[index_place + 1]))
                index_place += 2
            if return_list[index_place] == 'xyY':
                if self.is_enabled(3):
                    self.value_set(3, float(return_list[index_place + 1]))
                if self.is_enabled(4):
                    self.value_set(4, float(return_list[index_place + 2]))
                if self.is_enabled(5):
                    self.value_set(5, int(return_list[index_place + 3]))

        return self.return_dict
