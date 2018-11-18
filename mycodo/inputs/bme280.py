# coding=utf-8
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Based on the BMP280 driver with BME280 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
import logging

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'pressure',
        'unit': 'Pa'
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
        'measurement': 'altitude',
        'unit': 'm'
    }

}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BME280',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME280',
    'measurements_name': 'Pressure/Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'measurements_select',
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

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = BME280(address=self.i2c_address,
                                 busnum=self.i2c_bus)

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            return_dict[0]['value'] = self.sensor.read_pressure()

        if self.is_enabled(1):
            return_dict[1]['value'] = self.sensor.read_temperature()

        if self.is_enabled(2):
            return_dict[2]['value'] = self.sensor.read_humidity()

        if (self.is_enabled(3) and
                self.is_enabled(1) and
                self.is_enabled(2)):
            return_dict[3]['value'] = calculate_dewpoint(
                return_dict[1]['value'], return_dict[2]['value'])

        if self.is_enabled(4) and self.is_enabled(0):
            return_dict[4]['value'] = calculate_altitude(return_dict[0]['value'])

        return return_dict
