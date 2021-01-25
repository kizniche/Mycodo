# coding=utf-8
#
# dc_motor_l298n.py - Output for L298N DC motor controller
#
from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon


def constraints_pass_positive_or_zero_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value < 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


def constraints_pass_percent(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if 100 < value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    1: {
        'measurement': 'duration_time',
        'unit': 's',
    },
}

channels_dict = {
    0: {
        'name': 'Channel 1',
        'types': ['on_off'],
        'measurements': [0]
    },
    1: {
        'name': 'Channel 2',
        'types': ['on_off'],
        'measurements': [1]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'DC_MOTOR_L298N',
    'output_name': "DC Motor: L298N",
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_additional': 'https://www.electronicshub.org/raspberry-pi-l298n-interface-tutorial-control-dc-motor-l298n-raspberry-pi/',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO')
    ],

    'interfaces': ['GPIO'],

    'custom_channel_options': [
        {
            'id': 'pin_1',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Input Pin 1',
            'phrase': 'The Input Pin 1 of the controller (BCM numbering)'
        },
        {
            'id': 'pin_2',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Input Pin 2',
            'phrase': 'The Input Pin 2 of the controller (BCM numbering)'
        },
        {
            'id': 'pin_enable',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Enable Pin',
            'phrase': 'The Enable pin of the controller (BCM numbering)'
        },
        {
            'id': 'duty_cycle',
            'type': 'integer',
            'default_value': 50,
            'constraints_pass': constraints_pass_percent,
            'name': 'Duty Cycle',
            'phrase': 'The duty cycle of the motor (percent, 1 - 100)'
        },
        {
            'id': 'direction',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, 'Forward'),
                (0, 'Backward')
            ],
            'name': lazy_gettext('Direction'),
            'phrase': 'The direction to turn the motor'
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.driver = None
        self.channel_setup = {}
        self.gpio = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        self.setup_on_off_output(OUTPUT_INFORMATION)

        import RPi.GPIO as GPIO
        self.gpio = GPIO

        for channel in channels_dict:
            if (not self.options_channels['pin_1'][channel] or
                    not self.options_channels['pin_2'][channel] or
                    not self.options_channels['pin_enable'][channel] or
                    not self.options_channels['duty_cycle'][channel]):
                self.logger.error("Cannot initialize Output channel {} until all options are set. "
                                  "Check your configuration.".format(channel))
                self.channel_setup[channel] = False
            else:
                self.gpio.setmode(self.gpio.BCM)
                self.gpio.setup(self.options_channels['pin_1'][channel], self.gpio.OUT)
                self.gpio.setup(self.options_channels['pin_2'][channel], self.gpio.OUT)
                self.gpio.setup(self.options_channels['pin_enable'][channel], self.gpio.OUT)
                self.stop(channel)
                self.driver = self.gpio.PWM(self.options_channels['pin_enable'][channel], 1000)
                self.driver.start(self.options_channels['duty_cycle'][channel])
                self.channel_setup[channel] = True

    def run(self, channel):
        if self.options_channels['direction'][channel]:
            self.gpio.output(self.options_channels['pin_1'][channel], self.gpio.HIGH)
            self.gpio.output(self.options_channels['pin_2'][channel], self.gpio.LOW)
        else:
            self.gpio.output(self.options_channels['pin_1'][channel], self.gpio.LOW)
            self.gpio.output(self.options_channels['pin_2'][channel], self.gpio.HIGH)

    def stop(self, channel):
        self.gpio.output(self.options_channels['pin_1'][channel], self.gpio.LOW)
        self.gpio.output(self.options_channels['pin_2'][channel], self.gpio.LOW)

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.channel_setup[output_channel]:
            msg = "Output channel {} not set up, cannot turn it on or off.".format(output_channel)
            self.logger.error(msg)
            return msg

        if state == 'on':
            self.run(output_channel)
            self.output_states[output_channel] = True
        elif state == 'off':
            self.stop(output_channel)
            self.output_states[output_channel] = False

    def is_on(self, output_channel=None):
        if self.is_setup(channel=output_channel):
            return self.output_states[output_channel]

    def is_setup(self, channel=None):
        if channel:
            return self.channel_setup[channel]
        return any(self.channel_setup)

    def stop_output(self):
        """ Called when Output is stopped """
        for channel in channels_dict:
            self.stop(channel)
        self.running = False
