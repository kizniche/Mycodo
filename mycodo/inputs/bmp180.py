# coding=utf-8
import logging
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BMP180',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BMP180',
    'measurements_name': 'Pressure/Temperature',
    'measurements_dict': ['altitude', 'pressure', 'temperature'],
    'options_enabled': ['period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_BMP', 'Adafruit_BMP'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x77'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BMP 180/085's humidity,
    temperature, and pressure, then calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.bmp180")
        self._altitude = None
        self._pressure = None
        self._temperature = None

        if not testing:
            from Adafruit_BMP import BMP085
            self.logger = logging.getLogger(
                "mycodo.bmp180_{id}".format(id=input_dev.unique_id.split('-')[0]))
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.bmp = BMP085.BMP085(busnum=self.i2c_bus)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})(pressure={press})" \
               "(altitude={alt})>".format(
                cls=type(self).__name__,
                alt="{0:.6f}".format(self._altitude),
                press="{0:.6f}".format(self._pressure),
                temp="{0:.6f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Temperature: {temp}, Pressure: {press}, " \
               "Altitude: {alt}".format(
                alt="{0:.6f}".format(self._altitude),
                press="{0:.6f}".format(self._pressure),
                temp="{0:.6f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(altitude=float(self._altitude),
                    pressure=float(self._pressure),
                    temperature=float(self._temperature))

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
            'temperature', 'C', self.convert_to_unit,
            self.bmp.read_temperature())

        pressure = convert_units(
            'pressure', 'Pa', self.convert_to_unit,
            self.bmp.read_pressure())

        altitude = convert_units(
            'altitude', 'm', self.convert_to_unit,
            self.bmp.read_altitude())

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
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
