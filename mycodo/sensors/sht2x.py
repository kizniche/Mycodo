# coding=utf-8
# From https://github.com/ControlEverythingCommunity/SHT25/blob/master/Python/SHT25.py
import logging
import smbus
import time
from sensorutils import dewpoint
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.sht2x")


class SHT2xSensor(AbstractSensor):
    """
    A sensor support class that measures the SHT2x's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, address, bus):
        super(SHT2xSensor, self).__init__()
        self.i2c_address = address
        self.i2c_bus = bus
        self._dew_point = 0.0
        self._humidity = 0.0
        self._temperature = 0.0

        self.sht2x = smbus.SMBus(self.i2c_bus)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dewpoint={dpt})(humidity={hum})(temperature={temp})>".format(
            cls=type(self).__name__,
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Dew Point: {dpt}, Humidity: {hum}, Temperature: {temp}".format(
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SHT2xSensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    def info(self):
        conditions_measured = [
            ("Dew Point", "dewpoint", "float", "0.00",
             self._dew_point, self.dew_point),
            ("Humidity", "humidity", "float", "0.00",
             self._humidity, self.humidity),
            ("Temperature", "temperature", "float", "0.00",
             self._temperature, self.temperature)
        ]
        return conditions_measured

    @property
    def dew_point(self):
        """ SHT2x dew point in Celsius """
        if not self._dew_point:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ SHT2x relative humidity in percent """
        if not self._humidity:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ SHT2x temperature in Celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self._humidity = 0.0
        self._temperature = 0.0

        try:
            # Send temperature measurement command
            # 0xF3(243) NO HOLD master
            self.sht2x.write_byte(self.i2c_address, 0xF3)
            time.sleep(0.5)
            # Read data back, 2 bytes
            # Temp MSB, Temp LSB
            data0 = self.sht2x.read_byte(self.i2c_address)
            data1 = self.sht2x.read_byte(self.i2c_address)
            temperature = -46.85 + (((data0 * 256 + data1) * 175.72) / 65536.0)
            # Send humidity measurement command
            # 0xF5(245) NO HOLD master
            self.sht2x.write_byte(self.i2c_address, 0xF5)
            time.sleep(0.5)
            # Read data back, 2 bytes
            # Humidity MSB, Humidity LSB
            data0 = self.sht2x.read_byte(self.i2c_address)
            data1 = self.sht2x.read_byte(self.i2c_address)
            humidity = -6 + (((data0 * 256 + data1) * 125.0) / 65536.0)
            dew_point = dewpoint(temperature, humidity)
            self._dew_point = dew_point
            self._humidity = humidity
            self._temperature = temperature
        except Exception as e:
            logger.exception(
                "Exception when taking a reading: {err}".format(err=e))

    def read(self):
        """
        Takes a reading from the SHT2x and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            try:
                self.get_measurement()
                if self._humidity or self._temperature:
                    return  # success - no errors
            except Exception:
                logger.debug("Error occurred during first read")

            # Send soft reset and try a second read
            self.sht2x.write_byte(self.i2c_address, 0xFE)
            time.sleep(0.1) 
            self.get_measurement()
            if self._humidity or self._temperature:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
