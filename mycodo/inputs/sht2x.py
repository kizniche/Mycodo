# coding=utf-8
# From https://github.com/ControlEverythingCommunity/SHT25/blob/master/Python/SHT25.py
import logging
import time

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'temperature': {
        'C': {0: {}}
    },
    'humidity': {
        'percent': {0: {}}
    },
    'dewpoint': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SHT2x',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT2x',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT2x's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.sht2x")
        self._measurements = None

        if not testing:
            from smbus2 import SMBus
            self.logger = logging.getLogger(
                "mycodo.sht2x_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sht2x = SMBus(self.i2c_bus)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        return_dict = {
            'temperature': {
                'C': {}
            },
            'humidity': {
                'percent': {}
            },
            'dewpoint': {
                'C': {}
            }
        }

        dew_point = None
        humidity = None
        temperature = None

        for _ in range(2):
            try:
                # Send temperature measurement command
                # 0xF3(243) NO HOLD master
                self.sht2x.write_byte(self.i2c_address, 0xF3)
                time.sleep(0.5)
                # Read data back, 2 bytes
                # Temp MSB, Temp LSB
                data0 = self.sht2x.read_byte(self.i2c_address)
                data1 = self.sht2x.read_byte(self.i2c_address)
                temperature = -46.85 + (((data0 * 256 + data1) * 175.72) / 65536.0)
                # Send humidity measurement command
                # 0xF5(245) NO HOLD master
                self.sht2x.write_byte(self.i2c_address, 0xF5)
                time.sleep(0.5)
                # Read data back, 2 bytes
                # Humidity MSB, Humidity LSB
                data0 = self.sht2x.read_byte(self.i2c_address)
                data1 = self.sht2x.read_byte(self.i2c_address)
                humidity = -6 + (((data0 * 256 + data1) * 125.0) / 65536.0)
                return dew_point, humidity, temperature
            except Exception as e:
                self.logger.exception(
                    "Exception when taking a reading: {err}".format(err=e))
            # Send soft reset and try a second read
            self.sht2x.write_byte(self.i2c_address, 0xFE)
            time.sleep(0.1)

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = temperature

        if self.is_enabled('humidity', 'percent', 0):
            return_dict['humidity']['percent'][0] = humidity

        if self.is_enabled('dewpoint', 'C', 0):
            return_dict['dewpoint']['C'][0] = calculate_dewpoint(
                temperature, humidity)

        return return_dict
