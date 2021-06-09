# coding=utf-8
import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'acceleration_x',
        'unit': 'm_s_s'
    },
    1: {
        'measurement': 'acceleration_y',
        'unit': 'm_s_s'
    },
    2: {
        'measurement': 'acceleration_z',
        'unit': 'm_s_s'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADXL34x',
    'input_manufacturer': 'Analog Devices',
    'input_name': 'ADXL34x (343, 344, 345, 346)',
    'input_library': 'Adafruit_CircuitPython',
    'measurements_name': 'Acceleration',
    'measurements_dict': measurements_dict,
    'url_datasheet': [
        'https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL343.pdf',
        'https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL344.pdf',
        'https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL345.pdf',
        'https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL346.pdf'
    ],
    'url_product_purchase': [
        'https://www.analog.com/en/products/adxl343.html',
        'https://www.analog.com/en/products/adxl344.html',
        'https://www.analog.com/en/products/adxl345.html',
        'https://www.analog.com/en/products/adxl346.html'
    ],

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.1'),
        ('pip-pypi', 'adafruit_adxl34x', 'adafruit-circuitpython-adxl34x==1.11.7')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x53', '0x1d'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'range',
            'type': 'select',
            'default_value': '16',
            'options_select': [
                ('2', '±2 g (±19.6 m/s/s)'),
                ('4', '±4 g (±39.2 m/s/s)'),
                ('8', '±8 g (±78.4 m/s/s)'),
                ('16', '±16 g (±156.9 m/s/s)')
            ],
            'name': lazy_gettext('Range'),
            'phrase': 'Set the measurement range'
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class for the ADXL34x """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.range = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import adafruit_adxl34x
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_adxl34x.ADXL345(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

        if self.range == '2':
            self.sensor.range = adafruit_adxl34x.Range.RANGE_2_G
        elif self.range == '4':
            self.sensor.range = adafruit_adxl34x.Range.RANGE_4_G
        elif self.range == '8':
            self.sensor.range = adafruit_adxl34x.Range.RANGE_8_G
        elif self.range == '16':
            self.sensor.range = adafruit_adxl34x.Range.RANGE_16_G

    def get_measurement(self):
        """ Gets the ADXL34x measurements and stores them in the database """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        acceleration = self.sensor.acceleration
        self.logger.debug("Acceleration measurements: {}".format(acceleration))
        self.value_set(0, acceleration[0])
        self.value_set(1, acceleration[1])
        self.value_set(2, acceleration[2])

        return self.return_dict
