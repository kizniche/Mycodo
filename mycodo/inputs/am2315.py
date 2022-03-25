# coding=utf-8
#
# Copyright 2014 Matt Heitzenroder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Python wrapper exposes the capabilities of the AOSONG AM2315 humidity
# and temperature sensor.
# The datasheet for the device can be found here:
# http://www.adafruit.com/datasheets/AM2315.pdf
#
# Portions of this code were inspired by Joehrg Ehrsam's am2315-python-api
# code. http://code.google.com/p/am2315-python-api/
#
# This library was originally authored by Sopwith:
#     http://sopwith.ismellsmoke.net/?p=104
import math
import time

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
    'input_name_unique': 'AM2315',
    'input_manufacturer': 'AOSONG',
    'input_name': 'AM2315/AM2320',
    'input_library': 'quick2wire-api',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'https://cdn-shop.adafruit.com/datasheets/AM2315.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/1293',

    'measurements_rescale': False,

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'quick2wire', 'quick2wire-api==0.0.0.2')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x5c'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the AM2315's humidity and temperature
    and calculates the dew point

    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.powered = False
        self.control = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from mycodo.mycodo_client import DaemonControl

        self.control = DaemonControl()
        self.sensor = AM2315(self.input_dev.i2c_bus)

    def get_measurement(self):
        """Gets the humidity and temperature."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        temperature = None
        humidity = None
        dew_point = None
        measurements_success = False

        # Try twice to get measurement. This prevents an anomaly where
        # the first measurement fails if the sensor has just been powered
        # for the first time.
        for _ in range(2):
            dew_point, humidity, temperature = self.return_measurements()
            if dew_point is not None:
                measurements_success = True
                break
            time.sleep(2)

        if measurements_success:
            self.value_set(0, temperature)
            self.value_set(1, humidity)

            if self.is_enabled(0) and self.is_enabled(1):
                self.value_set(2, dew_point)
                self.value_set(3, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

            return self.return_dict
        else:
            self.logger.debug("Could not acquire a measurement")

    def return_measurements(self):
        # Retry measurement if CRC fails
        for num_measure in range(3):
            humidity, temperature = self.sensor.data()
            if humidity is None:
                self.logger.debug("Measurement {num} returned failed CRC".format(num=num_measure))
            else:
                dew_pt = calculate_dewpoint(temperature, humidity)
                return dew_pt, humidity, temperature
            time.sleep(2)

        self.logger.error("All measurements returned failed CRC")
        return None, None, None


class AM2315:
    """Wrapping for an AOSONG AM2315 humidity and temperature sensor.

    Provides simple access to a AM2315 chip using the quickwire i2c module
    Attributes:
        bus:       Int containing the smbus channel.
        address:   AM2315 bus address
        bus:       quickwire i2c object instance.
        lastError: String containing the last error string.Formatter
        debug:     bool containing debug state
    """
    def __init__(self, bus, address=0x5C, debug=False):
        import quick2wire.i2c as i2c
        self.i2c = i2c
        self.channel = bus
        self.address = address   				  # Default address 0x5C
        self.bus = self.i2c.I2CMaster(int(bus))        # quick2wire master
        self.lastError = None   				  # Contains last error string
        self.debug = debug       				  # Debug flag

    def data(self):
        """
        Reads the humidity and temperature from the AS2315.

        Returns:
            Tuple containing the following fields:
                humidity    - float
                temperature - float (Celsius)
        """
        # Send a wakeup call to the sensor. This call will always fail
        try:
            self.bus.transaction(self.i2c.writing(self.address, bytes([0x03,0x0,0x04])))
        except Exception:
             pass

        time.sleep(0.125)
        # Now that the device is awake, read the data
        try:
            self.bus.transaction(self.i2c.writing(self.address, bytes([0x03,0x0,0x04])))
            data = self.bus.transaction(self.i2c.reading(self.address, 0x08))
            data = bytearray(data[0])
        except IOError as e:
            self.lastError = 'I/O Error({0}): {1}'.format(e.errno,e.strerror)
            return None, None

        # 0x03-returned command, 0x04-no bytes read.
        if data[0] != 0x03 and data[1] != 0x04:
            self.lastError = 'Error reading data from AM2315 device.'
            return None, None

        # Parse the data list
        cmd_code = data[0]
        byte_cnt = data[1]
        humid_H  = data[2]
        humid_L  = data[3]
        temp_H   = data[4]
        temp_L   = data[5]
        crc_H    = data[6]
        crc_L    = data[7]

        negative = False
        humidity = (humid_H*256+humid_L)/10

        # Check for negative temp
        # 16-Sep-2014
        # Thanks to Ethan for pointing out this bug!
        # ethansimpson@xtra.co.nz
        if temp_H&0x08:
           negative = True
        # Mask the negative flag
        temp_H &=0x7F

        tempC = (temp_H * 256 + temp_L) / 10

        if negative:
            tempC = -abs(tempC)

        # tempF = self.c_to_f(tempC)

        # Verify CRC
        crc = 256 * crc_L + crc_H
        t = bytearray([data[0], data[1], data[2], data[3], data[4], data[5]])
        c = self.verify_crc(t)

        if crc != c:
            self.lastError = 'CRC error in sensor data.'
            return None, None

        return humidity, tempC

    def humidity(self):
        """Read humidity data from the sensor.

        Returns:
            float = humidity reading, None if error
        """
        time.sleep(.25)
        data = self.data()
        if data is not None:
            return self.data()[0]
        return None

    def temperature(self, fahrenheit=False):
        """Read temperature data from the sensor. (Celsius is default)

        Args:
            bool - if True returns temp in Fahrenheit. Default=False
        Returns:
            float = humidity reading, None if error
        """
        time.sleep(.25)
        data = self.data()
        if data is None:
            return None
        if fahrenheit:
            return self.data()[2]
        return self.data()[1]

    def fahrenheit(self):
        return self.temperature(True)

    def celsius(self):
        return self.temperature()

    @staticmethod
    def verify_crc(char):
        """Returns the 16-bit CRC of sensor data."""
        crc = 0xFFFF
        for l in char:
            crc = crc ^ l
            for _ in range(1,9):
                if crc & 0x01:
                    crc = crc >> 1
                    crc = crc ^ 0xA001
                else:
                    crc = crc >> 1
        return crc

    def c_to_f(self, celsius):
        """Convert Celsius to Fahrenheit.

        Params:
            celsius: int containing C temperature

        Returns:
            String with Fahrenheit conversion. None if error.
        """
        if celsius is None:
           return

        if celsius == 0:
            return 32

        try:
            temp_f = float((celsius * 9 / 5) + 32)
            return (math.trunc(temp_f * 10)) / 10
        except Exception:
            self.lastError = 'Error converting %s celsius to fahrenheit' % celsius
            return None

    def last_error(self):
        return self.lastError
