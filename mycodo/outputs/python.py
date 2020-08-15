# coding=utf-8
#
# python.py - Output for executing python code
#
import importlib.util
import textwrap

import os
from flask_babel import lazy_gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import set_user_grp

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

outputs_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'python',
    'output_name': "{} Python Code".format(lazy_gettext('On/Off')),
    'measurements_dict': measurements_dict,
    'outputs_dict': outputs_dict,
    'output_types': ['on_off'],

    'message': 'Python 3 code will be executed when this output is turned on or off.',

    'options_enabled': [
        'python_on',
        'python_off',
        'command_force',
        'on_off_none_state_startup',
        'on_off_none_state_shutdown',
        'current_draw',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['PYTHON']
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
        self.run_python_on = None
        self.run_python_off = None

    def setup_output(self):
        self.setup_on_off_output(OUTPUT_INFORMATION)
        self.state_startup = self.output.state_startup
        self.state_shutdown = self.output.state_shutdown
        self.on_command = self.output.on_command
        self.off_command = self.output.off_command

        if not self.on_command or not self.off_command:
            self.logger.error("Output must have both On and Off Python Code set")
            return

        try:
            self.save_output_python_code(self.unique_id)
            file_run_on = '{}/output_on_{}.py'.format(PATH_PYTHON_CODE_USER, self.unique_id)
            file_run_off = '{}/output_off_{}.py'.format(PATH_PYTHON_CODE_USER, self.unique_id)

            module_name = "mycodo.output.{}".format(os.path.basename(file_run_on).split('.')[0])
            spec = importlib.util.spec_from_file_location(module_name, file_run_on)
            output_run_on = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(output_run_on)
            self.run_python_on = output_run_on.OutputRun(self.logger, self.unique_id)

            module_name = "mycodo.output.{}".format(os.path.basename(file_run_off).split('.')[0])
            spec = importlib.util.spec_from_file_location(module_name, file_run_off)
            output_run_off = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(output_run_off)
            self.run_python_off = output_run_off.OutputRun(self.logger, self.unique_id)

            self.output_setup = True

            if self.state_startup == '1':
                self.output_switch('on')
            elif self.state_startup == '0':
                self.output_switch('off')
        except Exception:
            self.logger.exception("Could not set up output")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if state == 'on' and self.on_command:
            self.run_python_on.output_code_run()
            self.output_states[output_channel] = True
        elif state == 'off' and self.off_command:
            self.run_python_off.output_code_run()
            self.output_states[output_channel] = False
        else:
            return

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

    def save_output_python_code(self, unique_id):
        """Save python code to files"""
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

    def stop_output(self):
        self.running = False

    def output_code_run(self):
"""

        code_on_indented = textwrap.indent(self.on_command, ' ' * 8)
        full_command_on = pre_statement_run + code_on_indented

        code_off_indented = textwrap.indent(self.off_command, ' ' * 8)
        full_command_off = pre_statement_run + code_off_indented

        assure_path_exists(PATH_PYTHON_CODE_USER)
        file_run = '{}/output_on_{}.py'.format(PATH_PYTHON_CODE_USER, unique_id)
        with open(file_run, 'w') as fw:
            fw.write('{}\n'.format(full_command_on))
            fw.close()
        set_user_grp(file_run, 'mycodo', 'mycodo')

        file_run = '{}/output_off_{}.py'.format(PATH_PYTHON_CODE_USER, unique_id)
        with open(file_run, 'w') as fw:
            fw.write('{}\n'.format(full_command_off))
            fw.close()
        set_user_grp(file_run, 'mycodo', 'mycodo')
