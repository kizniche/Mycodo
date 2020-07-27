# coding=utf-8
#
# command_pwm.py - Output for executing linux commands with PWM
#
import copy

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
    'output_name': "{} Shell Script".format(lazy_gettext('PWM')),
    'output_library': 'subprocess.Popen',
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['pwm'],

    'message': 'Commands will be executed in the Linux shell by the specified user when the duty cycle '
               'is set for this output. The string "((duty_cycle))" in the command will be replaced with '
               'the duty cycle being set prior to execution.',

    'options_enabled': [
        'command_pwm',
        'command_execute_user',
        'pwm_state_startup',
        'pwm_state_shutdown',
        'trigger_functions_startup',
        'button_send_duty_cycle'
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
        self.pwm_state = None
        self.pwm_command = None
        self.linux_command_user = None
        self.pwm_invert_signal = None

        if not testing:
            self.initialize_output()

    def initialize_output(self):
        self.pwm_command = self.output.pwm_command
        self.linux_command_user = self.output.linux_command_user
        self.pwm_invert_signal = self.output.pwm_invert_signal

    def output_switch(self, state, output_type=None, amount=None):
        measure_dict = copy.deepcopy(measurements_dict)

        if self.pwm_command:
            if state == 'on' and 0 <= amount <= 100:
                if self.pwm_invert_signal:
                    amount = 100.0 - abs(amount)
            elif state == 'off':
                if self.pwm_invert_signal:
                    amount = 100
                else:
                    amount = 0
            else:
                return

            self.pwm_state = amount

            cmd = self.pwm_command.replace('((duty_cycle))', str(amount))
            cmd_return, cmd_error, cmd_status = cmd_output(cmd, user=self.linux_command_user)

            measure_dict[0]['value'] = self.pwm_state
            add_measurements_influxdb(self.unique_id, measure_dict)

            self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))
            self.logger.debug(
                "Output duty cycle {duty_cycle} command returned: "
                "Status: {stat}, "
                "Output: '{ret}', "
                "Error: '{err}'".format(
                    duty_cycle=amount,
                    stat=cmd_status,
                    ret=cmd_return,
                    err=cmd_error))

    def is_on(self):
        if self.is_setup():
            if self.pwm_state:
                return self.pwm_state
            return False

    def is_setup(self):
        if self.output_setup:
            return True

    def setup_output(self):
        if self.pwm_command:
            self.output_setup = True
        else:
            self.output_setup = False
            self.logger.error("Output must have command set")
