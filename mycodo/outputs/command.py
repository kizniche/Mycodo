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
    'output_name': lazy_gettext('On/Off (Linux Command)'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': True,
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
            self.output_on_command = output.on_command
            self.output_off_command = output.off_command
            self.output_linux_command_user = output.linux_command_user

    def output_switch(self, state, amount=None, duty_cycle=None):
        if state == 'on' and self.output_on_command:
            cmd_return, _, cmd_status = cmd_output(
                self.output_on_command,
                user=self.output_linux_command_user)
        elif state == 'off' and self.output_off_command:
            cmd_return, _, cmd_status = cmd_output(
                self.output_off_command,
                user=self.output_linux_command_user)
        else:
            return
        self.logger.debug(
            "Output {state} command returned: "
            "{stat}: '{ret}'".format(
                state=state,
                stat=cmd_status,
                ret=cmd_return))

    def is_on(self):
        pass

    def _is_setup(self):
        return True

    def setup_output(self):
        pass
