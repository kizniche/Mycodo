# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units


# Input information
INPUT_INFORMATION = {
    # Unique name (must be unique from all other inputs)
    'unique_name_input': 'SEN_TEMP_01',

    # Descriptive information
    'input_manufacturer': 'Company YY',
    'common_name_input': 'Temp Sen01',

    # Measurement information
    'common_name_measurements': 'Temperature',
    'unique_name_measurements': ['temperature'],  # List of strings

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
    'interfaces': ['I2C'],  # List of strings

    # I2C options
    # Enter more than one if multiple addresses exist.
    'i2c_location': ['0x01', '0x02'],  # List of strings
    'i2c_address_editable': False,  # Boolean

    # Custom location setting
    # Only one option, editable text box:
    'location': {
        'title': 'Host',
        'phrase': 'Host name or IP address',
        'options': [('127.0.0.1', '')]
    },
    # More than one option, selectable drop-down menu:
    # 'location': {
    #     'title': 'Location Name',
    #     'phrase': 'Location Description',
    #     'options': [('1', 'Option 1'),
    #                 ('2', 'Option 2'),
    #                 ('3', 'Option 3'),]
    # },

    # Display options
    # All variables below are able to be used
    # Additionally, location, gpio_location, i2c_location, uart_location may be used
    'options_enabled': ['period', 'convert_unit', 'pre_output', 'i2c_location'],
    'options_disabled': [''],

    # 1-Wire options
    #
    # Setting the following to True will use the module w1thermsensor to scan
    # for 1-Wire devices. Put 'location' in 'options_enabled' to display a
    # drop-down menu of detected devices.
    # Note: 'location' should not be set, only added to 'options_enabled'.
    #
    'w1thermsensor_detect_1wire': False,  # Boolean

    # Bluetooth
    'bt_location': '00:00:00:00:00:00',  # String
    'bt_adapter': 'hci0',  # String

    # UART options
    'uart_location': None,  # String
    'baud_rate': None,  # Integer
    'pin_cs': None,  # Integer
    'pin_miso': None,  # Integer
    'pin_mosi': None,  # Integer
    'pin_clock': None,  # Integer

    # Host options
    'times_check': None,  # Integer
    'deadline': None,  # Integer
    'port': None,  # Integer

    # Signal options
    'weighting': 0.0,  # Float
    'sample_time': 2.0,  # Float

    # Analog-to-digital converter options
    'analog_to_digital_converter': True,  # Boolean
    'adc_channel': [(0, 'Channel 0'),
                    (1, 'Channel 1'),
                    (2, 'Channel 2'),
                    (3, 'Channel 3')],  # List of tuples
    'adc_gain': [(1, '1'),
                 (2, '2'),
                 (3, '3'),
                 (4, '4'),
                 (8, '8'),
                 (16, '16')],  # List of tuples
    'adc_volts_min': -4.096,  # Float
    'adc_volts_max': 4.096,  # Float

    # Miscellaneous options
    'period': None,  # Float (Input Period, Default: 15.0)
    'convert_to_unit': [],  # List of strings
    'cmd_command': None,  # String
    'resolution': [],  # List of tuples (e.g. [(1, 'option 1 name'), (2, 'option 2 name')]) or list containing one string (e.g. ['12'])
    'resolution_2': [],  # List of tuples (e.g. [(1, 'option 1 name'), (2, 'option 2 name')]) or list containing one string (e.g. ['12'])
    'sensitivity': [],  # List of tuples (e.g. [(1, 'option 1 name'), (2, 'option 2 name')]) or list containing one string (e.g. ['12'])
    'thermocouple_type': [],  # List of tuples (e.g. [(1, 'option 1 name'), (2, 'option 2 name')]) or list containing one string (e.g. ['12'])
    'ref_ohm': None,  # Integer
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
            # Initialize the sensor class
            #

            if self.interface == 'I2C':
                self.i2c_address = int(str(input_dev.i2c_location), 16)
                self.i2c_bus = input_dev.i2c_bus
                # self.sensor = dependent_module.MY_SENSOR_CLASS(
                #     i2c_address=self.i2c_address,
                #     i2c_bus=self.i2c_bus,
                #     resolution=self.resolution)

            elif self.interface == 'UART':
                # No UART driver available for this input
                pass

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

        temperature = self.random.randint(50, 70)

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
