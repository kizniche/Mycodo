# coding=utf-8
#
# pwm_python.py - Output for Python code PWM
#
import copy
import importlib.util
import os
import textwrap

from flask import current_app
from flask_babel import lazy_gettext
from markupsafe import Markup
from sqlalchemy import and_

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_influxdb_single
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.system_pi import set_user_grp


def generate_code(code_pwm, unique_id):
    pre_statement_run = f"""import os
import sys
sys.path.append(os.path.abspath('/opt/Mycodo'))
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

    code_replaced = code_pwm.replace('((duty_cycle))', 'duty_cycle')
    indented_code = textwrap.indent(code_replaced, ' ' * 8)
    full_code = pre_statement_run + indented_code

    assure_path_exists(PATH_PYTHON_CODE_USER)
    file_run = '{}/output_{}.py'.format(PATH_PYTHON_CODE_USER, unique_id)
    with open(file_run, 'w') as fw:
        fw.write('{}\n'.format(full_code))
        fw.close()
    set_user_grp(file_run, 'mycodo', 'mycodo')

    return full_code, file_run


def execute_at_modification(
        messages,
        mod_output,
        request_form,
        custom_options_dict_presave,
        custom_options_channels_dict_presave,
        custom_options_dict_postsave,
        custom_options_channels_dict_postsave):
    """
    Function to run when the Output is saved to evaluate the Python 3 code using pylint
    :param messages: dict of info, warning, error, success messages as well as other variables
    :param mod_input: The WTForms object containing the form data submitted by the web GUI
    :param request_form: The custom_options form input data (if it exists)
    :param custom_options_dict_presave:
    :param custom_options_channels_dict_presave:
    :param custom_options_dict_postsave:
    :param custom_options_channels_dict_postsave:
    :return: tuple of (all_passed, error, mod_input) variables
    """
    messages["page_refresh"] = True
    pylint_message = None

    if current_app.config['TESTING']:
        return (messages,
                mod_output,
                custom_options_dict_postsave,
                custom_options_channels_dict_postsave)

    try:
        if not custom_options_dict_postsave['use_pylint']:
            messages["info"].append("Review your code for issues and test your Input "
                "before putting it into a production environment.")
            return (messages,
                    mod_output,
                    custom_options_dict_postsave,
                    custom_options_channels_dict_postsave)

        input_python_code_run, file_run = generate_code(
            custom_options_channels_dict_postsave[0]['pwm_command'],
            mod_output.unique_id)

        lines_code = ''
        for line_num, each_line in enumerate(input_python_code_run.splitlines(), 1):
            if len(str(line_num)) == 3:
                line_spacing = ''
            elif len(str(line_num)) == 2:
                line_spacing = ' '
            else:
                line_spacing = '  '
            lines_code += '{sp}{ln}: {line}\n'.format(
                sp=line_spacing,
                ln=line_num,
                line=each_line)

        cmd_test = 'mkdir -p /opt/Mycodo/.pylint.d && ' \
                   'export PYTHONPATH=$PYTHONPATH:/opt/Mycodo && ' \
                   'export PYLINTHOME=/opt/Mycodo/.pylint.d && ' \
                   '{dir}/env/bin/python -m pylint -d I,W0621,C0103,C0111,C0301,C0327,C0410,C0413 {path}'.format(
                       dir=INSTALL_DIRECTORY, path=file_run)
        cmd_out, cmd_error, cmd_status = cmd_output(cmd_test, user='root')
        pylint_message = Markup(
            '<pre>\n\n'
            'Full Python code:\n\n{code}\n\n'
            'Python code analysis:\n\n{report}'
            '</pre>'.format(
                code=lines_code, report=cmd_out.decode("utf-8")))
    except Exception as err:
        cmd_status = None
        messages["error"].append("Error running pylint: {}".format(err))

    if cmd_status:
        messages["warning"].append("pylint returned with status: {}. Note that warnings are not errors. This only indicates that the pylint analysis did not return a perfect score of 10.".format(cmd_status))

    if pylint_message:
        messages["info"].append("Review your code for issues and test your Input "
              "before putting it into a production environment.")
        messages["return_text"].append(pylint_message)

    return (messages,
            mod_output,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave)


# Measurements
measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

channels_dict = {
    0: {
        'types': ['pwm'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'python_pwm',
    'output_name': "{}: Python 3 Code".format(lazy_gettext('PWM')),
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'execute_at_modification': execute_at_modification,
    'output_types': ['pwm'],

    'message': 'Python 3 code will be executed when this output is turned on or off. The "duty_cycle" '
               'object is a float value that represents the duty cycle that has been set.',

    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylint', 'pylint==3.0.1')
    ],

    'interfaces': ['PYTHON'],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """Set the Duty Cycle."""
        },
        {
            'id': 'duty_cycle',
            'type': 'float',
            'default_value': 0,
            'name': 'Duty Cycle',
            'phrase': 'The duty cycle to set'
        },
        {
            'id': 'set_duty_cycle',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Set Duty Cycle'
        }
    ],

    'custom_options': [
        {
            'id': 'use_pylint',
            'type': 'bool',
            'default_value': True,
            'name': 'Analyze Python Code with Pylint',
            'phrase': 'Analyze your Python code with pylint when saving'
        }
    ],

    'custom_channel_options': [
        {
            'id': 'pwm_command',
            'type': 'multiline_text',
            'lines': 7,
            'default_value': """
log_string = "ID: {id}: {dc} % Duty Cycle".format(
    dc=duty_cycle, id=output_id)
self.logger.info(log_string)""",
            'required': True,
            'col_width': 12,
            'name': 'Python 3 Code',
            'phrase': 'Python code to execute to set the PWM duty cycle (%)'
        },
        {
            'id': 'linux_command_user',
            'type': 'text',
            'default_value': 'mycodo',
            'name': lazy_gettext('User'),
            'phrase': lazy_gettext('The user to execute the command')
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': '',
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value'),
                ('last_duty_cycle', 'Last Known Value')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state when Mycodo starts'
        },
        {
            'id': 'startup_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Startup Value'),
            'phrase': 'The value when Mycodo starts'
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': '',
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': 'Set the state when Mycodo shuts down'
        },
        {
            'id': 'shutdown_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Shutdown Value'),
            'phrase': 'The value when Mycodo shuts down'
        },
        {
            'id': 'pwm_invert_signal',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Signal'),
            'phrase': 'Invert the PWM signal'
        },
        {
            'id': 'pwm_invert_stored_signal',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Stored Signal'),
            'phrase': 'Invert the value that is saved to the measurement database'
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
            'name': "{} ({})".format(lazy_gettext('Current'), lazy_gettext('Amps')),
            'phrase': 'The current draw of the device being controlled'
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.output_run_python_pwm = None

        self.use_pylint = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if not self.options_channels['pwm_command'][0]:
            self.logger.error("Output must have Python Code set")
            return

        try:
            full_command, file_run = generate_code(
                self.options_channels['pwm_command'][0],self.unique_id)

            module_name = "mycodo.output.{}".format(os.path.basename(file_run).split('.')[0])
            spec = importlib.util.spec_from_file_location(module_name, file_run)
            output_run_pwm = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(output_run_pwm)
            self.output_run_python_pwm = output_run_pwm.OutputRun(self.logger, self.unique_id)

            self.output_setup = True

            if self.options_channels['state_startup'][0] == 0:
                self.output_switch('off')
            elif self.options_channels['state_startup'][0] == 'set_duty_cycle':
                self.output_switch('on', amount=self.options_channels['startup_value'][0])
            elif self.options_channels['state_startup'][0] == 'last_duty_cycle':
                device_measurement = db_retrieve_table_daemon(DeviceMeasurements).filter(
                    and_(DeviceMeasurements.device_id == self.unique_id,
                         DeviceMeasurements.channel == 0)).first()

                last_measurement = None
                if device_measurement:
                    channel, unit, measurement = return_measurement_info(device_measurement, None)
                    last_measurement = read_influxdb_single(
                        self.unique_id,
                        unit,
                        channel,
                        measure=measurement,
                        value='LAST')

                if last_measurement:
                    self.logger.info(
                        "Setting startup duty cycle to last known value of {dc} %".format(
                            dc=last_measurement[1]))
                    self.output_switch('on', amount=last_measurement[1])
                else:
                    self.logger.error(
                        "Output instructed at startup to be set to "
                        "the last known duty cycle, but a last known "
                        "duty cycle could not be found in the measurement "
                        "database")
        except Exception:
            self.logger.exception("Could not set up output")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        measure_dict = copy.deepcopy(measurements_dict)

        if self.options_channels['pwm_command'][0]:
            if state == 'on' and 100 >= amount >= 0:
                if self.options_channels['pwm_invert_signal'][0]:
                    amount = 100.0 - abs(amount)
            elif state == 'off' or amount == 0:
                if self.options_channels['pwm_invert_signal'][0]:
                    amount = 100
                else:
                    amount = 0
            else:
                return

            self.output_run_python_pwm.output_code_run(amount)
            self.output_states[0] = amount

            self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))

            if self.options_channels['pwm_invert_stored_signal'][0]:
                amount = 100.0 - abs(amount)

            measure_dict[0]['value'] = float(amount)
            add_measurements_influxdb(self.unique_id, measure_dict)

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.output_states[0]:
                return self.output_states[0]
            return False

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
            elif self.options_channels['state_shutdown'][0] == 'set_duty_cycle':
                self.output_switch('on', amount=self.options_channels['shutdown_value'][0])
        self.running = False

    def set_duty_cycle(self, args_dict):
        if 'duty_cycle' not in args_dict:
            self.logger.error("Cannot set without duty cycle")
            return
        test = self.control.output_on(
            self.output.unique_id,
            output_type='pwm',
            amount=args_dict["duty_cycle"],
            output_channel=0)
        return "Setting duty cycle: {}".format(test)
