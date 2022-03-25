# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Object'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Die'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MAX31855',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31855',
    'input_library': 'Adafruit_MAX31855',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31855.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/MAX31855.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/269',

    'options_enabled': [
        'pin_clock',
        'pin_cs',
        'pin_miso',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_MAX31855', 'git+https://github.com/adafruit/Adafruit_Python_MAX31855.git'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3')
    ],

    'interfaces': ['UART'],
    'pin_cs': 8,
    'pin_miso': 9,
    'pin_clock': 11
}


class InputModule(AbstractInput):
    """A sensor support class that measures the MAX31855's temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import Adafruit_MAX31855.MAX31855 as MAX31855

        self.sensor = MAX31855.MAX31855(
            self.input_dev.pin_clock,
            self.input_dev.pin_cs,
            self.input_dev.pin_miso)

    def get_measurement(self):
        """Gets the measurement in units by reading the."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.readTempC())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.readInternalC())

        return self.return_dict
