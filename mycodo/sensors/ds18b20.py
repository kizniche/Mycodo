# coding=utf-8

import time
from w1thermsensor import W1ThermSensor

class DS18B20(object):
    def __init__(self, pin):
        self._temperature = 0
        self.pin = pin
        self.running = True

    def read(self):
        temperature = []
        # Check continuity of two readings and return average
        for x in range(2):
            time.sleep(1)
            try:
                temperature.append(W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, self.pin).get_temperature())
            except:
                return 1
        if (None in temperature or
                max(temperature)-min(temperature) > 10):
            self._temperature = None
        else:
            self._temperature = sum(temperature, 0.0) / len(temperature)

    @property
    def temperature(self):
        return self._temperature

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature information.
        """
        if self.read() or self.temperature is None:
            return None
        response = {
            'temperature': float("{0:.2f}".format(self.temperature))
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    ds18b20 = DS18B20('00000531d23c')

    for measurement in ds18b20:
        print("Temperature: {}".format(measurement['temperature']))
        time.sleep(1)
