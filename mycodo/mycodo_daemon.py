# -*- coding: utf-8 -*-
#
#  mycodo_daemon.py - Daemon for managing Mycodo controllers, such as sensors,
#                     relays, PID controllers, etc.
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

import os
import sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import argparse
import logging
import resource
import threading
import time
import timeit
import rpyc
# Don't remove the next line. It's required to not crash strptime
# that's used in the controllers. I've tested with and without this line.
from time import strptime  # Fix multithread bug in strptime
from daemonize import Daemonize
from rpyc.utils.server import ThreadedServer

from mycodo.controller_lcd import LCDController
from mycodo.controller_pid import PIDController
from mycodo.controller_output import OutputController
from mycodo.controller_input import InputController
from mycodo.controller_timer import TimerController

from mycodo.databases.models import Camera
from mycodo.databases.models import LCD
from mycodo.databases.models import Misc
from mycodo.databases.models import PID
from mycodo.databases.models import Input
from mycodo.databases.models import Timer

from mycodo.databases.utils import session_scope
from mycodo.devices.camera import camera_record
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.statistics import add_update_csv
from mycodo.utils.statistics import recreate_stat_file
from mycodo.utils.statistics import return_stat_file_dict
from mycodo.utils.statistics import send_anonymous_stats
from mycodo.utils.tools import generate_relay_usage_report
from mycodo.utils.tools import next_schedule

from mycodo.config import DAEMON_LOG_FILE
from mycodo.config import DAEMON_PID_FILE
from mycodo.config import MYCODO_VERSION
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config import STATS_CSV
from mycodo.config import STATS_INTERVAL


MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


def mycodo_service(mycodo):
    class ComServer(rpyc.Service):
        """
        Class to handle communication between the client (mycodo_client.py) and
        the daemon (mycodo_daemon.py). This also serves as how other controllers
        (e.g. timers) communicate to the output controller.

        """

        @staticmethod
        def exposed_flash_lcd(lcd_id, state):
            """Starts or stops an LCD from flashing (alarm)"""
            return mycodo.flash_lcd(lcd_id, state)

        @staticmethod
        def exposed_controller_activate(cont_type, cont_id):
            """
            Activates a controller
            This may be a Input, PID, Timer, or LCD controllar

            """
            return mycodo.controller_activate(
                cont_type, cont_id)

        @staticmethod
        def exposed_controller_deactivate(cont_type, cont_id):
            """
            Deactivates a controller
            This may be a Input, PID, Timer, or LCD controllar

            """
            return mycodo.controller_deactivate(
                cont_type, cont_id)

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
        def exposed_refresh_sensor_conditionals(input_id,
                                                cond_mod):
            """
            Instruct the input controller to refresh the settings of a
            conditional statement
            """
            return mycodo.refresh_sensor_conditionals(input_id,
                                                      cond_mod)

        @staticmethod
        def exposed_relay_sec_currently_on(relay_id):
            """Turns the amount of time a output has already been on"""
            return mycodo.controller['Output'].relay_sec_currently_on(relay_id)

        @staticmethod
        def exposed_relay_setup(action, relay_id):
            """Add, delete, or modify a output in the running output controller"""
            return mycodo.output_setup(action, relay_id)

        @staticmethod
        def exposed_relay_state(relay_id):
            """Return the output state (not pin but whether output is on or off"""
            return mycodo.output_state(relay_id)

        @staticmethod
        def exposed_relay_on(
                relay_id, duration=0.0, min_off=0.0, duty_cycle=0.0):
            """Turns output on from the client"""
            return mycodo.relay_on(relay_id,
                                   duration=duration,
                                   min_off=min_off,
                                   duty_cycle=duty_cycle)

        @staticmethod
        def exposed_relay_off(relay_id, trigger_conditionals=True):
            """Turns output off from the client"""
            return mycodo.relay_off(relay_id, trigger_conditionals)

        @staticmethod
        def exposed_relay_sec_currently_on(relay_id):
            """Turns the amount of time a output has already been on"""
            return mycodo.controller['Output'].relay_sec_currently_on(relay_id)

        @staticmethod
        def exposed_relay_setup(action, relay_id):
            """Add, delete, or modify a output in the running output controller"""
            return mycodo.output_setup(action, relay_id)

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

    def run(self):
        try:
            # TODO: temporary for testing
            rpyc_test_log = threading.Thread(
                target=test_rpyc,
                args=(self.logger,))
            rpyc_test_log.start()

            # TODO: change logging level (default is info for rpyc)
            service = mycodo_service(self.mycodo)
            server = ThreadedServer(service, port=18813, logger=self.logger)
            server.start()
        except Exception as err:
            self.logger.exception(
                "TESTING: ComThread: {msg}".format(msg=err))


def test_rpyc(logger_rpyc):
    running = True
    log_timer = time.time() + 60
    while running:
        now = time.time()
        if now > log_timer:
            try:
                c = rpyc.connect('localhost', 18813)
                time.sleep(0.1)
                logger_rpyc.debug(
                    "TESTING: (30 min timer) rpyc communication thread: "
                    "closed={stat}".format(stat=c.closed))
            except Exception as err:
                logger_rpyc.exception(
                    "TESTING: test_rpyc exception: {msg}".format(msg=err))
            log_timer = log_timer + 1800
        time.sleep(1)


class DaemonController(threading.Thread):
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
        threading.Thread.__init__(self)
        self.logger = logging.getLogger("mycodo.daemon")
        self.logger.info("Mycodo daemon v{ver} starting".format(ver=MYCODO_VERSION))

        self.startup_timer = timeit.default_timer()
        self.daemon_startup_time = None
        self.daemon_run = True
        self.terminated = False
        self.controller = {
            'LCD': {},
            'PID': {},
            'Output': None,
            'Input': {},
            'Timer': {}
        }
        self.thread_shutdown_timer = None
        self.start_time = time.time()
        self.timer_ram_use = time.time()
        self.timer_stats = time.time() + 120

        # Update camera settings
        self.camera = []
        self.refresh_daemon_camera_settings()

        # Update Misc settings
        self.relay_usage_report_gen = None
        self.relay_usage_report_span = None
        self.relay_usage_report_day = None
        self.relay_usage_report_hour = None
        self.relay_usage_report_next_gen = None
        self.opt_out_statistics = None
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

                # Capture time-lapse image
                try:
                    for each_camera in self.camera:
                        self.timelapse_check(each_camera, now)
                except Exception:
                    self.logger.exception("Timelapse ERROR")

                # Generate output usage report
                if (self.relay_usage_report_gen and
                        now > self.relay_usage_report_next_gen):
                    try:
                        generate_relay_usage_report()
                        self.refresh_daemon_misc_settings()
                    except Exception:
                        self.logger.exception("Output Usage Report Generation ERROR")

                # Log ram usage every 24 hours
                if now > self.timer_ram_use:
                    try:
                        self.timer_ram_use = now + 86400
                        ram_mb = resource.getrusage(
                            resource.RUSAGE_SELF).ru_maxrss / float(1000)
                        self.logger.info("{ram:.2f} MB RAM in use".format(ram=ram_mb))
                    except Exception:
                        self.logger.exception("Free Ram ERROR")

                # collect and send anonymous statistics
                if (not self.opt_out_statistics and
                        now > self.timer_stats):
                    try:
                        self.timer_stats = self.timer_stats + STATS_INTERVAL
                        self.send_stats()
                    except Exception:
                        self.logger.exception("Stats ERROR")

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
        time.sleep(0.25)

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
            if cont_type == 'LCD':
                controller_manage['type'] = LCD
                controller_manage['function'] = LCDController
            elif cont_type == 'PID':
                controller_manage['type'] = PID
                controller_manage['function'] = PIDController
            elif cont_type == 'Input':
                controller_manage['type'] = Input
                controller_manage['function'] = InputController
            elif cont_type == 'Timer':
                controller_manage['type'] = Timer
                controller_manage['function'] = TimerController
            else:
                return 1, "'{type}' not a valid controller type.".format(
                    type=cont_type)

            # Check if the controller ID actually exists and start it
            controller = db_retrieve_table_daemon(controller_manage['type'],
                                                  device_id=cont_id)
            if controller:
                self.controller[cont_type][cont_id] = controller_manage['function'](
                    ready, cont_id)
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
            for lcd_id in self.controller['LCD']:
                if not self.controller['LCD'][lcd_id].is_running():
                    return "Error: LCD ID {}".format(lcd_id)
            for pid_id in self.controller['PID']:
                if not self.controller['PID'][pid_id].is_running():
                    return "Error: PID ID {}".format(pid_id)
            for input_id in self.controller['Input']:
                if not self.controller['Input'][input_id].is_running():
                    return "Error: Input ID {}".format(input_id)
            for timer_id in self.controller['Timer']:
                if not self.controller['Timer'][timer_id].is_running():
                    return "Error: Timer ID {}".format(timer_id)
            if not self.controller['Output'].is_running():
                return "Error: Output controller"
        except Exception as except_msg:
            message = "Could not check running threads:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)
            return "Exception: {msg}".format(msg=except_msg)

    def flash_lcd(self, lcd_id, state):
        """
        Begin or end a repeated flashing of an LCD

        :return: success or error message
        :rtype: str

        :param lcd_id: Which LCD controller ID is to be affected?
        :type lcd_id: str
        :param state: Turn flashing on (1) or off (0)
        :type state: int

        """
        try:
            return self.controller['LCD'][lcd_id].flash_lcd(state)
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
        try:
            self.logger.debug("Refreshing misc settings")
            misc = db_retrieve_table_daemon(Misc, entry='first')
            self.opt_out_statistics = misc.stats_opt_out
            self.relay_usage_report_gen = misc.relay_usage_report_gen
            self.relay_usage_report_span = misc.relay_usage_report_span
            self.relay_usage_report_day = misc.relay_usage_report_day
            self.relay_usage_report_hour = misc.relay_usage_report_hour
            old_time = self.relay_usage_report_next_gen
            self.relay_usage_report_next_gen = next_schedule(
                self.relay_usage_report_span,
                self.relay_usage_report_day,
                self.relay_usage_report_hour)
            if (self.relay_usage_report_gen and
                    old_time != self.relay_usage_report_next_gen):
                str_next_report = time.strftime(
                    '%c', time.localtime(self.relay_usage_report_next_gen))
                self.logger.debug(
                    "Generating next output usage report {time_date}".format(
                        time_date=str_next_report))
        except Exception as except_msg:
            message = "Could not refresh misc settings:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def refresh_sensor_conditionals(self, input_id, cond_mod):
        try:
            return self.controller['Input'][input_id].setup_sensor_conditionals(cond_mod)
        except Exception as except_msg:
            message = "Could not refresh input conditionals:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def relay_off(self, relay_id, trigger_conditionals=True):
        """
        Turn output off using default output controller

        :param relay_id: Unique ID for output
        :type relay_id: str
        :param trigger_conditionals: Whether to trigger output conditionals or not
        :type trigger_conditionals: bool
        """
        try:
            self.controller['Output'].output_on_off(
                relay_id,
                'off',
                trigger_conditionals=trigger_conditionals)
            return "Turned off"
        except Exception as except_msg:
            message = "Could not turn output off:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def relay_on(self, relay_id, duration=0.0, min_off=0.0, duty_cycle=0.0):
        """
        Turn output on using default output controller

        :param relay_id: Unique ID for output
        :type relay_id: str
        :param duration: How long to turn the output on
        :type duration: float
        :param min_off: Don't turn on if not off for at least this duration (0 = disabled)
        :type min_off: float
        :param duty_cycle: PWM duty cycle (0-100)
        :type duty_cycle: float
        """
        try:
            self.controller['Output'].output_on_off(
                relay_id,
                'on',
                duration=duration,
                min_off=min_off,
                duty_cycle=duty_cycle)
            return "Turned on"
        except Exception as except_msg:
            message = "Could not turn output on:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def output_setup(self, action, relay_id):
        """
        Setup output in running output controller

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param action: What action to perform on a specific output ID
        :type action: str
        :param relay_id: Unique ID for output
        :type relay_id: str
        """
        try:
            return self.controller['Output'].output_setup(action, relay_id)
        except Exception as except_msg:
            message = "Could not set up output:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def output_state(self, relay_id):
        """
        Return the output state, wither "on" or "off"

        :param relay_id: Unique ID for output
        :type relay_id: str
        """
        try:
            return self.controller['Output'].output_state(relay_id)
        except Exception as except_msg:
            message = "Could not query output state:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def send_stats(self):
        """Collect and send statistics"""
        try:
            stat_dict = return_stat_file_dict(STATS_CSV)
            if float(stat_dict['next_send']) < time.time():
                add_update_csv(STATS_CSV, 'next_send', self.timer_stats)
            else:
                self.timer_stats = float(stat_dict['next_send'])
        except Exception as msg:
            self.logger.exception(
                "Error: Could not read stats file. Regenerating. Message: "
                "{msg}".format(msg=msg))
            try:
                os.remove(STATS_CSV)
            except OSError:
                pass
            recreate_stat_file()
        try:
            send_anonymous_stats(self.start_time)
        except Exception as except_msg:
            self.logger.exception(
                "Error: Could not send statistics: {err}".format(
                    err=except_msg))

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
            lcd = db_retrieve_table_daemon(LCD, entry='all')
            pid = db_retrieve_table_daemon(PID, entry='all')
            input_dev = db_retrieve_table_daemon(Input, entry='all')
            timer = db_retrieve_table_daemon(Timer, entry='all')

            self.logger.debug("Starting output controller")
            self.controller['Output'] = OutputController()
            self.controller['Output'].start()

            self.logger.debug("Starting all activated timer controllers")
            for each_timer in timer:
                if each_timer.is_activated:
                    self.controller_activate('Timer', each_timer.id)
            self.logger.info("All activated timer controllers started")

            self.logger.debug("Starting all activated input controllers")
            for each_input in input_dev:
                if each_input.is_activated:
                    self.controller_activate('Input', each_input.id)
            self.logger.info("All activated input controllers started")

            self.logger.debug("Starting all activated PID controllers")
            for each_pid in pid:
                if each_pid.is_activated:
                    self.controller_activate('PID', each_pid.id)
            self.logger.info("All activated PID controllers started")

            self.logger.debug("Starting all activated LCD controllers")
            for each_lcd in lcd:
                if each_lcd.is_activated:
                    self.controller_activate('LCD', each_lcd.id)
            self.logger.info("All activated LCD controllers started")
        except Exception as except_msg:
            message = "Could not start all controllers:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)

    def stop_all_controllers(self):
        """Stop all running controllers"""
        try:
            lcd_controller_running = []
            pid_controller_running = []
            input_controller_running = []
            timer_controller_running = []

            for lcd_id in self.controller['LCD']:
                if self.controller['LCD'][lcd_id].is_running():
                    self.controller['LCD'][lcd_id].stop_controller()
                    lcd_controller_running.append(lcd_id)

            for pid_id in self.controller['PID']:
                if self.controller['PID'][pid_id].is_running():
                    self.controller['PID'][pid_id].stop_controller(ended_normally=False)
                    pid_controller_running.append(pid_id)

            for input_id in self.controller['Input']:
                if self.controller['Input'][input_id].is_running():
                    self.controller['Input'][input_id].stop_controller()
                    input_controller_running.append(input_id)

            for timer_id in self.controller['Timer']:
                if self.controller['Timer'][timer_id].is_running():
                    self.controller['Timer'][timer_id].stop_controller()
                    timer_controller_running.append(timer_id)

            # Wait for the threads to finish
            for lcd_id in lcd_controller_running:
                self.controller['LCD'][lcd_id].join()
            self.logger.info("All LCD controllers stopped")

            for timer_id in timer_controller_running:
                self.controller['Timer'][timer_id].join()
            self.logger.info("All Timer controllers stopped")

            for input_id in input_controller_running:
                self.controller['Input'][input_id].join()
            self.logger.info("All Input controllers stopped")

            for pid_id in pid_controller_running:
                self.controller['PID'][pid_id].join()
            self.logger.info("All PID controllers stopped")

            self.controller['Output'].stop_controller()
            self.controller['Output'].join()
        except Exception as except_msg:
            message = "Could not stop all controllers:" \
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

    def timelapse_check(self, camera, now):
        """ If time-lapses are active, take photo at predefined periods """
        try:
            if (camera.timelapse_started and
                    now > camera.timelapse_end_time):
                with session_scope(MYCODO_DB_PATH) as new_session:
                    mod_camera = new_session.query(Camera).filter(
                        Camera.id == camera.id).first()
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
                        Camera.id == camera.id).first()
                    mod_camera.timelapse_next_capture = next_capture
                    mod_camera.timelapse_capture_number = capture_number
                    new_session.commit()
                self.refresh_daemon_camera_settings()
                self.logger.debug(
                    "Camera {id}: Capturing time-lapse image".format(id=camera.id))
                # Capture image
                camera_record('timelapse', camera)
        except Exception as except_msg:
            message = "Could not execute timelapse:" \
                      " {err}".format(err=except_msg)
            self.logger.exception(message)


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
            self.mycodo.start()
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
