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
    'input_name_unique': 'SHT1x_7x',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT1x/7x',
    'input_library': 'sht_sensor',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': [
        'https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-accurate-measurements/',
        'https://www.sensirion.com/en/environmental-sensors/humidity-sensors/pintype-digital-humidity-sensors/'
    ],

    'options_enabled': [
        'gpio_location',
        'sht_voltage',
        'measurements_select',
        'period',
        'pin_clock',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'sht_sensor', 'sht-sensor==18.4.2')
    ],

    'interfaces': ['GPIO'],
    'pin_clock': 11,
    'sht_voltage': [
        ('2.5', '2.5V'),
        ('3.0', '3.0V'),
        ('3.5', '3.5V'),
        ('4.0', '4.0V'),
        ('5.0', '5.0V')
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT1x7x's humidity and temperature
    and calculates the dew point
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from sht_sensor import Sht
        from sht_sensor import ShtVDDLevel

        sht_vdd = {
            2.5: ShtVDDLevel.vdd_2_5,
            3.0: ShtVDDLevel.vdd_3,
            3.5: ShtVDDLevel.vdd_3_5,
            4.0: ShtVDDLevel.vdd_4,
            5.0: ShtVDDLevel.vdd_5
        }
        self.sensor = Sht(
            self.input_dev.pin_clock,
            int(self.input_dev.gpio_location),
            voltage=sht_vdd[round(float(self.input_dev.sht_voltage), 1)])

    def get_measurement(self):
        """Gets the humidity and temperature."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_t())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_rh())

        if self.is_enabled(2) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(2, calculate_dewpoint(self.value_get(0), self.value_get(1)))

        if self.is_enabled(3) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(3, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

        return self.return_dict
