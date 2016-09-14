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

import argparse
import csv
import logging
import resource
import os
import pwd
import sys
import threading
import time
import timeit
import rpyc
from collections import OrderedDict
from daemonize import Daemonize
from rpyc.utils.server import ThreadedServer

from utils.camera import camera_record
from utils.statistics import add_update_csv
from utils.statistics import recreate_stat_file
from utils.statistics import return_stat_file_dict
from utils.statistics import send_stats

from config import DAEMON_PID_FILE
from config import DAEMON_LOG_FILE
from config import FILE_TIMELAPSE_PARAM
from config import ID_FILE
from config import INSTALL_DIRECTORY
from config import LOCK_FILE_TIMELAPSE
from config import MYCODO_VERSION
from config import SQL_DATABASE_MYCODO
from config import SQL_DATABASE_USER
from config import STATS_INTERVAL
from config import STATS_CSV
from config import STATS_HOST
from config import STATS_PORT
from config import STATS_USER
from config import STATS_PASSWORD
from config import STATS_DATABASE

from controller_lcd import LCDController
from controller_log import LogController
from controller_pid import PIDController
from controller_relay import RelayController
from controller_sensor import SensorController
from controller_timer import TimerController

from databases.mycodo_db.models import LCD
from databases.mycodo_db.models import Log
from databases.mycodo_db.models import Method
from databases.mycodo_db.models import Misc
from databases.mycodo_db.models import PID
from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import Sensor
from databases.mycodo_db.models import Timer
from databases.users_db.models import Users
from databases.utils import session_scope


MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
USER_DB_PATH = 'sqlite:///' + SQL_DATABASE_USER


class ComThread(threading.Thread):
    """
    Class to run the rpyc server thread

    ComServer will handle execution of commands from the web UI or other
    controllers.

    """
    def run(self):
        server = ThreadedServer(ComServer, port=18813)
        server.start()


class ComServer(rpyc.Service):
    """
    Class to handle communication between the client (mycodo_client.py) and
    the daemon (mycodo_daemon.py). This also serves as how other controllers
    (e.g. timers) communicate to the relay controller .

    """

    def exposed_flash_lcd(self, lcd_id, state):
        """Starts or stops an LCD from flashing (alarm)"""
        return mycodo_daemon.flash_lcd(lcd_id, state)

    def exposed_relay_on(self, relay_id, duration):
        """Turns relay on from the client"""
        return mycodo_daemon.relay_on(relay_id, duration)

    def exposed_relay_off(self, relay_id):
        """Turns relay off from the client"""
        return mycodo_daemon.relay_off(relay_id)

    def exposed_add_relay(self, relay_id):
        """Add relay to running relay controller"""
        return mycodo_daemon.add_relay(relay_id)

    def exposed_mod_relay(self, relay_id):
        """Instruct the running relay controller to update the relay settings"""
        return mycodo_daemon.mod_relay(relay_id)

    def exposed_del_relay(self, relay_id):
        """Delete relay to running relay controller"""
        return mycodo_daemon.del_relay(relay_id)

    def exposed_activate_controller(self, cont_type, cont_id):
        """Activates controller"""
        return mycodo_daemon.activateController(
            cont_type, cont_id)

    def exposed_deactivate_controller(self, cont_type, cont_id):
        """Deactivates controller"""
        return mycodo_daemon.deactivateController(
            cont_type, cont_id)

    def exposed_refresh_sensor_conditionals(self, sensor_id, cond_mod, cond_id):
        """Deactivates controller"""
        return mycodo_daemon.refresh_sensor_conditionals(sensor_id, cond_mod, cond_id)

    def exposed_daemon_status(self):
        """Indicates if the daemon is alive ro not"""
        return 'alive'

    def exposed_terminate_daemon(self):
        """Instructs daemon to shut down"""
        return mycodo_daemon.terminateDaemon()


class DaemonController(threading.Thread):
    """
    Class for running the Mycodo daemon

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

    def __init__(self, new_logger):
        threading.Thread.__init__(self)

        self.startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = None
        self.logger = new_logger
        self.daemon_run = True
        self.terminated = False
        self.controller = {}
        self.controller['LCD'] = {}
        self.controller['Log'] = {}
        self.controller['PID'] = {}
        self.controller['Relay'] = None
        self.controller['Sensor'] = {}
        self.controller['Timer'] = {}
        self.opt_out_statistics = False
        self.timer_stats = time.time()+120
        self.timer_ram_use = time.time()


    def run(self):
        self.start_all_controllers()
        self.startup_stats()
        try:
            # loop until daemon is instructed to shut down
            while self.daemon_run:
                now = time.time()

                # If timelapse active, take photo at predefined periods
                if (os.path.isfile(FILE_TIMELAPSE_PARAM) and
                        os.path.isfile(LOCK_FILE_TIMELAPSE)):
                    # Read user-defined timelapse parameters
                    with open(FILE_TIMELAPSE_PARAM, mode='r') as infile:
                        reader = csv.reader(infile)
                        dict_timelapse_param = OrderedDict((row[0], row[1]) for row in reader)
                    if now > float(dict_timelapse_param['end_time']):
                        try:
                            os.remove(FILE_TIMELAPSE_PARAM)
                            os.remove(LOCK_FILE_TIMELAPSE)
                        except:
                            pass
                    elif now > float(dict_timelapse_param['next_capture']):
                        # Ensure next capture is greater than now (in case of power failure/reboot)
                        next_capture = float(dict_timelapse_param['next_capture'])
                        capture_number = int(dict_timelapse_param['capture_number'])
                        while next_capture < now:
                            # Update last capture and image number to latest before capture
                            next_capture += float(dict_timelapse_param['interval'])
                            capture_number += 1
                        add_update_csv(logger,
                                                   FILE_TIMELAPSE_PARAM,
                                                   'next_capture',
                                                   next_capture)
                        add_update_csv(logger,
                                                   FILE_TIMELAPSE_PARAM,
                                                   'capture_number',
                                                   capture_number)
                        # Capture image
                        camera_record(
                            INSTALL_DIRECTORY,
                            'timelapse',
                            start_time=dict_timelapse_param['start_time'],
                            capture_number=capture_number)

                elif (os.path.isfile(FILE_TIMELAPSE_PARAM) or
                        os.path.isfile(LOCK_FILE_TIMELAPSE)):
                    try:
                        os.remove(FILE_TIMELAPSE_PARAM)
                        os.remove(LOCK_FILE_TIMELAPSE)
                    except:
                        pass


                # Log ram usage every 24 hours
                if now > self.timer_ram_use:
                    self.timer_ram_use = now+86400
                    ram = resource.getrusage(
                        resource.RUSAGE_SELF).ru_maxrss / float(1000)
                    self.logger.info("[Daemon] {} MB ram in use".format(ram))

                # collect and send anonymous statistics
                if (not self.opt_out_statistics and
                        now > self.timer_stats):
                    self.send_stats()

                time.sleep(0.25)
        except Exception as except_msg:
            self.logger.exception("Unexpected error: {}: {}".format(
                sys.exc_info()[0], except_msg))
            raise
        # if it errors or finishes, shut it down
        finally:
            self.logger.debug("[Daemon] Stopping all running controllers")
            self.stop_all_controllers()

        self.logger.info("[Daemon] Mycodo terminated in {} seconds".format(
            timeit.default_timer()-self.thread_shutdown_timer))
        self.terminated = True
        # wait so the client doesn't disconnectd before it receives response
        time.sleep(0.25)


    def activateController(self, cont_type, cont_id):
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
            if self.controller[cont_type][cont_id].isRunning():
                self.logger.warning("[Daemon] Cannot activate {} controller "
                                    "with ID {}, it's already "
                                    "active.".format(cont_type,
                                                     cont_id))
                return 1, "Cannot activate {} controller with ID {}: "\
                    "Already active.".format(cont_type,
                                             cont_id)
        try:
            controller_manage = {}
            ready = threading.Event()
            if cont_type == 'LCD':
                controller_manage['type'] = LCD
                controller_manage['function'] = LCDController
            elif cont_type == 'Log':
                controller_manage['type'] = Log
                controller_manage['function'] = LogController
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
                return 1, "{} controller with ID {} not found.".format(
                    cont_type, cont_id)

            # Check if the controller ID actually exists and start it
            with session_scope(MYCODO_DB_PATH) as new_session:
                if new_session.query(controller_manage['type']).filter(
                        controller_manage['type'].id == cont_id).first():
                    self.controller[cont_type][cont_id] = controller_manage['function'](
                        ready, self.logger, cont_id)
                    self.controller[cont_type][cont_id].start()
                    ready.wait()  # wait for thread to return ready
                    return 0, "{} controller with ID {} activated.".format(
                        cont_type, cont_id)
                else:
                    return 1, "{} controller with ID {} not found.".format(
                        cont_type, cont_id)
        except Exception as except_msg:
            self.logger.exception("[Daemon] Could not activate {} controller "
                                  "with ID {}: {}".format(cont_type, cont_id,
                                                          except_msg))
            return 1, "Could not activate {} controller with ID "\
                "{}: {}".format(cont_type, cont_id, except_msg)


    def deactivateController(self, cont_type, cont_id):
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
            if self.controller[cont_type][cont_id].isRunning():
                try:
                    self.controller[cont_type][cont_id].stopController()
                    self.controller[cont_type][cont_id].join()
                    return 0, "{} controller with ID {} "\
                        "deactivated.".format(cont_type, cont_id)
                except Exception as except_msg:
                    self.logger.exception(
                        "[Daemon] Could not deactivate {} controller with ID "
                        "{}: {}".format(cont_type, cont_id, except_msg))
                    return 1, "Could not deactivate {} controller with ID {}:"\
                        " {}".format(cont_type, cont_id, except_msg)
            else:
                self.logger.warning("[Daemon] Cannot deactivate {} controller "
                                    "with ID {}, it's not active.".format(cont_type,
                                                                          cont_id))
                return 1, "Cannot deactivate {} controller with ID {}: It's not "\
                          "active.".format(cont_type, cont_id)
        else:
            return 1, "{} controller with ID {} not found".format(cont_type, cont_id)


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
        if self.controller['LCD'][lcd_id].isRunning():
            return self.controller['LCD'][lcd_id].flash_lcd(state)
        else:
            return "LCD {} not running".format(lcd_id)


    def relay_on(self, relay_id, duration):
        """
        Turn relay on using default relay controller

        :param relay_id: Unique ID for relay
        :type relay_id: str
        :param duration: How long to turn the relay on
        :type duration: float
        """
        self.controller['Relay'].relay_on_off(relay_id, 'on', duration)
        return "Relay turned on"


    def relay_off(self, relay_id):
        """
        Turn relay off using default relay controller

        :param relay_id: Unique ID for relay
        :type relay_id: str
        """
        self.controller['Relay'].relay_on_off(relay_id, 'off')
        return "Relay turned off"


    def add_relay(self, relay_id):
        """
        Add relay to running relay controller

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param relay_id: Unique ID for relay
        :type relay_id: str
        """
        return self.controller['Relay'].add_mod_relay(relay_id)


    def del_relay(self, relay_id):
        """
        Delete relay from running relay controller

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param relay_id: Unique ID for relay
        :type relay_id: str
        """
        return self.controller['Relay'].del_relay(relay_id)


    def mod_relay(self, relay_id):
        """
        Modify relay settings in running relay controller

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param relay_id: Unique ID for relay
        :type relay_id: str
        """
        return self.controller['Relay'].add_mod_relay(relay_id, do_setup_pin=True)


    def refresh_sensor_conditionals(self, sensor_id, cond_mod, cond_id):
        return self.controller['Sensor'][sensor_id].setup_sensor_conditionals(cond_mod, cond_id)


    def send_stats(self):
        """Collect and send statistics"""
        try:
            stat_dict = return_stat_file_dict(STATS_CSV)
            if float(stat_dict['next_send']) < time.time():
                self.timer_stats = self.timer_stats+STATS_INTERVAL
                add_update_csv(self.logger, STATS_CSV,
                                           'next_send', self.timer_stats)
            else:
                self.timer_stats = float(stat_dict['next_send'])
        except Exception as msg:
            self.logger.exception("Error: Cound not read file. Deleting file and regenerating. Error msg: {}".format(msg))
            os.remove(STATS_CSV)
            recreate_stat_file(ID_FILE, STATS_CSV, STATS_INTERVAL, MYCODO_VERSION)
        try:
            send_stats(self.logger, STATS_HOST, STATS_PORT,
                                   STATS_USER, STATS_PASSWORD, STATS_DATABASE,
                                   MYCODO_DB_PATH, USER_DB_PATH,
                                   STATS_CSV, MYCODO_VERSION,
                                   session_scope, LCD, Log, Method, PID,
                                   Relay, Sensor, Timer, Users)
        except Exception as msg:
            self.logger.exception("Error: Cound not send statistics: {}".format(msg))


    def startup_stats(self):
        """Initial statistics collection and transmssion at startup"""
        with session_scope(MYCODO_DB_PATH) as new_session:
            misc = new_session.query(Misc).first()
            self.opt_out_statistics = misc.stats_opt_out
        if not self.opt_out_statistics:
            self.logger.info("[Daemon] Anonymous statistics enabled")
        else:
            self.logger.info("[Daemon] Anonymous statistics disabled")

        try:
            # if statistics file doesn't exist, create it
            if not os.path.isfile(STATS_CSV):
                self.logger.debug("[Daemon] Statistics file doesn't "
                                  "exist, creating {}".format(STATS_CSV))
                recreate_stat_file(ID_FILE, STATS_CSV, STATS_INTERVAL, MYCODO_VERSION)

            daemon_startup_time = timeit.default_timer()-self.startup_timer
            self.logger.info("[Daemon] Mycodo v{} started in {} seconds".format(
                MYCODO_VERSION, daemon_startup_time))
            add_update_csv(self.logger, STATS_CSV,
                                       'daemon_startup_seconds',
                                       daemon_startup_time)
        except Exception as msg:
            self.logger.exception(
                "[Daemon] Statistics initilization Error: {}".format(msg))


    def start_all_controllers(self):
        """Start all activated controllers"""
        # Obtain database configuration options
        with session_scope(MYCODO_DB_PATH) as new_session:
            lcd = new_session.query(LCD).all()
            log = new_session.query(Log).all()
            pid = new_session.query(PID).all()
            sensor = new_session.query(Sensor).all()
            timer = new_session.query(Timer).all()
            new_session.expunge_all()
            new_session.close()

        # Start thread to control relays turning on and off
        self.logger.debug("[Daemon] Starting relay controller")
        self.controller['Relay'] = RelayController(self.logger)
        self.controller['Relay'].start()

        # Start threads to modulate relays at predefined periods
        self.logger.debug("[Daemon] Starting all activated timer controllers")
        for each_timer in timer:
            if each_timer.activated:
                self.activateController('Timer', each_timer.id)
        self.logger.info("[Daemon] All activated timer controllers started")

        # Start threads to read sensors and create influxdb entries
        self.logger.debug("[Daemon] Starting all activated sensor controllers")
        for each_sensor in sensor:
            if each_sensor.activated:
                self.activateController('Sensor', each_sensor.id)
        self.logger.info("[Daemon] All activated sensor controllers started")

        # Start threads to read influxdb entries and write to a log file
        self.logger.debug("[Daemon] Starting all activated log controllers")
        for each_log in log:
            if each_log.activated:
                self.activateController('Log', each_log.id)
        self.logger.info("[Daemon] All activated log controllers started")

        # start threads to manipulate relays with discrete PID control
        self.logger.debug("[Daemon] Starting all activated PID controllers")
        for each_pid in pid:
            if each_pid.activated:
                self.activateController('PID', each_pid.id)
        self.logger.info("[Daemon] All activated PID controllers started")

        # start threads to output to LCDs
        self.logger.debug("[Daemon] Starting all activated LCD controllers")
        for each_lcd in lcd:
            if each_lcd.activated:
                self.activateController('LCD', each_lcd.id)
        self.logger.info("[Daemon] All activated LCD controllers started")


    def stop_all_controllers(self):
        """Stop all running controllers"""
        lcd_controller_running = []
        log_controller_running = []
        pid_controller_running = []
        sensor_controller_running = []
        timer_controller_running = []

        # stop the controllers
        for lcd_id in self.controller['LCD']:
            if self.controller['LCD'][lcd_id].isRunning():
                self.controller['LCD'][lcd_id].stopController()
                lcd_controller_running.append(lcd_id)

        for pid_id in self.controller['PID']:
            if self.controller['PID'][pid_id].isRunning():
                self.controller['PID'][pid_id].stopController()
                pid_controller_running.append(pid_id)

        for log_id in self.controller['Log']:
            if self.controller['Log'][log_id].isRunning():
                self.controller['Log'][log_id].stopController()
                log_controller_running.append(log_id)

        for sensor_id in self.controller['Sensor']:
            if self.controller['Sensor'][sensor_id].isRunning():
                self.controller['Sensor'][sensor_id].stopController()
                sensor_controller_running.append(sensor_id)

        for timer_id in self.controller['Timer']:
            if self.controller['Timer'][timer_id].isRunning():
                self.controller['Timer'][timer_id].stopController()
                timer_controller_running.append(timer_id)

        # wait for the threads to finish
        for lcd_id in lcd_controller_running:
            self.controller['LCD'][lcd_id].join()
        self.logger.info("[Daemon] All LCD controllers stopped")

        for timer_id in timer_controller_running:
            self.controller['Timer'][timer_id].join()
        self.logger.info("[Daemon] All Timer controllers stopped")

        for sensor_id in sensor_controller_running:
            self.controller['Sensor'][sensor_id].join()
        self.logger.info("[Daemon] All Sensor controllers stopped")

        for log_id in log_controller_running:
            self.controller['Log'][log_id].join()
        self.logger.info("[Daemon] All Log controllers stopped")

        for pid_id in pid_controller_running:
            self.controller['PID'][pid_id].join()
        self.logger.info("[Daemon] All PID controllers stopped")

        self.controller['Relay'].stopController()
        self.controller['Relay'].join()


    def terminateDaemon(self):
        """Instruct the daemon to shut down"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.logger.info("[Daemon] Received command to terminate daemon")
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
    # Check for root priveileges
    if not os.geteuid() == 0:
        sys.exit("Script must be executed as root")

    # Check if lock file already exists
    if os.path.isfile(DAEMON_PID_FILE):
        sys.exit("Lock file present. Ensure the daemon isn't "
                 "already running and delete {}".format(DAEMON_PID_FILE))

    # Parse commandline arguments
    args = parse_args()

    # Set up logger
    logger = logging.getLogger(__name__)
    fh = logging.FileHandler(DAEMON_LOG_FILE, 'a')

    if args.debug:
        logger.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        fh.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.propagate = False
    logger.addHandler(fh)
    keep_fds = [fh.stream.fileno()]

    global mycodo_daemon
    mycodo_daemon = DaemonController(logger)

    # Set up daemon and start it
    daemon = Daemonize(app="Mycodod",
                       pid=DAEMON_PID_FILE,
                       action=start_daemon,
                       keep_fds=keep_fds)
    daemon.start()
