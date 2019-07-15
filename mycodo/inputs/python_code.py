# coding=utf-8
import sys
import traceback
import uuid

import os
from flask import Markup
from flask import flash
from io import StringIO

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import cmd_output


def format_pre_statement(unique_id, measure_info):
    """ Generate the code to place/execute before the user code """
    pre_statement = """import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))

from mycodo.mycodo_client import DaemonControl
from mycodo.utils.influx import add_measurements_influxdb

control = DaemonControl()

measurement_info = {measure_info}

def store_measurement(channel=None, measurement=None):
    if None in [channel, measurement]:
        return
    measure = {{channel: {{}}}}
    measure[channel]['measurement'] = measurement_info[channel]['measurement']
    measure[channel]['unit'] = measurement_info[channel]['unit']
    measure[channel]['value'] = measurement
    add_measurements_influxdb('{unique_id}', measure)

""".format(unique_id=unique_id, measure_info=measure_info)
    return pre_statement


def test_before_saving(mod_input, request_form):
    """
    Function to run when the Input is saved to evaluate the Python 3 code using pylint3
    :param mod_input: The WTForms object containing the form data submitted by the web GUI
    :param request_form: The custom_options form input data (if it exists)
    :return: tuple of (all_passed, error, mod_input) variables
    """
    all_passed = True

    # Only add strings to this list to prevent options from being saved.
    # Use flash('my error message', 'error') to show errors but allow options
    # to save.
    error = []

    measure_info = {}
    device_measurements = db_retrieve_table_daemon(
        DeviceMeasurements).filter(
        DeviceMeasurements.device_id == mod_input.unique_id)
    for each_measure in device_measurements.all():
        measure_info[each_measure.channel] = {}
        measure_info[each_measure.channel]['unit'] = each_measure.unit
        measure_info[each_measure.channel]['measurement'] = each_measure.measurement

    pre_statement = format_pre_statement(mod_input.unique_id, measure_info)
    code_combined = pre_statement + mod_input.cmd_command

    if len(code_combined.splitlines()) > 999:
        error.append("Too many lines in code. Reduce code to less than 1000 lines.")

    lines_code = ''
    for line_num, each_line in enumerate(code_combined.splitlines(), 1):
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

    path_file = '/tmp/input_code_{}.py'.format(
        str(uuid.uuid4()).split('-')[0])
    with open(path_file, 'w') as out:
        out.write('{}\n'.format(code_combined))

    cmd_test = 'export PYTHONPATH=$PYTHONPATH:/var/mycodo-root && ' \
               'pylint3 -d I,W0621,C0103,C0111,C0301,C0327,C0410,C0411,C0413 {path}'.format(
        path=path_file)
    cmd_out, cmd_err, cmd_status = cmd_output(cmd_test)

    os.remove(path_file)

    message = Markup(
        '<pre>\n\n'
        'Full Python 3 code:\n\n{code}\n\n'
        'Python 3 code analysis:\n\n{report}'
        '</pre>'.format(
            code=lines_code, report=cmd_out.decode("utf-8")))
    if cmd_status:
        flash(
            'Error(s) were found while evaluating your code. Review '
            'the error(s), below, and fix them before activating your Input.')
        flash(message, 'error')
    else:
        flash(
            "No errors were found while evaluating your code. However, "
            "this doesn't mean your code will perform as expected. "
            "Review your code for issues and test your Input "
            "before putting it into a production environment. Note: You "
            "must have the specified channels added for the Input to use the "
            "store_measurement() function.", 'success')
        flash(message, 'success')

    return all_passed, error, mod_input


# Measurements
measurements_dict = {}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'PythonCode',
    'input_manufacturer': 'Linux',
    'input_name': 'Python 3 Code',
    'measurements_name': 'Store Value(s)',
    'measurements_dict': measurements_dict,
    'measurements_variable_amount': True,

    'options_enabled': [
        'measurements_select',
        'period',
        'cmd_command',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'test_before_saving': test_before_saving,

    'interfaces': ['Mycodo'],
    'cmd_command': """import random  # Import any external libraries

# Get measurements/values (for example, these are randomly-generated numbers)
random_value_channel_0 = random.uniform(10.0, 100.0)
random_value_channel_1 = random.uniform(500.0, 1000.0)

# Store measurements in database (must specify the channel and measurement)
store_measurement(channel=0, measurement=random_value_channel_0)
store_measurement(channel=1, measurement=random_value_channel_1)"""
}


class InputModule(AbstractInput):
    """ A sensor support class that returns a value from a command """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            self.python_code = input_dev.cmd_command

            self.measure_info = {}
            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == self.input_dev.unique_id)
            for each_measure in self.device_measurements.all():
                self.measure_info[each_measure.channel] = {}
                self.measure_info[each_measure.channel]['unit'] = each_measure.unit
                self.measure_info[each_measure.channel]['measurement'] = each_measure.measurement

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self.return_dict = measurements_dict.copy()

        # Add functions to the top of the statement string
        pre_statement = format_pre_statement(
            self.unique_id, self.measure_info)

        code_combined = pre_statement + self.python_code
        self.logger.debug("Python 3 code to be executed:"
                          "\n{}".format(code_combined))

        try:
            codeOut = StringIO()
            codeErr = StringIO()
            # capture output and errors
            sys.stdout = codeOut
            sys.stderr = codeErr

            exec(code_combined, globals())

            # restore stdout and stderr
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            py_error = codeErr.getvalue()
            py_output = codeOut.getvalue()

            if py_error:
                self.logger.error("Error: {err}".format(err=py_error))
            if py_output:
                self.logger.debug("Output: {err}".format(err=py_output))

            codeOut.close()
            codeErr.close()
        except TimeoutError:
            self.logger.error("RPyC timed out. To prevent this error, increase the "
                              "RPyC Timeout value in the configuration menu.")
        except Exception:
            self.logger.error(
                "Error evaluating Python 3 code. Code and Traceback below.\n"
                "Python 3 code Executed:\n\n{code_rep}\n\n"
                "Error Traceback:\n\n{traceback}".format(
                    code_rep=code_combined,
                    traceback=traceback.format_exc()))
