# coding=utf-8
#
# Created in part with code with the following copyright:
#
# Copyright (c) 2014 D. Alex Gray
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN

import time

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
    'input_name_unique': 'HTU21D',
    'input_manufacturer': 'Measurement Specialties',
    'input_name': 'HTU21D',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the HTU21D's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            import pigpio

            self.i2c_bus = input_dev.i2c_bus
            self.i2c_address = 0x40  # HTU21D-F Address
            self.pi = pigpio.pi()

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.return_dict = measurements_dict.copy()

        if not self.pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod."
                              "Ensure it is running and try again.")
            return None, None, None

        self.htu_reset()
        # wtreg = 0xE6
        # rdreg = 0xE7
        rdtemp = 0xE3
        rdhumi = 0xE5

        handle = self.pi.i2c_open(self.i2c_bus, self.i2c_address)  # open i2c bus
        self.pi.i2c_write_byte(handle, rdtemp)  # send read temp command
        time.sleep(0.055)  # readings take up to 50ms, lets give it some time
        (_, byte_array) = self.pi.i2c_read_device(handle, 3)  # vacuum up those bytes
        self.pi.i2c_close(handle)  # close the i2c bus
        t1 = byte_array[0]  # most significant byte msb
        t2 = byte_array[1]  # least significant byte lsb
        temp_reading = (t1 * 256) + t2  # combine both bytes into one big integer
        temp_reading = float(temp_reading)
        temperature = ((temp_reading / 65536) * 175.72) - 46.85  # formula from datasheet

        handle = self.pi.i2c_open(self.i2c_bus, self.i2c_address)  # open i2c bus
        self.pi.i2c_write_byte(handle, rdhumi)  # send read humi command
        time.sleep(0.055)  # readings take up to 50ms, lets give it some time
        (_, byte_array) = self.pi.i2c_read_device(handle, 3)  # vacuum up those bytes
        self.pi.i2c_close(handle)  # close the i2c bus
        h1 = byte_array[0]  # most significant byte msb
        h2 = byte_array[1]  # least significant byte lsb
        humi_reading = (h1 * 256) + h2  # combine both bytes into one big integer
        humi_reading = float(humi_reading)
        uncomp_humidity = ((humi_reading / 65536) * 125) - 6  # formula from datasheet
        humidity = ((25 - temperature) * -0.15) + uncomp_humidity

        if self.is_enabled(0):
            self.value_set(0, temperature)

        if self.is_enabled(1):
            self.value_set(1, humidity)

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(2, calculate_dewpoint(
                self.value_get(0), self.value_get(1)))

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(3, calculate_vapor_pressure_deficit(
                self.value_get(0), self.value_get(1)))

        return self.return_dict

    def htu_reset(self):
        reset = 0xFE
        handle = self.pi.i2c_open(self.i2c_bus, self.i2c_address)  # open i2c bus
        self.pi.i2c_write_byte(handle, reset)  # send reset command
        self.pi.i2c_close(handle)  # close i2c bus
        time.sleep(0.2)  # reset takes 15ms so let's give it some time
