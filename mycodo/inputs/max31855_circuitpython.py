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
    'input_name_unique': 'MAX31855_CIRCUITPYTHON',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31855',
    'input_library': 'adafruit-circuitpython-max31855',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31855.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/MAX31855.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/269',   
    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],
    'dependencies_module': [
        ('pip-pypi', 'adafruit_max31855', 'adafruit-circuitpython-max31855==3.2.21')
    ],

    'interfaces': ['SPI'],

    'custom_options': [
        {
            'id': 'cs_pin',
            'type': 'integer',
            'default_value': 5,
            'name': 'Chip Select Pin',
            'phrase': 'Enter the GPIO Chip Select Pin for your device.'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that measures the MAX31855's temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.spi = None
        self.cs = None
        self.cs_pin = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import board
        import digitalio
        import adafruit_max31855
        
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
        
        self.spi = board.SPI()
        self.cs = digitalio.DigitalInOut(bcm_to_board[self.cs_pin - 1])
        
        self.sensor = adafruit_max31855.MAX31855(
            self.spi,
            self.cs)

    def get_measurement(self):
        """Gets the measurement in units by reading the."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.temperature)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.reference_temperature)

        return self.return_dict
