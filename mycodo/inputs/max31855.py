# coding=utf-8
import logging

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

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
    'input_name_unique': 'MAX31855',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31855',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'pin_clock',
        'pin_cs',
        'pin_miso',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-git', 'Adafruit_MAX31855', 'git://github.com/adafruit/Adafruit_Python_MAX31855.git#egg=adafruit-max31855'),
        ('pip-pypi', 'Adafruit_GPIO','Adafruit_GPIO')
    ],

    'interfaces': ['UART'],
    'pin_cs': 8,
    'pin_miso': 9,
    'pin_clock': 11
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the MAX31855's temperature

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            import Adafruit_MAX31855.MAX31855 as MAX31855

            self.pin_clock = input_dev.pin_clock
            self.pin_cs = input_dev.pin_cs
            self.pin_miso = input_dev.pin_miso
            self.sensor = MAX31855.MAX31855(
                self.pin_clock,
                self.pin_cs,
                self.pin_miso)

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.set_value(0, self.sensor.readTempC())

        if self.is_enabled(1):
            self.set_value(1, self.sensor.readInternalC())

        return self.return_dict
