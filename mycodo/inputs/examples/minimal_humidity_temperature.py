# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',  # Note: This is the "Measurement ID" on the measurements configuration page
        'unit': 'C'  # Note: This is the "Unit ID" on the measurements configuration page
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'dewpoint',
        'unit': 'C'
    }
}

# Input information
# See the inputs directory for examples of working modules.
# The following link provides the full list of options with descriptions:
# https://github.com/kizniche/Mycodo/blob/single_file_input_modules/mycodo/inputs/examples/example_all_options_temperature.py
INPUT_INFORMATION = {
    'input_name_unique': 'TEST_00',
    'input_manufacturer': 'AAA Company X',
    'input_name': 'Dummy Input 00',
    'input_library': 'random',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'message': "Note: This is just an informative note to the user.",

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug',
        'custom_actions'
    ],
    'options_disabled': [
        'interface',
        'i2c_location'
    ],

    'dependencies_module': [
        ('pip-pypi', 'random', 'random')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x5c'],
    'i2c_address_editable': False,

    'custom_options_message': 'This is a message for custom actions.',
    'custom_options': [
        {
            'id': 'option_one',
            'type': 'integer',
            'default_value': 999,
            'name': lazy_gettext('Option One Value'),
            'phrase': 'Value for option one.'
        },
    ],

    'custom_actions_message': 'This is a message for custom actions.',
    'custom_actions': [
        {
            'id': 'button_one_value',
            'type': 'integer',
            'default_value': 650,
            'name': lazy_gettext('Button One Value'),
            'phrase': 'Value for button one.'
        },
        {
            'id': 'button_one',
            'type': 'button',
            'name': lazy_gettext('Button One'),
            'phrase': "This is button one"
        },
        {
            'id': 'button_two_value',
            'type': 'integer',
            'default_value': 1500,
            'name': lazy_gettext('Button Two Value'),
            'phrase': 'Value for button two.'
        },
        {
            'id': 'button_two',
            'type': 'button',
            'name': lazy_gettext('Button Two'),
            'phrase': "This is button two"
        }
    ]
}


class InputModule(AbstractInput):
    """ Input support class """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        # Initialize custom options
        self.option_one = False
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            # Load dependent modules
            import random
            self.random = random

            self.interface = input_dev.interface

            # Retrieve options
            # These options can be used here to initialize an I2C device or elsewhere in this class
            self.i2c_address = input_dev.i2c_location
            self.i2c_bus = input_dev.i2c_bus

    def get_measurement(self):
        """ Measures temperature and humidity """
        # Resetting these values ensures old measurements aren't mistaken for new measurements
        self.return_dict = measurements_dict.copy()

        # Actual input measurement code
        try:
            humidity = self.random.randint(0, 100)
            temperature = self.random.randint(0, 50)

            self.logger.info("Option one value is {}".format(self.option_one))

            self.logger.info(
                "This INFO message will always be displayed. "
                "Acquiring measurements...")

            if self.is_enabled(0):
                self.value_set(0, temperature)

            if self.is_enabled(1):
                self.value_set(1, humidity)

            if (self.is_enabled(2) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                dewpoint = calculate_dewpoint(
                    self.value_get(0), self.value_get(1))
                self.value_set(2, dewpoint)

            self.logger.debug(
                "This DEBUG message will only be displayed if the Debug "
                "option is enabled. {}".format(self.return_dict))

            return self.return_dict
        except Exception as msg:
            self.logger.error("Exception: {}".format(msg))

    def button_one(self, args_dict):
        self.logger.error("Button One Pressed!: {}".format(int(args_dict['button_one_value'])))

    def button_two(self, args_dict):
        self.logger.error("Button Two Pressed!: {}".format(int(args_dict['button_two_value'])))
