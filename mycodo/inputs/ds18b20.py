# coding=utf-8
import logging
import time

from w1thermsensor import W1ThermSensor

from .base_input import AbstractInput

logger = logging.getLogger("mycodo.inputs.ds18b20")


class DS18B20Sensor(AbstractInput):
    """ A sensor support class that monitors the DS18B20's temperature """

    def __init__(self, pin, testing=False):
        super(DS18B20Sensor, self).__init__()
        self._temperature = None
        self.pin = pin

        if not testing:
            self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, self.pin)

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

    @property
    def temperature(self):
        """ DS18B20 temperature in celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the DS18B20's temperature in Celsius by reading the temp file and div by 1000"""
        self._temperature = None
        temperature = None
        n = 2
        for i in range(n):
            try:
                temperature = self.sensor.get_temperature()
            except Exception as e:
                if i == n:
                    logger.exception(
                        "{cls} raised an exception when taking a reading: "
                        "{err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)
        return temperature

    def read(self):
        """
        Takes a reading from the DS18B20 and updates the self._temperature value

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
