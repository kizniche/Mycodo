# coding=utf-8
import logging
import time

from w1thermsensor import W1ThermSensor

from .base_input import AbstractInput
from .sensorutils import convert_units

logger = logging.getLogger("mycodo.inputs.ds18b20")


class MAX31850KSensor(AbstractInput):
    """ A sensor support class that monitors the MAX31850K's temperature """

    def __init__(self, pin, convert_to_unit=None, testing=False):
        super(MAX31850KSensor, self).__init__()
        self._temperature = None

        self.pin = pin
        self.convert_to_unit = convert_to_unit

        if not testing:
            self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_MAX31850K, self.pin)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__, temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "Temperature: {}".format("{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ MAX31850KSensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ MAX31850K temperature in celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the MAX31850K's temperature in Celsius """
        self._temperature = None
        temperature = None
        n = 2
        for i in range(n):
            try:
                temperature = self.sensor.get_temperature()
                break
            except Exception as e:
                if i == n:
                    logger.exception(
                        "{cls} raised an exception when taking a reading: "
                        "{err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)

        temperature = convert_units(
            'temperature', 'celsius', self.convert_to_unit,
            temperature)

        return temperature

    def read(self):
        """
        Takes a reading from the MAX31850K and updates the self._temperature value

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
