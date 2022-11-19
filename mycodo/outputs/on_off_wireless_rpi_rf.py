# coding=utf-8
#
# on_off_wireless_rpi_rf.py - Output for Wireless
#
from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'wireless_rpi_rf',
    'output_name': "{}: {} 315/433 MHz".format(lazy_gettext('On/Off'), lazy_gettext('Wireless')),
    'output_library': 'rpi-rf',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'message': 'This output uses a 315 or 433 MHz transmitter to turn wireless power outlets on or off. '
               'Run ~/Mycodo/mycodo/devices/wireless_rpi_rf.py with a receiver to discover the codes '
               'produced from your remote.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1'),
        ('pip-pypi', 'rpi_rf', 'rpi_rf==0.9.7')
    ],

    'interfaces': ['GPIO'],

    'custom_channel_options': [
        {
            'id': 'pin',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {} ({})".format(lazy_gettext('Pin'), lazy_gettext('GPIO'), lazy_gettext('BCM')),
            'phrase': lazy_gettext('The pin to control the state of')
        },
        {
            'id': 'on_command',
            'type': 'text',
            'default_value': '22559',
            'required': True,
            'name': lazy_gettext('On Command'),
            'phrase': lazy_gettext('Command to execute when the output is instructed to turn on')
        },
        {
            'id': 'off_command',
            'type': 'text',
            'default_value': '22558',
            'required': True,
            'name': lazy_gettext('Off Command'),
            'phrase': lazy_gettext('Command to execute when the output is instructed to turn off')
        },
        {
            'id': 'protocol',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, '1'),
                (2, '2'),
                (3, '3'),
                (4, '4'),
                (5, '5'),
            ],
            'name': lazy_gettext('Protocol'),
            'phrase': ''
        },
        {
            'id': 'pulse_length',
            'type': 'integer',
            'default_value': 189,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Pulse Length'),
            'phrase': ''
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': lazy_gettext('Set the state when Mycodo starts')
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': lazy_gettext('Set the state when Mycodo shuts down')
        },
        {
            'id': 'trigger_functions_startup',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Trigger Functions at Startup'),
            'phrase': lazy_gettext('Whether to trigger functions when the output switches at startup')
        },
        {
            'id': 'command_force',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Force Command'),
            'phrase': lazy_gettext('Always send the command, regardless of the current state')
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Current'), lazy_gettext('Amps')),
            'phrase': lazy_gettext('The current draw of the device being controlled')
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.wireless_pi_switch = None
        self.Transmit433MHz = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        from mycodo.devices.wireless_rpi_rf import Transmit433MHz

        self.Transmit433MHz = Transmit433MHz

        self.setup_output_variables(OUTPUT_INFORMATION)

        if self.options_channels['pin'][0] is None:
            self.logger.warning("Invalid pin for output: {}.".format(
                self.options_channels['pin'][0]))
            return

        self.wireless_pi_switch = self.Transmit433MHz(
            self.options_channels['pin'][0],
            protocol=int(self.options_channels['protocol'][0]),
            pulse_length=int(self.options_channels['pulse_length'][0]))
        self.output_setup = True

        if self.options_channels['state_startup'][0] == 1:
            self.output_switch('on')
        elif self.options_channels['state_startup'][0] == 0:
            self.output_switch('off')

        if (self.options_channels['state_startup'][0] in [0, 1] and
                self.options_channels['trigger_functions_startup'][0]):
            try:
                self.check_triggers(self.unique_id, output_channel=0)
            except Exception as err:
                self.logger.error(
                    f"Could not check Trigger for channel 0 of output {self.unique_id}: {err}")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        if state == 'on':
            self.wireless_pi_switch.transmit(int(self.options_channels['on_command'][0]))
            self.output_states[output_channel] = True
        elif state == 'off':
            self.wireless_pi_switch.transmit(int(self.options_channels['off_command'][0]))
            self.output_states[output_channel] = False

    def is_on(self, output_channel=None):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 1:
                self.output_switch('on')
            elif self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
        self.running = False
