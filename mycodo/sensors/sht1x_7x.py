# coding=utf-8
import logging
from sht_sensor import Sht
from sht_sensor import ShtVDDLevel
from .base_sensor import AbstractSensor

logger = logging.getLogger(__name__)


class SHT1x7xSensor(AbstractSensor):
    """
    A sensor support class that measures the SHT1x7x's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, pin, clock_pin, voltage):
        super(SHT1x7xSensor, self).__init__()
        self._dew_point = 0.0
        self._humidity = 0.0
        self._temperature = 0.0
        self.pin = pin
        self.clock_pin = clock_pin

        sht_sensor_vdd_value = {
            2.5: ShtVDDLevel.vdd_2_5,
            3.0: ShtVDDLevel.vdd_3,
            3.5: ShtVDDLevel.vdd_3_5,
            4.0: ShtVDDLevel.vdd_4,
            5.0: ShtVDDLevel.vdd_5
        }
        self.voltage = sht_sensor_vdd_value[round(float(voltage), 1)]

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dewpoint={dpt})(humidity={hum})(temperature={temp})>".format(
            cls=type(self).__name__,
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Dew Point: {dpt}, Humidity: {hum}, Temperature: {temp}".format(
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SHT1x7xSensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    def info(self):
        conditions_measured = [
            ("Dew Point", "dewpoint", "float", "0.00", self._dew_point, self.dew_point),
            ("Humidity", "humidity", "float", "0.00", self._humidity, self.humidity),
            ("Temperature", "temperature", "float", "0.00", self._temperature, self.temperature)
        ]
        return conditions_measured

    @property
    def dew_point(self):
        """ SHT1x7x dew point in Celsius """
        if not self._dew_point:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ SHT1x7x relative humidity in percent """
        if not self._humidity:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ SHT1x7x temperature in Celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        sht_sensor = Sht(self.clock_pin, self.pin, voltage=self.voltage)
        temperature = sht_sensor.read_t()
        humidity = sht_sensor.read_rh()
        dew_point = sht_sensor.read_dew_point(temperature, humidity)
        return dew_point, humidity, temperature

    def read(self):
        """
        Takes a reading from the SHT1x7x and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._dew_point,
             self._humidity,
             self._temperature) = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1
