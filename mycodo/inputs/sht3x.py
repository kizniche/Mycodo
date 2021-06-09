# coding=utf-8
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Based on the BMP280 driver with SHT31 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
import math
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.constraints_pass import constraints_pass_positive_value

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
    'input_name_unique': 'SHT31',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT3x (30, 31, 35)',
    'input_library': 'Adafruit_SHT31',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-various-applications/',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3'),
        ('pip-pypi', 'Adafruit_SHT31', 'Adafruit-SHT31==1.0.2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x44', '0x45'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'heater_enable',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Heater',
            'phrase': 'Enable heater to evaporate condensation. Turn on heater x seconds every y measurements.'
        },
        {
            'id': 'heater_seconds',
            'type': 'float',
            'default_value': 1.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Heater On Seconds',
            'phrase': 'How long to turn the heater on (seconds).'
        },
        {
            'id': 'heater_measurements',
            'type': 'integer',
            'default_value': 10,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Heater On Period',
            'phrase': 'After how many measurements to turn the heater on. This will repeat.'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT31's humidity and temperature,
    them calculates the dew point and vapor pressure deficit
    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.measurement_count = 0

        self.heater_enable = None
        self.heater_seconds = None
        self.heater_measurements = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        from Adafruit_SHT31 import SHT31

        self.sensor = SHT31(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        temperature = None
        humidity = None
        success = False
        for _ in range(3):  # Three attempts
            try:
                temperature, humidity = self.sensor.read_temperature_humidity()
            except OSError as e:
                self.logger.debug("OSError: {}".format(e))
                self.logger.debug("Attempting reset of sensor and another measurement")
                try:
                    self.sensor.reset()
                    try:
                        temperature, humidity = self.sensor.read_temperature_humidity()
                    except Exception as e:
                        self.logger.debug("Measurement unsuccessful after reset")
                except Exception:
                    self.logger.debug("Reset command unsuccessful")
            if None in [temperature, humidity] or math.isnan(temperature) or math.isnan(humidity):
                self.logger.debug("One not a number: Temperature: {}, Humidity: {}".format(temperature, humidity))
            else:
                success = True
                break
            time.sleep(0.1)

        if not success:
            self.logger.debug("Could not obtain measurements after 3 tries")
            return

        if self.is_enabled(0):
            self.value_set(0, temperature)

        if self.is_enabled(1):
            self.value_set(1, humidity)

        if self.is_enabled(2) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(2, calculate_dewpoint(self.value_get(0), self.value_get(1)))

        if self.is_enabled(3) and self.is_enabled(0) and self.is_enabled(1):
            self.value_set(3, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

        if self.heater_enable and self.heater_seconds and self.heater_measurements:
            time.sleep(2)
            self.measurement_count += 1
            if self.measurement_count >= self.heater_measurements:
                self.measurement_count = 0
                self.sensor.set_heater(True)
                time.sleep(self.heater_seconds)
                self.sensor.set_heater(False)

        return self.return_dict

    def status(self):
        status = self.sensor.read_status()
        is_data_crc_error = self.sensor.is_data_crc_error()
        is_command_error = self.sensor.is_command_error()
        is_reset_detected = self.sensor.is_reset_detected()
        is_tracking_temperature_alert = self.sensor.is_tracking_temperature_alert()
        is_tracking_humidity_alert = self.sensor.is_tracking_humidity_alert()
        is_heater_active = self.sensor.is_heater_active()
        is_alert_pending = self.sensor.is_alert_pending()
        self.logger.info('Status           = {:04X}'.format(status))
        self.logger.info('  Data CRC Error = {}'.format(is_data_crc_error))
        self.logger.info('  Command Error  = {}'.format(is_command_error))
        self.logger.info('  Reset Detected = {}'.format(is_reset_detected))
        self.logger.info('  Tracking Temp  = {}'.format(is_tracking_temperature_alert))
        self.logger.info('  Tracking RH    = {}'.format(is_tracking_humidity_alert))
        self.logger.info('  Heater Active  = {}'.format(is_heater_active))
        self.logger.info('  Alert Pending  = {}'.format(is_alert_pending))
        time.sleep(0.1)
