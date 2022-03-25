# coding=utf-8
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude

# Measurements
measurements_dict = {
    0: {
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    2: {
        'measurement': 'altitude',
        'unit': 'm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BMP180',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BMP180',
    'input_library': 'Adafruit_BMP',
    'measurements_name': 'Pressure/Temperature',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'https://ae-bst.resource.bosch.com/media/_tech/media/product_flyer/BST-BMP180-FL000.pdf',

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
        ('pip-pypi', 'Adafruit_BMP', 'Adafruit-BMP==1.5.4'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x77'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BMP 180/085's humidity,
    temperature, and pressure, then calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from Adafruit_BMP import BMP085

        self.sensor = BMP085.BMP085(busnum=self.input_dev.i2c_bus)

    def get_measurement(self):
        """Gets the measurement in units by reading the BMP180/085"""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        time.sleep(2)

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_pressure())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_temperature())

        if self.is_enabled(0):
            self.value_set(2, calculate_altitude(self.value_get(0)))

        return self.return_dict
