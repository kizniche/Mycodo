# coding=utf-8
import time

import copy

from mycodo.inputs.base_input import AbstractInput


def constraints_pass_measure_range(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: str
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    if value not in ['w1thermsensor', 'ow_shell']:
        all_passed = False
        errors.append("Invalid range")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'DS18S20',
    'input_manufacturer': 'MAXIM',
    'input_name': 'DS18S20',
    'input_library': 'w1thermsensor',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/sensors/DS18S20.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/DS18S20.pdf',

    'options_enabled': [
        'location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor==2.0.0'),
    ],

    'interfaces': ['1WIRE'],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """Set the resolution, precision, and response time for the sensor. This setting will be written to the EEPROM to allow persistence after power loss. The EEPROM has a limited amount of writes (>50k)."""
        },
        {
            'id': 'resolution',
            'type': 'select',
            'default_value': '',
            'options_select': [
                ('9', '9-bit, 0.5 °C, 93.75 ms'),
                ('10', '10-bit, 0.25 °C, 187.5 ms'),
                ('11', '11-bit, 0.125 °C, 375 ms'),
                ('12', '12-bit, 0.0625 °C, 750 ms')
            ],
            'name': 'Resolution',
            'phrase': 'Select the resolution for the sensor'
        },
        {
            'id': 'set_resolution',
            'type': 'button',
            'name': 'Set Resolution'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the DS18S20's temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from w1thermsensor import W1ThermSensor
        from w1thermsensor import Sensor

        self.sensor = W1ThermSensor(
            Sensor.DS18S20, self.input_dev.location)

    def get_measurement(self):
        """Gets the DS18S20's temperature in Celsius."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        n = 2
        for i in range(n):
            try:
                self.value_set(0, self.sensor.get_temperature())
                break
            except Exception as e:
                if i == n:
                    self.logger.exception(
                        "{cls} raised an exception when taking a reading: {err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)

        return self.return_dict

    def set_resolution(self, args_dict):
        if 'resolution' not in args_dict or not args_dict['resolution']:
            self.logger.error("Resolution required")
            return
        try:
            self.sensor.set_resolution(
                int(args_dict['resolution']), persist=True)
        except Exception as err:
            self.logger.error(
                "Error setting resolution: {}".format(err))
