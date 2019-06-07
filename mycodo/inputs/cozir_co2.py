# coding=utf-8
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            from cozir import Cozir

            self.uart_location = input_dev.uart_location
            self.sensor = Cozir(self.uart_location)

    def get_measurement(self):
        """ Gets the measurements """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_CO2())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_temperature())

        if self.is_enabled(2):
            self.value_set(2, self.sensor.read_humidity())

        if (self.is_enabled(3) and
                self.is_enabled(1) and
                self.is_enabled(2)):
            self.value_set(3, calculate_dewpoint(
                self.value_get(1), self.value_get(2)))

        return self.return_dict
