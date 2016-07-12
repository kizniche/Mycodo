# coding=utf-8

import smbus
import time
import RPi.GPIO as GPIO
import Adafruit_ADS1x15


class ADS1x15_read(object):
    def __init__(self, logger, address, channel, gain):
        self.logger = logger
        self._voltage = None
        self.i2c_address = address
        self.channel = channel

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

        if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
            self.I2C_bus_number = 1
        else:
            self.I2C_bus_number = 0
        self.running = True


    def read(self):
        try:
            time.sleep(1)
            adc = Adafruit_ADS1x15.ADS1115(address=self.i2c_address, busnum=self.I2C_bus_number)
            self._voltage = adc.read_adc(self.channel, gain=self.gain)
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
    ads = ads1x15_read(0, 0x68, 0, 18)

    for measure in ads:
        print("Voltage: {}".format(measure['voltage']))
        time.sleep(1)
