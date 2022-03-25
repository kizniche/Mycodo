# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint

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
    'input_library': 'pierre-haessig/pycozir',
    'measurements_name': 'CO2/Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.co2meter.com/products/cozir-2000-ppm-co2-sensor',
    'url_datasheet': 'https://cdn.shopify.com/s/files/1/0019/5952/files/Datasheet_COZIR_A_CO2Meter_4_15.pdf',

    'options_enabled': [
        'uart_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'cozir', 'git+https://github.com/pierre-haessig/pycozir.git')
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
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from cozir import Cozir

        self.sensor = Cozir(self.input_dev.uart_location)

    def get_measurement(self):
        """Gets the measurements."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_CO2())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_temperature())

        if self.is_enabled(2):
            self.value_set(2, self.sensor.read_humidity())

        if self.is_enabled(1) and self.is_enabled(2):
            self.value_set(3, calculate_dewpoint(self.value_get(1), self.value_get(2)))

        return self.return_dict
