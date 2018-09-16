# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units
from mycodo.inputs.sensorutils import calculate_dewpoint


# Input information
# See the inputs directory for examples of working modules.
# The following link provides the full list of options with descriptions:
# https://github.com/kizniche/Mycodo/blob/single_file_input_modules/mycodo/inputs/examples/example_all_options_temperature.py
INPUT_INFORMATION = {
    'input_name_unique': 'TEST_00',
    'input_manufacturer': 'AAA Company X',
    'input_name': 'Dummy Input 00',
    'measurements_name': 'Humidity/Temperature',
    'measurements_list': ['dewpoint', 'humidity', 'temperature'],  # List of strings
    'dependencies_module': [
        ('pip-pypi', 'random', 'random')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x5c'],
    'i2c_address_editable': False,
    'options_enabled': ['period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface', 'i2c_location']
}


class InputModule(AbstractInput):
    """ Input support class """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.{name_lower}".format(
            name_lower=INPUT_INFORMATION['input_name_unique'].lower()))

        self._dewpoint = None
        self._humidity = None
        self._temperature = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.{name_lower}_{id}".format(
                    name_lower=INPUT_INFORMATION['input_name_unique'].lower(),
                    id=input_dev.id))
            self.convert_to_unit = input_dev.convert_to_unit
            self.interface = input_dev.interface

            # Load dependent modules
            import random
            self.random = random

            # Retrieve options
            # These options can be used here to initialize an I2C device or elsewhere in this class
            self.i2c_address = input_dev.i2c_location
            self.i2c_bus = input_dev.i2c_bus

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dewpoint={dewpoint})(humidity={humidity})(temperature={temperature})>".format(
            cls=type(self).__name__,
            dewpoint="{0:.2f}".format(self._dewpoint),
            humidity="{0:.2f}".format(self._humidity),
            temperature="{0:.2f}".format(self._humidity))

    def __str__(self):
        """ Return measurement information """
        return "Dewpoint: {dewpoint}, Humidity: {humidity}, Temperature: {temperature}".format(
            dewpoint="{0:.2f}".format(self._dewpoint),
            humidity="{0:.2f}".format(self._humidity),
            temperature="{0:.2f}".format(self._temperature))

    def __iter__(self):
        """ iterates through readings """
        return self

    def next(self):
        """ Get next reading """
        if self.read():
            raise StopIteration
        return dict(dewpoint=float('{0:.2f}'.format(self._dewpoint)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def dewpoint(self):
        """ dewpoint """
        if self._dewpoint is None:
            self.read()
        return self._dewpoint
    
    @property
    def humidity(self):
        """ temperature """
        if self._humidity is None:
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ temperature """
        if self._temperature is None:
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Measures temperature and humidity """
        # Resetting these values ensures old measurements aren't mistaken for new measurements
        self._dewpoint = None
        self._humidity = None
        self._temperature = None

        dewpoint = None
        humidity = None
        temperature = None

        # Actual input measurement code
        try:
            humidity = self.random.randint(0, 100)
            temperature = self.random.randint(0, 50)
            dewpoint = calculate_dewpoint(temperature, humidity)
        except Exception as msg:
            self.logger.error("Exception: {}".format(msg))

        # Unit conversions
        # A conversion may be specified for each measurement

        # Humidity is returned as %, but may be converted to another unit (e.g. decimal)
        humidity = convert_units(
            'humidity', '%', self.convert_to_unit,
            humidity)

        # Temperature is returned as C, but may be converted to another unit (e.g. K, F)
        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            temperature)

        # Dewpoint is returned as C, but may be converted to another unit (e.g. K, F)
        dewpoint = convert_units(
            'dewpoint', 'C', self.convert_to_unit,
            dewpoint)

        return humidity, temperature, dewpoint

    def read(self):
        """
        Takes a reading and updates the self._dewpoint, self._temperature, and
        self._humidity values
        :returns: None on success or 1 on error
        """
        try:
            # These measurements must be in the same order as the returned tuple from get_measurement()
            self._humidity, self._temperature, self._dewpoint = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
