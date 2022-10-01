# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'uv'
    },
    1: {
        'measurement': 'light',
        'unit': 'visible'
    },
    2: {
        'measurement': 'light',
        'unit': 'ir'
    },
    3: {
        'measurement': 'length',
        'unit': 'cm'
    }
}

INPUT_INFORMATION = {
    'input_name_unique': 'SI1145',
    'input_manufacturer': 'Silicon Labs',
    'input_name': 'SI1145',
    'input_library': 'si1145',
    'measurements_name': 'Light (UV/Visible/IR), Proximity (cm)',
    'measurements_dict': measurements_dict,

    'url_manufacturer': 'https://learn.adafruit.com/adafruit-si1145-breakout-board-uv-ir-visible-sensor',
    'url_datasheet': 'https://www.silabs.com/support/resources.p-sensors_optical-sensors_si114x',
    'url_product_purchase': 'https://www.adafruit.com/product/1777',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'SI1145', 'SI1145==1.0.2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x60'],
    'i2c_address_editable': False
}

class InputModule(AbstractInput):
    """A sensor support class that measures the SI1145"""

    def __init__(self, input_dev, testing=False):  # generally reserved for defining variable default values

        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import SI1145.SI1145 as SI1145

        self.sensor = SI1145.SI1145(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.readUV())
        if self.is_enabled(1):
            self.value_set(1, self.sensor.readVisible())
        if self.is_enabled(2):
            self.value_set(2, self.sensor.readIR())
        if self.is_enabled(3):
            self.value_set(3, self.sensor.readProx())

        return self.return_dict
