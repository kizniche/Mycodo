# coding=utf-8
import logging

from .base_input import AbstractInput
from .sensorutils import convert_units


class CCS811Sensor(AbstractInput):
    """
    A sensor support class that measures the CC2811's voc, temperature
    and co2

    """

    def __init__(self, input_dev, testing=False):
        super(CCS811Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.ccs811")
        self._co2 = None
        self._voc = None
        self._temperature = None

        if not testing:
            from Adafruit_CCS811 import Adafruit_CCS811
            self.logger = logging.getLogger(
                "mycodo.inputs.ccs811_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.sensor = Adafruit_CCS811(address=self.i2c_address, busnum=self.i2c_bus)
            while not self.sensor.available():
                pass
            temp = self.sensor.calculateTemperature()
            self.sensor.tempOffset = temp - 25.0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(co2={co2})(voc={voc})(temperature={temp})>".format(
            cls=type(self).__name__,
            co2="{0}".format(self._co2),
            voc="{0}".format(self._voc),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "CO2: {co2}, VOC: {voc}, Temperature: {temp}".format(
            co2="{0}".format(self._co2),
            voc="{0}".format(self._voc),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ CCS811Sensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(co2=float('{0}'.format(self._co2)),
                    voc=float('{0}'.format(self._voc)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def co2(self):
        """ CC2811 CO2 measurement (ppm) """
        if self._co2 is None:  # update if needed
            self.read()
        return self._co2

    @property
    def voc(self):
        """ CC2811 VOC measurement (ppb) """
        if self._voc is None:  # update if needed
            self.read()
        return self._voc

    @property
    def temperature(self):
        """ CC2811 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the CO2, VOC, and temperature """
        self._co2 = None
        self._voc = None
        self._temperature = None

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            self.sensor.calculateTemperature())

        if not self.sensor.readData():
            co2 = convert_units(
                'co2', 'ppm', self.convert_to_unit,
                self.sensor.geteCO2())
            voc = convert_units(
                'voc', 'ppb', self.convert_to_unit,
                self.sensor.getTVOC())
            return co2, voc, temperature
        else:
            return None, None, None

    def read(self):
        """
        Takes a reading from the AM2315 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            self._co2, self._voc, self._temperature = self.get_measurement()
            if self._co2 is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
