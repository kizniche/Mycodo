# coding=utf-8
import logging
import time

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
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'location',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor')
    ],

    'interfaces': ['1WIRE']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the MAX31850K's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.max31850k")

        if not testing:
            from w1thermsensor import W1ThermSensor
            self.logger = logging.getLogger(
                "mycodo.max31850k_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.location = input_dev.location
            self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_MAX31850K,
                                        self.location)

        if input_dev.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the MAX31850K's temperature in Celsius """
        return_dict = measurements_dict.copy()

        n = 2
        for i in range(n):
            try:
                return_dict[0]['value'] = self.sensor.get_temperature()
                return return_dict
            except Exception as e:
                if i == n:
                    self.logger.exception(
                        "{cls} raised an exception when taking a reading: "
                        "{err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)
