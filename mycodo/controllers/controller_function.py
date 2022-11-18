# coding=utf-8
#
# controller_function.py - Function controller that manages Custom Functions
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
import threading
import time

from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Misc
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.functions import parse_function_information
from mycodo.utils.modules import load_module_from_file


class FunctionController(AbstractController, threading.Thread):
    """
    Class for controlling the Function
    """
    def __init__(self, ready, unique_id):
        threading.Thread.__init__(self)
        super().__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.run_function = None
        self.sample_rate = None

        self.control = DaemonControl()

        self.timer_loop = time.time()
        self.dict_function = None
        self.device_measurements = None
        self.conversions = None
        self.function = None
        self.function_name = None
        self.log_level_debug = None
        self.device = None
        self.period = None

    def __str__(self):
        return str(self.__class__)

    def loop(self):
        if self.timer_loop < time.time():
            if not self.run_function:
                self.logger.error("Function could not be initialized. Shutting controller down.")
                self.running = False
                return

            while self.timer_loop < time.time():
                self.timer_loop += self.sample_rate

            try:
                self.run_function.loop()
            except Exception:
                self.logger.exception("Exception while running loop()")

    def run_finally(self):
        try:
            self.run_function.stop_function()
        except:
            pass

    def initialize_variables(self):
        function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)

        self.log_level_debug = function.log_level_debug
        self.set_log_level_debug(self.log_level_debug)

        self.dict_function = parse_function_information()

        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_function

        self.device_measurements = db_retrieve_table_daemon(
            DeviceMeasurements).filter(
            DeviceMeasurements.device_id == self.unique_id)

        self.conversions = db_retrieve_table_daemon(Conversion)

        self.function = function
        self.unique_id = function.unique_id
        self.function_name = function.name
        self.device = function.device

        if self.device in self.dict_function:
            function_loaded, status = load_module_from_file(
                self.dict_function[self.device]['file_path'],
                'function')

            if function_loaded:
                self.run_function = function_loaded.CustomModule(self.function)

            self.ready.set()
            self.running = True
        else:
            self.ready.set()
            self.running = False
            self.logger.error(f"'{self.device}' is not a valid device type. Deactivating controller.")
            return

    def call_module_function(self, button_id, args_dict, thread=True):
        """Execute function from custom action button press."""
        try:
            run_command = getattr(self.run_function, button_id)
            if thread:
                thread_run_command = threading.Thread(
                    target=run_command,
                    args=(args_dict,))
                thread_run_command.start()
                return 0, "Command sent to Function Controller and is running in the background."
            else:
                return_val = run_command(args_dict)
                return 0, ["Command sent to Function Controller.", return_val]
        except:
            self.logger.exception(
                f"Error executing button press function '{button_id}'")

    def function_action(self, action_string, args_dict=None, thread=True):
        """Execute function action."""
        if args_dict is None:
            args_dict = {}
        try:
            run_command = getattr(self.run_function, action_string)
            if thread:
                thread_run_command = threading.Thread(
                    target=run_command,
                    args=(args_dict,))
                thread_run_command.start()
                return 0, "Command sent to Function Controller and is running in the background."
            else:
                return_val = run_command(args_dict)
                return 0, ["Command sent to Function Controller.", return_val]
        except:
            self.logger.exception(f"Error executing function action '{action_string}'")

    def function_status(self):
        func_exists = getattr(self.run_function, "function_status", None)
        if callable(func_exists):
            return self.run_function.function_status()
        else:
            return {
                'error': ["function_status() missing from Function Class"]
            }
