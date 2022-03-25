# coding=utf-8
# From https://github.com/ControlEverythingCommunity/SHT25/blob/master/Python/SHT25.py
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

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
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SHT2x',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT2x',
    'input_library': 'smbus2',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': [
        'interface',
        'i2c_location'
    ],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
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
        super().__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            self.try_initialize()

    def initialize(self):
        from smbus2 import SMBus

        self.i2c_address = int(str(self.input_dev.i2c_location), 16)
        self.sht2x = SMBus(self.input_dev.i2c_bus)

    def get_measurement(self):
        """Gets the humidity and temperature."""
        if not self.sht2x:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

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

                if self.is_enabled(0):
                    self.value_set(0, temperature)

                if self.is_enabled(1):
                    self.value_set(1, humidity)

                if self.is_enabled(2) and self.is_enabled(0) and self.is_enabled(1):
                    self.value_set(2, calculate_dewpoint(self.value_get(0), self.value_get(1)))

                if self.is_enabled(3) and self.is_enabled(0) and self.is_enabled(1):
                    self.value_set(3, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

                return self.return_dict
            except Exception as e:
                self.logger.exception("Exception when taking a reading: {err}".format(err=e))

            # Send soft reset and try a second read
            self.sht2x.write_byte(self.i2c_address, 0xFE)
            time.sleep(0.1)
