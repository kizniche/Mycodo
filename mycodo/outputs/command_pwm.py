# coding=utf-8
#
# command_pwm.py - Output for executing linux commands with PWM
#
from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.system_pi import cmd_output

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'command_pwm',
    'output_name': lazy_gettext('PWM (Linux Command)'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['pwm'],

    'message': 'Information about this output.',

    'dependencies_module': []
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.pwm_state = None

        if not testing:
            self.output_pwm_command = output.pwm_command
            self.output_linux_command_user = output.linux_command_user

    def output_switch(self, state, amount=None, duty_cycle=None):
        if self.output_pwm_command:
            if state == 'on' and 100 >= duty_cycle >= 0:
                cmd = self.output_pwm_command.replace(
                    '((duty_cycle))', str(duty_cycle))
                cmd_return, _, cmd_status = cmd_output(
                    cmd, user=self.output_linux_command_user)
                self.pwm_state = abs(duty_cycle)
            elif state == 'off':
                cmd = self.output_pwm_command.replace(
                    '((duty_cycle))', str(0))
                cmd_return, _, cmd_status = cmd_output(
                    cmd, user=self.output_linux_command_user)
                self.pwm_state = None
            else:
                return
            self.logger.debug(
                "Output duty cycle {duty_cycle} command returned: "
                "{stat}: '{ret}'".format(
                    duty_cycle=duty_cycle,
                    stat=cmd_status,
                    ret=cmd_return))

    def is_on(self):
        return self.pwm_state

    def is_setup(self):
        return True

    def setup_output(self):
        pass
