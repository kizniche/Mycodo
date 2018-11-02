# coding=utf-8
import logging
import time

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements = {
    'temperature': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'DS18S20',
    'input_manufacturer': 'MAXIM',
    'input_name': 'DS18S20',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'location',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor')
    ],

    'interfaces': ['1WIRE'],
    'w1thermsensor_detect_1wire': True
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the DS18S20's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.ds18s20")
        self._measurements = None

        if not testing:
            from w1thermsensor import W1ThermSensor
            self.logger = logging.getLogger(
                "mycodo.ds18s20_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.location = input_dev.location
            self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18S20,
                                        self.location)

    def get_measurement(self):
        """ Gets the DS18S20's temperature in Celsius """
        return_dict = {
            'temperature': {
                'C': {}
            }
        }

        temperature = None
        n = 2
        for i in range(n):
            try:
                temperature = self.sensor.get_temperature()
                break
            except Exception as e:
                if i == n:
                    self.logger.exception(
                        "{cls} raised an exception when taking a reading: "
                        "{err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)

        return_dict['temperature']['C'][0] = temperature

        return return_dict
