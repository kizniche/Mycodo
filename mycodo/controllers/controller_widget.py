# coding=utf-8
#
# controller_widget.py - Widget controller to manage dashboard widgets
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
import threading
import timeit

from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Misc
from mycodo.databases.models import Widget
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.modules import load_module_from_file
from mycodo.utils.widgets import parse_widget_information


class WidgetController(AbstractController, threading.Thread):
    """class for controlling widgets."""
    def __init__(self, ready, debug):
        threading.Thread.__init__(self)
        super().__init__(ready, unique_id=None, name=__name__)

        self.set_log_level_debug(debug)
        self.control = DaemonControl()

        self.widget_loaded = {}
        self.widget_ready = {}
        self.dict_widgets = {}
        self.sample_rate = None

    def initialize_variables(self):
        """Begin initializing widget parameters."""
        self.dict_widgets = parse_widget_information()

        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_widget

        self.logger.debug("Initializing Widgets")
        try:
            widgets = db_retrieve_table_daemon(Widget, entry='all')

            for each_widget in widgets:
                if each_widget.graph_type in self.dict_widgets:
                    self.widget_add_refresh(each_widget.unique_id)
                else:
                    self.logger.error(f"'{each_widget.graph_type}' is not a valid widget type")

            self.logger.debug("Widgets Initialized")
        except Exception:
            self.logger.exception("Problem initializing widgets")

        self.ready.set()
        self.running = True

    def loop(self):
        for each_unique_id in self.widget_ready:
            if self.widget_ready[each_unique_id] and each_unique_id in self.widget_loaded:
                try:
                    self.widget_loaded[each_unique_id].loop()
                except Exception:
                    self.logger.exception("Error running widget loop()")

    def widget_add_refresh(self, unique_id):
        self.dict_widgets = parse_widget_information()
        widget = db_retrieve_table_daemon(Widget, unique_id=unique_id)
        if ('no_class' in self.dict_widgets[widget.graph_type] and
                self.dict_widgets[widget.graph_type]['no_class']):
            return

        try:
            timer = timeit.default_timer()
            widget_loaded, status = load_module_from_file(
                self.dict_widgets[widget.graph_type]['file_path'], 'widgets')
            widget = db_retrieve_table_daemon(Widget, unique_id=unique_id)

            if widget_loaded:
                self.widget_loaded[unique_id] = widget_loaded.WidgetModule(widget)
                self.widget_loaded[unique_id].initialize_variables()
                self.widget_ready[unique_id] = True
                diff = (timeit.default_timer() - timer) * 1000
                self.logger.info(f"Widget {widget.unique_id.split('-')[0]} created/refreshed in {diff:.1f} ms")
        except Exception:
            self.logger.exception("Widget create/refresh")

    def widget_remove(self, unique_id):
        """Remove a widget."""
        try:
            timer = timeit.default_timer()
            if unique_id in self.widget_loaded:
                self.widget_ready.pop(unique_id, None)
                self.widget_loaded.pop(unique_id, None)

                diff = (timeit.default_timer() - timer) * 1000
                self.logger.info(f"Widget object {unique_id.split('-')[0]} removed in {diff:.1f} ms")
        except Exception:
            self.logger.exception("Widget remove")

    def widget_execute(self, unique_id):
        """Execute widget Python code"""
        try:
            if unique_id not in self.widget_ready or not self.widget_ready[unique_id]:
                return "Widget Controller Not Ready"
            elif unique_id in self.widget_loaded:
                return_value = self.widget_loaded[unique_id].execute_refresh()
            else:
                return_value = "Widget not initialized in Daemon"
        except Exception as err:
            return_value = f"Error: {err}"
            self.logger.exception("widget_execute()")

        return return_value
