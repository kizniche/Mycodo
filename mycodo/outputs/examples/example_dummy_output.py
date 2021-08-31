# coding=utf-8
#
# example_dummy_output.py - Example Output module
#
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_value


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
    'output_name': 'Example Dummy Output',

    # Optional library name (for outputs that are named the same but use different libraries)
    'output_library': 'library_name',

    # The dictionary of measurements for this output. Don't edit this.
    'measurements_dict': measurements_dict,

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

    # Any dependencies required by the output module. An empty list means no dependencies are required.
    'dependencies_module': [],

    # A message to be displayed on the dependency install page
    'dependencies_message': 'Are you sure you want to install these dependencies? They require...',

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
            'name': 'Value Name',
            'phrase': 'A description for this input'
        },
        {
            'id': 'input_button',
            'type': 'button',
            'name': 'Button Name'
        }
    ],

    # Custom options that can be set by the user in the web interface.
    'custom_options_message': 'This is a message displayed for custom options.',
    'custom_options': [
        {
            'id': 'bool_value',
            'type': 'bool',
            'default_value': True,
            'name': 'Bool Value',
            'phrase': 'Set a bool value'
        },
        {
            'id': 'float_value',
            'type': 'float',
            'default_value': 5.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Decimal Value',
            'phrase': 'Set a decimal value'
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
            'name': 'Range Value',
            'phrase': 'Select a range value'
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

    def setup_output(self):
        """Code executed when Mycodo starts up to initialize the output"""
        # Variables set by the user interface
        self.gpio_pin = self.output.pin

        self.setup_output_variables(OUTPUT_INFORMATION)

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

        # Variable to store whether the output has been successfully set up
        self.logger.info("Output set up")
        self.output_setup = True

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None, output_channel=None):
        """
        Set the output on, off, to an amount, or to a duty cycle
        output_type can be None, 'sec', 'vol', or 'pwm', and determines the amount's unit
        """
        if state == 'on':
            self.logger.info("Output turned on")
            self.output_states[output_channel] = True
        elif state == 'off':
            self.logger.info("Output turned off")
            self.output_states[output_channel] = False

    def is_on(self, output_channel=None):
        """ Code to return the state of the output """
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        """Returns whether the output has successfully been set up"""
        return self.output_setup

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
