# coding=utf-8
import logging

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'temperature': {
        'C': {0: {}}
    },
    'humidity': {
        'percent': {0: {}}
    },
    'dewpoint': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SHT1x_7x',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT1x/7x',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict':measurements,

    'options_enabled': [
        'gpio_location',
        'sht_voltage',
        'measurements_select',
        'measurements_convert',
        'period',
        'pin_clock',
        'pre_output'
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
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.sht1x_7x")
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        if not testing:
            from sht_sensor import Sht
            from sht_sensor import ShtVDDLevel
            self.logger = logging.getLogger(
                "mycodo.sht1x_7x_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id).all()

            self.gpio = int(input_dev.gpio_location)
            self.clock_pin = input_dev.clock_pin
            sht_sensor_vdd_value = {
                2.5: ShtVDDLevel.vdd_2_5,
                3.0: ShtVDDLevel.vdd_3,
                3.5: ShtVDDLevel.vdd_3_5,
                4.0: ShtVDDLevel.vdd_4,
                5.0: ShtVDDLevel.vdd_5
            }
            self.sht_voltage = sht_sensor_vdd_value[round(float(input_dev.sht_voltage), 1)]
            self.sht_sensor = Sht(self.clock_pin,
                                  self.gpio,
                                  voltage=self.sht_voltage)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        return_dict = {
            'temperature': {
                'C': {}
            },
            'humidity': {
                'percent': {}
            },
            'dewpoint': {
                'C': {}
            }
        }

        temperature = self.sht_sensor.read_t()

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = temperature

        humidity = self.sht_sensor.read_rh()

        if self.is_enabled('humidity', 'percent', 0):
            return_dict['humidity']['percent'][0] = humidity

        if self.is_enabled('dewpoint', 'C', 0):
            return_dict['dewpoint']['C'][0] = self.sht_sensor.read_dew_point(
                temperature, humidity)

        return return_dict
