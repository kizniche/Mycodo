# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput


def constraints_pass_fan_seconds(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: value
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


def constraints_pass_measure_range(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['1000', '2000', '3000', '5000']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',  # Note: This is the "Measurement ID" on the measurements configuration page
        'unit': 'C'  # Note: This is the "Unit ID" on the measurements configuration page
    }
}

# Input information
INPUT_INFORMATION = {
    #
    # Required options
    #

    # Unique name (must be unique from all other inputs)
    'input_name_unique': 'SEN_TEMP_01',

    # Descriptive information
    'input_manufacturer': 'Company YY',
    'input_name': 'Example Temperature Sensor 01',
    'input_name_short': 'Ex. Temp. Sensor 01',  # A shorter name for display purposes
    'input_library': 'Library Name',

    # Measurement information
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,

    # Links to documentation. Can be a URL string or a list of URL strings
    'url_manufacturer': 'https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html',
    'url_datasheet': 'https://www.st.com/resource/en/datasheet/vl53l0x.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/3317',
        'https://www.pololu.com/product/2490'
    ],

    # For use with Inputs that store multiple measurements.
    # Set True if all measurements should be stored in the database with the same timestamp.
    # Set False to use the timestamp generated when self.value_set() is used to save measurement.
    'measurements_use_same_timestamp': True,

    # Web User Interface display options
    # Options that are enabled will be editable from the input options page.
    # Options that are disabled will appear on the input options page but not be editable.
    # There are several location options available for use:
    # 'location', 'gpio_location', 'i2c_location', 'bt_location', 'ftdi_location', and 'uart_location'
    'options_enabled': [
        'i2c_location',
        'ftdi_location',
        'uart_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    #
    # Non-required options
    #

    # Add a message that the user can see when they view the options of the Input.
    # This will be displayed at the top of the options when the user expands the input with the "+" icon.
    'message': "Don't forget to do x and y before activating this Input",

    # Python module dependencies
    # This must be a module that is able to be installed with pip or apt (pypi, git, and apt examples below)
    # Leave the list empty if there are no dependencies
    'dependencies_module': [  # List of tuples
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3'),
        ('pip-pypi', 'bluepy', 'bluepy==1.1.4'),
        ('pip-pypi', 'adafruit-bme280', 'git+https://github.com/adafruit/Adafruit_Python_BME280.git'),
        ('apt', 'whiptail', 'whiptail'),
        ('apt', 'zsh', 'zsh'),
        ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio'),
        ('pip-pypi', 'pigpio', 'pigpio==1.78'),
        ('internal', 'pip-exists wiringpi', 'wiringpi'),
        ('internal', 'file-exists /usr/local/include/bcm2835.h', 'bcm2835')
    ],

    # A message to be displayed on the dependency install page
    'dependencies_message': 'Are you sure you want to install these dependencies? They require...',

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

    # Host options
    'times_check': 1,  # Integer
    'deadline': 2,  # Integer
    'port': 80,  # Integer

    # Signal options
    'weighting': 0.0,  # Float
    'sample_time': 2.0,  # Float

    # Analog-to-digital converter options
    'analog_to_digital_converter': True,  # Boolean
    'adc_gain': [  # List of tuples
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (8, '8'),
        (16, '16')
    ],
    'scale_from_min': -4.096,  # Float
    'scale_from_max': 4.096,  # Float

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

    # Custom options that can be set by the user in the web interface.
    'custom_options_message': 'This is a message displayed for custom options.',
    'custom_options': [
        {
            'id': 'fan_modulate',
            'type': 'bool',
            'default_value': True,
            'name': 'Fan Off After Measure',
            'phrase': 'Turn the fan on only during the measurement'
        },
        {  # This starts a new line for the next options
            'type': 'new_line'
        },
        {
            'id': 'fan_seconds',
            'type': 'float',
            'default_value': 5.0,
            'constraints_pass': constraints_pass_fan_seconds,
            'name': 'Fan On Duration (Seconds)',
            'phrase': 'How long to turn the fan on before acquiring measurements'
        },
        {  # Adding 'disabled': True will make the option unable to be changed. Useful for default options or options determined as a result of other options.
            'id': 'disabled_option_1',
            'type': 'text',
            'default_value': 'Disabled Text Field',
            'disabled': True,
            'name': 'Disabled Option',
            'phrase': "The user can't change this option"
        },
        {  # This message will be displayed on its own line
            'type': 'message',
            'default_value': 'Another message between options',
        },
        {
            'id': 'measure_range',
            'type': 'select',
            'default_value': '5000',
            'options_select': [
                ('1000', '0 - 1000 ppmv'),
                ('2000', '0 - 2000 ppmv'),
                ('3000', '0 - 3000 ppmv'),
                ('5000', '0 - 5000 ppmv'),
            ],
            'constraints_pass': constraints_pass_measure_range,
            'name': 'Measurement Range',
            'phrase': 'Set the measuring range of the sensor'
        }
    ],

    # Custom actions are buttons and input fields that appear on the web UI for users to
    # execute functions within the Input class, such as to perform calibration. See the
    # button_one() and button_two() functions at the end of the class.
    'custom_commands_message': 'This is a message displayed for custom actions.',
    'custom_commands': [
        {
            'id': 'button_one_value',
            'type': 'integer',
            'default_value': 650,
            'name': 'Button One Value',
            'phrase': 'Value for button one.'
        },
        {
            'id': 'button_one',
            'type': 'button',
            'name': 'Button One',
            'phrase': "This is button one"
        },
        {
            'id': 'button_two_value',
            'type': 'integer',
            'default_value': 1500,
            'name': 'Button Two Value',
            'phrase': 'Value for button two.'
        },
        {
            'id': 'button_two',
            'type': 'button',
            'name': 'Button Two',
            'phrase': "This is button two"
        }
    ]
}


class InputModule(AbstractInput):
    """A dummy sensor support class."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        #
        # Initialize variables (set to None)
        #

        self.random = None
        self.interface = None
        self.resolution = None
        self.i2c_address = None
        self.i2c_bus = None

        #
        # Set variables to custom options
        #

        # Initialize custom option variables to None
        self.fan_modulate = None
        self.fan_seconds = None
        self.measure_range = None

        if not testing:
            # Set custom option variables to defaults or user-set values
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)

    def initialize(self):
        self.interface = self.input_dev.interface

        #
        # Begin dependent modules loading
        #

        import random
        self.random = random

        #
        # Load optional settings
        #

        self.resolution = self.input_dev.resolution

        #
        # Initialize the sensor class
        #

        if self.interface == 'I2C':
            self.i2c_address = int(str(self.input_dev.i2c_location), 16)
            self.i2c_bus = self.input_dev.i2c_bus
            # Intitialize this particular interface for the Input
            # self.sensor = dependent_module.MY_SENSOR_CLASS(
            #     i2c_address=self.i2c_address,
            #     i2c_bus=self.i2c_bus,
            #     resolution=self.resolution)

        elif self.interface == 'UART':
            # No UART driver available for this input
            pass

    def get_measurement(self):
        """Gets the temperature and humidity."""
        #
        # Copy measurements dictionary
        #

        self.return_dict = copy.deepcopy(measurements_dict)

        #
        # Begin sensor measurement code
        #

        self.value_set(0, self.random.randint(50, 70))

        #
        # End sensor measurement code
        #

        self.logger.info(
            "This INFO message will always be displayed. "
            "self.fan_modulate: {}, "
            "self.fan_seconds: {}, "
            "self.measure_range: {}.".format(
                self.fan_modulate, self.fan_seconds, self.measure_range))

        self.logger.debug(
            "This DEBUG message will only be displayed if the "
            "Debug option is enabled.")

        return self.return_dict

    def button_one(self, args_dict):
        self.logger.error("Button One Pressed!: {}".format(int(args_dict['button_one_value'])))

    def button_two(self, args_dict):
        self.logger.error("Button Two Pressed!: {}".format(int(args_dict['button_two_value'])))
