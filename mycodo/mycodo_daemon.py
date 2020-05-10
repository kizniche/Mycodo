#!/usr/bin/mycodo-python
# -*- coding: utf-8 -*-
#
#  mycodo_daemon.py - Daemon for managing Mycodo controllers, such as sensors,
#                     outputs, PID controllers, etc.
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

import sys

import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import argparse
import logging
import threading
import time
import timeit

import resource
from Pyro5.api import Daemon
from Pyro5.api import Proxy
from Pyro5.api import expose
from daemonize import Daemonize

from mycodo.config import DAEMON_LOG_FILE
from mycodo.config import DAEMON_PID_FILE
from mycodo.config import DOCKER_CONTAINER
from mycodo.config import MYCODO_VERSION
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config import STATS_CSV
from mycodo.config import STATS_INTERVAL
from mycodo.config import UPGRADE_CHECK_INTERVAL
from mycodo.controllers.controller_conditional import ConditionalController
from mycodo.controllers.controller_input import InputController
from mycodo.controllers.controller_lcd import LCDController
from mycodo.controllers.controller_math import MathController
from mycodo.controllers.controller_output import OutputController
from mycodo.controllers.controller_pid import PIDController
from mycodo.controllers.controller_trigger import TriggerController
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import CustomController
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import Math
from mycodo.databases.models import Misc
from mycodo.databases.models import PID
from mycodo.databases.models import Trigger
from mycodo.databases.utils import session_scope
from mycodo.devices.camera import camera_record
from mycodo.utils.controllers import parse_controller_information
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.function_actions import get_condition_value
from mycodo.utils.function_actions import get_condition_value_dict
from mycodo.utils.function_actions import trigger_action
from mycodo.utils.function_actions import trigger_function_actions
from mycodo.utils.github_release_info import MycodoRelease
from mycodo.utils.modules import load_module_from_file
from mycodo.utils.statistics import add_update_csv
from mycodo.utils.statistics import recreate_stat_file
from mycodo.utils.statistics import return_stat_file_dict
from mycodo.utils.statistics import send_anonymous_stats
from mycodo.utils.tools import generate_output_usage_report
from mycodo.utils.tools import next_schedule

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class DaemonController:
    """
    Mycodo daemon

    Read tables containing controller settings from SQLite database.
    Start a thread for each controller.
    Loop until the daemon is instructed to shut down.
    Signal each thread to shut down and wait for each thread to shut down.

    All output operations (turning on/off) is operated by one output controller.

    Each connected input has its own controller to collect all measurements
    that particular input can produce and put then into an influxdb database.

    Each PID controller is associated with only one measurement from one
    input controller.

    """

    def __init__(self, debug):
        self.logger = logging.getLogger('mycodo.daemon')
        if not debug:
            self.logger.setLevel(logging.INFO)

        self.logger.info(
            "Mycodo daemon v{ver} starting".format(ver=MYCODO_VERSION))

        self.log_level_debug = debug
        self.startup_timer = timeit.default_timer()
        self.daemon_startup_time = None
        self.daemon_run = True
        self.terminated = False
        self.debug = debug

        # Controller object that will store the thread objects for each
        # controller
        self.controller = {
            'Conditional': {},
            'Output': None,  # May only launch a single thread for this controller
            'Input': {},
            'LCD': {},
            'Math': {},
            'PID': {},
            'Trigger': {},
            'Custom': {}
        }

        # Controllers that may launch multiple threads
        # Order matters for starting and shutting down
        self.cont_types = [
            'Conditional',
            'Trigger',
            'Input',
            'Math',
            'PID',
            'LCD',
            'Custom'
        ]

        self.thread_shutdown_timer = None
        self.start_time = time.time()
        self.timer_ram_use = time.time()
        self.timer_stats = time.time() + 120
        self.timer_upgrade = time.time() + 120
        self.timer_upgrade_message = time.time()

        # Update camera settings
        self.camera = []
        self.refresh_daemon_camera_settings()

        # Update Misc settings
        self.output_usage_report_gen = None
        self.output_usage_report_span = None
        self.output_usage_report_day = None
        self.output_usage_report_hour = None
        self.output_usage_report_next_gen = None
        self.opt_out_statistics = None
        self.enable_upgrade_check = None
        self.refresh_daemon_misc_settings()

        state = 'disabled' if self.opt_out_statistics else 'enabled'
        self.logger.debug("Anonymous statistics {state}".format(state=state))

    def run(self):
        self.start_all_controllers(self.debug)
        self.daemon_startup_time = timeit.default_timer() - self.startup_timer
        self.logger.info("Mycodo daemon started in {sec:.3f} seconds".format(
            sec=self.daemon_startup_time))
        self.startup_stats()

        # loop until daemon is instructed to shut down
        while self.daemon_run:
            now = time.time()

            try:
                # Log ram usage every 5 days
                if now > self.timer_ram_use:
                    while now > self.timer_ram_use:
                        self.timer_ram_use += 432000
                    self.log_ram_usage()

                # Capture time-lapse image (if enabled)
                self.check_all_timelapses(now)

                # Generate output usage report (if enabled)
                if (self.output_usage_report_gen and
                        self.output_usage_report_next_gen and
                        now > self.output_usage_report_next_gen):
                    generate_output_usage_report()
                    self.refresh_daemon_misc_settings()  # Update timer

                # Collect and send anonymous statistics (if enabled)
                if (not self.opt_out_statistics and
                        now > self.timer_stats):
                    while now > self.timer_stats:
                        self.timer_stats += STATS_INTERVAL
                    self.send_stats()

                # Check if running the latest version (if enabled)
                if now > self.timer_upgrade:
                    while now > self.timer_upgrade:
                        self.timer_upgrade += UPGRADE_CHECK_INTERVAL
                    if self.enable_upgrade_check:
                        self.check_mycodo_upgrade_exists(now)

            except Exception:
                self.logger.exception("Daemon Error")
                raise

            time.sleep(1)

        # If the daemon errors or finishes, shut it down
        self.logger.debug("Stopping all running controllers")
        self.stop_all_controllers()

        self.logger.info(
            "Mycodo daemon terminated in {:.3f} seconds\n\n".format(
                timeit.default_timer() - self.thread_shutdown_timer))
        self.terminated = True

        # Wait for the client to receive the response before it disconnects
        time.sleep(1)

    @staticmethod
    def get_condition_measurement(condition_id):
        condition_return = get_condition_value(condition_id)
        return condition_return

    @staticmethod
    def get_condition_measurement_dict(condition_id):
        return get_condition_value_dict(condition_id)

    @staticmethod
    def determine_controller_type(unique_id):
        db_tables = {
            'Conditional': db_retrieve_table_daemon(Conditional, unique_id=unique_id),
            'Input': db_retrieve_table_daemon(Input, unique_id=unique_id),
            'LCD': db_retrieve_table_daemon(LCD, unique_id=unique_id),
            'Math': db_retrieve_table_daemon(Math, unique_id=unique_id),
            'PID': db_retrieve_table_daemon(PID, unique_id=unique_id),
            'Trigger': db_retrieve_table_daemon(Trigger, unique_id=unique_id),
            'Custom': db_retrieve_table_daemon(CustomController, unique_id=unique_id)
        }
        controller_type = None
        for each_type in db_tables:
            if db_tables[each_type]:
                controller_type = each_type
        return controller_type

    def controller_activate(self, cont_id):
        """
        Activate currently-inactive controller

        :return: 0 for success, 1 for fail, with success or error message
        :rtype: int, str

        :param cont_id: Unique ID for controller
        :type cont_id: str
        """
        cont_type = self.determine_controller_type(cont_id)
        try:
            if cont_id in self.controller[cont_type]:
                if self.controller[cont_type][cont_id].is_running():
                    message = "Cannot activate {type} controller with ID {id}: " \
                              "It's already active.".format(type=cont_type,
                                                            id=cont_id)
                    self.logger.warning(message)
                    return 1, message

            controller_manage = {}
            ready = threading.Event()

            if cont_type == 'Conditional':
                controller_manage['type'] = Conditional
                controller_manage['function'] = ConditionalController
            elif cont_type == 'LCD':
                controller_manage['type'] = LCD
                controller_manage['function'] = LCDController
            elif cont_type == 'Input':
                controller_manage['type'] = Input
                controller_manage['function'] = InputController
            elif cont_type == 'Math':
                controller_manage['type'] = Math
                controller_manage['function'] = MathController
            elif cont_type == 'PID':
                controller_manage['type'] = PID
                controller_manage['function'] = PIDController
            elif cont_type == 'Trigger':
                controller_manage['type'] = Trigger
                controller_manage['function'] = TriggerController
            elif cont_type == 'Custom':
                controller_manage['type'] = CustomController

                custom_controller = db_retrieve_table_daemon(controller_manage['type'],
                                                             unique_id=cont_id)
                dict_controllers = parse_controller_information()
                if custom_controller and custom_controller.device in dict_controllers:
                    input_loaded = load_module_from_file(
                        dict_controllers[custom_controller.device]['file_path'],
                        'controllers')
                    controller_manage['function'] = input_loaded.CustomModule
                else:
                    return 1, "Custom controller not found.".format(
                        type=cont_type)

            else:
                return 1, "'{type}' not a valid controller type.".format(
                    type=cont_type)

            # Check if the controller actually exists
            controller = db_retrieve_table_daemon(controller_manage['type'],
                                                  unique_id=cont_id)
            if not controller:
                return 1, "{type} controller with ID {id} not found.".format(
                    type=cont_type, id=cont_id)

            # set as active in SQL database
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_cont = new_session.query(controller_manage['type']).filter(
                    controller_manage['type'].unique_id == cont_id).first()
                mod_cont.is_activated = True
                new_session.commit()

            self.controller[cont_type][cont_id] = controller_manage['function'](
                ready, cont_id)
            self.controller[cont_type][cont_id].daemon = True
            self.controller[cont_type][cont_id].start()
            ready.wait()  # wait for thread to return ready

            return 0, "{type} controller with ID {id} " \
                "activated.".format(type=cont_type, id=cont_id)

        except Exception as except_msg:
            message = "Could not activate {type} controller with ID {id}:" \
                      " {e}".format(type=cont_type, id=cont_id, e=except_msg)
            self.logger.exception(message)
            return 1, message

    def controller_deactivate(self, cont_id):
        """
        Deactivate currently-active controller

        :return: 0 for success, 1 for fail, with success or error message
        :rtype: int, str

        :param cont_id: Unique ID for controller
        :type cont_id: str
        """
        cont_type = self.determine_controller_type(cont_id)
        try:
            if cont_id in self.controller[cont_type]:
                if self.controller[cont_type][cont_id].is_running():
                    try:
                        if cont_type == 'PID':
                            self.controller[cont_type][cont_id].stop_controller(deactivate_pid=True)
                        else:
                            self.controller[cont_type][cont_id].stop_controller()
                        self.controller[cont_type][cont_id].join()
                        return 0, "{type} controller with ID {id} "\
                            "deactivated.".format(type=cont_type, id=cont_id)
                    except Exception as except_msg:
                        message = "Could not deactivate {type} controller with " \
                                  "ID {id}: {err}".format(type=cont_type,
                                                          id=cont_id,
                                                          err=except_msg)
                        self.logger.exception(message)
                        return 1, message
                else:
                    message = "Could not deactivate {type} controller with ID " \
                              "{id}, it's not active.".format(type=cont_type,
                                                              id=cont_id)
                    self.logger.debug(message)
                    return 1, message
            else:
                message = "{type} controller with ID {id} not found".format(
                    type=cont_type, id=cont_id)
                self.logger.warning(message)
                return 1, message
        except Exception as except_msg:
            message = "Could not deactivate {type} controller with ID {id}:" \
                      " {e}".format(type=cont_type, id=cont_id, e=except_msg)
            self.logger.exception(message)
            return 1, message

    def controller_is_active(self, cont_id):
        """
        Checks if a controller is active

        :return: True for active, False for inactive
        :rtype: bool

        :param cont_id: Unique ID for controller
        :type cont_id: str
        """
        cont_type = self.determine_controller_type(cont_id)
        try:
            if cont_id in self.controller[cont_type]:
                if self.controller[cont_type][cont_id].is_running():
                    return True
                else:
                    message = "{type} controller with ID " \
                              "{id} is not active.".format(
                                type=cont_type, id=cont_id)
                    self.logger.debug(message)
                    return False
            else:
                message = "{type} controller with ID {id} not found".format(
                    type=cont_type, id=cont_id)
                self.logger.debug(message)
                return False
        except Exception as except_msg:
            message = "Error: {type} controller with ID {id}:" \
                      " {err}".format(
                type=cont_type, id=cont_id, err=except_msg)
            self.logger.exception(message)
            return False

    def check_daemon(self):
        try:
            for cond_id in self.controller['Conditional']:
                if not self.controller['Conditional'][cond_id].is_running():
                    return "Error: Conditional ID {}".format(cond_id)
            for input_id in self.controller['Input']:
                if not self.controller['Input'][input_id].is_running():
                    return "Error: Input ID {}".format(input_id)
            for lcd_id in self.controller['LCD']:
                if not self.controller['LCD'][lcd_id].is_running():
                    return "Error: LCD ID {}".format(lcd_id)
            for math_id in self.controller['Math']:
                if not self.controller['Math'][math_id].is_running():
                    return "Error: Math ID {}".format(math_id)
            for pid_id in self.controller['PID']:
                if not self.controller['PID'][pid_id].is_running():
                    return "Error: PID ID {}".format(pid_id)
            for trigger_id in self.controller['Trigger']:
                if not self.controller['Trigger'][trigger_id].is_running():
                    return "Error: Trigger ID {}".format(trigger_id)
            for controller_id in self.controller['Custom']:
                if not self.controller['Custom'][controller_id].is_running():
                    return "Error: Custom ID {}".format(controller_id)
            if not self.controller['Output'].is_running():
                return "Error: Output controller"
        except Exception as except_msg:
            message = "Could not check running threads: {e}".format(
                e=except_msg)
            self.logger.exception(message)
            return "Exception: {msg}".format(msg=except_msg)

    def input_force_measurements(self, input_id):
        """
        Force Input measurements to be acquired

        :return: success or error message
        :rtype: str

        :param input_id: Which Input controller ID is to be affected?
        :type input_id: str

        """
        try:
            return self.controller['Input'][input_id].force_measurements()
        except Exception as except_msg:
            message = "Cannot force acquisition of Input measurements:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)
            return 1, message

    def input_custom_button(self, input_id, button_id, args_dict):
        """
        Force Input function to be executed

        :return: success or error message
        :rtype: str

        :param input_id: Which Input controller ID is to be affected?
        :type input_id: str
        :param button_id: ID of button pressed
        :type button_id: str

        """
        try:
            return self.controller['Input'][input_id].custom_button_exec_function(button_id, args_dict)
        except Exception as except_msg:
            message = "Cannot execute Input function from custom action:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)
            return 1, message

    def input_atlas_flow_clear_total_volume(self, input_id):
        """
        Force Input to clear the total flow amount

        :return: success or error message
        :rtype: str

        :param input_id: Which Input controller ID is to be affected?
        :type input_id: str

        """
        try:
            return self.controller['Input'][input_id].clear_total_volume()
        except Exception as except_msg:
            message = "Could not clear total volume:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)
            return 1, message

    def lcd_reset(self, lcd_id):
        """
        Resets an LCD

        :return: success or error message
        :rtype: str

        :param lcd_id: Which LCD controller ID is to be affected?
        :type lcd_id: str

        """
        try:
            return self.controller['LCD'][lcd_id].lcd_init()
        except KeyError:
            message = "Cannot reset LCD, LCD not running"
            self.logger.exception(message)
            return 0, message
        except Exception as except_msg:
            message = "Could not reset LCD: {e}".format(e=except_msg)
            self.logger.exception(message)

    def lcd_backlight(self, lcd_id, state):
        """
        Turn on or off the LCD backlight

        :return: success or error message
        :rtype: str

        :param lcd_id: Which LCD controller ID is to be affected?
        :type lcd_id: str
        :param state: Turn flashing on (1) or off (0)
        :type state: bool

        """
        try:
            return self.controller['LCD'][lcd_id].lcd_backlight(state)
        except KeyError:
            message = "Cannot stop flashing, LCD not running"
            self.logger.exception(message)
            return 0, message
        except Exception as except_msg:
            message = "Could not flash LCD: {e}".format(e=except_msg)
            self.logger.exception(message)

    def lcd_flash(self, lcd_id, state):
        """
        Begin or end a repeated flashing of an LCD

        :return: success or error message
        :rtype: str

        :param lcd_id: Which LCD controller ID is to be affected?
        :type lcd_id: str
        :param state: Turn flashing on (1/True) or off (0/False)
        :type state: bool

        """
        try:
            return self.controller['LCD'][lcd_id].lcd_flash(state)
        except KeyError:
            message = "LCD not running"
            self.logger.error(message)
            return 0, message
        except Exception as except_msg:
            message = "Could not flash LCD ({state}): {e}".format(
                state=state, e=except_msg)
            self.logger.exception(message)
            return 0, message

    def pid_hold(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_hold()
        except KeyError:
            message = "PID not running"
            self.logger.error(message)
            return message
        except Exception as except_msg:
            message = "Could not hold PID: {e}".format(e=except_msg)
            self.logger.exception(message)

    def pid_mod(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_mod()
        except KeyError:
            message = "PID not running"
            self.logger.error(message)
            return message
        except Exception as except_msg:
            message = "Could not modify PID: {e}".format(e=except_msg)
            self.logger.exception(message)

    def pid_pause(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_pause()
        except KeyError:
            message = "PID not running"
            self.logger.error(message)
            return message
        except Exception as except_msg:
            message = "Could not pause PID: {e}".format(e=except_msg)
            self.logger.exception(message)

    def pid_resume(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_resume()
        except KeyError:
            message = "PID not running"
            self.logger.error(message)
            return message
        except Exception as except_msg:
            message = "Could not resume PID: {e}".format(e=except_msg)
            self.logger.exception(message)

    def pid_get(self, pid_id, setting):
        try:
            if setting == 'setpoint':
                return self.controller['PID'][pid_id].get_setpoint()
            elif setting == 'setpoint_band':
                return self.controller['PID'][pid_id].get_setpoint_band()
            elif setting == 'error':
                return self.controller['PID'][pid_id].get_error()
            elif setting == 'integrator':
                return self.controller['PID'][pid_id].get_integrator()
            elif setting == 'derivator':
                return self.controller['PID'][pid_id].get_derivator()
            elif setting == 'kp':
                return self.controller['PID'][pid_id].get_kp()
            elif setting == 'ki':
                return self.controller['PID'][pid_id].get_ki()
            elif setting == 'kd':
                return self.controller['PID'][pid_id].get_kd()
        except Exception as except_msg:
            message = "Could not set PID {opt}: {e}".format(
                opt=setting, e=except_msg)
            self.logger.exception(message)

    def pid_set(self, pid_id, setting, value):
        try:
            if setting == 'setpoint':
                return self.controller['PID'][pid_id].set_setpoint(value)
            elif setting == 'method':
                return self.controller['PID'][pid_id].set_method(value)
            elif setting == 'integrator':
                return self.controller['PID'][pid_id].set_integrator(value)
            elif setting == 'derivator':
                return self.controller['PID'][pid_id].set_derivator(value)
            elif setting == 'kp':
                return self.controller['PID'][pid_id].set_kp(value)
            elif setting == 'ki':
                return self.controller['PID'][pid_id].set_ki(value)
            elif setting == 'kd':
                return self.controller['PID'][pid_id].set_kd(value)
        except Exception as except_msg:
            message = "Could not set PID {opt}: {e}".format(
                opt=setting, e=except_msg)
            self.logger.exception(message)

    def refresh_daemon_camera_settings(self):
        try:
            self.logger.debug("Refreshing camera settings")
            self.camera = db_retrieve_table_daemon(
                Camera, entry='all')
        except Exception as except_msg:
            self.camera = []
            message = "Could not read camera table:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def refresh_daemon_conditional_settings(self, unique_id):
        try:
            return self.controller['Conditional'][unique_id].refresh_settings()
        except Exception as except_msg:
            message = "Could not refresh conditional settings: {e}".format(
                e=except_msg)
            self.logger.exception(message)

    def refresh_daemon_misc_settings(self):
        old_time = self.output_usage_report_next_gen
        self.output_usage_report_next_gen = next_schedule(
            self.output_usage_report_span,
            self.output_usage_report_day,
            self.output_usage_report_hour)
        try:
            self.logger.debug("Refreshing misc settings")
            misc = db_retrieve_table_daemon(Misc, entry='first')
            self.opt_out_statistics = misc.stats_opt_out
            self.enable_upgrade_check = misc.enable_upgrade_check
            self.output_usage_report_gen = misc.output_usage_report_gen
            self.output_usage_report_span = misc.output_usage_report_span
            self.output_usage_report_day = misc.output_usage_report_day
            self.output_usage_report_hour = misc.output_usage_report_hour
            if (self.output_usage_report_gen and
                    old_time != self.output_usage_report_next_gen):
                str_next_report = time.strftime(
                    '%c', time.localtime(self.output_usage_report_next_gen))
                self.logger.debug(
                    "Generating next output usage report {time_date}".format(
                        time_date=str_next_report))
        except Exception as except_msg:
            message = "Could not refresh misc settings: {e}".format(
                e=except_msg)
            self.logger.exception(message)

    def refresh_daemon_trigger_settings(self, unique_id):
        try:
            return self.controller['Trigger'][unique_id].refresh_settings()
        except Exception as except_msg:
            message = "Could not refresh trigger settings: {e}".format(
                e=except_msg)
            self.logger.exception(message)

    def output_duty_cycle(self, output_id, duty_cycle, trigger_conditionals=True):
        """
        Set the output duty cycle

        :param output_id: Unique ID for output
        :param duty_cycle: pwm duty cycle, in percent
        :param trigger_conditionals: allow triggers to respond to a duty cycle change
        :return:
        """
        try:
            return self.controller['Output'].output_duty_cycle(
                output_id, duty_cycle, trigger_conditionals)
        except Exception as except_msg:
            message = "Could set output duty cycle: {e}".format(e=except_msg)
            self.logger.exception(message)
            return 1, message

    def output_off(self, output_id, trigger_conditionals=True):
        """
        Turn output off using default output controller

        :param output_id: Unique ID for output
        :type output_id: str
        :param trigger_conditionals: Whether to trigger output conditionals or not
        :type trigger_conditionals: bool
        """
        try:
            return self.controller['Output'].output_on_off(
                output_id,
                'off',
                trigger_conditionals=trigger_conditionals)
        except Exception as except_msg:
            message = "Could not turn output off: {e}".format(e=except_msg)
            self.logger.exception(message)
            return 1, message

    def output_on(self, output_id, amount=0.0, min_off=0.0,
                  duty_cycle=0.0, trigger_conditionals=True):
        """
        Turn output on using default output controller

        :param output_id: Unique ID for output
        :type output_id: str
        :param amount: How long to turn the output on or how much volume to dispense
        :type amount: float
        :param min_off: Don't turn on if not off for at least this duration (0 = disabled)
        :type min_off: float
        :param duty_cycle: PWM duty cycle % (0-100)
        :type duty_cycle: float
        :param trigger_conditionals: bool
        :type trigger_conditionals: Indicate whether to trigger conditional statements
        """
        try:
            if self.controller['Output'] is None:
                self.logger.error("Could not find Output Controller")
                return "Error"
            else:
                return self.controller['Output'].output_on_off(
                    output_id,
                    'on',
                    amount=amount,
                    min_off=min_off,
                    duty_cycle=duty_cycle,
                    trigger_conditionals=trigger_conditionals)
        except Exception as except_msg:
            message = "Could not turn output on: {e}".format(e=except_msg)
            self.logger.exception(message)
            return 1, message

    def output_setup(self, action, output_id):
        """
        Setup output in running output controller

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param action: What action to perform on a specific output ID
        :type action: str
        :param output_id: Unique ID for output
        :type output_id: str
        """
        try:
            return self.controller['Output'].output_setup(action, output_id)
        except Exception as except_msg:
            message = "Could not set up output: {e}".format(e=except_msg)
            self.logger.exception(message)

    def output_state(self, output_id):
        """
        Return the output state, whether "on" or "off"

        :param output_id: Unique ID for output
        :type output_id: str
        """
        try:
            return self.controller['Output'].output_state(output_id)
        except Exception as except_msg:
            message = "Could not query output state: {e}".format(e=except_msg)
            self.logger.exception(message)

    def output_states_all(self):
        """
        Return all output states, whether "on" or "off"
        """
        try:
            return self.controller['Output'].output_states_all()
        except Exception as except_msg:
            message = "Could not query output state: {e}".format(e=except_msg)
            self.logger.exception(message)

    def startup_stats(self):
        """Ensure existence of statistics file and save daemon startup time"""
        try:
            # if statistics file doesn't exist, create it
            if not os.path.isfile(STATS_CSV):
                self.logger.debug(
                    "Statistics file doesn't exist, creating {file}".format(
                        file=STATS_CSV))
                recreate_stat_file()
            add_update_csv(
                STATS_CSV, 'daemon_startup_seconds', self.daemon_startup_time)
        except Exception as msg:
            self.logger.exception(
                "Statistics initialization Error: {e}".format(e=msg))

    def start_all_controllers(self, debug):
        """
        Start all activated controllers

        See the files named controller_[name].py for details of what each
        controller does.
        """
        try:
            # Obtain database configuration options
            db_tables = {
                'Conditional': db_retrieve_table_daemon(Conditional, entry='all'),
                'Input': db_retrieve_table_daemon(Input, entry='all'),
                'LCD': db_retrieve_table_daemon(LCD, entry='all'),
                'Math': db_retrieve_table_daemon(Math, entry='all'),
                'PID': db_retrieve_table_daemon(PID, entry='all'),
                'Trigger': db_retrieve_table_daemon(Trigger, entry='all'),
                'Custom': db_retrieve_table_daemon(CustomController, entry='all')
            }

            self.logger.debug("Starting Output Controller")
            ready = threading.Event()
            self.controller['Output'] = OutputController(ready, debug)
            self.controller['Output'].daemon = True
            self.controller['Output'].start()
            ready.wait()  # wait for thread to return ready

            # Ensure Output controller has started before continuing
            time.sleep(0.5)
            output_controller_timout = time.time() + 60
            while not self.controller['Output'].is_running():
                if time.time() > output_controller_timout:
                    self.logger.error("Output Controller timed out")
                    break
                time.sleep(0.1)
            self.logger.debug("Output Controller fully started")

            for each_controller in self.cont_types:
                self.logger.debug(
                    "Starting all activated {type} controllers".format(
                        type=each_controller))
                for each_entry in db_tables[each_controller]:
                    if each_entry.is_activated:
                        self.controller_activate(each_entry.unique_id)
                self.logger.info(
                    "All activated {type} controllers started".format(
                        type=each_controller))

            time.sleep(0.5)

        except Exception as except_msg:
            message = "Could not start all controllers:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def stop_all_controllers(self):
        """Stop all running controllers"""
        controller_running = {}

        # Reverse the list to shut down each controller in the
        # reverse order they were started in
        for each_controller in list(reversed(self.cont_types)):
            controller_running[each_controller] = []
            for cont_id in self.controller[each_controller]:
                try:
                    if self.controller[each_controller][cont_id].is_running():
                        self.controller[each_controller][cont_id].stop_controller()
                        controller_running[each_controller].append(cont_id)
                except Exception as err:
                    self.logger.info(
                        "{type} controller {id} thread had an issue "
                        "stopping: {err}".format(
                            type=each_controller, id=cont_id, err=err))

        for each_controller in list(reversed(self.cont_types)):
            for cont_id in controller_running[each_controller]:
                try:
                    self.controller[each_controller][cont_id].join()
                except Exception as err:
                    self.logger.info(
                        "{type} controller {id} thread had an issue being "
                        "joined: {err}".format(
                            type=each_controller, id=cont_id, err=err))
            self.logger.info(
                "All {type} controllers stopped".format(type=each_controller))

        try:
            self.controller['Output'].stop_controller()
            self.controller['Output'].join(15)  # Give each thread 15 seconds to stop
        except Exception as err:
            self.logger.info(
                "Output controller had an issue stopping: {err}".format(
                    err=err))

    def send_infrared_code_broadcast(self, code):
        """Broadcast IR code to all active IR Triggers (thread for speed)"""
        for each_trigger_id in self.controller['Trigger']:
            if self.controller['Trigger'][each_trigger_id].trigger_type == 'trigger_infrared_remote_input':
                broadcast_ir = threading.Thread(
                    target=self.controller['Trigger'][each_trigger_id].receive_infrared_code_broadcast,
                    args=(code,))
                broadcast_ir.start()

    def trigger_action(self, action_id, message='', single_action=False, debug=False):
        try:
            return trigger_action(
                action_id,
                message=message,
                single_action=single_action,
                debug=debug)
        except Exception as except_msg:
            message = "Could not trigger Conditional Actions:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def trigger_all_actions(self, function_id, message='', debug=False):
        try:
            return trigger_function_actions(
                function_id,
                message=message,
                debug=debug)
        except Exception as except_msg:
            message = "Could not trigger Conditional Actions:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def terminate_daemon(self):
        """Instruct the daemon to shut down"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.logger.info("Received command to terminate daemon")
        self.daemon_run = False
        while not self.terminated:
            time.sleep(0.1)
        return 1

    #
    # Timed functions
    #

    def log_ram_usage(self):
        try:
            ram_mb = resource.getrusage(
                resource.RUSAGE_SELF).ru_maxrss / float(1000)
            self.logger.info("{ram:.2f} MB RAM in use".format(ram=ram_mb))
        except Exception:
            self.logger.exception("Free Ram ERROR")

    def check_mycodo_upgrade_exists(self, now):
        """Check for any new Mycodo releases on github"""
        try:
            mycodo_releases = MycodoRelease()
            (upgrade_exists,
             _, _, _, errors) = mycodo_releases.github_upgrade_exists()

            if errors:
                for each_error in errors:
                    self.logger.debug(each_error)

            if upgrade_exists:
                upgrade_available = True
                if now > self.timer_upgrade_message:
                    # Only display message in log every 10 days
                    self.timer_upgrade_message += 864000
                    self.logger.info(
                        "A new version of Mycodo is available. Upgrade "
                        "through the web interface under Config -> Upgrade. "
                        "This message will repeat every 10 days unless "
                        "Mycodo is upgraded or upgrade checks are disabled.")
            else:
                upgrade_available = False

            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_misc = new_session.query(Misc).first()
                if mod_misc.mycodo_upgrade_available != upgrade_available:
                    mod_misc.mycodo_upgrade_available = upgrade_available
                    new_session.commit()
        except Exception:
            self.logger.exception("Mycodo Upgrade Check ERROR")

    def check_all_timelapses(self, now):
        try:
            if self.camera:
                for each_camera in self.camera:
                    self.timelapse_check(each_camera, now)
        except Exception:
            self.logger.exception("Timelapse ERROR")

    def timelapse_check(self, camera, now):
        """ If time-lapses are active, take photo at predefined periods """
        try:
            if (camera.timelapse_started and
                    now > camera.timelapse_end_time):
                with session_scope(MYCODO_DB_PATH) as new_session:
                    mod_camera = new_session.query(Camera).filter(
                        Camera.unique_id == camera.unique_id).first()
                    mod_camera.timelapse_started = False
                    mod_camera.timelapse_paused = False
                    mod_camera.timelapse_start_time = None
                    mod_camera.timelapse_end_time = None
                    mod_camera.timelapse_interval = None
                    mod_camera.timelapse_next_capture = None
                    mod_camera.timelapse_capture_number = None
                    new_session.commit()
                self.refresh_daemon_camera_settings()
                self.logger.debug(
                    "Camera {id}: End of time-lapse.".format(id=camera.id))
            elif ((camera.timelapse_started and not camera.timelapse_paused) and
                    now > camera.timelapse_next_capture):
                # Ensure next capture is greater than now (in case of power failure/reboot)
                next_capture = camera.timelapse_next_capture
                capture_number = camera.timelapse_capture_number
                while now > next_capture:
                    # Update last capture and image number to latest before capture
                    next_capture += camera.timelapse_interval
                    capture_number += 1
                with session_scope(MYCODO_DB_PATH) as new_session:
                    mod_camera = new_session.query(Camera).filter(
                        Camera.unique_id == camera.unique_id).first()
                    mod_camera.timelapse_next_capture = next_capture
                    mod_camera.timelapse_capture_number = capture_number
                    new_session.commit()
                self.refresh_daemon_camera_settings()
                self.logger.debug(
                    "Camera {id}: Capturing time-lapse image".format(id=camera.id))
                # Capture image
                camera_record('timelapse', camera.unique_id)
        except Exception as except_msg:
            message = "Could not execute timelapse:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def send_stats(self):
        """Collect and send statistics"""
        # Check if stats file exists, recreate if not
        try:
            return_stat_file_dict(STATS_CSV)
        except Exception as except_msg:
            self.logger.exception(
                "Error reading stats file: {err}".format(
                    err=except_msg))
            try:
                os.remove(STATS_CSV)
            except OSError:
                pass
            recreate_stat_file()

        # Send stats
        try:
            send_anonymous_stats(self.start_time, self.log_level_debug)
        except Exception as except_msg:
            self.logger.exception(
                "Could not send statistics: {err}".format(
                    err=except_msg))


@expose
class PyroServer(object):
    """
    Pyro for communicating between the client and the daemon
    """
    def __init__(self, mycodo):
        self.mycodo = mycodo

    def lcd_reset(self, lcd_id):
        """Resets an LCD"""
        return self.mycodo.lcd_reset(lcd_id)

    def lcd_backlight(self, lcd_id, state):
        """Turns an LCD backlight on or off"""
        return self.mycodo.lcd_backlight(lcd_id, state)

    def lcd_flash(self, lcd_id, state):
        """Starts or stops an LCD from flashing (alarm)"""
        return self.mycodo.lcd_flash(lcd_id, state)

    def get_condition_measurement(self, condition_id):
        return self.mycodo.get_condition_measurement(condition_id)

    def get_condition_measurement_dict(self, condition_id):
        return self.mycodo.get_condition_measurement_dict(condition_id)

    def controller_activate(self, cont_id):
        """Activates a controller"""
        return self.mycodo.controller_activate(cont_id)

    def controller_deactivate(self, cont_id):
        """Deactivates a controller"""
        return self.mycodo.controller_deactivate(cont_id)

    def controller_is_active(self, cont_id):
        """Checks if a controller is active"""
        return self.mycodo.controller_is_active(cont_id)

    def check_daemon(self):
        """Check if all active controllers respond"""
        return self.mycodo.check_daemon()

    def input_force_measurements(self, input_id):
        """Updates all input information"""
        return self.mycodo.input_force_measurements(input_id)

    def input_custom_button(self, input_id, button_id, args_dict):
        """execute input function"""
        return self.mycodo.input_custom_button(input_id, button_id, args_dict)

    def input_atlas_flow_clear_total_volume(self, input_id):
        """Updates all input information"""
        return self.mycodo.input_atlas_flow_clear_total_volume(input_id)

    def pid_hold(self, pid_id):
        """Hold PID Controller operation"""
        return self.mycodo.pid_hold(pid_id)

    def pid_mod(self, pid_id):
        """Set new PID Controller settings"""
        return self.mycodo.pid_mod(pid_id)

    def pid_pause(self, pid_id):
        """Pause PID Controller operation"""
        return self.mycodo.pid_pause(pid_id)

    def pid_resume(self, pid_id):
        """Resume PID controller operation"""
        return self.mycodo.pid_resume(pid_id)

    def pid_get(self, pid_id, setting):
        """Get PID setting"""
        return self.mycodo.pid_get(pid_id, setting)

    def pid_set(self, pid_id, setting, value):
        """Set PID setting"""
        return self.mycodo.pid_set(pid_id, setting, value)

    def refresh_daemon_camera_settings(self, ):
        """Instruct the daemon to refresh the camera settings"""
        return self.mycodo.refresh_daemon_camera_settings()

    def refresh_daemon_conditional_settings(self, unique_id):
        """Instruct the daemon to refresh a conditional's settings"""
        return self.mycodo.refresh_daemon_conditional_settings(unique_id)

    def refresh_daemon_misc_settings(self):
        """Instruct the daemon to refresh the misc settings"""
        return self.mycodo.refresh_daemon_misc_settings()

    def refresh_daemon_trigger_settings(self, unique_id):
        """Instruct the daemon to refresh a conditional's settings"""
        return self.mycodo.refresh_daemon_trigger_settings(unique_id)

    def output_state(self, output_id):
        """Return the output state (not pin but whether output is on or off)"""
        return self.mycodo.output_state(output_id)

    def output_states_all(self):
        """Return all output states"""
        return self.mycodo.output_states_all()

    def output_duty_cycle(self, output_id, duty_cycle, trigger_conditionals=True):
        """Sets the output duty cycle"""
        return self.mycodo.output_duty_cycle(output_id, duty_cycle, trigger_conditionals)

    def output_on(self, output_id, amount=0.0, min_off=0.0,
                  duty_cycle=0.0, trigger_conditionals=True):
        """Turns output on from the client"""
        return self.mycodo.output_on(
            output_id,
            amount=amount,
            min_off=min_off,
            duty_cycle=duty_cycle,
            trigger_conditionals=trigger_conditionals)

    def output_off(self, output_id, trigger_conditionals=True):
        """Turns output off from the client"""
        return self.mycodo.output_off(output_id, trigger_conditionals)

    def output_sec_currently_on(self, output_id):
        """Turns the amount of time a output has already been on"""
        return self.mycodo.controller['Output'].output_sec_currently_on(output_id)

    def output_setup(self, action, output_id):
        """Add, delete, or modify a output in the running output controller"""
        return self.mycodo.output_setup(action, output_id)

    def send_infrared_code_broadcast(self, code):
        """Broadcast infrared code to all IR Triggers"""
        return self.mycodo.send_infrared_code_broadcast(code)

    def trigger_action(self, action_id, message='', single_action=False, debug=False):
        """Trigger action"""
        return self.mycodo.trigger_action(
            action_id,
            message=message,
            single_action=single_action,
            debug=debug)

    def trigger_all_actions(self, function_id, message='', debug=False):
        """Trigger all actions"""
        return self.mycodo.trigger_all_actions(
            function_id, message=message, debug=debug)

    def terminate_daemon(self):
        """Instruct the daemon to shut down"""
        return self.mycodo.terminate_daemon()

    @staticmethod
    def daemon_status():
        """
        Merely indicates if the daemon is running or not, with successful
        response of 'alive'. This will perform checks in the future and
        return a more detailed daemon status.

        TODO: Incorporate controller checks with daemon status
        """
        return 'alive'

    @staticmethod
    def is_in_virtualenv():
        """Returns True if this script is running in a virtualenv"""
        return hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix

    @staticmethod
    def ram_use():
        """Return the amount of ram used by the daemon"""
        return resource.getrusage(
            resource.RUSAGE_SELF).ru_maxrss / float(1000)


class PyroDaemon(threading.Thread):
    """
    Class to run the Pyro5 server thread

    ComServer will handle execution of commands from the web UI or other
    controllers. It allows the client (mycodo_client.py to be executed as non-root
    user) to communicate with the daemon (mycodo_daemon.py running with root privileges).

    """
    def __init__(self, mycodo, debug):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger('mycodo.pyro_daemon')
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)
        self.mycodo = mycodo

    def run(self):
        try:
            self.logger.info("Starting Pyro5 daemon")
            Daemon.serveSimple({
                PyroServer(self.mycodo): 'mycodo.pyro_server',
            }, host="0.0.0.0", port=9090, ns=False)
        except Exception as err:
            self.logger.exception(
                "ERROR: PyroDaemon: {msg}".format(msg=err))


class PyroMonitor(threading.Thread):
    """
    Monitor whether the Pyro5 server (and daemon) is active or not

    """
    def __init__(self, debug):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger('mycodo.pyro_monitor')
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)
        self.timer_sec = 1800

    def run(self):
        try:
            self.logger.info(
                "Starting Pyro5 daemon monitor ({:.0f} min timer)".format(
                    self.timer_sec / 60.0))
            log_timer = time.time() + 1
            while True:
                now = time.time()
                if now > log_timer:
                    while now > log_timer:
                        log_timer += self.timer_sec
                    try:
                        proxy = Proxy(
                            "PYRO:mycodo.pyro_server@127.0.0.1:9090")
                        proxy.check_daemon()
                        self.logger.debug(
                            "Pyro5 daemon monitor: daemon_status() response: "
                            "'{stat}'".format(stat=proxy.daemon_status()))
                    except Exception as err:
                        self.logger.exception(
                            "Pyro5 daemon monitor Exception: {msg}".format(
                                msg=err))
                time.sleep(1)
        except Exception as err:
            self.logger.exception(
                "ERROR: PyroMonitor: {msg}".format(msg=err))


class MycodoDaemon:
    """
    Handle starting the components of the Mycodo Daemon

    """

    def __init__(self, mycodo, debug):
        self.logger = logging.getLogger('mycodo.daemon')
        if not debug:
            self.logger.setLevel(logging.INFO)
        self.debug = debug
        self.mycodo = mycodo

    def start_daemon(self):
        """Start communication and daemon threads"""
        try:
            pd = PyroDaemon(self.mycodo, self.debug)
            pd.daemon = True
            pd.start()

            if self.debug:
                pm = PyroMonitor(self.debug)
                pm.daemon = True
                pm.start()

            self.mycodo.run()  # Start daemon thread that manages controllers
        except Exception:
            self.logger.exception("ERROR Starting Mycodo Daemon")


def parse_args():
    parser = argparse.ArgumentParser(description='Mycodo daemon.')

    parser.add_argument('-d', '--debug', action='store_true',
                        help='Set Log Level to Debug.')

    return parser.parse_args()


if __name__ == '__main__':
    # Check for root privileges
    if not os.geteuid() == 0:
        sys.exit("Script must be executed as root")

    # Check if lock file already exists
    # if os.path.isfile(DAEMON_PID_FILE):
    #     sys.exit(
    #         "Daemon PID file present. Ensure the daemon isn't already "
    #         "running and delete {file}".format(file=DAEMON_PID_FILE))

    # Parse commandline arguments
    args = parse_args()

    # Set up logger
    logger = logging.getLogger('mycodo')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    fh = logging.FileHandler(DAEMON_LOG_FILE, 'a')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    keep_fds = [fh.stream.fileno()]

    debug = False
    misc = db_retrieve_table_daemon(Misc, entry='first')
    if misc:
        debug = misc.daemon_debug_mode
    if args.debug:
        debug = args.debug

    daemon_controller = DaemonController(debug)
    mycodo_daemon = MycodoDaemon(daemon_controller, debug)

    if DOCKER_CONTAINER:
        mycodo_daemon.start_daemon()
    else:
        # Set up daemon and start it
        daemon = Daemonize(app="mycodo_daemon",
                           pid=DAEMON_PID_FILE,
                           action=mycodo_daemon.start_daemon,
                           keep_fds=keep_fds)
        daemon.start()
