# coding=utf-8

import time
from sht_sensor import Sht


class SHT1x_7x_read(object):
    def __init__(self, pin, clock_pin, voltage):
        self._temperature = 0
        self._humidity = 0
        self._dewpoint = 0
        self.pin = pin
        self.clock_pin = clock_pin
        self.voltage = "{}V".format(voltage)
        self.running = True

    def read(self):
        try:
            sht_sensor = Sht(self.clock_pin, self.pin, voltage=self.voltage)
            self._temperature = sht_sensor.read_t()
            self._humidity = sht_sensor.read_rh()
            self._dewpoint = sht_sensor.read_dew_point(self.temperature, self.humidity)
        except:
            return 1

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity

    @property
    def dewpoint(self):
        return self._dewpoint

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
            'dewpoint': float("{0:.2f}".format(self.dewpoint))
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    sht = SHT1x_7x_read(16, 17, 3.5)

    for measurements in sht:
        print("Temperature: {}".format(measurements['temperature']))
        print("Humidity: {}".format(measurements['humidity']))
        print("Dew Point: {}".format(measurements['dewpoint']))
        time.sleep(1)
