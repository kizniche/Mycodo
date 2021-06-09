# coding=utf-8
import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'pressure',
        'unit': 'psi'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_EZO_PRESS',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas Pressure',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Pressure',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/pressure/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/EZO-PRS-Datasheet.pdf',

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
        ('pip-pypi', 'pylibftdi', 'pylibftdi==0.19.0')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x6a'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0',

    'custom_options': [
        {
            'id': 'led',
            'type': 'select',
            'default_value': 'on',
            'options_select': [
                ('on', lazy_gettext('Always On')),
                ('off', lazy_gettext('Always Off')),
                ('measure', lazy_gettext('Only On During Measure'))
            ],
            'name': lazy_gettext('LED Mode'),
            'phrase': lazy_gettext('When to turn the LED on')
        }
    ],

    'custom_actions_message':
        'The I2C address can be changed. Enter a new address in the 0xYY format '
        '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and '
        'change the I2C address option after setting the new address.',

    'custom_actions': [
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x6a',
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
    """ A sensor support class that acquires measurements from the sensor """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None

        self.led = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)
            if self.led == 'on':
                self.atlas_device.query('L,1')
            elif self.led == 'off':
                self.atlas_device.query('L,0')
        except Exception:
            self.logger.exception("Exception while initializing sensor")

    def get_measurement(self):
        """ Gets the Atlas Scientific pressure sensor measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        pressure = None
        self.return_dict = copy.deepcopy(measurements_dict)

        if self.led == 'measure':
            self.atlas_device.query('L,1')

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            press_status, press_list = self.atlas_device.query('R')
            if press_list:
                self.logger.debug("Returned list: {lines}".format(lines=press_list))

            # Find float value in list
            float_value = None
            for each_split in press_list:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in press_list:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                pressure = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=pressure))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=press_list))

        elif self.interface == 'I2C':
            pressure_status, pressure_str = self.atlas_device.query('R')
            if pressure_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(err=pressure_str))
            elif pressure_status == 'success':
                pressure = float(pressure_str)

        if self.led == 'measure':
            self.atlas_device.query('L,0')

        self.value_set(0, pressure)

        return self.return_dict

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
