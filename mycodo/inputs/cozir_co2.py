# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    2: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    3: {
        'measurement': 'dewpoint',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'COZIR_CO2',
    'input_manufacturer': 'Cozir',
    'input_name': 'Cozir CO2',
    'measurements_name': 'CO2/Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'uart_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-git', 'cozir', 'git://github.com/pierre-haessig/pycozir.git#egg=pycozir')
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
        self.setup_logger(name=__name__)

        if not testing:
            from cozir import Cozir

            self.setup_logger(
                name=__name__, log_id=input_dev.unique_id.split('-')[0])

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.uart_location = input_dev.uart_location
            self.sensor = Cozir(self.uart_location)

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the measurements """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.set_value(0, self.sensor.read_CO2())

        if self.is_enabled(1):
            self.set_value(1, self.sensor.read_temperature())

        if self.is_enabled(2):
            self.set_value(2, self.sensor.read_humidity())

        if (self.is_enabled(3) and
                self.is_enabled(1) and
                self.is_enabled(2)):
            self.set_value(3, calculate_dewpoint(
                self.get_value(1), self.get_value(2)))

        return self.return_dict
