# coding=utf-8
import logging

from .base_input import AbstractInput
from .sensorutils import convert_units


class MAX31855Sensor(AbstractInput):
    """
    A sensor support class that measures the MAX31855's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(MAX31855Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.max31855")
        self._temperature = None
        self._temperature_die = None

        self.pin_clock = input_dev.pin_clock
        self.pin_cs = input_dev.pin_cs
        self.pin_miso = input_dev.pin_miso
        self.convert_to_unit = input_dev.convert_to_unit

        if not testing:
            import Adafruit_MAX31855.MAX31855 as MAX31855
            self.logger = logging.getLogger(
                "mycodo.inputs.max31855_{id}".format(id=input_dev.id))
            self.sensor = MAX31855.MAX31855(self.pin_clock,
                                            self.pin_cs,
                                            self.pin_miso)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature_die={tdie})(temperature={temp})>".format(
            cls=type(self).__name__,
            tdie="{0:.2f}".format(self._temperature_die),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Temperature (Die): {tdie}, Temperature: {temp}".format(
            tdie="{0:.2f}".format(self._temperature_die),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature_die=float('{0:.2f}'.format(self._temperature_die)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ MAX31855 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    @property
    def temperature_die(self):
        """ MAX31855 temperature in Celsius """
        if self._temperature_die is None:  # update if needed
            self.read()
        return self._temperature_die

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self._temperature = None
        self._temperature_die = None

        temp = self.sensor.readTempC()
        temp = convert_units(
            'temperature', 'celsius', self.convert_to_unit, temp)
        temp_die = self.sensor.readInternalC()
        temp_die = convert_units(
            'temperature_die', 'celsius', self.convert_to_unit, temp_die)
        return temp, temp_die

    def read(self):
        """
        Takes a reading from the MAX31855 and updates the self._humidity and
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._temperature,
             self._temperature_die) = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
