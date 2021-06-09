# coding=utf-8
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
    'input_name_unique': 'BMP280_2',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BMP280',
    'input_library': 'bmp280-python',
    'measurements_name': 'Pressure/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/pressure-sensors-bmp280-1.html',
    'url_datasheet': 'https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/2651',

    'message': 'This is similar to the other BMP280 Input, except it uses a different library, whcih includes the ability to set forced mode.',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1'),
        ('pip-pypi', 'bmp280', 'bmp280==0.0.3')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x76', '0x77'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'forced',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Forced Mode',
            'phrase': 'Enable heater to evaporate condensation. Turn on heater x seconds every y measurements.'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BMP280's humidity,
    temperature, and pressure, then calculates the altitude and dew point
    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.forced = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        from bmp280 import BMP280
        from smbus2 import SMBus

        self.sensor = BMP280(
            i2c_addr=int(str(self.input_dev.i2c_location), 16),
            i2c_dev=SMBus(self.input_dev.i2c_bus))

        if self.forced:
            self.sensor.setup(mode="forced")

    def get_measurement(self):
        """ Gets the measurement """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.get_pressure())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.get_temperature())

        if self.is_enabled(0):
            self.value_set(2, calculate_altitude(self.value_get(0)))

        return self.return_dict
