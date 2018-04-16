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
import resource
import threading
import time
import timeit

import rpyc
from collections import OrderedDict
from daemonize import Daemonize
from pkg_resources import parse_version
from rpyc.utils.server import ThreadedServer

from mycodo.config import DAEMON_LOG_FILE
from mycodo.config import DAEMON_PID_FILE
from mycodo.config import MYCODO_VERSION
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config import STATS_CSV
from mycodo.config import STATS_INTERVAL
from mycodo.config import UPGRADE_CHECK_INTERVAL
from mycodo.controller_conditional import ConditionalController
from mycodo.controller_input import InputController
from mycodo.controller_lcd import LCDController
from mycodo.controller_math import MathController
from mycodo.controller_output import OutputController
from mycodo.controller_pid import PIDController
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import Math
from mycodo.databases.models import Misc
from mycodo.databases.models import PID
from mycodo.databases.utils import session_scope
from mycodo.devices.camera import camera_record
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.github_release_info import github_releases
from mycodo.utils.statistics import add_update_csv
from mycodo.utils.statistics import recreate_stat_file
from mycodo.utils.statistics import return_stat_file_dict
from mycodo.utils.statistics import send_anonymous_stats
from mycodo.utils.tools import generate_output_usage_report
from mycodo.utils.tools import next_schedule

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


def mycodo_service(mycodo):
    class ComServer(rpyc.Service):
        """
        Class to handle communication between the client (mycodo_client.py) and
        the daemon (mycodo_daemon.py). This also serves as how other controllers
        (e.g. timers) communicate to the output controller.

        """

        @staticmethod
        def exposed_lcd_backlight(lcd_id, state):
            """Turns an LCD backlight on or off"""
            return mycodo.lcd_backlight(lcd_id, state)

        @staticmethod
        def exposed_lcd_flash(lcd_id, state):
            """Starts or stops an LCD from flashing (alarm)"""
            return mycodo.lcd_flash(lcd_id, state)

        @staticmethod
        def exposed_controller_activate(cont_type, cont_id):
            """
            Activates a controller
            May be a Conditional, Input, Math, PID, or LCD controller

            """
            return mycodo.controller_activate(cont_type, cont_id)

        @staticmethod
        def exposed_controller_deactivate(cont_type, cont_id):
            """
            Deactivates a controller
            May be a Conditional, Input, Math, PID, or LCD controller

            """
            return mycodo.controller_deactivate(cont_type, cont_id)

        @staticmethod
        def exposed_check_daemon():
            """
            Check if all active controllers respond

            """
            return mycodo.check_daemon()

        @staticmethod
        def exposed_daemon_status():
            """
            Merely indicates if the daemon is running or not, with successful
            response of 'alive'. This will perform checks in the future and
            return a more detailed daemon status.

            TODO: Incorporate controller checks with daemon status
            """
            return 'alive'

        @staticmethod
        def exposed_is_in_virtualenv():
            """Returns True if this script is running in a virtualenv"""
            if hasattr(sys, 'real_prefix'):
                return True
            return False

        @staticmethod
        def exposed_pid_hold(pid_id):
            """Hold PID Controller operation"""
            return mycodo.pid_hold(pid_id)

        @staticmethod
        def exposed_pid_mod(pid_id):
            """Set new PID Controller settings"""
            return mycodo.pid_mod(pid_id)

        @staticmethod
        def exposed_pid_pause(pid_id):
            """Pause PID Controller operation"""
            return mycodo.pid_pause(pid_id)

        @staticmethod
        def exposed_pid_resume(pid_id):
            """Resume PID controller operation"""
            return mycodo.pid_resume(pid_id)

        @staticmethod
        def exposed_pid_get(pid_id, setting):
            """Get PID setting"""
            return mycodo.pid_get(pid_id, setting)

        @staticmethod
        def exposed_pid_set(pid_id, setting, value):
            """Set PID setting"""
            return mycodo.pid_set(pid_id, setting, value)

        @staticmethod
        def exposed_ram_use():
            """Return the amount of ram used by the daemon"""
            return resource.getrusage(
                resource.RUSAGE_SELF).ru_maxrss / float(1000)

        @staticmethod
        def exposed_refresh_daemon_camera_settings():
            """
            Instruct the daemon to refresh the camera settings
            """
            return mycodo.refresh_daemon_camera_settings()

        @staticmethod
        def exposed_refresh_daemon_misc_settings():
            """
            Instruct the daemon to refresh the misc settings
            """
            return mycodo.refresh_daemon_misc_settings()

        @staticmethod
        def exposed_output_state(output_id):
            """Return the output state (not pin but whether output is on or off"""
            return mycodo.output_state(output_id)

        @staticmethod
        def exposed_output_on(output_id, duration=0.0, min_off=0.0,
                             duty_cycle=0.0, trigger_conditionals=True):
            """Turns output on from the client"""
            return mycodo.output_on(output_id,
                                    duration=duration,
                                    min_off=min_off,
                                    duty_cycle=duty_cycle,
                                    trigger_conditionals=trigger_conditionals)

        @staticmethod
        def exposed_output_off(output_id, trigger_conditionals=True):
            """Turns output off from the client"""
            return mycodo.output_off(output_id, trigger_conditionals)

        @staticmethod
        def exposed_output_sec_currently_on(output_id):
            """Turns the amount of time a output has already been on"""
            return mycodo.controller['Output'].output_sec_currently_on(output_id)

        @staticmethod
        def exposed_output_setup(action, output_id):
            """Add, delete, or modify a output in the running output controller"""
            return mycodo.output_setup(action, output_id)

        @staticmethod
        def exposed_trigger_conditional_actions(
                conditional_id, message='', edge=None, output_state=None,
                on_duration=None, duty_cycle=None):
            """Return the output state (not pin but whether output is on or off"""
            return mycodo.trigger_conditional_actions(
                conditional_id, message, edge=edge, output_state=output_state,
                on_duration=on_duration, duty_cycle=duty_cycle)

        @staticmethod
        def exposed_terminate_daemon():
            """Instruct the daemon to shut down"""
            return mycodo.terminate_daemon()

    return ComServer


class ComThread(threading.Thread):
    """
    Class to run the rpyc server thread

    ComServer will handle execution of commands from the web UI or other
    controllers. It allows the client (mycodo_client.py, excuted as non-root
    user) to communicate with the daemon (mycodo_daemon.py, executed as root).

    """
    def __init__(self, mycodo):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.rpyc")
        self.logger.setLevel(logging.WARNING)
        self.mycodo = mycodo
        self.server = None
        self.rpyc_monitor = None

    def run(self):
        try:
            # Start RPYC server
            service = mycodo_service(self.mycodo)
            self.server = ThreadedServer(service, port=18813, logger=self.logger)
            self.server.start()

            # self.rpyc_monitor = threading.Thread(
            #     target=monitor_rpyc,
            #     args=(self.logger,))
            # self.rpyc_monitor.daemon = True
            # self.rpyc_monitor.start()
        except Exception as err:
            self.logger.exception(
                "ERROR: ComThread: {msg}".format(msg=err))

    def close(self):
        self.server.close()


def monitor_rpyc(logger_rpyc):
    """Monitor whether the RPYC server is active or not"""
    log_timer = time.time() + 1
    while True:
        now = time.time()
        if now > log_timer:
            try:
                c = rpyc.connect('localhost', 18813)
                time.sleep(0.5)
                logger_rpyc.debug(
                    "RPYC communication thread (30-minute timer): "
                    "closed={stat}".format(stat=c.closed))
            except Exception as err:
                logger_rpyc.exception(
                    "RPYC Exception: {msg}".format(msg=err))
            log_timer = log_timer + 1800
        time.sleep(1)


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

    def __init__(self):
        self.logger = logging.getLogger("mycodo.daemon")
        self.logger.info("Mycodo daemon v{ver} starting".format(ver=MYCODO_VERSION))

        self.startup_timer = timeit.default_timer()
        self.daemon_startup_time = None
        self.daemon_run = True
        self.terminated = False

        # Controller object that will store the thread objects for each
        # controller
        self.controller = {
            # May only launch a single thread for this controller
            'Conditional': {},
            'Output': None,
            # May launch multiple threads per each of these controllers
            'Input': {},
            'LCD': {},
            'Math': {},
            'PID': {}
        }

        # Controllers that may launch multiple threads
        # Order matters for starting and shutting down
        self.cont_types = [
            'Input',
            'Math',
            'PID',
            'LCD',
            'Conditional'
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
        self.logger.info("Anonymous statistics {state}".format(state=state))

    def run(self):
        self.start_all_controllers()
        self.daemon_startup_time = timeit.default_timer() - self.startup_timer
        self.logger.info("Mycodo daemon v{ver} started in {time:.3f}"
                         " seconds".format(ver=MYCODO_VERSION,
                                           time=self.daemon_startup_time))
        self.startup_stats()
        try:
            # loop until daemon is instructed to shut down
            while self.daemon_run:
                now = time.time()

                # Log ram usage every 5 days
                if now > self.timer_ram_use:
                    self.timer_ram_use = now + 432000
                    self.log_ram_usage()

                # Capture time-lapse image (if enabled)
                self.check_all_timelapses(now)

                # Generate output usage report (if enabled)
                if (self.output_usage_report_gen and
                        now > self.output_usage_report_next_gen):
                    generate_output_usage_report()
                    self.refresh_daemon_misc_settings()  # Update timer

                # Collect and send anonymous statistics (if enabled)
                if (not self.opt_out_statistics and
                        now > self.timer_stats):
                    self.timer_stats = self.timer_stats + STATS_INTERVAL
                    self.send_stats()

                # Check if running the latest version (if enabled)
                if now > self.timer_upgrade:
                    self.timer_upgrade = self.timer_upgrade + UPGRADE_CHECK_INTERVAL
                    if self.enable_upgrade_check:
                        self.check_mycodo_upgrade_exists(now)

                time.sleep(0.25)
        except Exception as except_msg:
            self.logger.exception("Unexpected error: {msg}".format(
                msg=except_msg))
            raise

        # If the daemon errors or finishes, shut it down
        finally:
            self.logger.debug("Stopping all running controllers")
            self.stop_all_controllers()

        self.logger.info("Mycodo terminated in {:.3f} seconds\n\n".format(
            timeit.default_timer() - self.thread_shutdown_timer))
        self.terminated = True

        # Wait for the client to receive the response before it disconnects
        time.sleep(1)

    def controller_activate(self, cont_type, cont_id):
        """
        Activate currently-inactive controller

        :return: 0 for success, 1 for fail, with success or error message
        :rtype: int, str

        :param cont_type: Which controller type is to be activated?
        :type cont_type: str
        :param cont_id: Unique ID for controller
        :type cont_id: str
        """
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
            else:
                return 1, "'{type}' not a valid controller type.".format(
                    type=cont_type)

            # Check if the controller actually exists
            controller = db_retrieve_table_daemon(controller_manage['type'],
                                                  unique_id=cont_id)
            if controller:
                self.controller[cont_type][cont_id] = controller_manage['function'](
                    ready, cont_id)
                self.controller[cont_type][cont_id].daemon = True
                self.controller[cont_type][cont_id].start()
                ready.wait()  # wait for thread to return ready
                return 0, "{type} controller with ID {id} " \
                    "activated.".format(type=cont_type, id=cont_id)
            else:
                return 1, "{type} controller with ID {id} not found.".format(
                    type=cont_type, id=cont_id)
        except Exception as except_msg:
            message = "Could not activate {type} controller with ID {id}:" \
                      " {err}".format(type=cont_type, id=cont_id,
                                      err=except_msg)
            self.logger.exception(message)
            return 1, message

    def controller_deactivate(self, cont_type, cont_id):
        """
        Deactivate currently-active controller

        :return: 0 for success, 1 for fail, with success or error message
        :rtype: int, str

        :param cont_type: Which controller type is to be activated?
        :type cont_type: str
        :param cont_id: Unique ID for controller
        :type cont_id: str
        """
        try:
            if cont_id in self.controller[cont_type]:
                if self.controller[cont_type][cont_id].is_running():
                    try:
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
                      " {err}".format(type=cont_type, id=cont_id,
                                      err=except_msg)
            self.logger.exception(message)
            return 1, message

    def check_daemon(self):
        try:
            for cond_id in self.controller['Conditional']:
                if not self.controller['Conditional'][cond_id].is_running():
                    return "Error: Conditional ID {}".format(cond_id)
            for lcd_id in self.controller['LCD']:
                if not self.controller['LCD'][lcd_id].is_running():
                    return "Error: LCD ID {}".format(lcd_id)
            for math_id in self.controller['Math']:
                if not self.controller['Math'][math_id].is_running():
                    return "Error: Math ID {}".format(math_id)
            for pid_id in self.controller['PID']:
                if not self.controller['PID'][pid_id].is_running():
                    return "Error: PID ID {}".format(pid_id)
            for input_id in self.controller['Input']:
                if not self.controller['Input'][input_id].is_running():
                    return "Error: Input ID {}".format(input_id)
            if not self.controller['Output'].is_running():
                return "Error: Output controller"
            if not self.controller['Conditional'].is_running():
                return "Error: Conditional controller"
        except Exception as except_msg:
            message = "Could not check running threads:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)
            return "Exception: {msg}".format(msg=except_msg)

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
            message = "Could not flash LCD:" \
                      " {err}".format(err=except_msg)
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
            message = "Cannot stop flashing, LCD not running"
            self.logger.exception(message)
            return 0, message
        except Exception as except_msg:
            message = "Could not flash LCD:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def pid_hold(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_hold()
        except Exception as except_msg:
            message = "Could not hold PID:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def pid_mod(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_mod()
        except Exception as except_msg:
            message = "Could not modify PID:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def pid_pause(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_pause()
        except Exception as except_msg:
            message = "Could not pause PID:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def pid_resume(self, pid_id):
        try:
            return self.controller['PID'][pid_id].pid_resume()
        except Exception as except_msg:
            message = "Could not resume PID:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def pid_get(self, pid_id, setting):
        try:
            if setting == 'setpoint':
                return self.controller['PID'][pid_id].get_setpoint()
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
            message = "Could not set PID {option}:" \
                      " {err}".format(option=setting, err=except_msg)
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
            message = "Could not set PID {option}:" \
                      " {err}".format(option=setting, err=except_msg)
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
            message = "Could not refresh misc settings:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def output_off(self, output_id, trigger_conditionals=True):
        """
        Turn output off using default output controller

        :param output_id: Unique ID for output
        :type output_id: str
        :param trigger_conditionals: Whether to trigger output conditionals or not
        :type trigger_conditionals: bool
        """
        try:
            self.controller['Output'].output_on_off(
                output_id,
                'off',
                trigger_conditionals=trigger_conditionals)
            return "Turned off"
        except Exception as except_msg:
            message = "Could not turn output off:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def output_on(self, output_id, duration=0.0, min_off=0.0,
                 duty_cycle=0.0, trigger_conditionals=True):
        """
        Turn output on using default output controller

        :param output_id: Unique ID for output
        :type output_id: str
        :param duration: How long to turn the output on
        :type duration: float
        :param min_off: Don't turn on if not off for at least this duration (0 = disabled)
        :type min_off: float
        :param duty_cycle: PWM duty cycle (0-100)
        :type duty_cycle: float
        :param trigger_conditionals: bool
        :type trigger_conditionals: Indicate whether to trigger conditional statements
        """
        try:
            self.controller['Output'].output_on_off(
                output_id,
                'on',
                duration=duration,
                min_off=min_off,
                duty_cycle=duty_cycle,
                trigger_conditionals=trigger_conditionals)
            return "Turned on"
        except Exception as except_msg:
            message = "Could not turn output on:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

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
            message = "Could not set up output:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def output_state(self, output_id):
        """
        Return the output state, wither "on" or "off"

        :param output_id: Unique ID for output
        :type output_id: str
        """
        try:
            return self.controller['Output'].output_state(output_id)
        except Exception as except_msg:
            message = "Could not query output state:" \
                      " {err}".format(err=except_msg)
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
            add_update_csv(STATS_CSV, 'daemon_startup_seconds',
                           self.daemon_startup_time)
        except Exception as msg:
            self.logger.exception(
                "Statistics initialization Error: {err}".format(err=msg))

    def start_all_controllers(self):
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
                'Math': db_retrieve_table_daemon(Math, entry='all'),
                'PID': db_retrieve_table_daemon(PID, entry='all'),
                'LCD': db_retrieve_table_daemon(LCD, entry='all')
            }

            self.logger.debug("Starting Output controller")
            self.controller['Output'] = OutputController()
            self.controller['Output'].daemon = True
            self.controller['Output'].start()

            time.sleep(0.5)

            for each_controller in self.cont_types:
                self.logger.debug(
                    "Starting all activated {type} controllers".format(
                        type=each_controller))
                for each_entry in db_tables[each_controller]:
                    if each_entry.is_activated:
                        self.controller_activate(
                            each_controller, each_entry.unique_id)
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

    def trigger_conditional_actions(
            self, conditional_id, message='', edge=None,
            output_state=None, on_duration=None, duty_cycle=None):
        try:
            return self.controller['Conditional'][conditional_id].trigger_conditional_actions(
                message=message, edge=edge,
                output_state=output_state, on_duration=on_duration,
                duty_cycle=duty_cycle)
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
        releases = []
        upgrade_available = False
        try:
            maj_version = int(MYCODO_VERSION.split('.')[0])
            releases = github_releases(maj_version)
        except Exception:
            self.logger.error("Could not determine local mycodo version or "
                              "online release versions. Upgrade checks can "
                              "be disabled in the Mycodo configuration.")

        try:
            if len(releases):
                if parse_version(releases[0]) > parse_version(MYCODO_VERSION):
                    upgrade_available = True
                    if now > self.timer_upgrade_message:
                        # Only display message in log every 10 days
                        self.timer_upgrade_message = time.time() + 864000
                        self.logger.info(
                            "A new version of Mycodo is available. Upgrade "
                            "through the web interface under Config -> Upgrade. "
                            "This message will repeat every 10 days unless "
                            "Mycodo is upgraded or upgrade checks are disabled.")

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
            send_anonymous_stats(self.start_time)
        except Exception as except_msg:
            self.logger.exception(
                "Could not send statistics: {err}".format(
                    err=except_msg))


class MycodoDaemon:
    """
    Handle starting the components of the Mycodo Daemon

    """

    def __init__(self, mycodo):
        self.logger = logging.getLogger("mycodo.daemon")
        self.mycodo = mycodo

    def start_daemon(self):
        """Start communication and daemon threads"""
        try:
            self.logger.info("Starting rpyc server")
            ct = ComThread(self.mycodo)
            ct.daemon = True
            # Start communication thread for receiving commands from mycodo_client.py
            ct.start()
            # Start daemon thread that manages all controllers
            self.mycodo.run()
            # Stop communication thread after daemon has stopped
            ct.close()
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
    if os.path.isfile(DAEMON_PID_FILE):
        sys.exit(
            "Lock file present. Ensure the daemon isn't already running and "
            "delete {file}".format(file=DAEMON_PID_FILE))

    # Parse commandline arguments
    args = parse_args()

    # Set up logger
    logger = logging.getLogger("mycodo")
    fh = logging.FileHandler(DAEMON_LOG_FILE, 'a')

    if args.debug:
        logger.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        fh.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.propagate = False
    logger.addHandler(fh)
    keep_fds = [fh.stream.fileno()]

    daemon_controller = DaemonController()
    mycodo_daemon = MycodoDaemon(daemon_controller)

    # Set up daemon and start it
    daemon = Daemonize(app="mycodo_daemon",
                       pid=DAEMON_PID_FILE,
                       action=mycodo_daemon.start_daemon,
                       keep_fds=keep_fds)
    daemon.start()
