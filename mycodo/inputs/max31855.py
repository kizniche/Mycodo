# coding=utf-8
import logging

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'temperature': {
        'C': {
            0: {'name': 'Object'},
            1: {'name': 'Die'}
        }
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MAX31855',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31855',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements,

    'options_enabled': [
        'pin_clock',
        'pin_cs',
        'pin_miso',
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
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
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.max31855")
        self._measurements = None

        if not testing:
            import Adafruit_MAX31855.MAX31855 as MAX31855
            self.logger = logging.getLogger(
                "mycodo.max31855_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id).all()

            self.pin_clock = input_dev.pin_clock
            self.pin_cs = input_dev.pin_cs
            self.pin_miso = input_dev.pin_miso
            self.sensor = MAX31855.MAX31855(self.pin_clock,
                                            self.pin_cs,
                                            self.pin_miso)

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        return_dict = {
            'temperature': {
                'C': {}
            }
        }

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = self.sensor.readTempC()

        if self.is_enabled('temperature', 'C', 1):
            return_dict['temperature']['C'][1] = self.sensor.readInternalC()

        return return_dict
