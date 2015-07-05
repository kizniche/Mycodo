#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo.py - A temperature and sensor_ht_read_hum regulation system that allows
#              easy configuration and monitoring through a web interface.
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

#### Configure Directories ####
install_directory = "/var/www/mycodo"

import Adafruit_DHT
import ConfigParser
import datetime
import fcntl
import filecmp
import fileinput
import getopt
import logging
import os
import re
import rpyc
import RPi.GPIO as GPIO
import serial
import smtplib
import sqlite3
import subprocess
import sys
import threading
import time
from array import *
from email.mime.text import MIMEText
from lockfile import LockFile
from rpyc.utils.server import ThreadedServer

sql_database = "%s/config/mycodo.sqlite3" % install_directory
config_file = "%s/config/mycodo.cfg" % install_directory
relay_script = "%s/cgi-bin/relay.sh" % install_directory
image_path = "%s/images" % install_directory
log_path = "%s/log" % install_directory
daemon_log_file_tmp = "%s/daemon-tmp.log" % log_path
daemon_log_file = "%s/daemon.log" % log_path
sensor_ht_log_file_tmp = "%s/sensor-ht-tmp.log" % log_path
sensor_ht_log_file = "%s/sensor-ht.log" % log_path
sensor_co2_log_file_tmp = "%s/sensor-co2-tmp.log" % log_path
sensor_co2_log_file = "%s/sensor-co2.log" % log_path
relay_log_file_tmp = "%s/relay-tmp.log" % log_path
relay_log_file = "%s/relay.log" % log_path

logging.basicConfig(
    filename = daemon_log_file_tmp,
    level = logging.INFO,
    format = '%(asctime)s [%(levelname)s] %(message)s')

lock_directory = "/var/lock/mycodo"
sql_lock_path = "%s/config" % lock_directory
daemon_lock_path = "%s/daemon" % lock_directory
sensor_ht_lock_path = "%s/sensor-ht" % lock_directory
sensor_co2_lock_path = "%s/sensor-co2" % lock_directory
relay_lock_path = "%s/relay" % lock_directory
logs_lock_path = "%s/logs" % lock_directory

# GPIO pins (BCM numbering) and name of devices attached to relay
relay_num = None
relay_pin = [0] * 9
relay_name = [0] * 9
relay_trigger = [0] * 9

# Temperature & Humidity Sensors
sensor_ht_num = 0
sensor_ht_name = [0] * 5
sensor_ht_device = [0] * 5
sensor_ht_pin = [0] * 5
sensor_ht_period = [0] * 5
sensor_ht_log = [0] * 5
sensor_ht_graph = [0] * 5
sensor_ht_read_temp_c = [0] * 5
sensor_ht_read_hum = [0] * 5
sensor_ht_dewpt_c = [0] * 5

# Temperature PID
pid_temp_relay = [0] * 5
pid_temp_set = [0] * 5
pid_temp_period = [0] * 5
pid_temp_p = [0] * 5
pid_temp_i = [0] * 5
pid_temp_d = [0] * 5
pid_temp_or = [0] * 5
pid_temp_alive = [1] * 5
pid_temp_down = 0
pid_temp_up = 0
pid_temp_number = None

# Humidity PID
pid_hum_relay = [0] * 5
pid_hum_set = [0] * 5
pid_hum_period = [0] * 5
pid_hum_p = [0] * 5
pid_hum_i = [0] * 5
pid_hum_d = [0] * 5
pid_hum_or = [0] * 5
pid_hum_alive = [1] * 5
pid_hum_down = 0
pid_hum_up = 0
pid_hum_number = None

# CO2 Sensors
sensor_co2_num = 0
sensor_co2_name = [0] * 5
sensor_co2_device = [0] * 5
sensor_co2_pin = [0] * 5
sensor_co2_period = [0] * 5
sensor_co2_log = [0] * 5
sensor_co2_graph = [0] * 5
sensor_co2_read_co2 = [0] * 5

# CO2 PID
pid_co2_relay = [0] * 5
pid_co2_set = [0] * 5
pid_co2_period = [0] * 5
pid_co2_p = [0] * 5
pid_co2_i = [0] * 5
pid_co2_d = [0] * 5
pid_co2_or = [0] * 5
pid_co2_alive = [1] * 5
pid_co2_down = 0
pid_co2_up = 0
pid_co2_number = None

# Timers
timer_num = None
timer_name = [0] * 9
timer_relay = [0] * 9
timer_state = [0] * 9
timer_duration_on = [0] * 9
timer_duration_off = [0] * 9
timer_change = 0

# SMTP notify
smtp_host = None
smtp_ssl = None
smtp_port = None
smtp_user = None
smtp_pass = None
smtp_email_from = None
smtp_email_to = None

# Miscellaneous
camera_light = None
server = None
client_que = '0'
client_var = None
terminate = False

# Threaded server that receives commands from mycodo-client.py
class ComServer(rpyc.Service):
    def exposed_ChangeRelay(self, relay, state):
        if (state == 1):
            logging.info("[Client command] Changing Relay %s to HIGH", relay)
            relay_onoff(int(relay), 1)
        elif (state == 0):
            logging.info("[Client command] Changing Relay %s to LOW", relay)
            relay_onoff(int(relay), 0)
        else:
            logging.info("[Client command] Turning Relay %s On for %s seconds", relay, state)
            rod = threading.Thread(target = relay_on_duration, 
                args = (int(relay), int(state), 0,))
            rod.start()
        return 1
    def exposed_ChangeTimer(self, timernumber, timerstate, timerrelay,
            timerdurationon, timerdurationoff):
        global client_que
        global timer_relay
        global timer_state
        global timer_duration_on
        global timer_duration_off
        global timer_change
        timer_relay[timernumber] = timerrelay
        timer_state[timernumber] = timerstate
        timer_duration_on[timernumber] = timerdurationon
        timer_duration_off[timernumber] = timerdurationoff
        timer_change = timernumber
        logging.info("[Client command] Change Timer: %s, State: %s, Relay: %s, On: %s, Off %s",
            timernumber, timerstate, timerrelay,
            timerdurationon, timerdurationoff)
        write_sql()
        client_que = 'TimerChange'
        return 1
    def exposed_ChangeCO2Sensor(self, sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph):
        global sensor_co2_name
        global sensor_co2_device
        global sensor_co2_pin
        global sensor_co2_period
        global sensor_co2_log
        global sensor_co2_graph
        logging.info("[Client command] Change CO2 sensor %s: %s: Device: %s Pin: %s Period: %s sec. Activated: %s Graph: %s",
            sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph)
        sensor_co2_name[sensornumber] = sensorname
        sensor_co2_device[sensornumber] = sensordevice
        sensor_co2_pin[sensornumber] = sensorpin
        sensor_co2_period[sensornumber] = sensorperiod
        sensor_co2_log[sensornumber] = sensoractivated
        sensor_co2_graph[sensornumber] = sensorgraph
        write_sql()
        return 1
    def exposed_ChangeHTSensor(self, sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph):
        global sensor_ht_name
        global sensor_ht_device
        global sensor_ht_pin
        global sensor_ht_period
        global sensor_ht_log
        global sensor_ht_graph
        logging.info("[Client command] Change HT sensor %s: %s: Device: %s Pin: %s Period: %s sec. Activated: %s Graph: %s",
            sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph)
        sensor_ht_name[sensornumber] = sensorname
        sensor_ht_device[sensornumber] = sensordevice
        sensor_ht_pin[sensornumber] = sensorpin
        sensor_ht_period[sensornumber] = sensorperiod
        sensor_ht_log[sensornumber] = sensoractivated
        sensor_ht_graph[sensornumber] = sensorgraph
        write_sql()
        return 1
    def exposed_ChangeCO2OR(self, sensornum, override):
        global pid_co2_or
        global pid_co2_number
        global pid_co2_down
        global pid_co2_up
        logging.info("[Client command] Change CO2OR for sensor %s to %s",
            sensornum, override)
        pid_co2_or[sensornum] = override
        pid_co2_number = sensornum
        pid_co2_down = 1
        while pid_co2_down == 1:
            time.sleep(0.1)
        write_sql()
        read_sql()
        pid_co2_up = 1
        while pid_co2_up:
            time.sleep(0.1)
        return 1
    def exposed_ChangeCO2PID(self, sensornum, relay, set, p, i, d, period):
        global pid_co2_relay
        global pid_co2_set
        global pid_co2_period
        global pid_co2_p
        global pid_co2_i
        global pid_co2_d
        global pid_co2_or
        global pid_co2_number
        global pid_co2_down
        global pid_co2_up
        logging.info("[Client command] Change Co2 PID for sensor %s: Relay: %s Set: %s P: %s I: %s D: %s Period: %s",
            sensornum, relay, set, p , i, d, period)
        pid_co2_relay[sensornum] = relay
        pid_co2_set[sensornum] = set
        pid_co2_period[sensornum] = period
        pid_co2_p[sensornum] = p
        pid_co2_i[sensornum] = i
        pid_co2_d[sensornum] = d
        pid_co2_number = sensornum
        pid_co2_down = 1
        while pid_co2_down == 1:
            time.sleep(0.1)
        write_sql()
        read_sql()
        pid_co2_up = 1
        while pid_co2_up:
            time.sleep(0.1)
        return 1
    def exposed_ChangeTempOR(self, sensornum, override):
        global pid_temp_or
        global pid_temp_number
        global pid_temp_down
        global pid_temp_up
        logging.info("[Client command] Change pid_temp_or for sensor %s to %s",
            sensornum, override)
        pid_temp_or[sensornum] = override
        pid_temp_number = sensornum
        pid_temp_down = 1
        while pid_temp_down == 1:
            time.sleep(0.1)
        write_sql()
        read_sql()
        pid_temp_up = 1
        while pid_temp_up:
            time.sleep(0.1)
        return 1
    def exposed_ChangeTempPID(self, sensornum, relay, set, p, i, d, period):
        global pid_temp_relay
        global pid_temp_set
        global pid_temp_period
        global pid_temp_p
        global pid_temp_i
        global pid_temp_d
        global pid_temp_or
        global pid_temp_number
        global pid_temp_down
        global pid_temp_up
        logging.info("[Client command] Change Temp PID for sensor %s: Relay: %s Set: %s P: %s I: %s D: %s Period: %s",
            sensornum, relay, set, p , i, d, period)
        pid_temp_relay[sensornum] = relay
        pid_temp_set[sensornum] = set
        pid_temp_period[sensornum] = period
        pid_temp_p[sensornum] = p
        pid_temp_i[sensornum] = i
        pid_temp_d[sensornum] = d
        pid_temp_number = sensornum
        pid_temp_down = 1
        while pid_temp_down == 1:
            time.sleep(0.1)
        write_sql()
        read_sql()
        pid_temp_up = 1
        while pid_temp_up:
            time.sleep(0.1)
        return 1
    def exposed_ChangeHumOR(self, sensornum, override):
        global pid_hum_or
        global pid_hum_number
        global pid_hum_down
        global pid_hum_up
        pid_hum_or[sensornum] = override
        logging.info("[Client command] Change pid_hum_or for sensor %s to %s",
            sensornum, override)
        pid_hum_number = sensornum
        pid_hum_down = 1
        while pid_hum_down == 1:
            time.sleep(0.1)
        write_sql()
        read_sql()
        pid_hum_up = 1
        while pid_hum_up:
            time.sleep(0.1)
        return 1
    def exposed_ChangeHumPID(self, sensornum, relay, set, p, i, d, period):
        global pid_hum_relay
        global pid_hum_set
        global pid_hum_period
        global pid_hum_p
        global pid_hum_i
        global pid_hum_d
        global pid_hum_or
        global pid_hum_number
        global pid_hum_down
        global pid_hum_up
        logging.info("[Client command] Change Hum PID for sensor %s: Relay: %s Set: %s P: %s I: %s D: %s Period: %s",
            sensornum, relay, set, p , i, d, period)
        pid_hum_relay[sensornum] = relay
        pid_hum_set[sensornum] = set
        pid_hum_period[sensornum] = period
        pid_hum_p[sensornum] = p
        pid_hum_i[sensornum] = i
        pid_hum_d[sensornum] = d
        
        pid_hum_number = sensornum
        pid_hum_down = 1
        while pid_hum_down == 1:
            time.sleep(0.1)
        write_sql()
        read_sql()
        pid_hum_up = 1
        while pid_hum_up:
            time.sleep(0.1)
        return 1
    def exposed_ChangeRelayNames(self, relayname1, relayname2, relayname3,
            relayname4, relayname5, relayname6, relayname7, relayname8):
        global relay_name
        relay_name[1] = relayname1
        relay_name[2] = relayname2
        relay_name[3] = relayname3
        relay_name[4] = relayname4
        relay_name[5] = relayname5
        relay_name[6] = relayname6
        relay_name[7] = relayname7
        relay_name[8] = relayname8
        logging.info("[Client command] Change Relay Names: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            relay_name[1], relay_name[2], relay_name[3], relay_name[4],
            relay_name[5], relay_name[6], relay_name[7], relay_name[8])
        write_sql()
        return 1
    def exposed_ChangeRelayPins(self, relaypin1, relaypin2, relaypin3,
            relaypin4, relaypin5, relaypin6, relaypin7, relaypin8):
        global relay_pin
        relay_pin[1] = relaypin1
        relay_pin[2] = relaypin2
        relay_pin[3] = relaypin3
        relay_pin[4] = relaypin4
        relay_pin[5] = relaypin5
        relay_pin[6] = relaypin6
        relay_pin[7] = relaypin7
        relay_pin[8] = relaypin8
        logging.info("[Client command] Change Relay Pins: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            relay_pin[1], relay_pin[2], relay_pin[3], relay_pin[4],
            relay_pin[5], relay_pin[6], relay_pin[7], relay_pin[8])
        write_sql()
        return 1
    def exposed_ChangeRelayTriggers(self, relaytrigger1, relaytrigger2, relaytrigger3,
            relaytrigger4, relaytrigger5, relaytrigger6, relaytrigger7, relaytrigger8):
        global relay_trigger
        relay_trigger[1] = relaytrigger1
        relay_trigger[2] = relaytrigger2
        relay_trigger[3] = relaytrigger3
        relay_trigger[4] = relaytrigger4
        relay_trigger[5] = relaytrigger5
        relay_trigger[6] = relaytrigger6
        relay_trigger[7] = relaytrigger7
        relay_trigger[8] = relaytrigger8
        logging.info("[Client command] Change Relay Triggers: 1: %s, 2: %s, 3: %s, 4: %s, 5: %s, 6: %s, 7: %s, 8: %s",
            relay_trigger[1], relay_trigger[2], relay_trigger[3], relay_trigger[4],
            relay_trigger[5], relay_trigger[6], relay_trigger[7], relay_trigger[8])
        write_sql()
        return 1
    def exposed_GenerateGraph(self, graph_out_file, id, sensor):
        logging.info("[Client command] Generate Graph: %s %s %s", graph_out_file, id, sensor)
        generate_graph(graph_out_file, id, sensor)
        return 1
    def exposed_Modify_Variables(self, *variable_list):
        logging.info("[Client command] Request to change variables")
        modify_var(*variable_list)
        return 1
    def exposed_ReadCO2Sensor(self, pin, sensor):
        logging.info("[Client command] Read CO2 Sensor %s from GPIO pin %s", sensor, pin)
        if (sensor == 'K30'):
            read_co2_sensor(sensor)
            return (sensor_co2_read_co2)
        else:
            return 'Invalid Sensor Name'
    def exposed_ReadHTSensor(self, pin, sensor):
        logging.info("[Client command] Read HT Sensor %s from GPIO pin %s", sensor, pin)
        if (sensor == 'DHT11'): device = Adafruit_DHT.DHT11
        elif (sensor == 'DHT22'): device = Adafruit_DHT.DHT22
        elif (sensor == 'AM2302'): device = Adafruit_DHT.AM2302
        else: return 'Invalid Sensor Name'
        hum, tc = Adafruit_DHT.read_retry(device, pin)
        return (tc, hum)
    def exposed_Terminate(self, remoteCommand):
        global client_que
        global terminate
        terminate = True
        client_que = 'TerminateServer'
        logging.info("[Client command] terminate threads and shut down")
        return 1
    def exposed_WriteHTSensorLog(self, sensor):
        global client_que
        global client_var
        client_var = sensor
        client_que = 'write_ht_sensor_log'
        if sensor:
            logging.info("[Client command] Read HT sensor number %s and append log", sensor)
        else:
            logging.info("[Client command] Read all HT sensors and append log")
        global change_sensor_log
        change_sensor_log = 1
        while (change_sensor_log):
            time.sleep(0.1)
        return 1
    def exposed_WriteCO2SensorLog(self, sensor):
        global client_que
        global client_var
        client_var = sensor
        client_que = 'write_co2_sensor_log'
        if sensor:
            logging.info("[Client command] Read CO2 sensor number %s and append log", sensor)
        else:
            logging.info("[Client command] Read all CO2 sensors and append log")
        global change_sensor_log
        change_sensor_log = 1
        while (change_sensor_log):
            time.sleep(0.1)
        return 1

class ComThread(threading.Thread):
    def run(self):
        global server
        server = ThreadedServer(ComServer, port = 18812)
        server.start()

# PID controller for sensor_ht_read_hum
class Humidity_PID:
    def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0,
            Integrator_max=500, Integrator_min=-500):
        self.Kp=P
        self.Ki=I
        self.Kd=D
        self.Derivator=Derivator
        self.Integrator=Integrator
        self.Integrator_max=Integrator_max
        self.Integrator_min=Integrator_min
        self.set_point=0.0
        self.error=0.0
    def update(self, current_value):
        """Calculate PID output value from reference input and feedback"""
        self.error = self.set_point - current_value
        self.P_value = self.Kp * self.error
        self.D_value = self.Kd * ( self.error - self.Derivator)
        self.Derivator = self.error
        self.Integrator = self.Integrator + self.error
        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min
        self.I_value = self.Integrator * self.Ki
        PID = self.P_value + self.I_value + self.D_value
        return PID
    def setPoint(self, set_point):
        """Initilize the setpoint of PID"""
        self.set_point = set_point
        self.Integrator=0
        self.Derivator=0
    def setIntegrator(self, Integrator):
        self.Integrator = Integrator
    def setDerivator(self, Derivator):
        self.Derivator = Derivator
    def setKp(self,P):
        self.Kp=P
    def setKi(self,I):
        self.Ki=I
    def setKd(self,D):
        self.Kd=D
    def getPoint(self):
        return self.set_point
    def getError(self):
        return self.error
    def getIntegrator(self):
        return self.Integrator
    def getDerivator(self):
        return self.Derivator

# PID controller for temperature
class Temperature_PID:
    def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0,
            Integrator_max=500, Integrator_min=-500):
        self.Kp=P
        self.Ki=I
        self.Kd=D
        self.Derivator=Derivator
        self.Integrator=Integrator
        self.Integrator_max=Integrator_max
        self.Integrator_min=Integrator_min
        self.set_point=0.0
        self.error=0.0
    def update(self,current_value):
        """Calculate PID output value from reference input and feedback"""
        self.error = self.set_point - current_value
        self.P_value = self.Kp * self.error
        self.D_value = self.Kd * ( self.error - self.Derivator)
        self.Derivator = self.error
        self.Integrator = self.Integrator + self.error
        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min
        self.I_value = self.Integrator * self.Ki
        PID = self.P_value + self.I_value + self.D_value
        return PID
    def setPoint(self,set_point):
        """Initilize the setpoint of PID"""
        self.set_point = set_point
        self.Integrator=0
        self.Derivator=0
    def setIntegrator(self, Integrator):
        self.Integrator = Integrator
    def setDerivator(self, Derivator):
        self.Derivator = Derivator
    def setKp(self,P):
        self.Kp=P
    def setKi(self,I):
        self.Ki=I
    def setKd(self,D):
        self.Kd=D
    def getPoint(self):
        return self.set_point
    def getError(self):
        return self.error
    def getIntegrator(self):
        return self.Integrator
    def getDerivator(self):
        return self.Derivator

# PID controller for CO2
class CO2_PID:
    def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0,
            Integrator_max=500, Integrator_min=-500):
        self.Kp=P
        self.Ki=I
        self.Kd=D
        self.Derivator=Derivator
        self.Integrator=Integrator
        self.Integrator_max=Integrator_max
        self.Integrator_min=Integrator_min
        self.set_point=0.0
        self.error=0.0
    def update(self, current_value):
        """Calculate PID output value from reference input and feedback"""
        self.error = self.set_point - current_value
        self.P_value = self.Kp * self.error
        self.D_value = self.Kd * ( self.error - self.Derivator)
        self.Derivator = self.error
        self.Integrator = self.Integrator + self.error
        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min
        self.I_value = self.Integrator * self.Ki
        PID = self.P_value + self.I_value + self.D_value
        return PID
    def setPoint(self, set_point):
        """Initilize the setpoint of PID"""
        self.set_point = set_point
        self.Integrator=0
        self.Derivator=0
    def setIntegrator(self, Integrator):
        self.Integrator = Integrator
    def setDerivator(self, Derivator):
        self.Derivator = Derivator
    def setKp(self,P):
        self.Kp=P
    def setKi(self,I):
        self.Ki=I
    def setKd(self,D):
        self.Kd=D
    def getPoint(self):
        return self.set_point
    def getError(self):
        return self.error
    def getIntegrator(self):
        return self.Integrator
    def getDerivator(self):
        return self.Derivator

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
    a = 'silent'
    b = 'info'
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hl:v',
            ["help", "log", "verbose"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        return 2

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            return 1
        elif opt in ("-l", "--log"):
            if (arg == 'w'): b = 'warning'
            elif (arg == 'd'): b = 'debug'
        elif opt in ("-v", "--verbose"):
            a = 'verbose'
        else:
            assert False, "Fail"

    daemon(a, b)
    return 1

    
#################################################
#                    Daemon                     #
#################################################

# Read sensors, modify relays based on sensor values, write sensor/relay
# logs, and receive/execute commands from mycodo-client.py
def daemon(output, log):
    global pid_temp_alive
    global pid_temp_down
    global pid_temp_up
    global pid_hum_alive
    global pid_hum_down
    global pid_hum_up
    global pid_co2_alive
    global pid_co2_down
    global pid_co2_up
    global change_sensor_log
    global server
    global client_que
    timer_time = [0] * 9
    timerHTSensorLog  = [0] * 5
    timerCo2SensorLog  = [0] * 2
    
    if (log == 'warning'):
        logging.getLogger().setLevel(logging.WARNING)
    elif (log == 'info'):
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.DEBUG)

    if (output == 'verbose'):
        # define a Handler which writes DEBUG messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)
    
    logging.info("[Daemon] Daemon Started")
    logging.info("[Daemon} Communication server thread starting")
    ct = ComThread()
    ct.daemon = True
    ct.start()
    time.sleep(1)
    
    logging.info("[Daemon] Reading SQL database and initializing variables")
    read_sql()
    
    # Initial sensor readings
    logging.info("[Daemon] Conducting initial sensor readings from %s HT and %s CO2 sensors", sum(sensor_ht_log), sum(sensor_co2_log))
    for i in range(1, sensor_ht_num+1):
        if sensor_ht_device[i] != 'Other' and sensor_ht_log[i] == 1:
            read_dht_sensor(i)
            time.sleep(2) # Ensure a minimum of 2 seconds between sensor reads
    
    for i in range(1, sensor_co2_num+1):
        if sensor_co2_device[i] != 'Other' and sensor_co2_log[i] == 1:
            read_co2_sensor(i)
            time.sleep(2) # Ensure a minimum of 2 seconds between sensor reads
    
    timerLogBackup = int(time.time()) + 21600 # 21600 seconds = 6 hours
    
    for i in range(1, sensor_ht_num+1):
        timerHTSensorLog[i] = int(time.time()) + sensor_ht_period[i]
        
    for i in range(1, sensor_co2_num+1):
        timerCo2SensorLog[i] = int(time.time()) + sensor_co2_period[i]
    
    for i in range(1, 9):
        timer_time[i] = int(time.time())
    
    threadst = []
    threadsh = []
    threadsc = []
    
    for i in range(1, 5):
        rod = threading.Thread(target = temperature_monitor, 
            args = ('Thread-%d' % i, i,))
        rod.start()
        threadst.append(rod)

    for i in range(1, 5):
        rod = threading.Thread(target = humidity_monitor, 
            args = ('Thread-%d' % i, i,))
        rod.start()
        threadsh.append(rod)
        
    for i in range(1, 5):
        rod = threading.Thread(target = co2_monitor, 
            args = ('Thread-%d' % i, i,))
        rod.start()
        threadsc.append(rod)

    while True: # Main loop of the daemon
        if client_que != '0': # Run remote commands issued by mycodo-client.py
            if client_que == 'write_co2_sensor_log':
                logging.debug("[Client command] Write CO2 Sensor Log")
                if (client_var != 0):
                    read_co2_sensor(client_var)
                    write_co2_sensor_log(client_var)
                else:
                    for i in range(1, int(sensor_co2_num)+1): 
                        read_co2_sensor(i)
                        write_co2_sensor_log(i)
                        time.sleep(2)
                change_sensor_log = 0
            elif client_que == 'write_ht_sensor_log':
                logging.debug("[Client command] Write HT Sensor Log")
                if (client_var != 0):
                    read_dht_sensor(client_var)
                    write_dht_sensor_log(client_var)
                else:
                    for i in range(1, int(sensor_ht_num)+1): 
                        read_dht_sensor(i)
                        write_dht_sensor_log(i)
                        time.sleep(2)
                change_sensor_log = 0
            elif client_que == 'TerminateServer':
                logging.info("[Daemon] Turning off relays")
                Relays_Off()
                logging.info("[Daemon] Backing up logs")
                Concatenate_Logs()
                pid_temp_alive = [0] * 5
                for t in threadst:
                    t.join()
                pid_hum_alive = [0] * 5
                for t in threadsh:
                    t.join()
                pid_co2_alive = [0] * 5
                for t in threadsc:
                    t.join()
                server.close()
                logging.info("[Daemon] Exiting Python")
                return 0
            elif client_que == 'TimerChange':
                timer_time[timer_change] = 0
                if (timer_state[timer_change] == 0 and timer_relay[timer_change] != 0):
                    relay_onoff(timer_relay[timer_change], 0)
                    
            client_que = '0'

        if pid_temp_down:
            logging.info("[Daemon] Shutting Down Temperature PID Thread-%s", pid_temp_number)
            pid_temp_alive[pid_temp_number] = 0
            while pid_temp_alive[pid_temp_number] != 2:
                time.sleep(0.1)
            if (relay_trigger[int(pid_temp_relay[1])] == 0): gpio_change(int(pid_temp_relay[1]), 1)
            else: gpio_change(int(pid_temp_relay[1]), 0)
            pid_temp_alive[pid_temp_number] = 1
            pid_temp_down = 0
        if pid_temp_up == 1:
            logging.info("[Daemon] Starting Temperature PID Thread-%s", pid_temp_number)
            rod = threading.Thread(target = temperature_monitor, 
                args = ('Thread-%d' % pid_temp_number, pid_temp_number,))
            rod.start()
            pid_temp_up = 0
            
        if pid_hum_down:
            logging.info("[Daemon] Shutting Down Humidity PID Thread-%s", pid_hum_number)
            pid_hum_alive[pid_hum_number] = 0
            while pid_hum_alive[pid_hum_number] != 2:
                time.sleep(0.1)
            if (relay_trigger[int(pid_hum_relay[1])] == 0): gpio_change(int(pid_hum_relay[1]), 1)
            else: gpio_change(int(pid_hum_relay[1]), 1)
            pid_hum_alive[pid_hum_number] = 1
            pid_hum_down = 0
        if pid_hum_up == 1:
            logging.info("[Daemon] Starting Temperature PID Thread-%s", pid_hum_number)
            rod = threading.Thread(target = humidity_monitor, 
                args = ('Thread-%d' % pid_hum_number, pid_hum_number,))
            rod.start()
            pid_hum_up = 0
            
        if pid_co2_down:
            logging.info("[Daemon] Shutting Down CO2 PID Thread-%s", pid_co2_number)
            pid_co2_alive[pid_co2_number] = 0
            while pid_co2_alive[pid_co2_number] != 2:
                time.sleep(0.1)
            if (relay_trigger[int(pid_co2_relay[1])] == 0): gpio_change(int(pid_co2_relay[1]), 1)
            else: gpio_change(int(pid_co2_relay[1]), 0)
            pid_co2_alive[pid_co2_number] = 1
            pid_co2_down = 0
        if pid_co2_up == 1:
            logging.info("[Daemon] Starting CO2 PID Thread-%s", pid_co2_number)
            rod = threading.Thread(target = co2_monitor, 
                args = ('Thread-%d' % pid_co2_number, pid_co2_number,))
            rod.start()
            pid_co2_up = 0

        # Write temperature and sensor_ht_read_hum to sensor log
        for i in range(1, int(sensor_ht_num)+1):
            if int(time.time()) > timerHTSensorLog[i] and sensor_ht_device[i] != 'Other' and sensor_ht_log[i] == 1:
                logging.debug("[Timer Expiration] Read sensor %s every %s seconds: Write sensor log", i, sensor_ht_period[i])
                if read_dht_sensor(i) == 1:
                    write_dht_sensor_log(i)
                timerHTSensorLog[i] = int(time.time()) + sensor_ht_period[i]

        # Write CO2 to sensor log
        for i in range(1, int(sensor_co2_num)+1):
            if int(time.time()) > timerCo2SensorLog[i] and sensor_co2_device[i] != 'Other' and sensor_co2_log[i] == 1:
                if read_co2_sensor(i) == 1:
                    write_co2_sensor_log(i)
                timerCo2SensorLog[i] = int(time.time()) + sensor_co2_period[i]
        
        # Concatenate local log with tempfs log every 6 hours
        if int(time.time()) > timerLogBackup:
            Concatenate_Logs()
            timerLogBackup = int(time.time()) + 21600
        
        # Handle timers
        for i in range(1, 9):
            if int(time.time()) > timer_time[i]:
                if timer_state[i] == 1:
                    logging.debug("[Timer Expiration] Timer %s: Turn Relay %s on for %s seconds, off %s seconds.", i, timer_relay[i], timer_duration_on[i], timer_duration_off[i])
                    rod = threading.Thread(target = relay_on_duration, 
                        args = (timer_relay[i], timer_duration_on[i], 0,))
                    rod.start()
                    timer_time[i] = int(time.time()) + timer_duration_on[i] + timer_duration_off[i]

        time.sleep(0.1)


#################################################
#                  PID Control                  #
#################################################

# Temperature modulation by PID control
def temperature_monitor(ThreadName, sensor):
    global pid_temp_alive
    timerTemp = 0
    PIDTemp = 0
    logging.info("[PID Temperature-%s] Starting %s", sensor, ThreadName)
    
    if pid_temp_relay[sensor] != 0:
        if relay_trigger[int(pid_temp_relay[sensor])] == 0: gpio_change(int(pid_temp_relay[sensor]), 1)
        else: gpio_change(int(pid_temp_relay[sensor]), 0)
    
    p_temp = Temperature_PID(pid_temp_p[sensor], pid_temp_i[sensor], pid_temp_d[sensor])
    p_temp.setPoint(pid_temp_set[sensor])
    
    while (pid_temp_alive[sensor]):
        if pid_temp_or[sensor] == 0 and pid_temp_down == 0 and pid_temp_relay[sensor] != 0 and sensor_ht_log[sensor] == 1:
            if int(time.time()) > timerTemp:
                logging.debug("[PID Temperature-%s] Reading temperature...", sensor)
                read_dht_sensor(sensor)
                PIDTemp = p_temp.update(float(sensor_ht_read_temp_c[sensor]))
                if (sensor_ht_read_temp_c[sensor] < pid_temp_set[sensor]):
                    logging.debug("[PID Temperature-%s] Temperature (%.1f°C) < (%.1f°C) pid_temp_set", sensor, sensor_ht_read_temp_c[sensor], float(pid_temp_set[sensor]))
                    logging.debug("[PID Temperature-%s] PID = %.1f (seconds)", sensor, PIDTemp)
                    if (PIDTemp > 0 and sensor_ht_read_temp_c[sensor] < pid_temp_set[sensor]):
                        rod = threading.Thread(target = relay_on_duration, 
                            args = (pid_temp_relay[sensor], round(PIDTemp,2), sensor,))
                        rod.start()
                    timerTemp = int(time.time()) + int(PIDTemp) + int(pid_temp_period[sensor])
                else:
                    logging.debug("[PID Temperature-%s] Temperature (%.1f°C) >= (%.1f°C) pid_temp_set, waiting 60 seconds", sensor, sensor_ht_read_temp_c[sensor], pid_temp_set[sensor])
                    logging.debug("[PID Temperature-%s] PID = %.1f (seconds)", sensor, PIDTemp)
                    timerTemp = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID Temperature-%s] Shutting Down %s", sensor, ThreadName)
    pid_temp_alive[sensor] = 2

# Humidity modulation by PID control
def humidity_monitor(ThreadName, sensor):
    global pid_hum_alive
    timerHum = 0
    PIDHum = 0

    logging.info("[PID Humidity-%s] Starting %s", sensor, ThreadName)

    if pid_hum_relay[sensor] != 0:
        if relay_trigger[int(pid_hum_relay[sensor])] == 0: gpio_change(int(pid_hum_relay[sensor]), 1)
        else: gpio_change(int(pid_hum_relay[sensor]), 1)
    
    p_hum = Humidity_PID(pid_hum_p[sensor], pid_hum_i[sensor], pid_hum_d[sensor])
    p_hum.setPoint(pid_hum_set[sensor])

    while (pid_hum_alive[sensor]):
        if pid_hum_or[sensor] == 0 and pid_hum_down == 0 and pid_hum_relay[sensor] != 0 and sensor_ht_log[sensor] == 1:
            if int(time.time()) > timerHum:
                logging.debug("[PID Humidity-%s] Reading Humidity...", sensor)
                read_dht_sensor(sensor)
                PIDHum = p_hum.update(float(sensor_ht_read_hum[sensor]))
                if (sensor_ht_read_hum[sensor] < pid_hum_set[sensor]):
                    logging.debug("[PID Humidity-%s] Humidity (%.1f%%) < (%.1f%%) pid_hum_set", sensor, sensor_ht_read_hum[sensor], float(pid_hum_set[sensor]))
                    logging.debug("[PID Humidity-%s] PID = %.1f (seconds)", sensor, PIDHum)
                    if (PIDHum > 0 and sensor_ht_read_hum[sensor] < pid_hum_set[sensor]):
                        rod = threading.Thread(target = relay_on_duration,
                            args=(pid_hum_relay[sensor], round(PIDHum,2), sensor,))
                        rod.start()
                    timerHum = int(time.time()) + int(PIDHum) + int(pid_hum_period[sensor])
                else:
                    logging.debug("[PID Humidity-%s] Humidity (%.1f%%) >= (%.1f%%) pid_hum_set, waiting 60 seconds", sensor, sensor_ht_read_hum[sensor], pid_hum_set[sensor])
                    logging.debug("[PID Humidity-%s] PID = %.1f (seconds)", sensor, PIDHum)
                    timerHum = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID Humidity-%s] Shutting Down %s", sensor,  ThreadName)
    pid_hum_alive[sensor] = 2

# CO2 modulation by PID control
def co2_monitor(ThreadName, sensor):
    global pid_co2_alive
    timerCo2 = 0
    PIDCo2 = 0

    logging.info("[PID CO2-%s] Starting %s", sensor, ThreadName)

    if pid_co2_relay[sensor] != 0:
        if relay_trigger[int(pid_co2_relay[sensor])] == 0: gpio_change(int(pid_co2_relay[sensor]), 1)
        else: gpio_change(int(pid_co2_relay[sensor]), 1)
    
    p_co2 = CO2_PID(pid_co2_p[sensor], pid_co2_i[sensor], pid_co2_d[sensor])
    p_co2.setPoint(pid_co2_set[sensor])

    while (pid_co2_alive[sensor]):
        if pid_co2_or[sensor] == 0 and pid_co2_down == 0 and pid_co2_relay[sensor] != 0 and sensor_co2_log[sensor] == 1:
            if int(time.time()) > timerCo2:
                logging.debug("[PID CO2-%s] Reading CO2...", sensor)
                read_co2_sensor(sensor)
                PIDCo2 = p_co2.update(float(sensor_co2_read_co2[sensor]))
                if (sensor_co2_read_co2[sensor] > pid_co2_set[sensor]):
                    logging.debug("[PID CO2-%s] CO2 (%.1f%%) > (%.1f%%) setCO2", sensor, sensor_co2_read_co2[sensor], pid_co2_set[sensor])
                    logging.debug("[PID CO2-%s] PID = %.1f (seconds)", sensor, PIDCo2)
                    if (PIDCo2 > 0 and sensor_co2_read_co2[sensor] > pid_co2_set[sensor]):
                        rod = threading.Thread(target = relay_on_duration,
                            args=(pid_co2_relay[sensor], round(PIDCo2,2), sensor,))
                        rod.start()
                    timerCo2 = int(time.time()) + int(PIDCo2) + int(pid_co2_period[sensor])
                else:
                    logging.debug("[PID CO2-%s] CO2 (%.1f%%) <= (%.1f%%) pid_co2_set, waiting 60 seconds", sensor, sensor_co2_read_co2[sensor], pid_co2_set[sensor])
                    logging.debug("[PID CO2-%s] PID = %.1f (seconds)", sensor, PIDCo2)
                    timerCo2 = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID CO2-%s] Shutting Down %s", sensor,  ThreadName)
    pid_co2_alive[sensor] = 2


#################################################
#                Sensor Reading                 #
#################################################
    
# Read CO2 sensor
def read_co2_sensor(sensor):
    global sensor_co2_read_co2
    chkco2 = 1
    
    if (sensor_co2_device[1] == 'K30'): device = 'K30'
    else:
        logging.warning("[Read CO2 Sensor-%s] Cannot read CO2 from an unknown device!", sensor)
        return 0

    logging.debug("[Read CO2 Sensor-%s] Taking first CO2 reading", sensor)
        
    if device == 'K30': co22 = read_K30()
    if co22 == None:
        logging.warning("[Read CO2 Sensor-%s] Could not read CO2!", sensor)
        return 0
    
    logging.debug("[Read CO2 Sensor-%s] CO2: %s", sensor, co22)

    while not terminate:
        logging.debug("[Read CO2 Sensor-%s] Taking second CO2 reading", sensor)
        
        if device == 'K30': sensor_co2_read_co2[sensor] = read_K30()
        if sensor_co2_read_co2[sensor] == 'None':
            logging.warning("[Read CO2 Sensor-%s] Could not read CO2!", sensor)
            return 0

        logging.debug("[Read CO2 Sensor-%s] CO2: %s", sensor, sensor_co2_read_co2[sensor])
        logging.debug("[Read CO2 Sensor-%s] Difference: %s", sensor, abs(co22-sensor_co2_read_co2[sensor]))
            
        if abs(co22-sensor_co2_read_co2[sensor]) > 20 and not terminate:
            co22 = sensor_co2_read_co2[sensor]
            logging.debug("[Read CO2 Sensor-%s] Successive readings > 20 difference: Rereading", sensor)
        elif not terminate:
            logging.debug("[Read CO2 Sensor-%s] Successive readings < 20 difference: keeping.", sensor)
            logging.debug("[Read CO2 Sensor-%s] CO2: %s", sensor, sensor_co2_read_co2[sensor])
            return 1
            
# Read K30 CO2 Sensor
def read_K30():
    time.sleep(2) # Ensure 2 seconds between sensor reads
    ser = serial.Serial("/dev/ttyAMA0", timeout=3) # Wait 3 seconds for reply
    ser.flushInput()
    time.sleep(1)
    ser.write("\xFE\x44\x00\x08\x02\x9F\x25")
    time.sleep(.01)
    resp = ser.read(7)
    if len(resp) == 0:
        return None
    high = ord(resp[3])
    low = ord(resp[4])
    co2 = (high*256) + low
    return co2

# Read the temperature and sensor_ht_read_hum from sensor
def read_dht_sensor(sensor):
    global sensor_ht_read_temp_c
    global sensor_ht_read_hum
    global sensor_ht_dewpt_c
    chktemp = 1
    
    if (sensor_ht_device[1] == 'DHT11'): device = Adafruit_DHT.DHT11
    elif (sensor_ht_device[1] == 'DHT22'): device = Adafruit_DHT.DHT22
    elif (sensor_ht_device[1] == 'AM2302'): device = Adafruit_DHT.AM2302
    else:
        device = 'Other'
        return 'cannot read temperature/humidity from an unknown device'

    logging.debug("[Read HT Sensor-%s] Taking first Temperature/Humidity reading", sensor)
        
    humidity2, tempc2 = Adafruit_DHT.read_retry(device, sensor_ht_pin[sensor])
    
    if humidity2 == None or tempc2 == None:
        logging.warning("[Read HT Sensor-%s] Could not read temperature/humidity!", sensor)
        return 0
        
    logging.debug("[Read HT Sensor-%s] %.1f°C, %.1f%%", sensor, tempc2, humidity2)

    time.sleep(2) # Wait 2 seconds between sensor reads
    
    logging.debug("[Read HT Sensor-%s] Taking second Temperature/Humidity reading", sensor)
            
    while chktemp and not terminate:
        sensor_ht_read_hum[sensor], sensor_ht_read_temp_c[sensor] = Adafruit_DHT.read_retry(device, sensor_ht_pin[sensor])
            
        if sensor_ht_read_hum[sensor] == 'None' or sensor_ht_read_temp_c[sensor] == 'None':
            logging.warning("[Read HT Sensor-%s] Could not read temperature/humidity!", sensor)
            return 0
        
        logging.debug("[Read HT Sensor-%s] %.1f°C, %.1f%%", sensor, sensor_ht_read_temp_c[sensor], sensor_ht_read_hum[sensor])
        logging.debug("[Read HT Sensor-%s] Differences: %.1f°C, %.1f%%", sensor, abs(tempc2-sensor_ht_read_temp_c[sensor]), abs(humidity2-sensor_ht_read_hum[sensor]))
            
        if abs(tempc2-sensor_ht_read_temp_c[sensor]) > 1 or abs(humidity2-sensor_ht_read_hum[sensor]) > 1:
            tempc2 = sensor_ht_read_temp_c[sensor]
            humidity2 = sensor_ht_read_hum[sensor]
            chktemp = 1
            
            logging.debug("[Read HT Sensor-%s] Successive readings > 1 difference: Rereading", sensor)
            time.sleep(2) # Wait 2 seconds between sensor reads
        else:
            chktemp = 0

            logging.debug("[Read HT Sensor-%s] Successive readings < 1 difference: keeping.", sensor)

            temperature_f = float(sensor_ht_read_temp_c[sensor])*9.0/5.0 + 32.0
            sensor_ht_dewpt_c[sensor] = sensor_ht_read_temp_c[sensor] - ((100-sensor_ht_read_hum[sensor]) / 5)
            #sensor_ht_dewpt_f[sensor] = sensor_ht_dewpt_c[sensor] * 9 / 5 + 32
            #sensor_ht_heatindex_f = -42.379 + 2.04901523 * temperature_f + 10.14333127 * sensor_ht_read_hum - 0.22475541 * temperature_f * sensor_ht_read_hum - 6.83783 * 10**-3 * temperature_f**2 - 5.481717 * 10**-2 * sensor_ht_read_hum**2 + 1.22874 * 10**-3 * temperature_f**2 * sensor_ht_read_hum + 8.5282 * 10**-4 * temperature_f * sensor_ht_read_hum**2 - 1.99 * 10**-6 * temperature_f**2 * sensor_ht_read_hum**2
            #sensor_ht_heatindex_c[sensor] = (heatindexf - 32) * (5 / 9)
            
            logging.debug("[Read HT Sensor-%s] Temp: %.1f°C, Hum: %.1f%%, DP: %.1f°C", sensor, sensor_ht_read_temp_c[sensor], sensor_ht_read_hum[sensor], sensor_ht_dewpt_c[sensor])
            time.sleep(2) # Wait 2 seconds between sensor reads
            return 1


#################################################
#           Sensor and Relay Logging            #
#################################################

# Log temperature/sensor_ht_read_hum sensor reading
def write_dht_sensor_log(sensor):
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)
        
    if not terminate:
        lock = LockFile(sensor_ht_lock_path)
        while not lock.i_am_locking():
            try:
                logging.debug("[Write Sensor Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Write Sensor Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Write Sensor Log] Gained lock: %s", lock.path)

        try:
            with open(sensor_ht_log_file_tmp, "ab") as sensorlog:
                sensorlog.write('{0} {1:.1f} {2:.1f} {3:.1f} {4}\n'.format(
                    datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                    sensor_ht_read_temp_c[sensor], sensor_ht_read_hum[sensor], sensor_ht_dewpt_c[sensor], sensor))
                logging.debug("[Write Sensor Log] Data appended to %s", sensor_ht_log_file_tmp)
        except:
            logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_ht_log_file_tmp)

        logging.debug("[Write Sensor Log] Removing lock: %s", lock.path)
        lock.release()

# Log CO2 sensor reading
def write_co2_sensor_log(sensor):
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)
        
    if not terminate:
        lock = LockFile(sensor_co2_lock_path)
        while not lock.i_am_locking():
            try:
                logging.debug("[Write CO2 Sensor Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Write CO2 Sensor Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Write CO2 Sensor Log] Gained lock: %s", lock.path)

        try:
            with open(sensor_co2_log_file_tmp, "ab") as sensorlog:
                sensorlog.write('{0} {1} {2}\n'.format(
                    datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                    sensor_co2_read_co2[sensor], sensor))
                logging.debug("[Write CO2 Sensor Log] Data appended to %s", sensor_co2_log_file_tmp)
        except:
            logging.warning("[Write CO2 Sensor Log] Unable to append data to %s", sensor_co2_log_file_tmp)

        logging.debug("[Write CO2 Sensor Log] Removing lock: %s", lock.path)
        lock.release()

# Log the relay duration
def write_relay_log(relayNumber, relaySeconds, sensor):
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)
    if not terminate:
        lock = LockFile(relay_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Write Relay Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Write Relay Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Write Relay Log] Gained lock: %s", lock.path)
        relay = [0] * 9

        for n in range(1, 9):
            if n == relayNumber:
                relay[relayNumber] = relaySeconds

        try:
            with open(relay_log_file_tmp, "ab") as relaylog:
                relaylog.write('{0} {1} {2} {3} {4} {5} {6} {7} {8} {9}\n'.format(
                    datetime.datetime.now().strftime("%Y %m %d %H %M %S"),
                    relay[1], relay[2], relay[3], relay[4],
                    relay[5], relay[6], relay[7], relay[8], sensor))
        except:
            logging.warning("[Write Relay Log] Unable to append data to %s", relay_log_file_tmp)

        logging.debug("[Write Relay Log] Removing lock: %s", lock.path)
        lock.release()

# Combines the logs on the SD card with the logs on the temporary file system
def Concatenate_Logs():
    logging.debug("[Timer Expiration] Run every 6 hours: Concatenate logs")

    # Daemon Logs
    if not filecmp.cmp(daemon_log_file_tmp, daemon_log_file):
        logging.debug("[Daemon Log] Concatenating daemon logs to %s", daemon_log_file)
        lock = LockFile(logs_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Daemon Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Daemon Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Daemon Log] Gained lock: %s", lock.path)

        try:
            with open(daemon_log_file, 'a') as fout:
                for line in fileinput.input(daemon_log_file_tmp):
                    fout.write(line)
            logging.debug("[Daemon Log] Appended data to %s", daemon_log_file)
        except:
            logging.warning("[Daemon Log] Unable to append data to %s", daemon_log_file)

        open(daemon_log_file_tmp, 'w').close()
        logging.debug("[Daemon Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Daemon Log] Daemon logs the same, skipping.")

    # Humidity & Temperature Logs
    if not filecmp.cmp(sensor_ht_log_file_tmp, sensor_ht_log_file):
        logging.debug("[Sensor Log] Concatenating HT sensor logs to %s", sensor_ht_log_file)
        lock = LockFile(sensor_ht_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Sensor Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Sensor Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Sensor Log] Gained lock: %s", lock.path)

        try:
            with open(sensor_ht_log_file, 'a') as fout:
                for line in fileinput.input(sensor_ht_log_file_tmp):
                    fout.write(line)
            logging.debug("[Daemon Log] Appended HT data to %s", sensor_ht_log_file)
        except:
            logging.warning("[Sensor Log] Unable to append data to %s", sensor_ht_log_file)

        open(sensor_ht_log_file_tmp, 'w').close()
        logging.debug("[Sensor Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Sensor Log] HT Sensor logs the same, skipping.")
    
    # CO2 Logs
    if not filecmp.cmp(sensor_co2_log_file_tmp, sensor_co2_log_file):
        logging.debug("[Sensor Log] Concatenating CO2 sensor logs to %s", sensor_co2_log_file)
        lock = LockFile(sensor_co2_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Sensor Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Sensor Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Sensor Log] Gained lock: %s", lock.path)

        try:
            with open(sensor_co2_log_file, 'a') as fout:
                for line in fileinput.input(sensor_co2_log_file_tmp):
                    fout.write(line)
            logging.debug("[Daemon Log] Appended CO2 data to %s", sensor_co2_log_file)
        except:
            logging.warning("[Sensor Log] Unable to append data to %s", sensor_co2_log_file)

        open(sensor_co2_log_file_tmp, 'w').close()
        logging.debug("[Sensor Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Sensor Log] CO2 Sensor logs the same, skipping.")

    # Relay Logs
    if not filecmp.cmp(relay_log_file_tmp, relay_log_file):
        logging.debug("[Relay Log] Concatenating relay logs to %s", relay_log_file)
        lock = LockFile(relay_lock_path)

        while not lock.i_am_locking():
            try:
                logging.debug("[Relay Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Relay Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()

        logging.debug("[Relay Log] Gained lock: %s", lock.path)

        try:
            with open(relay_log_file, 'a') as fout:
                for line in fileinput.input(relay_log_file_tmp):
                    fout.write(line)
            logging.debug("[Daemon Log] Appended data to %s", relay_log_file)
        except:
            logging.warning("[Relay Log] Unable to append data to %s", relay_log_file)

        open(relay_log_file_tmp, 'w').close()
        logging.debug("[Relay Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Relay Log] Relay logs the same, skipping.")


#################################################
#                Graph Generation               #
#################################################

# Generate gnuplot graph
def generate_graph(graph_out_file, graph_id, sensorn):
    tmp_path = "/var/tmp"
    h = 0
    d = 0

    # Calculate a past date from a number of hours or days ago
    if "1h" in graph_out_file:
        h = 1
        time_ago = '1 Hour'
    elif "6h" in graph_out_file:
        h = 6
        time_ago = '6 Hours'
    elif "1d" in graph_out_file or "dayweek" in graph_out_file:
        d = 1
        time_ago = '1 Day'
    elif "3d" in graph_out_file:
        d = 3
        time_ago = '3 Days'
    elif "1w" in graph_out_file:
        d = 7
        time_ago = '1 Week'
    elif "1m" in graph_out_file:
        d = 30
        time_ago = '1 Month'
    elif "3m" in graph_out_file:
        d = 90
        time_ago = '3 Months'
    elif "legend-full" in graph_out_file:
        h = 6
        time_ago = '6 Hours'
    date_now = datetime.datetime.now().strftime("%Y %m %d %H %M %S")
    date_now_disp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
    date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
    date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%d/%m/%Y %H:%M:%S") 

    # Combine sensor and relay logs on SD card with sensor and relay logs in /tmp
    sensor_ht_log_files_combine = [sensor_ht_log_file, sensor_ht_log_file_tmp]
    sensor_ht_log_generate = "%s/sensor-ht-logs-combined.log" % tmp_path
    with open(sensor_ht_log_generate, 'w') as fout:
        for line in fileinput.input(sensor_ht_log_files_combine):
            fout.write(line)
            
    sensor_co2_log_files_combine = [sensor_co2_log_file, sensor_co2_log_file_tmp]
    sensor_co2_log_generate = "%s/sensor-co2-logs-combined.log" % tmp_path
    with open(sensor_co2_log_generate, 'w') as fout:
        for line in fileinput.input(sensor_co2_log_files_combine):
            fout.write(line)
            
    relay_log_files_combine = [relay_log_file, relay_log_file_tmp]
    relay_log_generate = "%s/relay-logs-combined.log" % tmp_path
    with open(relay_log_generate, 'w') as fout:
        for line in fileinput.input(relay_log_files_combine):
            fout.write(line)

    # Define how many lines to read in file (speeds processing large logs)
    sensor_head = ''
    #sensor_head = ' | head -n 180'
    relay_head = ''
    #relay_head = ' | head -n 180'

    # Axes size constraints
    y1_min = '0'
    y1_max = '100'
    
    if "co2" in graph_out_file:
        y2_min = '0'
        y2_max = '5000'
    else:
        y2_min = '0'
        y2_max = '35'
    
    # Line colors (see comments further down with their use)
    graph_colors = ['#FF3100', '#0772A1', '#00B74A', '#91180B',
                    '#582557', '#04834C', '#DC32E6', '#957EF9',
                    '#CC8D9C', '#717412', '#0B479B',
                    '#7164a3', '#599e86', '#c3ae4f', '#c3744f',
                    ]

    # Write the following output to a file that will be executed with gnuplot 
    gnuplot_graph = "%s/plot-%s-%s.gnuplot" % (tmp_path, graph_out_file, sensorn)
    plot = open(gnuplot_graph, 'w')
    
    plot.write('reset\n') 
    plot.write('set xdata time\n')
    plot.write('set timefmt \"%Y %m %d %H %M %S\"\n')
    
    if "combined" in graph_out_file:
        plot.write('set terminal png size 1000,1500\n')
        plot.write('set output \"' + image_path + '/graph-' + graph_out_file + '-' + graph_id + '.png\"\n')
    elif "separate" in graph_out_file:
        plot.write('set terminal png size 1000,600\n')
        plot.write('set output \"' + image_path + '/graph-' + graph_out_file + '-' + graph_id + '-' + sensorn + '.png\"\n')
    elif "dayweek" in graph_out_file:
        plot.write('set terminal png size 1000,1000\n')
        plot.write('set output \"' + image_path + '/graph-' + graph_out_file + '-' + graph_id + '-' + sensorn + '.png\"\n')
    elif "legend-small" in graph_out_file:
        plot.write('set terminal png size 250,300\n')
        plot.write('set output \"' + image_path + '/graph-' + graph_out_file + '-' + graph_id + '.png\"\n')
    elif "legend-full" in graph_out_file:
        plot.write('set terminal png size 800,500\n')
        plot.write('set output \"' + image_path + '/graph-' + graph_out_file + '-' + graph_id + '.png\"\n')
    
    if "legend-small" not in graph_out_file:
        plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
        plot.write('set format x \"%H:%M\\n%m/%d\"\n')
        plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
        plot.write('set y2range [' + y2_min + ':' + y2_max + ']\n')
        plot.write('set style line 11 lc rgb \'#808080\' lt 1\n')
        plot.write('set border 3 back ls 11\n')
        plot.write('set tics nomirror\n')
        plot.write('set style line 12 lc rgb \'#808080\' lt 0 lw 1\n')
        plot.write('set grid xtics ytics back ls 12\n')
    
    if "dayweek" in graph_out_file:
        plot.write('set mytics 10\n')
        plot.write('set my2tics 5\n')
        plot.write('set ytics 0,20\n')
        if "co2" in graph_out_file:
            plot.write('set y2tics 500\n')
        else:
            plot.write('set y2tics 5\n')
    else:
        plot.write('set my2tics 10\n')
        plot.write('set ytics 10\n')
        if "co2" in graph_out_file:
            plot.write('set y2tics 500\n')
        else:
            plot.write('set y2tics 5\n')
            
    
    plot.write('set style line 11 lc rgb \'#808080\' lt 1\n')
    plot.write('set border 3 back ls 11\n')
    plot.write('set tics nomirror\n')
    plot.write('set style line 12 lc rgb \'#808080\' lt 0 lw 1\n')
    plot.write('set grid xtics ytics back ls 12\n')
       
    # Horizontal lines: separate temperature, sensor_ht_read_hum, and dewpoint
    plot.write('set style line 1 lc rgb \'' + graph_colors[0] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 2 lc rgb \'' + graph_colors[1] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 3 lc rgb \'' + graph_colors[2] + '\' pt 0 ps 1 lt 1 lw 2\n')
    
    # Vertical lines: relays 1 - 8
    plot.write('set style line 4 lc rgb \'' + graph_colors[3] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 5 lc rgb \'' + graph_colors[4] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 6 lc rgb \'' + graph_colors[5] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 7 lc rgb \'' + graph_colors[6] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 8 lc rgb \'' + graph_colors[7] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 9 lc rgb \'' + graph_colors[8] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 10 lc rgb \'' + graph_colors[9] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 11 lc rgb \'' + graph_colors[10] + '\' pt 0 ps 1 lt 1 lw 1\n')
    
    # Horizontal lines: combined temperatures and humidities
    plot.write('set style line 12 lc rgb \'' + graph_colors[11] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 13 lc rgb \'' + graph_colors[12] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 14 lc rgb \'' + graph_colors[13] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 15 lc rgb \'' + graph_colors[14] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('unset key\n')
    
    # Generate a graph with all temperatures and one graph with all humidities 
    if "combined" in graph_out_file:
        plot.write('set multiplot layout 3,1\n')
        plot.write('set origin 0.0,0.66\n')
        plot.write('set title \"Combined Temperatures: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot ')
        if sensor_ht_graph[1]:
            plot.write('\"<awk \'$10 == 1\' ' + sensor_ht_log_generate + sensor_head + '" using 1:7 index 0 title \"T1\" w lp ls 12 axes x1y2')
            if sensor_ht_graph[2] or sensor_ht_graph[3] or sensor_ht_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_ht_graph[2]:
            plot.write('\"<awk \'$10 == 2\' ' + sensor_ht_log_generate + sensor_head + '" u 1:7 index 0 title \"T2\" w lp ls 13 axes x1y2')
            if sensor_ht_graph[3] or sensor_ht_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_ht_graph[3]:
            plot.write('\"<awk \'$10 == 3\' ' + sensor_ht_log_generate + sensor_head + '" u 1:7 index 0 title \"T3\" w lp ls 14 axes x1y2')
            if sensor_ht_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_ht_graph[4]:
            plot.write('\"<awk \'$10 == 4\' ' + sensor_ht_log_generate + sensor_head + '" u 1:7 index 0 title \"T4\" w lp ls 15 axes x1y2\n')
            
        plot.write('set origin 0.0,0.33\n')
        plot.write('set title \"Combined Humidities: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot ')
        if sensor_ht_graph[1]:
            plot.write('\"<awk \'$10 == 1\' ' + sensor_ht_log_generate + sensor_head + '" using 1:8 index 0 title \"H1\" w lp ls 12 axes x1y1')
            if sensor_ht_graph[2] or sensor_ht_graph[3] or sensor_ht_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_ht_graph[2]:
            plot.write('\"<awk \'$10 == 2\' ' + sensor_ht_log_generate + sensor_head + '" u 1:8 index 0 title \"H2\" w lp ls 13 axes x1y1')
            if sensor_ht_graph[3] or sensor_ht_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_ht_graph[3]:
            plot.write('\"<awk \'$10 == 3\' ' + sensor_ht_log_generate + sensor_head + '" u 1:8 index 0 title \"H3\" w lp ls 14 axes x1y1')
            if sensor_ht_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_ht_graph[4]:
            plot.write('\"<awk \'$10 == 4\' ' + sensor_ht_log_generate + sensor_head + '" u 1:8 index 0 title \"H4\" w lp ls 15 axes x1y1\n')
            
        plot.write('set origin 0.0,0.0\n')
        plot.write('set title \"Combined CO2s: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        y2_min = '0'
        y2_max = '5000'
        plot.write('set y2range [' + y2_min + ':' + y2_max + ']\n')
        plot.write('set y2tics 500\n')
        plot.write('plot ')
        if sensor_co2_graph[1]:
            plot.write('\"<awk \'$8 == 1\' ' + sensor_co2_log_generate + sensor_head + '" using 1:7 index 0 title \"CO2-1\" w lp ls 12 axes x1y2')
            if sensor_co2_graph[2] or sensor_co2_graph[3] or sensor_co2_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_co2_graph[2]:
            plot.write('\"<awk \'$8 == 2\' ' + sensor_co2_log_generate + sensor_head + '" u 1:7 index 0 title \"CO2-2\" w lp ls 13 axes x1y2')
            if sensor_co2_graph[3] or sensor_co2_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_co2_graph[3]:
            plot.write('\"<awk \'$8 == 3\' ' + sensor_co2_log_generate + sensor_head + '" u 1:7 index 0 title \"CO2-3\" w lp ls 14 axes x1y2')
            if sensor_co2_graph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensor_co2_graph[4]:
            plot.write('\"<awk \'$8 == 4\' ' + sensor_co2_log_generate + sensor_head + '" u 1:7 index 0 title \"CO2-4\" w lp ls 15 axes x1y2\n')
        plot.write('unset multiplot\n')

    # Generate a graph with temp, hum, and dew point for a specific sensor
    if "htseparate" in graph_out_file:
        plot.write('set title \"Hum/Temp Sensor ' + sensorn + ': ' + sensor_ht_name[int(float(sensorn))] + '\\n\\n' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot \"<awk \'$10 == ' + sensorn + '\' ' + sensor_ht_log_generate + sensor_head + '" using 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, ')
        plot.write('\"\" u 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, ')
        plot.write('\"\" u 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, ')
        
        plot.write('\"<awk \'$15 == ' + sensorn + '\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relay_name[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" u 1:8 index 0 title \"' + relay_name[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" u 1:9 index 0 title \"' + relay_name[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" u 1:10 index 0 title \"' + relay_name[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" u 1:11 index 0 title \"' + relay_name[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" u 1:12 index 0 title \"' + relay_name[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" u 1:13 index 0 title \"' + relay_name[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" u 1:14 index 0 title \"' + relay_name[8] + '\" w impulses ls 11 axes x1y1\n')
        
    if "co2separate" in graph_out_file:
        plot.write('set title \"CO2 Sensor ' + sensorn + ': ' + sensor_co2_name[int(float(sensorn))] + '\\n\\n' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot \"<awk \'$8 == ' + sensorn + '\' ' + sensor_co2_log_generate + sensor_head + '" using 1:7 index 0 title \"CO2\" w lp ls 1 axes x1y2, ')
        
        plot.write('\"<awk \'$15 == ' + sensorn + '\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relay_name[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" u 1:8 index 0 title \"' + relay_name[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" u 1:9 index 0 title \"' + relay_name[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" u 1:10 index 0 title \"' + relay_name[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" u 1:11 index 0 title \"' + relay_name[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" u 1:12 index 0 title \"' + relay_name[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" u 1:13 index 0 title \"' + relay_name[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" u 1:14 index 0 title \"' + relay_name[8] + '\" w impulses ls 11 axes x1y1\n')

    # Generate a graph of the past day and week periods for each HT sensor 
    if "htdayweek" in graph_out_file:
        plot.write('set origin 0.0,0.0\n')
        plot.write('set multiplot\n')
        # Top graph - day
        plot.write('set size 1.0,0.5\n')
        plot.write('set origin 0.0,0.5\n')
        plot.write('set title \"Hum/Temp Sensor ' + sensorn + ': ' + sensor_ht_name[int(float(sensorn))] + '\\n\\nPast Day: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot \"<awk \'$10 == ' + sensorn + '\' ' + sensor_ht_log_generate + sensor_head + '" using 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, ')
        plot.write('\"\" using 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, ')
        plot.write('\"<awk \'$15 == ' + sensorn + '\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relay_name[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" using 1:8 index 0 title \"' + relay_name[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"' + relay_name[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" using 1:10 index 0 title \"' + relay_name[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" using 1:11 index 0 title \"' + relay_name[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" using 1:12 index 0 title \"' + relay_name[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" using 1:13 index 0 title \"' + relay_name[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" using 1:14 index 0 title \"' + relay_name[8] + '\" w impulses ls 11 axes x1y1\n')
        # Bottom graph - week
        d = 7
        time_ago = '1 Week'
        date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
        date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y/%m/%d %H:%M:%S") 
        plot.write('set size 1.0,0.5\n')
        plot.write('set origin 0.0,0.0\n')
        plot.write('set title \"Past Week: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('set format x \"%a\\n%m/%d\"\n')
        plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
        plot.write('plot \"<awk \'$10 == ' + sensorn + '\' ' + sensor_ht_log_generate + sensor_head + '" using 1:7 index 0 notitle w lp ls 1 axes x1y2, ')
        plot.write('\"\" using 1:8 index 0 notitle w lp ls 2 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 notitle w lp ls 3 axes x1y2\n')
        plot.write('unset multiplot\n')
        
    # Generate a graph of the past day and week periods for each CO2 sensor 
    if "co2dayweek" in graph_out_file:
        plot.write('set origin 0.0,0.0\n')
        plot.write('set multiplot\n')
        # Top graph - day
        plot.write('set size 1.0,0.5\n')
        plot.write('set origin 0.0,0.5\n')
        plot.write('set title \"CO2 Sensor ' + sensorn + ': ' + sensor_co2_name[int(float(sensorn))] + '\\n\\nPast Day: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot \"<awk \'$8 == ' + sensorn + '\' ' + sensor_co2_log_generate + sensor_head + '" using 1:7 index 0 title \"CO2\" w lp ls 1 axes x1y2, ')
        plot.write('\"<awk \'$15 == ' + sensorn + '\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relay_name[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" using 1:8 index 0 title \"' + relay_name[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"' + relay_name[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" using 1:10 index 0 title \"' + relay_name[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" using 1:11 index 0 title \"' + relay_name[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" using 1:12 index 0 title \"' + relay_name[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" using 1:13 index 0 title \"' + relay_name[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" using 1:14 index 0 title \"' + relay_name[8] + '\" w impulses ls 11 axes x1y1\n')
        # Bottom graph - week
        d = 7
        time_ago = '1 Week'
        date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
        date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y/%m/%d %H:%M:%S") 
        plot.write('set size 1.0,0.5\n')
        plot.write('set origin 0.0,0.0\n')
        plot.write('set title \"Past Week: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('set format x \"%a\\n%m/%d\"\n')
        plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
        plot.write('plot \"<awk \'$8 == ' + sensorn + '\' ' + sensor_co2_log_generate + sensor_head + '" using 1:7 index 0 notitle w lp ls 1 axes x1y2\n')
        plot.write('unset multiplot\n')

    if "legend-small" in graph_out_file:
        plot.write('unset border\n')
        plot.write('unset tics\n')
        plot.write('unset grid\n')
        plot.write('set yrange [0:400]\n')
        plot.write('set key center center box\n')
        plot.write('plot sqrt(-1) title \"Temperature\" w lp ls 1,')
        plot.write('sqrt(-1) title \"Rel. Humidity\" w lp ls 2,')
        plot.write('sqrt(-1) title \"Dew Point\" w lp ls 3,')
        plot.write('sqrt(-1) title \"' + relay_name[1] + '\" w impulses ls 4, ')
        plot.write('sqrt(-1) title \"' + relay_name[2] + '\" w impulses ls 5, ')
        plot.write('sqrt(-1) title \"' + relay_name[3] + '\" w impulses ls 6, ')
        plot.write('sqrt(-1) title \"' + relay_name[4] + '\" w impulses ls 7, ')
        plot.write('sqrt(-1) title \"' + relay_name[5] + '\" w impulses ls 8, ')
        plot.write('sqrt(-1) title \"' + relay_name[6] + '\" w impulses ls 9, ')
        plot.write('sqrt(-1) title \"' + relay_name[7] + '\" w impulses ls 10, ')
        plot.write('sqrt(-1) title \"' + relay_name[8] + '\" w impulses ls 11\n')
        
    if "legend-full" in graph_out_file:
        plot.write('set xlabel \"Date and Time\"\n')
        plot.write('set ylabel \"# Seconds Relays On and % Humidity\"\n')
        plot.write('set y2label \"Temperature and Dew Point\"\n')
        plot.write('set border 3 back ls 11\n')
        plot.write('set tics nomirror\n')
        plot.write('set key outside\n')
        plot.write('plot \"<awk \'$10 == 1\' ' + sensor_ht_log_generate + sensor_head + '" using 1:7 index 0 title \"Temperature\" w lp ls 1 axes x1y2, ')
        plot.write('\"\" using 1:8 index 0 title \"Rel. Humidity\" w lp ls 2 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"Dew Point\" w lp ls 3 axes x1y2, ')
        plot.write('\"<awk \'$15 == 1\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relay_name[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" using 1:8 index 0 title \"' + relay_name[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"' + relay_name[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" using 1:10 index 0 title \"' + relay_name[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" using 1:11 index 0 title \"' + relay_name[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" using 1:12 index 0 title \"' + relay_name[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" using 1:13 index 0 title \"' + relay_name[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" using 1:14 index 0 title \"' + relay_name[8] + '\" w impulses ls 11 axes x1y1\n')
    plot.close()

    # Generate graph with gnuplot with the above generated command sequence
    if logging.getLogger().isEnabledFor(logging.DEBUG) is False:
        subprocess.call(['gnuplot', gnuplot_graph])
        os.remove(gnuplot_graph)
        os.remove(sensor_ht_log_generate)
        os.remove(sensor_co2_log_generate)
        os.remove(relay_log_generate)
    else:
        gnuplot_log = "%s/plot-%s-%s.log" % (log_path, graph_out_file, sensorn)
        with open(gnuplot_log, 'ab') as errfile:
            subprocess.call(['gnuplot', gnuplot_graph], stderr=errfile)


#################################################
#        Configuration File Read/Write          #
#################################################

# Read variables from the configuration file
def read_sql():
    global sensor_ht_name
    global sensor_ht_device
    global sensor_ht_pin
    global sensor_ht_period
    global sensor_ht_log
    global sensor_ht_graph
    
    global sensor_co2_name
    global sensor_co2_device
    global sensor_co2_pin
    global sensor_co2_period
    global sensor_co2_log
    global sensor_co2_graph
    
    global pid_co2_period
    global pid_co2_relay
    global pid_co2_set
    global pid_co2_or
    global pid_co2_p
    global pid_co2_i
    global pid_co2_d
    
    global relay_name
    global relay_pin
    global relay_trigger
    
    global pid_hum_relay
    global pid_hum_set
    global pid_hum_or
    global pid_hum_p
    global pid_hum_i
    global pid_hum_d
    
    global pid_temp_relay
    global pid_temp_set
    global pid_temp_or
    global pid_temp_p
    global pid_temp_i
    global pid_temp_d
    
    global factorHumSeconds
    global factorTempSeconds
    global camera_light
    global relay_num
    global sensor_ht_num
    global sensor_co2_num
    global timer_num
    global timer_name
    global timer_relay
    global timer_state
    global timer_duration_on
    global timer_duration_off
    global smtp_host
    global smtp_ssl
    global smtp_port
    global smtp_user
    global smtp_pass
    global smtp_email_from
    global smtp_email_to

    verbose = 0
    # Check if all required tables exist in the SQL database
    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    tables = ['Relays', 'HTSensor', 'CO2Sensor', 'Timers', 'Numbers', 'SMTP']
    missing = []
    for i in range(0, len(tables)):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s'" % tables[i]
        cur.execute(query)
        if cur.fetchone() == None: missing.append(tables[i])
    if missing != []:
        print "Missing required table(s):",
        for i in range(0, len(missing)):
            if len(missing) == 1:
                print "%s" % missing[i]
            elif len(missing) != 1 and i != len(missing)-1:
                print "%s," % missing[i],
            else:
                print "%s" % missing[i]
        print "Reinitialize database to correct."
        return 0
  
    # Begin setting global variables from SQL database values
    cur.execute('SELECT Id, Name, Pin, Trigger FROM Relays')
    if verbose:
            print "Table: Relays"
    for row in cur :
        if verbose:
            print "%s %s %s %s" % (row[0], row[1], row[2], row[3])
        relay_name[row[0]] = row[1]
        relay_pin[row[0]] = row[2]
        relay_trigger[row[0]] = row[3]

    cur.execute('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_P, Hum_I, Hum_D FROM HTSensor')
    if verbose:
            print "Table: HTSensor"
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s%s " % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18])
        sensor_ht_name[row[0]] = row[1]
        sensor_ht_pin[row[0]] = row[2]
        sensor_ht_device[row[0]] = row[3]
        sensor_ht_period[row[0]] = row[4]
        sensor_ht_log[row[0]] = row[5]
        sensor_ht_graph[row[0]] = row[6]
        pid_temp_relay[row[0]] = row[7]
        pid_temp_or[row[0]] = row[8]
        pid_temp_set[row[0]] = row[9]
        pid_temp_p[row[0]] = row[10]
        pid_temp_i[row[0]] = row[11]
        pid_temp_d[row[0]] = row[12]
        pid_hum_relay[row[0]] = row[13]
        pid_hum_or[row[0]] = row[14]
        pid_hum_set[row[0]] = row[15]
        pid_hum_p[row[0]] = row[16]
        pid_hum_i[row[0]] = row[17]
        pid_hum_d[row[0]] = row[18]
    
    cur.execute('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay, CO2_OR, CO2_Set, CO2_P, CO2_I, CO2_D FROM CO2Sensor ')
    if verbose:
            print "Table: CO2Sensor "
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s %s %s %s %s %s %s %s" % (
                row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                row[7], row[8], row[9], row[10], row[11], row[12])
        sensor_co2_name[row[0]] = row[1]
        sensor_co2_pin[row[0]] = row[2]
        sensor_co2_device[row[0]] = row[3]
        sensor_co2_period[row[0]] = row[4]
        sensor_co2_log[row[0]] = row[5]
        sensor_co2_graph[row[0]] = row[6]
        pid_co2_relay[row[0]] = row[7]
        pid_co2_or[row[0]] = row[8]
        pid_co2_set[row[0]] = row[9]
        pid_co2_p[row[0]] = row[10]
        pid_co2_i[row[0]] = row[11]
        pid_co2_d[row[0]] = row[12]
    
    cur.execute('SELECT Id, Name, Relay, State, DurationOn, DurationOff FROM Timers ')
    if verbose:
            print "Table: Timers "
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s" % (
                row[0], row[1], row[2], row[3], row[4], row[5])
        timer_name[row[0]] = row[1]
        timer_relay[row[0]] = row[2]
        timer_state[row[0]] = row[3]
        timer_duration_on[row[0]] = row[4]
        timer_duration_off[row[0]] = row[5]
        
    cur.execute('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers ')
    if verbose:
            print "Table: Numbers "
    for row in cur :
        if verbose:
            print "%s %s %s %s" % (
                row[0], row[1], row[2], row[3])
        relay_num = row[0]
        sensor_ht_num = row[1]
        sensor_co2_num = row[2]
        timer_num = row[3]
        
    cur.execute('SELECT Host, SSL, Port, User, Pass, Email_From, Email_To FROM SMTP ')
    if verbose:
            print "Table: SMTP "
    for row in cur :
        if verbose:
            print "%s %s %s %s %s %s %s" % (
                row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        smtp_host = row[0]
        smtp_ssl = row[1]
        smtp_port = row[2]
        smtp_user = row[3]
        smtp_pass = row[4]
        smtp_email_from = row[5]
        smtp_email_to = row[6]

    cur.close()

# Write variables to configuration file
def write_sql():
    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(sql_lock_path)
    
    while not lock.i_am_locking():
        try:
            logging.debug("[Write SQL] Waiting, Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write SQL] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()
           
    logging.debug("[Write SQL] Gained lock: %s", lock.path)
    logging.debug("[Write SQL] Writing SQL Database %s", sql_database)

    conn = sqlite3.connect(sql_database)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS Relays ')
    cur.execute('DROP TABLE IF EXISTS HTSensor ')
    cur.execute('DROP TABLE IF EXISTS CO2Sensor ')
    cur.execute('DROP TABLE IF EXISTS Timers ')
    cur.execute('DROP TABLE IF EXISTS Numbers ')
    cur.execute('DROP TABLE IF EXISTS SMTP ')
    cur.execute("CREATE TABLE Relays (Id INT, Name TEXT, Pin INT, Trigger INT)")
    cur.execute("CREATE TABLE HTSensor (Id INT, Name TEXT, Pin INT, Device TEXT, Period INT, Activated INT, Graph INT, Temp_Relay INT, Temp_OR INT, Temp_Set REAL, Temp_P REAL, Temp_I REAL, Temp_D, Hum_Relay INT, Hum_OR INT, Hum_Set REAL, Hum_P REAL, Hum_I REAL, Hum_D REAL)")
    cur.execute("CREATE TABLE CO2Sensor (Id INT, Name TEXT, Pin INT, Device TEXT, Period INT, Activated INT, Graph INT, CO2_Relay INT, CO2_OR INT, CO2_Set INT, CO2_P REAL, CO2_I REAL, CO2_D REAL)")
    cur.execute("CREATE TABLE Timers (Id INT, Name TEXT, Relay INT, State INT, DurationOn INT, DurationOff INT)")
    cur.execute("CREATE TABLE Numbers (Relays INT, HTSensors INT, CO2Sensors INT, Timers INT)")
    cur.execute("CREATE TABLE SMTP (Host TEXT, SSL INT, Port INT, User TEXT, Pass TEXT, Email_From TEXT, Email_To TEXT)")
    for i in range(1, 9):
        query = "INSERT INTO Relays VALUES(%d, '%s', %s, %s)" % (i, relay_name[i], relay_pin[i], relay_trigger[i])
        cur.execute(query)
    for i in range(1, 5):
        query = "INSERT INTO HTSensor VALUES(%d, '%s', %s, '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % (i, sensor_ht_name[i], sensor_ht_pin[i], sensor_ht_device[i], sensor_ht_period[i], sensor_ht_log[i], sensor_ht_graph[i], pid_temp_relay[i], pid_temp_or[i], pid_temp_set[i], pid_temp_p[i], pid_temp_i[i], pid_temp_d[i], pid_hum_relay[i], pid_hum_or[i], pid_hum_set[i], pid_hum_p[i], pid_hum_i[i], pid_hum_d[i])
        cur.execute(query)
    for i in range(1, 5):
        query = "INSERT INTO CO2Sensor VALUES(%d, '%s', %s, '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s)" % (i, sensor_co2_name[i], sensor_co2_pin[i], sensor_co2_device[i], sensor_co2_period[i], sensor_co2_log[i], sensor_co2_graph[i], pid_co2_relay[i], pid_co2_or[i], pid_co2_set[i], pid_co2_p[i], pid_co2_i[i], pid_co2_d[i])
        cur.execute(query)
    for i in range(1, 9):
        query = "INSERT INTO Timers VALUES(%d, '%s', %s, %s, %s, %s)" % (i, timer_name[i], timer_state[i], timer_relay[i], timer_duration_on[i], timer_duration_off[i])
        cur.execute(query)
    query = "INSERT INTO Numbers VALUES(%s, %s, %s, %s)" % (relay_num, sensor_ht_num, sensor_co2_num, timer_num)
    cur.execute(query)
    query = "INSERT INTO SMTP VALUES('%s', %s, %s, '%s', '%s', '%s', '%s')" % (smtp_host, smtp_ssl, smtp_port, smtp_user, smtp_pass, smtp_email_from, smtp_email_to)
    cur.execute(query)
    conn.commit()
    cur.close()
    
    logging.debug("[Write SQL] Removing lock: %s", lock.path)
    lock.release()

# Check if a variable name in config_file matches a string
def modify_var(*names_and_values):
    namesOfVariables = [
    'relay_num',
    'sensor_ht_num',
    'sensor_co2_num',
    'timer_num',
    'smtp_host',
    'smtp_port',
    'smtp_user',
    'smtp_pass',
    'smtp_email_from',
    'smtp_email_to']
    
    for i in range(1, len(names_and_values), 2):
        for variable in namesOfVariables:
            if names_and_values[i] == variable:
                # Log variable name: previous value -> new value
                logging.info("[Change Variable] %s: %s -> %s", 
                    names_and_values[i], 
                    globals()[names_and_values[i]], 
                    names_and_values[i+1])
                globals()[names_and_values[i]] = names_and_values[i+1]   
    write_sql()
    read_sql()


#################################################
#               GPIO Manipulation               #
#################################################
    
# Initialize GPIO
def gpio_initialize():
    logging.info("[GPIO Initialize] Set GPIO mode to BCM numbering, all as output")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Initialize
    for i in range(1, 9):
        GPIO.setup(relay_pin[i], GPIO.OUT)
    
    Relays_Off()

# Change GPIO (Select) to a specific state (State)
def gpio_change(relay, State):
    logging.debug("[GPIO Write] Setting relay %s (%s) to %s (was %s)", 
        relay, relay_name[relay], 
        State, GPIO.input(relay_pin[relay]))
    GPIO.output(relay_pin[relay], State)

# Turn Relays Off
def Relays_Off():
    for i in range(1, 9):
        if relay_trigger[i] == 0: GPIO.output(relay_pin[i], 1)
        else: GPIO.output(relay_pin[i], 0)

# Read states (HIGH/LOW) of GPIO pins
def gpio_read():
    for x in range(1, 9):
        if GPIO.input(relay_pin[x]): logging.info("[GPIO Read] Relay %s: OFF", x)
        else: logging.info("[GPIO Read] Relay %s: ON", x)

# Turn relay on or off (accounts for trigger)
def relay_onoff(relay, state):
    if (relay_trigger[relay] == 1 and state == 1):
        gpio_change(relay, 1)
    elif (relay_trigger[relay] == 1 and state == 0):
        gpio_change(relay, 0)
    elif (relay_trigger[relay] == 0 and state == 1):
        gpio_change(relay, 0)
    elif (relay_trigger[relay] == 0 and state == 0):
        gpio_change(relay, 1)

# Set relay on for a specific duration
def relay_on_duration(relay, seconds, sensor):
    if (relay_trigger[relay] == 0 and GPIO.input(relay_pin[relay]) == 0) or (
            relay_trigger[relay] == 1 and GPIO.input(relay_pin[relay]) == 1):
        logging.warning("[Relay Duration] Relay %s (%s) is already On. Turning off in %s seconds.", 
            relay, relay_name[relay], seconds)
    else:
        logging.debug("[Relay Duration] Relay %s (%s) ON for %s seconds", 
            relay, relay_name[relay], round(seconds, 1))
   
    GPIO.output(relay_pin[relay], relay_trigger[relay]) # Turn relay on    
    timer_on = int(time.time()) + seconds
    write_relay_log(relay, seconds, sensor)
    
    while (client_que != 'TerminateServer' and timer_on > int(time.time())):
        time.sleep(0.1)
        
    # Turn relay off
    if relay_trigger[relay] == 0: GPIO.output(relay_pin[relay], 1)
    else: GPIO.output(relay_pin[relay], 0)
    
    logging.debug("[Relay Duration] Relay %s (%s) Off (was On for %s sec)", 
        relay, relay_name[relay], round(seconds, 1))
    return 1

#################################################
#                 Email Notify                  #
#################################################

# Email if temperature or sensor_ht_read_hum is outside of critical range (Not yet implemented)
def email(message):
    if (smtp_ssl):
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        server.ehlo()
    else:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()

    server.ehlo
    server.login(smtp_user, smtp_pass)

    # Body of email
    # message = "Critical warning!"
    
    msg = MIMEText(message)
    msg['Subject'] = "Critical warning!"
    msg['From'] = "Raspberry Pi"
    msg['To'] = smtp_email_from
    server.sendmail(smtp_email_from, smtp_email_to, msg.as_string())
    server.quit()


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

# Timestamp format used in sensor and relay logs
def timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')


#################################################
#                 Main Program                  #
#################################################

if not os.geteuid() == 0:
    print "Script must be run as root"
    usage()
    sys.exit(0)

if not os.path.exists(lock_directory):
    os.makedirs(lock_directory)

runlock = LockFile(daemon_lock_path)

while not runlock.i_am_locking():
    try:
        runlock.acquire(timeout=1)
    except:
        print "Error: Lock file present: %s" % runlock.path
        sys.exit(0)

read_sql()
gpio_initialize()
menu()
runlock.release()