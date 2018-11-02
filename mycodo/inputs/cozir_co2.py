# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.databases.models import InputMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'co2': {
        'ppm': {0: {}}
    },
    'dewpoint': {
        'C': {0: {}}
    },
    'temperature': {
        'C': {0: {}}
    },
    'humidity': {
        'percent': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'COZIR_CO2',
    'input_manufacturer': 'Cozir',
    'input_name': 'Cozir CO2',
    'measurements_name': 'CO2/Humidity/Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'uart_location',
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-git', 'pycozir', 'git://github.com/pierre-haessig/pycozir.git#egg=pycozir')
    ],

    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0'
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the COZIR's CO2, humidity, and temperature
    and calculates the dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.cozir")
        self._measurements = None

        if not testing:
            from pycozir import Cozir
            self.logger = logging.getLogger(
                "mycodo.cozir_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id).all()

            self.uart_location = input_dev.uart_location
            self.sensor = Cozir(self.uart_location)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        return_dict = {
            'co2': {
                'ppm': {}
            },
            'dewpoint': {
                'C': {}
            },
            'temperature': {
                'C': {}
            },
            'humidity': {
                'percent': {}
            }
        }

        if self.is_enabled('co2', 'ppm', 0):
            return_dict['co2']['ppm'][0] = self.sensor.read_CO2()

        temperature = self.sensor.read_temperature()

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = temperature

        humidity = self.sensor.read_humidity()

        if self.is_enabled('humidity', 'percent', 0):
            return_dict['humidity']['percent'][0] = humidity

        if self.is_enabled('dewpoint', 'C', 0):
            return_dict['dewpoint']['C'][0] = calculate_dewpoint(
                temperature, humidity)

        return return_dict
