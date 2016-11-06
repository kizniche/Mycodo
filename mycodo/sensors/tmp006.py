# coding=utf-8
import logging
import Adafruit_TMP.TMP006 as TMP006
from .base_sensor import AbstractSensor


class TMP006Sensor(AbstractSensor):
    """ A sensor support class that monitors the TMP006's die and object temperatures """

    def __init__(self, address, bus):
        super(TMP006Sensor, self).__init__()
        self.i2c_address = address
        self.i2c_bus = bus
        self._temperature_die = 0.0
        self._temperature_object = 0.0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature_die={tdie})(temperature_object={tobj})>".format(
            cls=type(self).__name__,
            tdie="{0:.2f}".format(self._temperature_die),
            tobj="{0:.2f}".format(self._temperature_object))

    def __str__(self):
        """ Return temperature information """
        return "temperature_die: {tdie}, temperature_object: {tobj}".format(
            tdie="{0:.2f}".format(self._temperature_die),
            tobj="{0:.2f}".format(self._temperature_object))

    def __iter__(self):  # must return an iterator
        """ TMP006Sensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature_die=float('{0:.2f}'.format(self._temperature_die)),
                    temperature_object=float('{0:.2f}'.format(self._temperature_object)))

    def get_measurement(self):
        """ Gets the TMP006's temperature in Celsius """
        sensor = TMP006.TMP006(address=self.i2c_address, busnum=self.i2c_bus)
        sensor.begin()
        return sensor.readDieTempC(), sensor.readObjTempC()

    @property
    def temperature_die(self):
        """ Die temperature in celsius """
        if not self._temperature_die:  # update if needed
            self.read()
        return self._temperature_die

    @property
    def temperature_object(self):
        """ Object temperature in celsius """
        if not self._temperature_object:  # update if needed
            self.read()
        return self._temperature_object

    def read(self):
        """
        Takes a reading from the TMP006 and updates the self._temperature_die
        and self._temperature_object values

        :returns: None on success or 1 on error
        """
        try:
            self._temperature_die, self._temperature_object = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logging.error("Unknown error in {cls}.get_measurement(): {err}".format(cls=type(self).__name__, err=e))
        return 1
