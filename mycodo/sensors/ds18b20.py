# coding=utf-8
import logging
from w1thermsensor import W1ThermSensor
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.ds18b20")


class DS18B20Sensor(AbstractSensor):
    """ A sensor support class that monitors the DS18B20's temperature """

    def __init__(self, pin):
        super(DS18B20Sensor, self).__init__()
        self.pin = pin
        self._temperature = 0.0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__, temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "Temperature: {}".format("{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ DS18B20Sensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    def info(self):
        conditions_measured = [
            ("Temperature", "temperature", "float", "0.00",
             self._temperature, self.temperature)
        ]
        return conditions_measured

    @property
    def temperature(self):
        """ DS18B20 temperature in celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the DS18B20's temperature in Celsius by reading the temp file and div by 1000"""
        return W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, self.pin).get_temperature()

    def read(self):
        """
        Takes a reading from the DS18B20 and updates the self._temperature value

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
