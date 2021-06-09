# coding=utf-8
import copy

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.constraints_pass import constraints_pass_percent


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
    'input_name': 'Atlas Color',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'RGB, CIE, LUX, Proximity',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/ezo-rgb/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/EZO_RGB_Datasheet.pdf',

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
    'i2c_location': ['0x70'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0',
    
    'custom_options': [
        {
            'id': 'led_only_while_reading',
            'type': 'bool',
            'default_value': True,
            'name': 'LED Only For Measure',
            'phrase': 'Turn the LED on only during the measurement'
        },
        {
            'id': 'led_percentage',
            'type': 'integer',
            'default_value': 30,
            'constraints_pass': constraints_pass_percent,
            'name': 'LED Percentage',
            'phrase': 'What percentage of power to supply to the LEDs during measurement'
        },
        {
            'id': 'gamma_correction',
            'type': 'float',
            'default_value': 1.0,
            'constraints_pass': constraints_pass_gamma,
            'name': 'Gamma Correction',
            'phrase': 'Gamma correction between 0.01 and 4.99 (default is 1.0)'
        },
    ],

    'custom_actions': [
        {
            'type': 'message',
            'default_value': 'The EZO-RGB color sensor is designed to be calibrated to a white '
                             'object at the maximum brightness the object will be viewed under. '
                             'In order to get the best results, Atlas Scientific strongly '
                             'recommends that the sensor is mounted into a fixed location. Holding '
                             'the sensor in your hand during calibration will decrease performance.'
                             '<br>1. Embed the EZO-RGB color sensor into its intended use location.'
                             '<br>2. Set LED brightness to the desired level.'
                             '<br>3. Place a white object in front of the target object and press '
                             'the Calibration button.'
                             '<br>4. A single color reading will be taken and the device will be '
                             'fully calibrated.'
        },
        {
            'id': 'calibrate',
            'type': 'button',
            'name': lazy_gettext('Calibrate')
        },
        {
            'type': 'message',
            'default_value': """The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address."""
        },
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x70',
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
    """A sensor support class that monitors the Atlas Scientific sensor"""
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None
        self.enabled_rgb = False

        self.led_only_while_reading = None
        self.led_percentage = None
        self.gamma_correction = None

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
        if self.led_only_while_reading and self.led_percentage:
            self.atlas_device.query('L,{},T'.format(self.led_percentage))

        if self.gamma_correction:
            self.atlas_device.query('G,{}'.format(self.gamma_correction))

        if self.is_enabled(0) or self.is_enabled(1) or self.is_enabled(2):
            self.enabled_rgb = True
            self.atlas_device.query('O,RGB,1')
        else:
            self.atlas_device.query('O,RGB,0')

        if self.is_enabled(3) or self.is_enabled(4) or self.is_enabled(5):
            self.atlas_device.query('O,CIE,1')
        else:
            self.atlas_device.query('O,CIE,0')

        if self.is_enabled(6):
            self.atlas_device.query('O,LUX,1')
        else:
            self.atlas_device.query('O,LUX,0')

        if self.is_enabled(7):
            self.atlas_device.query('O,PROX,1')
        else:
            self.atlas_device.query('O,PROX,0')

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def get_measurement(self):
        """ Gets the sensor's Electrical Conductivity measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        return_string = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            rgb_status, rgb_list = self.atlas_device.query('R')
            if rgb_list:
                self.logger.debug("Returned list: {lines}".format(lines=rgb_list))

            # Check for "check probe"
            for each_split in rgb_list:
                if 'check probe' in each_split:
                    self.logger.error('"check probe" returned from sensor')
                    return

            # Find float value in list
            for each_split in rgb_list:
                if "," in each_split:
                    return_string = each_split
                    break

        # Read sensor via I2C
        elif self.interface == 'I2C':
            ec_status, return_string = self.atlas_device.query('R')
            if ec_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(err=return_string))
            elif ec_status == 'success':
                self.logger.debug('Value: {val}'.format(val=return_string))

        # Parse return string
        if ',' in return_string:
            index_place = 0
            return_list = return_string.split(',')
            if self.enabled_rgb:
                self.value_set(0, int(return_list[index_place]))
                self.value_set(1, int(return_list[index_place + 1]))
                self.value_set(2, int(return_list[index_place + 2]))
                index_place += 3
            if return_list[index_place] == 'P':
                self.value_set(7, int(return_list[index_place + 1]))
                index_place += 2
            if return_list[index_place] == 'Lux':
                self.value_set(6, int(return_list[index_place + 1]))
                index_place += 2
            if return_list[index_place] == 'xyY':
                self.value_set(3, float(return_list[index_place + 1]))
                self.value_set(4, float(return_list[index_place + 2]))
                self.value_set(5, int(return_list[index_place + 3]))

        return self.return_dict

    def calibrate(self, args_dict):
        self.atlas_device.query('Cal')

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
