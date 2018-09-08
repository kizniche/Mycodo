# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units


# Input information
INPUT_INFORMATION = {
    # Unique name (must be unique from all other inputs)
    'unique_name_input': 'SEN_HUM_01',

    # Descriptive information
    'input_manufacturer': 'Company XX',
    'common_name_input': 'Hum Sen01',

    # Measurement information
    'common_name_measurements': 'Humidity',
    'unique_name_measurements': ['humidity'],  # List of strings

    # Python module dependencies
    # This must be a module that is able to be installed with pip via pypi.org
    # Leave the list empty if there are no pip or github dependencies
    'dependencies_pypi': ['random'],  # List of strings
    'dependencies_github': [],  # List of strings

    #
    # The below options are available from the input_dev variable
    # See the example, below: "self.resolution = input_dev.resolution"
    #

    # Interface options: 'I2C', 'UART'
    'interfaces': ['I2C', 'UART'],  # List of strings

    # I2C options
    # Enter more than one if multiple addresses exist.
    'i2c_location': ['0x01'],  # List of strings
    'i2c_address_editable': True,  # Boolean

    # Display options
    'options_enabled': ['period', 'convert_unit', 'pre_output', 'uart_location', 'baud_rate', 'resolution'],
    'options_disabled': ['i2c_location'],

    # Non-standard (I2C, UART, etc.) location setting
    'location': '',  # String

    # UART options
    'uart_location': '/dev/ttyAMA0',  # String
    'baud_rate': 9600,  # Integer
    'pin_cs': None,  # Integer
    'pin_miso': None,  # Integer
    'pin_mosi': None,  # Integer
    'pin_clock': None,  # Integer

    # Analog-to-digital converter options
    'adc_measure': None,  # String
    'adc_measure_units': None,  # String
    'convert_to_unit': [],  # List of strings
    'adc_volts_min': None,  # Float
    'adc_volts_max': None,  # Float

    # Miscellaneous options
    'period': None,  # Float (Input Period, Default: 15.0)
    'cmd_command': None,  # String
    'cmd_measurement': None,  # String
    'cmd_measurement_units': None,  # String
    'resolution': [],  # List of integers
    'resolution_2': [],  # List of integers
    'sensitivity': [],  # List of integers
    'thermocouple_type': [],  # List of strings
    'ref_ohm': None,  # Integer

    #
    # Custom options
    #
    # Custom options may be created if they aren't already available above
    #
    'custom_options': {
        'custom_option_1': {
            'name': 'Option 1',
            'value': '15',  # String (can be converted to other types)
            'description': 'This text describes option 1 and is translatable'
        }
    }
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
        self._humidity = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.{name_lower}_{id}".format(
                    name_lower=INPUT_INFORMATION['unique_name_input'].lower(),
                    id=input_dev.id))
            self.convert_to_unit = input_dev.convert_to_unit
            self.interface = input_dev.interface

            #
            # Begin dependent modules loading
            #

            import random
            self.random = random

            #
            # Load optional settings
            #

            self.resolution = input_dev.resolution

            #
            # Interface-specific initializations
            #

            if self.interface == 'I2C':

                self.i2c_address = int(str(input_dev.location), 16)
                self.i2c_bus = input_dev.i2c_bus
                # self.sensor = dependent_module.MY_SENSOR_CLASS(
                #     i2c_address=self.i2c_address,
                #     i2c_bus=self.i2c_bus,
                #     resolution=self.resolution)

            elif self.interface == 'UART':

                self.serial_device = input_dev.location
                self.baud_rate = input_dev.baud_rate
                # self.sensor = dependent_module.MY_SENSOR_CLASS(
                #     serial_device=self.serial_device,
                #     baud_rate=self.baud_rate,
                #     resolution=self.resolution)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(humidity={humidity})>".format(
            cls=type(self).__name__,
            humidity="{0:.2f}".format(self._humidity))

    def __str__(self):
        """ Return measurement information """
        return "Humidity {humidity}".format(
            humidity="{0:.2f}".format(self._humidity))

    def __iter__(self):  # must return an iterator
        """ DummySensor iterates through readings """
        return self

    def next(self):
        """ Get next reading """
        if self.read():
            raise StopIteration
        return dict(humidity=float('{0:.2f}'.format(self._humidity)))

    @property
    def humidity(self):
        """ humidity """
        if self._humidity is None:
            self.read()
        return self._humidity

    def get_measurement(self):
        """ Gets the temperature and humidity """
        #
        # Resetting these values ensures old measurements aren't mistaken for new measurements
        #
        self._humidity = None

        humidity = None

        #
        # Begin sensor measurement code
        #

        # I2C-specific measurement code
        if self.interface == 'I2C':
            humidity = self.random.randint(15, 45)

        # UART-specific measurement code
        elif self.interface == 'UART':
            humidity = self.random.randint(15, 45)

        #
        # End sensor measurement code
        #

        #
        # Unit conversions
        # A conversion may be specified for each measurement, if more than one unit exists for that particular measurement
        #

        # Humidity is returned in percent, but it may be converted to another specified unit (e.g. decimal)
        humidity = convert_units(
            'humidity', 'percent', self.convert_to_unit,
            humidity)

        return humidity

    def read(self):
        """
        Takes a reading and updates the self._temperature and self._humidity values

        :returns: None on success or 1 on error
        """
        try:
            #
            # These measurements must be in the same order as the returned tuple from get_measurement()
            #
            self._humidity = self.get_measurement()
            if self._humidity is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
