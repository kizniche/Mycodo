# coding=utf-8
import importlib.util
import importlib.util
import os
import textwrap

from flask import flash

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.databases.models import Actions
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import set_user_grp

def generate_code(input_id, python_code):
    error = []
    pre_statement_run = """import os
import sys
sys.path.append(os.path.abspath('/opt/Mycodo'))
from mycodo.databases.models import Conversion
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.inputs import parse_measurement
control = DaemonControl()

class PythonActionRun:
    def __init__(self, logger, action_id):
        self.logger = logger
        self.action_id = action_id
        self.control = control

    def python_code_run(self, dict_vars):
"""

    indented_code = textwrap.indent(python_code, ' ' * 8)
    action_python_code_run = pre_statement_run + indented_code

    assure_path_exists(PATH_PYTHON_CODE_USER)
    file_run = '{}/action_input_python_code_{}.py'.format(
        PATH_PYTHON_CODE_USER, input_id)
    with open(file_run, 'w') as fw:
        fw.write('{}\n'.format(action_python_code_run))
        fw.close()
    set_user_grp(file_run, 'mycodo', 'mycodo')

    for each_error in error:
        flash(each_error, 'error')

    return action_python_code_run, file_run


ACTION_INFORMATION = {
    'name_unique': 'action_input_execute_python_code',
    'name': "Execute Python 3 Code",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['inputs'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Execute Python 3 code when measurements are acquired.',

    'usage': '',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'python_code',
            'type': 'multiline_text',
            'lines': 7,
            'default_value': """# Print dictionary of Input value(s) to log
self.logger.info(f"Input measurements: {dict_vars['measurements_dict']}")

# Return dictionary. This allows you to modify the values before being passed to the next Action.
return dict_vars""",
            'required': True,
            'col_width': 12,
            'name': 'Python 3 Code',
            'phrase': 'The code to execute'
        },
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Execute Python Code."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.python_code = None

        self.run_python = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        action_python_code_run, file_run = generate_code(self.unique_id, self.python_code)

        module_name = "mycodo.action.{}".format(os.path.basename(file_run).split('.')[0])
        spec = importlib.util.spec_from_file_location(module_name, file_run)
        action_run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(action_run)
        self.run_python = action_run.PythonActionRun(self.logger, self.unique_id)

        self.action_setup = True

    def run_action(self, dict_vars):
        self.logger.debug(f"pre action run dict_vars: {dict_vars}")

        dict_vars = self.run_python.python_code_run(dict_vars)

        self.logger.debug(f"post action run dict_vars: {dict_vars}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
