# coding=utf-8
import copy
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'lux'
    },
    1: {
        'measurement': 'moisture',
        'unit': 'unitless'
    },
    2: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'CHIRP',
    'input_manufacturer': 'Catnip Electronics',
    'input_name': 'Chirp',
    'input_library': 'smbus2',
    'measurements_name': 'Light/Moisture/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://wemakethings.net/chirp/',
    'url_product_purchase': 'https://www.tindie.com/products/miceuz/chirp-plant-watering-alarm/',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': True,

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address."""
        },
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x20',
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
    """
    A sensor support class that measures the Chirp's moisture, temperature
    and light

    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.i2c_address = None
        self.bus = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from smbus2 import SMBus

        self.i2c_address = int(str(self.input_dev.i2c_location), 16)
        self.bus = SMBus(self.input_dev.i2c_bus)
        self.filter_average('lux', init_max=3)

    def get_measurement(self):
        """Gets the light, moisture, and temperature."""
        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.filter_average('lux', measurement=self.light()))

        if self.is_enabled(1):
            self.value_set(1, self.moist())

        if self.is_enabled(2):
            self.value_set(2, self.temp() / 10.0)

        return self.return_dict

    def get_reg(self, reg):
        # read 2 bytes from register
        val = self.bus.read_word_data(self.i2c_address, reg)
        # return swapped bytes (they come in wrong order)
        return (val >> 8) + ((val & 0xFF) << 8)

    def reset(self):
        # To reset the sensor, write 6 to the device I2C address
        self.bus.write_byte(self.i2c_address, 6)

    def set_addr(self, new_addr):
        # To change the I2C address of the sensor, write a new address
        # (one byte [1..127]) to register 1; the new address will take effect after reset
        self.bus.write_byte_data(self.i2c_address, 1, new_addr)
        # second request is required since FW 0x26 to protect against spurious address changes
        self.bus.write_byte_data(self.i2c_address, 1, new_addr)
        self.reset()
        self.i2c_address = new_addr

    def moist(self):
        # To read soil moisture, read 2 bytes from register 0
        return self.get_reg(0)

    def temp(self):
        # To read temperature, read 2 bytes from register 5
        return self.get_reg(5)

    def light(self):
        # To read light level, start measurement by writing 3 to the
        # device I2C address, wait for 3 seconds, read 2 bytes from register 4
        self.bus.write_byte(self.i2c_address, 3)
        time.sleep(1.5)
        lux = self.get_reg(4)
        if lux == 0:
            return 65535.0
        else:
            return(1 - (lux / 65535.0)) * 65535.0

    def set_i2c_address(self, args_dict):
        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            self.set_addr(i2c_address)
        except:
            self.logger.exception("Exception changing I2C address")
