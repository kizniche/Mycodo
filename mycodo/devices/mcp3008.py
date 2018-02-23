# coding=utf-8
import logging

import Adafruit_MCP3008


class MCP3008Read(object):
    """ ADC Read """
    def __init__(self, clockpin, cspin, misopin, mosipin, channel):
        self.logger = logging.getLogger(
            'mycodo.mcp3008-{clock}-{cs}-{miso}-{mosi}-{chan}'.format(
                clock=clockpin, cs=cspin, miso=misopin,
                mosi=mosipin, chan=channel))
        self._voltage = None
        self.channel = channel

        self.adc = Adafruit_MCP3008.MCP3008(clk=clockpin,
                                            cs=cspin,
                                            miso=misopin,
                                            mosi=mosipin)

    def read(self):
        """ Take a measurement """
        try:
            self._voltage = (self.adc.read_adc(self.channel) / 1023.0) * 3.3
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
