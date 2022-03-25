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
    'input_name_unique': 'MAX31865_CIRCUITPYTHON',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31865',
    'input_library': 'Adafruit-CircuitPython-MAX31865',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31865.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/3328',

    'message': 'This module was added to allow support for multiple sensors to be connected at the same time, '
               'which the original MAX31865 module was not designed for.',

    'options_enabled': [
        'thermocouple_type',
        'ref_ohm',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'adafruit_max31865', 'adafruit-circuitpython-max31865==2.2.8')
    ],

    'interfaces': ['SPI'],

    'custom_options': [
        {
            'id': 'cs_pin',
            'type': 'integer',
            'default_value': 8,
            'name': 'Chip Select Pin',
            'phrase': 'Enter the GPIO Chip Select Pin for your device.'
        },
        {
            'id': 'wires',
            'type': 'select',
            'default_value': '2',
            'options_select': [
                ('2', '2 Wires'),
                ('3', '3 Wires'),
                ('4', '4 Wires')
            ],
            'name': 'Number of wires',
            'phrase': 'Select the number of wires your thermocouple has.'
        },
    ],

    'thermocouple_type': [
        ('PT100', 'PT-100'),
        ('PT1000', 'PT-1000')
    ],
    'ref_ohm': 430
}


class InputModule(AbstractInput):
    """A sensor support class that measures the MAX31865's temperature"""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.thermocouple_type = None
        self.spi = None
        self.cs = None
        self.cs_pin = None
        self.wires = None
        self.ref_ohm = None
        self.rtd_nominal = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import busio
        import board
        import digitalio
        import adafruit_max31865

        bcm_to_board = [
            board.D1,
            board.D2,
            board.D3,
            board.D4,
            board.D5,
            board.D6,
            board.D7,
            board.D8,
            board.D9,
            board.D10,
            board.D11,
            board.D12,
            board.D13,
            board.D14,
            board.D15,
            board.D16,
            board.D17,
            board.D18,
            board.D19,
            board.D20,
            board.D21,
            board.D22,
            board.D23,
            board.D24,
            board.D25,
            board.D26,
            board.D27
        ]

        self.thermocouple_type = self.input_dev.thermocouple_type
        if self.thermocouple_type == 'PT100':
            self.rtd_nominal = 100
        elif self.thermocouple_type == 'PT1000':
            self.rtd_nominal = 1000

        self.ref_ohm = self.input_dev.ref_ohm

        self.spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        self.cs = digitalio.DigitalInOut(bcm_to_board[self.cs_pin - 1])

        self.sensor = adafruit_max31865.MAX31865(
            self.spi,
            self.cs,
            rtd_nominal=self.rtd_nominal,
            ref_resistor=self.ref_ohm,
            wires=int(self.wires))

    def get_measurement(self):
        """Gets the measurement in units by reading the"""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)
        self.value_set(0, self.sensor.temperature)
        return self.return_dict
