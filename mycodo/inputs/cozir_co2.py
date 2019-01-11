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
        'pre_output'
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
        self.logger = logging.getLogger("mycodo.inputs.cozir_co2")

        if not testing:
            from cozir import Cozir
            self.logger = logging.getLogger(
                "mycodo.cozir_co2_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.uart_location = input_dev.uart_location
            self.sensor = Cozir(self.uart_location)

    def get_measurement(self):
        """ Gets the measurements """
        return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            return_dict[0]['value'] = self.sensor.read_CO2()

        if self.is_enabled(1):
            return_dict[1]['value'] = self.sensor.read_temperature()

        if self.is_enabled(2):
            return_dict[2]['value'] = self.sensor.read_humidity()

        if (self.is_enabled(3) and
                self.is_enabled(1) and
                self.is_enabled(2)):
            return_dict[3]['value'] = calculate_dewpoint(
                return_dict[1]['value'], return_dict[2]['value'])

        return return_dict
