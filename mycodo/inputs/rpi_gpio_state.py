# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'gpio_state',
        'unit': 'bool'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'GPIO_STATE',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'GPIO State',
    'input_library': 'RPi.GPIO',
    'measurements_name': 'GPIO State',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'gpio_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.0')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'pin_mode',
            'type': 'select',
            'default_value': 'floating',
            'options_select': [
                ('floating', 'Floating'),
                ('pull_down', 'Pull Down'),
                ('pull_up', 'Pull Up')
            ],
            'name': 'Pin Mode',
            'phrase': 'Enables or disables the pull-up or pull-down resistor'
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the K30's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.gpio = None

        self.pin_mode = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import RPi.GPIO as GPIO

        self.gpio = GPIO

        self.location = int(self.input_dev.gpio_location)
        self.gpio.setmode(self.gpio.BCM)

        if self.pin_mode == "pull_down":
            self.logger.debug("Pull-DOWN enabled for pin {ch}".format(ch=self.location))
            self.gpio.setup(self.location, self.gpio.IN, pull_up_down=GPIO.PUD_DOWN)
        elif self.pin_mode == "pull_up":
            self.logger.debug("Pull-UP enabled for pin {ch}".format(ch=self.location))
            self.gpio.setup(self.location, self.gpio.IN, pull_up_down=GPIO.PUD_UP)
        else:
            self.gpio.setup(self.location, self.gpio.IN)

    def get_measurement(self):
        """ Gets the GPIO state via RPi.GPIO """
        self.return_dict = copy.deepcopy(measurements_dict)

        self.value_set(0, self.gpio.input(self.location))

        return self.return_dict

    def stop_input(self):
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.cleanup(self.location)
