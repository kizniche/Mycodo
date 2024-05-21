# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'AHTx0_CIRCUITPYTHON',
    'input_manufacturer': 'ASAIR',
    'input_name': 'AHTx0',
    'input_library': 'Adafruit_CircuitPython_AHTx0',
    'measurements_name': 'Temperature/Humidity',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'http://www.aosong.com/en/products-40.html',
    'url_datasheet': 'https://server4.eca.ir/eshop/AHT10/Aosong_AHT10_en_draft_0c.pdf',

    'options_enabled': [
        'i2c_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_ahtx0', 'adafruit-circuitpython-ahtx0==1.0.21')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x38'],
    'i2c_address_editable': False,
}


class InputModule(AbstractInput):
    """A sensor support class that measures."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import adafruit_ahtx0
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_ahtx0.AHTx0(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

    def get_measurement(self):
        """Gets the measurements."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.temperature)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.relative_humidity)

        return self.return_dict
