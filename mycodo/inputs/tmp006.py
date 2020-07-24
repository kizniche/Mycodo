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
    'input_name_unique': 'TMP006',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'TMP006',
    'input_library': 'Adafruit_TMP',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'http://www.adafruit.com/datasheets/tmp006.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/1296',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_TMP', 'Adafruit_TMP')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40', '0x41', '0x42', '0x43', '0x44', '0x45', '0x46', '0x47'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TMP006's die and object temperatures """
    def __init__(self, input_dev,  testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        from Adafruit_TMP import TMP006

        self.sensor = TMP006.TMP006(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)

    def get_measurement(self):
        """ Gets the TMP006's temperature in Celsius """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        self.sensor.begin()

        if self.is_enabled(0):
            self.value_set(0, self.sensor.readObjTempC())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.readDieTempC())

        return self.return_dict
