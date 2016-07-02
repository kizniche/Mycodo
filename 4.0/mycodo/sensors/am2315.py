# coding=utf-8

import time
import RPi.GPIO as GPIO
from tentacle_pi.AM2315 import AM2315


class AM2315_read(object):
    def __init__(self):
        self._temperature = 0
        self._humidity = 0
        self._crc_check = 0
        if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
            self.I2C_bus_number = '1'
        else:
            self.I2C_bus_number = '0'
        self.running = True

    def read(self):
        try:
            self.am = AM2315(0x5c, "/dev/i2c-"+self.I2C_bus_number)
            temperature, humidity, crc_check = self.am.sense()
            if crc_check != 1:
                self._temperature = self._humidity = self._crc_check = None
                return 1
            else:
                self._temperature = temperature
                self._humidity = humidity
                self._crc_check = crc_check
        except:
            return 1

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity

    @property
    def crc_check(self):
        return self._crc_check

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
            'crc_check': self.crc_check
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    am2315 = AM2315_read()

    for measure in am2315:
        print("Temperature: {}".format(measure['temperature']))
        print("Humidity: {}".format(measure['humidity']))
        print("CRC Check: {}".format(measure['crc_check']))
        time.sleep(1)
