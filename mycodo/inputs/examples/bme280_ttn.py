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
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
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
    'input_library': 'Adafruit_BME280/pyserial',
    'measurements_name': 'Pressure/Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,
    'url_manufacturer': 'https://www.bosch-sensortec.com/bst/products/all_products/bme280',
    'url_datasheet': 'https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/2652',
        'https://www.sparkfun.com/products/13676'
    ],

    'message': "This input outputs the measurements from the BME280 to a serial device that is expected to send "
               "the data to The Things Network. See the Additional URL for more information.",

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'serial', 'pyserial==3.5'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3'),
        ('pip-pypi', 'Adafruit_BME280', 'git+https://github.com/adafruit/Adafruit_Python_BME280.git')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x76', '0x77'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'serial_device',
            'type': 'text',
            'default_value': '/dev/ttyUSB0',
            'name': 'Serial Device',
            'phrase': 'The serial device to write to'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.serial = None
        self.serial_send = None
        self.lock_file = "/var/lock/mycodo_ttn.lock"
        self.ttn_serial_error = False
        self.timer = 0

        # Initialize custom options
        self.serial_device = None

        if not testing:
            # Set custom options
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)

    def initialize_input(self):
        from Adafruit_BME280 import BME280
        import serial

        self.sensor = BME280(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)
        self.serial = serial

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_temperature())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_humidity())

        if self.is_enabled(2):
            self.value_set(2, self.sensor.read_pressure())

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            dewpoint = calculate_dewpoint(
                self.value_get(0), self.value_get(1))
            self.value_set(3, dewpoint)

        if self.is_enabled(4) and self.is_enabled(2):
            altitude = calculate_altitude(self.value_get(2))
            self.value_set(4, altitude)

        if (self.is_enabled(5) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            vpd = calculate_vapor_pressure_deficit(
                self.value_get(0), self.value_get(1))
            self.value_set(5, vpd)

        try:
            now = time.time()
            if now > self.timer:
                self.timer = now + 80
                # "B" designates this data belonging to the BME280
                string_send = 'B,{},{},{}'.format(
                    self.value_get(1),
                    self.value_get(2),
                    self.value_get(0))

                if self.lock_acquire(self.lock_file, timeout=10):
                    try:
                        self.serial_send = self.serial.Serial(
                            port=self.serial_device,
                            baudrate=9600,
                            timeout=5,
                            writeTimeout=5)
                        self.serial_send.write(string_send.encode())
                        time.sleep(4)
                    finally:
                        self.lock_release(self.lock_file)
                self.ttn_serial_error = False
        except Exception as e:
            if not self.ttn_serial_error:
                # Only send this error once if it continually occurs
                self.logger.error("TTN: Could not send serial: {}".format(e))
                self.ttn_serial_error = True

        return self.return_dict
