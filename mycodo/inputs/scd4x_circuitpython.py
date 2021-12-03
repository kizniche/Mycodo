# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

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
    },
    4: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SCD4x_CIRCUITPYTHON',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SCD-4x (SCD-40, SCD-41)',
    'input_library': 'Adafruit-CircuitPython-SCD4x',
    'measurements_name': 'CO2/Temperature/Humidity',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensor-scd4x/',

    'options_enabled': [
        'i2c_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.1'),
        ('pip-pypi', 'adafruit_scd4x', 'adafruit-circuitpython-scd4x==1.2.1 ')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x62'],
    'i2c_address_editable': False,
}


class InputModule(AbstractInput):
    """ A sensor support class that measures """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        import adafruit_scd4x
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_scd4x.SCD4X(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

    def get_measurement(self):
        """ Gets the measurements """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.CO2)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.temperature)

        if self.is_enabled(2):
            self.value_set(2, self.sensor.relative_humidity)

        if self.is_enabled(3) and self.is_enabled(1) and self.is_enabled(2):
            self.value_set(3, calculate_dewpoint(self.value_get(1), self.value_get(2)))

        if self.is_enabled(4) and self.is_enabled(1) and self.is_enabled(2):
            self.value_set(4, calculate_vapor_pressure_deficit(self.value_get(1), self.value_get(2)))

        return self.return_dict
