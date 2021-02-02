# coding=utf-8
#
# on_off_python.py - Output for executing python code
#
import importlib.util
import os
import textwrap

from flask_babel import lazy_gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import set_user_grp

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
    'output_name_unique': 'python',
    'output_name': "Python Code: {}".format(lazy_gettext('On/Off')),
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'message': 'Python 3 code will be executed when this output is turned on or off.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['PYTHON'],

    'custom_channel_options': [
        {
            'id': 'on_command',
            'type': 'multiline_text',
            'lines': 7,
            'default_value': """
import datetime
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_string = "{ts}: ID: {id}: ON".format(id=output_id, ts=timestamp)
self.logger.info(log_string)""",
            'required': True,
            'col_width': 12,
            'name': lazy_gettext('On Command'),
            'phrase': lazy_gettext('Python code to execute when the output is instructed to turn on')
        },
        {
            'id': 'off_command',
            'type': 'multiline_text',
            'lines': 7,
            'default_value': """
import datetime
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_string = "{ts}: ID: {id}: OFF".format(id=output_id, ts=timestamp)
self.logger.info(log_string)""",
            'required': True,
            'col_width': 12,
            'name': lazy_gettext('Off Command'),
            'phrase': lazy_gettext('Python code to execute when the output is instructed to turn off')
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
            'phrase': lazy_gettext('Always send the command if instructed, regardless of the current state')
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Current (Amps)'),
            'phrase': lazy_gettext('The current draw of the device being controlled')
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.run_python_on = None
        self.run_python_off = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if not self.options_channels['on_command'][0] or not self.options_channels['off_command'][0]:
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

            if self.options_channels['state_startup'][0] == 1:
                self.output_switch('on')
            elif self.options_channels['state_startup'][0] == 0:
                self.output_switch('off')
        except Exception:
            self.logger.exception("Could not set up output")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if state == 'on' and self.options_channels['on_command'][0]:
            self.run_python_on.output_code_run()
            self.output_states[output_channel] = True
        elif state == 'off' and self.options_channels['off_command'][0]:
            self.run_python_off.output_code_run()
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
        """ Called when Output is stopped """
        if self.options_channels['state_shutdown'][0] == 1:
            self.output_switch('on')
        elif self.options_channels['state_shutdown'][0] == 0:
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

        code_on_indented = textwrap.indent(self.options_channels['on_command'][0], ' ' * 8)
        full_command_on = pre_statement_run + code_on_indented

        code_off_indented = textwrap.indent(self.options_channels['off_command'][0], ' ' * 8)
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
