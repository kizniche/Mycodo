# coding=utf-8

import logging
import Adafruit_ADS1x15


class ADS1x15Read(object):
    """ Sensor  """
    def __init__(self, address, bus, channel, gain):
        self.logger = logging.getLogger('mycodo.ads1x15-{bus}-{add}'.format(
            bus=bus, add=address))
        self._voltage = None
        self.i2c_address = address
        self.i2c_bus = bus
        self.channel = channel
        self.adc = Adafruit_ADS1x15.ADS1115(address=self.i2c_address,
                                            busnum=self.i2c_bus)

        # Choose a gain of 1 for reading voltages from 0 to 4.09V.
        # Or pick a different gain to change the range of voltages that are read:
        #  - 2/3 = +/-6.144V
        #  -   1 = +/-4.096V
        #  -   2 = +/-2.048V
        #  -   4 = +/-1.024V
        #  -   8 = +/-0.512V
        #  -  16 = +/-0.256V
        # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
        self.gain = gain
        self.running = True

    def read(self):
        """ Take measurement """
        try:
            self._voltage = self.adc.read_adc(
                self.channel, gain=self.gain) / 10000.0
        except Exception as e:
            self.logger.exception(
                "{cls} raised an error during read() call: "
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

    def stop_sensor(self):
        self.running = False


if __name__ == "__main__":
    ads = ADS1x15Read(0x48, 1, 0, 1)
    print("Channel 0: {}".format(ads.next()))
    ads = ADS1x15Read(0x48, 1, 1, 1)
    print("Channel 1: {}".format(ads.next()))
    ads = ADS1x15Read(0x48, 1, 2, 1)
    print("Channel 2: {}".format(ads.next()))
    ads = ADS1x15Read(0x48, 1, 3, 1)
    print("Channel 3: {}".format(ads.next()))
