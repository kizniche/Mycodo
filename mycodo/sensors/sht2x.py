# coding=utf-8
#
# From https://github.com/ControlEverythingCommunity/SHT25/blob/master/Python/SHT25.py

import smbus
import time
import RPi.GPIO as GPIO

from sensorutils import dewpoint


class SHT2x_read(object):
    def __init__(self, address, bus):
        self._temperature = 0
        self._humidity = 0
        self._dewpoint = 0
        self.i2c_address = address
        self.i2c_bus = bus
        self.running = True

    def read(self):
        try:
            bus = smbus.SMBus(self.i2c_bus)
            # SHT25 address, 0x40(64)
            # Send temperature measurement command
            #       0xF3(243)   NO HOLD master
            bus.write_byte(self.i2c_address, 0xF3)
            time.sleep(0.5)
            # SHT25 address, 0x40(64)
            # Read data back, 2 bytes
            # Temp MSB, Temp LSB
            data0 = bus.read_byte(self.i2c_address)
            data1 = bus.read_byte(self.i2c_address)
            self._temperature = -46.85 + (((data0 * 256 + data1) * 175.72) / 65536.0)

            # SHT25 address, 0x40(64)
            # Send humidity measurement command
            #       0xF5(245)   NO HOLD master
            bus.write_byte(self.i2c_address, 0xF5)
            time.sleep(0.5)
            # SHT25 address, 0x40(64)
            # Read data back, 2 bytes
            # Humidity MSB, Humidity LSB
            data0 = bus.read_byte(self.i2c_address)
            data1 = bus.read_byte(self.i2c_address)
            self._humidity = -6 + (((data0 * 256 + data1) * 125.0) / 65536.0)

            self._dewpoint = dewpoint(self.temperature, self.humidity)
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
    if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
        I2C_bus_number = 1
    else:
        I2C_bus_number = 0
    sht = SHT2x_read(0x40, I2C_bus_number)

    for measurements in sht:
        print("Temperature: {}".format(measurements['temperature']))
        print("Humidity: {}".format(measurements['humidity']))
        print("Dew Point: {}".format(measurements['dewpoint']))
        time.sleep(1)
