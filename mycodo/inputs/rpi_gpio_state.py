# coding=utf-8
import logging

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
    'measurements_name': 'GPIO State',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'gpio_location',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO')
    ],

    'interfaces': ['GPIO']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the K30's CO2 concentration """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, name=__name__)

        if not testing:
            import RPi.GPIO as GPIO

            self.location = int(input_dev.gpio_location)
            self.gpio = GPIO
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.location, self.gpio.IN)

    def get_measurement(self):
        """ Gets the GPIO state via RPi.GPIO """
        self.return_dict = measurements_dict.copy()

        self.set_value(0, self.gpio.input(self.location))

        return self.return_dict

    def stop_sensor(self):
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.cleanup(self.location)
