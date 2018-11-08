# coding=utf-8
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Based on the BMP280 driver with BME280 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import altitude
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.databases.models import InputMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'altitude': {
        'm': {0: {}}
    },
    'pressure': {
        'Pa': {0: {}}
    },
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
    'input_name_unique': 'BME280',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME280',
    'measurements_name': 'Pressure/Humidity/Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-git', 'Adafruit_BME280', 'git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x76'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.bme280")

        if not testing:
            from Adafruit_BME280 import BME280
            self.logger = logging.getLogger(
                "mycodo.bme280_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = BME280(address=self.i2c_address,
                                 busnum=self.i2c_bus)

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        return_dict = {
            'altitude': {
                'm': {}
            },
            'pressure': {
                'Pa': {}
            },
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

        pressure_pa = self.sensor.read_pressure()

        if self.is_enabled('pressure', 'Pa', 0):
            return_dict['pressure']['Pa'][0] = pressure_pa

        if self.is_enabled('altitude', 'm', 0):
            return_dict['altitude']['m'][0] = altitude(pressure_pa)

        temperature = self.sensor.read_temperature()

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = temperature

        humidity = self.sensor.read_humidity()

        if self.is_enabled('humidity', 'percent', 0):
            return_dict['humidity']['percent'][0] = humidity

        if self.is_enabled('dewpoint', 'C', 0):
            return_dict['dewpoint']['C'][0] = calculate_dewpoint(
                temperature, humidity)

        return return_dict
