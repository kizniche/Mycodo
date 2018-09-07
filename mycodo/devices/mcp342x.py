# coding=utf-8
import logging
import time

import smbus
from MCP342x import MCP342x


class MCP342xRead(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.mcp342x')
        self.acquiring_measurement = False
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

    @property
    def voltage(self):
        return self._voltage

    def get_measurement(self):
        self._voltage = None
        voltage = self.adc.convert_and_read()
        return voltage

    def read(self):
        """
        Takes a reading

        :returns: None on success or 1 on error
        """
        if self.acquiring_measurement:
            self.logger.error("Attempting to acquire a measurement when a"
                              " measurement is already being acquired.")
            return 1
        try:
            self.acquiring_measurement = True
            self._voltage = self.get_measurement()
            if self._voltage is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        finally:
            self.acquiring_measurement = False
        return 1


if __name__ == "__main__":
    class Data:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    input_dev = Data(id='00001',
                     location='0x68',
                     i2c_bus=1,
                     adc_channel=0,
                     adc_gain=1,
                     adc_resolution=12)

    mcp = MCP342xRead(input_dev)

    while 1:
        mcp.read()
        print("Voltage: {}".format(mcp.voltage))
        time.sleep(1)
