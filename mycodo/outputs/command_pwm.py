# coding=utf-8
#
# command_pwm.py - Output for executing linux commands with PWM
#
from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb
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

    'message': 'Commands will be executed in the Linux shell by the specified user when the duty cycle '
               'is set for this output. The string "((duty_cycle))" in the command will be replaced with '
               'the duty cycle being set prior to execution.',

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
            self.output_unique_id = output.unique_id
            self.output_pwm_command = output.pwm_command
            self.output_linux_command_user = output.linux_command_user
            self.pwm_invert_signal = output.pwm_invert_signal

    def output_switch(self, state, amount=None, duty_cycle=None):
        measure_dict = measurements_dict.copy()

        if self.output_pwm_command:
            if state == 'on' and 0 <= duty_cycle <= 100:
                if self.pwm_invert_signal:
                    duty_cycle = 100.0 - abs(duty_cycle)
            elif state == 'off':
                if self.pwm_invert_signal:
                    duty_cycle = 100
                else:
                    duty_cycle = 0
            else:
                return

            self.pwm_state = duty_cycle

            cmd = self.output_pwm_command.replace(
                '((duty_cycle))', str(duty_cycle))
            cmd_return, _, cmd_status = cmd_output(
                cmd, user=self.output_linux_command_user)

            measure_dict[0]['value'] = self.pwm_state
            add_measurements_influxdb(self.output_unique_id, measure_dict)

            self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=duty_cycle))
            self.logger.debug(
                "Output duty cycle {duty_cycle} command returned: "
                "{stat}: '{ret}'".format(
                    duty_cycle=duty_cycle,
                    stat=cmd_status,
                    ret=cmd_return))

    def is_on(self):
        if self.pwm_state:
            return self.pwm_state
        return False

    def is_setup(self):
        return True

    def setup_output(self):
        pass
