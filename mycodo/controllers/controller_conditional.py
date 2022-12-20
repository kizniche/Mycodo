# coding=utf-8
#
# controller_conditional.py - Conditional controller
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
import datetime
import importlib.util
import os
import threading
import time
import timeit

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Misc
from mycodo.utils.conditional import save_conditional_code
from mycodo.utils.database import db_retrieve_table_daemon


class ConditionalController(AbstractController, threading.Thread):
    """
    Class to operate Conditional controller

    Conditional controllers allow user-editable Python code to be executed.
    This code typically queries measurement data and causes execution of function
    actions as a result of the conditions set by the user.
    """
    def __init__(self, ready, unique_id):
        threading.Thread.__init__(self)
        super().__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.pause_loop = False
        self.verify_pause_loop = True
        self.is_activated = None
        self.period = None
        self.start_offset = None
        self.pyro_timeout = None
        self.log_level_debug = None
        self.use_pylint = None
        self.message_include_code = None
        self.conditional_import = None
        self.conditional_initialize = None
        self.conditional_statement = None
        self.conditional_status = None
        self.timer_period = None
        self.file_run = None
        self.sample_rate = None
        self.time_conditional = None
        self.conditional_run = None

    def loop(self):
        # Pause loop to modify conditional.
        # Prevents execution of conditional while variables are
        # being modified.
        if self.pause_loop:
            self.verify_pause_loop = True
            while self.pause_loop:
                time.sleep(0.1)

        self.time_conditional = time.time()
        # Check if the conditional period has elapsed
        if (self.is_activated and self.timer_period and
                self.timer_period < self.time_conditional):

            while self.timer_period < self.time_conditional:
                self.timer_period += self.period

            self.attempt_execute(self.check_conditionals)

    def initialize_variables(self):
        """Define all settings."""
        cond = db_retrieve_table_daemon(
            Conditional, unique_id=self.unique_id)
        self.is_activated = cond.is_activated
        self.conditional_statement = cond.conditional_statement
        self.conditional_import = cond.conditional_import
        self.conditional_initialize = cond.conditional_initialize
        self.conditional_status = cond.conditional_status
        self.period = cond.period
        self.start_offset = cond.start_offset
        self.pyro_timeout = cond.pyro_timeout
        self.log_level_debug = cond.log_level_debug
        self.use_pylint = cond.use_pylint
        self.message_include_code = cond.message_include_code

        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_conditional

        self.set_log_level_debug(self.log_level_debug)

        now = time.time()
        self.timer_period = now + self.start_offset

        self.file_run = f'{PATH_PYTHON_CODE_USER}/conditional_{self.unique_id}.py'

        # If the file to execute doesn't exist, generate it
        if not os.path.exists(self.file_run):
            save_conditional_code(
                [],
                self.conditional_import,
                self.conditional_initialize,
                self.conditional_statement,
                self.conditional_status,
                self.unique_id,
                db_retrieve_table_daemon(ConditionalConditions, entry='all'),
                db_retrieve_table_daemon(Actions, entry='all'),
                timeout=self.pyro_timeout)

        module_name = f"mycodo.conditional.{os.path.basename(self.file_run).split('.')[0]}"
        spec = importlib.util.spec_from_file_location(
            module_name, self.file_run)
        conditional_run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conditional_run)
        self.conditional_run = conditional_run.ConditionalRun(
            self.logger, self.unique_id, '')

        self.logger.debug(
            f"Run Python Code (pre-replacement):\n{self.conditional_statement}")

        with open(self.file_run, 'r') as file:
            self.logger.debug(
                f"Run Python Code (post-replacement):\n{file.read()}")

        self.ready.set()
        self.running = True

    def refresh_settings(self):
        """Signal to pause the main loop and wait for verification, the refresh settings."""
        self.pause_loop = True
        while not self.verify_pause_loop:
            time.sleep(0.1)

        self.logger.info("Refreshing conditional settings")
        self.initialize_variables()

        self.pause_loop = False
        self.verify_pause_loop = False
        return "Conditional settings successfully refreshed"

    def check_conditionals(self):
        """
        Check if any Conditionals are activated and execute their code
        """
        cond = db_retrieve_table_daemon(
            Conditional, unique_id=self.unique_id, entry='first')

        timestamp = datetime.datetime.fromtimestamp(
            self.time_conditional).strftime('%Y-%m-%d %H:%M:%S')
        message = f"{timestamp}\n[Conditional {self.unique_id}]\n[Name: {cond.name}]"

        if self.message_include_code:
            message += '\n[Run Python Code Code Executed]:' \
                       '\n--------------------' \
                       f'\n{cond.conditional_statement}' \
                       '\n--------------------\n'

        message += '\n[Messages]:\n'

        self.conditional_run.message = message
        try:
            self.conditional_run.conditional_code_run()
        except Exception:
            self.logger.exception("Exception executing Run Python Code")

    def function_status(self):
        return self.conditional_run.function_status()

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.pre_stop()
        try:
            self.conditional_run.stop_conditional()
        except Exception:
            pass
        self.running = False
