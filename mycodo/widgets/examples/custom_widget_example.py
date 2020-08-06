# coding=utf-8
#
#  custom_widget_example.py - Custom widget example file for importing into Mycodo
#
#  Copyright (C) 2017  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com
#
import importlib.util
import os
import textwrap
import threading
import time

from flask import flash
from flask_babel import lazy_gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Widget
from mycodo.utils.code_verification import create_python_file
from mycodo.utils.code_verification import test_python_code
from mycodo.utils.database import db_retrieve_table_daemon


def execute_at_creation(widget, dict_widgets):
    pre_statement_loop = """import os
import sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.mycodo_client import DaemonControl
control = DaemonControl()

class PythonRun:
    def __init__(self, logger, unique_id):
        self.logger = logger
        self.unique_id = unique_id

    def python_code_loop(self):
"""

    pre_statement_single = """

    def python_code_refresh(self):
"""

    indented_code_loop = textwrap.indent(widget.code_execute_loop, ' ' * 8)
    indented_code_single = textwrap.indent(widget.code_execute_single, ' ' * 8)
    widget_python_code_run = pre_statement_loop + indented_code_loop + pre_statement_single + indented_code_single

    file_run = '{}/python_code_{}.py'.format(PATH_PYTHON_CODE_USER, unique_id)
    create_python_file(widget_python_code_run, file_run)
    success, error = test_python_code(widget_python_code_run, file_run)

    return error, success


def execute_at_modification(mod_widget, request_form):
    """
    Function to run when the Input is saved to evaluate the Python 3 code using pylint3
    :param mod_input: The WTForms object containing the form data submitted by the web GUI
    :param request_form: The custom_options form input data (if it exists)
    :return: tuple of (all_passed, error, mod_input) variables
    """
    all_passed = True

    error, success = execute_at_creation(
        mod_widget.unique_id, mod_widget, None)

    for each_error in error:
        flash(each_error, "error")

    for each_success in success:
        flash(each_success, "success")

    return all_passed, error, mod_widget


def constraints_pass_positive_value(mod_widget, value):
    """
    Check if the user widget is acceptable
    :param mod_widget: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_widget


WIDGET_INFORMATION = {
    'widget_name_unique': 'EXAMPLE_WIDGET',
    'widget_name': 'Example Custom Widget',
    'widget_library': '',

    'message': 'This is a custom message that will appear above the Widget options on the Function page. It merely demonstrates how to generate user option inputs. It will retrieve the last selected measurement, turn as selected output on for 15 seconds, then deactivate itself. Study the code to develop your own widget.',

    'options_enabled': [
        'custom_options'
    ],

    'execute_at_creation': execute_at_creation,
    'execute_at_modification': execute_at_modification,

    'dependencies_module': [
        # Example dependencies that will be installed when the user adds the widget
        # ('apt', 'build-essential', 'build-essential'),
        # ('apt', 'bison', 'bison'),
        # ('apt', 'libasound2-dev', 'libasound2-dev'),
        # ('apt', 'libpulse-dev', 'libpulse-dev'),
        # ('apt', 'swig', 'swig'),
        # ('pip-pypi', 'pocketsphinx', 'pocketsphinx')
    ],

    'custom_options': [
        {
            'id': 'python_code_loop',
            'type': 'text',
            'default_value': """import time
self.logger.info("TEST00: {}".format(time.time()))""",
            'required': True,
            'name': lazy_gettext('Python Code (Loop)'),
            'phrase': lazy_gettext('Python code to execute in a loop')
        },
        {
            'id': 'python_code_refresh',
            'type': 'text',
            'default_value': """import time
self.logger.info("TEST01: {}".format(time.time()))""",
            'required': True,
            'name': lazy_gettext('Python Code (Refresh)'),
            'phrase': lazy_gettext('Python code to execute every dashboard/widget refresh')
        },
    ]
}


class WidgetModule(AbstractController, threading.Thread):
    """
    Class to operate custom widget
    """
    def __init__(self, ready, unique_id, testing=False):
        threading.Thread.__init__(self)
        super(WidgetModule, self).__init__(ready, unique_id=unique_id, name=__name__)

        self.running = False
        self.unique_id = unique_id
        self.log_level_debug = None
        self.widget = {}
        self.timer = None
        self.period = None

        # Initialize custom options
        self.python_code_loop = None
        self.python_code_refresh = None

        # Set custom options
        widget = db_retrieve_table_daemon(Widget, unique_id=unique_id)
        self.setup_custom_options(WIDGET_INFORMATION['custom_options'], widget)

    def initialize_variables(self):
        widget = db_retrieve_table_daemon(Widget, unique_id=self.unique_id)
        self.log_level_debug = widget.log_level_debug
        self.set_log_level_debug(self.log_level_debug)

        self.logger.debug("Starting all Widget controllers")

        self.timer = time.time() + widget.refresh_duration
        self.period = widget.refresh_duration

        if not widget.code_execute_loop and not widget.code_execute_single:
            self.logger.error("Widget ID {}: No Python code to execute".format(widget.unique_id))
            return

        file_run = '{}/python_code_{}.py'.format(PATH_PYTHON_CODE_USER, widget.unique_id)
        module_name = "mycodo.widget.python_code_{}".format(os.path.basename(file_run).split('.')[0])
        spec = importlib.util.spec_from_file_location(module_name, file_run)
        python_code_run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(python_code_run)
        self.widget['class'] = python_code_run.PythonRun(self.logger, widget.unique_id)
        self.running = True
        self.widget['class'].python_code_loop()

    def loop(self):
        now = time.time()
        if self.timer < now and self.running:
            while self.timer < now:
                self.timer += self.period
            self.widget['class'].python_code_loop()

    def execute_refresh(self):
        if self.running:
            return self.widget['class'].python_code_refresh()
