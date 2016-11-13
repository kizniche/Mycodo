# coding=utf-8
import smbus
import time


class ChirpSensor(object):
    def __init__(self, address, bus):
        self.address = address
        self.bus = smbus.SMBus(bus)
        self._lux = 0
        self._moisture = 0
        self._temperature = 0.0

    def read(self):
        try:
            self._lux = self.light()
            self._moisture = self.moist()
            self._temperature = self.temp() / 10.0
        except:
            return 1

    @property
    def lux(self):
        return self._lux

    @property
    def moisture(self):
        return self._moisture

    @property
    def temperature(self):
        return self._temperature

    def __iter__(self):  # must return an iterator
        """ ChirpSensor iterates through live measurement readings """
        return self

    def next(self):
        """
        Call the read method and return temperature, pressure, and altitude information.
        """
        if self.read():
            return None
        response = {
            'temperature': float("{0:.2f}".format(self.temperature)),
            'lux': self.lux,
            'moisture': self.moisture
        }
        return response

    def stopSensor(self):
        self.running = False

    def get_reg(self, reg):
        # read 2 bytes from register
        val = self.bus.read_word_data(self.address, reg)
        # return swapped bytes (they come in wrong order)
        return (val >> 8) + ((val & 0xFF) << 8)

    def reset(self):
        # To reset the sensor, write 6 to the device I2C address
        self.bus.write_byte(self.address, 6)

    def set_addr(self, new_addr):
        # To change the I2C address of the sensor, write a new address
        # (one byte [1..127]) to register 1; the new address will take effect after reset
        self.bus.write_byte_data(self.address, 1, new_addr)
        self.reset()
        # self.address = new_addr

    def moist(self):
        # To read soil moisture, read 2 bytes from register 0
        return self.get_reg(0)

    def temp(self):
        # To read temperature, read 2 bytes from register 5
        return self.get_reg(5)

    def light(self):
        # To read light level, start measurement by writing 3 to the
        # device I2C address, wait for 3 seconds, read 2 bytes from register 4
        self.bus.write_byte(self.address, 3)
        time.sleep(1.5)
        return self.get_reg(4)
