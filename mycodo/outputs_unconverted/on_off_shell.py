# coding=utf-8
#
# command.py - Output for executing linux commands
#
from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput
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
    'output_name': "{} Shell Script".format(lazy_gettext('On/Off')),
    'output_library': 'subprocess.Popen',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'message': 'Commands will be executed in the Linux shell by the specified user when this output is '
               'turned on or off.',

    'options_enabled': [
        'command_on',
        'command_off',
        'command_execute_user',
        'command_force',
        'on_off_none_state_startup',
        'on_off_none_state_shutdown',
        'current_draw',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['SHELL']
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.state_startup = None
        self.state_shutdown = None
        self.on_command = None
        self.off_command = None
        self.linux_command_user = None

    def setup_output(self):
        self.setup_on_off_output(OUTPUT_INFORMATION)
        self.state_startup = self.output.state_startup
        self.state_shutdown = self.output.state_shutdown
        self.on_command = self.output.on_command
        self.off_command = self.output.off_command
        self.linux_command_user = self.output.linux_command_user

        if self.on_command and self.off_command:
            self.output_setup = True
            if self.state_startup == '1':
                self.output_switch('on')
            elif self.state_startup == '0':
                self.output_switch('off')
        else:
            self.logger.error("Output must have both On and Off commands set")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            self.logger.error('Output not set up')
            return

        if state == 'on':
            cmd_return, cmd_error, cmd_status = cmd_output(self.on_command, user=self.linux_command_user)
            self.output_states[output_channel] = True
        elif state == 'off':
            cmd_return, cmd_error, cmd_status = cmd_output(self.off_command, user=self.linux_command_user)
            self.output_states[output_channel] = False
        else:
            return

        self.logger.debug(
            "Output on/off {state} command returned: Status: {stat}, Output: '{ret}', Error: '{err}'".format(
                state=state, stat=cmd_status, ret=cmd_return, err=cmd_error))

    def is_on(self, output_channel=None):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        if self.state_shutdown == '1':
            self.output_switch('on')
        elif self.state_shutdown == '0':
            self.output_switch('off')
        self.running = False
