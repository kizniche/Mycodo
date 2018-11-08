# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import InputMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'co2': {
        'ppm': {0: {}}
    },
    'voc': {
        'ppb': {0: {}}
    },
    'temperature': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'CCS811',
    'input_manufacturer': 'Ams',
    'input_name': 'CCS811',
    'measurements_name': 'CO2/VOC/Temperature',
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
        ('pip-pypi', 'Adafruit_CCS811', 'Adafruit_CCS811'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x5a', '0x5b'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the CC2811's voc, temperature
    and co2

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.ccs811")
        self._co2 = None
        self._voc = None
        self._temperature = None

        if not testing:
            from Adafruit_CCS811 import Adafruit_CCS811
            self.logger = logging.getLogger(
                "mycodo.ccs811_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = Adafruit_CCS811(address=self.i2c_address,
                                          busnum=self.i2c_bus)
            while not self.sensor.available():
                pass
            temp = self.sensor.calculateTemperature()
            self.sensor.tempOffset = temp - 25.0

    def get_measurement(self):
        """ Gets the CO2, VOC, and temperature """
        return_dict = {
            'co2': {
                'ppm': {}
            },
            'voc': {
                'ppb': {}
            },
            'temperature': {
                'C': {}
            }
        }

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = self.sensor.calculateTemperature()

        if not self.sensor.readData():
            if self.is_enabled('voc', 'ppb', 0):
                return_dict['voc']['ppb'][0] = self.sensor.getTVOC()

            if self.is_enabled('co2', 'ppm', 0):
                return_dict['co2']['ppm'][0] = self.sensor.geteCO2()

            return return_dict
        else:
            return None
