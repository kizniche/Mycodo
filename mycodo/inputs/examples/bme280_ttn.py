# coding=utf-8
#
# Example module for measuring with the BME280 and sending
# the measurement to a serial device. For accompaniment with
# the The Things Network (TTN) Data Storage Input module
#
# Use this module to send measurements via serial to a
# LoRaWAN-enabled device, which transmits the data to TTN.
#
# Comment will be updated with other code to go along with this module
#
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Based on the BMP280 driver with BME280 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
import logging
import os
import time
from flask_babel import lazy_gettext

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
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
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    3: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    4: {
        'measurement': 'altitude',
        'unit': 'm'
    },
    5: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }

}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BME280_TTN',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME280 (->Serial->TTN)',
    'measurements_name': 'Pressure/Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'options_enabled': [
        'i2c_location',
        'custom_options',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'locket', 'locket'),
        ('pip-pypi', 'serial', 'pyserial'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-git', 'Adafruit_BME280', 'git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x76',
        '0x77'
    ],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'serial_device',
            'type': 'text',
            'default_value': '/dev/ttyUSB0',
            'name': lazy_gettext('Serial Device'),
            'phrase': lazy_gettext('The serial device to write to')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.bme280_ttn")
        self.timer = 0

        if not testing:
            from Adafruit_BME280 import BME280
            import serial
            import locket
            self.logger = logging.getLogger(
                "mycodo.bme280_ttn_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'serial_device':
                        self.serial_device = value

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = BME280(address=self.i2c_address,
                                 busnum=self.i2c_bus)
            self.serial = serial
            self.serial_send = None
            self.locket = locket
            self.lock = None
            self.lock_file = "/var/lock/mycodo_ttn.lock"
            self.locked = False
            self.ttn_serial_error = False

        if input_dev.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def lock_setup(self):
        self.lock = self.locket.lock_file(self.lock_file, timeout=10)
        try:
            self.lock.acquire()
            self.locked = True
        except self.locket.LockError:
            self.logger.error("Could not acquire input lock. Breaking for future locking.")
            try:
                os.remove(self.lock_file)
            except OSError:
                self.logger.error("Can't delete lock file: Lock file doesn't exist.")

    def lock_release(self):
        try:
            if self.locked:
                self.lock.release()
                self.locked = False
        except AttributeError:
            self.logger.error("Can't release lock: Lock file not present.")

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.set_value(return_dict, 0, self.sensor.read_temperature())

        if self.is_enabled(1):
            self.set_value(return_dict, 1, self.sensor.read_humidity())

        if self.is_enabled(2):
            self.set_value(return_dict, 2, self.sensor.read_pressure())

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            dewpoint = calculate_dewpoint(
                return_dict[0]['value'], return_dict[1]['value'])
            self.set_value(return_dict, 3, dewpoint)

        if self.is_enabled(4) and self.is_enabled(2):
            altitude = calculate_altitude(return_dict[2]['value'])
            self.set_value(return_dict, 4, altitude)

        if (self.is_enabled(5) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            vpd = calculate_vapor_pressure_deficit(
                return_dict[0]['value'], return_dict[1]['value'])
            self.set_value(return_dict, 5, vpd)

        try:
            now = time.time()
            if now > self.timer:
                self.timer = now + 80
                # "B" designates this data belonging to the BME280
                string_send = 'B,{},{},{}'.format(
                    self.get_value(1),
                    self.get_value(2),
                    self.get_value(0))
                self.lock_setup()
                self.serial_send = self.serial.Serial(self.serial_device, 9600)
                self.serial_send.write(string_send.encode())
                time.sleep(4)
                self.lock_release()
                self.ttn_serial_error = False
        except:
            if not self.ttn_serial_error:
                # Only send this error once if it continually occurs
                self.logger.error("TTN: Could not send serial")
                self.ttn_serial_error = True

        return return_dict
