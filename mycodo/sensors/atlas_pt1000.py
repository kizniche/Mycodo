# coding=utf-8
import logging
from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.atlas_pt1000")


class AtlasPT1000Sensor(AbstractSensor):
    """ A sensor support class that monitors the PT1000's temperature """

    def __init__(self, address, bus):
        super(AtlasPT1000Sensor, self).__init__()
        self._temperature = 0.0
        self.address = address
        self.running = True
        self.I2C_bus_number = bus
        self.atlas_temp = AtlasScientificI2C(
            address=self.address, bus=self.I2C_bus_number)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "Temperature: {temp}".format(
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ Atlas_PT1000Sensor iterates through live temperature readings """
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
        """ CPU temperature in celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the Atlas PT1000's temperature in Celsius """
        temp_str = self.atlas_temp.query('R')
        # the temperature return string, if successfully read, will be
        # "Command succeeded X.XX", where X denotes the temperature
        if 'Command succeeded' in temp_str:
            raise Exception(
                "Sensor read unsuccessful: {err}".format(err=temp_str))
        else:
            return float(temp_str[18:24])

    def read(self):
        """
        Takes a reading from the PT-1000 and updates self._temperature

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1
