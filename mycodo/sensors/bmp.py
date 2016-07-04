# coding=utf-8

import time
import Adafruit_BMP.BMP085 as BMP085


class BMP(object):
    def __init__(self):
        self._temperature = None
        self._pressure = None
        self._altitude = None
        self.running = True

    def read(self):
        try:
            time.sleep(2)
            self._temperature = BMP085.BMP085().read_temperature()
            self._pressure = BMP085.BMP085().read_pressure()
            self._altitude = BMP085.BMP085().read_altitude()
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
    bmp = BMP()

    for measure in bmp:
        print("Temperature: {}".format(measure['temperature']))
        print("Pressure: {}".format(measure['pressure']))
        print("Altitude: {}".format(measure['altitude']))
        time.sleep(1)
