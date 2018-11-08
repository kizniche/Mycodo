# coding=utf-8
import logging
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import InputMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'altitude': {
        'm': {0: {}}
    },
    'pressure': {
        'Pa': {0: {}}
    },
    'temperature': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BMP180',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BMP180',
    'measurements_name': 'Pressure/Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_BMP', 'Adafruit_BMP'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x77'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BMP 180/085's humidity,
    temperature, and pressure, then calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.bmp180")
        self._measurements = None

        if not testing:
            from Adafruit_BMP import BMP085
            self.logger = logging.getLogger(
                "mycodo.bmp180_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_bus = input_dev.i2c_bus
            self.bmp = BMP085.BMP085(busnum=self.i2c_bus)

    def get_measurement(self):
        """ Gets the measurement in units by reading the BMP180/085 """
        time.sleep(2)

        return_dict = {
            'altitude': {
                'm': {}
            },
            'pressure': {
                'Pa': {}
            },
            'temperature': {
                'C': {}
            }
        }

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = self.bmp.read_temperature()

        if self.is_enabled('pressure', 'Pa', 0):
            return_dict['pressure']['Pa'][0] = self.bmp.read_pressure()

        if self.is_enabled('altitude', 'm', 0):
            return_dict['altitude']['m'][0] = self.bmp.read_altitude()

        return return_dict
