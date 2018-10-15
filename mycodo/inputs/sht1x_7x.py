# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SHT1x_7x',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT1x/7x',
    'measurements_name': 'Humidity/Temperature',
    'measurements_list': ['dewpoint', 'humidity', 'temperature'],
    'options_enabled': ['gpio_location', 'sht_voltage', 'period', 'pin_clock', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'sht_sensor', 'sht_sensor')
    ],
    'interfaces': ['GPIO'],
    'pin_clock': 11,
    'sht_voltage': [
        ('2.5', '2.5V'),
        ('3.0', '3.0V'),
        ('3.5', '3.5V'),
        ('4.0', '4.0V'),
        ('5.0', '5.0V')
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT1x7x's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.sht1x_7x")
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        if not testing:
            from sht_sensor import Sht
            from sht_sensor import ShtVDDLevel
            self.logger = logging.getLogger(
                "mycodo.sht1x_7x_{id}".format(id=input_dev.unique_id.split('-')[0]))
            self.gpio = int(input_dev.gpio_location)
            self.clock_pin = input_dev.clock_pin
            self.convert_to_unit = input_dev.convert_to_unit
            sht_sensor_vdd_value = {
                2.5: ShtVDDLevel.vdd_2_5,
                3.0: ShtVDDLevel.vdd_3,
                3.5: ShtVDDLevel.vdd_3_5,
                4.0: ShtVDDLevel.vdd_4,
                5.0: ShtVDDLevel.vdd_5
            }
            self.sht_voltage = sht_sensor_vdd_value[round(float(input_dev.sht_voltage), 1)]
            self.sht_sensor = Sht(self.clock_pin,
                                  self.gpio,
                                  voltage=self.sht_voltage)

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
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            self.sht_sensor.read_t())

        humidity = self.sht_sensor.read_rh()

        dew_point = self.sht_sensor.read_dew_point(temperature, humidity)
        dew_point = convert_units(
            'dewpoint', 'C', self.convert_to_unit, dew_point)

        humidity = convert_units(
            'humidity', 'percent', self.convert_to_unit,
            humidity)

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
            if self._dew_point is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
