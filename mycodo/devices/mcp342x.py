# coding=utf-8

import logging
import smbus
import time
from MCP342x import MCP342x

logger = logging.getLogger('mycodo.devices.mcp342x')


class MCP342xRead(object):
    """ Sensor """
    def __init__(self, address, bus, channel, gain, resolution):
        self._voltage = None
        self.i2c_address = address
        self.bus = smbus.SMBus(bus)
        self.channel = channel
        self.gain = gain
        self.resolution = resolution

    def read(self):
        """ Take a measurement """
        try:
            time.sleep(1)
            adc = MCP342x(self.bus,
                          self.i2c_address,
                          channel=self.channel,
                          gain=self.gain,
                          resolution=self.resolution)
            self._voltage = adc.convert_and_read()
        except Exception as e:
            logger.error("{cls} raised exception during read(): "
                         "{err}".format(cls=type(self).__name__, err=e))
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


if __name__ == "__main__":
    mcp = MCP342xRead(0x68, 1, 1, 0, 18)

    for measure in mcp:
        print("Voltage: {}".format(measure['voltage']))
        time.sleep(1)
