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

import pigpio
import time
import RPi.GPIO as GPIO
from sensorutils import dewpoint

class HTU21D_read(object):
    def __init__(self, bus):
        self.pi = pigpio.pi()
        # HTU21D-F Commands
        self.rdtemp = 0xE3
        self.rdhumi = 0xE5
        self.wtreg = 0xE6
        self.rdreg = 0xE7
        self.reset = 0xFE

        self.address = 0x40  # HTU21D-F Address
        self._temperature = 0
        self._humidity = 0
        self.I2C_bus_number = bus
        self.running = True

    def read(self):
        try:
            self.htu_reset()
            self._temperature = self.read_temperature()
            self._humidity = self.read_humidity()
        except:
            return 1

    def htu_reset(self):
        handle = self.pi.i2c_open(self.I2C_bus_number, self.address) # open i2c bus
        self.pi.i2c_write_byte(handle, self.reset) # send reset command
        self.pi.i2c_close(handle) # close i2c bus
        time.sleep(0.2) # reset takes 15ms so let's give it some time

    def read_temperature(self):
        handle = self.pi.i2c_open(self.I2C_bus_number, self.address) # open i2c bus
        self.pi.i2c_write_byte(handle, self.rdtemp) # send read temp command
        time.sleep(0.055) # readings take up to 50ms, lets give it some time
        (count, byteArray) = self.pi.i2c_read_device(handle, 3) # vacuum up those bytes
        self.pi.i2c_close(handle) # close the i2c bus
        t1 = byteArray[0] # most significant byte msb
        t2 = byteArray[1] # least significant byte lsb
        temp_reading = (t1 * 256) + t2 # combine both bytes into one big integer
        temp_reading = float(temp_reading)
        return ((temp_reading / 65536) * 175.72 ) - 46.85 # formula from datasheet

    def read_humidity(self):
        handle = self.pi.i2c_open(self.I2C_bus_number, self.address) # open i2c bus
        self.pi.i2c_write_byte(handle, self.rdhumi) # send read humi command
        time.sleep(0.055) # readings take up to 50ms, lets give it some time
        (count, byteArray) = self.pi.i2c_read_device(handle, 3) # vacuum up those bytes
        self.pi.i2c_close(handle) # close the i2c bus
        h1 = byteArray[0] # most significant byte msb
        h2 = byteArray[1] # least significant byte lsb
        humi_reading = (h1 * 256) + h2 # combine both bytes into one big integer
        humi_reading = float(humi_reading)
        uncomp_humidity = ((humi_reading / 65536) * 125 ) - 6 # formula from datasheet
        return ((25 - self.temperature) * -0.15) + uncomp_humidity

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature and humidity information.
        """
        if self.read():
            return None
        response = {
            'humidity': float("{0:.2f}".format(self.humidity)),
            'temperature': float("{0:.2f}".format(self.temperature)),
            'dewpoint': float("{0:.2f}".format(dewpoint(self.temperature, self.humidity)))
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
        I2C_bus_number = 1
    else:
        I2C_bus_number = 0
    htu21d = HTU21D_read(I2C_bus_number)

    for measurements in htu21d:
        print("Temperature: {}".format(measurements['temperature']))
        print("Humidity: {}".format(measurements['humidity']))
        print("Dew Point: {}".format(dewpoint(measurements['temperature'], measurements['humidity'])))
        time.sleep(1)
