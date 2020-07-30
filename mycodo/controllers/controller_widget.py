# coding=utf-8
#
# controller_widget.py - Widget controller to manage dashboard widgets
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
import importlib.util
import threading
import time
import timeit

import os

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Misc
from mycodo.databases.models import Widget
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class WidgetController(AbstractController, threading.Thread):
    """
    class for controlling widgets

    """
    def __init__(self, ready, debug):
        threading.Thread.__init__(self)
        super(WidgetController, self).__init__(ready, unique_id=None, name=__name__)

        self.set_log_level_debug(debug)
        self.control = DaemonControl()

        self.sample_rate = None
        self.dashboard_widget = {}
        self.widget_ready = {}
        self.period = {}
        self.timer = {}

    def initialize_variables(self):
        """ Begin initializing output parameters """
        self.sample_rate = db_retrieve_table_daemon(Misc, entry='first').sample_rate_controller_widget

        self.logger.debug("Initializing Widgets")
        try:
            widgets = db_retrieve_table_daemon(Widget, entry='all')
            for each_widget in widgets:
                self.widget_add_refresh(each_widget.unique_id)
            self.logger.debug("Widgets Initialized")
        except Exception as except_msg:
            self.logger.exception(
                "Problem initializing widgets: {err}".format(err=except_msg))

    def loop(self):
        """ Main loop of the widget controller """
        now = time.time()
        for unique_id, timer in self.timer.items():
            if timer < now:
                while self.timer[unique_id] < now:
                    self.timer[unique_id] += self.period[unique_id]
                self.dashboard_widget[unique_id]['class'].python_code_loop()

    def run_finally(self):
        """ Run when the controller is shutting down """
        pass

    def widget_add_refresh(self, unique_id):
        try:
            timer = timeit.default_timer()
            widget = db_retrieve_table_daemon(Widget, unique_id=unique_id)
            if widget and widget.graph_type == 'python_code':
                self.logger.debug("Starting all Widget controllers")
                self.dashboard_widget[widget.unique_id] = {}

                if not widget.code_execute_loop and not widget.code_execute_single:
                    self.logger.error("Widget ID {}: No Python code to execute".format(widget.unique_id))
                    return

                file_run = '{}/python_code_{}.py'.format(PATH_PYTHON_CODE_USER, widget.unique_id)
                module_name = "mycodo.widget.python_code_{}".format(os.path.basename(file_run).split('.')[0])
                spec = importlib.util.spec_from_file_location(module_name, file_run)
                python_code_run = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(python_code_run)
                self.dashboard_widget[widget.unique_id]['class'] = python_code_run.PythonRun(
                    self.logger, widget.unique_id)

                self.period[widget.unique_id] = widget.refresh_duration
                self.timer[widget.unique_id] = time.time() + widget.refresh_duration
                self.dashboard_widget[unique_id]['class'].python_code_loop()
                self.widget_ready[widget.unique_id] = True
                self.logger.info("Widget object {id} created/refreshed in {time:.1f} ms".format(
                    id=widget.unique_id.split('-')[0], time=(timeit.default_timer() - timer) * 1000))
        except Exception:
            self.logger.exception("Widget create/refresh")

    def widget_remove(self, unique_id):
        """Remove a widget"""
        try:
            timer = timeit.default_timer()
            if unique_id in self.dashboard_widget:
                self.widget_ready.pop(unique_id, None)
                self.dashboard_widget.pop(unique_id, None)
                self.period.pop(unique_id, None)
                self.timer.pop(unique_id, None)

                self.logger.info("Widget object {id} removed in {time:.1f} ms".format(
                    id=unique_id.split('-')[0], time=(timeit.default_timer() - timer) * 1000))
        except Exception:
            self.logger.exception("Widget remove")

    def widget_execute(self, unique_id):
        """Execute widget Python code"""
        try:
            if unique_id not in self.widget_ready or not self.widget_ready[unique_id]:
                return "Widget Controller Not Ready"
            if unique_id in self.dashboard_widget and 'class' in self.dashboard_widget[unique_id]:
                return_value = self.dashboard_widget[unique_id]['class'].python_code_refresh()
            else:
                return_value = "Widget not initialized in Daemon"
        except Exception as err:
            return_value = "Error: {}".format(err)
            self.logger.exception(1)

        return return_value