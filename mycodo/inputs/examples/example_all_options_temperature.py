# coding=utf-8
import logging

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    #
    # Required options
    #

    # Unique name (must be unique from all other inputs)
    'input_name_unique': 'SEN_TEMP_01',

    # Descriptive information
    'input_manufacturer': 'Company YY',
    'input_name': 'Temp Sen01',

    # Measurement information
    'measurements_name': 'Temperature',
    'measurements_list': ['temperature'],  # List of strings

    # Web User Interface display options
    # Options that are enabled will be editable from the input options page.
    # Options that are disabled will appear on the input options page but not be editable.
    # There are several location options available for use:
    # 'location', 'gpio_location', 'i2c_location', 'bt_location', and 'uart_location'
    'options_enabled': ['i2c_location', 'uart_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface'],


    #
    # Non-required options
    #

    # Python module dependencies
    # This must be a module that is able to be installed with pip or apt (pypi, git, and apt examples below)
    # Leave the list empty if there are no dependencies
    'dependencies_module': [  # List of tuples
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-pypi', 'bluepy', 'bluepy==1.1.4'),
        ('pip-git', 'adafruit-bme280', 'git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280'),
        ('apt', 'whiptail', 'whiptail'),
        ('apt', 'zsh', 'zsh'),
        ('internal', 'pip-exists pigpio', 'pigpio'),
        ('internal', 'pip-exists wiringpi', 'wiringpi'),
        ('internal', 'file-exists /usr/local/include/bcm2835.h', 'bcm2835')
    ],

    # Interface options: 'GPIO', 'I2C', 'UART', '1WIRE', 'BT', 'Mycodo', 'RPi'
    'interfaces': [  # List of strings
        'I2C',
        'UART'
    ],

    # I2C options
    # Enter more than one if multiple addresses exist.
    'i2c_location': [  # List of strings
        '0x01',
        '0x02'
    ],
    'i2c_address_editable': False,  # Boolean

    # UART options
    'uart_location': '/dev/ttyAMA0',  # String
    'baud_rate': 9600,  # Integer
    'pin_cs': 8,  # Integer
    'pin_miso': 9,  # Integer
    'pin_mosi': 10,  # Integer
    'pin_clock': 11,  # Integer

    # Bluetooth options
    'bt_location': '00:00:00:00:00:00',  # String
    'bt_adapter': 'hci0',  # String

    # Custom location options
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

    # 1-Wire option
    # Setting the following to True will use the module w1thermsensor to scan
    # for 1-Wire devices. Put 'location' in 'options_enabled' to display a
    # drop-down menu of detected devices.
    # Note: 'location' should not be set, only added to 'options_enabled'.
    'w1thermsensor_detect_1wire': False,  # Boolean

    # Host options
    'times_check': 1,  # Integer
    'deadline': 2,  # Integer
    'port': 80,  # Integer

    # Signal options
    'weighting': 0.0,  # Float
    'sample_time': 2.0,  # Float

    # Analog-to-digital converter options
    'analog_to_digital_converter': True,  # Boolean
    'adc_channel': [  # List of tuples
        (0, 'Channel 0'),
        (1, 'Channel 1'),
        (2, 'Channel 2'),
        (3, 'Channel 3')
    ],
    'adc_gain': [  # List of tuples
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (8, '8'),
        (16, '16')
    ],
    'adc_volts_min': -4.096,  # Float
    'adc_volts_max': 4.096,  # Float

    # Miscellaneous options
    'period': 15,  # Float
    'cmd_command': 'shuf -i 50-70 -n 1',  # String
    'ref_ohm': 0,  # Integer

    # The following options must either be a list of tuples or a list containing one string
    # 'several_options': [
    #     (1, 'option 1 name'),
    #     (2, 'option 2 name')
    # ],
    # 'one_option': ['12'],
    'resolution': [],  # List of tuples or string
    'resolution_2': [],  # List of tuples or string
    'sensitivity': [],  # List of tuples or string
    'thermocouple_type': [],  # List of tuples or string
    'sht_voltage': [  # List of tuples or string
        ('2.5', '2.5V'),
        ('3.0', '3.0V'),
        ('3.5', '3.5V'),
        ('4.0', '4.0V'),
        ('5.0', '5.0V')
    ],

    # Custom options
    # Values are stored as text, therefore if you require a float or integer,
    # cast it as such in the "Load custom options" section in __init__
    # Example: self.another_option = int(value)
    # Make sure your string represents the type you're attempting to cast
    'custom_options': [
        {
            'id': 'modulate_fan',
            'type': 'checkbox',
            'default_value': True,
            'name': lazy_gettext('Fan Off After Measure'),
            'phrase': lazy_gettext('Turn the fan on only during the measurement')
        },
        {
            'id': 'another_option',
            'type': 'textbox',
            'default_value': 'my_text_value',
            'name': lazy_gettext('Another Custom Option'),
            'phrase': lazy_gettext('Another custom option description (this is translatable)')
        }

    ]
}


class InputModule(AbstractInput):
    """ A dummy sensor support class """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.{name_lower}".format(
            name_lower=INPUT_INFORMATION['input_name_unique'].lower()))

        #
        # Initialize the measurements this input returns
        #
        self._temperature = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.{name_lower}_{id}".format(
                    name_lower=INPUT_INFORMATION['input_name_unique'].lower(),
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
            # Load custom options
            #

            self.modulate_fan = None
            self.another_option = None

            for each_option in input_dev.custom_options.split(';'):
                option = each_option.split(',')[0]
                value = each_option.split(',')[1]
                if option == 'modulate_fan':
                    self.modulate_fan = value
                if option == 'another_option':
                    self.another_option = value

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
