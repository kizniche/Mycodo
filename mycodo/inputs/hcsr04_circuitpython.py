# coding=utf-8
import copy
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value

# Measurements
measurements_dict = {
    0: {
        'measurement': 'length',
        'unit': 'cm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HCSR04_CIRCUITPYTHON',
    'input_manufacturer': 'Multiple Manufacturers',
    'input_name': 'HC-SR04',
    'input_library': 'Adafruit_CircuitPython_HCSR04',
    'measurements_name': 'Ultrasonic Distance',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.cytron.io/p-5v-hc-sr04-ultrasonic-sensor',
    'url_datasheet': 'http://web.eece.maine.edu/~zhu/book/lab/HC-SR04%20User%20Manual.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/3942',
    'url_additional': 'https://learn.adafruit.com/ultrasonic-sonar-distance-sensors/python-circuitpython',

    'options_enabled': [
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libgpiod-dev', 'libgpiod-dev'),
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_hcsr04', 'adafruit-circuitpython-hcsr04==0.4.6')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'pin_trigger',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Trigger Pin',
            'phrase': 'Enter the GPIO Trigger Pin for your device (BCM numbering).'
        },
        {
            'id': 'pin_echo',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Echo Pin',
            'phrase': 'Enter the GPIO Echo Pin for your device (BCM numbering).'
        },
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that measures the HCSR04's temperature"""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.pin_trigger = None
        self.pin_echo = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import board
        import adafruit_hcsr04

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

        if self.pin_trigger and self.pin_echo:
            self.sensor = adafruit_hcsr04.HCSR04(
                trigger_pin=bcm_to_board[self.pin_trigger - 1],
                echo_pin=bcm_to_board[self.pin_echo - 1])
        else:
            self.logger.error("Must set trigger and enable pins")

    def get_measurement(self):
        """Gets the measurement."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        # try 3 times
        for _ in range(3):
            try:
                self.value_set(0, self.sensor.distance)
                return self.return_dict
            except Exception as err:
                self.logger.debug("Error: {}".format(err))
            time.sleep(0.5)
