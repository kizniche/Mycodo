# coding=utf-8
#
# example_dummy_output.py - Example Output module
#
from flask_babel import lazy_gettext
from mycodo.outputs.base_output import AbstractOutput


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
        'measurement': 'duration_time',
        'unit': 's'
    }
}

# Output information
OUTPUT_INFORMATION = {
    # A unique output name used to distinguish it from others
    'output_name_unique': 'example_output_dummy',

    # A friendly/common name for the output to display to the user
    'output_name': lazy_gettext('Example Dummy Output'),

    # The dictionary of measurements for this output. Don't edit this.
    'measurements_dict': measurements_dict,

    # Should the output controller handle storing whether the output is on or off?
    # If this output module should handle determining the output state, choose False
    'on_state_internally_handled': False,

    # Type of output. Options: "on_off", "pwm", "volume"
    'output_types': ['on_off'],

    # A message to display at the top of the output options
    'message': 'Information about this output.',

    # Form input options that are enabled or disabled
    'options_enabled': [
        'gpio_pin',           # Enables an input field to set a GPIO pin
        'current_draw',       # Enables an input field to set the Amp-draw
        'button_on',          # Shows a button to turn the output on
        'button_send_duration'  # Shows an input field and an button to turn on for a duration
    ],
    'options_disabled': [
        'interface'  # Show the interface (as a disabled input)
    ],

    # Any dependencies required by the output module
    'dependencies_module': [],

    # The interface or interfaces that can be used with this module
    # A custom interface can be used.
    # Options: SHELL, PYTHON, GPIO, I2C, FTDI, UART
    'interfaces': ['GPIO'],

    # Custom actions that will appear at the top of the options in the user interface.
    # Buttons are required to have a function with the same name that will be executed
    # when the button is pressed. Input values will be passed to the button in a
    # dictionary. See the function input_button() at the end of this module.
    'custom_actions_message': 'This is a message displayed for custom actions.',
    'custom_actions': [
        {
            'id': 'input_value',
            'type': 'float',
            'name': lazy_gettext('Value Name'),
            'phrase': 'A description for this input'
        },
        {
            'id': 'input_button',
            'type': 'button',
            'name': lazy_gettext('Button Name')
        }
    ],

    # Custom options that can be set by the user in the web interface.
    'custom_options_message': 'This is a message displayed for custom options.',
    'custom_options': [
        {
            'id': 'bool_value',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Bool Value'),
            'phrase': lazy_gettext('Set a bool value')
        },
        {
            'id': 'float_value',
            'type': 'float',
            'default_value': 5.0,
            'constraints_pass': constraints_pass_fan_seconds,
            'name': lazy_gettext('Decimal Value'),
            'phrase': lazy_gettext('Set a decimal value')
        },
        {
            'id': 'range_value',
            'type': 'select',
            'default_value': '3000',
            'options_select': [
                ('1000', '0 - 1000'),
                ('2000', '0 - 2000'),
                ('3000', '0 - 3000'),
                ('5000', '0 - 5000'),
            ],
            'constraints_pass': constraints_pass_measure_range,
            'name': lazy_gettext('Range Value'),
            'phrase': lazy_gettext('Select a range value')
        }
    ],
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        # Initialize custom option variables to None
        self.bool_value = None
        self.float_value = None
        self.range_value = None

        # Set custom option variables to defaults or user-set values
        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        if not testing:
            # Variable to store whether the output has been successfully set up
            self.output_setup = None

            # Since on_state_internally_handled is False, we will store the state of the output
            self.output_state = False

            # Variables set by the user interface
            self.gpio_pin = output.pin

            self.logger.info(
                "Output class initialized with: "
                "gpio_pin: {gp}; "
                "bool_value: {bt}, {bv}; "
                "float_value: {ft}, {fv}; "
                "range_value: {rt}, {rv}".format(
                    gp=self.gpio_pin,
                    bt=type(self.bool_value), bv=self.bool_value,
                    ft=type(self.float_value), fv=self.float_value,
                    rt=type(self.range_value), rv=self.range_value))

    def output_switch(self, state, amount=None, duty_cycle=None):
        """
        Set the output on, off, to an amount, or to a duty cycle
        if output_types is 'on_off', state will represent the on or off state to set
        if output_types is 'volume', amount will represent the volume to set
        if output_types is 'pwm', duty_cycle will represent the duty cycle to set
        """
        if state == 'on':
            self.logger.info("Output turned on")
            self.output_state = True
        elif state == 'off':
            self.logger.info("Output turned off")
            self.output_state = False

    def is_on(self):
        """
        Code to return the state of the output.

        This can also be handled internally by the output controller if on_state_internally_handled is set to True.
        """
        if self.is_setup():
            if self.output_state:
                return self.output_state  # Output is on
            else:
                return False  # Output is off
        else:
            return None  # Indicate output is unconfigured

    def is_setup(self):
        """Returns whether the output has successfully been set up"""
        if self.output_setup:
            return True
        return False

    def setup_output(self):
        """Code executed when Mycodo starts up to initialize the output"""
        self.logger.info("Output set up")
        self.output_setup = True

    def input_button(self, args_dict):
        """Executed when custom action button pressed"""
        if 'input_value' not in args_dict:
            self.logger.error("Cannot execute function without an input value")
            return
        if not isinstance(args_dict['input_value'], float):
            self.logger.error("Input value does not represent a float: '{}', type: {}".format(
                args_dict['input_value'], type(args_dict['input_value'])))
            return

        try:
            self.logger.info("Received your input of {} and executing this log write".format(
                args_dict['input_value']))
        except:
            self.logger.exception("Could not execute code")
