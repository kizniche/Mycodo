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

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'command',
    'output_name': lazy_gettext('On/Off'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
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
        'trigger_functions_startup',
        'current_draw',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [],

    'interfaces': ['SHELL']
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.output_setup = None
        self.output_state = None

        if not testing:
            self.output_on_command = output.on_command
            self.output_off_command = output.off_command
            self.output_linux_command_user = output.linux_command_user

    def output_switch(self, state, amount=None, duty_cycle=None):
        if state == 'on':
            cmd_return, cmd_error, cmd_status = cmd_output(
                self.output_on_command, user=self.output_linux_command_user)
            self.output_state = True
        elif state == 'off':
            cmd_return, cmd_error, cmd_status = cmd_output(
                self.output_off_command, user=self.output_linux_command_user)
            self.output_state = False
        else:
            return

        self.logger.debug(
            "Output on/off {state} command returned: "
            "Status: {stat}, "
            "Output: '{ret}', "
            "Error: '{err}'".format(
                state=state,
                stat=cmd_status,
                ret=cmd_return,
                err=cmd_error))

    def is_on(self):
        if self.is_setup():
            return self.output_state

    def is_setup(self):
        if self.output_setup:
            return True

    def setup_output(self):
        if self.output_on_command and self.output_off_command:
            self.output_setup = True
            self.output_state = False
        else:
            self.output_setup = False
            self.logger.error("Output must have both On and Off commands set")
