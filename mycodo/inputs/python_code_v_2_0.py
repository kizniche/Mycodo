# coding=utf-8
import copy
import importlib.util
import os
import textwrap

from flask import current_app
from flask import flash
from markupsafe import Markup

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp


def generate_code(input_id, python_code):
    error = []
    pre_statement_run = """import os
import sys
sys.path.append(os.path.abspath('/opt/Mycodo'))
from mycodo.mycodo_client import DaemonControl
control = DaemonControl()

class PythonInputRun:
    def __init__(self, logger, input_id, measurement_info, channels_conversion, channels_measurement):
        self.logger = logger
        self.input_id = input_id
        self.measurement_info = measurement_info
        self.channels_conversion = channels_conversion
        self.channels_measurement = channels_measurement

    def python_code_run(self):
"""

    indented_code = textwrap.indent(python_code, ' ' * 8)
    input_python_code_run = pre_statement_run + indented_code

    assure_path_exists(PATH_PYTHON_CODE_USER)
    file_run = '{}/input_python_code_{}.py'.format(
        PATH_PYTHON_CODE_USER, input_id)
    with open(file_run, 'w') as fw:
        fw.write('{}\n'.format(input_python_code_run))
        fw.close()
    set_user_grp(file_run, 'mycodo', 'mycodo')

    for each_error in error:
        flash(each_error, 'error')

    return input_python_code_run, file_run


def execute_at_creation(error, new_input, dict_inputs=None, python_code=None):
    code = None

    # Get python code
    if dict_inputs:
        for option in dict_inputs['custom_options']:
            if option['id'] == 'python_code':
                code = option['default_value']
                break
    elif python_code:
        code = python_code

    generate_code(new_input.unique_id, code)
    return error, new_input

def execute_at_modification(
        messages,
        mod_input,
        request_form,
        custom_options_dict_presave,
        custom_options_channels_dict_presave,
        custom_options_dict_postsave,
        custom_options_channels_dict_postsave):
    """
    Function to run when the Input is saved to evaluate the Python 3 code using pylint
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
                mod_input,
                custom_options_dict_postsave,
                custom_options_channels_dict_postsave)

    try:
        input_python_code_run, file_run = generate_code(
            mod_input.unique_id, custom_options_dict_postsave['python_code'])

        if not custom_options_dict_postsave['use_pylint']:
            messages["info"].append("Review your code for issues and test your Input "
                "before putting it into a production environment.")
            return (messages,
                    mod_input,
                    custom_options_dict_postsave,
                    custom_options_channels_dict_postsave)

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
            'Full Python Code Input code:\n\n{code}\n\n'
            'Python Code Input code analysis:\n\n{report}'
            '</pre>'.format(
                code=lines_code, report=cmd_out.decode("utf-8")))
    except Exception as err:
        cmd_status = None
        cmd_error = None
        messages["error"].append("Error running pylint: {}".format(err))

    if cmd_status:
        messages["warning"].append("pylint returned with status: {}. Note that warnings are not errors. This only indicates that the pylint analysis did not return a perfect score of 10.".format(cmd_status))

    if pylint_message:
        messages["info"].append("Review your code for issues and test your Input "
              "before putting it into a production environment.")
        messages["return_text"].append(pylint_message)

    return (messages,
            mod_input,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave)


# Measurements
measurements_dict = {}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'PythonCode_v_2_0',
    'input_manufacturer': 'Linux',
    'input_name': 'Python 3 Code (v2.0)',
    'measurements_name': 'Store Value(s)',
    'measurements_dict': measurements_dict,
    'measurements_variable_amount': True,
    'channel_quantity_same_as_measurements': False,
    'execute_at_creation': execute_at_creation,
    'execute_at_modification': execute_at_modification,

    'message': 'This is an alternate Python 3 Code Input that uses a different method for storing values to the '
               'database. This was created because the Python 3 Code v1.0 Input does not allow the use of Input '
               'Actions. This method does allow the use of Input Actions. (11/21/2023 Update: The Python 3 Code '
               '(v1.0) Input now allows the execution of Actions). '
               'All channels require a Measurement Unit to be selected and saved in order to store values to the '
               'database. Your code is executed from the same Python virtual environment that Mycodo runs from. '
               'Therefore, you must install Python libraries to this environment if you want them to be available to '
               'your code. This virtualenv is located at /opt/Mycodo/env and if you wanted to install a library, for '
               'example "my_library" using pip, you would execute "sudo /opt/Mycodo/env/bin/pip install my_library".',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylint', 'pylint==3.0.1')
    ],

    'interfaces': ['Mycodo'],

    'custom_options': [
        {
            'id': 'python_code',
            'type': 'multiline_text',
            'lines': 7,
            'default_value': """import random  # Import any external libraries

# Get measurements/values (for example, these are randomly-generated numbers)
random_value = random.uniform(10.0, 100.0)

# Store measurements in database (must return a dictionary of channels and values)
return {0: random_value}""",
            'required': True,
            'col_width': 12,
            'name': 'Python 3 Code',
            'phrase': 'The code to execute. Must return a value.'
        },
        {
            'id': 'use_pylint',
            'type': 'bool',
            'default_value': True,
            'name': 'Analyze Python Code with Pylint',
            'phrase': 'Analyze your Python code with pylint when saving'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that returns a value from a command."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.input_dev = input_dev
        self.python_code = None

        self.use_pylint = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        self.unique_id = self.input_dev.unique_id

        self.measure_info = {}
        self.device_measurements = db_retrieve_table_daemon(
            DeviceMeasurements).filter(
            DeviceMeasurements.device_id == self.input_dev.unique_id)
        for each_measure in self.device_measurements.all():
            self.measure_info[each_measure.channel] = {}
            self.measure_info[each_measure.channel]['unit'] = each_measure.unit
            self.measure_info[each_measure.channel]['measurement'] = each_measure.measurement

    def get_measurement(self):
        """Determine if the return value of the command is a number."""
        if not self.python_code:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(self.measure_info)

        file_run = '{}/input_python_code_{}.py'.format(PATH_PYTHON_CODE_USER, self.unique_id)

        # If the file to execute doesn't exist, generate it
        if not os.path.exists(file_run):
            dict_inputs = parse_input_information()
            execute_at_creation([], self.input_dev, dict_inputs)

        with open(file_run, 'r') as file:
            self.logger.debug("Python Code:\n{}".format(file.read()))

        module_name = "mycodo.input.python_code_exec_{}".format(os.path.basename(file_run).split('.')[0])
        spec = importlib.util.spec_from_file_location(module_name, file_run)
        python_code_run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(python_code_run)
        run = python_code_run.PythonInputRun(self.logger, self.unique_id, self.measure_info, self.channels_conversion, self.channels_measurement)

        try:
            return_value = run.python_code_run()
            for channel, value in return_value.items():
                self.return_dict[channel]['value'] = value
        except Exception:
            self.logger.exception(1)

        return self.return_dict
