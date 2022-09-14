# coding=utf-8
#
#  widget_python_code.py - Python code dashboard widget
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
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
import json
import logging
import os
import textwrap
import threading
import time

from flask import flash
from flask_babel import lazy_gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.databases import set_uuid
from mycodo.utils.code_verification import create_python_file
from mycodo.utils.code_verification import test_python_code
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.widgets.base_widget import AbstractWidget

logger = logging.getLogger(__name__)


def save_python_file(custom_options_json, unique_id):
    """Save python file"""
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

    indented_code_loop = textwrap.indent(
        custom_options_json['python_code_loop'], ' ' * 8)
    indented_code_single = textwrap.indent(
        custom_options_json['python_code_refresh'], ' ' * 8)
    widget_python_code_run = (
        pre_statement_loop +
        indented_code_loop +
        pre_statement_single +
        indented_code_single
    )

    file_run = '{}/python_code_{}.py'.format(PATH_PYTHON_CODE_USER, unique_id)
    create_python_file(widget_python_code_run, file_run)
    info, warning, success, error = test_python_code(
        widget_python_code_run, file_run)
    return info, warning, success, error


def execute_at_creation(error, new_widget, dict_widget):
    custom_options_json = json.loads(new_widget.custom_options)
    uuid = set_uuid()
    new_widget.unique_id = uuid
    info, warning, success, errors = save_python_file(
        custom_options_json, uuid)
    for each_success in success:
        flash(each_success, 'success')
    for each_info in info:
        flash(each_info, "info")
    for each_warning in warning:
        flash(each_warning, "warning")
    for each_error in error:
        flash(each_error, 'error')
    return error, new_widget


def execute_at_modification(
        mod_widget,
        request_form,
        custom_options_json_presave,
        custom_options_json_postsave):
    """
    Function to run when the Input is saved to evaluate the Python 3 code using pylint
    :param mod_widget:
    :param request_form:
    :param custom_options_json_presave:
    :param custom_options_json_postsave:
    :return:
    """
    allow_saving = True
    page_refresh = False

    info, warning, success, error = save_python_file(
        custom_options_json_postsave, mod_widget.unique_id)
    for each_success in success:
        flash(each_success, 'success')
    for each_info in info:
        flash(each_info, "info")
    for each_warning in warning:
        flash(each_warning, "warning")
    for each_error in error:
        flash(each_error, 'error')
    return allow_saving, page_refresh, mod_widget, custom_options_json_postsave


def execute_at_deletion(unique_id):
    pass


WIDGET_INFORMATION = {
    'widget_name_unique': 'widget_python_code',
    'widget_name': 'Python Code',
    'widget_library': '',

    'message': 'Executes Python code and displays the output within the widget.',

    'widget_width': 5,
    'widget_height': 4,

    'execute_at_creation': execute_at_creation,
    'execute_at_modification': execute_at_modification,
    'execute_at_deletion': execute_at_deletion,

    'custom_options': [
        {
            'id': 'enable_loop',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Enable Loop'),
            'phrase': lazy_gettext('Enable the Python Code (Loop) to be executed every Period')
        },
        {
            'id': 'period_seconds',
            'type': 'float',
            'default_value': 60,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Loop Period ({})'.format(lazy_gettext("Seconds")),
            'phrase': 'The period of time between executing loop code'
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 30.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': '{} ({})'.format(lazy_gettext("Refresh"), lazy_gettext("Seconds")),
            'phrase': 'The period of time between refreshing the widget'
        },
        {
            'id': 'font_em_body',
            'type': 'float',
            'default_value': 1.5,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Body Font Size (em)',
            'phrase': 'The font size of the body text'
        },
        {
            'id': 'python_code_loop',
            'type': 'multiline_text',
            'lines': 11,
            'default_value': """# This code is executed first and every controller refresh period.
# This will be executed even after browser sessions have ended.
from random import randint

if not hasattr(self, "stored_value"):  # Initialize objects saved across executions
    self.count = 0
    self.stored_value = None
    self.return_string = None

self.count += 1
current_value = randint(0, 100)  # Generate a random integer between 0 and 100
self.return_string = "Count: {count}<br>Last: {last}<br>Random: {now}".format(
    count=self.count, last=self.stored_value, now=current_value)
self.stored_value = current_value""",
            'required': True,
            'name': lazy_gettext('Python Code (Loop)'),
            'phrase': lazy_gettext('Python code to execute in a loop')
        },
        {
            'id': 'python_code_refresh',
            'type': 'multiline_text',
            'lines': 11,
            'default_value': """# This code will only be executed when a browser session is open on the dashboard.
# This code may be executed many times by different browser sessions viewing the dashboard.

return self.return_string""",
            'required': True,
            'name': lazy_gettext('Python Code (On Refresh)'),
            'phrase': lazy_gettext('Python code to execute every dashboard/widget refresh')
        },
    ],

    'widget_dashboard_head': """<!-- No head content -->""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    'widget_dashboard_body': """<span style="font-size: {{widget_options['font_em_body']}}em" id="text-python-code-{{each_widget.unique_id}}"></span>""",

    'widget_dashboard_js': """
  function getPythonCodeResponse(widget_id) {
    const url = '/widget_execute/' + widget_id;
    $.ajax(url, {
      success: function (response, responseText, jqXHR) {
        if (jqXHR.status !== 204) {
          if (response !== null) {
            document.getElementById("text-python-code-" + widget_id).innerHTML = response;
          } else {
            document.getElementById("text-python-code-" + widget_id).innerHTML = '{{_('NO DATA ERROR')}}';
          }
        } else {
          document.getElementById("text-python-code-" + widget_id).innerHTML = '{{_('CONNECTION ERROR')}}';
        }
      },
      error: function (jqXHR, textStatus, errorThrown) {
        document.getElementById("text-python-code-" + widget_id).innerHTML = '{{_('CONNECTION ERROR')}}';
      }
    });
  }

  function repeatPythonCodeResponse(widget_id, refresh_duration) {
    setInterval(function () {
      getPythonCodeResponse(widget_id);
    }, refresh_duration * 1000);  // Refresh duration in milliseconds
  }
""",

    'widget_dashboard_js_ready': """<!-- No JS ready content -->""",

    'widget_dashboard_js_ready_end': """
  $(function() {
    getPythonCodeResponse('{{each_widget.unique_id}}');
    repeatPythonCodeResponse('{{each_widget.unique_id}}', {{widget_options['refresh_seconds']}});
  });
"""
}


class WidgetModule(AbstractWidget, threading.Thread):
    """Class to operate custom widget."""
    def __init__(self, widget, testing=False):
        threading.Thread.__init__(self)
        super().__init__(widget, testing=testing, name=__name__)

        self.running = False
        self.unique_id = widget.unique_id
        self.log_level_debug = None
        self.widget = None
        self.timer = time.time()

        # Unused custom options (only used in frontend)
        # self.refresh_seconds = None
        # self.font_em_body = None
        # self.python_code_loop = None
        # self.python_code_refresh = None

        self.enable_loop = None
        self.period_seconds = None
        self.setup_custom_options_json(WIDGET_INFORMATION['custom_options'], widget)

    def initialize_variables(self):
        self.logger.debug("Initializing module")

        file_run = '{}/python_code_{}.py'.format(PATH_PYTHON_CODE_USER, self.unique_id)
        if not os.path.exists(file_run):
            self.logger.error("Widget ID {}: No Python file found to execute: {}".format(
                self.unique_id, file_run))
            return

        module_name = "mycodo.widget.python_code_{}".format(os.path.basename(file_run).split('.')[0])
        spec = importlib.util.spec_from_file_location(module_name, file_run)
        python_code_run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(python_code_run)
        self.widget = python_code_run.PythonRun(self.logger, self.unique_id)
        self.running = True

    def loop(self):
        if self.enable_loop and self.running and self.widget:
            now = time.time()
            if self.timer < now:
                while self.timer < now:
                    self.timer += self.period_seconds
                self.widget.python_code_loop()

    def execute_refresh(self):
        if self.running and self.widget:
            return self.widget.python_code_refresh()
