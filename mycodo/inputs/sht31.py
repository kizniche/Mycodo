# coding=utf-8
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Based on the BMP280 driver with SHT31 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
import logging
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.database import db_retrieve_table_daemon


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


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
    'input_name': 'SHT31',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'custom_options',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-git', 'Adafruit_SHT31', 'git://github.com/ralf1070/Adafruit_Python_SHT31.git#egg=adafruit-sht31')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x44',
        '0x45'
    ],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'heater_enable',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Enable Heater'),
            'phrase': lazy_gettext(
                'Enable heater to evaporate condensation. Turn on heater x seconds every y measurements.')
        },
        {
            'id': 'heater_seconds',
            'type': 'float',
            'default_value': 1.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Heater On Seconds'),
            'phrase': lazy_gettext('How long to turn the heater on (seconds).')
        },
        {
            'id': 'heater_measurements',
            'type': 'integer',
            'default_value': 10,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Heater On Period'),
            'phrase': lazy_gettext('After how many measurements to turn the heater on. This will repeat.')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT31's humidity and temperature,
    them calculates the dew point and vapor pressure deficit
    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, name=__name__)
        self.measurement_count = 0
        self.heater_enable = None
        self.heater_seconds = None
        self.heater_measurements = None

        if not testing:
            from Adafruit_SHT31 import SHT31

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'heater_enable':
                        self.heater_enable = bool(value)
                    elif option == 'heater_seconds':
                        self.heater_seconds = float(value)
                    elif option == 'heater_measurements':
                        self.heater_measurements = int(value)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = SHT31(
                address=self.i2c_address,
                busnum=self.i2c_bus)

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.set_value(0, self.sensor.read_temperature())

        if self.is_enabled(1):
            self.set_value(1, self.sensor.read_humidity())

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
