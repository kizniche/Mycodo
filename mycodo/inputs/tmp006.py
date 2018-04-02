# coding=utf-8
import logging

from .base_input import AbstractInput
from .sensorutils import convert_units

logger = logging.getLogger("mycodo.inputs.tmp006")


class TMP006Sensor(AbstractInput):
    """ A sensor support class that monitors the TMP006's die and object temperatures """

    def __init__(self, address, bus, convert_to_unit=None, testing=False):
        super(TMP006Sensor, self).__init__()
        self._temperature_die = None
        self._temperature_object = None

        self.i2c_address = address
        self.i2c_bus = bus
        self.convert_to_unit = convert_to_unit

        if not testing:
            from Adafruit_TMP import TMP006
            self.sensor = TMP006.TMP006(
                address=self.i2c_address, busnum=self.i2c_bus)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature_die={tdie})(temperature_object={tobj})>".format(
            cls=type(self).__name__,
            tdie="{0:.2f}".format(self._temperature_die),
            tobj="{0:.2f}".format(self._temperature_object))

    def __str__(self):
        """ Return temperature information """
        return "Temperature (Die): {tdie}, Temperature (Object): {tobj}".format(
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

    @property
    def temperature_die(self):
        """ Die temperature in celsius """
        if self._temperature_die is None:  # update if needed
            self.read()
        return self._temperature_die

    @property
    def temperature_object(self):
        """ Object temperature in celsius """
        if self._temperature_object is None:  # update if needed
            self.read()
        return self._temperature_object

    def get_measurement(self):
        """ Gets the TMP006's temperature in Celsius """
        self._temperature_die = None
        self._temperature_object = None

        self.sensor.begin()

        temperature_die = convert_units(
            'temperature_die', 'celsius', self.convert_to_unit,
            self.sensor.readDieTempC())
        temperature_object = convert_units(
            'temperature_object', 'celsius', self.convert_to_unit,
            self.sensor.readObjTempC())

        return temperature_die, temperature_object

    def read(self):
        """
        Takes a reading from the TMP006 and updates the self._temperature_die
        and self._temperature_object values

        :returns: None on success or 1 on error
        """
        try:
            self._temperature_die, self._temperature_object = self.get_measurement()
            if self._temperature_die is not None:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
