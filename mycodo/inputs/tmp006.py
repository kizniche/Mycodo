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
    'input_name_unique': 'TMP006',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'TMP006',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_TMP', 'Adafruit_TMP')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x40',
        '0x41',
        '0x42',
        '0x43',
        '0x44',
        '0x45',
        '0x46',
        '0x47'
    ],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TMP006's die and object temperatures """

    def __init__(self, input_dev,  testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tmp006")
        self._temperature_die = None
        self._temperature_object = None

        if not testing:
            from Adafruit_TMP import TMP006
            self.logger = logging.getLogger(
                "mycodo.tmp006_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = TMP006.TMP006(
                address=self.i2c_address, busnum=self.i2c_bus)

    def get_measurement(self):
        """ Gets the TMP006's temperature in Celsius """
        return_dict = {
            'temperature': {
                'C': {}
            }
        }

        self.sensor.begin()

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = self.sensor.readObjTempC()

        if self.is_enabled('temperature', 'C', 1):
            return_dict['temperature']['C'][0] = self.sensor.readDieTempC()

        return return_dict
