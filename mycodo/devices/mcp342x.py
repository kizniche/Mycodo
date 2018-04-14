# coding=utf-8
import logging
import time

import smbus
from MCP342x import MCP342x


class MCP342xRead(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.mcp342x')
        self._voltage = None

        self.i2c_address = int(str(input_dev.location), 16)
        self.i2c_bus = input_dev.i2c_bus
        self.adc_channel = input_dev.adc_channel
        self.adc_gain = input_dev.adc_gain
        self.adc_resolution = input_dev.adc_resolution

        if not testing:
            self.logger = logging.getLogger(
                'mycodo.mcp342x_{id}'.format(id=input_dev.id))
            self.bus = smbus.SMBus(self.i2c_bus)
            self.adc = MCP342x(self.bus,
                               self.i2c_address,
                               channel=self.adc_channel,
                               gain=self.adc_gain,
                               resolution=self.adc_resolution)

    def read(self):
        """ Take a measurement """
        try:
            self._voltage = self.adc.convert_and_read()
        except Exception as e:
            self.logger.exception(
                "{cls} raised exception during read(): "
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
        return dict(voltage=float('{0:.4f}'.format(self._voltage)))


if __name__ == "__main__":
    mcp = MCP342xRead(0x68, 1, 1, 0, 18)

    for measure in mcp:
        print("Voltage: {}".format(measure['voltage']))
        time.sleep(1)
