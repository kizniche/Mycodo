# coding=utf-8
import copy
import time

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'lux'
    },
    1: {
        'measurement': 'light',
        "unit": "unitless",
        "name": "Ambient Light"
    },
    2: {
        "measurement": "light",
        "unit": "unitless",
        "name": "UV"
    },
    3: {
        "measurement": "light",
        "unit": "unitless",
        "name": "UV Index"
    },
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'LTR390',
    'input_manufacturer': 'LITE-ON',
    'input_name': 'LTR390',
    'input_library': 'adafruit-circuitpython-ltr390',
    'measurements_name': 'Light/UV',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'https://optoelectronics.liteon.com/upload/download/DS86-2015-0004/LTR-390UV_Final_%20DS_V1%201.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/4831',

    'options_enabled': [
        'i2c_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_ltr390', 'adafruit-circuitpython-ltr390==1.1.22')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x53'],
    'i2c_address_editable': False
}



class InputModule(AbstractInput):
    """A sensor support class that monitors the LTR390's lux/uv."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import adafruit_ltr390
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_ltr390.LTR390(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

    def get_measurement(self):
        """Gets the LTR390's lux."""
        self.return_dict = copy.deepcopy(measurements_dict)

        self.value_set(0, self.sensor.lux)
        self.value_set(1, self.sensor.light)
        self.value_set(2, self.sensor.uvs)
        self.value_set(3, self.sensor.uvi)

        return self.return_dict
