# coding=utf-8
#
# example_dummy_output.py - Example Output module
#
from flask_babel import lazy_gettext
from mycodo.outputs.base_output import AbstractOutput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'example_output_dummy',  # a unique output name used to distinguish it from others
    'output_name': lazy_gettext('Example Dummy Output'),  # A friendly/common name for the output
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
        'gpio_pin',
        'current_draw'
    ],
    'options_disabled': ['interface'],

    # Any dependencies required by the output module
    'dependencies_module': [],

    # THe interface or interfaces that can be used with this module
    'interfaces': ['GPIO'],

    # Custom actions that will appear at the top of the options in the user interface
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
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        if not testing:
            # Variable to store whether the output has been successfully set up
            self.output_setup = None

            # Since on_state_internally_handled is False, we will store the state of the output
            self.output_state = False

            # Variables set by the user interface
            self.gpio_pin = output.pin

            self.logger.info(
                "Output class initialized with GPIO pin {}".format(
                    self.gpio_pin))

    def output_switch(self, state, amount=None, duty_cycle=None):
        """Turn the output on, off, on for an amount, or set a duty cycle"""
        if state == 'on':
            self.logger.info("Output turned on")
            self.output_state = True
        elif state == 'off':
            self.logger.info("Output turned off")
            self.output_state = False

    def is_on(self):
        """
        Code to return the state of the output.
        This can also be handled internally by the output controller
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
        """
        Executed when custom action button pressed
        """
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
