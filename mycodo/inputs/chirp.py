# coding=utf-8
import logging
import time

from smbus2 import SMBus

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

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
    'measurements_name': 'Light/Moisture/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': True
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the Chirp's moisture, temperature
    and light

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.bus = SMBus(self.i2c_bus)
            self.filter_average('lux', init_max=3)

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.set_value(0, self.filter_average('lux', measurement=self.light()))

        if self.is_enabled(1):
            self.set_value(1, self.moist())

        if self.is_enabled(2):
            self.set_value(2, self.temp() / 10.0)

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
        self.reset()
        # self.address = new_addr

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
