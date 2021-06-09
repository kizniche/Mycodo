# coding=utf-8
import copy
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'dewpoint',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_EZO_HUMIDITY',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas Humidity',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://atlas-scientific.com/probes/humidity-sensor/',
    'url_datasheet': 'https://atlas-scientific.com/files/EZO-HUM-Datasheet.pdf',

    'options_enabled': [
        'measurements_select',
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
    'i2c_location': ['0x6f'],
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
            'phrase': 'When to turn the LED on'
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
            'default_value': '0x6f',
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

            if self.is_enabled(0):
                self.atlas_device.query('O,T,1')
            else:
                self.atlas_device.query('O,T,0')
            if self.is_enabled(1):
                self.atlas_device.query('O,HUM,1')
            else:
                self.atlas_device.query('O,HUM,0')
            if self.is_enabled(2):
                self.atlas_device.query('O,Dew,1')
            else:
                self.atlas_device.query('O,Dew,0')
        except Exception:
            self.logger.exception("Exception while initializing sensor")

    def get_measurement(self):
        """ Gets the Atlas Scientific humidity sensor measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        return_string = None
        self.return_dict = copy.deepcopy(measurements_dict)

        if self.led == 'measure':
            self.atlas_device.query('L,1')

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            hum_status, hum_list = self.atlas_device.query('R')
            if hum_list:
                self.logger.debug("Returned list: {lines}".format(
                    lines=hum_list))

            if 'check probe' in hum_list:
                self.logger.error('"check probe" returned from sensor')
                return

            # Find value(s) in list
            for each_split in hum_list:
                if "," in each_split or str_is_float(each_split):
                    return_string = each_split
                    break

        elif self.interface == 'I2C':
            hum_status, return_string = self.atlas_device.query('R')
            if hum_status == 'error':
                # try again
                time.sleep(1)
                hum_status, return_string = self.atlas_device.query('R')
                if hum_status == 'error':
                    self.logger.error("Sensor read unsuccessful (after 2 attempts): {err}".format(
                        err=return_string))
            if hum_status == 'success':
                self.logger.debug("Sensor returned: type: {}, value: {}".format(
                    type(return_string), return_string))

        if self.led == 'measure':
            self.atlas_device.query('L,0')

        self.logger.debug("Sensor returned: Type: {}, Value: {}".format(
            type(return_string), return_string))

        # Parse return string
        if ',' in return_string:
            index_place = 0
            return_list = return_string.split(',')
            if self.is_enabled(1):
                self.value_set(1, return_list[index_place])
                index_place += 1
            if self.is_enabled(0):
                self.value_set(0, return_list[index_place])
                index_place += 1
            if self.is_enabled(2):
                self.value_set(2, return_list[index_place + 1])
        elif self.is_enabled(0) and not self.is_enabled(1) and not self.is_enabled(2):
            self.value_set(0, return_string)
        elif not self.is_enabled(0) and self.is_enabled(1) and not self.is_enabled(2):
            self.value_set(1, return_string)

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
