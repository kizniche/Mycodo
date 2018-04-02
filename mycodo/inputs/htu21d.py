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

import logging
import time

from .base_input import AbstractInput
from .sensorutils import convert_units
from .sensorutils import dewpoint

logger = logging.getLogger("mycodo.inputs.htu21d")


class HTU21DSensor(AbstractInput):
    """
    A sensor support class that measures the HTU21D's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, bus, convert_to_unit=None, testing=False):
        super(HTU21DSensor, self).__init__()
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        self.I2C_bus_number = bus
        self.address = 0x40  # HTU21D-F Address
        self.convert_to_unit = convert_to_unit

        if not testing:
            import pigpio
            self.pi = pigpio.pi()

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dewpoint={dpt})(humidity={hum})(temperature={temp})>".format(
            cls=type(self).__name__,
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Dew Point: {dpt}, Humidity: {hum}, Temperature: {temp}".format(
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ HTU21DSensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def dew_point(self):
        """ HTU21D dew point in Celsius """
        if self._dew_point is None:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ HTU21D relative humidity in percent """
        if self._humidity is None:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ HTU21D temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        if not self.pi.connected:  # Check if pigpiod is running
            logger.error("Could not connect to pigpiod."
                         "Ensure it is running and try again.")
            return None, None, None

        self.htu_reset()
        # wtreg = 0xE6
        # rdreg = 0xE7
        rdtemp = 0xE3
        rdhumi = 0xE5

        handle = self.pi.i2c_open(self.I2C_bus_number, self.address)  # open i2c bus
        self.pi.i2c_write_byte(handle, rdtemp)  # send read temp command
        time.sleep(0.055)  # readings take up to 50ms, lets give it some time
        (_, byte_array) = self.pi.i2c_read_device(handle, 3)  # vacuum up those bytes
        self.pi.i2c_close(handle)  # close the i2c bus
        t1 = byte_array[0]  # most significant byte msb
        t2 = byte_array[1]  # least significant byte lsb
        temp_reading = (t1 * 256) + t2  # combine both bytes into one big integer
        temp_reading = float(temp_reading)
        temperature = ((temp_reading / 65536) * 175.72) - 46.85  # formula from datasheet

        handle = self.pi.i2c_open(self.I2C_bus_number, self.address)  # open i2c bus
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
        dew_pt = dewpoint(temperature, humidity)

        # Check for conversions
        dew_pt = convert_units(
            'dewpoint', 'celsius', self.convert_to_unit, dew_pt)
        temperature = convert_units(
            'temperature', 'celsius', self.convert_to_unit, temperature)

        return dew_pt, humidity, temperature

    def read(self):
        """
        Takes a reading from the HTU21D and updates the self._humidity and
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._dew_point,
             self._humidity,
             self._temperature) = self.get_measurement()
            if self._dew_point is not None:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

    def htu_reset(self):
        reset = 0xFE
        handle = self.pi.i2c_open(self.I2C_bus_number, self.address)  # open i2c bus
        self.pi.i2c_write_byte(handle, reset)  # send reset command
        self.pi.i2c_close(handle)  # close i2c bus
        time.sleep(0.2)  # reset takes 15ms so let's give it some time
