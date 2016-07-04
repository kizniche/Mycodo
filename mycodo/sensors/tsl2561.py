# coding=utf-8


import time
import RPi.GPIO as GPIO
from tentacle_pi.TSL2561 import TSL2561


class TSL2561_read(object):
    def __init__(self, i2c_address):
        self._lux = None
        self.i2c_address = int(i2c_address, 16)
        if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
            self.I2C_bus_number = '1'
        else:
            self.I2C_bus_number = '0'
        self.running = True

    def read(self):
        try:
            tsl = TSL2561(self.i2c_address, "/dev/i2c-"+self.I2C_bus_number)
            tsl.enable_autogain()
            # tsl.set_gain(16)
            tsl.set_time(0x00)
            self._lux = tsl.lux()
        except:
            return 1

    @property
    def lux(self):
        return self._lux


    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return lux information.
        """
        if self.read():
            return None
        response = {
            'lux': self.lux
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    tsl2561 = TSL2561_read('0x39')

    for measurement in tsl2561:
        print("Lumenosity: {} lux".format(measurement['lux']))
        time.sleep(3)
