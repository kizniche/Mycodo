# coding=utf-8

import smbus
import time
import RPi.GPIO as GPIO
from MCP342x import MCP342x


class MCP342x_read(object):
    def __init__(self, address, channel, gain, resolution):
        self._voltage = None
        self.i2c_address = address
        self.channel = channel
        self.gain = gain
        self.resolution = resolution
        if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
            self.I2C_bus_number = 1
        else:
            self.I2C_bus_number = 0
        self.running = True


    def read(self):
        try:
            time.sleep(1)
            self.bus = smbus.SMBus(self.I2C_bus_number)
            adc = MCP342x(self.bus, self.i2c_address, channel=self.channel, gain=self.gain, resolution=self.resolution)
            self._voltage = adc.convert_and_read()
        except:
            return 1

    @property
    def voltage(self):
        return self._voltage

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return voltage information.
        """
        if self.read():
            return None
        response = {
            'voltage': float("{}".format(self.voltage))
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    mcp = MCP342x_read(0, 0x68, 0, 18)

    for measure in mcp:
        print("Voltage: {}".format(measure['voltage']))
        time.sleep(1)
