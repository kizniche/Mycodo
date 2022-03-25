# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'full'
    },
    1: {
        'measurement': 'light',
        'unit': 'ir'
    },
    2: {
        'measurement': 'light',
        'unit': 'lux'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TSL2591',
    'input_manufacturer': 'AMS',
    'input_name': 'TSL2591',
    'input_library': 'maxlklaxl/python-tsl2591',
    'measurements_name': 'Light',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://ams.com/tsl25911',
    'url_datasheet': 'https://ams.com/documents/20143/36005/TSL2591_DS000338_6-00.pdf/090eb50d-bb18-5b45-4938-9b3672f86b80',
    'url_product_purchase': 'https://www.adafruit.com/product/1980',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'tsl2591', 'git+https://github.com/maxlklaxl/python-tsl2591.git')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x29'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the TSL2591's lux."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import tsl2591

        self.sensor = tsl2591.Tsl2591(
            i2c_bus=self.input_dev.i2c_bus,
            sensor_address=int(str(self.input_dev.i2c_location), 16))

    def get_measurement(self):
        """Gets the TSL2591's lux."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        full, ir = self.sensor.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)

        self.value_set(0, full)
        self.value_set(1, ir)

        if self.is_enabled(2) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(2, self.sensor.calculate_lux(self.value_get(0), self.value_get(1)))

        return self.return_dict
