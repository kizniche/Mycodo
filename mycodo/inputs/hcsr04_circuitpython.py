# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

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
    'input_name': 'HCSR04',
    'input_library': 'Adafruit-CircuitPython-HCSR04',
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
        ('pip-pypi', 'usb.core', 'pyusb==1.0.2'),
        ('pip-pypi', 'adafruit_hcsr04','adafruit-circuitpython-hcsr04')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'pin_trigger',
            'type': 'select',
            'default_value': '20',
            'options_select': [
                ('0', 'GPIO 0'),
                ('1', 'GPIO 1'),
                ('2', 'GPIO 2'),
                ('3', 'GPIO 3'),
                ('4', 'GPIO 4'),
                ('5', 'GPIO 5'),
                ('6', 'GPIO 6'),
                ('7', 'GPIO 7'),
                ('8', 'GPIO 8'),
                ('9', 'GPIO 9'),
                ('10', 'GPIO 10'),
                ('11', 'GPIO 11'),
                ('12', 'GPIO 12'),
                ('13', 'GPIO 13'),
                ('14', 'GPIO 14'),
                ('15', 'GPIO 15'),
                ('16', 'GPIO 16'),
                ('17', 'GPIO 17'),
                ('18', 'GPIO 18'),
                ('19', 'GPIO 19'),
                ('20', 'GPIO 20'),
                ('21', 'GPIO 21'),
                ('22', 'GPIO 22'),
                ('23', 'GPIO 23'),
                ('24', 'GPIO 24'),
                ('25', 'GPIO 25'),
                ('26', 'GPIO 26'),
                ('27', 'GPIO 27')
            ],
            'name': 'Trigger Pin',
            'phrase': 'Enter the GPIO Trigger Pin for your device (GPIO numbering).'
        },
        {
            'id': 'pin_echo',
            'type': 'select',
            'default_value': '21',
            'options_select': [
                ('0', 'GPIO 0'),
                ('1', 'GPIO 1'),
                ('2', 'GPIO 2'),
                ('3', 'GPIO 3'),
                ('4', 'GPIO 4'),
                ('5', 'GPIO 5'),
                ('6', 'GPIO 6'),
                ('7', 'GPIO 7'),
                ('8', 'GPIO 8'),
                ('9', 'GPIO 9'),
                ('10', 'GPIO 10'),
                ('11', 'GPIO 11'),
                ('12', 'GPIO 12'),
                ('13', 'GPIO 13'),
                ('14', 'GPIO 14'),
                ('15', 'GPIO 15'),
                ('16', 'GPIO 16'),
                ('17', 'GPIO 17'),
                ('18', 'GPIO 18'),
                ('19', 'GPIO 19'),
                ('20', 'GPIO 20'),
                ('21', 'GPIO 21'),
                ('22', 'GPIO 22'),
                ('23', 'GPIO 23'),
                ('24', 'GPIO 24'),
                ('25', 'GPIO 25'),
                ('26', 'GPIO 26'),
                ('27', 'GPIO 27')
            ],
            'name': 'Echo Pin',
            'phrase': 'Enter the GPIO Echo Pin for your device (GPIO numbering).'
        },
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that measures the HCSR04's temperature """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.pin_trigger = None
        self.pin_echo = None

        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        import board
        import adafruit_hcsr04

        bcm_to_board = {
            "0": board.D0,
            "1": board.D1,
            "2": board.D2,
            "3": board.D3,
            "4": board.D4,
            "5": board.D5,
            "6": board.D6,
            "7": board.D7,
            "8": board.D8,
            "9": board.D9,
            "10": board.D10,
            "11": board.D11,
            "12": board.D12,
            "13": board.D13,
            "14": board.D14,
            "15": board.D15,
            "16": board.D16,
            "17": board.D17,
            "18": board.D18,
            "19": board.D19,
            "20": board.D20,
            "21": board.D21,
            "22": board.D22,
            "23": board.D23,
            "24": board.D24,
            "25": board.D25,
            "26": board.D26,
            "27": board.D27
        }

        if self.pin_trigger and self.pin_echo:
            self.sensor = adafruit_hcsr04.HCSR04(
                trigger_pin=bcm_to_board[self.pin_trigger],
                echo_pin=bcm_to_board[self.pin_echo])

    def get_measurement(self):
        """ Gets the measurement """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        # try 3 times
        for _ in range(3):
            try:
                self.value_set(0, self.sensor.distance)
                break
            except RuntimeError:
                pass

        return self.return_dict
