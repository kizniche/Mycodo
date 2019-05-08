# coding=utf-8
#
# controller_conditional.py - Conditional controller
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

import datetime
import logging
import sys
import threading
import time
import timeit
import traceback

from io import StringIO

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Misc
from mycodo.databases.models import SMTP
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class ConditionalController(threading.Thread):
    """
    Class to operate Conditional controller

    Conditionals are conditional statements that can either be True or False
    When a conditional is True, one or more actions associated with that
    conditional are executed.

    The main loop in this class will continually check if the timers for
    Measurement Conditionals have elapsed, then check if any of the
    conditionals are True with the check_conditionals() function. If any are
    True, trigger_conditional_actions() will be ran to execute all actions
    associated with that particular conditional.

    Edge and Output conditionals are triggered from
    the Input and Output controllers, respectively, and the
    trigger_conditional_actions() function in this class will be ran.
    """
    def __init__(self, ready, function_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger(__name__)
        self.logger = logging.LoggerAdapter(
            self.logger, {'name_info': function_id.split('-')[0]})

        self.function_id = function_id
        self.running = False
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.pause_loop = False
        self.verify_pause_loop = True
        self.ready = ready
        self.control = DaemonControl()

        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_conditional

        self.is_activated = None
        self.smtp_max_count = None
        self.email_count = None
        self.allowed_to_send_notice = None
        self.smtp_wait_timer = None
        self.timer_period = None
        self.period = None
        self.start_offset = None
        self.refractory_period = None
        self.log_level_debug = None
        self.conditional_statement = None
        self.timer_refractory_period = None
        self.smtp_wait_timer = None
        self.timer_period = None
        self.timer_start_time = None
        self.timer_end_time = None
        self.unique_id_1 = None
        self.unique_id_2 = None
        self.trigger_actions_at_period = None
        self.trigger_actions_at_start = None
        self.method_start_time = None
        self.method_end_time = None
        self.method_start_act = None

        self.setup_settings()

    def run(self):
        try:
            self.running = True
            self.logger.info(
                "Activated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            while self.running:
                # Pause loop to modify conditional statements.
                # Prevents execution of conditional while variables are
                # being modified.
                if self.pause_loop:
                    self.verify_pause_loop = True
                    while self.pause_loop:
                        time.sleep(0.1)

                if (self.is_activated and self.timer_period and
                        self.timer_period < time.time()):
                    check_approved = False

                    # Check if the conditional period has elapsed
                    if self.timer_refractory_period < time.time():
                        while self.timer_period < time.time():
                            self.timer_period += self.period
                        check_approved = True

                    if check_approved:
                        self.check_conditionals()

                time.sleep(self.sample_rate)

            self.running = False
            self.logger.info(
                "Deactivated in {:.1f} ms".format(
                    (timeit.default_timer() -
                     self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
            self.logger.exception("Run Error: {err}".format(
                err=except_msg))

    def refresh_settings(self):
        """ Signal to pause the main loop and wait for verification, the refresh settings """
        self.pause_loop = True
        while not self.verify_pause_loop:
            time.sleep(0.1)

        self.logger.info("Refreshing conditional settings")
        self.setup_settings()

        self.pause_loop = False
        self.verify_pause_loop = False
        return "Conditional settings successfully refreshed"

    def setup_settings(self):
        """ Define all settings """
        cond = db_retrieve_table_daemon(
            Conditional, unique_id=self.function_id)

        self.is_activated = cond.is_activated

        self.smtp_max_count = db_retrieve_table_daemon(
            SMTP, entry='first').hourly_max
        self.email_count = 0
        self.allowed_to_send_notice = True

        now = time.time()

        self.smtp_wait_timer = now + 3600
        self.timer_period = None

        self.conditional_statement = cond.conditional_statement
        self.period = cond.period
        self.start_offset = cond.start_offset
        self.refractory_period = cond.refractory_period
        self.log_level_debug = cond.log_level_debug
        self.timer_refractory_period = 0
        self.smtp_wait_timer = now + 3600
        self.timer_period = now + self.start_offset

        if self.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def check_conditionals(self):
        """
        Check if any Conditionals are activated and
        execute their actions if the Conditional is true.

        For example, if "temperature > 30", notify me@gmail.com

        "if measured temperature is above 30C" is the Conditional to check.
        "notify me@gmail.com" is the Condition Action to execute if the
        Conditional is True.
        """

        cond = db_retrieve_table_daemon(
            Conditional, unique_id=self.function_id, entry='first')

        now = time.time()
        timestamp = datetime.datetime.fromtimestamp(
            now).strftime('%Y-%m-%d %H:%M:%S')
        message = "{ts}\n[Conditional {id}]\n[Name: {name}]".format(
            ts=timestamp,
            name=cond.name,
            id=self.function_id)

        # self.logger.info("Conditional Statement (pre-replacement):\n{}".format(self.conditional_statement))
        cond_statement_replaced = self.conditional_statement

        # Replace short condition IDs in conditional statement with full condition IDs
        for each_condition in db_retrieve_table_daemon(
                ConditionalConditions, entry='all'):
            condition_id_short = each_condition.unique_id.split('-')[0]
            cond_statement_replaced = cond_statement_replaced.replace(
                '{{{id}}}'.format(id=condition_id_short),
                each_condition.unique_id)

        # Replace short action IDs in conditional statement with full action IDs
        for each_action in db_retrieve_table_daemon(Actions, entry='all'):
            action_id_short = each_action.unique_id.split('-')[0]
            cond_statement_replaced = cond_statement_replaced.replace(
                '{{{id}}}'.format(id=action_id_short),
                each_action.unique_id)

        message += '\n[Conditional Statement]:' \
                   '\n--------------------' \
                   '\n{statement}' \
                   '\n--------------------' \
                   '\n'.format(
            statement=cond.conditional_statement)

        # Add functions to the top of the statement string
        pre_statement = """
import os, sys
sys.path.append(os.path.abspath('/var/mycodo-root'))
from mycodo.mycodo_client import DaemonControl
control = DaemonControl()

message='''{message}'''

def measure(condition_id):
    return control.get_condition_measurement(condition_id)

def measure_dict(condition_id):
    string_sets = control.get_condition_measurement_dict(condition_id)
    if string_sets:
        list_ts_values = []
        for each_set in string_sets.split(';'):
            ts_value = each_set.split(',')
            list_ts_values.append({{'time': ts_value[0], 'value': float(ts_value[1])}})
        return list_ts_values

def run_all_actions(message=message):
    control.trigger_all_actions('{function_id}', message=message)

def run_action(action_id, message=message):
    control.trigger_action(action_id, message=message, single_action=True)

""".format(message=message, function_id=self.function_id)

        cond_statement_replaced = pre_statement + cond_statement_replaced
        # self.logger.info("Conditional Statement (replaced):\n{}".format(cond_statement_replaced))

        # Set the refractory period
        if self.refractory_period:
            self.timer_refractory_period = time.time() + self.refractory_period

        try:
            codeOut = StringIO()
            codeErr = StringIO()
            # capture output and errors
            sys.stdout = codeOut
            sys.stderr = codeErr

            exec(cond_statement_replaced, globals())

            # restore stdout and stderr
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            py_error = codeErr.getvalue()
            py_output = codeOut.getvalue()

            if py_error:
                self.logger.error("Error: {err}".format(err=py_error))

            codeOut.close()
            codeErr.close()
        except:
            self.logger.error(
                "Error evaluating conditional statement. "
                "Replaced Conditional Statement:\n\n{cond_rep}\n\n{traceback}".format(
                    cond_rep=cond_statement_replaced,
                    traceback=traceback.format_exc()))

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
