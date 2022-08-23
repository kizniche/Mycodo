# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADT7410',
    'input_manufacturer': 'Analog Devices',
    'input_name': 'ADT7410',
    'input_library': 'Adafruit_CircuitPython_ADT7410',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'https://www.analog.com/media/en/technical-documentation/data-sheets/ADT7410.pdf',
    'url_product_purchase': 'https://www.analog.com/en/products/adt7410.html',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_adt7410', 'adafruit-circuitpython-adt7410==1.2.5')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49', '0x4a', '0x4b'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """A sensor support class for the ADT7410"""

    def __init__(self, input_dev,  testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import adafruit_adt7410
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_adt7410.ADT7410(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))
        self.sensor.high_resolution = True

    def get_measurement(self):
        """Gets the ADT7410 measurements and stores them in the database."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        temperature = self.sensor.temperature
        self.logger.debug("Temperature: {} C".format(temperature))
        self.value_set(0, temperature)

        return self.return_dict
