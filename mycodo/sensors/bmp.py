# coding=utf-8

import time
import Adafruit_BMP.BMP085 as BMP085
import RPi.GPIO as GPIO


class BMP(object):
    def __init__(self, bus):
        self.I2C_bus_number = bus
        self._temperature = None
        self._pressure = None
        self._altitude = None
        self.running = True

    def read(self):
        try:
            time.sleep(2)
            bmp = BMP085.BMP085(busnum=self.I2C_bus_number)
            self._temperature = bmp.read_temperature()
            self._pressure = bmp.read_pressure()
            self._altitude = bmp.read_altitude()
        except:
            return 1

    @property
    def temperature(self):
        return self._temperature

    @property
    def pressure(self):
        return self._pressure

    @property
    def altitude(self):
        return self._altitude

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature, pressure, and altitude information.
        """
        if self.read():
            return None
        response = {
            'temperature': float("{0:.2f}".format(self.temperature)),
            'pressure': self.pressure,
            'altitude': float("{0:.2f}".format(self.altitude))
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
        I2C_bus_number = 1
    else:
        I2C_bus_number = 0
    bmp = BMP(I2C_bus_number)

    for measure in bmp:
        print("Temperature: {}".format(measure['temperature']))
        print("Pressure: {}".format(measure['pressure']))
        print("Altitude: {}".format(measure['altitude']))
        time.sleep(1)
