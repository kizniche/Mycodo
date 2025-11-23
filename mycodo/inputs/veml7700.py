# coding=utf-8
import copy
import time

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'lux'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'VEML7700',
    'input_manufacturer': 'VISHAY',
    'input_name': 'VEML7700',
    'input_library': 'adafruit-circuitpython-veml7700',
    'measurements_name': 'Light',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'https://www.vishay.com/docs/84286/veml7700.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/4162',

    'options_enabled': [
        'i2c_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_veml7700', 'adafruit-circuitpython-veml7700==2.2.0')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x10'],
    'i2c_address_editable': False
}



class InputModule(AbstractInput):
    """A sensor support class that monitors the DS18B20's lux."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import adafruit_veml7700
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_veml7700.VEML7700(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

    @property
    def lux(self):
        """VEML7700 luminosity in lux."""
        if self._measurements is None:  # update if needed
            self.read()
        return self._measurements

    def get_measurement(self):
        """Gets the VEML7700's lux."""
        self.return_dict = copy.deepcopy(measurements_dict)

        lux = self.sensor.light

        self.value_set(0, lux)

        return self.return_dict
