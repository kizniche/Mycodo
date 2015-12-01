#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo.py - The Mycodo deamon performs all crucial back-end tasks in
#              the system.
#
#  Copyright (C) 2015  Kyle T. Gabriel
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

#### Install Directory ####
install_directory = "/var/www/mycodo"

# Mycodo modules
import mycodoGraph
import mycodoLog
from mycodoPID import PID

# Other modules
import Adafruit_DHT
import Adafruit_BMP.BMP085 as BMP085
import datetime
import getopt
import logging
import os
import rpyc
import RPi.GPIO as GPIO
import serial
import shutil
import smtplib
import socket
import sqlite3
import subprocess
import smbus
import sys
import threading
import time
from email.mime.text import MIMEText
from lockfile import LockFile
from rpyc.utils.server import ThreadedServer
from tentacle_pi.AM2315 import AM2315

mycodo_database = os.path.join(install_directory, "config/mycodo.db")  # SQLite database
image_path = os.path.join(install_directory, "images")  # Where generated graphs are stored
log_path = os.path.join(install_directory, "log")  # Where generated logs are stored

# Daemon log on tempfs
daemon_log_file_tmp = os.path.join(log_path, "daemon-tmp.log")

logging.basicConfig(filename=daemon_log_file_tmp, level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Where lockfiles are stored for certain processes
lock_directory = "/var/lock/mycodo"
sql_lock_path = os.path.join(lock_directory, "config")
daemon_lock_path = os.path.join(lock_directory, "daemon")
sensor_t_lock_path = os.path.join(lock_directory, "sensor-t")
sensor_ht_lock_path = os.path.join(lock_directory, "sensor-ht")
sensor_co2_lock_path = os.path.join(lock_directory, "sensor-co2")
sensor_press_lock_path = os.path.join(lock_directory, "sensor-press")

# Logs that are on the tempfs
daemon_log_file_tmp = os.path.join(log_path, "daemon-tmp.log")
sensor_t_log_file_tmp = os.path.join(log_path, "sensor-t-tmp.log")
sensor_ht_log_file_tmp = os.path.join(log_path, "sensor-ht-tmp.log")
sensor_co2_log_file_tmp = os.path.join(log_path, "sensor-co2-tmp.log")
sensor_press_log_file_tmp = os.path.join(log_path, "sensor-press-tmp.log")
relay_log_file_tmp = os.path.join(log_path, "relay-tmp.log")

# PID Restarting
pid_number = None
pid_t_temp_down = 0
pid_t_temp_up = 0
pid_ht_temp_down = 0
pid_ht_temp_up = 0
pid_ht_hum_down = 0
pid_ht_hum_up = 0
pid_co2_down = 0
pid_co2_up = 0
pid_press_temp_down = 0
pid_press_temp_up = 0
pid_press_press_down = 0
pid_press_press_up = 0

# Miscellaneous
start_all_t_pids = None
stop_all_t_pids = None
start_all_ht_pids = None
stop_all_ht_pids = None
start_all_co2_pids = None
stop_all_co2_pids = None
camera_light = None
server = None
client_que = '0'
client_var = None

last_t_reading = 0
last_ht_reading = 0
last_co2_reading = 0
last_press_reading = 0

pause_daemon = 0
pause_daemon_confirm = 0

on_duration_timer = []
on_duration_seconds = []


# Threaded server that receives commands from mycodo-client.py
class ComServer(rpyc.Service):
    def exposed_ChangeRelay(self, relay, state):
        if state == 1:
            logging.info("[Client command] Changing Relay %s (%s) to HIGH", relay, relay_name[relay - 1])
            relay_onoff(int(relay), 'on')
        elif state == 0:
            logging.info("[Client command] Changing Relay %s (%s) to LOW", relay, relay_name[relay - 1])
            relay_onoff(int(relay), 'off')
        else:
            logging.info("[Client command] Turning Relay %s (%s) On for %s seconds", relay, relay_name[relay - 1], state)
            rod = threading.Thread(target=relay_on_duration, args=(int(relay), int(state), 0, relay_trigger, relay_pin,))
            rod.start()
        return 1

    def exposed_GenerateGraph(self, theme, graph_type, graph_id, graph_span, time_from, time_to, width):
        # Calculate the size of /var/tmp
        folder_path = '/var/tmp'
        total_tmp_folder_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_tmp_folder_size += os.path.getsize(fp)
        # Delete /var/tmp/* if the folder size is greater than 20 MB
        if total_tmp_folder_size > 20000000:
            logging.debug("[Cleanup] /var/tmp size = %s bytes > 20000000 bytes (20 MB). Cleaning up free space.", total_tmp_folder_size)
            folder = '/var/tmp'
            for the_file in os.listdir(folder):
                file_path = os.path.join(folder, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path): 
                        shutil.rmtree(file_path)
                except Exception, error:
                    logging.warning("[Cleanup] Error: %s", error)
            time.sleep(0.1)

        conn = sqlite3.connect(mycodo_database)
        cur = conn.cursor()
        cur.execute("""SELECT combined_temp_min,
                              combined_temp_max,
                              combined_temp_tics,
                              combined_temp_mtics,
                              combined_temp_relays_up,
                              combined_temp_relays_down,
                              combined_temp_relays_min,
                              combined_temp_relays_max,
                              combined_temp_relays_tics,
                              combined_temp_relays_mtics,
                              combined_hum_min,
                              combined_hum_max,
                              combined_hum_tics,
                              combined_hum_mtics,
                              combined_hum_relays_up,
                              combined_hum_relays_down,
                              combined_hum_relays_min,
                              combined_hum_relays_max,
                              combined_hum_relays_tics,
                              combined_hum_relays_mtics,
                              combined_co2_min,
                              combined_co2_max,
                              combined_co2_tics,
                              combined_co2_mtics,
                              combined_co2_relays_up,
                              combined_co2_relays_down,
                              combined_co2_relays_min,
                              combined_co2_relays_max,
                              combined_co2_relays_tics,
                              combined_co2_relays_mtics,
                              combined_press_min,
                              combined_press_max,
                              combined_press_tics,
                              combined_press_mtics,
                              combined_press_relays_up,
                              combined_press_relays_down,
                              combined_press_relays_min,
                              combined_press_relays_max,
                              combined_press_relays_tics,
                              combined_press_relays_mtics
                       FROM   customgraph """)
        for row in cur:
            combined_temp_min = row[0]
            combined_temp_max = row[1]
            combined_temp_tics = row[2]
            combined_temp_mtics = row[3]
            combined_temp_relays_up = row[4]
            combined_temp_relays_down = row[5]
            combined_temp_relays_min = row[6]
            combined_temp_relays_max = row[7]
            combined_temp_relays_tics = row[8]
            combined_temp_relays_mtics = row[9]
            combined_hum_min = row[10]
            combined_hum_max = row[11]
            combined_hum_tics = row[12]
            combined_hum_mtics = row[13]
            combined_hum_relays_up = row[14]
            combined_hum_relays_down = row[15]
            combined_hum_relays_min = row[16]
            combined_hum_relays_max = row[17]
            combined_hum_relays_tics = row[18]
            combined_hum_relays_mtics = row[19]
            combined_co2_min = row[20]
            combined_co2_max = row[21]
            combined_co2_tics = row[22]
            combined_co2_mtics = row[23]
            combined_co2_relays_up = row[24]
            combined_co2_relays_down = row[25]
            combined_co2_relays_min = row[26]
            combined_co2_relays_max = row[27]
            combined_co2_relays_tics = row[28]
            combined_co2_relays_mtics = row[29]
            combined_press_min = row[30]
            combined_press_max = row[31]
            combined_press_tics = row[32]
            combined_press_mtics = row[33]
            combined_press_relays_up = row[34]
            combined_press_relays_down = row[35]
            combined_press_relays_min = row[36]
            combined_press_relays_max = row[37]
            combined_press_relays_tics = row[38]
            combined_press_relays_mtics = row[39]

        combined_temp_relays_up_list = [int(x) for x in combined_temp_relays_up.split(',')]
        combined_temp_relays_down_list = [int(x) for x in combined_temp_relays_down.split(',')]
        combined_hum_relays_up_list = [int(x) for x in combined_hum_relays_up.split(',')]
        combined_hum_relays_down_list = [int(x) for x in combined_hum_relays_down.split(',')]
        combined_co2_relays_up_list = [int(x) for x in combined_co2_relays_up.split(',')]
        combined_co2_relays_down_list = [int(x) for x in combined_co2_relays_down.split(',')]
        combined_press_relays_up_list = [int(x) for x in combined_press_relays_up.split(',')]
        combined_press_relays_down_list = [int(x) for x in combined_press_relays_down.split(',')]

        logging.info("[Client command] Generate Graph: %s %s %s %s %s %s %s", theme, graph_type, graph_span, graph_id, time_from, time_to, width)
        mycodoGraph.generate_graph(theme, graph_type, graph_span, graph_id, sensor_t_name, sensor_t_graph, sensor_t_period, sensor_t_yaxis_relay_min, sensor_t_yaxis_relay_max, sensor_t_yaxis_relay_tics, sensor_t_yaxis_relay_mtics, sensor_t_yaxis_temp_min, sensor_t_yaxis_temp_max, sensor_t_yaxis_temp_tics, sensor_t_yaxis_temp_mtics, sensor_t_temp_relays_up_list, sensor_t_temp_relays_down_list, pid_t_temp_relay_high, pid_t_temp_relay_low, sensor_ht_name, sensor_ht_graph, sensor_ht_period, sensor_ht_yaxis_relay_min, sensor_ht_yaxis_relay_max, sensor_ht_yaxis_relay_tics, sensor_ht_yaxis_relay_mtics, sensor_ht_yaxis_temp_min, sensor_ht_yaxis_temp_max, sensor_ht_yaxis_temp_tics, sensor_ht_yaxis_temp_mtics, sensor_ht_yaxis_hum_min, sensor_ht_yaxis_hum_max, sensor_ht_yaxis_hum_tics, sensor_ht_yaxis_hum_mtics, sensor_ht_temp_relays_up_list, sensor_ht_temp_relays_down_list, sensor_ht_hum_relays_up_list, sensor_ht_hum_relays_down_list, pid_ht_temp_relay_high, pid_ht_temp_relay_low, pid_ht_hum_relay_high, pid_ht_hum_relay_low, sensor_co2_name, sensor_co2_graph, sensor_co2_period, sensor_co2_yaxis_relay_min, sensor_co2_yaxis_relay_max, sensor_co2_yaxis_relay_tics, sensor_co2_yaxis_relay_mtics, sensor_co2_yaxis_co2_min, sensor_co2_yaxis_co2_max, sensor_co2_yaxis_co2_tics, sensor_co2_yaxis_co2_mtics, sensor_co2_relays_up_list, sensor_co2_relays_down_list, pid_co2_relay_high, pid_co2_relay_low, sensor_press_name, sensor_press_graph, sensor_press_period, sensor_press_yaxis_relay_min, sensor_press_yaxis_relay_max, sensor_press_yaxis_relay_tics, sensor_press_yaxis_relay_mtics, sensor_press_yaxis_temp_min, sensor_press_yaxis_temp_max, sensor_press_yaxis_temp_tics, sensor_press_yaxis_temp_mtics, sensor_press_yaxis_press_min, sensor_press_yaxis_press_max, sensor_press_yaxis_press_tics, sensor_press_yaxis_press_mtics, sensor_press_temp_relays_up_list, sensor_press_temp_relays_down_list, sensor_press_press_relays_up_list, sensor_press_press_relays_down_list, pid_press_temp_relay_high, pid_press_temp_relay_low, pid_press_press_relay_high, pid_press_press_relay_low, relay_name, relay_pin, time_from, time_to, width, combined_temp_min, combined_temp_max, combined_temp_tics, combined_temp_mtics, combined_temp_relays_up, combined_temp_relays_down, combined_temp_relays_min, combined_temp_relays_max, combined_temp_relays_tics, combined_temp_relays_mtics, combined_hum_min, combined_hum_max, combined_hum_tics, combined_hum_mtics, combined_hum_relays_up, combined_hum_relays_down, combined_hum_relays_min, combined_hum_relays_max, combined_hum_relays_tics, combined_hum_relays_mtics, combined_co2_min, combined_co2_max, combined_co2_tics, combined_co2_mtics, combined_co2_relays_up, combined_co2_relays_down, combined_co2_relays_min, combined_co2_relays_max, combined_co2_relays_tics, combined_co2_relays_mtics, combined_press_min, combined_press_max, combined_press_tics, combined_press_mtics, combined_press_relays_up, combined_press_relays_down, combined_press_relays_min, combined_press_relays_max, combined_press_relays_tics, combined_press_relays_mtics, combined_temp_relays_up_list, combined_temp_relays_down_list, combined_hum_relays_up_list, combined_hum_relays_down_list, combined_co2_relays_up_list, combined_co2_relays_down_list, combined_press_relays_up_list, combined_press_relays_down_list)
        return 1

    def exposed_all_PID_restart(self, sensortype):
        global PID_change
        PID_change = 1
        logging.info("[Daemon] Commanding all %s PID controllers to restart", sensortype)
        if sensortype == 'T':
            global start_all_t_pids
            global stop_all_t_pids
            stop_all_t_pids = 1
            for i in range(0, len(sensor_t_id)):
                if pid_t_temp_or[i] == 0:
                    while pid_t_temp_alive[i] == 0:
                        time.sleep(0.1)
            time.sleep(0.25)
            read_sql()
            logging.info("[Daemon] Commanding all T PID controllers to start")
            time.sleep(0.25)
            start_all_t_pids = 1
        elif sensortype == 'HT':
            global start_all_ht_pids
            global stop_all_ht_pids
            stop_all_ht_pids = 1
            for i in range(0, len(sensor_ht_id)):
                if pid_ht_temp_or[i] == 0:
                    while pid_ht_temp_alive[i] == 0:
                        time.sleep(0.1)
            for i in range(0, len(sensor_ht_id)):
                if pid_ht_hum_or[i] == 0:
                    while pid_ht_hum_alive[i] == 0:
                        time.sleep(0.1)
            read_sql()
            logging.info("[Daemon] Commanding all HT PID controllers to start")
            start_all_ht_pids = 1
        elif sensortype == 'CO2':
            global start_all_co2_pids
            global stop_all_co2_pids
            stop_all_co2_pids = 1
            for i in range(0, len(sensor_co2_id)):
                if pid_co2_or[i] == 0:
                    while pid_co2_alive[i] == 0:
                        time.sleep(0.1)
            read_sql()
            logging.info("[Daemon] Commanding all CO2 PID controllers to start")
            start_all_co2_pids = 1
        elif sensortype == 'Press':
            global start_all_press_pids
            global stop_all_press_pids
            stop_all_press_pids = 1
            for i in range(0, len(sensor_press_id)):
                if pid_press_temp_or[i] == 0:
                    while pid_press_temp_alive[i] == 0:
                        time.sleep(0.1)
            for i in range(0, len(sensor_press_id)):
                if pid_press_press_or[i] == 0:
                    while pid_press_press_alive[i] == 0:
                        time.sleep(0.1)
            read_sql()
            logging.info("[Daemon] Commanding all Press PID controllers to start")
            start_all_press_pids = 1
        return 1

    def exposed_PID_restart(self, pidtype, number):
        global PID_change
        PID_change = 1
        PID_stop(pidtype, number)
        logging.info("[Client command] Reload SQLite database (Note: May cause interruption of sensor readings)")
        read_sql()
        PID_start(pidtype, number)
        return 1

    def exposed_PID_start(self, pidtype, number):
        global PID_change
        PID_change = 1
        PID_start(pidtype, number)
        return 1

    def exposed_PID_stop(self, pidtype, number):
        global PID_change
        PID_change = 1
        PID_stop(pidtype, number)
        return 1


    def exposed_ReadTSensor(self, device, sensor_id):
        """
        User facing function takes sensor_id as numbered on webpage.
        """
        return self.readtsensor(device, sensor_id - 1)

    def readtsensor(self, device, raw_sensor_id):
        """
        Internal implementation of readtsensor.  May change over time or as sensors are added.  Consistent internal notation 
        """

        logging.info("[Client command] Read %s T Sensor %s", device, raw_sensor_id + 1)
        if device in 'DS18B20':
            return read_t_sensor(raw_sensor_id)
        else:
            return 'Invalid Sensor Name'


    def exposed_ReadHTSensor(self, device, sensor_id):
        """
        User facing function takes sensor_id as numbered on webpage.
        """
        return self.readhtsensor(device, sensor_id - 1)

    def readhtsensor(self, device, raw_sensor_id):
        """
        Internal implementation of readhtsensor.  May change over time or as sensors are added.  Consistent internal notation 
        """

        logging.info("[Client command] Read %s HT Sensor %s", device, raw_sensor_id + 1)
        if device in ['DHT11', 'DHT22', 'AM2302', 'AM2315']:
            return read_ht_sensor(raw_sensor_id)
        else:
            return 'Invalid Sensor Name'


    def exposed_ReadCO2Sensor(self, device, sensor_id):
        """
        User facing function takes sensor_id as numbered on webpage.
        """
        return self.readco2sensor(device, sensor_id - 1)

    def readco2sensor(self, device, raw_sensor_id):
        """
        Internal implementation of readco2sensor.  May change over time or as sensors are added.  Consistent internal notation 
        """

        logging.info("[Client command] Read %s CO2 Sensor %s", device, raw_sensor_id + 1)
        if device in 'K30':
            return read_co2_sensor(raw_sensor_id)
        else:
            return 'Invalid Sensor Name'


    def exposed_ReadPressSensor(self, device, sensor_id):
        """
        User facing function takes sensor_id as numbered on webpage.
        """
        return self.readpresssensor(device, sensor_id - 1)

    def readpresssensor(self, device, raw_sensor_id):
        """
        Internal implementation of readpresssensor.  May change over time or as sensors are added.  Consistent internal notation 
        """

        logging.info("[Client command] Read %s Press Sensor %s", device, raw_sensor_id + 1)
        if device in 'BMP085-180':
            return read_press_sensor(raw_sensor_id)
        else:
            return 'Invalid Sensor Name'


    def exposed_SQLReload(self, relay):
        if relay != -1:
            logging.info("[Client command] Relay %s GPIO pin changed to %s, initialize and turn off", relay, relay_pin[relay])
            initialize_gpio(relay)
        logging.info("[Client command] Reload SQLite database (Note: May cause interruption of sensor readings)")
        read_sql()
        return 1

    def exposed_Status(self, var):
        logging.info("[Client command] Request status report")        
        return 1, globals().keys(), globals().values()

    def exposed_TestEmail(self, email_to):
        logging.info("[Client command] Send test email to %s", email_to)
        email(email_to, "This is a test of the Mycodo email notification system")
        return 1

    def exposed_Terminate(self, remoteCommand):
        global client_que
        client_que = 'TerminateServer'
        logging.info("[Client command] Shut down the daemon")
        mycodoLog.Concatenate_Logs()
        return 1


# Communication thread to receive client commands from mycodo-client.py
class ComThread(threading.Thread):
    def run(self):
        global server
        server = ThreadedServer(ComServer, port=18812)
        server.start()


# Displays the program usage
def usage():
    print "mycodo.py: Daemon that reads sensors, writes logs, and operates"
    print "           relays to maintain set environmental conditions."
    print "           Run as root.\n"
    print "Usage:  mycodo.py [OPTION]...\n"
    print "Options:"
    print "    -h, --help"
    print "           Display this help and exit"
    print "    -l, --log level"
    print "           Set logging level: w < i < d (default: ""i"")"
    print "           Options:"
    print "           ""w"": warnings only"
    print "           ""i"": info and warnings"
    print "           ""d"": debug, info, and warnings"
    print "    -v, --verbose"
    print "           enables log output to the console\n"
    print "Examples: mycodo.py"
    print "          mycodo.py -l d"
    print "          mycodo.py -l w -v\n"


# Check for any command line options
def menu():
    global a
    a = 'silent'
    global b
    b = 'info'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hl:v', ["help", "log", "verbose"])
    except getopt.GetoptError as err:
        print(err)  # will print "option -a not recognized"
        usage()
        return 2
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            return 0
        elif opt in ("-l", "--log"):
            if arg == 'w':
                b = 'warning'
            elif arg == 'd':
                b = 'debug'
        elif opt in ("-v", "--verbose"):
            a = 'verbose'
        else:
            assert False, "Fail"
    return 1


#################################################
#                    Daemon                     #
#################################################

# Read sensors, modify relays based on sensor values, write sensor/relay
# logs, and receive/execute commands from mycodo-client.py
def daemon(output, log):
    global pid_t_temp_alive
    global pid_t_temp_down
    global pid_t_temp_up

    global pid_ht_temp_alive
    global pid_ht_temp_down
    global pid_ht_temp_up

    global pid_ht_hum_alive
    global pid_ht_hum_down
    global pid_ht_hum_up

    global pid_co2_alive
    global pid_co2_down
    global pid_co2_up

    global pid_press_temp_alive
    global pid_press_temp_down
    global pid_press_temp_up

    global pid_press_press_alive
    global pid_press_press_down
    global pid_press_press_up

    global pid_t_temp_active
    global pid_ht_temp_active
    global pid_ht_hum_active
    global pid_co2_active
    global pid_press_temp_active
    global pid_press_press_active

    pid_t_temp_active = []
    pid_ht_temp_active = []
    pid_ht_hum_active = []
    pid_co2_active = []
    pid_press_temp_active = []
    pid_press_press_active = []

    global start_all_t_pids
    global stop_all_t_pids
    global start_all_ht_pids
    global stop_all_ht_pids
    global start_all_co2_pids
    global stop_all_co2_pids
    global start_all_press_pids
    global stop_all_press_pids

    start_all_t_pids = 1
    stop_all_t_pids = 0
    start_all_ht_pids = 1
    stop_all_ht_pids = 0
    start_all_co2_pids = 1
    stop_all_co2_pids = 0
    start_all_press_pids = 1
    stop_all_press_pids = 0

    global change_sensor_log
    global server
    global client_que

    global PID_change
    PID_change = 0

    global pause_daemon_confirm
    pause_daemon_confirm = -1

    # Set log level based on startup argument
    if log == 'warning':
        logging.getLogger().setLevel(logging.WARNING)
    elif log == 'info':
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.DEBUG)

    if output == 'verbose':
        # define a Handler which writes DEBUG messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)
    logging.info("[Daemon] Starting daemon")
    logging.info("[Daemon] Starting communication server")
    ct = ComThread()
    ct.daemon = True
    ct.start()
    time.sleep(1)
    pid_t_temp_alive = [1] * len(sensor_t_id)
    pid_ht_temp_alive = [1] * len(sensor_ht_id)
    pid_ht_hum_alive = [1] * len(sensor_ht_id)
    pid_co2_alive = [1] * len(sensor_co2_id)
    pid_press_temp_alive = [1] * len(sensor_press_id)
    pid_press_press_alive = [1] * len(sensor_press_id)
    # How often to check log sizes and backup all logs to SD card
    timerLogBackup = time.time() + 600  # 600 seconds = 10 minutes
    timerLogBackupCount = 0

    while True:  # Main loop of the daemon
        # Wait for and pause the daemon while the SQL database is reloaded
        if pause_daemon:
            logging.debug("[Daemon] Daemon Paused")
            pause_daemon_confirm = 0
            while pause_daemon and client_que != 'TerminateServer':
                time.sleep(0.1)
            pause_daemon_confirm = -1

        #
        # Run remote commands issued by mycodo-client.py
        #
        if client_que == 'TerminateServer':
            logging.info("[Daemon] Shutting down all threads")
            for t in threads_t_t:
                t.join()
            for t in threads_ht_t:
                t.join()
            for t in threads_ht_h:
                t.join()
            for t in threads_co2:
                t.join()
            server.close()
            logging.info("[Daemon] Turning off all relays")
            Relays_Off()
            logging.info("[Daemon] Shutdown success")
            return 0

        #
        # Stop/Start all PID threads of a particular sensor type
        #
        if stop_all_t_pids:
            pid_t_temp_alive = [0] * len(sensor_t_id)
            stop_all_t_pids = 0
        if start_all_t_pids:
            pid_t_temp_alive = []
            pid_t_temp_alive = [1] * len(sensor_t_id)
            threads_t_t = []
            for i in range(0, len(sensor_t_id)):
                if pid_t_temp_or[i] == 0:
                    pid_t_temp_active.append(1)
                    rod = threading.Thread(target=t_sensor_temperature_monitor, args=('Thread-T-T-%d' % (i + 1), i,))
                    rod.start()
                    threads_t_t.append(rod)
                else:
                    pid_t_temp_active.append(0)
            start_all_t_pids = 0

        if stop_all_ht_pids:
            pid_ht_temp_alive = [0] * len(sensor_ht_id)
            pid_ht_hum_alive = [0] * len(sensor_ht_id)
            stop_all_ht_pids = 0
        if start_all_ht_pids:
            pid_ht_temp_alive = []
            pid_ht_temp_alive = [1] * len(sensor_ht_id)
            pid_ht_hum_alive = []
            pid_ht_hum_alive = [1] * len(sensor_ht_id)
            threads_ht_t = []
            for i in range(0, len(sensor_ht_id)):
                if pid_ht_temp_or[i] == 0:
                    pid_ht_temp_active.append(1)
                    rod = threading.Thread(target=ht_sensor_temperature_monitor, args=('Thread-HT-T-%d' % (i + 1), i,))
                    rod.start()
                    threads_ht_t.append(rod)
                else:
                    pid_ht_temp_active.append(0)
            threads_ht_h = []
            for i in range(0, len(sensor_ht_id)):
                if pid_ht_hum_or[i] == 0:
                    pid_ht_hum_active.append(1)
                    rod = threading.Thread(target=ht_sensor_humidity_monitor, args=('Thread-HT-H-%d' % (i + 1), i,))
                    rod.start()
                    threads_ht_h.append(rod)
                else:
                    pid_ht_hum_active.append(0)
            start_all_ht_pids = 0

        if stop_all_co2_pids:
            pid_co2_temp_alive = [0] * len(sensor_co2_id)
            stop_all_co2_pids = 0
        if start_all_co2_pids:
            pid_co2_alive = []
            pid_co2_alive = [1] * len(sensor_co2_id)
            threads_co2 = []
            for i in range(0, len(sensor_co2_id)):
                if pid_co2_or[i] == 0:
                    pid_co2_active[i] = 1
                    rod = threading.Thread(target=co2_monitor, args=('Thread-CO2-%d' % (i + 1), i,))
                    rod.start()
                    threads_co2.append(rod)
            start_all_co2_pids = 0

        if stop_all_press_pids:
            pid_press_temp_alive = [0] * len(sensor_press_id)
            pid_press_press_alive = [0] * len(sensor_press_id)
            stop_all_press_pids = 0
        if start_all_press_pids:
            pid_press_temp_alive = []
            pid_press_temp_alive = [1] * len(sensor_press_id)
            pid_press_press_alive = []
            pid_press_press_alive = [1] * len(sensor_press_id)
            threads_press_t = []
            for i in range(0, len(sensor_press_id)):
                if pid_press_temp_or[i] == 0:
                    pid_press_temp_active.append(1)
                    rod = threading.Thread(target=press_sensor_temperature_monitor, args=('Thread-HT-T-%d' % (i + 1), i,))
                    rod.start()
                    threads_press_t.append(rod)
                else:
                    pid_press_temp_active.append(0)
            threads_press_h = []
            for i in range(0, len(sensor_press_id)):
                if pid_press_press_or[i] == 0:
                    pid_press_press_active.append(1)
                    rod = threading.Thread(target=press_sensor_pressure_monitor, args=('Thread-HT-H-%d' % (i + 1), i,))
                    rod.start()
                    threads_press_h.append(rod)
                else:
                    pid_press_press_active.append(0)
            start_all_press_pids = 0

        # Check if a PID is being stopped or started, used to pause other tasks
        if any((pid_t_temp_up, pid_ht_temp_up, pid_ht_hum_up, pid_co2_up, pid_press_temp_up,
               pid_press_press_up, pid_t_temp_down, pid_ht_temp_down, pid_ht_hum_down,
               pid_co2_down, pid_press_temp_down, pid_press_press_down, stop_all_t_pids,
               start_all_t_pids, stop_all_ht_pids, start_all_ht_pids, stop_all_co2_pids,
               start_all_co2_pids, stop_all_press_pids, start_all_press_pids)):
            PID_change = 1
        else:
            PID_change = 0

        #
        # Read sensors and write logs
        #
        for i in range(0, len(sensor_t_id)):
            if time.time() > timerTSensorLog[i] and sensor_t_device[i] != 'Other' and sensor_t_activated[i] == 1 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                logging.debug("[Timer Expiration] Read Temp-%s sensor every %s seconds: Write sensor log", i + 1, sensor_t_period[i])
                if read_t_sensor(i) is not None:
                    mycodoLog.write_t_sensor_log(sensor_t_read_temp_c, i)
                else:
                    logging.warning("Could not read Temp-%s sensor, not writing to sensor log", i + 1)
                timerTSensorLog[i] = time.time() + sensor_t_period[i]

        for i in range(0, len(sensor_ht_id)):
            if time.time() > timerHTSensorLog[i] and sensor_ht_device[i] != 'Other' and sensor_ht_activated[i] == 1 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                logging.debug("[Timer Expiration] Read HT-%s sensor every %s seconds: Write sensor log", i + 1, sensor_ht_period[i])
                if read_ht_sensor(i) is not None:
                    if (sensor_ht_verify_hum_notify[i] or sensor_ht_verify_temp_notify[i]) and sensor_ht_verify_pin[i] != 0:
                        verify_ht_sensor(i, sensor_ht_verify_pin[i])
                    mycodoLog.write_ht_sensor_log(sensor_ht_read_temp_c, sensor_ht_read_hum, sensor_ht_dewpt_c, i)
                else:
                    logging.warning("Could not read HT-%s sensor, not writing to sensor log", i + 1)
                timerHTSensorLog[i] = time.time() + sensor_ht_period[i]

        for i in range(0, len(sensor_co2_id)):
            if time.time() > timerCo2SensorLog[i] and sensor_co2_device[i] != 'Other' and sensor_co2_activated[i] == 1 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                if read_co2_sensor(i) is not None:
                    mycodoLog.write_co2_sensor_log(sensor_co2_read_co2, i)
                else:
                    logging.warning("Could not read CO2-%s sensor, not writing to sensor log", i + 1)
                timerCo2SensorLog[i] = time.time() + sensor_co2_period[i]

        for i in range(0, len(sensor_press_id)):
            if time.time() > timerPressSensorLog[i] and sensor_press_device[i] != 'Other' and sensor_press_activated[i] == 1 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                logging.debug("[Timer Expiration] Read Press-%s sensor every %s seconds: Write sensor log", i + 1, sensor_press_period[i])
                if read_press_sensor(i) is not None:
                    mycodoLog.write_press_sensor_log(sensor_press_read_temp_c, sensor_press_read_press, sensor_press_read_alt, i)
                else:
                    logging.warning("Could not read Press-%s sensor, not writing to sensor log", i + 1)
                timerPressSensorLog[i] = time.time() + sensor_press_period[i]

        #
        # Check if T conditional statements are true
        #
        for j in range(0, len(conditional_t_number_sensor)):
            for k in range(0, len(conditional_t_number_conditional)):
                if conditional_t_id[j][k][0] != 0 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                    if time.time() > timerTConditional[j][k] and conditional_t_state[j][k][0] == 1:
                        logging.debug("[Conditional T] Check conditional statement %s: %s", k + 1, conditional_t_name[j][k][0])
                        if read_t_sensor(j) is not None:
                            if (conditional_t_direction[j][k][0] == 1 and sensor_t_read_temp_c[j] > conditional_t_setpoint[j][k][0]) or (conditional_t_direction[j][k][0] == -1 and sensor_t_read_temp_c[j] < conditional_t_setpoint[j][k][0]):
                                if conditional_t_sel_relay[j][k][0]:
                                    if conditional_t_relay_state[j][k][0] == 1:
                                        if conditional_t_relay_seconds_on[j][k][0] > 0:
                                            logging.debug("[Conditional T] Conditional statement %s True: Turn relay %s on for %s seconds", k + 1, conditional_t_relay[j][k][0], conditional_t_relay_seconds_on[j][k][0])
                                            rod = threading.Thread(target=relay_on_duration, args=(conditional_t_relay[j][k][0], conditional_t_relay_seconds_on[j][k][0], j, relay_trigger, relay_pin,))
                                            rod.start()
                                        else:
                                            relay_onoff(conditional_t_relay[j][k][0], 'on')
                                    elif conditional_t_relay_state[j][k][0] == 0:
                                        relay_onoff(conditional_t_relay[j][k][0], 'off')
                                if conditional_t_sel_command[j][k][0]:
                                    p = subprocess.Popen(conditional_t_do_command[j][k][0], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    output, errors = p.communicate()
                                    logging.debug("[Conditional T] Conditional %s (%s) T Sensor %s (%s) True: Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_t_name[j][k][0], conditional_t_do_command[j][k][0], output, errors)
                                if conditional_t_sel_notify[j][k][0] and conditional_t_time_notify[j][k][0] < time.time():
                                    logging.debug("[Conditional T] Conditional %s (%s) T Sensor %s (%s) True: Notify %s", j + 1, sensor_t_name[j], k + 1, conditional_t_name[j][k][0], conditional_t_do_notify[j][k][0])
                                    if (conditional_t_direction[j][k][0] == 1 and
                                            sensor_t_read_temp_c[j] > conditional_t_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) T Sensor %s (%s) Temperature: %s C > %s C." % (j + 1, sensor_t_name[j], k + 1, conditional_t_name[j][k][0], round(sensor_t_read_temp_c[j], 2), conditional_t_setpoint[j][k][0])
                                    if (conditional_t_direction[j][k][0] == -1 and
                                            sensor_t_read_temp_c[j] < conditional_t_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) T Sensor %s (%s) Temperature: %s C < %s C." % (j + 1, sensor_t_name[j], k + 1, conditional_t_name[j][k][0], round(sensor_t_read_temp_c[j], 2), conditional_t_setpoint[j][k][0])
                                    email(conditional_t_do_notify[j][k][0], message)
                                    conditional_t_time_notify[j][k][0] = time.time() + smtp_wait_time
                                elif conditional_t_sel_notify[j][k][0]:
                                    logging.debug("[Conditional T] Conditional %s (%s) T Sensor %s (%s) True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", j + 1, sensor_t_name[j], k + 1, conditional_t_name[j][k][0], conditional_t_do_notify[j][k][0], (smtp_wait_time - (smtp_wait_time - (conditional_t_time_notify[j][k][0] - time.time()))), smtp_wait_time)
                        else:
                            logging.warning("[Conditional T] Could not read sensor %s, did not check conditional %s", j + 1, k + 1)
                        timerTConditional[j][k] = time.time() + conditional_t_period[j][k][0]

        #
        # Check if HT conditional statements are true
        #
        for j in range(0, len(conditional_ht_number_sensor)):
            for k in range(0, len(conditional_ht_number_conditional)):
                if conditional_ht_id[j][k][0] != 0 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                    if time.time() > timerHTConditional[j][k] and conditional_ht_state[j][k][0] == 1:
                        logging.debug("[Conditional HT] Check conditional statement %s: %s", k + 1, conditional_ht_name[j][k][0])
                        if read_ht_sensor(j) is not None:
                            if (conditional_ht_condition[j][k][0] == "Temperature" and conditional_ht_direction[j][k][0] == 1 and sensor_ht_read_temp_c[j] > conditional_ht_setpoint[j][k][0]) or (conditional_ht_condition[j][k][0] == "Temperature" and conditional_ht_direction[j][k][0] == -1 and sensor_ht_read_temp_c[j] < conditional_ht_setpoint[j][k][0]) or (conditional_ht_condition[j][k][0] == "Humidity" and conditional_ht_direction[j][k][0] == 1 and sensor_ht_read_hum[j] > conditional_ht_setpoint[j][k][0]) or (conditional_ht_condition[j][k][0] == "Humidity" and conditional_ht_direction[j][k][0] == -1 and sensor_ht_read_hum[j] < conditional_ht_setpoint[j][k][0]):
                                if conditional_ht_sel_relay[j][k][0]:
                                    if conditional_ht_relay_state[j][k][0] == 1:
                                        if conditional_ht_relay_seconds_on[j][k][0] > 0:
                                            logging.debug("[Conditional HT] Conditional %s (%s) HT Sensor %s (%s) True: Turn relay %s on for %s seconds", j + 1, sensor_ht_name[j], k + 1, conditional_ht_name[j][k][0], conditional_ht_relay[j][k][0], conditional_ht_relay_seconds_on[j][k][0])
                                            rod = threading.Thread(target=relay_on_duration, args=(conditional_ht_relay[j][k][0], conditional_ht_relay_seconds_on[j][k][0], j, relay_trigger, relay_pin,))
                                            rod.start()
                                        else:
                                            relay_onoff(conditional_ht_relay[j][k][0], 'on')
                                    elif conditional_ht_relay_state[j][k][0] == 0:
                                        relay_onoff(conditional_ht_relay[j][k][0], 'off')
                                if conditional_ht_sel_command[j][k][0]:
                                    p = subprocess.Popen(conditional_ht_do_command[j][k][0], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    output, errors = p.communicate()
                                    logging.debug("[Conditional HT] Conditional %s (%s) HT Sensor %s (%s) True: Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_ht_name[j][k][0], conditional_ht_do_command[j][k][0], output, errors)
                                if conditional_ht_sel_notify[j][k][0] and conditional_ht_time_notify[j][k][0] < time.time():
                                    logging.debug("[Conditional HT] Conditional %s (%s) HT Sensor %s (%s) True: Notify %s", j + 1, sensor_ht_name[j], k + 1, conditional_ht_name[j][k][0], conditional_ht_do_notify[j][k][0])
                                    if (conditional_ht_condition[j][k][0] == "Temperature" and
                                            conditional_ht_direction[j][k][0] == 1 and
                                            sensor_ht_read_temp_c[j] > conditional_ht_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) HT Sensor %s (%s) Temperature: %s C > %s C." % (j + 1, sensor_ht_name[j], k + 1, conditional_ht_name[j][k][0], round(sensor_ht_read_temp_c[j], 2), conditional_ht_setpoint[j][k][0])
                                    if (conditional_ht_condition[j][k][0] == "Temperature" and
                                            conditional_ht_direction[j][k][0] == -1 and
                                            sensor_ht_read_temp_c[j] < conditional_ht_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) HT Sensor %s (%s) Temperature: %s C < %s C." % (j + 1, sensor_ht_name[j], k + 1, conditional_ht_name[j][k][0], round(sensor_ht_read_temp_c[j], 1), conditional_ht_setpoint[j][k][0])
                                    if (conditional_ht_condition[j][k][0] == "Humidity" and
                                            conditional_ht_direction[j][k][0] == 1 and
                                            sensor_ht_read_hum[j] > conditional_ht_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) HT Sensor %s (%s) Humidity: %s%% > %s%%." % (j + 1, sensor_ht_name[j], k + 1, conditional_ht_name[j][k][0], round(sensor_ht_read_hum[j], 2), conditional_ht_setpoint[j][k][0])
                                    if (conditional_ht_condition[j][k][0] == "Humidity" and
                                            conditional_ht_direction[j][k][0] == -1 and
                                            sensor_ht_read_hum[j] < conditional_ht_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) HT Sensor %s (%s) Humidity: %s%% < %s%%." % (j + 1, sensor_ht_name[j], k + 1, conditional_ht_name[j][k][0], round(sensor_ht_read_hum[j], 2), conditional_ht_setpoint[j][k][0])
                                    email(conditional_ht_do_notify[j][k][0], message)
                                    conditional_ht_time_notify[j][k][0] = time.time() + smtp_wait_time
                                elif conditional_ht_sel_notify[j][k][0]:
                                    logging.debug("[Conditional HT] Conditional %s (%s) HT Sensor %s (%s) True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", j + 1, sensor_ht_name[j], k + 1, conditional_ht_name[j][k][0], conditional_ht_do_notify[j][k][0], (smtp_wait_time - (smtp_wait_time - (conditional_ht_time_notify[j][k][0] - time.time()))), smtp_wait_time)
                        else:
                            logging.warning("[Conditional HT] Could not read sensor %s, did not check conditional %s", j + 1, k + 1)
                        timerHTConditional[j][k] = time.time() + conditional_ht_period[j][k][0]

        #
        # Check if CO2 conditional statements are true
        #
        for j in range(0, len(conditional_co2_number_sensor)):
            for k in range(0, len(conditional_co2_number_conditional)):
                if conditional_co2_id[j][k][0] != 0 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                    if time.time() > timerCO2Conditional[j][k] and conditional_co2_state[j][k][0] == 1:
                        logging.debug("[Conditional CO2] Check conditional statement %s: %s", k + 1, conditional_co2_name[j][k][0])
                        if read_co2_sensor(j) is not None:
                            if (conditional_co2_direction[j][k][0] == 1 and sensor_co2_read_co2[j] > conditional_co2_setpoint[j][k][0]) or (conditional_co2_direction[j][k][0] == -1 and sensor_co2_read_co2[j] < conditional_co2_setpoint[j][k][0]):
                                if conditional_co2_sel_relay[j][k][0]:
                                    if conditional_co2_relay_state[j][k][0] == 1:
                                        if conditional_co2_relay_seconds_on[j][k][0] > 0:
                                            logging.debug("[Conditional CO2] Conditional statement %s True: Turn relay %s on for %s seconds", k + 1, conditional_co2_relay[j][k][0], conditional_co2_relay_seconds_on[j][k][0])
                                            rod = threading.Thread(target=relay_on_duration, args=(conditional_co2_relay[j][k][0], conditional_co2_relay_seconds_on[j][k][0], j, relay_trigger, relay_pin,))
                                            rod.start()
                                        else:
                                            relay_onoff(conditional_co2_relay[j][k][0], 'on')
                                    elif conditional_co2_relay_state[j][k][0] == 0:
                                        relay_onoff(conditional_co2_relay[j][k][0], 'off')
                                if conditional_co2_sel_command[j][k][0]:
                                    p = subprocess.Popen(conditional_co2_do_command[j][k][0], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    output, errors = p.communicate()
                                    logging.debug("[Conditional CO2] Conditional %s (%s) T Sensor %s (%s) True: Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_co2_name[j][k][0], conditional_co2_do_command[j][k][0], output, errors)
                                if conditional_co2_sel_notify[j][k][0] and conditional_co2_time_notify[j][k][0] < time.time():
                                    logging.debug("[Conditional CO2] Conditional %s (%s) CO2 Sensor %s (%s) True: Notify %s", j + 1, sensor_co2_name[j], k + 1, conditional_co2_name[j][k][0], conditional_co2_do_notify[j][k][0])
                                    if (conditional_co2_direction[j][k][0] == 1 and
                                            sensor_co2_read_co2[j] > conditional_co2_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) CO2 Sensor %s (%s) CO2: %s ppmv > %s ppmv." % (j + 1, sensor_co2_name[j], k + 1, conditional_co2_name[j][k][0], sensor_co2_read_co2[j], conditional_co2_setpoint[j][k][0])
                                    if (conditional_co2_direction[j][k][0] == -1 and
                                            sensor_co2_read_co2[j] < conditional_co2_setpoint[j][k][0]):
                                        message = "Conditional %s (%s) CO2 Sensor %s (%s) CO2: %s ppmv < %s ppmv." % (j + 1, sensor_co2_name[j], k + 1, conditional_co2_name[j][k][0], sensor_co2_read_co2[j], conditional_co2_setpoint[j][k][0])
                                    email(conditional_co2_do_notify[j][k][0], message)
                                    conditional_co2_time_notify[j][k][0] = time.time() + smtp_wait_time
                                elif conditional_co2_sel_notify[j][k][0]:
                                    logging.debug("[Conditional CO2] Conditional %s (%s) CO2 Sensor %s (%s) True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", j + 1, sensor_co2_name[j], k + 1, conditional_co2_name[j][k][0], conditional_co2_do_notify[j][k][0], (smtp_wait_time - (smtp_wait_time - (conditional_co2_time_notify[j][k][0] - time.time()))), smtp_wait_time)
                        else:
                            logging.warning("[Conditional CO2] Could not read sensor %s, did not check conditional %s", j + 1, k + 1)
                        timerCO2Conditional[j][k] = time.time() + conditional_co2_period[j][k][0]

        #
        # Check if Press conditional statements are true
        #
        for j in range(0, len(conditional_press_number_sensor)):
            for k in range(0, len(conditional_press_number_conditional)):
                if conditional_press_id[j][k][0] != 0 and client_que != 'TerminateServer' and pause_daemon != 1 and PID_change != 1:
                    if time.time() > timerPressConditional[j][k] and conditional_press_state[j][k][0] == 1:
                        logging.debug("[Conditional Press] Check conditional statement %s: %s", k + 1, conditional_press_name[j][k][0])
                        if read_press_sensor(j) is not None:
                            if (conditional_press_condition[j][k][0] == "Pressure" and conditional_press_direction[j][k][0] == 1 and sensor_press_read_press[j] > conditional_press_setpoint[j][k][0]) or (conditional_press_condition[j][k][0] == "Pressure" and conditional_press_direction[j][k][0] == -1 and sensor_press_read_press[j] < conditional_press_setpoint[j][k][0]) or (conditional_press_condition[j][k][0] == "Temperature" and conditional_press_direction[j][k][0] == 1 and sensor_press_read_temp_c[j] > conditional_press_setpoint[j][k][0]) or (conditional_press_condition[j][k][0] == "Temperature" and conditional_press_direction[j][k][0] == -1 and sensor_press_read_temp_c[j] < conditional_press_setpoint[j][k][0]):
                                if conditional_press_sel_relay[j][k][0]:
                                    if conditional_press_relay_state[j][k][0] == 1:
                                        if conditional_press_relay_seconds_on[j][k][0] > 0:
                                            logging.debug("[Conditional Press] Conditional statement %s True: Turn relay %s on for %s seconds", k + 1, conditional_press_relay[j][k][0], conditional_press_relay_seconds_on[j][k][0])
                                            rod = threading.Thread(target=relay_on_duration, args=(conditional_press_relay[j][k][0], conditional_press_relay_seconds_on[j][k][0], j, relay_trigger, relay_pin,))
                                            rod.start()
                                        else:
                                            relay_onoff(conditional_press_relay[j][k][0], 'on')
                                    elif conditional_press_relay_state[j][k][0] == 0:
                                        relay_onoff(conditional_press_relay[j][k][0], 'off')
                                if conditional_press_sel_command[j][k][0]:
                                    p = subprocess.Popen(conditional_press_do_command[j][k][0], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    output, errors = p.communicate()
                                    logging.debug("[Conditional Press] Conditional %s (%s) Press Sensor %s (%s) True: Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_press_name[j][k][0], conditional_press_do_command[j][k][0], output, errors)
                                if conditional_press_sel_notify[j][k][0] and conditional_press_time_notify[j][k][0] < time.time():
                                    logging.debug("[Conditional Press] Conditional %s (%s) Press Sensor %s (%s) True: Notify %s", j + 1, sensor_press_name[j], k + 1, conditional_press_name[j][k][0], conditional_press_do_notify[j][k][0])
                                    if conditional_press_condition[j][k][0] == "Pressure" and conditional_press_direction[j][k][0] == 1 and sensor_press_read_press[j] > conditional_press_setpoint[j][k][0]:
                                        message = "Conditional %s (%s) Press Sensor %s (%s) Pressure: %s kPa > %s kPa." % (j + 1, sensor_press_name[j], k + 1, conditional_press_name[j][k][0], sensor_press_read_press[j], conditional_press_setpoint[j][k][0])
                                    if conditional_press_condition[j][k][0] == "Pressure" and conditional_press_direction[j][k][0] == -1 and sensor_press_read_press[j] < conditional_press_setpoint[j][k][0]:
                                        message = "Conditional %s (%s) Press Sensor %s (%s) Pressure: %s kPa < %s kPa." % (j + 1, sensor_press_name[j], k + 1, conditional_press_name[j][k][0], sensor_press_read_press[j], conditional_press_setpoint[j][k][0])
                                    if conditional_press_condition[j][k][0] == "Temperature" and conditional_press_direction[j][k][0] == 1 and sensor_press_read_temp_c[j] > conditional_press_setpoint[j][k][0]:
                                        message = "Conditional %s (%s) Press Sensor %s (%s) Temperature: %s C > %s C." % (j + 1, sensor_press_name[j], k + 1, conditional_press_name[j][k][0], sensor_press_read_temp_c[j], conditional_press_setpoint[j][k][0])
                                    if conditional_press_condition[j][k][0] == "Temperature" and conditional_press_direction[j][k][0] == -1 and sensor_press_read_temp_c[j] < conditional_press_setpoint[j][k][0]:
                                        message = "Conditional %s (%s) Press Sensor %s (%s) Temperature: %s C < %s C." % (j + 1, sensor_press_name[j], k + 1, conditional_press_name[j][k][0], sensor_press_read_temp_c[j], conditional_press_setpoint[j][k][0])
                                    email(conditional_press_do_notify[j][k][0], message)
                                    conditional_press_time_notify[j][k][0] = time.time() + smtp_wait_time
                                elif conditional_press_sel_notify[j][k][0]:
                                    logging.debug("[Conditional Press] Conditional %s (%s) Press Sensor %s (%s) True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", j + 1, sensor_press_name[j], k + 1, conditional_press_name[j][k][0], conditional_press_do_notify[j][k][0], (smtp_wait_time - (smtp_wait_time - (conditional_press_time_notify[j][k][0] - time.time()))), smtp_wait_time)
                        else:
                            logging.warning("[Conditional Press] Could not read sensor %s, did not check conditional %s", j + 1, k + 1)
                        timerPressConditional[j][k] = time.time() + conditional_press_period[j][k][0]

        #
        # Check log size on tempfs every 10 minutes and back up if larger than maximum allowed
        #
        if time.time() > timerLogBackup and client_que != 'TerminateServer' and PID_change != 1:
            total_log_size = os.stat(daemon_log_file_tmp).st_size + os.stat(sensor_t_log_file_tmp).st_size + os.stat(sensor_ht_log_file_tmp).st_size + os.stat(sensor_co2_log_file_tmp).st_size + os.stat(sensor_press_log_file_tmp).st_size + os.stat(relay_log_file_tmp).st_size
            # Back up logs if their combined size is greater than 5 MB
            if total_log_size > 5000000:
                logging.debug("[Log Backup] Sum of log sizes = %s bytes > 5,000,000 bytes (5 MB). Backing up logs.", total_log_size)
                mycodoLog.Concatenate_Logs()
            elif timerLogBackupCount > 5:
                logging.debug("[Log Backup] 1-hour timer expired. Backing up logs.", total_log_size)
                mycodoLog.Concatenate_Logs()
                timerLogBackupCount = 0
            timerLogBackupCount += 1
            timerLogBackup = time.time() + 600

        #
        # Simple duration timers
        #
        if len(timer_id) != 0:
            for i in range(0, len(timer_id)):
                if timer_state[i] == 1 and time.time() > timer_time[i] and client_que != 'TerminateServer' and PID_change != 1:
                    logging.debug("[Timer Expiration] Timer %s: Turn Relay %s on for %s seconds, off %s seconds.", i, timer_relay[i], timer_duration_on[i], timer_duration_off[i])
                    rod = threading.Thread(target=relay_on_duration, args=(timer_relay[i], timer_duration_on[i], 0, relay_trigger, relay_pin,))
                    rod.start()
                    timer_time[i] = time.time() + timer_duration_on[i] + timer_duration_off[i]

        #
        # Stop/Start indevidual PID threads
        #
        if pid_t_temp_down:
            if pid_t_temp_active[pid_number] == 1:
                logging.info("[Daemon] Shutting Down Temperature PID Thread-T-T-%s", pid_number + 1)
                pid_t_temp_alive[pid_number] = 0
                while pid_t_temp_alive[pid_number] != 2:
                    time.sleep(0.1)
                pid_t_temp_alive[pid_number] = 1
                pid_t_temp_active[pid_number] = 0
            else:
                logging.warning("[Daemon] Cannot Shut Down Temperature PID Thread-T-T-%s: It isn't running.", pid_number + 1)
            pid_t_temp_down = 0
        if pid_t_temp_up:
            if pid_t_temp_active[pid_number] == 0:
                logging.info("[Daemon] Starting Temperature PID Thread-T-T-%s", pid_number + 1)
                rod = threading.Thread(target=t_sensor_temperature_monitor, args=('Thread-T-T-%d' % (int(pid_number) + 1), pid_number,))
                rod.start()
                pid_t_temp_active[pid_number] = 1
            else:
                logging.warning("[Daemon] Cannot Start Temperature PID Thread-T-T-%s: It's already running.", pid_number + 1)
            pid_t_temp_up = 0

        if pid_ht_temp_down:
            if pid_ht_temp_active[pid_number] == 1:
                logging.info("[Daemon] Shutting Down Temperature PID Thread-HT-T-%s", pid_number + 1)
                pid_ht_temp_alive[pid_number] = 0
                while pid_ht_temp_alive[pid_number] != 2:
                    time.sleep(0.1)
                pid_ht_temp_alive[pid_number] = 1
                pid_ht_temp_active[pid_number] = 0
            else:
                logging.warning("[Daemon] Cannot Shut Down Temperature PID Thread-HT-T-%s: It isn't running.", pid_number + 1)
            pid_ht_temp_down = 0
        if pid_ht_temp_up:
            if pid_ht_temp_active[pid_number] == 0:
                logging.info("[Daemon] Starting Temperature PID Thread-HT-T-%s", pid_number + 1)
                rod = threading.Thread(target=ht_sensor_temperature_monitor, args=('Thread-%d' % (int(pid_number) + 1), pid_number,))
                rod.start()
                pid_ht_temp_active[pid_number] = 1
            else:
                logging.warning("[Daemon] Cannot Start Temperature PID Thread-HT-T-%s: It's already running.", pid_number + 1)
            pid_ht_temp_up = 0

        if pid_ht_hum_down:
            if pid_ht_hum_active[pid_number] == 1:
                logging.info("[Daemon] Shutting Down Humidity PID Thread-HT-H-%s", pid_number + 1)
                pid_ht_hum_alive[pid_number] = 0
                while pid_ht_hum_alive[pid_number] != 2:
                    time.sleep(0.1)
                pid_ht_hum_alive[pid_number] = 1
                pid_ht_hum_active[pid_number] = 0
            else:
                logging.warning("[Daemon] Cannot Shut Down Humidity PID Thread-HT-H-%s: It isn't running.", pid_number + 1)
            pid_ht_hum_down = 0
        if pid_ht_hum_up:
            if pid_ht_hum_active[pid_number] == 0:
                logging.info("[Daemon] Starting Humidity PID Thread-HT-H-%s", pid_number + 1)
                rod = threading.Thread(target=ht_sensor_humidity_monitor, args=('Thread-%d' % (int(pid_number) + 1), pid_number,))
                rod.start()
                pid_ht_hum_active[pid_number] = 1
            else:
                logging.warning("[Daemon] Cannot Start Humidity PID Thread-HT-H-%s: It's already running.", pid_number + 1)
            pid_ht_hum_up = 0

        if pid_co2_down:
            if pid_co2_active[pid_number] == 1:
                logging.info("[Daemon] Shutting Down CO2 PID Thread-CO2-%s", pid_number + 1)
                pid_co2_alive[pid_number] = 0
                while pid_co2_alive[pid_number] != 2:
                    time.sleep(0.1)
                pid_co2_alive[pid_number] = 1
                pid_co2_active[pid_number] = 0
            else:
                logging.warning("[Daemon] Cannot Shut Down CO2 PID Thread-CO2-%s: It isn't running.", pid_number + 1)
            pid_co2_down = 0
        if pid_co2_up:
            if pid_co2_active[pid_number] == 0:
                logging.info("[Daemon] Starting CO2 PID Thread-CO2-%s", pid_number + 1)
                rod = threading.Thread(target=co2_monitor, args=('Thread-%d' % (int(pid_number) + 1), pid_number,))
                rod.start()
                pid_co2_active[pid_number] = 1
            else:
                logging.warning("[Daemon] Cannot Start CO2 PID Thread-CO2-%s: It's already running.", pid_number + 1)
            pid_co2_up = 0

        if pid_press_temp_down:
            if pid_press_temp_active[pid_number] == 1:
                logging.info("[Daemon] Shutting Down Pressure PID Thread-Press-T-%s", pid_number + 1)
                pid_press_temp_alive[pid_number] = 0
                while pid_press_temp_alive[pid_number] != 2:
                    time.sleep(0.1)
                pid_press_temp_alive[pid_number] = 1
                pid_press_temp_active[pid_number] = 0
            else:
                logging.warning("[Daemon] Cannot Shut Down Pressure PID Thread-Press-T-%s: It isn't running.", pid_number + 1)
            pid_press_temp_down = 0
        if pid_press_temp_up:
            if pid_press_temp_active[pid_number] == 0:
                logging.info("[Daemon] Starting Pressure PID Thread-Press-T-%s", pid_number + 1)
                rod = threading.Thread(target=press_sensor_temperature_monitor, args=('Thread-%d' % (int(pid_number) + 1), pid_number,))
                rod.start()
                pid_press_temp_active[pid_number] = 1
            else:
                logging.warning("[Daemon] Cannot Start Pressure PID Thread-Press-T-%s: It's already running.", pid_number + 1)
            pid_press_temp_up = 0

        if pid_press_press_down:
            if pid_press_press_active[pid_number] == 1:
                logging.info("[Daemon] Shutting Down Humidity PID Thread-Press-P-%s", pid_number + 1)
                pid_press_press_alive[pid_number] = 0
                while pid_press_press_alive[pid_number] != 2:
                    time.sleep(0.1)
                pid_press_press_alive[pid_number] = 1
                pid_press_press_active[pid_number] = 0
            else:
                logging.warning("[Daemon] Cannot Shut Down Humidity PID Thread-Press-P-%s: It isn't running.", pid_number + 1)
            pid_press_press_down = 0
        if pid_press_press_up:
            if pid_press_press_active[pid_number] == 0:
                logging.info("[Daemon] Starting Humidity PID Thread-Press-P-%s", pid_number + 1)
                rod = threading.Thread(target=press_sensor_pressure_monitor, args=('Thread-%d' % (int(pid_number) + 1), pid_number,))
                rod.start()
                pid_press_press_active[pid_number] = 1
            else:
                logging.warning("[Daemon] Cannot Start Humidity PID Thread-Press-P-%s: It's already running.", pid_number + 1)
            pid_press_press_up = 0

        time.sleep(0.25)


#################################################
#                  PID Control                  #
#################################################

# Temperature Sensor Temperature modulation by PID control
def t_sensor_temperature_monitor(ThreadName, sensor_id):
    global pid_t_temp_alive
    timerTemp = 0
    PIDTemp = 0
    logging.info("[PID T-Temperature-%s] Starting %s", sensor_id + 1, ThreadName)

    if pid_t_temp_relay_high[sensor_id]:
        relay_onoff(int(pid_t_temp_relay_high[sensor_id]), 'off')
    if pid_t_temp_relay_low[sensor_id]:
        relay_onoff(int(pid_t_temp_relay_low[sensor_id]), 'off')

    pid_temp = PID(pid_t_temp_p[sensor_id], pid_t_temp_i[sensor_id], pid_t_temp_d[sensor_id], Measure_interval=pid_t_temp_period[sensor_id])
    pid_temp.setPoint(pid_t_temp_set[sensor_id])

    while pid_t_temp_alive[sensor_id]:

        if pause_daemon:
            logging.debug("[PID T-Temperature-%s] Pausing Temp sensor read for SQL reload", sensor_id + 1)
            while pause_daemon:
                time.sleep(0.1)

        if ((pid_t_temp_set_dir[sensor_id] == 0 and pid_t_temp_relay_high[sensor_id] != 0 and pid_t_temp_relay_low[sensor_id] != 0) or (pid_t_temp_set_dir[sensor_id] == -1 and pid_t_temp_relay_high[sensor_id] != 0) or (pid_t_temp_set_dir[sensor_id] == 1 and pid_t_temp_relay_low[sensor_id] != 0)) and pid_t_temp_or[sensor_id] == 0 and pid_t_temp_down == 0 and sensor_t_activated[sensor_id] == 1:

            if time.time() > timerTemp:

                logging.debug("[PID T-Temperature-%s] Reading temperature...", sensor_id + 1)
                if read_t_sensor(sensor_id) is not None:

                    PIDTemp = pid_temp.update(float(sensor_t_read_temp_c[sensor_id]))
                    if sensor_t_read_temp_c[sensor_id] > pid_t_temp_set[sensor_id]:
                        logging.debug("[PID T-Temperature-%s] Temperature: %.1f°C now > %.1f°C set", sensor_id + 1, sensor_t_read_temp_c[sensor_id], pid_t_temp_set[sensor_id])
                    elif sensor_t_read_temp_c[sensor_id] < pid_t_temp_set[sensor_id]:
                        logging.debug("[PID T-Temperature-%s] Temperature: %.1f°C now < %.1f°C set", sensor_id + 1, sensor_t_read_temp_c[sensor_id], pid_t_temp_set[sensor_id])
                    else:
                        logging.debug("[PID T-Temperature-%s] Temperature: %.1f°C now = %.1f°C set", sensor_id + 1, sensor_t_read_temp_c[sensor_id], pid_t_temp_set[sensor_id])

                    if pid_t_temp_set_dir[sensor_id] > -1 and PIDTemp > 0:
                        if pid_t_temp_outmin_low[sensor_id] != 0 and PIDTemp < pid_t_temp_outmin_low[sensor_id]:
                            logging.debug("[PID T-Temperature-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDTemp, pid_t_temp_outmin_low[sensor_id])
                        elif pid_t_temp_outmax_low[sensor_id] != 0 and PIDTemp > pid_t_temp_outmax_low[sensor_id]:
                            logging.debug("[PID T-Temperature-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDTemp, pid_t_temp_outmax_low[sensor_id])
                            PIDTemp = pid_t_temp_outmax_low[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_t_temp_relay_low[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID T-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_t_temp_relay_low[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    elif pid_t_temp_set_dir[sensor_id] < 1 and PIDTemp < 0:
                        PIDTemp = abs(PIDTemp)
                        if pid_t_temp_outmin_high[sensor_id] != 0 and PIDTemp < pid_t_temp_outmin_high[sensor_id]:
                            logging.debug("[PID T-Temperature-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDTemp, pid_t_temp_outmin_high[sensor_id])
                        elif pid_t_temp_outmax_high[sensor_id] != 0 and PIDTemp > pid_t_temp_outmax_high[sensor_id]:
                            logging.debug("[PID T-Temperature-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDTemp, pid_t_temp_outmax_high[sensor_id])
                            PIDTemp = pid_t_temp_outmax_high[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_t_temp_relay_high[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID T-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_t_temp_relay_high[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    else:
                        logging.debug("[PID T-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                        PIDTemp = 0
                    timerTemp = time.time() + pid_t_temp_period[sensor_id]
                else:
                    logging.warning("[PID T-Temperature-%s] Could not read Temp sensor, not updating PID", sensor_id + 1)
        time.sleep(0.1)
    logging.info("[PID T-Temperature-%s] Shutting Down %s", sensor_id + 1, ThreadName)

    if pid_t_temp_relay_high[sensor_id]:
        relay_onoff(int(pid_t_temp_relay_high[sensor_id]), 'off')
    if pid_t_temp_relay_low[sensor_id]:
        relay_onoff(int(pid_t_temp_relay_low[sensor_id]), 'off')

    pid_t_temp_alive[sensor_id] = 2


# HT Sensor Temperature modulation by PID control
def ht_sensor_temperature_monitor(ThreadName, sensor_id):
    global pid_ht_temp_alive
    timerTemp = 0
    PIDTemp = 0
    logging.info("[PID HT-Temperature-%s] Starting %s", sensor_id + 1, ThreadName)

    if pid_ht_temp_relay_high[sensor_id]:
        relay_onoff(int(pid_ht_temp_relay_high[sensor_id]), 'off')
    if pid_ht_temp_relay_low[sensor_id]:
        relay_onoff(int(pid_ht_temp_relay_low[sensor_id]), 'off')

    pid_temp = PID(pid_ht_temp_p[sensor_id], pid_ht_temp_i[sensor_id], pid_ht_temp_d[sensor_id], Measure_interval=pid_ht_temp_period[sensor_id])
    pid_temp.setPoint(pid_ht_temp_set[sensor_id])

    while pid_ht_temp_alive[sensor_id]:

        if pause_daemon:
            logging.debug("[PID HT-Temperature-%s] Pausing Hum/Temp sensor read for SQL reload", sensor_id + 1)
            while pause_daemon:
                time.sleep(0.1)

        if ((pid_ht_temp_set_dir[sensor_id] == 0 and pid_ht_temp_relay_high[sensor_id] != 0 and pid_ht_temp_relay_low[sensor_id] != 0) or (pid_ht_temp_set_dir[sensor_id] == -1 and pid_ht_temp_relay_high[sensor_id] != 0) or (pid_ht_temp_set_dir[sensor_id] == 1 and pid_ht_temp_relay_low[sensor_id] != 0)) and pid_ht_temp_or[sensor_id] == 0 and pid_ht_temp_down == 0 and sensor_ht_activated[sensor_id] == 1:

            if time.time() > timerTemp:

                logging.debug("[PID HT-Temperature-%s] Reading temperature...", sensor_id + 1)
                if read_ht_sensor(sensor_id) is not None:

                    verify_check = {"temperature": 0, "humidity": 0}
                    if (sensor_ht_verify_temp_stop[sensor_id] or sensor_ht_verify_temp_notify[sensor_id]) and sensor_ht_verify_pin[sensor_id] != 0:
                        return_value, verify_check["temperature"], verify_check["humidity"] = verify_ht_sensor(sensor_id, sensor_ht_verify_pin[sensor_id])

                    if sensor_ht_verify_temp_stop[sensor_id] and verify_check["temperature"]:
                        logging.warning("[PID HT-Temperature-%s] Verification of Temperature failed, not updating PID or turning on relay", sensor_id + 1)
                        timerTemp = time.time() + pid_ht_temp_period[sensor_id]
                    else:
                        PIDTemp = pid_temp.update(float(sensor_ht_read_temp_c[sensor_id]))
                        if sensor_ht_read_temp_c[sensor_id] > pid_ht_temp_set[sensor_id]:
                            logging.debug("[PID HT-Temperature-%s] Temperature: %.1f°C now > %.1f°C set", sensor_id + 1, sensor_ht_read_temp_c[sensor_id], pid_ht_temp_set[sensor_id])
                        elif sensor_ht_read_temp_c[sensor_id] < pid_ht_temp_set[sensor_id]:
                            logging.debug("[PID HT-Temperature-%s] Temperature: %.1f°C now < %.1f°C set", sensor_id + 1, sensor_ht_read_temp_c[sensor_id], pid_ht_temp_set[sensor_id])
                        else:
                            logging.debug("[PID HT-Temperature-%s] Temperature: %.1f°C now = %.1f°C set", sensor_id + 1, sensor_ht_read_temp_c[sensor_id], pid_ht_temp_set[sensor_id])

                        if pid_ht_temp_set_dir[sensor_id] > -1 and PIDTemp > 0:
                            if pid_ht_temp_outmin_low[sensor_id] != 0 and PIDTemp < pid_ht_temp_outmin_low[sensor_id]:
                                logging.debug("[PID HT-Temperature-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDTemp, pid_ht_temp_outmin_low[sensor_id])
                            elif pid_ht_temp_outmax_low[sensor_id] != 0 and PIDTemp > pid_ht_temp_outmax_low[sensor_id]:
                                logging.debug("[PID HT-Temperature-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDTemp, pid_ht_temp_outmax_low[sensor_id])
                                PIDTemp = pid_ht_temp_outmax_low[sensor_id]
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_temp_relay_low[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()
                            else:
                                logging.debug("[PID HT-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_temp_relay_low[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()

                        elif pid_ht_temp_set_dir[sensor_id] < 1 and PIDTemp < 0:
                            PIDTemp = abs(PIDTemp)
                            if pid_ht_temp_outmin_high[sensor_id] != 0 and PIDTemp < pid_ht_temp_outmin_high[sensor_id]:
                                logging.debug("[PID HT-Temperature-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDTemp, pid_ht_temp_outmin_high[sensor_id])
                            elif pid_ht_temp_outmax_high[sensor_id] != 0 and PIDTemp > pid_ht_temp_outmax_high[sensor_id]:
                                logging.debug("[PID HT-Temperature-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDTemp, pid_ht_temp_outmax_high[sensor_id])
                                PIDTemp = pid_ht_temp_outmax_high[sensor_id]
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_temp_relay_high[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()
                            else:
                                logging.debug("[PID HT-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_temp_relay_high[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()

                        else:
                            logging.debug("[PID HT-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                            PIDTemp = 0
                        timerTemp = time.time() + pid_ht_temp_period[sensor_id]
                else:
                    logging.warning("[PID HT-Temperature-%s] Could not read Hum/Temp sensor, not updating PID", sensor_id + 1)

        time.sleep(0.1)
    logging.info("[PID HT-Temperature-%s] Shutting Down %s", sensor_id + 1, ThreadName)

    if pid_ht_temp_relay_high[sensor_id]:
        relay_onoff(int(pid_ht_temp_relay_high[sensor_id]), 'off')
    if pid_ht_temp_relay_low[sensor_id]:
        relay_onoff(int(pid_ht_temp_relay_low[sensor_id]), 'off')

    pid_ht_temp_alive[sensor_id] = 2


# HT Sensor Humidity modulation by PID control
def ht_sensor_humidity_monitor(ThreadName, sensor_id):
    global pid_ht_hum_alive
    timerHum = 0
    PIDHum = 0
    logging.info("[PID HT-Humidity-%s] Starting %s", sensor_id + 1, ThreadName)

    if pid_ht_hum_relay_high[sensor_id]:
        relay_onoff(int(pid_ht_hum_relay_high[sensor_id]), 'off')
    if pid_ht_hum_relay_low[sensor_id]:
        relay_onoff(int(pid_ht_hum_relay_low[sensor_id]), 'off')

    pid_hum = PID(pid_ht_hum_p[sensor_id], pid_ht_hum_i[sensor_id], pid_ht_hum_d[sensor_id], Measure_interval=pid_ht_hum_period[sensor_id])
    pid_hum.setPoint(pid_ht_hum_set[sensor_id])

    while pid_ht_hum_alive[sensor_id]:

        if pause_daemon:
            logging.debug("[PID HT-Humidity-%s] Pausing Hum/Temp sensor read for SQL reload", sensor_id + 1)
            while pause_daemon:
                time.sleep(0.1)

        if ((pid_ht_hum_set_dir[sensor_id] == 0 and pid_ht_hum_relay_high[sensor_id] != 0 and pid_ht_hum_relay_low[sensor_id] != 0) or (pid_ht_hum_set_dir[sensor_id] == -1 and pid_ht_hum_relay_high[sensor_id] != 0) or (pid_ht_hum_set_dir[sensor_id] == 1 and pid_ht_hum_relay_low[sensor_id] != 0)) and pid_ht_hum_or[sensor_id] == 0 and pid_ht_hum_down == 0 and sensor_ht_activated[sensor_id] == 1:

            if time.time() > timerHum:

                logging.debug("[PID HT-Humidity-%s] Reading humidity...", sensor_id + 1)
                if read_ht_sensor(sensor_id) is not None:

                    verify_check = {"temperature": 0, "humidity": 0}
                    if (sensor_ht_verify_hum_stop[sensor_id] or sensor_ht_verify_hum_notify[sensor_id]) and sensor_ht_verify_pin[sensor_id] != 0:
                        return_value, verify_check["temperature"], verify_check["humidity"] = verify_ht_sensor(sensor_id, sensor_ht_verify_pin[sensor_id])

                    if sensor_ht_verify_hum_stop[sensor_id] and verify_check["humidity"]:
                        logging.warning("[PID HT-Humidity-%s] Verification of Humidity failed, not updating PID or turning on relay", sensor_id + 1)
                        timerHum = time.time() + pid_ht_hum_period[sensor_id]
                    else:
                        PIDHum = pid_hum.update(float(sensor_ht_read_hum[sensor_id]))
                        if sensor_ht_read_hum[sensor_id] > pid_ht_hum_set[sensor_id]:
                            logging.debug("[PID HT-Humidity-%s] Humidity: %.1f%% now > %.1f%% set", sensor_id + 1, sensor_ht_read_hum[sensor_id], pid_ht_hum_set[sensor_id])
                        elif sensor_ht_read_hum[sensor_id] < pid_ht_hum_set[sensor_id]:
                            logging.debug("[PID HT-Humidity-%s] Humidity: %.1f%% now < %.1f%% set", sensor_id + 1, sensor_ht_read_hum[sensor_id], pid_ht_hum_set[sensor_id])
                        else:
                            logging.debug("[PID HT-Humidity-%s] Humidity: %.1f%% now = %.1f%% set", sensor_id + 1, sensor_ht_read_hum[sensor_id], pid_ht_hum_set[sensor_id])

                        if pid_ht_hum_set_dir[sensor_id] > -1 and PIDHum > 0:
                            if pid_ht_hum_outmin_low[sensor_id] != 0 and PIDHum < pid_ht_hum_outmin_low[sensor_id]:
                                logging.debug("[PID HT-Humidity-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDHum, pid_ht_hum_outmin_low[sensor_id])
                            elif pid_ht_hum_outmax_low[sensor_id] != 0 and PIDHum > pid_ht_hum_outmax_low[sensor_id]:
                                logging.debug("[PID HT-Humidity-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDHum, pid_ht_hum_outmax_low[sensor_id])
                                PIDHum = pid_ht_hum_outmax_low[sensor_id]
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_hum_relay_low[sensor_id], round(PIDHum, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()
                            else:
                                logging.debug("[PID HT-Humidity-%s] PID = %.1f (max disabled)", sensor_id + 1, PIDHum)
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_hum_relay_low[sensor_id], round(PIDHum, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()

                        elif pid_ht_hum_set_dir[sensor_id] < 1 and PIDHum < 0:
                            PIDHum = abs(PIDHum)
                            if pid_ht_hum_outmin_high[sensor_id] != 0 and PIDHum < pid_ht_hum_outmin_high[sensor_id]:
                                logging.debug("[PID HT-Humidity-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDHum, pid_ht_hum_outmin_high[sensor_id])
                            elif pid_ht_hum_outmax_high[sensor_id] != 0 and PIDHum > pid_ht_hum_outmax_high[sensor_id]:
                                logging.debug("[PID HT-Humidity-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDHum, pid_ht_hum_outmax_high[sensor_id])
                                PIDHum = pid_ht_hum_outmax_high[sensor_id]
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_hum_relay_high[sensor_id], round(PIDHum, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()
                            else:
                                logging.debug("[PID HT-Humidity-%s] PID = %.1f", sensor_id + 1, PIDHum)
                                rod = threading.Thread(target=relay_on_duration, args=(pid_ht_hum_relay_high[sensor_id], round(PIDHum, 2), sensor_id, relay_trigger, relay_pin,))
                                rod.start()

                        else:
                            logging.debug("[PID HT-Humidity-%s] PID = %.1f", sensor_id + 1, PIDHum)
                            PIDHum = 0
                        timerHum = time.time() + pid_ht_hum_period[sensor_id]
                else:
                    logging.warning("[PID HT-Humidity-%s] Could not read Hum/Temp sensor, not updating PID", sensor_id + 1)
        time.sleep(0.1)
    logging.info("[PID HT-Humidity-%s] Shutting Down %s", sensor_id + 1, ThreadName)

    if pid_ht_hum_relay_high[sensor_id]:
        relay_onoff(int(pid_ht_hum_relay_high[sensor_id]), 'off')
    if pid_ht_hum_relay_low[sensor_id]:
        relay_onoff(int(pid_ht_hum_relay_low[sensor_id]), 'off')

    pid_ht_hum_alive[sensor_id] = 2


# CO2 modulation by PID control
def co2_monitor(ThreadName, sensor_id):
    global pid_co2_alive
    timerCO2 = 0
    PIDCO2 = 0
    logging.info("[PID CO2-%s] Starting %s", sensor_id + 1, ThreadName)

    if pid_co2_relay_high[sensor_id]:
        relay_onoff(int(pid_co2_relay_high[sensor_id]), 'off')
    if pid_co2_relay_low[sensor_id]:
        relay_onoff(int(pid_co2_relay_low[sensor_id]), 'off')

    pid_co2 = PID(pid_co2_p[sensor_id], pid_co2_i[sensor_id], pid_co2_d[sensor_id], Measure_interval=pid_co2_period[sensor_id])
    pid_co2.setPoint(pid_co2_set[sensor_id])

    while pid_co2_alive[sensor_id]:

        if pause_daemon:
            logging.debug("[PID CO2-%s] Pausing CO2 sensor read for SQL reload", sensor_id + 1)
            while pause_daemon:
                time.sleep(0.1)

        if ((pid_co2_set_dir[sensor_id] == 0 and pid_co2_relay_high[sensor_id] != 0 and pid_co2_relay_low[sensor_id] != 0) or (pid_co2_set_dir[sensor_id] == -1 and pid_co2_relay_high[sensor_id] != 0) or (pid_co2_set_dir[sensor_id] == 1 and pid_co2_relay_low[sensor_id] != 0)) and pid_co2_or[sensor_id] == 0 and pid_co2_down == 0 and sensor_co2_activated[sensor_id] == 1:

            if time.time() > timerCO2:

                logging.debug("[PID CO2-%s] Reading temperature...", sensor_id + 1)
                if read_co2_sensor(sensor_id) is not None:

                    PIDCO2 = pid_co2.update(float(sensor_co2_read_co2[sensor_id]))
                    if sensor_co2_read_co2[sensor_id] > pid_co2_set[sensor_id]:
                        logging.debug("[PID CO2-%s] CO2: %.1f ppm > %.1f ppm set", sensor_id + 1, sensor_co2_read_co2[sensor_id], pid_co2_set[sensor_id])
                    elif sensor_co2_read_co2[sensor_id] < pid_co2_set[sensor_id]:
                        logging.debug("[PID CO2-%s] CO2: %.1f ppm < %.1f ppm set", sensor_id + 1, sensor_co2_read_co2[sensor_id], pid_co2_set[sensor_id])
                    else:
                        logging.debug("[PID CO2-%s] CO2: %.1f ppm now = %.1f ppm set", sensor_id + 1, sensor_co2_read_co2[sensor_id], pid_co2_set[sensor_id])

                    if pid_co2_set_dir[sensor_id] > -1 and PIDCO2 > 0:
                        if pid_co2_outmin_low[sensor_id] != 0 and PIDCO2 < pid_co2_outmin_low[sensor_id]:
                            logging.debug("[PID CO2-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDCO2, pid_co2_outmin_low[sensor_id])
                        elif pid_co2_outmax_low[sensor_id] != 0 and PIDCO2 > pid_co2_outmax_low[sensor_id]:
                            logging.debug("[PID CO2-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDCO2, pid_co2_outmax_low[sensor_id])
                            PIDCO2 = pid_co2_outmax_low[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_co2_relay_low[sensor_id], round(PIDCO2, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID CO2-%s] PID = %.1f", sensor_id + 1, PIDCO2)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_co2_relay_low[sensor_id], round(PIDCO2, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    elif pid_co2_set_dir[sensor_id] < 1 and PIDCO2 < 0:
                        PIDCO2 = abs(PIDCO2)
                        if pid_co2_outmin_high[sensor_id] != 0 and PIDCO2 < pid_co2_outmin_high[sensor_id]:
                            logging.debug("[PID CO2-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDCO2, pid_co2_outmin_high[sensor_id])
                        elif pid_co2_outmax_high[sensor_id] != 0 and PIDCO2 > pid_co2_outmax_high[sensor_id]:
                            logging.debug("[PID CO2-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDCO2, pid_co2_outmax_high[sensor_id])
                            PIDCO2 = pid_co2_outmax_high[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_co2_relay_high[sensor_id], round(PIDCO2, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID CO2-%s] PID = %.1f", sensor_id + 1, PIDCO2)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_co2_relay_high[sensor_id], round(PIDCO2, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    else:
                        logging.debug("[PID CO2-%s] PID = %.1f", sensor_id + 1, PIDCO2)
                        PIDCO2 = 0
                    timerCO2 = time.time() + pid_co2_period[sensor_id]
                else:
                    logging.warning("[PID CO2-%s] Could not read CO2 sensor, not updating PID", sensor_id + 1)
        time.sleep(0.1)
    logging.info("[PID CO2-%s] Shutting Down %s", sensor_id + 1, ThreadName)

    if pid_co2_relay_high[sensor_id]:
        relay_onoff(int(pid_co2_relay_high[sensor_id]), 'off')
    if pid_co2_relay_low[sensor_id]:
        relay_onoff(int(pid_co2_relay_low[sensor_id]), 'off')

    pid_co2_alive[sensor_id] = 2


# Press Sensor Temperature modulation by PID control
def press_sensor_temperature_monitor(ThreadName, sensor_id):
    global pid_press_temp_alive
    timerTemp = 0
    PIDTemp = 0
    logging.info("[PID Press-Temperature-%s] Starting %s", sensor_id + 1, ThreadName)

    if pid_press_temp_relay_high[sensor_id]:
        relay_onoff(int(pid_press_temp_relay_high[sensor_id]), 'off')
    if pid_press_temp_relay_low[sensor_id]:
        relay_onoff(int(pid_press_temp_relay_low[sensor_id]), 'off')

    pid_temp = PID(pid_press_temp_p[sensor_id], pid_press_temp_i[sensor_id], pid_press_temp_d[sensor_id], Measure_interval=pid_press_temp_period[sensor_id])
    pid_temp.setPoint(pid_press_temp_set[sensor_id])

    while pid_press_temp_alive[sensor_id]:

        if pause_daemon:
            logging.debug("[PID Press-Temperature-%s] Pausing Press/Temp sensor read for SQL reload", sensor_id + 1)
            while pause_daemon:
                time.sleep(0.1)

        if ((pid_press_temp_set_dir[sensor_id] == 0 and pid_press_temp_relay_high[sensor_id] != 0 and pid_press_temp_relay_low[sensor_id] != 0) or (pid_press_temp_set_dir[sensor_id] == -1 and pid_press_temp_relay_high[sensor_id] != 0) or (pid_press_temp_set_dir[sensor_id] == 1 and pid_press_temp_relay_low[sensor_id] != 0)) and pid_press_temp_or[sensor_id] == 0 and pid_press_temp_down == 0 and sensor_ht_activated[sensor_id] == 1:

            if time.time() > timerTemp:

                logging.debug("[PID Press-Temperature-%s] Reading temperature...", sensor_id + 1)
                if read_press_sensor(sensor_id) is not None:

                    PIDTemp = pid_temp.update(float(sensor_ht_read_temp_c[sensor_id]))
                    if sensor_ht_read_temp_c[sensor_id] > pid_press_temp_set[sensor_id]:
                        logging.debug("[PID Press-Temperature-%s] Temperature: %.1f°C now > %.1f°C set", sensor_id + 1, sensor_ht_read_temp_c[sensor_id], pid_press_temp_set[sensor_id])
                    elif sensor_ht_read_temp_c[sensor_id] < pid_press_temp_set[sensor_id]:
                        logging.debug("[PID Press-Temperature-%s] Temperature: %.1f°C now < %.1f°C set", sensor_id + 1, sensor_ht_read_temp_c[sensor_id], pid_press_temp_set[sensor_id])
                    else:
                        logging.debug("[PID Press-Temperature-%s] Temperature: %.1f°C now = %.1f°C set", sensor_id + 1, sensor_ht_read_temp_c[sensor_id], pid_press_temp_set[sensor_id])

                    if pid_press_temp_set_dir[sensor_id] > -1 and PIDTemp > 0:
                        if pid_press_temp_outmin_low[sensor_id] != 0 and PIDTemp < pid_press_temp_outmin_low[sensor_id]:
                            logging.debug("[PID Press-Temperature-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDTemp, pid_press_temp_outmin_low[sensor_id])
                        elif pid_press_temp_outmax_low[sensor_id] != 0 and PIDTemp > pid_press_temp_outmax_low[sensor_id]:
                            logging.debug("[PID Press-Temperature-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDTemp, pid_press_temp_outmax_low[sensor_id])
                            PIDTemp = pid_press_temp_outmax_low[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_temp_relay_low[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID Press-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_temp_relay_low[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    elif pid_press_temp_set_dir[sensor_id] < 1 and PIDTemp < 0:
                        PIDTemp = abs(PIDTemp)
                        if pid_press_temp_outmin_high[sensor_id] != 0 and PIDTemp < pid_press_temp_outmin_high[sensor_id]:
                            logging.debug("[PID Press-Temperature-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDTemp, pid_press_temp_outmin_high[sensor_id])
                        elif pid_press_temp_outmax_high[sensor_id] != 0 and PIDTemp > pid_press_temp_outmax_high[sensor_id]:
                            logging.debug("[PID Press-Temperature-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDTemp, pid_press_temp_outmax_high[sensor_id])
                            PIDTemp = pid_press_temp_outmax_high[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_temp_relay_high[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID Press-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_temp_relay_high[sensor_id], round(PIDTemp, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    else:
                        logging.debug("[PID Press-Temperature-%s] PID = %.1f", sensor_id + 1, PIDTemp)
                        PIDTemp = 0
                    timerTemp = time.time() + pid_press_temp_period[sensor_id]
                else:
                    logging.warning("[PID Press-Temperature-%s] Could not read Press/Temp sensor, not updating PID", sensor_id + 1)
        time.sleep(0.1)
    logging.info("[PID Press-Temperature-%s] Shutting Down %s", sensor_id + 1, ThreadName)

    if pid_press_temp_relay_high[sensor_id]:
        relay_onoff(int(pid_press_temp_relay_high[sensor_id]), 'off')
    if pid_press_temp_relay_low[sensor_id]:
        relay_onoff(int(pid_press_temp_relay_low[sensor_id]), 'off')

    pid_press_temp_alive[sensor_id] = 2


# Press Sensor Pressure modulation by PID control
def press_sensor_pressure_monitor(ThreadName, sensor_id):
    global pid_press_press_alive
    timerPress = 0
    PIDPress = 0
    logging.info("[PID Press-Pressure-%s] Starting %s", sensor_id + 1, ThreadName)

    if pid_press_press_relay_high[sensor_id]:
        relay_onoff(int(pid_press_press_relay_high[sensor_id]), 'off')
    if pid_press_press_relay_low[sensor_id]:
        relay_onoff(int(pid_press_press_relay_low[sensor_id]), 'off')

    pid_press = PID(pid_press_press_p[sensor_id], pid_press_press_i[sensor_id], pid_press_press_d[sensor_id], Measure_interval=pid_press_press_period[sensor_id])
    pid_press.setPoint(pid_press_press_set[sensor_id])

    while pid_press_press_alive[sensor_id]:

        if pause_daemon:
            logging.debug("[PID Press-Pressure-%s] Pausing Press/Temp sensor read for SQL reload", sensor_id + 1)
            while pause_daemon:
                time.sleep(0.1)

        if ((pid_press_press_set_dir[sensor_id] == 0 and pid_press_press_relay_high[sensor_id] != 0 and pid_press_press_relay_low[sensor_id] != 0) or (pid_press_press_set_dir[sensor_id] == -1 and pid_press_press_relay_high[sensor_id] != 0) or (pid_press_press_set_dir[sensor_id] == 1 and pid_press_press_relay_low[sensor_id] != 0)) and pid_press_press_or[sensor_id] == 0 and pid_press_press_down == 0 and sensor_press_activated[sensor_id] == 1:

            if time.time() > timerPress:

                logging.debug("[PID Press-Pressure-%s] Reading pressure...", sensor_id + 1)
                if read_press_sensor(sensor_id) is not None:

                    PIDPress = pid_press.update(float(sensor_press_read_press[sensor_id]))
                    if sensor_press_read_press[sensor_id] > pid_press_press_set[sensor_id]:
                        logging.debug("[PID Press-Pressure-%s] Pressure: %.1f%% now > %.1fPa set", sensor_id + 1, sensor_press_read_press[sensor_id], pid_press_press_set[sensor_id])
                    elif sensor_press_read_press[sensor_id] < pid_press_press_set[sensor_id]:
                        logging.debug("[PID Press-Pressure-%s] Pressure: %.1f%% now < %.1fPa set", sensor_id + 1, sensor_press_read_press[sensor_id], pid_press_press_set[sensor_id])
                    else:
                        logging.debug("[PID Press-Pressure-%s] Pressure: %.1f%% now = %.1fPa set", sensor_id + 1, sensor_press_read_press[sensor_id], pid_press_press_set[sensor_id])

                    if pid_press_press_set_dir[sensor_id] > -1 and PIDPress > 0:
                        if pid_press_press_outmin_low[sensor_id] != 0 and PIDPress < pid_press_press_outmin_low[sensor_id]:
                            logging.debug("[PID Press-Pressure-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDPress, pid_press_press_outmin_low[sensor_id])
                        elif pid_press_press_outmax_low[sensor_id] != 0 and PIDPress > pid_press_press_outmax_low[sensor_id]:
                            logging.debug("[PID Press-Pressure-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDPress, pid_press_press_outmax_low[sensor_id])
                            PIDPress = pid_press_press_outmax_low[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_press_relay_low[sensor_id], round(PIDPress, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID Press-Pressure-%s] PID = %.1f", sensor_id + 1, PIDPress)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_press_relay_low[sensor_id], round(PIDPress, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    elif pid_press_press_set_dir[sensor_id] < 1 and PIDPress < 0:
                        PIDPress = abs(PIDPress)
                        if pid_press_press_outmin_high[sensor_id] != 0 and PIDPress < pid_press_press_outmin_high[sensor_id]:
                            logging.debug("[PID Press-Pressure-%s] PID = %.1f (min enabled, %s, not turning on)", sensor_id + 1, PIDPress, pid_press_press_outmin_high[sensor_id])
                        elif pid_press_press_outmax_high[sensor_id] != 0 and PIDPress > pid_press_press_outmax_high[sensor_id]:
                            logging.debug("[PID Press-Pressure-%s] PID = %.1f (max enabled, %s)", sensor_id + 1, PIDPress, pid_press_press_outmax_high[sensor_id])
                            PIDPress = pid_press_press_outmax_high[sensor_id]
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_press_relay_high[sensor_id], round(PIDPress, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()
                        else:
                            logging.debug("[PID Press-Pressure-%s] PID = %.1f", sensor_id + 1, PIDPress)
                            rod = threading.Thread(target=relay_on_duration, args=(pid_press_press_relay_high[sensor_id], round(PIDPress, 2), sensor_id, relay_trigger, relay_pin,))
                            rod.start()

                    else:
                        logging.debug("[PID Press-Pressure-%s] PID = %.1f", sensor_id + 1, PIDPress)
                        PIDPress = 0
                    timerPress = time.time() + pid_press_press_period[sensor_id]
                else:
                    logging.warning("[PID Press-Pressure-%s] Could not read Press/Temp sensor, not updating PID", sensor_id + 1)
        time.sleep(0.1)
    logging.info("[PID Press-Pressure-%s] Shutting Down %s", sensor_id + 1, ThreadName)

    if pid_press_press_relay_high[sensor_id]:
        relay_onoff(int(pid_press_press_relay_high[sensor_id]), 'off')
    if pid_press_press_relay_low[sensor_id]:
        relay_onoff(int(pid_press_press_relay_low[sensor_id]), 'off')

    pid_press_press_alive[sensor_id] = 2


def PID_start(type_, number):
    global pid_number
    pid_number = number
    if type_ == 'TTemp':
        global pid_t_temp_up
        pid_t_temp_up = 1
        while pid_t_temp_up:
            time.sleep(0.1)
    if type_ == 'HTTemp':
        global pid_ht_temp_up
        pid_ht_temp_up = 1
        while pid_ht_temp_up:
            time.sleep(0.1)
    elif type_ == 'HTHum':
        global pid_ht_hum_up
        pid_ht_hum_up = 1
        while pid_ht_hum_up:
            time.sleep(0.1)
    elif type_ == 'CO2':
        global pid_co2_up
        pid_co2_up = 1
        while pid_co2_up:
            time.sleep(0.1)
    if type_ == 'PressTemp':
        global pid_press_temp_up
        pid_press_temp_up = 1
        while pid_press_temp_up:
            time.sleep(0.1)
    elif type_ == 'PressPress':
        global pid_press_press_up
        pid_press_press_up = 1
        while pid_press_press_up:
            time.sleep(0.1)
    return 1


def PID_stop(type_, number):
    global pid_number
    pid_number = number
    if type_ == 'TTemp':
        global pid_t_temp_down
        pid_t_temp_down = 1
        while pid_t_temp_down == 1:
            time.sleep(0.1)
    if type_ == 'HTTemp':
        global pid_ht_temp_down
        pid_ht_temp_down = 1
        while pid_ht_temp_down == 1:
            time.sleep(0.1)
    if type_ == 'HTHum':
        global pid_ht_hum_down
        pid_ht_hum_down = 1
        while pid_ht_hum_down == 1:
            time.sleep(0.1)
    if type_ == 'CO2':
        global pid_co2_down
        pid_co2_down = 1
        while pid_co2_down == 1:
            time.sleep(0.1)
    if type_ == 'PressTemp':
        global pid_press_temp_down
        pid_press_temp_down = 1
        while pid_press_temp_down == 1:
            time.sleep(0.1)
    if type_ == 'PressPress':
        global pid_press_press_down
        pid_press_press_down = 1
        while pid_press_press_down == 1:
            time.sleep(0.1)
    return 1


#################################################
#                Sensor Reading                 #
#################################################

# Read the temperature and humidity from sensor
def read_t_sensor(sensor_id):
    global sensor_t_read_temp_c
    tempc = None
    tempc2 = None
    t_read_tries = 5

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_t_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Read T Sensor-%s] Acquiring Lock: %s", sensor_id + 1, lock.path)
            lock.acquire(timeout=90)    # wait up to 60 seconds
        except:
            logging.warning("[Read T Sensor-%s] Breaking Lock to Acquire: %s", sensor_id + 1, lock.path)
            lock.break_lock()
            lock.acquire()
    logging.debug("[Read T Sensor-%s] Gained lock: %s", sensor_id + 1, lock.path)
    timerT = 0
    if sensor_t_premeasure_relay[sensor_id] and sensor_t_premeasure_dur[sensor_id]:
        timerT = time.time() + sensor_t_premeasure_dur[sensor_id]
        rod = threading.Thread(target=relay_on_duration, args=(sensor_t_premeasure_relay[sensor_id], sensor_t_premeasure_dur[sensor_id], sensor_id, relay_trigger, relay_pin,))
        rod.start()
        while timerT > time.time() and client_que != 'TerminateServer':
            if pause_daemon:
                relay_onoff(sensor_t_premeasure_relay[sensor_id], 'off')
                break
            time.sleep(0.25)

    for r in range(0, t_read_tries):  # Multiple attempts to get similar consecutive readings
        if not pid_t_temp_alive[sensor_id] or client_que == 'TerminateServer' or pause_daemon:
            break
        logging.debug("[Read T Sensor-%s] Taking first Temperature/Humidity reading", sensor_id + 1)
        for i in range(0, t_read_tries):
            if pid_t_temp_alive[sensor_id] and client_que != 'TerminateServer' and pause_daemon != 1:
                tempc2 = read_t(sensor_id, sensor_t_device[sensor_id], sensor_t_pin[sensor_id])
                if tempc2 is not None:
                    break
            else:
                break

        if tempc2 is None:
            logging.warning("[Read T Sensor-%s] Could not read first Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read T Sensor-%s] %.1f°C", sensor_id, tempc2)
            logging.debug("[Read T Sensor-%s] Taking second Temperature reading", sensor_id + 1)

        for i in range(0, t_read_tries):  # Multiple attempts to get first reading
            if pid_t_temp_alive[sensor_id] and client_que != 'TerminateServer' and pause_daemon != 1:
                tempc = read_t(sensor_id, sensor_t_device[sensor_id], sensor_t_pin[sensor_id])
                if tempc is not None:
                    break
            else:
                break

        if tempc is None:
            logging.warning("[Read T Sensor-%s] Could not read second Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read T Sensor-%s] %.1f°C", sensor_id, tempc)
            logging.debug("[Read T Sensor-%s] Differences: %.1f°C", sensor_id + 1, abs(tempc2 - tempc))

            if abs(tempc2 - tempc) > 1:
                tempc2 = tempc
                logging.debug("[Read T Sensor-%s] Successive readings > 1 difference: Rereading", sensor_id + 1)
            else:
                logging.debug("[Read T Sensor-%s] Successive readings < 1 difference: keeping.", sensor_id + 1)
                temperature_f = float(tempc) * 9.0 / 5.0 + 32.0
                logging.debug("[Read T Sensor-%s] Temp: %.1f°C", sensor_id + 1, tempc)
                sensor_t_read_temp_c[sensor_id] = tempc
                logging.debug("[Read T Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
                lock.release()
                return tempc
    else:
        logging.warning("[Read T Sensor-%s] Could not get two consecutive Temp measurements that were consistent.", sensor_id + 1)
    logging.debug("[Read T Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
    lock.release()
    return None


# Read the temperature and humidity from sensor
def read_ht_sensor(sensor_id):
    global sensor_ht_read_temp_c
    global sensor_ht_read_hum
    global sensor_ht_dewpt_c
    tempc = None
    tempc2 = None
    humidity = None
    humidity2 = None
    ht_read_tries = 5

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_ht_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Read HT Sensor-%s] Acquiring Lock: %s", sensor_id + 1, lock.path)
            lock.acquire(timeout=90)    # wait up to 60 seconds
        except:
            logging.warning("[Read HT Sensor-%s] Breaking Lock to Acquire: %s", sensor_id + 1, lock.path)
            lock.break_lock()
            lock.acquire()
    logging.debug("[Read HT Sensor-%s] Gained lock: %s", sensor_id + 1, lock.path)
    timerHT = 0
    if sensor_ht_premeasure_relay[sensor_id] and sensor_ht_premeasure_dur[sensor_id]:
        timerHT = time.time() + sensor_ht_premeasure_dur[sensor_id]
        rod = threading.Thread(target=relay_on_duration, args=(sensor_ht_premeasure_relay[sensor_id], sensor_ht_premeasure_dur[sensor_id], sensor_id, relay_trigger, relay_pin,))
        rod.start()
        while (timerHT > time.time()) and client_que != 'TerminateServer':
            if pause_daemon:
                relay_onoff(sensor_ht_premeasure_relay[sensor_id], 'off')
                break
            time.sleep(0.25)

    for r in range(0, ht_read_tries):  # Multiple attempts to get similar consecutive readings
        if (not pid_ht_temp_alive[sensor_id] and not pid_ht_hum_alive[sensor_id]) or client_que == 'TerminateServer' or pause_daemon:
            break

        logging.debug("[Read HT Sensor-%s] Taking first Temperature/Humidity reading", sensor_id + 1)

        for i in range(0, ht_read_tries):
            if (pid_ht_temp_alive[sensor_id] or pid_ht_hum_alive[sensor_id]) and client_que != 'TerminateServer' and pause_daemon != 1:
                humidity2, tempc2 = read_ht(sensor_id, sensor_ht_device[sensor_id], sensor_ht_pin[sensor_id])
                if humidity2 is not None and tempc2 is not None:
                    break
            else:
                break

        if humidity2 is None or tempc2 is None:
            logging.warning("[Read HT Sensor-%s] Could not read first Hum/Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read HT Sensor-%s] %.1f°C, %.1f%%", sensor_id + 1, tempc2, humidity2)
            logging.debug("[Read HT Sensor-%s] Taking second Temperature/Humidity reading", sensor_id + 1)
        
        for i in range(0, ht_read_tries):  # Multiple attempts to get first reading
            if (pid_ht_temp_alive[sensor_id] or pid_ht_hum_alive[sensor_id]) and client_que != 'TerminateServer' and pause_daemon != 1:
                humidity, tempc = read_ht(sensor_id, sensor_ht_device[sensor_id], sensor_ht_pin[sensor_id])
                if humidity is not None and tempc is not None:
                    break
            else:
                break

        if humidity is None or tempc is None:
            logging.warning("[Read HT Sensor-%s] Could not read second Hum/Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read HT Sensor-%s] %.1f°C, %.1f%%", sensor_id + 1, tempc, humidity)
            logging.debug("[Read HT Sensor-%s] Differences: %.1f°C, %.1f%%", sensor_id + 1, abs(tempc2 - tempc), abs(humidity2 - humidity))

            if abs(tempc2 - tempc) > 1 or abs(humidity2 - humidity) > 1:
                tempc2 = tempc
                humidity2 = humidity
                logging.debug("[Read HT Sensor-%s] Successive readings > 1 difference: Rereading", sensor_id + 1)
            else:
                logging.debug("[Read HT Sensor-%s] Successive readings < 1 difference: keeping.", sensor_id + 1)
                temperature_f = float(tempc) * 9.0 / 5.0 + 32.0
                sensor_ht_dewpt_c[sensor_id] = tempc - ((100 - humidity) / 5)
                #sensor_ht_dewpt_f[sensor] = sensor_ht_dewpt_c[sensor] * 9 / 5 + 32
                #sensor_ht_heatindex_f = -42.379 + 2.04901523 * temperature_f + 10.14333127 * sensor_ht_read_hum - 0.22475541 * temperature_f * sensor_ht_read_hum - 6.83783 * 10**-3 * temperature_f**2 - 5.481717 * 10**-2 * sensor_ht_read_hum**2 + 1.22874 * 10**-3 * temperature_f**2 * sensor_ht_read_hum + 8.5282 * 10**-4 * temperature_f * sensor_ht_read_hum**2 - 1.99 * 10**-6 * temperature_f**2 * sensor_ht_read_hum**2
                #sensor_ht_heatindex_c[sensor] = (heatindexf - 32) * (5 / 9)
                logging.debug("[Read HT Sensor-%s] Temp: %.1f°C, Hum: %.1f%%, DP: %.1f°C", sensor_id + 1, tempc, humidity, sensor_ht_dewpt_c[sensor_id])
                sensor_ht_read_hum[sensor_id] = humidity
                sensor_ht_read_temp_c[sensor_id] = tempc
                logging.debug("[Read HT Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
                lock.release()
                return humidity, tempc

    logging.warning("[Read HT Sensor-%s] Could not get two consecutive Hum/Temp measurements that were consistent.", sensor_id + 1)
    logging.debug("[Read HT Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
    lock.release()
    return None


# Verify the temperature and/or humidity from second sensor
def verify_ht_sensor(sensor_id, GPIO):
    global sensor_ht_verify_read_temp_c
    global sensor_ht_verify_read_hum
    tempc = None
    tempc2 = None
    humidity = None
    humidity2 = None
    ht_read_tries = 5

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_ht_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Verify HT Sensor-%s] Acquiring Lock: %s", sensor_id + 1, lock.path)
            lock.acquire(timeout=90)    # wait up to 60 seconds
        except:
            logging.warning("[Verify HT Sensor-%s] Breaking Lock to Acquire: %s", sensor_id + 1, lock.path)
            lock.break_lock()
            lock.acquire()
    logging.debug("[Verify HT Sensor-%s] Gained lock: %s", sensor_id + 1, lock.path)
    timerHT = 0
    if sensor_ht_premeasure_relay[sensor_id] and sensor_ht_premeasure_dur[sensor_id]:
        timerHT = time.time() + sensor_ht_premeasure_dur[sensor_id]
        rod = threading.Thread(target=relay_on_duration, args=(sensor_ht_premeasure_relay[sensor_id], sensor_ht_premeasure_dur[sensor_id], sensor_id, relay_trigger, relay_pin,))
        rod.start()
        while (timerHT > time.time()) and client_que != 'TerminateServer':
            if pause_daemon:
                relay_onoff(sensor_ht_premeasure_relay[sensor_id], 'off')
                break
            time.sleep(0.25)

    for r in range(0, ht_read_tries):  # Multiple attempts to get similar consecutive readings
        if (not pid_ht_temp_alive[sensor_id] and not pid_ht_hum_alive[sensor_id]) or client_que == 'TerminateServer' or pause_daemon:
            break

        logging.debug("[Verify HT Sensor-%s] Taking first Temperature/Humidity reading", sensor_id + 1)

        for i in range(0, ht_read_tries):
            if (pid_ht_temp_alive[sensor_id] or pid_ht_hum_alive[sensor_id]) and client_que != 'TerminateServer' and pause_daemon != 1:
                humidity2, tempc2 = read_ht(sensor_id, sensor_ht_device[sensor_id], GPIO)
                if humidity2 is not None and tempc2 is not None:
                    break
            else:
                break

        if humidity2 is None or tempc2 is None:
            logging.warning("[Verify HT Sensor-%s] Could not read first Hum/Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Verify HT Sensor-%s] %.1f°C, %.1f%%", sensor_id + 1, tempc2, humidity2)
            logging.debug("[Verify HT Sensor-%s] Taking second Temperature/Humidity reading", sensor_id + 1)
        
        for i in range(0, ht_read_tries):  # Multiple attempts to get first reading
            if (pid_ht_temp_alive[sensor_id] or pid_ht_hum_alive[sensor_id]) and client_que != 'TerminateServer' and pause_daemon != 1:
                humidity, tempc = read_ht(sensor_id, sensor_ht_device[sensor_id], GPIO)
                if humidity is not None and tempc is not None:
                    break
            else:
                break

        if humidity is None or tempc is None:
            logging.warning("[Verify HT Sensor-%s] Could not read second Hum/Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Verify HT Sensor-%s] %.1f°C, %.1f%%", sensor_id + 1, tempc, humidity)
            logging.debug("[Verify HT Sensor-%s] Differences: %.1f°C, %.1f%%", sensor_id + 1, abs(tempc2 - tempc), abs(humidity2 - humidity))

            if abs(tempc2 - tempc) > 1 or abs(humidity2 - humidity) > 1:
                tempc2 = tempc
                humidity2 = humidity
                logging.debug("[Verify HT Sensor-%s] Successive readings > 1 difference: Rereading", sensor_id + 1)
            else:
                logging.debug("[Verify HT Sensor-%s] Successive readings < 1 difference: keeping.", sensor_id + 1)
                temperature_f = float(tempc) * 9.0 / 5.0 + 32.0
                logging.debug("[Verify HT Sensor-%s] Temp: %.1f°C, Hum: %.1f%%", sensor_id + 1, tempc, humidity)
                sensor_ht_verify_read_hum = humidity
                sensor_ht_verify_read_temp_c = tempc
                logging.debug("[Verify HT Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
                lock.release()

                verify_check = {"temperature": 0, "humidity": 0}
                if abs(tempc - sensor_ht_read_temp_c[sensor_id]) > sensor_ht_verify_temp[sensor_id]:
                    verify_check["temperature"] = 1
                if abs(humidity - sensor_ht_read_hum[sensor_id]) > sensor_ht_verify_hum[sensor_id]:
                    verify_check["humidity"] = 1

                if verify_check["temperature"] and verify_check["humidity"]:
                    message = "[Verify HT Sensor-%s] (%s) Temperature difference (%.1f C) greater than set (%.1f C) and Humidity difference (%.1f%%) greater than set (%.1f%%)" % (sensor_id + 1, sensor_ht_name[sensor_id], abs(tempc - sensor_ht_read_temp_c[sensor_id]), sensor_ht_verify_temp[sensor_id], abs(humidity - sensor_ht_read_hum[sensor_id]), sensor_ht_verify_hum[sensor_id])
                elif verify_check["temperature"] and not verify_check["humidity"]:
                    message = "[Verify HT Sensor-%s] (%s) Temperature difference (%.1f C) greater than set (%.1f C)" % (sensor_id + 1, sensor_ht_name[sensor_id], abs(tempc - sensor_ht_read_temp_c[sensor_id]), sensor_ht_verify_temp[sensor_id])
                elif verify_check["humidity"] and not verify_check["temperature"]:
                    message = "[Verify HT Sensor-%s] (%s) Humidity difference (%.1f%%) greater than set (%.1f%%)" % (sensor_id + 1, sensor_ht_name[sensor_id], abs(humidity - sensor_ht_read_hum[sensor_id]), sensor_ht_verify_hum[sensor_id])

                if verify_check["temperature"] or verify_check["humidity"]:
                    if ((sensor_ht_verify_temp_notify[sensor_id] and sensor_ht_verify_hum_notify[sensor_id]) and (verify_check["temperature"] and verify_check["humidity"])) or (sensor_ht_verify_temp_notify[sensor_id] and verify_check["temperature"]) or (sensor_ht_verify_hum_notify[sensor_id] and verify_check["humidity"]):
                        email(sensor_ht_verify_email[sensor_id], message)
                    logging.warning(message)
                    return 2, verify_check["temperature"], verify_check["humidity"]
                else:
                    logging.debug("[Verify HT Sensor-%s] Both differences within range: %.1f°C <= %.1f°C set, %.1f%% <= %.1f%% set", sensor_id + 1, abs(tempc - sensor_ht_read_temp_c[sensor_id]), sensor_ht_verify_temp[sensor_id], abs(humidity - sensor_ht_read_hum[sensor_id]), sensor_ht_verify_hum[sensor_id])
                    return 1, verify_check["temperature"], verify_check["humidity"]
                    
    logging.warning("[Verify HT Sensor-%s] Could not get two consecutive Hum/Temp measurements that were consistent.", sensor_id + 1)
    logging.debug("[Verify HT Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
    lock.release()
    return 0


# Read CO2 sensor
def read_co2_sensor(sensor_id):
    global sensor_co2_read_co2
    co2 = None
    co22 = None
    co2_read_tries = 5

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_co2_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Read CO2 Sensor-%s] Acquiring Lock: %s", sensor_id + 1, lock.path)
            lock.acquire(timeout=90)    # wait up to 60 seconds
        except:
            logging.warning("[Read CO2 Sensor-%s] Breaking Lock to Acquire: %s", sensor_id + 1, lock.path)
            lock.break_lock()
            lock.acquire()
    logging.debug("[Read CO2 Sensor-%s] Gained lock: %s", sensor_id + 1, lock.path)
    timerCO2 = 0
    if sensor_co2_premeasure_relay[sensor_id] and sensor_co2_premeasure_dur[sensor_id]:
        timerCO2 = time.time() + sensor_co2_premeasure_dur[sensor_id]
        rod = threading.Thread(target=relay_on_duration, args=(sensor_co2_premeasure_relay[sensor_id], sensor_co2_premeasure_dur[sensor_id], sensor_id, relay_trigger, relay_pin,))
        rod.start()
        while (timerCO2 > time.time()) and client_que != 'TerminateServer':
            if pause_daemon:
                relay_onoff(sensor_co2_premeasure_relay[sensor_id], 'off')
                break
            time.sleep(0.25)

    for r in range(0, co2_read_tries):
        if not pid_co2_alive[sensor_id] or client_que == 'TerminateServer' or pause_daemon:
            break

        logging.debug("[Read CO2 Sensor-%s] Taking first CO2 reading", sensor_id + 1)

        for i in range(0, co2_read_tries):  # Multiple attempts to get first reading
            if pid_co2_alive[sensor_id] and client_que != 'TerminateServer' and pause_daemon != 1:
                co22 = read_co2(sensor_id, sensor_co2_device[sensor_id])
                if co22 is not None:
                    break
            else:
                break

        if co22 is None:
            logging.warning("[Read CO2 Sensor-%s] Could not read first CO2 measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read CO2 Sensor-%s] CO2: %s", sensor_id + 1, co22)
            logging.debug("[Read CO2 Sensor-%s] Taking second CO2 reading", sensor_id + 1)

        for i in range(0, co2_read_tries):  # Multiple attempts to get second reading
            if pid_co2_alive[sensor_id] and client_que != 'TerminateServer' and pause_daemon != 1:
                co2 = read_co2(sensor_id, sensor_co2_device[sensor_id])
                if co2 is not None:
                    break
            else:
                break

        if co2 is None:
            logging.warning("[Read CO2 Sensor-%s] Could not read second CO2 measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read CO2 Sensor-%s] CO2: %s", sensor_id + 1, co2)
            logging.debug("[Read CO2 Sensor-%s] Difference: %s", sensor_id + 1, abs(co22 - co2))

            if abs(co22 - co2) > 200:
                co22 = co2
                logging.debug("[Read CO2 Sensor-%s] Successive readings > 200 difference: Rereading", sensor_id + 1)
            else:
                logging.debug("[Read CO2 Sensor-%s] Successive readings < 200 difference: keeping.", sensor_id + 1)
                logging.debug("[Read CO2 Sensor-%s] CO2: %s", sensor_id + 1, co2)
                sensor_co2_read_co2[sensor_id] = co2
                logging.debug("[Read CO2 Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
                lock.release()
                return co2

    logging.warning("[Read CO2 Sensor-%s] Could not get two consecutive CO2 measurements that were consistent.", sensor_id + 1)
    logging.debug("[Read CO2 Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
    lock.release()
    return None


# Read the temperature and pressure from sensor
def read_press_sensor(sensor_id):
    global sensor_press_read_temp_c
    global sensor_press_read_press
    tempc = None
    tempc2 = None
    pressure = None
    pressure2 = None
    alt = None
    alt2 = None
    press_read_tries = 5

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sensor_press_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Read Press Sensor-%s] Acquiring Lock: %s", sensor_id + 1, lock.path)
            lock.acquire(timeout=90)    # wait up to 60 seconds
        except:
            logging.warning("[Read Press Sensor-%s] Breaking Lock to Acquire: %s", sensor_id + 1, lock.path)
            lock.break_lock()
            lock.acquire()
    logging.debug("[Read Press Sensor-%s] Gained lock: %s", sensor_id + 1, lock.path)
    timerPress = 0
    if sensor_press_premeasure_relay[sensor_id] and sensor_press_premeasure_dur[sensor_id]:
        timerPress = time.time() + sensor_press_premeasure_dur[sensor_id]
        rod = threading.Thread(target=relay_on_duration, args=(sensor_press_premeasure_relay[sensor_id], sensor_press_premeasure_dur[sensor_id], sensor_id, relay_trigger, relay_pin,))
        rod.start()
        while timerPress > time.time() and client_que != 'TerminateServer':
            if pause_daemon:
                relay_onoff(sensor_press_premeasure_relay[sensor_id], 'off')
                break
            time.sleep(0.25)

    for r in range(0, press_read_tries):  # Multiple attempts to get similar consecutive readings
        if (not pid_press_temp_alive[sensor_id] and not pid_press_press_alive[sensor_id]) and client_que == 'TerminateServer' or pause_daemon:
            break

        logging.debug("[Read Press Sensor-%s] Taking first Temperature/Pressure reading", sensor_id + 1)

        for i in range(0, press_read_tries):  # Multiple attempts to get first reading
            if (pid_press_temp_alive[sensor_id] or pid_press_press_alive[sensor_id]) and client_que != 'TerminateServer' and pause_daemon != 1:
                pressure2, tempc2, alt2 = read_press(sensor_id, sensor_press_device[sensor_id], sensor_press_pin[sensor_id])
                if pressure2 is not None and tempc2 is not None and alt is not None:
                    break
            else:
                break

        if pressure2 is None or tempc2 is None:
            logging.warning("[Read Press Sensor-%s] Could not read first Press/Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read Press Sensor-%s] %.1f°C, %.1fPa", sensor_id + 1, tempc2, pressure2)
            logging.debug("[Read Press Sensor-%s] Taking second Temperature/Pressure reading", sensor_id + 1)
        
        for i in range(0, press_read_tries):  # Multiple attempts to get second reading
            if (pid_press_temp_alive[sensor_id] or pid_press_press_alive[sensor_id]) and client_que != 'TerminateServer' and pause_daemon != 1:
                pressure, tempc, alt = read_press(sensor_id, sensor_press_device[sensor_id], sensor_press_pin[sensor_id])
                if pressure is not None and tempc is not None and alt is not None:
                    break
            else:
                break
           
        if pressure is None or tempc is None:
            logging.warning("[Read Press Sensor-%s] Could not read second Press/Temp measurement!", sensor_id + 1)
            break
        else:
            logging.debug("[Read Press Sensor-%s] %.1f°C, %.1fPa", sensor_id + 1, tempc, pressure)
            logging.debug("[Read Press Sensor-%s] Differences: %.1f°C, %.1fPa", sensor_id + 1, abs(tempc2 - tempc), abs(pressure2 - pressure))

            if abs(tempc2 - tempc) > 1 or abs(pressure2 - pressure) > 15:
                tempc2 = tempc
                pressure2 = pressure
                logging.debug("[Read Press Sensor-%s] Successive readings > 15 Pa or > 1°C difference: Rereading", sensor_id + 1)
            else:
                logging.debug("[Read Press Sensor-%s] Successive readings < 15 Pa or < 1°C difference: keeping.", sensor_id + 1)
                temperature_f = float(tempc) * 9.0 / 5.0 + 32.0
                logging.debug("[Read Press Sensor-%s] Temp: %.1f°C, Press: %.1fPa, ALT: %.1fm", sensor_id + 1, tempc, pressure, alt)
                sensor_press_read_press[sensor_id] = pressure
                sensor_press_read_temp_c[sensor_id] = tempc
                sensor_press_read_alt[sensor_id] = alt
                logging.debug("[Read Press Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
                lock.release()
                return pressure, tempc, alt

    logging.warning("[Read Press Sensor-%s] Could not get two consecutive Press measurements that were consistent.", sensor_id + 1)
    logging.debug("[Read Press Sensor-%s] Removing lock: %s", sensor_id + 1, lock.path)
    lock.release()
    return None



#################################################
#            Read Data From Sensors             #
#################################################

# Obtain reading from Temperature sensor
def read_t(sensor_id, device, pin):
    # Ensure at least 2 seconds between sensor reads
    global last_t_reading
    while last_t_reading > time.time():
        time.sleep(0.2)

    if device in 'RPi':
        if pin in '0':
            CPUtempFile = open('/sys/class/thermal/thermal_zone0/temp')
            CPUtempF = float(CPUtempFile.read())
            temperature = CPUtempF/1000  # Temperature in Celsius
        else:
            GPUtempStr = subprocess.check_output(('/opt/vc/bin/vcgencmd','measure_temp'))
            temperature = float(GPUtempStr.split('=')[1].split("'")[0])  # Temperature in Celsius
    elif device in 'DS18B20':
        import glob
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        base_dir = '/sys/bus/w1/devices/'
        #device_folder = glob.glob(base_dir + '28*')[0]
        device_file = base_dir + '28-' + pin + '/w1_slave'
        
        def read_temp_raw():
            f = open(device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines
        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temperature = float(temp_string) / 1000.0
            #temp_f = temp_c * 9.0 / 5.0 + 32.0
    else:
        logging.debug("[Read T Sensor-%s] Device not recognized: %s", sensor_id + 1, device)
        temperature = None

    last_t_reading = time.time() + 2
    return temperature


# Obtain reading from Humidity/Temperature sensor
def read_ht(sensor_id, device, pin):
    # Ensure at least 2 seconds between sensor reads
    global last_ht_reading
    while last_ht_reading > time.time():
        time.sleep(0.2)

    if device == 'DHT11':
        device = Adafruit_DHT.DHT11
    elif device == 'DHT22':
        device = Adafruit_DHT.DHT22
    elif device == 'AM2302':
        device = Adafruit_DHT.AM2302
    elif device == 'AM2315':
        device = 'AM2315'

    if device == Adafruit_DHT.DHT11 or device == Adafruit_DHT.DHT22 or device == Adafruit_DHT.AM2302:
        humidity, temperature = Adafruit_DHT.read_retry(device, pin)
    elif device == 'AM2315':
        if pin != 0:
            I2C_address = 0x70 + pin // 10
            if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
                I2C_bus_number = 1
            else:
                I2C_bus_number = 0
            bus = smbus.SMBus(I2C_bus_number)
            bus.write_byte(I2C_address, pin % 10)
            time.sleep(0.1)
        am = AM2315(0x5c, "/dev/i2c-1")
        temperature, humidity, crc_check = am.sense()
    else:
        logging.debug("[Read HT Sensor-%s] Device not recognized: %s", sensor_id + 1, device)
        temperature = humidity = None

    last_ht_reading = time.time() + 2
    return humidity, temperature


# Obtain reading from CO2 Sensor
def read_co2(sensor_id, device):
    # Ensure at least 2 seconds between sensor reads
    global last_co2_reading
    while last_co2_reading > time.time():
        time.sleep(0.2)

    if device == 'K30':
        ser = serial.Serial("/dev/ttyAMA0", timeout=1)  # Wait 1 second for reply
        ser.flushInput()
        time.sleep(1)
        ser.write("\xFE\x44\x00\x08\x02\x9F\x25")
        time.sleep(.01)
        resp = ser.read(7)
        if len(resp) == 0:
            last_co2_reading = time.time() + 2
            co2 = None
        else:
            high = ord(resp[3])
            low = ord(resp[4])
            co2 = (high * 256) + low
    else:
        logging.debug("[Read CO2 Sensor-%s] Device not recognized: %s", sensor_id + 1, device)
        co2 = None

    last_co2_reading = time.time() + 2
    return co2


# Obtain reading from Pressure sensor
def read_press(sensor_id, device, pin):
    # Ensure at least 2 seconds between sensor reads
    global last_press_reading
    while last_press_reading > time.time():
        time.sleep(0.2)

    if device == 'BMP085-180':
        if pin != 0:
            I2C_address = 0x70 + pin // 10
            if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
                I2C_bus_number = 1
            else:
                I2C_bus_number = 0
            bus = smbus.SMBus(I2C_bus_number)
            bus.write_byte(I2C_address, pin % 10)
            time.sleep(0.1)
        press_sensor = BMP085.BMP085()
        temperature = press_sensor.read_temperature()
        pressure = press_sensor.read_pressure()
        altitude = press_sensor.read_altitude()
        #sea_level = sensor.read_sealevel_pressure()
    else:
        logging.debug("[Read Press Sensor-%s] Device not recognized: %s", sensor_id + 1, device)
        pressure = temperature = altitude = None

    last_press_reading = time.time() + 2
    return pressure, temperature, altitude



#################################################
#          SQLite Database Read/Write           #
#################################################

# Read variables from the SQLite database
def read_sql():
    global pause_daemon
    global pause_daemon_confirm
    pause_daemon = 1
    while pause_daemon_confirm == -1:
        time.sleep(0.1)
    time.sleep(1)

    # Temperature sensor globals
    global sensor_t_id
    global sensor_t_name
    global sensor_t_device
    global sensor_t_pin
    global sensor_t_period
    global sensor_t_premeasure_relay
    global sensor_t_premeasure_dur
    global sensor_t_activated
    global sensor_t_graph
    global sensor_t_yaxis_relay_min
    global sensor_t_yaxis_relay_max
    global sensor_t_yaxis_relay_tics
    global sensor_t_yaxis_relay_mtics
    global sensor_t_yaxis_temp_min
    global sensor_t_yaxis_temp_max
    global sensor_t_yaxis_temp_tics
    global sensor_t_yaxis_temp_mtics
    global sensor_t_temp_relays_up
    global sensor_t_temp_relays_down
    global pid_t_temp_relay_high
    global pid_t_temp_outmin_high
    global pid_t_temp_outmax_high
    global pid_t_temp_relay_low
    global pid_t_temp_outmin_low
    global pid_t_temp_outmax_low
    global pid_t_temp_set
    global pid_t_temp_set_dir
    global pid_t_temp_or
    global pid_t_temp_period
    global pid_t_temp_p
    global pid_t_temp_i
    global pid_t_temp_d
    global pid_t_temp_alive
    global sensor_t_read_temp_c
    
    # Temperature sensor variable reset
    sensor_t_id = []
    sensor_t_name = []
    sensor_t_device = []
    sensor_t_pin = []
    sensor_t_period = []
    sensor_t_premeasure_relay = []
    sensor_t_premeasure_dur = []
    sensor_t_activated = []
    sensor_t_graph = []
    sensor_t_yaxis_relay_min = []
    sensor_t_yaxis_relay_max = []
    sensor_t_yaxis_relay_tics = []
    sensor_t_yaxis_relay_mtics = []
    sensor_t_yaxis_temp_min = []
    sensor_t_yaxis_temp_max = []
    sensor_t_yaxis_temp_tics = []
    sensor_t_yaxis_temp_mtics = []
    sensor_t_temp_relays_up = []
    sensor_t_temp_relays_down = []
    pid_t_temp_relay_high = []
    pid_t_temp_outmin_high = []
    pid_t_temp_outmax_high = []
    pid_t_temp_relay_low = []
    pid_t_temp_outmin_low = []
    pid_t_temp_outmax_low = []
    pid_t_temp_set = []
    pid_t_temp_set_dir = []
    pid_t_temp_period = []
    pid_t_temp_p = []
    pid_t_temp_i = []
    pid_t_temp_d = []
    pid_t_temp_or = []
    sensor_t_read_temp_c = []

    # Temperature/Humidity sensor globals
    global sensor_ht_id
    global sensor_ht_name
    global sensor_ht_device
    global sensor_ht_pin
    global sensor_ht_period
    global sensor_ht_premeasure_relay
    global sensor_ht_premeasure_dur
    global sensor_ht_activated
    global sensor_ht_graph
    global sensor_ht_verify_pin
    global sensor_ht_verify_temp
    global sensor_ht_verify_temp_notify
    global sensor_ht_verify_temp_stop
    global sensor_ht_verify_hum
    global sensor_ht_verify_hum_notify
    global sensor_ht_verify_hum_stop
    global sensor_ht_verify_email
    global sensor_ht_yaxis_relay_min
    global sensor_ht_yaxis_relay_max
    global sensor_ht_yaxis_relay_tics
    global sensor_ht_yaxis_relay_mtics
    global sensor_ht_yaxis_temp_min
    global sensor_ht_yaxis_temp_max
    global sensor_ht_yaxis_temp_tics
    global sensor_ht_yaxis_temp_mtics
    global sensor_ht_yaxis_hum_min
    global sensor_ht_yaxis_hum_max
    global sensor_ht_yaxis_hum_tics
    global sensor_ht_yaxis_hum_mtics
    global sensor_ht_temp_relays_up
    global sensor_ht_temp_relays_down
    global pid_ht_temp_relay_high
    global pid_ht_temp_outmin_high
    global pid_ht_temp_outmax_high
    global pid_ht_temp_relay_low
    global pid_ht_temp_outmin_low
    global pid_ht_temp_outmax_low
    global pid_ht_temp_set
    global pid_ht_temp_set_dir
    global pid_ht_temp_or
    global pid_ht_temp_period
    global pid_ht_temp_p
    global pid_ht_temp_i
    global pid_ht_temp_d
    global sensor_ht_hum_relays_up
    global sensor_ht_hum_relays_down
    global pid_ht_hum_relay_high
    global pid_ht_hum_outmin_high
    global pid_ht_hum_outmax_high
    global pid_ht_hum_relay_low
    global pid_ht_hum_outmin_low
    global pid_ht_hum_outmax_low
    global pid_ht_hum_set
    global pid_ht_hum_set_dir
    global pid_ht_hum_or
    global pid_ht_hum_period
    global pid_ht_hum_p
    global pid_ht_hum_i
    global pid_ht_hum_d
    global pid_ht_temp_alive
    global pid_ht_hum_alive
    global sensor_ht_dewpt_c
    global sensor_ht_read_hum
    global sensor_ht_read_temp_c

    # Temperature/Humidity sensor variable reset
    sensor_ht_id = []
    sensor_ht_name = []
    sensor_ht_device = []
    sensor_ht_pin = []
    sensor_ht_period = []
    sensor_ht_premeasure_relay = []
    sensor_ht_premeasure_dur = []
    sensor_ht_activated = []
    sensor_ht_graph = []
    sensor_ht_verify_pin = []
    sensor_ht_verify_temp = []
    sensor_ht_verify_temp_notify = []
    sensor_ht_verify_temp_stop = []
    sensor_ht_verify_hum = []
    sensor_ht_verify_hum_notify = []
    sensor_ht_verify_hum_stop = []
    sensor_ht_verify_email = []
    sensor_ht_yaxis_relay_min = []
    sensor_ht_yaxis_relay_max = []
    sensor_ht_yaxis_relay_tics = []
    sensor_ht_yaxis_relay_mtics = []
    sensor_ht_yaxis_temp_min = []
    sensor_ht_yaxis_temp_max = []
    sensor_ht_yaxis_temp_tics = []
    sensor_ht_yaxis_temp_mtics = []
    sensor_ht_yaxis_hum_min = []
    sensor_ht_yaxis_hum_max = []
    sensor_ht_yaxis_hum_tics = []
    sensor_ht_yaxis_hum_mtics = []
    sensor_ht_temp_relays_up = []
    sensor_ht_temp_relays_down = []
    pid_ht_temp_relay_high = []
    pid_ht_temp_outmin_high = []
    pid_ht_temp_outmax_high = []
    pid_ht_temp_relay_low = []
    pid_ht_temp_outmin_low = []
    pid_ht_temp_outmax_low = []
    pid_ht_temp_set = []
    pid_ht_temp_set_dir = []
    pid_ht_temp_period = []
    pid_ht_temp_p = []
    pid_ht_temp_i = []
    pid_ht_temp_d = []
    pid_ht_temp_or = []
    sensor_ht_hum_relays_up = []
    sensor_ht_hum_relays_down = []
    pid_ht_hum_relay_high = []
    pid_ht_hum_outmin_high = []
    pid_ht_hum_outmax_high = []
    pid_ht_hum_relay_low = []
    pid_ht_hum_outmin_low = []
    pid_ht_hum_outmax_low = []
    pid_ht_hum_set = []
    pid_ht_hum_set_dir = []
    pid_ht_hum_period = []
    pid_ht_hum_p = []
    pid_ht_hum_i = []
    pid_ht_hum_d = []
    pid_ht_hum_or = []
    sensor_ht_dewpt_c = []
    sensor_ht_read_hum = []
    sensor_ht_read_temp_c = []
    
    # CO2 sensor globals
    global sensor_co2_id
    global sensor_co2_name
    global sensor_co2_device
    global sensor_co2_pin
    global sensor_co2_period
    global sensor_co2_premeasure_relay
    global sensor_co2_premeasure_dur
    global sensor_co2_activated
    global sensor_co2_graph
    global sensor_co2_yaxis_relay_min
    global sensor_co2_yaxis_relay_max
    global sensor_co2_yaxis_relay_tics
    global sensor_co2_yaxis_relay_mtics
    global sensor_co2_yaxis_co2_min
    global sensor_co2_yaxis_co2_max
    global sensor_co2_yaxis_co2_tics
    global sensor_co2_yaxis_co2_mtics
    global sensor_co2_relays_up
    global sensor_co2_relays_down
    global pid_co2_relay_high
    global pid_co2_outmin_high
    global pid_co2_outmax_high
    global pid_co2_relay_low
    global pid_co2_outmin_low
    global pid_co2_outmax_low
    global pid_co2_set
    global pid_co2_set_dir
    global pid_co2_or
    global pid_co2_period
    global pid_co2_p
    global pid_co2_i
    global pid_co2_d
    global pid_co2_alive
    global sensor_co2_read_co2

    # CO2 sensor variable reset
    sensor_co2_id = []
    sensor_co2_name = []
    sensor_co2_device = []
    sensor_co2_pin = []
    sensor_co2_period = []
    sensor_co2_premeasure_relay = []
    sensor_co2_premeasure_dur = []
    sensor_co2_activated = []
    sensor_co2_graph = []
    sensor_co2_yaxis_relay_min = []
    sensor_co2_yaxis_relay_max = []
    sensor_co2_yaxis_relay_tics = []
    sensor_co2_yaxis_relay_mtics = []
    sensor_co2_yaxis_co2_min = []
    sensor_co2_yaxis_co2_max = []
    sensor_co2_yaxis_co2_tics = []
    sensor_co2_yaxis_co2_mtics = []
    sensor_co2_relays_up = []
    sensor_co2_relays_down = []
    pid_co2_relay_high = []
    pid_co2_outmin_high = []
    pid_co2_outmax_high = []
    pid_co2_relay_low = []
    pid_co2_outmin_low = []
    pid_co2_outmax_low = []
    pid_co2_set = []
    pid_co2_set_dir = []
    pid_co2_period = []
    pid_co2_p = []
    pid_co2_i = []
    pid_co2_d = []
    pid_co2_outmax = []
    pid_co2_or = []
    sensor_co2_read_co2 = []

    # Pressure sensor globals
    global sensor_press_id
    global sensor_press_name
    global sensor_press_device
    global sensor_press_pin
    global sensor_press_period
    global sensor_press_premeasure_relay
    global sensor_press_premeasure_dur
    global sensor_press_activated
    global sensor_press_graph
    global sensor_press_yaxis_relay_min
    global sensor_press_yaxis_relay_max
    global sensor_press_yaxis_relay_tics
    global sensor_press_yaxis_relay_mtics
    global sensor_press_yaxis_temp_min
    global sensor_press_yaxis_temp_max
    global sensor_press_yaxis_temp_tics
    global sensor_press_yaxis_temp_mtics
    global sensor_press_yaxis_press_min
    global sensor_press_yaxis_press_max
    global sensor_press_yaxis_press_tics
    global sensor_press_yaxis_press_mtics
    global sensor_press_temp_relays_up
    global sensor_press_temp_relays_down
    global pid_press_temp_relay_high
    global pid_press_temp_outmin_high
    global pid_press_temp_outmax_high
    global pid_press_temp_relay_low
    global pid_press_temp_outmin_low
    global pid_press_temp_outmax_low
    global pid_press_temp_set
    global pid_press_temp_set_dir
    global pid_press_temp_or
    global pid_press_temp_period
    global pid_press_temp_p
    global pid_press_temp_i
    global pid_press_temp_d
    global sensor_press_press_relays_up
    global sensor_press_press_relays_down
    global pid_press_press_relay_high
    global pid_press_press_outmin_high
    global pid_press_press_outmax_high
    global pid_press_press_relay_low
    global pid_press_press_outmin_low
    global pid_press_press_outmax_low
    global pid_press_press_set
    global pid_press_press_set_dir
    global pid_press_press_or
    global pid_press_press_period
    global pid_press_press_p
    global pid_press_press_i
    global pid_press_press_d
    global pid_press_temp_alive
    global pid_press_press_alive
    global sensor_press_read_alt
    global sensor_press_read_press
    global sensor_press_read_temp_c
    
    # Pressure sensor variable reset
    sensor_press_id = []
    sensor_press_name = []
    sensor_press_device = []
    sensor_press_pin = []
    sensor_press_period = []
    sensor_press_premeasure_relay = []
    sensor_press_premeasure_dur = []
    sensor_press_activated = []
    sensor_press_graph = []
    sensor_press_yaxis_relay_min = []
    sensor_press_yaxis_relay_max = []
    sensor_press_yaxis_relay_tics = []
    sensor_press_yaxis_relay_mtics = []
    sensor_press_yaxis_temp_min = []
    sensor_press_yaxis_temp_max = []
    sensor_press_yaxis_temp_tics = []
    sensor_press_yaxis_temp_mtics = []
    sensor_press_yaxis_press_min = []
    sensor_press_yaxis_press_max = []
    sensor_press_yaxis_press_tics = []
    sensor_press_yaxis_press_mtics = []
    sensor_press_temp_relays_up = []
    sensor_press_temp_relays_down = []
    pid_press_temp_relay_high = []
    pid_press_temp_outmin_high = []
    pid_press_temp_outmax_high = []
    pid_press_temp_relay_low = []
    pid_press_temp_outmin_low = []
    pid_press_temp_outmax_low = []
    pid_press_temp_set = []
    pid_press_temp_set_dir = []
    pid_press_temp_period = []
    pid_press_temp_p = []
    pid_press_temp_i = []
    pid_press_temp_d = []
    pid_press_temp_or = []
    sensor_press_press_relays_up = []
    sensor_press_press_relays_down = []
    pid_press_press_relay_high = []
    pid_press_press_outmin_high = []
    pid_press_press_outmax_high = []
    pid_press_press_relay_low = []
    pid_press_press_outmin_low = []
    pid_press_press_outmax_low = []
    pid_press_press_set = []
    pid_press_press_set_dir = []
    pid_press_press_period = []
    pid_press_press_p = []
    pid_press_press_i = []
    pid_press_press_d = []
    pid_press_press_or = []
    sensor_press_read_alt = []
    sensor_press_read_press = []
    sensor_press_read_temp_c = []

    # Relay globals
    global relay_id
    global relay_name
    global relay_pin
    global relay_amps
    global relay_trigger
    global relay_start_state

    # Relay variable reset
    relay_id = []
    relay_name = []
    relay_pin = []
    relay_amps = []
    relay_trigger = []
    relay_start_state = []

    # Timer globals
    global timer_id
    global timer_name
    global timer_relay
    global timer_state
    global timer_duration_on
    global timer_duration_off

    # Timer variable reset 
    timer_id = []
    timer_name = []
    timer_relay = []
    timer_state = []
    timer_duration_on = []
    timer_duration_off = []

    # Daemon timer globals
    global timer_time
    global timerTSensorLog
    global timerHTSensorLog
    global timerCo2SensorLog
    global timerPressSensorLog

    # Daemon timer variable reset
    timer_time = []
    timerTSensorLog = []
    timerHTSensorLog = []
    timerCo2SensorLog = []
    timerPressSensorLog = []

    global on_duration_timer
    global on_duration_seconds

    # Email notification globals
    global smtp_host
    global smtp_ssl
    global smtp_port
    global smtp_user
    global smtp_pass
    global smtp_email_from
    global smtp_wait_time

    # Misc
    global enable_max_amps
    global max_amps

    # Check if all required tables exist in the SQL database
    conn = sqlite3.connect(mycodo_database)
    cur = conn.cursor()
    tables = ['Relays', 'TSensor', 'HTSensor', 'CO2Sensor', 'PressSensor', 'Timers', 'CustomGraph', 'SMTP', 'Misc']
    missing = []
    for each in tables:
        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND NAME = ? ", (each,))
        if cur.fetchone() is None:
            missing.append(each)
    if missing:
        print "Missing required table(s): %s" % " ,".join(missing)
        print "Reinitialize database to correct."
        return 0

    # Begin setting global variables from SQL database values
    cur.execute('SELECT enable_max_amps, max_amps FROM misc')
    for row in cur:
        enable_max_amps = row[0]
        max_amps = row[1]

    # Begin setting global variables from SQL database values
    cur.execute('SELECT id, name, pin, amps, trigger, start_state FROM relays')
    for row in cur:
        relay_id.append(row[0])
        relay_name.append(row[1])
        relay_pin.append(row[2])
        relay_amps.append(row[3])
        relay_trigger.append(row[4])
        relay_start_state.append(row[5])

    # Relay conditional statement globals
    global conditional_relay_id
    global conditional_relay_name
    global conditional_relay_ifrelay
    global conditional_relay_ifaction
    global conditional_relay_ifduration
    global conditional_relay_sel_relay
    global conditional_relay_dorelay
    global conditional_relay_doaction
    global conditional_relay_doduration
    global conditional_relay_sel_command
    global conditional_relay_do_command
    global conditional_relay_sel_notify
    global conditional_relay_do_notify
    global conditional_relay_time_notify

    # Relay conditional statement reset
    conditional_relay_id = []
    conditional_relay_name = []
    conditional_relay_ifrelay = []
    conditional_relay_ifaction = []
    conditional_relay_ifduration = []
    conditional_relay_sel_relay = []
    conditional_relay_dorelay = []
    conditional_relay_doaction = []
    conditional_relay_doduration = []
    conditional_relay_sel_command = []
    conditional_relay_do_command = []
    conditional_relay_sel_notify = []
    conditional_relay_do_notify = []
    conditional_relay_time_notify = []

    cur.execute("""SELECT id,
                          name,
                          if_relay,
                          if_action,
                          if_duration,
                          sel_relay,
                          do_relay,
                          do_action,
                          do_duration,
                          sel_command,
                          do_command,
                          sel_notify,
                          do_notify
                   FROM   relayconditional""")
    for row in cur:
        conditional_relay_id.append(row[0])
        conditional_relay_name.append(row[1])
        conditional_relay_ifrelay.append(row[2])
        conditional_relay_ifaction.append(row[3])
        conditional_relay_ifduration.append(row[4])
        conditional_relay_sel_relay.append(row[5])
        conditional_relay_dorelay.append(row[6])
        conditional_relay_doaction.append(row[7])
        conditional_relay_doduration.append(row[8])
        conditional_relay_sel_command.append(row[9])
        if row[10] is None:
            conditional_relay_do_command.append(row[10])
        else:
            if "\'\'" not in row[10]:   
                conditional_relay_do_command.append(row[10])
            else:
                conditional_relay_do_command.append(row[10].replace("\'\'", "\'"))
        conditional_relay_sel_notify.append(row[11])
        conditional_relay_do_notify.append(row[12])
        conditional_relay_time_notify.append(0)

    cur.execute("""SELECT id,
                          name,
                          pin,
                          device,
                          period,
                          pre_measure_relay,
                          pre_measure_dur,
                          activated,
                          graph,
                          yaxis_relay_min,
                          yaxis_relay_max,
                          yaxis_relay_tics,
                          yaxis_relay_mtics,
                          yaxis_temp_min,
                          yaxis_temp_max,
                          yaxis_temp_tics,
                          yaxis_temp_mtics,
                          temp_relays_up,
                          temp_relays_down,
                          temp_relay_high,
                          temp_outmin_high,
                          temp_outmax_high,
                          temp_relay_low,
                          temp_outmin_low,
                          temp_outmax_low,
                          temp_or,
                          temp_set,
                          temp_set_direction,
                          temp_period,
                          temp_p,
                          temp_i,
                          temp_d
                   FROM   tsensor """)
    for row in cur:
        sensor_t_id.append(row[0])
        sensor_t_name.append(row[1])
        sensor_t_pin.append(row[2])
        sensor_t_device.append(row[3])
        sensor_t_period.append(row[4])
        sensor_t_premeasure_relay.append(row[5])
        sensor_t_premeasure_dur.append(row[6])
        sensor_t_activated.append(row[7])
        sensor_t_graph.append(row[8])
        sensor_t_yaxis_relay_min.append(row[9])
        sensor_t_yaxis_relay_max.append(row[10])
        sensor_t_yaxis_relay_tics.append(row[11])
        sensor_t_yaxis_relay_mtics.append(row[12])
        sensor_t_yaxis_temp_min.append(row[13])
        sensor_t_yaxis_temp_max.append(row[14])
        sensor_t_yaxis_temp_tics.append(row[15])
        sensor_t_yaxis_temp_mtics.append(row[16])
        sensor_t_temp_relays_up.append(row[17])
        sensor_t_temp_relays_down.append(row[18])
        pid_t_temp_relay_high.append(row[19])
        pid_t_temp_outmin_high.append(row[20])
        pid_t_temp_outmax_high.append(row[21])
        pid_t_temp_relay_low.append(row[22])
        pid_t_temp_outmin_low.append(row[23])
        pid_t_temp_outmax_low.append(row[24])
        pid_t_temp_or.append(row[25])
        pid_t_temp_set.append(row[26])
        pid_t_temp_set_dir.append(row[27])
        pid_t_temp_period.append(row[28])
        pid_t_temp_p.append(row[29])
        pid_t_temp_i.append(row[30])
        pid_t_temp_d.append(row[31])

    # Convert string of comma-separated values to a 2-dimensional list of integers
    global sensor_t_temp_relays_up_list
    sensor_t_temp_relays_up_list = []
    for i in range(0, len(sensor_t_temp_relays_up)):
        if sensor_t_temp_relays_up[i] != '':
            sensor_t_temp_relays_up_list.append(sensor_t_temp_relays_up[i].split(","))
            sensor_t_temp_relays_up_list[i] = map(int, sensor_t_temp_relays_up_list[i])

    global sensor_t_temp_relays_down_list
    sensor_t_temp_relays_down_list = []
    for i in range(0, len(sensor_t_temp_relays_down)):
        if sensor_t_temp_relays_down[i] != '':
            sensor_t_temp_relays_down_list.append(sensor_t_temp_relays_down[i].split(","))
            sensor_t_temp_relays_down_list[i] = map(int, sensor_t_temp_relays_down_list[i])

    global conditional_t_number_sensor
    global conditional_t_number_conditional
    conditional_t_number_sensor = []
    conditional_t_number_conditional = []

    cur.execute('SELECT id FROM tsensor')
    for row in cur:
        conditional_t_number_sensor.append(row[0])

    cur.execute('SELECT id FROM tsensorconditional')
    for row in cur:
        conditional_t_number_conditional.append(row[0])

    global conditional_t_id
    global conditional_t_name
    global conditional_t_state
    global conditional_t_direction
    global conditional_t_setpoint
    global conditional_t_period
    global conditional_t_sel_relay
    global conditional_t_relay
    global conditional_t_relay_state
    global conditional_t_relay_seconds_on
    global conditional_t_sel_command
    global conditional_t_do_command
    global conditional_t_sel_notify
    global conditional_t_do_notify
    global conditional_t_time_notify

    # There may be multiple conditional statements per sensor.
    # get_3d_array() will initialize (to 0) a 3-dimensional array with the length of indexes
    # equal to the number of sensors and the number of conditionals per each sensor.
    # Elements are then set and accessed with conditional_x[sensor_number][conditonal_number][0]
    conditional_t_id = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_name = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_state = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_direction = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_setpoint = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_period = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_sel_relay = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_relay = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_relay_state = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_relay_seconds_on = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_sel_command = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_do_command = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_sel_notify = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_do_notify = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)
    conditional_t_time_notify = get_3d_array(len(conditional_t_number_sensor), len(conditional_t_number_conditional), 1)

    for j in range(0, len(conditional_t_number_sensor)):
        cur.execute("""SELECT id,
                              name,
                              state,
                              direction,
                              setpoint,
                              period,
                              sel_relay,
                              relay,
                              relay_state,
                              relay_seconds_on,
                              sel_command,
                              do_command,
                              sel_notify,
                              do_notify
                       FROM   tsensorconditional
                       WHERE  sensor = ? """, (str(j),))
        count = 0
        for row in cur:
            conditional_t_id[j][count][0] = row[0]
            conditional_t_name[j][count][0] = row[1]
            conditional_t_state[j][count][0] = row[2]
            conditional_t_direction[j][count][0] = row[3]
            conditional_t_setpoint[j][count][0] = row[4]
            conditional_t_period[j][count][0] = row[5]
            conditional_t_sel_relay[j][count][0] = row[6]
            conditional_t_relay[j][count][0] = row[7]
            conditional_t_relay_state[j][count][0] = row[8]
            conditional_t_relay_seconds_on[j][count][0] = row[9]
            conditional_t_sel_command[j][count][0] = row[10]
            if row[11] is None:
                conditional_t_do_command[j][count][0] = row[11]
            else:
                if "\'\'" not in row[11]:   
                    conditional_t_do_command[j][count][0] = row[11]
                else:
                    conditional_t_do_command[j][count][0] = row[11].replace("\'\'", "\'")
            conditional_t_sel_notify[j][count][0] = row[12]
            conditional_t_do_notify[j][count][0] = row[13]
            conditional_t_time_notify[j][count][0] = 0
            count += 1

    cur.execute("""SELECT id,
                          name,
                          pin,
                          device,
                          period,
                          pre_measure_relay,
                          pre_measure_dur,
                          activated,
                          graph,
                          verify_pin,
                          verify_temp,
                          verify_temp_notify,
                          verify_temp_stop,
                          verify_hum,
                          verify_hum_notify,
                          verify_hum_stop,
                          verify_notify_email,
                          yaxis_relay_min,
                          yaxis_relay_max,
                          yaxis_relay_tics,
                          yaxis_relay_mtics,
                          yaxis_temp_min,
                          yaxis_temp_max,
                          yaxis_temp_tics,
                          yaxis_temp_mtics,
                          yaxis_hum_min,
                          yaxis_hum_max,
                          yaxis_hum_tics,
                          yaxis_hum_mtics,
                          temp_relays_up,
                          temp_relays_down,
                          temp_relay_high,
                          temp_outmin_high,
                          temp_outmax_high,
                          temp_relay_low,
                          temp_outmin_low,
                          temp_outmax_low,
                          temp_or,
                          temp_set,
                          temp_set_direction,
                          temp_period,
                          temp_p,
                          temp_i,
                          temp_d,
                          hum_relays_up,
                          hum_relays_down,
                          hum_relay_high,
                          hum_outmin_high,
                          hum_outmax_high,
                          hum_relay_low,
                          hum_outmin_low,
                          hum_outmax_low,
                          hum_or,
                          hum_set,
                          hum_set_direction,
                          hum_period,
                          hum_p,
                          hum_i,
                          hum_d
                   FROM   htsensor """)
    for row in cur:
        sensor_ht_id.append(row[0])
        sensor_ht_name.append(row[1])
        sensor_ht_pin.append(row[2])
        sensor_ht_device.append(row[3])
        sensor_ht_period.append(row[4])
        sensor_ht_premeasure_relay.append(row[5])
        sensor_ht_premeasure_dur.append(row[6])
        sensor_ht_activated.append(row[7])
        sensor_ht_graph.append(row[8])
        sensor_ht_verify_pin.append(row[9])
        sensor_ht_verify_temp.append(row[10])
        sensor_ht_verify_temp_notify.append(row[11])
        sensor_ht_verify_temp_stop.append(row[12])
        sensor_ht_verify_hum.append(row[13])
        sensor_ht_verify_hum_notify.append(row[14])
        sensor_ht_verify_hum_stop.append(row[15])
        sensor_ht_verify_email.append(row[16])
        sensor_ht_yaxis_relay_min.append(row[17])
        sensor_ht_yaxis_relay_max.append(row[18])
        sensor_ht_yaxis_relay_tics.append(row[19])
        sensor_ht_yaxis_relay_mtics.append(row[20])
        sensor_ht_yaxis_temp_min.append(row[21])
        sensor_ht_yaxis_temp_max.append(row[22])
        sensor_ht_yaxis_temp_tics.append(row[23])
        sensor_ht_yaxis_temp_mtics.append(row[24])
        sensor_ht_yaxis_hum_min.append(row[25])
        sensor_ht_yaxis_hum_max.append(row[26])
        sensor_ht_yaxis_hum_tics.append(row[27])
        sensor_ht_yaxis_hum_mtics.append(row[28])
        sensor_ht_temp_relays_up.append(row[29])
        sensor_ht_temp_relays_down.append(row[30])
        pid_ht_temp_relay_high.append(row[31])
        pid_ht_temp_outmin_high.append(row[32])
        pid_ht_temp_outmax_high.append(row[33])
        pid_ht_temp_relay_low.append(row[34])
        pid_ht_temp_outmin_low.append(row[35])
        pid_ht_temp_outmax_low.append(row[36])
        pid_ht_temp_or.append(row[37])
        pid_ht_temp_set.append(row[38])
        pid_ht_temp_set_dir.append(row[39])
        pid_ht_temp_period.append(row[40])
        pid_ht_temp_p.append(row[41])
        pid_ht_temp_i.append(row[42])
        pid_ht_temp_d.append(row[43])
        sensor_ht_hum_relays_up.append(row[44])
        sensor_ht_hum_relays_down.append(row[45])
        pid_ht_hum_relay_high.append(row[46])
        pid_ht_hum_outmin_high.append(row[47])
        pid_ht_hum_outmax_high.append(row[48])
        pid_ht_hum_relay_low.append(row[49])
        pid_ht_hum_outmin_low.append(row[50])
        pid_ht_hum_outmax_low.append(row[51])
        pid_ht_hum_or.append(row[52])
        pid_ht_hum_set.append(row[53])
        pid_ht_hum_set_dir.append(row[54])
        pid_ht_hum_period.append(row[55])
        pid_ht_hum_p.append(row[56])
        pid_ht_hum_i.append(row[57])
        pid_ht_hum_d.append(row[58])

    # Convert string of comma-separated values to a 2-dimensional list of integers
    global sensor_ht_temp_relays_up_list
    sensor_ht_temp_relays_up_list = []
    for i in range(0, len(sensor_ht_temp_relays_up)):
        if sensor_ht_temp_relays_up[i] != '':
            sensor_ht_temp_relays_up_list.append(sensor_ht_temp_relays_up[i].split(","))
            sensor_ht_temp_relays_up_list[i] = map(int, sensor_ht_temp_relays_up_list[i])

    global sensor_ht_temp_relays_down_list
    sensor_ht_temp_relays_down_list = []
    for i in range(0, len(sensor_ht_temp_relays_down)):
        if sensor_ht_temp_relays_down[i] != '':
            sensor_ht_temp_relays_down_list.append(sensor_ht_temp_relays_down[i].split(","))
            sensor_ht_temp_relays_down_list[i] = map(int, sensor_ht_temp_relays_down_list[i])

    global sensor_ht_hum_relays_up_list
    sensor_ht_hum_relays_up_list = []
    for i in range(0, len(sensor_ht_hum_relays_up)):
        if sensor_ht_hum_relays_up[i] != '':
            sensor_ht_hum_relays_up_list.append(sensor_ht_hum_relays_up[i].split(","))
            sensor_ht_hum_relays_up_list[i] = map(int, sensor_ht_hum_relays_up_list[i])

    global sensor_ht_hum_relays_down_list
    sensor_ht_hum_relays_down_list = []
    for i in range(0, len(sensor_ht_hum_relays_down)):
        if sensor_ht_hum_relays_down[i] != '':
            sensor_ht_hum_relays_down_list.append(sensor_ht_hum_relays_down[i].split(","))
            sensor_ht_hum_relays_down_list[i] = map(int, sensor_ht_hum_relays_down_list[i])
    
    global conditional_ht_number_sensor
    global conditional_ht_number_conditional
    conditional_ht_number_sensor = []
    conditional_ht_number_conditional = []

    cur.execute('SELECT id FROM htsensor')
    for row in cur:
        conditional_ht_number_sensor.append(row[0])

    cur.execute('SELECT id FROM htsensorconditional')
    for row in cur:
        conditional_ht_number_conditional.append(row[0])

    global conditional_ht_id
    global conditional_ht_name
    global conditional_ht_state
    global conditional_ht_condition
    global conditional_ht_direction
    global conditional_ht_setpoint
    global conditional_ht_period
    global conditional_ht_sel_relay
    global conditional_ht_relay
    global conditional_ht_relay_state
    global conditional_ht_relay_seconds_on
    global conditional_ht_sel_command
    global conditional_ht_do_command
    global conditional_ht_sel_notify
    global conditional_ht_do_notify
    global conditional_ht_time_notify

    # There may be multiple conditional statements per sensor.
    # get_3d_array() will initialize (to 0) a 3-dimensional array with the length of indexes
    # equal to the number of sensors and the number of conditionals per each sensor.
    # Elements are then set and accessed with conditional_x[sensor_number][conditonal_number][0]
    conditional_ht_id = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_name = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_state = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_condition = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_direction = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_setpoint = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_period = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_sel_relay = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_relay = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_relay_state = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_relay_seconds_on = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_sel_command = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_do_command = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_sel_notify = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_do_notify = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)
    conditional_ht_time_notify = get_3d_array(len(conditional_ht_number_sensor), len(conditional_ht_number_conditional), 1)

    for j in range(0, len(conditional_ht_number_sensor)):
        cur.execute("""SELECT id,
                              name,
                              state,
                              condition,
                              direction,
                              setpoint,
                              period,
                              sel_relay,
                              relay,
                              relay_state,
                              relay_seconds_on,
                              sel_command,
                              do_command,
                              sel_notify,
                              do_notify
                       FROM   htsensorconditional
                       WHERE  sensor = ? """, (str(j),))

        count = 0
        for row in cur:
            conditional_ht_id[j][count][0] = row[0]
            conditional_ht_name[j][count][0] = row[1]
            conditional_ht_state[j][count][0] = row[2]
            conditional_ht_condition[j][count][0] = row[3]
            conditional_ht_direction[j][count][0] = row[4]
            conditional_ht_setpoint[j][count][0] = row[5]
            conditional_ht_period[j][count][0] = row[6]
            conditional_ht_sel_relay[j][count][0] = row[7]
            conditional_ht_relay[j][count][0] = row[8]
            conditional_ht_relay_state[j][count][0] = row[9]
            conditional_ht_relay_seconds_on[j][count][0] = row[10]
            conditional_ht_sel_command[j][count][0] = row[11]
            if row[12] is None:
                conditional_ht_do_command[j][count][0] = row[12]
            else:
                if "\'\'" not in row[12]:
                    conditional_ht_do_command[j][count][0] = row[12]
                else:
                    conditional_ht_do_command[j][count][0] = row[12].replace("\'\'", "\'")
            conditional_ht_sel_notify[j][count][0] = row[13]
            conditional_ht_do_notify[j][count][0] = row[14]
            conditional_ht_time_notify[j][count][0] = 0
            count += 1

    cur.execute("""SELECT id,
                          name,
                          pin,
                          device,
                          period,
                          pre_measure_relay,
                          pre_measure_dur,
                          activated,
                          graph,
                          yaxis_relay_min,
                          yaxis_relay_max,
                          yaxis_relay_tics,
                          yaxis_relay_mtics,
                          yaxis_co2_min,
                          yaxis_co2_max,
                          yaxis_co2_tics,
                          yaxis_co2_mtics,
                          co2_relays_up,
                          co2_relays_down,
                          co2_relay_high,
                          co2_outmin_high,
                          co2_outmax_high,
                          co2_relay_low,
                          co2_outmin_low,
                          co2_outmax_low,
                          co2_or,
                          co2_set,
                          co2_set_direction,
                          co2_period,
                          co2_p,
                          co2_i,
                          co2_d
                   FROM   co2sensor """)
    for row in cur:
        sensor_co2_id.append(row[0])
        sensor_co2_name.append(row[1])
        sensor_co2_pin.append(row[2])
        sensor_co2_device.append(row[3])
        sensor_co2_period.append(row[4])
        sensor_co2_premeasure_relay.append(row[5])
        sensor_co2_premeasure_dur.append(row[6])
        sensor_co2_activated.append(row[7])
        sensor_co2_graph.append(row[8])
        sensor_co2_yaxis_relay_min.append(row[9])
        sensor_co2_yaxis_relay_max.append(row[10])
        sensor_co2_yaxis_relay_tics.append(row[11])
        sensor_co2_yaxis_relay_mtics.append(row[12])
        sensor_co2_yaxis_co2_min.append(row[13])
        sensor_co2_yaxis_co2_max.append(row[14])
        sensor_co2_yaxis_co2_tics.append(row[15])
        sensor_co2_yaxis_co2_mtics.append(row[16])
        sensor_co2_relays_up.append(row[17])
        sensor_co2_relays_down.append(row[18])
        pid_co2_relay_high.append(row[19])
        pid_co2_outmin_high.append(row[20])
        pid_co2_outmax_high.append(row[21])
        pid_co2_relay_low.append(row[22])
        pid_co2_outmin_low.append(row[23])
        pid_co2_outmax_low.append(row[24])
        pid_co2_or.append(row[25])
        pid_co2_set.append(row[26])
        pid_co2_set_dir.append(row[27])
        pid_co2_period.append(row[28])
        pid_co2_p.append(row[29])
        pid_co2_i.append(row[30])
        pid_co2_d.append(row[31])

    # Convert string of comma-separated values to a 2-dimensional list of integers
    global sensor_co2_relays_up_list
    sensor_co2_relays_up_list = []
    for i in range(0, len(sensor_co2_relays_up)):
        if sensor_co2_relays_up[i] != '':
            sensor_co2_relays_up_list.append(sensor_co2_relays_up[i].split(","))
            sensor_co2_relays_up_list[i] = map(int, sensor_co2_relays_up_list[i])

    global sensor_co2_relays_down_list
    sensor_co2_relays_down_list = []
    for i in range(0, len(sensor_co2_relays_down)):
        if sensor_co2_relays_down[i] != '':
            sensor_co2_relays_down_list.append(sensor_co2_relays_down[i].split(","))
            sensor_co2_relays_down_list[i] = map(int, sensor_co2_relays_down_list[i])

    global conditional_co2_number_sensor
    global conditional_co2_number_conditional
    conditional_co2_number_sensor = []
    conditional_co2_number_conditional = []

    cur.execute('SELECT id FROM co2sensor')
    for row in cur:
        conditional_co2_number_sensor.append(row[0])

    cur.execute('SELECT id FROM co2sensorconditional ')
    for row in cur:
        conditional_co2_number_conditional.append(row[0])

    global conditional_co2_id
    global conditional_co2_name
    global conditional_co2_state
    global conditional_co2_condition
    global conditional_co2_direction
    global conditional_co2_setpoint
    global conditional_co2_period
    global conditional_co2_sel_relay
    global conditional_co2_relay
    global conditional_co2_relay_state
    global conditional_co2_relay_seconds_on
    global conditional_co2_sel_command
    global conditional_co2_do_command
    global conditional_co2_sel_notify
    global conditional_co2_do_notify
    global conditional_co2_time_notify

    # There may be multiple conditional statements per sensor.
    # get_3d_array() will initialize (to 0) a 3-dimensional array with the length of indexes
    # equal to the number of sensors and the number of conditionals per each sensor.
    # Elements are then set and accessed with conditional_x[sensor_number][conditonal_number][0]
    conditional_co2_id = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_name = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_state = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_direction = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_setpoint = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_period = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_sel_relay = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_relay = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_relay_state = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_relay_seconds_on = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_sel_command = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_do_command = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_sel_notify = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_do_notify = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)
    conditional_co2_time_notify = get_3d_array(len(conditional_co2_number_sensor), len(conditional_co2_number_conditional), 1)

    for j in range(0, len(conditional_co2_number_sensor)):
        cur.execute("""SELECT id,
                              name,
                              state,
                              direction,
                              setpoint,
                              period,
                              sel_relay,
                              relay,
                              relay_state,
                              relay_seconds_on,
                              sel_command,
                              do_command,
                              sel_notify,
                              do_notify
                       FROM   co2sensorconditional
                       WHERE  sensor = ? """, (str(j),))
        count = 0
        for row in cur:
            conditional_co2_id[j][count][0] = row[0]
            conditional_co2_name[j][count][0] = row[1]
            conditional_co2_state[j][count][0] = row[2]
            conditional_co2_direction[j][count][0] = row[3]
            conditional_co2_setpoint[j][count][0] = row[4]
            conditional_co2_period[j][count][0] = row[5]
            conditional_co2_sel_relay[j][count][0] = row[6]
            conditional_co2_relay[j][count][0] = row[7]
            conditional_co2_relay_state[j][count][0] = row[8]
            conditional_co2_relay_seconds_on[j][count][0] = row[9]
            conditional_co2_sel_command[j][count][0] = row[10]
            if row[11] is None:
                conditional_co2_do_command[j][count][0] = row[11]
            else:
                if "\'\'" not in row[11]:
                    conditional_co2_do_command[j][count][0] = row[11]
                else:
                    conditional_co2_do_command[j][count][0] = row[11].replace("\'\'", "\'")
            conditional_co2_sel_notify[j][count][0] = row[12]
            conditional_co2_do_notify[j][count][0] = row[13]
            conditional_co2_time_notify[j][count][0] = 0
            count += 1

    cur.execute("""SELECT id,
                          name,
                          pin,
                          device,
                          period,
                          pre_measure_relay,
                          pre_measure_dur,
                          activated,
                          graph,
                          yaxis_relay_min,
                          yaxis_relay_max,
                          yaxis_relay_tics,
                          yaxis_relay_mtics,
                          yaxis_temp_min,
                          yaxis_temp_max,
                          yaxis_temp_tics,
                          yaxis_temp_mtics,
                          yaxis_press_min,
                          yaxis_press_max,
                          yaxis_press_tics,
                          yaxis_press_mtics,
                          temp_relays_up,
                          temp_relays_down,
                          temp_relay_high,
                          temp_outmin_high,
                          temp_outmax_high,
                          temp_relay_low,
                          temp_outmin_low,
                          temp_outmax_low,
                          temp_or,
                          temp_set,
                          temp_set_direction,
                          temp_period,
                          temp_p,
                          temp_i,
                          temp_d,
                          press_relays_up,
                          press_relays_down,
                          press_relay_high,
                          press_outmin_high,
                          press_outmax_high,
                          press_relay_low,
                          press_outmin_low,
                          press_outmax_low,
                          press_or,
                          press_set,
                          press_set_direction,
                          press_period,
                          press_p,
                          press_i,
                          press_d
                   FROM   presssensor """)
    for row in cur:
        sensor_press_id.append(row[0])
        sensor_press_name.append(row[1])
        sensor_press_pin.append(row[2])
        sensor_press_device.append(row[3])
        sensor_press_period.append(row[4])
        sensor_press_premeasure_relay.append(row[5])
        sensor_press_premeasure_dur.append(row[6])
        sensor_press_activated.append(row[7])
        sensor_press_graph.append(row[8])
        sensor_press_yaxis_relay_min.append(row[9])
        sensor_press_yaxis_relay_max.append(row[10])
        sensor_press_yaxis_relay_tics.append(row[11])
        sensor_press_yaxis_relay_mtics.append(row[12])
        sensor_press_yaxis_temp_min.append(row[13])
        sensor_press_yaxis_temp_max.append(row[14])
        sensor_press_yaxis_temp_tics.append(row[15])
        sensor_press_yaxis_temp_mtics.append(row[16])
        sensor_press_yaxis_press_min.append(row[17])
        sensor_press_yaxis_press_max.append(row[18])
        sensor_press_yaxis_press_tics.append(row[19])
        sensor_press_yaxis_press_mtics.append(row[20])
        sensor_press_temp_relays_up.append(row[21])
        sensor_press_temp_relays_down.append(row[22])
        pid_press_temp_relay_high.append(row[23])
        pid_press_temp_outmin_high.append(row[24])
        pid_press_temp_outmax_high.append(row[25])
        pid_press_temp_relay_low.append(row[26])
        pid_press_temp_outmin_low.append(row[27])
        pid_press_temp_outmax_low.append(row[28])
        pid_press_temp_or.append(row[29])
        pid_press_temp_set.append(row[30])
        pid_press_temp_set_dir.append(row[31])
        pid_press_temp_period.append(row[32])
        pid_press_temp_p.append(row[33])
        pid_press_temp_i.append(row[34])
        pid_press_temp_d.append(row[35])
        sensor_press_press_relays_up.append(row[36])
        sensor_press_press_relays_down.append(row[37])
        pid_press_press_relay_high.append(row[38])
        pid_press_press_outmin_high.append(row[39])
        pid_press_press_outmax_high.append(row[40])
        pid_press_press_relay_low.append(row[41])
        pid_press_press_outmin_low.append(row[42])
        pid_press_press_outmax_low.append(row[43])
        pid_press_press_or.append(row[44])
        pid_press_press_set.append(row[45])
        pid_press_press_set_dir.append(row[46])
        pid_press_press_period.append(row[47])
        pid_press_press_p.append(row[48])
        pid_press_press_i.append(row[49])
        pid_press_press_d.append(row[50])

    # Convert string of comma-separated values to a 2-dimensional list of integers
    global sensor_press_temp_relays_up_list
    sensor_press_temp_relays_up_list = []
    for i in range(0, len(sensor_press_temp_relays_up)):
        if sensor_press_temp_relays_up[i] != '':
            sensor_press_temp_relays_up_list.append(sensor_press_temp_relays_up[i].split(","))
            sensor_press_temp_relays_up_list[i] = map(int, sensor_press_temp_relays_up_list[i])

    global sensor_press_temp_relays_down_list
    sensor_press_temp_relays_down_list = []
    for i in range(0, len(sensor_press_temp_relays_down)):
        if sensor_press_temp_relays_down[i] != '':
            sensor_press_temp_relays_down_list.append(sensor_press_temp_relays_down[i].split(","))
            sensor_press_temp_relays_down_list[i] = map(int, sensor_press_temp_relays_down_list[i])

    global sensor_press_press_relays_up_list
    sensor_press_press_relays_up_list = []
    for i in range(0, len(sensor_press_press_relays_up)):
        if sensor_press_press_relays_up[i] != '':
            sensor_press_press_relays_up_list.append(sensor_press_press_relays_up[i].split(","))
            sensor_press_press_relays_up_list[i] = map(int, sensor_press_press_relays_up_list[i])

    global sensor_press_press_relays_down_list
    sensor_press_press_relays_down_list = []
    for i in range(0, len(sensor_press_press_relays_down)):
        if sensor_press_press_relays_down[i] != '':
            sensor_press_press_relays_down_list.append(sensor_press_press_relays_down[i].split(","))
            sensor_press_press_relays_down_list[i] = map(int, sensor_press_press_relays_down_list[i])

    global conditional_press_number_sensor
    global conditional_press_number_conditional
    conditional_press_number_sensor = []
    conditional_press_number_conditional = []

    cur.execute('SELECT id FROM presssensor')
    for row in cur:
        conditional_press_number_sensor.append(row[0])

    cur.execute('SELECT id FROM presssensorconditional')
    for row in cur:
        conditional_press_number_conditional.append(row[0])

    global conditional_press_id
    global conditional_press_name
    global conditional_press_state
    global conditional_press_condition
    global conditional_press_direction
    global conditional_press_setpoint
    global conditional_press_period
    global conditional_press_sel_relay
    global conditional_press_relay
    global conditional_press_relay_state
    global conditional_press_relay_seconds_on
    global conditional_press_sel_command
    global conditional_press_do_command
    global conditional_press_sel_notify
    global conditional_press_do_notify
    global conditional_press_time_notify

    # There may be multiple conditional statements per sensor.
    # get_3d_array() will initialize (to 0) a 3-dimensional array with the length of indexes
    # equal to the number of sensors and the number of conditionals per each sensor.
    # Elements are then set and accessed with conditional_x[sensor_number][conditonal_number][0]
    conditional_press_id = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_name = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_state = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_condition = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_direction = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_setpoint = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_period = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_sel_relay = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_relay = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_relay_state = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_relay_seconds_on = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_sel_command = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_do_command = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_sel_notify = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_do_notify = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)
    conditional_press_time_notify = get_3d_array(len(conditional_press_number_sensor), len(conditional_press_number_conditional), 1)

    for j in range(0, len(conditional_press_number_sensor)):
        cur.execute("""SELECT id,
                              name,
                              state,
                              condition,
                              direction,
                              setpoint,
                              period,
                              sel_relay,
                              relay,
                              relay_state,
                              relay_seconds_on,
                              sel_command,
                              do_command,
                              sel_notify,
                              do_notify
                       FROM   presssensorconditional
                       WHERE  sensor = ? """, (str(j),))
        count = 0
        for row in cur:
            conditional_press_id[j][count][0] = row[0]
            conditional_press_name[j][count][0] = row[1]
            conditional_press_state[j][count][0] = row[2]
            conditional_press_condition[j][count][0] = row[3]
            conditional_press_direction[j][count][0] = row[4]
            conditional_press_setpoint[j][count][0] = row[5]
            conditional_press_period[j][count][0] = row[6]
            conditional_press_sel_relay[j][count][0] = row[7]
            conditional_press_relay[j][count][0] = row[8]
            conditional_press_relay_state[j][count][0] = row[9]
            conditional_press_relay_seconds_on[j][count][0] = row[10]
            conditional_press_sel_command[j][count][0] = row[11]
            if row[12] is None:
                conditional_press_do_command[j][count][0] = row[12]
            else:
                if "\'\'" not in row[12]:
                    conditional_press_do_command[j][count][0] = row[12]
                else:
                    conditional_press_do_command[j][count][0] = row[12].replace("\'\'", "\'")
            conditional_press_sel_notify[j][count][0] = row[13]
            conditional_press_do_notify[j][count][0] = row[14]
            conditional_press_time_notify[j][count][0] = 0
            count += 1

    cur.execute('SELECT id, name, relay, state, durationon, durationoff FROM timers')
    for row in cur:
        timer_id.append(row[0])
        timer_name.append(row[1])
        timer_relay.append(row[2])
        timer_state.append(row[3])
        timer_duration_on.append(row[4])
        timer_duration_off.append(row[5])

    cur.execute('SELECT host, ssl, port, user, pass, email_from, wait_time FROM smtp')
    for row in cur:
        smtp_host = row[0]
        smtp_ssl = row[1]
        smtp_port = row[2]
        smtp_user = row[3]
        smtp_pass = row[4]
        smtp_email_from = row[5]
        smtp_wait_time = row[6]

    cur.close()

    for i in range(0, len(sensor_t_id)):
        timerTSensorLog.append(0)

    for i in range(0, len(sensor_ht_id)):
        timerHTSensorLog.append(0)

    for i in range(0, len(sensor_co2_id)):
        timerCo2SensorLog.append(0)

    for i in range(0, len(sensor_press_id)):
        timerPressSensorLog.append(0)

    for i in range(0, len(timer_id)):
        timer_time.append(0)

    if len(on_duration_timer) != len(relay_id):
        on_duration_timer = []
        for i in range(0, len(relay_id)):
            on_duration_timer.append(0)

    if len(on_duration_seconds) != len(relay_id):
        on_duration_seconds = []
        for i in range(0, len(relay_id)):
            on_duration_seconds.append(0)

    global timerTConditional
    global timerHTConditional
    global timerCO2Conditional
    global timerPressConditional

    timerTConditional = [[0 for j in xrange(len(conditional_t_number_conditional))] for i in xrange(len(conditional_t_number_sensor))]
    timerHTConditional = [[0 for j in xrange(len(conditional_ht_number_conditional))] for i in xrange(len(conditional_ht_number_sensor))]
    timerCO2Conditional = [[0 for j in xrange(len(conditional_co2_number_conditional))] for i in xrange(len(conditional_co2_number_sensor))]
    timerPressConditional = [[0 for j in xrange(len(conditional_press_number_conditional))] for i in xrange(len(conditional_press_number_sensor))]
    
    for j in range(0, len(conditional_t_number_sensor)):
        for k in range(0, len(conditional_t_number_conditional)):
            if conditional_t_id[j][k][0] != 0:
                timerTConditional[j][k] = 0

    for j in range(0, len(conditional_ht_number_sensor)):
        for k in range(0, len(conditional_ht_number_conditional)):
            if conditional_ht_id[j][k][0] != 0:
                timerHTConditional[j][k] = 0

    for j in range(0, len(conditional_co2_number_sensor)):
        for k in range(0, len(conditional_co2_number_conditional)):
            if conditional_co2_id[j][k][0] != 0:
                timerCO2Conditional[j][k] = 0

    for j in range(0, len(conditional_press_number_sensor)):
        for k in range(0, len(conditional_press_number_conditional)):
            if conditional_press_id[j][k][0] != 0:
                timerPressConditional[j][k] = 0

    sensor_t_read_temp_c = [0] * len(sensor_t_id)
    sensor_ht_dewpt_c = [0] * len(sensor_ht_id)
    sensor_ht_read_hum = [0] * len(sensor_ht_id)
    sensor_ht_read_temp_c = [0] * len(sensor_ht_id)
    sensor_co2_read_co2 = [0] * len(sensor_co2_id)
    sensor_press_read_alt = [0] * len(sensor_press_id)
    sensor_press_read_press = [0] * len(sensor_press_id)
    sensor_press_read_temp_c = [0] * len(sensor_press_id)

    pid_t_temp_alive = []
    pid_ht_temp_alive = []
    pid_ht_hum_alive = []
    pid_co2_alive = []
    pid_press_temp_alive = []
    pid_press_press_alive = []
    
    pid_t_temp_alive = [1] * len(sensor_t_id)
    pid_ht_temp_alive = [1] * len(sensor_ht_id)
    pid_ht_hum_alive = [1] * len(sensor_ht_id)
    pid_co2_alive = [1] * len(sensor_co2_id)
    pid_press_temp_alive = [1] * len(sensor_press_id)
    pid_press_press_alive = [1] * len(sensor_press_id)

    pause_daemon = 0


#################################################
#               GPIO Manipulation               #
#################################################

# Initialize all relay GPIO pins
def initialize_all_gpio():
    logging.info("[GPIO Initialize] Set GPIO mode to BCM numbering, all set GPIOs as output")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Initialize GPIOs from all 8 relays
    for i in range(0, len(relay_id)):
        if relay_pin[i] > 0:
            GPIO.setup(relay_pin[i], GPIO.OUT)
    logging.info("[GPIO Initialize] Turning off all relays")
    Relays_Off()
    logging.info("[GPIO Initialize] Turning on all relays set to on at startup")
    Relays_Start()


# Initialize specified GPIO pin
def initialize_gpio(relay):
    logging.info("[GPIO Initialize] Set GPIO mode to BCM numbering, GPIO %s as output", relay_pin[relay])
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    #initialize one GPIO
    if relay_pin[relay] > 0:
        GPIO.setup(relay_pin[relay], GPIO.OUT)
        relay_onoff(relay + 1, 'off')


# Turn Relays Off
def Relays_Off():
    for i in range(0, len(relay_id)):
        if relay_pin[i] > 0:
            if relay_trigger[i] == 0:
                GPIO.output(relay_pin[i], 1)
            else:
                GPIO.output(relay_pin[i], 0)


# Turn Select Relays On
def Relays_Start():
    for i in range(0, len(relay_id)):
        if relay_pin[i] > 0:
            if relay_trigger[i] == 0:
                if relay_start_state[i] == 1:
                    GPIO.output(relay_pin[i], 0)
                else:
                    GPIO.output(relay_pin[i], 1)
            else: 
                if relay_start_state[i] == 1:
                    GPIO.output(relay_pin[i], 1)
                else:
                    GPIO.output(relay_pin[i], 0)

# 
# TODO: rename relay_id_ when relay_id is no longer a global variable
# 
def read_relay(relay_id_):
    """
    Read the state of a relay

    :param relay_id_: Relay number
    :type relay_id_: int
    :return: State of the relay as a string.  Either 'on' or 'off'
    :rtype: str
    """
    relay_active_low = relay_trigger[relay_id_ - 1] == 0 and GPIO.input(relay_pin[relay_id_ - 1]) == 0
    relay_active_high = relay_trigger[relay_id_ - 1] == 1 and GPIO.input(relay_pin[relay_id_ - 1]) == 1

    if relay_active_low or relay_active_high:
        return "on"
    else:
        return "off"


# Change GPIO (Select) to a specific state (State)
def set_relay_gpio(relay, State):
    if relay == 0:
        logging.warning("[GPIO Write] 0 is an invalid relay number. Check your configuration.")
    else:
        logging.debug("[GPIO Write] Setting relay %s (%s) to %s (was %s)", relay, relay_name[relay - 1], State, GPIO.input(relay_pin[relay - 1]))
        GPIO.output(relay_pin[relay - 1], State)


# Turn relay on or off and use conditionals
def relay_onoff(relay, state):
    if relay_trigger[relay - 1] == 1 and state == 'on':
        if enable_max_amps == 1:
            total_amps = 0
            for i in range(0, len(relay_id)):
                if (relay_trigger[i] == 0 and GPIO.input(relay_pin[i]) == 0) or (relay_trigger[i] == 1 and GPIO.input(relay_pin[i]) == 1):
                    total_amps += relay_amps[i]
            if ((relay_trigger[relay - 1] == 0 and GPIO.input(relay_pin[relay - 1]) == 1) or (
                    relay_trigger[relay - 1] == 1 and GPIO.input(relay_pin[relay - 1]) == 0)):
                total_amps += relay_amps[relay - 1]
            if total_amps > max_amps:
                logging.warning("[Daemon] Cannot turn relay %s (%s) On. If this relay turns on, there will be %s amps being drawn, which exceeds the maximum set draw of %s amps.", relay, relay_name[relay - 1], total_amps, max_amps)
                return 1
        set_relay_gpio(relay, 1)
    elif relay_trigger[relay - 1] == 0 and state == 'on':
        if enable_max_amps == 1:
            total_amps = 0
            for i in range(0, len(relay_id)):
                if (relay_trigger[i] == 0 and GPIO.input(relay_pin[i]) == 0) or (relay_trigger[i] == 1 and GPIO.input(relay_pin[i]) == 1):
                    total_amps += relay_amps[i]   
            if ((relay_trigger[relay - 1] == 0 and GPIO.input(relay_pin[relay - 1]) == 1) or (
                    relay_trigger[relay - 1] == 1 and GPIO.input(relay_pin[relay - 1]) == 0)):
                total_amps += relay_amps[relay - 1]
            if total_amps > max_amps:
                logging.warning("[Daemon] Cannot turn relay %s (%s) On. If this relay turns on, there will be %s amps being drawn, which exceeds the maximum set draw of %s amps.", relay, relay_name[relay - 1], total_amps, max_amps)
                return 1
        set_relay_gpio(relay, 0)

    elif relay_trigger[relay - 1] == 0 and state == 'off':
        set_relay_gpio(relay, 1)
    elif relay_trigger[relay - 1] == 1 and state == 'off':
        set_relay_gpio(relay, 0)

    for i in range(0, len(conditional_relay_id)):
        if state == 'on':
            if conditional_relay_ifrelay[i] == relay and conditional_relay_ifaction[i] == 'on' and conditional_relay_ifduration[i] == 0:
                if conditional_relay_sel_relay[i]:
                    if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                        rod = threading.Thread(target=relay_on_duration, args=(conditional_relay_dorelay[i], conditional_relay_doduration[i], 0, relay_trigger, relay_pin,))
                        rod.start()
                    else:
                        relay_onoff(conditional_relay_dorelay[i], conditional_relay_doaction[i])
                if conditional_relay_sel_command[i]:
                    p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, errors = p.communicate()
                    logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
                if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                    logging.debug("[Relay Conditional %s (%s)] True: Notify %s", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i])
                    if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                        message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                    else:
                        message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                    email(conditional_relay_do_notify[i], message)
                    conditional_relay_time_notify[i] = time.time() + smtp_wait_time
                elif conditional_relay_sel_notify[i]:
                    logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)
        elif state == 'off':
            if conditional_relay_ifrelay[i] == relay and conditional_relay_ifaction[i] == 'off':
                if conditional_relay_sel_relay[i]:
                    if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                        rod = threading.Thread(target=relay_on_duration, args=(conditional_relay_dorelay[i], conditional_relay_doduration[i], 0, relay_trigger, relay_pin,))
                        rod.start()
                    else:
                        relay_onoff(conditional_relay_dorelay[i], conditional_relay_doaction[i])
                if conditional_relay_sel_command[i]:
                    p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, errors = p.communicate()
                    logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
                if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                    if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                        message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                    else:
                        message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                    email(conditional_relay_do_notify[i], message)
                    conditional_relay_time_notify[i] = time.time() + smtp_wait_time
                elif conditional_relay_sel_notify[i]:
                    logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)


# Turn relay off without conditional check
def relay_off(relay, local_relay_pin, local_relay_trigger):
    logging.debug("[Relay Off] Relay %s turning off.", relay)
    if local_relay_trigger[relay - 1] == 0:
        GPIO.output(local_relay_pin[relay - 1], 1)
    else:
        GPIO.output(local_relay_pin[relay - 1], 0)


# Turn relay on for a specific duration
def relay_on_timed(relay, seconds):
    relay_on_duration(relay, seconds, 0, relay_trigger, relay_pin)


# Set relay on for a specific duration (seconds may be negative)
def relay_on_duration(relay, seconds, sensor, local_relay_trigger, local_relay_pin):
    global on_duration_timer
    global on_duration_seconds
    if enable_max_amps == 1:
        total_amps = 0
        for i in range(0, len(relay_id)):
            if (local_relay_trigger[i] == 0 and GPIO.input(local_relay_pin[i]) == 0) or (local_relay_trigger[i] == 1 and GPIO.input(local_relay_pin[i]) == 1):
                total_amps += relay_amps[i]
        if ((local_relay_trigger[relay - 1] == 0 and GPIO.input(local_relay_pin[relay - 1]) == 1) or (
                local_relay_trigger[relay - 1] == 1 and GPIO.input(local_relay_pin[relay - 1]) == 0)):
            total_amps += relay_amps[relay - 1]
        if total_amps > max_amps:
            logging.warning("[Daemon] Cannot turn relay %s (%s) On. If this relay turns on, there will be %s amps being drawn, which exceeds the maximum set draw of %s amps.", relay, relay_name[relay - 1], total_amps, max_amps)
            return 1

    if (((local_relay_trigger[relay - 1] == 0 and GPIO.input(local_relay_pin[relay - 1]) == 0) or (
            local_relay_trigger[relay - 1] == 1 and GPIO.input(local_relay_pin[relay - 1]) == 1)) and
            on_duration_timer[relay - 1] > time.time()):
        logging.debug("[Relay Duration] Relay %s (%s) is already On for a duration (%.1f sec with %.1f sec remaining). Recording the amount of time the relay has been on (%.1f sec) to log and updating On duration to %.1f seconds.", relay, relay_name[relay - 1], on_duration_seconds[relay - 1], (on_duration_timer[relay - 1] - time.time()), (on_duration_seconds[relay - 1] - (on_duration_timer[relay - 1] - time.time())), seconds)
        wrl = threading.Thread(target=mycodoLog.write_relay_log, args=(relay, (on_duration_seconds[relay - 1] - (on_duration_timer[relay - 1] - time.time())), sensor, local_relay_pin[relay - 1],))
        wrl.start()
        on_duration_timer[relay - 1] = time.time() + abs(seconds)
        on_duration_seconds[relay - 1] = abs(seconds)

        for i in range(0, len(conditional_relay_id)):
            if conditional_relay_ifrelay[i] == relay and conditional_relay_ifaction[i] == 'on':
                if conditional_relay_ifduration[i] == seconds:
                    if conditional_relay_sel_relay[i]:
                        if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                            rod = threading.Thread(target=relay_on_duration, args=(conditional_relay_dorelay[i], conditional_relay_doduration[i], sensor, relay_trigger, relay_pin,))
                            rod.start()
                        elif (conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] == 0) or conditional_relay_doaction[i] == 'off':
                            relay_onoff(conditional_relay_dorelay[i], conditional_relay_doaction[i])
                    if conditional_relay_sel_command[i]:
                        p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        output, errors = p.communicate()
                        logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
                    if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                        logging.debug("[Relay Conditional %s (%s)] True: Notify %s", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i])
                        if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                            message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                        else:
                            message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                        email(conditional_relay_do_notify[i], message)
                        conditional_relay_time_notify[i] = time.time() + smtp_wait_time
                    elif conditional_relay_sel_notify[i]:
                        logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)
                elif conditional_relay_ifduration[i] == 0:
                    if conditional_relay_sel_relay[i]:
                        relay_onoff(conditional_relay_dorelay[i], conditional_relay_doaction[i])
                    if conditional_relay_sel_command[i]:
                        p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        output, errors = p.communicate()
                        logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
                    if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                        logging.debug("[Relay Conditional %s (%s)] True: Notify %s", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i])
                        if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                            message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                        else:
                            message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                        email(conditional_relay_do_notify[i], message)
                        conditional_relay_time_notify[i] = time.time() + smtp_wait_time
                    elif conditional_relay_sel_notify[i]:
                        logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)
        return 1

    elif ((local_relay_trigger[relay - 1] == 0 and GPIO.input(local_relay_pin[relay - 1]) == 0) or (local_relay_trigger[relay - 1] == 1 and GPIO.input(local_relay_pin[relay - 1]) == 1)) and on_duration_timer[relay - 1] < time.time():
        logging.debug("[Relay Duration] Relay %s (%s) is set On without a duration. Turning into a duration (%.1f).", relay, relay_name[relay - 1], seconds)
    
    on_duration_seconds[relay - 1] = abs(seconds)
    on_duration_timer[relay - 1] = time.time() + abs(seconds)

    logging.debug("[Relay Duration] Relay %s (%s) On for %s seconds.", relay, relay_name[relay - 1], round(abs(seconds), 1))

    # Turn relay on
    GPIO.output(local_relay_pin[relay - 1], local_relay_trigger[relay - 1])

    try:
        for i in range(0, len(conditional_relay_id)):
            if conditional_relay_ifrelay[i] == relay and conditional_relay_ifaction[i] == 'on':
                if conditional_relay_ifduration[i] == seconds:
                    if conditional_relay_sel_relay[i]:
                        if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                            rod = threading.Thread(target=relay_on_duration, args=(conditional_relay_dorelay[i], conditional_relay_doduration[i], sensor, relay_trigger, relay_pin,))
                            rod.start()
                        elif (conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] == 0) or conditional_relay_doaction[i] == 'off':
                            relay_onoff(conditional_relay_dorelay[i], conditional_relay_doaction[i])
                    if conditional_relay_sel_command[i]:
                        p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        output, errors = p.communicate()
                        logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
                    if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                        logging.debug("[Relay Conditional %s (%s)] True: Notify %s", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i])
                        if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                            message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                        else:
                            message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                        email(conditional_relay_do_notify[i], message)
                        conditional_relay_time_notify[i] = time.time() + smtp_wait_time
                    elif conditional_relay_sel_notify[i]:
                        logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)
                elif conditional_relay_ifduration[i] == 0:
                    if conditional_relay_sel_relay[i]:
                        relay_onoff(conditional_relay_dorelay[i], conditional_relay_doaction[i])
                    if conditional_relay_sel_command[i]:
                        p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        output, errors = p.communicate()
                        logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
                    if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                        logging.debug("[Relay Conditional %s (%s)] True: Notify %s", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i])
                        if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                            message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                        else:
                            message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                        email(conditional_relay_do_notify[i], message)
                        conditional_relay_time_notify[i] = time.time() + smtp_wait_time
                    elif conditional_relay_sel_notify[i]:
                        logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)

        if pause_daemon:
            logging.warning("[Relay Duration] SQL database reloaded while Relay %s is in a timed on duration. Turning off and cancelling current timer.", relay)
            relay_off(relay, local_relay_pin, local_relay_trigger)
        else:
            while client_que != 'TerminateServer' and on_duration_timer[relay - 1] > time.time():
                if pause_daemon:
                    relay_off(relay, local_relay_pin, local_relay_trigger)
                    logging.warning("[Relay Duration] SQL database reloaded while Relay %s is in a timed on duration. Turning off and cancelling current timer.", relay)
                    break
                if (local_relay_trigger[relay - 1] == 0 and GPIO.input(local_relay_pin[relay - 1]) == 1) or (local_relay_trigger[relay - 1] == 1 and GPIO.input(local_relay_pin[relay - 1]) == 0):
                    relay_off(relay, local_relay_pin, local_relay_trigger)
                    logging.warning("[Relay Duration] Relay %s detected as off during a timed on duration. Turning off and cancelling current timer.", relay, relay_name[relay - 1])
                    break
                time.sleep(0.1)

    except Exception, error:
        relay_off(relay, local_relay_pin, local_relay_trigger)
        logging.warning("[Relay Duration] Exception caught while Relay %s was supposed to be on for %.1f seconds.",
                        relay, seconds)
        logging.warning("[Relay Duration] Exception error: %s", error)
        if conditional_relay_ifrelay[i] == relay and conditional_relay_ifaction[i] == 'off' and conditional_relay_doaction[i] == 'off':
            if conditional_relay_sel_relay[i]:
                relay_onoff(conditional_relay_dorelay[i], 'off')
        return 1
    
    # Turn relay off
    relay_off(relay, local_relay_pin, local_relay_trigger)

    if on_duration_seconds[relay - 1] == 0:
        wrl = threading.Thread(target=mycodoLog.write_relay_log, args=(relay, seconds, sensor, local_relay_pin[relay - 1],))
        wrl.start()
    else:
        wrl = threading.Thread(target=mycodoLog.write_relay_log, args=(relay, on_duration_seconds[relay - 1], sensor, local_relay_pin[relay - 1],))
        wrl.start()

    while pause_daemon:
        time.sleep(0.1)

    for i in range(0, len(conditional_relay_id)):
        if conditional_relay_ifrelay[i] == relay and conditional_relay_ifaction[i] == 'off' and conditional_relay_doaction[i] == 'off':
            if conditional_relay_sel_relay[i]:
                relay_onoff(conditional_relay_dorelay[i], 'off')
            if conditional_relay_sel_command[i]:
                p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, errors = p.communicate()
                logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
            if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                logging.debug("[Relay Conditional %s (%s)] True: Notify %s", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i])
                if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                    message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                else:
                    message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                email(conditional_relay_do_notify[i], message)
                conditional_relay_time_notify[i] = time.time() + smtp_wait_time
            elif conditional_relay_sel_notify[i]:
                logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)
        elif conditional_relay_ifrelay[i] == relay and conditional_relay_ifaction[i] == 'off' and conditional_relay_doaction[i] == 'on':
            if conditional_relay_sel_relay[i]:
                if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                    rod = threading.Thread(target=relay_on_duration, args=(conditional_relay_dorelay[i], conditional_relay_doduration[i], sensor, relay_trigger, relay_pin,))
                    rod.start()
                elif (conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] == 0) or conditional_relay_doaction[i] == 'off':
                    relay_onoff(conditional_relay_dorelay[i], conditional_relay_doaction[i])
            if conditional_relay_sel_command[i]:
                p = subprocess.Popen(conditional_relay_do_command[i], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, errors = p.communicate()
                logging.debug("[Relay Conditional %s (%s)] Execute command: %s Command output: %s Command errors: %s", i + 1, conditional_relay_name[i], conditional_relay_do_command[i], output, errors)
            if conditional_relay_sel_notify[i] and conditional_relay_time_notify[i] < time.time():
                logging.debug("[Relay Conditional %s (%s)] True: Notify %s", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i])
                if conditional_relay_doaction[i] == 'on' and conditional_relay_doduration[i] != 0:
                    message = "Relay Conditional %s (%s): Relay %s turned %s for %s seconds." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i], conditional_relay_doduration[i])
                else:
                    message = "Relay Conditional %s (%s): Relay %s turned %s." % ((i + 1), conditional_relay_name[i], relay, conditional_relay_doaction[i])
                email(conditional_relay_do_notify[i], message)
                conditional_relay_time_notify[i] = time.time() + smtp_wait_time
            elif conditional_relay_sel_notify[i]:
                logging.debug("[Relay Conditional %s (%s)] True: Waiting to notify %s. %s seconds left to wait to be able to notify again (of %s seconds).", i + 1, conditional_relay_name[i], conditional_relay_do_notify[i], (smtp_wait_time - (smtp_wait_time - (conditional_relay_time_notify[i] - time.time()))), smtp_wait_time)
    logging.debug("[Relay Duration] Relay %s (%s) Off (was On for %s seconds)", relay, relay_name[relay - 1], round(abs(seconds), 1))
    return 1


#################################################
#              Email Notification               #
#################################################

# Email notification
def email(email_to, message):
    try:
        if smtp_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
            server.starttls()
        server.login(smtp_user, smtp_pass)
        msg = MIMEText(message.decode('utf-8'), 'plain', 'utf-8')
        msg['Subject'] = "Mycodo Notification (%s)" % socket.getfqdn()
        msg['From'] = smtp_email_from
        msg['To'] = email_to
        server.sendmail(msg['From'], msg['To'].split(","), msg.as_string())
        server.quit()
    except Exception, error:
        logging.warning("[Email Notification] Error: %s", error)
        logging.warning("[Email Notification] Cound not send email to %s with message: %s", email_to, message)


#################################################
#                 Miscellaneous                 #
#################################################

# Check if string represents an integer value
def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


# Check if string represents a float value
def represents_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# Log timestamp format
def timestamp():
    return datetime.datetime.now().strftime('%Y %m %d %H %M %S')


def get_3d_array(z, y, x=1):
    """
    Get a three dimensional array initialized with zeroes.  These are normally set to values
    later in the code.

    Example:
        get_3d_array(3,2,4) -> [[[0,0,0],[0,0,0]],[[0,0,0],[0,0,0]],[[0,0,0],[0,0,0]],[[0,0,0],[0,0,0]]]

    :return: Array of zeroes
    :rtype: list

    :param x: How many values
    :type x: int
    :param y: How many lists of values
    :type y: int
    :param z: How many lists of lists
    :type z: int
    """

    return [[[0 for _ in range(x)] for _ in range(y)] for _ in range(z)]


#################################################
#                 Main Program                  #
#################################################
def main():
    if not os.geteuid() == 0:
        print "\nScript must be executed as root\n"
        logging.warning("Must be executed as root.")
        usage()
        sys.exit("Must be executed as root")
    if menu() == 1:
        if not os.path.exists(lock_directory):
            os.makedirs(lock_directory)
        runlock = LockFile(daemon_lock_path)
        while not runlock.i_am_locking():
            try:
                runlock.acquire(timeout=1)
            except:
                logging.warning("Lock file present: %s. Ensure another instance of the Mycodo daemon is not running and delete the file.", runlock.path)
                error = "Error: Lock file present: %s" % runlock.path
                print error
                usage()
                sys.exit(error)
        read_sql()
        initialize_all_gpio()
        daemon(a, b)
        runlock.release()
try:
    main()
except:
    logging.exception(1)
