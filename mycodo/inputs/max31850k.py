# coding=utf-8
import time

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
    'input_name_unique': 'MAX31850K',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31850K',
    'input_library': 'w1thermsensor',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/sensors/MAX31850EVKIT.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/MAX31850-MAX31851.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/1727',

    'options_enabled': [
        'location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor==2.0.0')
    ],

    'interfaces': ['1WIRE']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the MAX31850K's temperature """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        from w1thermsensor import W1ThermSensor
        from w1thermsensor import Sensor

        self.sensor = W1ThermSensor(
            Sensor.MAX31850K, self.input_dev.location)

    def get_measurement(self):
        """ Gets the MAX31850K's temperature in Celsius """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        n = 2
        for i in range(n):
            try:
                self.value_set(0, self.sensor.get_temperature())
                return self.return_dict
            except Exception as e:
                if i == n:
                    self.logger.exception(
                        "{cls} raised an exception when taking a reading: {err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)
