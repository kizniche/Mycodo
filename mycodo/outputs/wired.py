# coding=utf-8
#
# wired.py - Output for simple GPIO switching
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
    'output_name_unique': 'wired',
    'output_name': lazy_gettext('On/Off'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['on_off'],

    'message': 'The specified GPIO pin will be set HIGH (3.3 volts) or LOW (0 volts) when turned '
               'on or off, depending on the On State option.',

    'options_enabled': [
        'gpio_pin',
        'on_off_state_on',
        'on_off_state_startup',
        'on_off_state_shutdown',
        'trigger_functions_startup',
        'current_draw',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO')
    ],

    'interfaces': ['GPIO']
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.output_setup = False

        if not testing:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.output_pin = output.pin
            self.output_on_state = output.on_state

    def output_switch(self, state, amount=None, duty_cycle=None):
        try:
            if state == 'on':
                self.GPIO.output(self.output_pin, self.output_on_state)
            elif state == 'off':
                self.GPIO.output(self.output_pin, not self.output_on_state)
        except Exception as e:
            self.logger.error(
                "State change error: {}".format(e))

    def is_on(self):
        if self.is_setup():
            try:
                return self.output_on_state == self.GPIO.input(self.output_pin)
            except Exception as e:
                self.logger.error(
                    "Status check error: {}".format(e))

    def is_setup(self):
        return self.output_setup

    def setup_output(self):
        if self.output_pin is None:
            self.logger.warning("Invalid pin for output: {}.".format(
                self.output_pin))
            return

        try:
            try:
                self.GPIO.setmode(self.GPIO.BCM)
                self.GPIO.setwarnings(True)
                self.GPIO.setup(self.output_pin, self.GPIO.OUT)
                self.GPIO.output(self.output_pin, not self.output_on_state)
                self.output_setup = True
            except Exception as e:
                self.logger.error(
                    "Setup error: {}".format(e))
            state = 'LOW' if self.output_on_state else 'HIGH'
            self.logger.info(
                "Output setup on pin {pin} and turned OFF (OFF={state})".format(
                    pin=self.output_pin, state=state))
        except Exception as except_msg:
            self.logger.exception(
                "Output was unable to be setup on pin {pin} with trigger={trigger}: {err}".format(
                    pin=self.output_pin,
                    trigger=self.output_on_state,
                    err=except_msg))
