# coding=utf-8
import logging

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.database import db_retrieve_table_daemon

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
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'gpio_location',
        'sht_voltage',
        'measurements_select',
        'period',
        'pin_clock',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'sht_sensor', 'sht_sensor')
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        if not testing:
            from sht_sensor import Sht
            from sht_sensor import ShtVDDLevel

            self.gpio = int(input_dev.gpio_location)
            self.clock_pin = input_dev.clock_pin
            sht_sensor_vdd_value = {
                2.5: ShtVDDLevel.vdd_2_5,
                3.0: ShtVDDLevel.vdd_3,
                3.5: ShtVDDLevel.vdd_3_5,
                4.0: ShtVDDLevel.vdd_4,
                5.0: ShtVDDLevel.vdd_5
            }
            self.sht_voltage = sht_sensor_vdd_value[
                round(float(input_dev.sht_voltage), 1)]
            self.sht_sensor = Sht(
                self.clock_pin,
                self.gpio,
                voltage=self.sht_voltage)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.set_value(0, self.sht_sensor.read_t())

        if self.is_enabled(1):
            self.set_value(1, self.sht_sensor.read_rh())

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.set_value(2, calculate_dewpoint(
                self.get_value(0), self.get_value(1)))

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.set_value(3, calculate_vapor_pressure_deficit(
                self.get_value(0), self.get_value(1)))

        return self.return_dict
