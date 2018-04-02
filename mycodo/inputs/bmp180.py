# coding=utf-8
import logging
import time

from .base_input import AbstractInput
from .sensorutils import convert_units

logger = logging.getLogger("mycodo.inputs.bmp180")


class BMP180Sensor(AbstractInput):
    """
    A sensor support class that measures the BMP 180/085's humidity,
    temperature, and pressure, then calculates the altitude and dew point

    """

    def __init__(self, bus, convert_to_unit=None, testing=False):
        super(BMP180Sensor, self).__init__()
        self._altitude = None
        self._pressure = None
        self._temperature = None

        self.I2C_bus_number = bus
        self.convert_to_unit = convert_to_unit

        if not testing:
            from Adafruit_BMP import BMP085
            self.bmp = BMP085.BMP085(busnum=self.I2C_bus_number)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})(pressure={press})" \
               "(altitude={alt})>".format(
                cls=type(self).__name__,
                alt="{0:.2f}".format(self._altitude),
                press=self._pressure,
                temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Temperature: {temp}, Pressure: {press}, " \
               "Altitude: {alt}".format(
                alt="{0:.2f}".format(self._altitude),
                press="{0}".format(self._pressure),
                temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(altitude=float('{0:.2f}'.format(self._altitude)),
                    pressure=int(self._pressure),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def altitude(self):
        """ BMP180/085 altitude in meters """
        if self._altitude is None:  # update if needed
            self.read()
        return self._altitude

    @property
    def pressure(self):
        """ BME180/085 pressure in Pascals """
        if self._pressure is None:  # update if needed
            self.read()
        return self._pressure

    @property
    def temperature(self):
        """ BMP180/085 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the measurement in units by reading the BMP180/085 """
        time.sleep(2)
        temperature = convert_units(
            'temperature', 'celsius', self.convert_to_unit,
            self.bmp.read_temperature())
        pressure = self.bmp.read_pressure()
        altitude = self.bmp.read_altitude()
        altitude = convert_units(
            'altitude', 'meters', self.convert_to_unit, altitude)
        return temperature, pressure, altitude

    def read(self):
        """
        Takes a reading from the BMP180/085 and updates the self._humidity and
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            self._temperature, self._pressure, self._altitude = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
