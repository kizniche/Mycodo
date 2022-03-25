# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit

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
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    3: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    4: {
        'measurement': 'altitude',
        'unit': 'm'
    },
    5: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }

}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BME280_RPI_BME280',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME280',
    'input_library': 'RPi.bme280',
    'measurements_name': 'Pressure/Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.bosch-sensortec.com/bst/products/all_products/bme280',
    'url_datasheet': 'https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/2652',
        'https://www.sparkfun.com/products/13676'
    ],

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'bme280', 'RPi.bme280==0.2.3')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x76', '0x77'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.i2c_address = None
        self.i2c_bus = None
        self.bus = None
        self.calibration_params = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import smbus2
        import bme280

        self.i2c_address = int(str(self.input_dev.i2c_location), 16)
        self.i2c_bus = self.input_dev.i2c_bus
        self.bus = smbus2.SMBus(self.i2c_bus)
        self.calibration_params = bme280.load_calibration_params(self.bus, self.i2c_address)
        self.sensor = bme280

    def get_measurement(self):
        """Gets the measurement in units by reading the"""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        data = self.sensor.sample(self.bus, self.i2c_address, self.calibration_params)

        if self.is_enabled(0):
            self.value_set(0, data.temperature)

        if self.is_enabled(1):
            self.value_set(1, data.humidity)

        if self.is_enabled(2):
            self.value_set(2, convert_from_x_to_y_unit('hPa', 'Pa', data.pressure))

        if self.is_enabled(0) and self.is_enabled(1):
            self.value_set(3, calculate_dewpoint(self.value_get(0), self.value_get(1)))

        if self.is_enabled(2):
            self.value_set(4, calculate_altitude(self.value_get(2)))

        if self.is_enabled(0) and self.is_enabled(1):
            self.value_set(5, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

        return self.return_dict
