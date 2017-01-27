# coding=utf-8
import logging
from tentacle_pi import AM2315
from sensorutils import dewpoint
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.am2315")


class AM2315Sensor(AbstractSensor):
    """
    A sensor support class that measures the AM2315's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, bus):
        super(AM2315Sensor, self).__init__()
        self.I2C_bus_number = str(bus)
        self._dew_point = 0.0
        self._humidity = 0.0
        self._temperature = 0.0
        self.am = None

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
        """ AM2315Sensor iterates through live measurement readings """
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
        """ AM2315 dew point in Celsius """
        if not self._dew_point:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ AM2315 relative humidity in percent """
        if not self._humidity:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ AM2315 temperature in Celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.am = AM2315.AM2315(0x5c, "/dev/i2c-" + self.I2C_bus_number)
        temperature, humidity, crc_check = self.am.sense()
        if crc_check != 1:
            return 1
        else:
            dew_pt = dewpoint(temperature, humidity)
            return dew_pt, humidity, temperature

    def read(self):
        """
        Takes a reading from the AM2315 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            self._dew_point, self._humidity, self._temperature = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1
