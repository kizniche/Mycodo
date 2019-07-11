# coding=utf-8
import sys
import traceback

from io import StringIO

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

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

    'interfaces': ['Mycodo'],
    'cmd_command': """import random  # Import any external libraries

# Get measurements/values (for example, these are randomly-generated numbers)
random_value_channel_0 = random.uniform(10.0,100.0)
random_value_channel_1 = random.uniform(500.0,1000.0)

# Store measurements in database (must specify the channel and measurement)
store_measurement(channel=0, measurement=random_value_channel_0)
store_measurement(channel=1, measurement=random_value_channel_1)
"""
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
        pre_statement = """
import os, sys
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

""".format(unique_id=self.unique_id, measure_info=self.measure_info)

        cond_statement_combined = pre_statement + self.python_code
        self.logger.debug("Python 3 code to be executed:"
                          "\n{}".format(cond_statement_combined))

        try:
            codeOut = StringIO()
            codeErr = StringIO()
            # capture output and errors
            sys.stdout = codeOut
            sys.stderr = codeErr

            exec(cond_statement_combined, globals())

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
                "Error evaluating conditional statement. Code and Traceback below.\n"
                "Conditional Statement Executed:\n\n{cond_rep}\n\n"
                "Conditional Statement Traceback:\n\n{traceback}".format(
                    cond_rep=cond_statement_replaced,
                    traceback=traceback.format_exc()))
