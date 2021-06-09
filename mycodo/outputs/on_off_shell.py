# coding=utf-8
#
# on_off_shell.py - Output for executing shell commands
#
from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import cmd_output

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
    'output_name_unique': 'command',
    'output_name': "Shell Script: {}".format(lazy_gettext('On/Off')),
    'output_library': 'subprocess.Popen',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'message': 'Commands will be executed in the Linux shell by the specified user when this output is '
               'turned on or off.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['SHELL'],

    'custom_channel_options': [
        {
            'id': 'on_command',
            'type': 'text',
            'default_value': '/home/pi/script_on_off.sh on',
            'required': True,
            'col_width': 12,
            'name': lazy_gettext('On Command'),
            'phrase': 'Command to execute when the output is instructed to turn on'
        },
        {
            'id': 'off_command',
            'type': 'text',
            'default_value': '/home/pi/script_on_off.sh off',
            'required': True,
            'col_width': 12,
            'name': lazy_gettext('Off Command'),
            'phrase': 'Command to execute when the output is instructed to turn off'
        },
        {
            'id': 'linux_command_user',
            'type': 'text',
            'default_value': 'mycodo',
            'name': lazy_gettext('User'),
            'phrase': 'The user to execute the command'
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
            'phrase': 'Set the state when Mycodo starts'
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
            'phrase': 'Set the state when Mycodo shuts down'
        },
        {
            'id': 'trigger_functions_startup',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Trigger Functions at Startup'),
            'phrase': 'Whether to trigger functions when the output switches at startup'
        },
        {
            'id': 'command_force',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Force Command'),
            'phrase': 'Always send the command if instructed, regardless of the current state'
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Current (Amps)'),
            'phrase': 'The current draw of the device being controlled'
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if self.options_channels['on_command'][0] and self.options_channels['off_command'][0]:
            self.output_setup = True
            if self.options_channels['state_startup'][0] == 1:
                self.output_switch('on')
            elif self.options_channels['state_startup'][0] == 0:
                self.output_switch('off')
        else:
            self.logger.error("Output must have both On and Off commands set")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            self.logger.error('Output not set up')
            return

        if state == 'on':
            cmd_return, cmd_error, cmd_status = cmd_output(
                self.options_channels['on_command'][0],
                user=self.options_channels['linux_command_user'][0])
            self.output_states[0] = True
        elif state == 'off':
            cmd_return, cmd_error, cmd_status = cmd_output(
                self.options_channels['off_command'][0],
                user=self.options_channels['linux_command_user'][0])
            self.output_states[0] = False
        else:
            return

        self.logger.debug(
            "Output on/off {state} command returned: Status: {stat}, Output: '{ret}', Error: '{err}'".format(
                state=state, stat=cmd_status, ret=cmd_return, err=cmd_error))

    def is_on(self, output_channel=None):
        if self.is_setup():
            return self.output_states[0]

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 1:
                self.output_switch('on')
            elif self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
        self.running = False
