# coding=utf-8

import time
from sht_sensor import Sht


class SHT(object):
    def __init__(self, pin, clock_pin, voltage):
        self._temperature = 0
        self._humidity = 0
        self.pin = pin
        self.click_pin = clock_pin
        self.voltage = voltage
        self.running = True

    def read(self):
        try:
            sht_sensor = Sht(self.clock_pin, self.pin, voltage=self.voltage)
            self._temperature = sht_sensor.read_t()
            self._humidity = sht_sensor.read_rh()
        except:
            return None

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
        if self.read() is None:
            return None
        response = {
            'humidity': self.humidity,
            'temperature': self.temperature,
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    sht = SHT(16, 17, '3.5V')

    for measure in sht:
        print("Temperature: {}".format(measure['temperature']))
        print("Humidity: {}".format(measure['humidity']))
        time.sleep(1)
