# coding=utf-8
import logging
import time

from smbus2 import SMBus

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import InputMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'light': {
        'lux': {0: {}}
    },
    'moisture': {
        'unitless': {0: {}}
    },
    'temperature': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'CHIRP',
    'input_manufacturer': 'Catnip Electronics',
    'input_name': 'Chirp',
    'measurements_name': 'Light/Moisture/Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
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
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.chirp")
        self._measurements = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.chirp_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.bus = SMBus(self.i2c_bus)
            self.filter_average('lux', init_max=3)

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        return_dict = {
            'light': {
                'lux': {}
            },
            'moisture': {
                'unitless': {}
            },
            'temperature': {
                'C': {}
            }
        }

        if self.is_enabled('light', 'lux', 0):
            return_dict['light']['lux'][0] = self.filter_average('lux', measurement=self.light())

        if self.is_enabled('moisture', 'unitless', 0):
            return_dict['moisture']['unitless'][0] = self.moist()

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = self.temp() / 10.0

        return return_dict

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
