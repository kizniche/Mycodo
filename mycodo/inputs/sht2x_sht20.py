# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SHT2x_sht20',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT2x',
    'input_library': 'sht20',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': [
        'interface',
        'i2c_location'
    ],

    'dependencies_module': [
        ('pip-pypi', 'sht20', 'sht20==0.1.4')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'temperature_resolution',
            'type': 'select',
            'default_value': '14',
            'options_select': [
                ('11', '11-bit'),
                ('12', '12-bit'),
                ('13', '13-bit'),
                ('14', '14-bit')
            ],
            'name': 'Temperature Resolution',
            'phrase': 'The resolution of the temperature measurement'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT2x's humidity and temperature
    and calculates the dew point
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.temperature_resolution = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from sht20 import SHT20

        if self.temperature_resolution == '11':
            resolution = SHT20.TEMP_RES_11bit
        elif self.temperature_resolution == '12':
            resolution = SHT20.TEMP_RES_12bit
        elif self.temperature_resolution == '13':
            resolution = SHT20.TEMP_RES_13bit
        elif self.temperature_resolution == '14':
            resolution = SHT20.TEMP_RES_14bit
        else:
            self.logger.error("Unexpected resolution: '{}'".format(
                self.temperature_resolution))
            return

        self.sensor = SHT20(self.input_dev.i2c_bus, resolution=resolution)

    def get_measurement(self):
        """Gets the humidity and temperature"""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_temp())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_humid())

        if self.is_enabled(2) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(2, calculate_dewpoint(self.value_get(0), self.value_get(1)))

        if self.is_enabled(3) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(3, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

        return self.return_dict
