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
    'output_name_unique': 'example_output_dummy',
    'output_name': lazy_gettext('Example Dummy Output'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['on_off', 'duration'],

    'message': 'Information about this output.',

    'dependencies_module': []
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        if not testing:
            self.output_setup = None
            self.output_state = False
            self.logger.info("Output class initialized")

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
        if self.output_state:
            return self.output_state
        return False

    def _is_setup(self):
        """Returns whether the output has successfully been set up"""
        if self.output_setup:
            return True
        return False

    def setup_output(self):
        """Code executed when Mycodo starts up to initialize the output"""
        self.logger.info("Output set up")
        self.output_setup = True
