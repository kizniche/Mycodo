# coding=utf-8


import time
import RPi.GPIO as GPIO
import Adafruit_TMP.TMP006 as TMP006


class TMP006_read(object):
    def __init__(self, i2c_address):
        self._temperature_die = None
        self._temperature_object = None
        self.i2c_address = int(i2c_address, 16)
        if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
            self.I2C_bus_number = '1'
        else:
            self.I2C_bus_number = '0'
        self.running = True

    def read(self):
        try:
            sensor = TMP006.TMP006(address=self.i2c_address, busnum=self.I2C_bus_number)
            sensor.begin()
            self._temperature_object = sensor.readObjTempC()
            self._temperature_die = sensor.readDieTempC()
        except:
            return 1

    @property
    def temperature_die(self):
        return self._temperature_die

    @property
    def temperature_object(self):
        return self._temperature_object

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0

    def next(self):
        """
        Call the read method and return temperature information.
        """
        if self.read():
            return None
        response = {
            'temperature_die': float("{0:.2f}".format(self.temperature_die)),
            'temperature_object': float("{0:.2f}".format(self.temperature_object))
        }
        return response

    def stopSensor(self):
        self.running = False



if __name__ == "__main__":
    tmp006 = TMP006_read('0x40')

    for measurement in tmp006:
        print("Temperature (die): {} C".format(measurement['temperature_die']))
        print("Temperature (object): {} C".format(measurement['temperature_object']))
        time.sleep(2)
