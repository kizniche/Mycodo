# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements = {
    'gpio_state': {
        'bool': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'GPIO_STATE',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'GPIO State',
    'measurements_name': 'GPIO State',
    'measurements_dict': measurements,

    'options_enabled': [
        'gpio_location',
        'period',
        'pre_output'
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
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.gpio_state")
        self._measurements = None

        if not testing:
            import RPi.GPIO as GPIO
            self.logger = logging.getLogger(
                "mycodo.gpio_state_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.location = int(input_dev.gpio_location)
            self.gpio = GPIO
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.location, self.gpio.IN)

    def get_measurement(self):
        """ Gets the GPIO state via RPi.GPIO """
        return_dict = {
            'gpio_state': {
                'bool': {}
            }
        }

        return_dict['gpio_state']['bool'][0] = self.gpio.input(self.location)

        return return_dict

    def stop_sensor(self):
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.cleanup(self.location)
