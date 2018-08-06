# coding=utf-8
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Based on the BMP280 driver with BME280 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
import logging

from .base_input import AbstractInput
from .sensorutils import altitude
from .sensorutils import convert_units
from .sensorutils import dewpoint


class BME280Sensor(AbstractInput):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(BME280Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.bme280")
        self._altitude = None
        self._dew_point = None
        self._humidity = None
        self._pressure = None
        self._temperature = None

        if not testing:
            from Adafruit_BME280 import BME280
            self.logger = logging.getLogger(
                "mycodo.inputs.bme280_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.sensor = BME280(address=self.i2c_address,
                                 busnum=self.i2c_bus)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(altitude={alt})(dewpoint={dpt})" \
               "(humidity={hum})(pressure={press})" \
               "(temperature={temp})>".format(
                cls=type(self).__name__,
                alt="{0:.6f}".format(self._altitude),
                dpt="{0:.6f}".format(self._dew_point),
                hum="{0:.6f}".format(self._humidity),
                press='{0:.6f}'.format(self._pressure),
                temp="{0:.6f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Altitude: {alt}, Dew Point: {dpt}, " \
               "Humidity: {hum}, Pressure: {press}, " \
               "Temperature: {temp}".format(
                alt="{0:.6f}".format(self._altitude),
                dpt="{0:.6f}".format(self._dew_point),
                hum="{0:.6f}".format(self._humidity),
                press='{0:.6f}'.format(self._pressure),
                temp="{0:.6f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(altitude=float(self._altitude),
                    dewpoint=float(self._dew_point),
                    humidity=float(self._humidity),
                    pressure=float(self._pressure),
                    temperature=float(self._temperature))

    @property
    def altitude(self):
        """ BME280 altitude in meters """
        if self._altitude is None:  # update if needed
            self.read()
        return self._altitude

    @property
    def dew_point(self):
        """ BME280 dew point in Celsius """
        if self._dew_point is None:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ BME280 relative humidity in percent """
        if self._humidity is None:  # update if needed
            self.read()
        return self._humidity

    @property
    def pressure(self):
        """ BME280 pressure in Pascals """
        if self._pressure is None:  # update if needed
            self.read()
        return self._pressure

    @property
    def temperature(self):
        """ BME280 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self._altitude = None
        self._dew_point = None
        self._humidity = None
        self._pressure = None
        self._temperature = None

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            self.sensor.read_temperature())

        pressure_pa = self.sensor.read_pressure()
        pressure = convert_units(
            'pressure', 'Pa', self.convert_to_unit,
            pressure_pa)

        alt = convert_units(
            'altitude', 'm', self.convert_to_unit,
            altitude(pressure_pa))

        humidity = convert_units(
            'humidity', 'percent', self.convert_to_unit,
            self.sensor.read_humidity())

        dew_pt = convert_units(
            'dewpoint', 'C', self.convert_to_unit,
            dewpoint(temperature, humidity))

        return alt, dew_pt, humidity, pressure, temperature

    def read(self):
        """
        Takes a reading from the BME280 and updates the self._humidity and
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._altitude,
             self._dew_point,
             self._humidity,
             self._pressure,
             self._temperature) = self.get_measurement()
            if self._altitude is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
