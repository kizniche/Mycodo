# coding=utf-8
import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

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
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HTU21D_CIRCUITPYTHON',
    'input_manufacturer': 'TE Connectivity',
    'input_name': 'HTU21D',
    'input_library': 'Adafruit_CircuitPython_HTU21D',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.te.com/usa-en/product-CAT-HSC0004.html',
    'url_datasheet': 'https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FHPC199_6%7FA6%7Fpdf%7FEnglish%7FENG_DS_HPC199_6_A6.pdf%7FCAT-HSC0004',
    'url_product_purchase': 'https://www.adafruit.com/product/1899',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ("pip-pypi", "adafruit_extended_bus", "Adafruit-extended-bus==1.0.2"),
        ("pip-pypi", "adafruit_htu21d", "adafruit-circuitpython-HTU21D==0.11.0"),
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'temperature_offset',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext("Temperature Offset"),
            'phrase': "The temperature offset (degrees Celsius) to apply"
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the HTU21D's humidity and temperature
    and calculates the dew point
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.i2c_address = 0x40  # HTU21D-F Address

        self.temperature_offset = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import adafruit_htu21d
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_htu21d.HTU21D(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=self.i2c_address,
        )

    def get_measurement(self):
        """Gets the humidity and temperature"""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.temperature + self.temperature_offset)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.relative_humidity)

        if self.is_enabled(2) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(2, calculate_dewpoint(self.value_get(0), self.value_get(1)))

        if self.is_enabled(3) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(3, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

        return self.return_dict
