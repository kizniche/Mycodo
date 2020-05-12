# coding=utf-8
#
# python_pwm.py - Output for Python code PWM
#
import importlib.util
import textwrap

import os
from flask_babel import lazy_gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import set_user_grp

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'python_pwm',
    'output_name': lazy_gettext('PWM (Python Command)'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['pwm'],

    'message': 'Python 3 code will be executed when this output is turned on or off. The "duty_cycle" '
               'object is a float value that represents the duty cycle that has been set.',

    'dependencies_module': []
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.pwm_state = None
        self.output_run_python_pwm = None

        if not testing:
            self.output_unique_id = output.unique_id
            self.output_pwm_command = output.pwm_command
            self.pwm_invert_signal = output.pwm_invert_signal

    def output_switch(self, state, amount=None, duty_cycle=None):
        measure_dict = measurements_dict.copy()

        if self.output_pwm_command:
            if state == 'on' and 100 >= duty_cycle >= 0:
                if self.pwm_invert_signal:
                    duty_cycle = 100.0 - abs(duty_cycle)
            elif state == 'off' or duty_cycle == 0:
                if self.pwm_invert_signal:
                    duty_cycle = 100
                else:
                    duty_cycle = 0
            else:
                return

            self.output_run_python_pwm.output_code_run(duty_cycle)
            self.pwm_state = duty_cycle

            measure_dict[0]['value'] = duty_cycle
            add_measurements_influxdb(self.output_unique_id, measure_dict)

            self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=duty_cycle))

    def is_on(self):
        if self.pwm_state:
            return self.pwm_state
        return False

    def is_setup(self):
        if self.output_run_python_pwm:
            return True
        return False

    def setup_output(self):
        self.save_output_python_pwm_code(self.output_unique_id)
        file_run_pwm = '{}/output_pwm_{}.py'.format(
            PATH_PYTHON_CODE_USER, self.output_unique_id)

        module_name = "mycodo.output.{}".format(
            os.path.basename(file_run_pwm).split('.')[0])
        spec = importlib.util.spec_from_file_location(
            module_name, file_run_pwm)
        output_run_pwm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(output_run_pwm)
        self.output_run_python_pwm = output_run_pwm.OutputRun(
            self.logger, self.output_unique_id)

    def save_output_python_pwm_code(self, unique_id):
        """Save python PWM code to files"""
        pre_statement_run = f"""import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.mycodo_client import DaemonControl
control = DaemonControl()
output_id = '{unique_id}'

class OutputRun:
    def __init__(self, logger, output_id):
        self.logger = logger
        self.output_id = output_id
        self.variables = {{}}
        self.running = True
        self.duty_cycle = None

    def stop_output(self):
        self.running = False

    def output_code_run(self, duty_cycle):
"""

        code_replaced = self.output_pwm_command.replace('((duty_cycle))', 'duty_cycle')
        indented_code = textwrap.indent(code_replaced, ' ' * 8)
        full_command_pwm = pre_statement_run + indented_code

        assure_path_exists(PATH_PYTHON_CODE_USER)
        file_run = '{}/output_pwm_{}.py'.format(
            PATH_PYTHON_CODE_USER, unique_id)
        with open(file_run, 'w') as fw:
            fw.write('{}\n'.format(full_command_pwm))
            fw.close()
        set_user_grp(file_run, 'mycodo', 'mycodo')
