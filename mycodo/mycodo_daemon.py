#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo_daemon.py - Daemon for managing Mycodo controllers, such as sensors,
#                     relays, PID controllers, etc.
#
#  Copyright (C) 2016  Kyle T. Gabriel
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
import csv
import logging
import resource
import RPi.GPIO as GPIO
import threading
import time
import timeit
import rpyc
# Don't remove the next line. It's required to not crash strptime
# that's used in the controllers. I've tested with and without this line.
from time import strptime  # Fix multithread bug in strptime
from daemonize import Daemonize
from rpyc.utils.server import ThreadedServer

# Classes
from mycodo.controller_lcd import LCDController
from mycodo.controller_pid import PIDController
from mycodo.controller_relay import RelayController
from mycodo.controller_sensor import SensorController
from mycodo.controller_timer import TimerController
from mycodo.databases.mycodo_db.models import (
    Camera,
    LCD,
    Misc,
    PID,
    Sensor,
    Timer
)

# Functions
from mycodo.databases.utils import session_scope
from mycodo.devices.camera import camera_record
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.statistics import (
    add_update_csv,
    recreate_stat_file,
    return_stat_file_dict,
    send_stats
)

# Config
from mycodo.config import (
    DAEMON_LOG_FILE,
    DAEMON_PID_FILE,
    MYCODO_VERSION,
    SQL_DATABASE_MYCODO,
    STATS_CSV,
    STATS_INTERVAL
)

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class ComThread(threading.Thread):
    """
    Class to run the rpyc server thread

    ComServer will handle execution of commands from the web UI or other
    controllers. It allows the client (mycodo_client.py, excuted as non-root
    user) to communicate with the daemon (mycodo_daemon.py, executed as root).

    """
    def run(self):
        server = ThreadedServer(ComServer, port=18813)
        server.start()


class ComServer(rpyc.Service):
    """
    Class to handle communication between the client (mycodo_client.py) and
    the daemon (mycodo_daemon.py). This also serves as how other controllers
    (e.g. timers) communicate to the relay controller.

    """
    @staticmethod
    def exposed_flash_lcd(lcd_id, state):
        """Starts or stops an LCD from flashing (alarm)"""
        return mycodo_daemon.flash_lcd(lcd_id, state)

    @staticmethod
    def exposed_relay_state(relay_id):
        """Return the relay state (not pin but whether relay is on or off"""
        return mycodo_daemon.relay_state(relay_id)

    @staticmethod
    def exposed_relay_on(relay_id, duration, min_off_duration=0.0):
        """Turns relay on from the client"""
        return mycodo_daemon.relay_on(relay_id, duration, min_off_duration)

    @staticmethod
    def exposed_relay_off(relay_id, trigger_conditionals=True):
        """Turns relay off from the client"""
        return mycodo_daemon.relay_off(relay_id, trigger_conditionals)

    @staticmethod
    def exposed_relay_setup(action, relay_id, setup_pin):
        """Add, delete, or modify a relay in the running relay controller"""
        return mycodo_daemon.relay_setup(action, relay_id, setup_pin)

    @staticmethod
    def exposed_activate_controller(cont_type, cont_id):
        """
        Activates a controller
        This may be a Sensor, PID, Timer, or LCD controllar

        """
        return mycodo_daemon.activate_controller(
            cont_type, cont_id)

    @staticmethod
    def exposed_deactivate_controller(cont_type, cont_id):
        """
        Deactivates a controller
        This may be a Sensor, PID, Timer, or LCD controllar

        """
        return mycodo_daemon.deactivate_controller(
            cont_type, cont_id)

    @staticmethod
    def exposed_refresh_sensor_conditionals(sensor_id,
                                            cond_mod, cond_id):
        """
        Instruct the sensor controller to refresh the settings of a
        conditionalstatement
        """
        return mycodo_daemon.refresh_sensor_conditionals(sensor_id,
                                                         cond_mod,
                                                         cond_id)

    @staticmethod
    def exposed_daemon_status():
        """
        Merely indicates if the daemon is running or not, with succesful
        response of 'alive'. This will perform checks in the future and return
        a more detailed daemon status.

        TODO: Incorporate controller checks with daemon status
        """
        return 'alive'

    @staticmethod
    def exposed_pid_mod(pid_id):
        """Set new PID Controller settings"""
        return mycodo_daemon.pid_mod(pid_id)

    @staticmethod
    def exposed_pid_hold(pid_id):
        """Hold PID Controller operation"""
        return mycodo_daemon.pid_hold(pid_id)

    @staticmethod
    def exposed_pid_pause(pid_id):
        """Pause PID Controller operation"""
        return mycodo_daemon.pid_pause(pid_id)

    @staticmethod
    def exposed_pid_resume(pid_id):
        """Resume PID controller operation"""
        return mycodo_daemon.pid_resume(pid_id)

    @staticmethod
    def exposed_terminate_daemon():
        """Instruct the daemon to shut down"""
        return mycodo_daemon.terminateDaemon()


class DaemonController(threading.Thread):
    """
    Mycodo daemon

    Read tables containing controller settings from SQLite database.
    Start a thread for each controller.
    Loop until the daemon is instructed to shut down.
    Signal each thread to shut down and wait for each thread to shut down.

    All relay operations (turning on/off) is operated by one relay controller.

    Each connected sensor has its own controller to collect all measurements
    that particular sensor can produce and put then into an influxdb database.

    Each PID controller is associated with only one measurement from one
    sensor controller.

    """

    def __init__(self):
        threading.Thread.__init__(self)

        self.startup_timer = timeit.default_timer()
        self.logger = logger
        self.logger.info("Mycodo daemon v{ver} starting".format(ver=MYCODO_VERSION))
        self.thread_shutdown_timer = None
        self.daemon_run = True
        self.terminated = False
        self.controller = {
            'LCD': {},
            'PID': {},
            'Relay': None,
            'Sensor': {},
            'Timer': {}
        }
        self.timer_ram_use = time.time()
        self.timer_stats = time.time()+120

        misc = db_retrieve_table_daemon(Misc, entry='first')

        self.opt_out_statistics = misc.stats_opt_out
        if self.opt_out_statistics:
            self.logger.info("Anonymous statistics disabled")
        else:
            self.logger.info("Anonymous statistics enabled")

    def run(self):
        self.start_all_controllers()
        self.startup_stats()

        try:
            # loop until daemon is instructed to shut down
            while self.daemon_run:
                now = time.time()

                try:
                    # If time-lapses are active, take photo at predefined periods
                    try:
                        camera = db_retrieve_table_daemon(Camera, entry='all')
                    except Exception:
                        self.logger.error("Could not read camera table.")
                    for each_camera in camera:
                        if (each_camera.timelapse_started and
                                now > each_camera.timelapse_end_time):
                            with session_scope(MYCODO_DB_PATH) as new_session:
                                mod_camera = new_session.query(Camera).filter(
                                    Camera.id == each_camera.id).first()
                                mod_camera.timelapse_started = False
                                mod_camera.timelapse_paused = False
                                mod_camera.timelapse_start_time = None
                                mod_camera.timelapse_end_time = None
                                mod_camera.timelapse_interval = None
                                mod_camera.timelapse_next_capture = None
                                mod_camera.timelapse_capture_number = None
                                new_session.commit()
                        elif ((each_camera.timelapse_started and not each_camera.timelapse_paused) and
                                now > each_camera.timelapse_next_capture):
                            # Ensure next capture is greater than now (in case of power failure/reboot)
                            next_capture = each_camera.timelapse_next_capture
                            capture_number = each_camera.timelapse_capture_number
                            while now > next_capture:
                                # Update last capture and image number to latest before capture
                                next_capture += each_camera.timelapse_interval
                                capture_number += 1
                            with session_scope(MYCODO_DB_PATH) as new_session:
                                mod_camera = new_session.query(Camera).filter(
                                    Camera.id == each_camera.id).first()
                                mod_camera.timelapse_next_capture = next_capture
                                mod_camera.timelapse_capture_number = capture_number
                                new_session.commit()
                            # Capture image
                            camera_record('timelapse', each_camera)
                except Exception:
                    self.logger.exception("Timelapse ERROR")

                # Log ram usage every 24 hours
                if now > self.timer_ram_use:
                    self.timer_ram_use = now+86400
                    ram = resource.getrusage(
                        resource.RUSAGE_SELF).ru_maxrss / float(1000)
                    self.logger.info("{} MB ram in use".format(ram))

                # collect and send anonymous statistics
                if (not self.opt_out_statistics and
                        now > self.timer_stats):
                    self.send_stats()

                time.sleep(0.25)
            GPIO.cleanup()
        except Exception as except_msg:
            self.logger.exception("Unexpected error: {}: {}".format(
                sys.exc_info()[0], except_msg))
            raise

        # If the daemon errors or finishes, shut it down
        finally:
            self.logger.debug("Stopping all running controllers")
            self.stop_all_controllers()

        self.logger.info("Mycodo terminated in {:.3f} seconds".format(
            timeit.default_timer()-self.thread_shutdown_timer))
        self.terminated = True

        # Wait for the client to receive the response before it disconnects
        time.sleep(0.25)

    def activate_controller(self, cont_type, cont_id):
        """
        Activate currently-inactive controller

        :return: 0 for success, 1 for fail, with success or error message
        :rtype: int, str

        :param cont_type: Which controller type is to be activated?
        :type cont_type: str
        :param cont_id: Unique ID for controller
        :type cont_id: str
        """
        if cont_id in self.controller[cont_type]:
            if self.controller[cont_type][cont_id].is_running():
                message = "Cannot activate {type} controller with ID {id}: " \
                          "It's already active.".format(type=cont_type,
                                                        id=cont_id)
                self.logger.warning(message)
                return 1, message
        try:
            controller_manage = {}
            ready = threading.Event()
            if cont_type == 'LCD':
                controller_manage['type'] = LCD
                controller_manage['function'] = LCDController
            elif cont_type == 'PID':
                controller_manage['type'] = PID
                controller_manage['function'] = PIDController
            elif cont_type == 'Sensor':
                controller_manage['type'] = Sensor
                controller_manage['function'] = SensorController
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
            message = "Could not activate {type} controller with ID {id}: " \
                      "{err}".format(type=cont_type, id=cont_id,
                                     err=except_msg)
            self.logger.exception(message)
            return 1, message

    def deactivate_controller(self, cont_type, cont_id):
        """
        Deactivate currently-active controller

        :return: 0 for success, 1 for fail, with success or error message
        :rtype: int, str

        :param cont_type: Which controller type is to be activated?
        :type cont_type: str
        :param cont_id: Unique ID for controller
        :type cont_id: str
        """
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
        if self.controller['LCD'][lcd_id].is_running():
            return self.controller['LCD'][lcd_id].flash_lcd(state)
        else:
            return "Cannot flash, LCD not running"

    def relay_state(self, relay_id):
        """
        Return the relay state, wither "on" or "off"

        :param relay_id: Unique ID for relay
        :type relay_id: str
        """
        return self.controller['Relay'].relay_state(relay_id)

    def relay_on(self, relay_id, duration, min_off_duration=0.0):
        """
        Turn relay on using default relay controller

        :param relay_id: Unique ID for relay
        :type relay_id: str
        :param duration: How long to turn the relay on
        :type duration: float
        :param min_off_duration: Don't turn on if not off for at least this duration (0 = disabled)
        :type min_off_duration: float
        """
        self.controller['Relay'].relay_on_off(
            relay_id,
            'on',
            duration=duration,
            min_off_duration=min_off_duration)
        return "Relay turned on"

    def relay_off(self, relay_id, trigger_conditionals=True):
        """
        Turn relay off using default relay controller

        :param relay_id: Unique ID for relay
        :type relay_id: str
        :param trigger_conditionals: Whether to trigger relay conditionals or not
        :type trigger_conditionals: bool
        """
        self.controller['Relay'].relay_on_off(
            relay_id,
            'off',
            trigger_conditionals=trigger_conditionals)
        return "Relay turned off"

    def relay_setup(self, action, relay_id, setup_pin=False):
        """
        Setup relay in running relay controller

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param action: What action to perform on a specific relay ID
        :type action: str
        :param relay_id: Unique ID for relay
        :type relay_id: str
        :param setup_pin: Whether or not to setup the GPIO pin as output
        :type setup_pin: bool
        """
        return self.controller['Relay'].relay_setup(
            action,
            relay_id,
            setup_pin)

    def pid_mod(self, pid_id):
        return self.controller['PID'][pid_id].pid_mod()

    def pid_hold(self, pid_id):
        return self.controller['PID'][pid_id].pid_hold()

    def pid_pause(self, pid_id):
        return self.controller['PID'][pid_id].pid_pause()

    def pid_resume(self, pid_id):
        return self.controller['PID'][pid_id].pid_resume()

    def refresh_sensor_conditionals(self, sensor_id, cond_mod, cond_id):
        return self.controller['Sensor'][sensor_id].setup_sensor_conditionals(cond_mod, cond_id)

    def send_stats(self):
        """Collect and send statistics"""
        try:
            stat_dict = return_stat_file_dict(STATS_CSV)
            if float(stat_dict['next_send']) < time.time():
                self.timer_stats = self.timer_stats+STATS_INTERVAL
                add_update_csv(STATS_CSV, 'next_send', self.timer_stats)
            else:
                self.timer_stats = float(stat_dict['next_send'])
        except Exception as msg:
            self.logger.exception(
                "Error: Could not read stats file. Regenerating. Error msg: "
                "{msg}".format(msg=msg))
            try:
                os.remove(STATS_CSV)
            except OSError:
                pass
            recreate_stat_file()
        try:
            send_stats()
        except Exception as except_msg:
            self.logger.exception(
                "Error: Could not send statistics: {err}".format(
                    err=except_msg))

    def startup_stats(self):
        """Initial statistics collection and transmssion at startup"""
        try:
            # if statistics file doesn't exist, create it
            if not os.path.isfile(STATS_CSV):
                self.logger.debug(
                    "Statistics file doesn't exist, creating {file}".format(
                        file=STATS_CSV))
                recreate_stat_file()

            daemon_startup_time = timeit.default_timer()-self.startup_timer
            self.logger.info("Mycodo daemon v{ver} started in {time:.3f}"
                             " seconds".format(ver=MYCODO_VERSION,
                                               time=daemon_startup_time))
            add_update_csv(STATS_CSV, 'daemon_startup_seconds',
                           daemon_startup_time)
        except Exception as msg:
            self.logger.exception(
                "Statistics initialization Error: {err}".format(err=msg))

    def start_all_controllers(self):
        """
        Start all activated controllers

        See the files named controller_[name].py for details of what each
        controller does.
        """
        # Obtain database configuration options
        lcd = db_retrieve_table_daemon(LCD, entry='all')
        pid = db_retrieve_table_daemon(PID, entry='all')
        sensor = db_retrieve_table_daemon(Sensor, entry='all')
        timer = db_retrieve_table_daemon(Timer, entry='all')

        self.logger.debug("Starting relay controller")
        self.controller['Relay'] = RelayController()
        self.controller['Relay'].start()

        self.logger.debug("Starting all activated timer controllers")
        for each_timer in timer:
            if each_timer.is_activated:
                self.activate_controller('Timer', each_timer.id)
        self.logger.info("All activated timer controllers started")

        self.logger.debug("Starting all activated sensor controllers")
        for each_sensor in sensor:
            if each_sensor.is_activated:
                self.activate_controller('Sensor', each_sensor.id)
        self.logger.info("All activated sensor controllers started")

        self.logger.debug("Starting all activated PID controllers")
        for each_pid in pid:
            if each_pid.is_activated:
                self.activate_controller('PID', each_pid.id)
        self.logger.info("All activated PID controllers started")

        self.logger.debug("Starting all activated LCD controllers")
        for each_lcd in lcd:
            if each_lcd.is_activated:
                self.activate_controller('LCD', each_lcd.id)
        self.logger.info("All activated LCD controllers started")

    def stop_all_controllers(self):
        """Stop all running controllers"""
        lcd_controller_running = []
        pid_controller_running = []
        sensor_controller_running = []
        timer_controller_running = []

        for lcd_id in self.controller['LCD']:
            if self.controller['LCD'][lcd_id].is_running():
                self.controller['LCD'][lcd_id].stop_controller()
                lcd_controller_running.append(lcd_id)

        for pid_id in self.controller['PID']:
            if self.controller['PID'][pid_id].is_running():
                self.controller['PID'][pid_id].stop_controller()
                pid_controller_running.append(pid_id)

        for sensor_id in self.controller['Sensor']:
            if self.controller['Sensor'][sensor_id].is_running():
                self.controller['Sensor'][sensor_id].stop_controller()
                sensor_controller_running.append(sensor_id)

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

        for sensor_id in sensor_controller_running:
            self.controller['Sensor'][sensor_id].join()
        self.logger.info("All Sensor controllers stopped")

        for pid_id in pid_controller_running:
            self.controller['PID'][pid_id].join()
        self.logger.info("All PID controllers stopped")

        self.controller['Relay'].stop_controller()
        self.controller['Relay'].join()

    def terminateDaemon(self):
        """Instruct the daemon to shut down"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.logger.info("Received command to terminate daemon")
        self.daemon_run = False
        while not self.terminated:
            time.sleep(0.1)
        return 1


def start_daemon():
    """Start the daemon"""
    ct = ComThread()
    ct.daemon = True
    # Start communication thread for receiving commands from mycodo_client.py
    ct.start()
    # Start daemon thread that manages all controllers
    mycodo_daemon.start()


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

    global mycodo_daemon
    mycodo_daemon = DaemonController()

    # Set up daemon and start it
    daemon = Daemonize(app="Mycodod",
                       pid=DAEMON_PID_FILE,
                       action=start_daemon,
                       keep_fds=keep_fds)
    daemon.start()
