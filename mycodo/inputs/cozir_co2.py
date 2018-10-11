# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units
from mycodo.inputs.sensorutils import calculate_dewpoint

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'COZIR_CO2',
    'input_manufacturer': 'Cozir',
    'input_name': 'Cozir CO2',
    'measurements_name': 'CO2/Humidity/Temperature',
    'measurements_list': ['co2', 'dewpoint', 'humidity', 'temperature'],
    'options_enabled': ['uart_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-git', 'pycozir', 'git://github.com/pierre-haessig/pycozir.git#egg=pycozir')
    ],
    'interfaces': ['UART'],
    'uart_location': '/dev/ttyAMA0'
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the COZIR's CO2, humidity, and temperature
    and calculates the dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.cozir")
        self._co2 = None
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        if not testing:
            from pycozir import Cozir
            self.logger = logging.getLogger(
                "mycodo.inputs.cozir_{id}".format(id=input_dev.id))
            self.uart_location = input_dev.uart_location
            self.convert_to_unit = input_dev.convert_to_unit
            self.sensor = Cozir(self.uart_location)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(co2={co2})(dewpoint={dpt})(humidity={hum})(temperature={temp})>".format(
            cls=type(self).__name__,
            co2="{0:.2f}".format(self._co2),
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "CO2: {co2}, Dew Point: {dpt}, Humidity: {hum}, Temperature: {temp}".format(
            co2="{0:.2f}".format(self._co2),
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ COZIRSensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(co2=float('{0:.2f}'.format(self._co2)),
                    dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def co2(self):
        """ COZIR CO2 in ppm """
        if self._co2 is None:  # update if needed
            self.read()
        return self._co2

    @property
    def dew_point(self):
        """ COZIR dew point in Celsius """
        if self._dew_point is None:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ COZIR relative humidity in percent """
        if self._humidity is None:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ COZIR temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self._co2 = None
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        co2 = self.sensor.read_CO2()
        temperature = self.sensor.read_temperature()
        humidity = self.sensor.read_humidity()
        dew_pt = calculate_dewpoint(temperature, humidity)

        # Check for conversions
        co2 = convert_units(
            'co2', 'ppm', self.convert_to_unit, co2)

        dew_pt = convert_units(
            'dewpoint', 'C', self.convert_to_unit, dew_pt)

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit, temperature)

        humidity = convert_units(
            'humidity', 'percent', self.convert_to_unit,
            humidity)

        return co2, dew_pt, humidity, temperature

    def read(self):
        """
        Takes a reading from the COZIR and updates the self._co2, self._humidity and
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._co2,
             self._dew_point,
             self._humidity,
             self._temperature) = self.get_measurement()
            if self._dew_point is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
