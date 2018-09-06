# coding=utf-8
import logging

import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/../..'))

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units


# Input information
INPUT_INFORMATION = {
    # Input information
    'common_name_input': 'Temperature Sensor 01',
    'unique_name_input': 'SEN_TEMP_01',

    # Measurement information
    'common_name_measurements': 'Temperature',
    'unique_name_measurements': {
        'temperature': 'C'
    },

    # Python module dependencies
    # This must be a module that is able to be installed with pip via pypi.org
    # Leave the list empty if there are no pip or github dependencies
    'dependencies_pypi': [],
    'dependencies_github': [],

    #
    # The below options are available from the input_dev variable
    # See the example, below: "self.resolution = input_dev.resolution"
    #

    # Interface options: 'I2C' or 'UART'
    'interface': 'I2C',

    # I2C options
    'location': ['0x01', '0x02'],  # I2C address(s). Must be list. Enter more than one if multiple addresses exist.

    # UART options
    'serial_default_baud_rate': 9600,
    'pin_cs': None,
    'pin_miso': None,
    'pin_mosi': None,
    'pin_clock': None,

    # Miscellaneous options available
    'resolution': [],
    'resolution_2': [],
    'sensitivity': [],
    'thermocouple_type': [],
}

class InputModule(AbstractInput):
    """ A dummy sensor support class """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.{name_lower}".format(
            name_lower=INPUT_INFORMATION['unique_name_input'].lower()))

        #
        # Initialize the measurements this input returns
        #
        self._temperature = None

        if not testing:
            #
            # Begin dependent modules loading
            #

            # import dependent_module

            #
            # End dependent modules loading
            #

            self.logger = logging.getLogger(
                "mycodo.inputs.{name_lower}_{id}".format(
                    name_lower=INPUT_INFORMATION['unique_name_input'].lower(),
                    id=input_dev.id))
            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.resolution = input_dev.resolution
            self.convert_to_unit = input_dev.convert_to_unit

            #
            # Initialize the sensor class
            #
            # self.sensor = dependent_module.MY_SENSOR_CLASS(
            #     i2c_address=self.i2c_address,
            #     i2c_bus=self.i2c_bus,
            #     resolution=self.resolution)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temperature})>".format(
            cls=type(self).__name__,
            temperature="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Temperature: {temperature}".format(
            temperature="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ DummySensor iterates through readings """
        return self

    def next(self):
        """ Get next reading """
        if self.read():
            raise StopIteration
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ temperature """
        if self._temperature is None:
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the temperature and humidity """
        #
        # Resetting these values ensures old measurements aren't mistaken for new measurements
        #
        self._temperature = None

        temperature = None

        #
        # Begin sensor measurement code
        #

        import random
        temperature = random.randint(50, 70)

        #
        # End sensor measurement code
        #

        #
        # Unit conversions
        # A conversion may be specified for each measurement, if more than one unit exists for that particular measurement
        #

        # Temperature is returned in C, but it may be converted to another unit (e.g. K, F)
        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            temperature)

        return temperature

    def read(self):
        """
        Takes a reading and updates the self._temperature and self._humidity values

        :returns: None on success or 1 on error
        """
        try:
            #
            # These measurements must be in the same order as the returned tuple from get_measurement()
            #
            self._temperature = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
