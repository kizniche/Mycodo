#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo.py - Read sensors, write log, read configuration file, write
#              configuration file, and modulate relays to regulate temperature
#              and humidity.
#
#  Kyle Gabriel (2012 - 2015)
#
# Start with:
# sudo stdbuf -oL python ./mycodo.py -d | tee /var/log/some.log
# sudo stdbuf -oL python ./mycodo.py -d >> /var/log/some.log 2>&1 &
#

#### Configure Install Directory ####
install_directory = "/var/www/mycodo"
#### Configure Install Directory ####

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
import smtplib
import subprocess
import sys
import threading
import time
from array import *
from email.mime.text import MIMEText
from lockfile import LockFile
from rpyc.utils.server import ThreadedServer

config_file = "%s/config/mycodo.cfg" % install_directory
daemon_log_file_tmp = "%s/log/daemon-tmp.log" % install_directory
daemon_log_file = "%s/log/daemon.log" % install_directory
sensor_log_file_tmp = "%s/log/sensor-tmp.log" % install_directory
sensor_log_file = "%s/log/sensor.log" % install_directory
relay_log_file_tmp = "%s/log/relay-tmp.log" % install_directory
relay_log_file = "%s/log/relay.log" % install_directory
relay_script = "%s/cgi-bin/relay.sh" % install_directory

logging.basicConfig(
    filename = daemon_log_file_tmp,
    level = logging.INFO,
    format = '%(asctime)s [%(levelname)s] %(message)s')

lock_directory = "/var/lock/mycodo"
config_lock_path = "%s/config" % lock_directory
daemon_lock_path = "%s/daemon" % lock_directory
sensor_lock_path = "%s/sensor" % lock_directory
relay_lock_path = "%s/relay" % lock_directory

# GPIO pins (BCM numbering) and name of devices attached to relay
numRelays = None
relayPin = [0] * 9
relayName = [0] * 9
relayTrigger = [0] * 9

#PID
relayTemp =None
relayHum = None
setTemp = None
setHum = None
Hum_P = None
Hum_I = None
Hum_D = None
Temp_P = None
Temp_I = None
Temp_D = None
factorHumSeconds = None
factorTempSeconds = None

# Control States
TempOR = None
HumOR = None

# Timers
DHTSeconds = None
numTimers = None
timerRelay = [0] * 9
timerState = [0] * 9
timerDurationOn = [0] * 9
timerDurationOff = [0] * 9
timerChange = 0

# SMTP notify
smtp_host = None
smtp_ssl = None
smtp_port = None
smtp_user = None
smtp_pass = None
email_from = None
email_to = None

# Sensors
numSensors = None
DHTSensor = None
DHTPin = None

# Sensor data
chktemp = None
tempc = None
humidity = None
dewpointc = None
heatindexc =  None

# Miscellaneous
cameraLight = None
server = None
variableName = None
variableValue = None
ClientQue = '0'
Terminate = False
TAlive = 1
HAlive = 1
Temp_PID_Down = 0
Temp_PID_Up = 0
Hum_PID_Down = 0
Hum_PID_Up = 0

# Threaded server that receives commands from mycodo-client.py
class ComServer(rpyc.Service):
    def exposed_Modify_Variables(self, *variable_list):
        logging.info("[Client command] Request to change variables")
        modify_var(*variable_list)
        return 1
    def exposed_Terminate(self, remoteCommand):
        global ClientQue
        global Terminate
        Terminate = True
        ClientQue = 'TerminateServer'
        logging.info("[Client command] Terminate threads and shut down")
        return 1
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
                args = (int(relay), int(state),))
            rod.start()
        return 1
    def exposed_ChangeTimer(self, timernumber, timerstate, timerrelay,
            timerdurationon, timerdurationoff):
        global ClientQue
        global timerRelay
        global timerState
        global timerDurationOn
        global timerDurationOff
        global timerChange
        timerRelay[timernumber] = timerrelay
        timerState[timernumber] = timerstate
        timerDurationOn[timernumber] = timerdurationon
        timerDurationOff[timernumber] = timerdurationoff
        timerChange = timernumber
        logging.info("[Client command] Change Timer: %s, State: %s, Relay: %s, On: %s, Off %s",
            timernumber, timerstate, timerrelay,
            timerdurationon, timerdurationoff)
        write_config()
        ClientQue = 'TimerChange'
        return 1
    def exposed_ChangeRelayNames(self, relayname1, relayname2, relayname3,
            relayname4, relayname5, relayname6, relayname7, relayname8):
        global relayName
        relayName[1] = relayname1
        relayName[2] = relayname2
        relayName[3] = relayname3
        relayName[4] = relayname4
        relayName[5] = relayname5
        relayName[6] = relayname6
        relayName[7] = relayname7
        relayName[8] = relayname8
        logging.info("[Client command] Change Relay Names: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            relayName[1], relayName[2], relayName[3], relayName[4],
            relayName[5], relayName[6], relayName[7], relayName[8])
        write_config()
        return 1
    def exposed_ChangeRelayPins(self, relaypin1, relaypin2, relaypin3,
            relaypin4, relaypin5, relaypin6, relaypin7, relaypin8):
        global relayPin
        relayPin[1] = relaypin1
        relayPin[2] = relaypin2
        relayPin[3] = relaypin3
        relayPin[4] = relaypin4
        relayPin[5] = relaypin5
        relayPin[6] = relaypin6
        relayPin[7] = relaypin7
        relayPin[8] = relaypin8
        logging.info("[Client command] Change Relay Pins: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            relayPin[1], relayPin[2], relayPin[3], relayPin[4],
            relayPin[5], relayPin[6], relayPin[7], relayPin[8])
        write_config()
        return 1
    def exposed_ChangeRelayTriggers(self, relaytrigger1, relaytrigger2, relaytrigger3,
            relaytrigger4, relaytrigger5, relaytrigger6, relaytrigger7, relaytrigger8):
        global relayTrigger
        relayTrigger[1] = relaytrigger1
        relayTrigger[2] = relaytrigger2
        relayTrigger[3] = relaytrigger3
        relayTrigger[4] = relaytrigger4
        relayTrigger[5] = relaytrigger5
        relayTrigger[6] = relaytrigger6
        relayTrigger[7] = relaytrigger7
        relayTrigger[8] = relaytrigger8
        logging.info("[Client command] Change Relay Triggers: 1: %s, 2: %s, 3: %s, 4: %s, 5: %s, 6: %s, 7: %s, 8: %s",
            relayTrigger[1], relayTrigger[2], relayTrigger[3], relayTrigger[4],
            relayTrigger[5], relayTrigger[6], relayTrigger[7], relayTrigger[8])
        write_config()
        return 1
    def exposed_WriteSensorLog(self):
        global ClientQue
        ClientQue = 'write_sensor_log'
        logging.info("[Client command] Read sensors and append log")
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

# PID controller for humidity
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

# Displays the program usage
def usage():
    print "mycodo.py: Reads sensors, writes logs, and operates relays to" \
        " maintain set environmental conditions.\n"
    print "Usage:  mycodo.py [OPTION]...\n"
    print "Options:"
    print "    -d, --daemon [v/s] [w/i/d]"
    print "           Start program as daemon that monitors conditions and modulates relays"
    print "           ""v"" enables log output to the console, ""s"" silences"
    print "           Log leve: ""w"": >= warnings, ""i"": >= info, ""d"": >= debug"
    print "    -h, --help"
    print "           Display this help and exit"
    print "    -p, --pin"
    print "           Display status of the GPIO pins (HIGH or LOW)"
    print "    -r, --relay [Relay Number] [0/1/X]"
    print "           Change the state of a relay"
    print "           0=OFF, 1=ON, or X number of seconds On"
    print "    -s,  --sensor"
    print "           Read and display sensor data"
    print "    -w, --write=FILE"
    print "           Write sensor data to log file\n"
    print "Examples: mycodo.py -w /var/www/mycodo/log/sensor.log"
    print "          mycodo.py -d s"
    print "          mycodo.py --read"
    print "          mycodo.py -c 4 OFF\n"

# Checks user options and arguments for validity
def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'r:dhpstw',
            ["relay=", "daemon", "help", "pin",
            "sensor", "write="])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-d", "--daemon"):
            if (sys.argv[2] == 'v'): a = 'verbose'
            else: a = 'silent'
            if (sys.argv[3] == 'w'): b = 'warning'
            elif (sys.argv[3] == 'i'): b = 'info'
            else: b = 'debug'
            daemon(a, b)
            sys.exit(0)
        elif opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-p", "--pin"):
            read_config(0)
            gpio_read()
            sys.exit(0)
        elif opt in ("-r", "--relay"):
            if not represents_int(sys.argv[2]) or \
                    int(float(sys.argv[2])) > 8 or \
                    int(float(sys.argv[2])) < 1:
                print "Error: --relay only accepts integers 1 though 8"
                sys.exit(1)
            else:
                global relaySelect
                relaySelect = int(float(sys.argv[2]))
            if represents_int(sys.argv[3]) and int(float(sys.argv[3])):
                read_config(0)
                if sys.argv[3] == 1:
                    print "%s [GPIO Write] Relay %s ON" % (
                        timestamp(), relaySelect)
                    if (relayTrigger[int(float(sys.argv[2]))] == 1): gpio_change(relaySelect, 1)
                    else: gpio_change(relaySelect, 0)
                    gpio_read()
                    sys.exit(0)
                elif sys.argv[3] == 0:
                    print "%s [GPIO Write] Relay %s OFF" % (
                        timestamp(), relaySelect)
                    if (relayTrigger[int(float(sys.argv[2]))] == 1): gpio_change(relaySelect, 0)
                    else: gpio_change(relaySelect, 1)
                    gpio_read()
                    sys.exit(0)
                elif int(float(sys.argv[3])) > 1:
                    print "%s [GPIO Write] Relay %s ON for %s seconds" % (
                        timestamp(), int(float(arg)))
                    relay_on_duration(int(float(sys.argv[2])), int(float(sys.argv[3])))
                    sys.exit(0)
                else:
                    print "--state only accepts ON, OFF, integers > 1"
                    usage()
                    sys.exit(1)
        elif opt in ("-s", "--sensor"):
            read_sensors(0)
            sys.exit(0)
        elif opt in ("-w", "--write"):
            global sensor_log_file_tmp
            if arg == '':
                print "[Write Log] No file specified, using default: %s" % (
                    sensor_log_file_tmp)
            else:
                sensor_log_file_tmp = arg
            read_sensors(0)
            write_sensor_log()
            sys.exit(0)
        else:
            assert False, "Fail"

# Main loop that reads sensors, modifies relays based on sensor values, writes
# sensor/relay logs, and receives/executes commands from mycodo-client.py
def daemon(output, log):
    global change_sensor_log
    global Temp_PID_Down
    global Temp_PID_Up
    global Hum_PID_Down
    global Hum_PID_Up
    global server
    global HAlive
    global TAlive
    global ClientQue
    timer_time = [0] * 9
    
    if (log == 'warning'):
        logging.getLogger().setLevel(logging.WARNING)
    elif (log == 'info'):
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.DEBUG)

    if (output == 'verbose'):
        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.debug)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)
    
    logging.info("[Daemon] Daemon Started")
    logging.info("[Daemon} Communication server thread starting")
    ct = ComThread()
    ct.daemon = True
    ct.start()
    time.sleep(1)
    
    logging.info("[Daemon] Reading configuration file and initializing variables")
    read_config(1)
    
    if DHTSensor != 'Other':
        read_sensors(0)
    
    timerLogBackup = int(time.time()) + 21600 # 21600 seconds = 6 hours
    timerSensorLog = int(time.time()) + DHTSeconds
    for i in range(1, 9):
        timer_time[i] = int(time.time())
   
    tm = threading.Thread(target = temperature_monitor)   
    tm.daemon = True
    tm.start()
    
    hm = threading.Thread(target = humidity_monitor)
    hm.daemon = True
    hm.start()

    while True: # Main loop of the daemon
        if ClientQue != '0': # Run remote commands issued by mycodo-client.py
            if ClientQue == 'write_sensor_log':
                logging.debug("[Client command] Write Sensor Log")
                read_sensors(0)
                write_sensor_log()
                change_sensor_log = 0
            elif ClientQue == 'TerminateServer':
                logging.info("[Daemon] Backing up logs")
                Concatenate_Logs()
                TAlive = 0
                while TAlive != 2:
                    time.sleep(0.1)
                HAlive = 0
                while HAlive != 2:
                    time.sleep(0.1)
                server.close()
                logging.info("[Daemon] Exiting Python")
                sys.exit(0)
            elif ClientQue == 'TimerChange':
                timer_time[timerChange] = 0
                if (timerState[timerChange] == 0 and timerRelay[timerChange] != 0):
                    relay_onoff(timerRelay[timerChange], 0)
                    
            ClientQue = '0'

        if Temp_PID_Down == 1:
            if tm.isAlive():
                logging.info("[Daemon] Shutting Down Temperature PID thread")
                TAlive = 0
                while TAlive != 2:
                    time.sleep(0.1)
                if (relayTrigger[int(relayTemp)] == 0): gpio_change(int(relayTemp), 1)
                else: gpio_change(int(relayTemp), 0)
                TAlive = 1
            Temp_PID_Down = 0
        if Temp_PID_Up == 1:
            logging.info("[Daemon] Starting Temperature PID thread")
            tm = threading.Thread(target = temperature_monitor)  
            tm.daemon = True
            tm.start()
            Temp_PID_Up = 0
            
        if Hum_PID_Down:
            if hm.isAlive():
                logging.info("[Daemon] Shutting Down Humidity PID thread")
                HAlive = 0
                while HAlive != 2:
                    time.sleep(0.1)
                if (relayTrigger[int(relayHum)] == 0): gpio_change(int(relayHum), 1)
                else: gpio_change(int(relayHum), 1)
                HAlive = 1
            Hum_PID_Down = 0
        if Hum_PID_Up == 1:
            logging.info("[Daemon] Starting Temperature PID thread")
            hm = threading.Thread(target = humidity_monitor)
            hm.daemon = True
            hm.start()
            Hum_PID_Up = 0
        
        # Write sensor log
        if int(time.time()) > timerSensorLog and DHTSensor != 'Other':
            logging.debug("[Timer Expiration] Run every %s seconds: Write sensor log", DHTSeconds)
            read_sensors(0)
            write_sensor_log()
            timerSensorLog = int(time.time()) + DHTSeconds
        
        # Concatenate local log with tempfs log every 6 hours
        if int(time.time()) > timerLogBackup:
            Concatenate_Logs()
            timerLogBackup = int(time.time()) + 21600
        
        # Handle timers
        for i in range(1, 9):
            if int(time.time()) > timer_time[i]:
                if timerState[i] == 1:
                    logging.debug("[Timer Expiration] Timer %s: Turn Relay %s on for %s seconds, off %s seconds.", i, timerRelay[i], timerDurationOn[i], timerDurationOff[i])
                    rod = threading.Thread(target = relay_on_duration, 
                        args = (timerRelay[i], timerDurationOn[i],))
                    rod.start()
                    timer_time[i] = int(time.time()) + timerDurationOn[i] + timerDurationOff[i]
                

        time.sleep(0.1)

# Temperature modulation by PID control
def temperature_monitor():
    global TAlive
    timerTemp = 0
    PIDTemp = 0
    logging.info("[PID Temperature] Starting Thread")
    if (tempc < setTemp):
        if (relayTrigger[int(relayTemp)] == 0): gpio_change(int(relayTemp), 1)
        else: gpio_change(int(relayTemp), 0)
    p_temp = Temperature_PID(Temp_P, Temp_I, Temp_D)
    p_temp.setPoint(setTemp)
    
    while (TAlive):
        if TempOR == 0 and Temp_PID_Down == 0:
            if int(time.time()) > timerTemp:
                logging.debug("[PID Temperature] Reading temperature...")
                read_sensors(1)
                PIDTemp = p_temp.update(float(tempc))
                if (tempc < setTemp):
                    logging.debug("[PID Temperature] Temperature (%.1f°C) < (%.1f°C) setTemp", tempc, float(setTemp))
                    logging.debug("[PID Temperature] PID = %.1f (seconds)", PIDTemp)
                    if (PIDTemp > 0 and tempc < setTemp):
                        rod = threading.Thread(target = relay_on_duration, 
                            args = (relayTemp, PIDTemp,))
                        rod.start()
                    timerTemp = int(time.time()) + int(PIDTemp) + int(factorTempSeconds)
                else:
                    logging.debug("[PID Temperature] Temperature (%.1f°C) >= (%.1f°C) setTemp, waiting 60 seconds", tempc, setTemp)
                    logging.debug("[PID Temperature] PID = %.1f (seconds)", PIDTemp)
                    timerTemp = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID Temperature] Shutting Down Thread")
    TAlive = 2

# Humidity modulation by PID control
def humidity_monitor():
    global HAlive
    timerHum = 0
    PIDHum = 0

    logging.info("[PID Humidity] Starting Thread")
    if (humidity > setHum):
        if (relayTrigger[int(relayHum)] == 0): gpio_change(int(relayHum), 1)
        else: gpio_change(int(relayHum), 1)
    p_hum = Humidity_PID(Hum_P, Hum_I, Hum_D)
    p_hum.setPoint(setHum)

    while (HAlive):
        if HumOR == 0 and Hum_PID_Down == 0:
            if int(time.time()) > timerHum:
                logging.debug("[PID Humidity] Reading humidity...")
                read_sensors(1)
                PIDHum = p_hum.update(float(humidity))
                if (humidity < setHum):
                    logging.debug("[PID Humidity] Humidity (%.1f%%) < (%.1f%%) setHum", humidity, float(setHum))
                    logging.debug("[PID Humidity] PID = %.1f (seconds)", PIDHum)
                    if (PIDHum > 0 and humidity < setHum):
                        rod = threading.Thread(target = relay_on_duration,
                            args=(relayHum, PIDHum,))
                        rod.start()
                    timerHum = int(time.time()) + int(PIDHum) + int(factorHumSeconds)
                else:
                    logging.debug("[PID Humidity] Humidity (%.1f%%) >= (%.1f%%) setHum, waiting 60 seconds", humidity, setHum)
                    logging.debug("[PID Humidity] PID = %.1f (seconds)", PIDHum)
                    timerHum = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID Humidity] Shutting Down Thread")
    HAlive = 2

# Append sensor data to the log file
def write_sensor_log():
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)
    if not Terminate:
        lock = LockFile(sensor_lock_path)
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
            with open(sensor_log_file_tmp, "ab") as sensorlog:
                sensorlog.write('{0} {1:.1f} {2:.1f} {3:.1f}\n'.format(
                    datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                    tempc, humidity, dewpointc))
                logging.debug("[Write Sensor Log] Data appended to %s", sensor_log_file_tmp)
        except:
            logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_log_file_tmp)
        logging.debug("[Write Sensor Log] Removing lock: %s", lock.path)
        lock.release()

# Append the duration the relay has been on to the log file
def write_relay_log(relayNumber, relaySeconds):
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)
    if not Terminate:
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
                relaylog.write('{0} {1} {2} {3} {4} {5} {6} {7} {8}\n'.format(
                    datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                    relay[1], relay[2], relay[3], relay[4],
                    relay[5], relay[6], relay[7], relay[8]))
        except:
            logging.warning("[Write Relay Log] Unable to append data to %s", relay_log_file_tmp)
        logging.debug("[Write Relay Log] Removing lock: %s", lock.path)
        lock.release()

# Combines the logs on the SD card with the logs on the temporary file system
def Concatenate_Logs():
    logging.debug("[Timer Expiration] Run every 6 hours: Concatenate logs")
    if not filecmp.cmp(daemon_log_file_tmp, daemon_log_file):
        logging.debug("[Daemon Log] Concatenating daemon logs to %s", daemon_log_file)
        lock = LockFile(daemon_lock_path)
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
    if not filecmp.cmp(sensor_log_file_tmp, sensor_log_file):
        logging.debug("[Sensor Log] Concatenating sensor logs to %s", sensor_log_file)
        lock = LockFile(sensor_lock_path)
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
            with open(sensor_log_file, 'a') as fout:
                for line in fileinput.input(sensor_log_file_tmp):
                    fout.write(line)
            logging.debug("[Daemon Log] Appended data to %s", sensor_log_file)
        except:
            logging.warning("[Sensor Log] Unable to append data to %s", sensor_log_file)
        open(sensor_log_file_tmp, 'w').close()
        logging.debug("[Sensor Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.debug("[Sensor Log] Sensor logs the same, skipping.")
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

# Read the temperature and humidity from the DHT22 sensor
def read_sensors(silent):
    global tempc
    global humidity
    global dewpointc
    global heatindexc
    global chktemp
    chktemp = 1
    
    if (DHTSensor == 'DHT11'): sensor = Adafruit_DHT.DHT11
    elif (DHTSensor == 'DHT22'): sensor = Adafruit_DHT.DHT22
    elif (DHTSensor == 'AM2302'): sensor = Adafruit_DHT.AM2302
    else: sensor = 'Other'

    if not silent and not Terminate:
        logging.debug("[Read Sensors] Taking first Temperature/humidity reading")
    if not Terminate:
        humidity2, tempc2 = Adafruit_DHT.read_retry(sensor, DHTPin)
        if humidity2 == None or tempc2 == None:
            logging.warning("[Read Sensors] Could not read temperature/humidity!")
        if not silent and humidity2 != None and tempc2 != None:
            logging.debug("[Read Sensors] %.1f°C, %.1f%%", tempc2, humidity2)
    if not Terminate:
        time.sleep(2)
        if not silent: 
            logging.debug("[Read Sensors] Taking second Temperature/humidity reading")
    while chktemp and not Terminate and humidity2 != None and tempc2 != None:
        if not Terminate:
            humidity, tempc = Adafruit_DHT.read_retry(sensor, DHTPin)
        if humidity != 'None' or tempc != 'None':
            if not silent and not Terminate: 
                logging.debug("[Read Sensors] %.1f°C, %.1f%%", tempc, humidity)
                logging.debug("[Read Sensors] Differences: %.1f°C, %.1f%%", abs(tempc2-tempc), abs(humidity2-humidity))
            if abs(tempc2-tempc) > 1 or abs(humidity2-humidity) > 1 and not Terminate:
                tempc2 = tempc
                humidity2 = humidity
                chktemp = 1
                if not silent:
                    logging.debug("[Read Sensors] Successive readings > 1 difference: Rereading")
                time.sleep(2)
            elif not Terminate:
                chktemp = 0
                if not silent: 
                    logging.debug("[Read Sensors] Successive readings < 1 difference: keeping.")
                tempf = float(tempc)*9.0/5.0 + 32.0
                dewpointc = tempc - ((100-humidity) / 5)
                #dewpointf = dewpointc * 9 / 5 + 32
                #heatindexf =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
                #heatindexc = (heatindexf - 32) * (5 / 9)
                if not silent: 
                    logging.debug("[Read Sensors] Temp: %.1f°C, Hum: %.1f%%, DP: %.1f°C", tempc, humidity, dewpointc)
        else: logging.warning("[Read Sensors] Could not read temperature/humidity!")

# Read variables from the configuration file
def read_config(silent):
    global config_file
    global DHTSensor
    global DHTPin
    global DHTSeconds
    global relayName
    global relayPin
    global relayTrigger
    global relayTemp
    global relayHum
    global setTemp
    global setHum
    global TempOR
    global HumOR
    global Hum_P
    global Hum_I
    global Hum_D
    global Temp_P
    global Temp_I
    global Temp_D
    global factorHumSeconds
    global factorTempSeconds
    global cameraLight
    global numRelays
    global numSensors
    global numTimers
    global timerRelay
    global timerState
    global timerDurationOn
    global timerDurationOff
    global smtp_host
    global smtp_ssl
    global smtp_port
    global smtp_user
    global smtp_pass
    global email_from
    global email_to

    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    
    DHTSensor = config.get('Sensor', 'dhtsensor')
    DHTPin = config.getint('Sensor', 'dhtpin')
    DHTSeconds = config.getint('Sensor', 'dhtseconds')
    
    relayTemp = config.getint('PID', 'relaytemp')
    relayHum = config.getint('PID', 'relayhum')
    setTemp = config.getfloat('PID', 'settemp')
    setHum = config.getfloat('PID', 'sethum')
    TempOR = config.getint('PID', 'tempor')
    HumOR = config.getint('PID', 'humor')
    Hum_P = config.getfloat('PID', 'hum_p')
    Hum_I = config.getfloat('PID', 'hum_i')
    Hum_D = config.getfloat('PID', 'hum_d')
    Temp_P = config.getfloat('PID', 'temp_p')
    Temp_I = config.getfloat('PID', 'temp_i')
    Temp_D = config.getfloat('PID', 'temp_d')
    factorHumSeconds = config.getint('PID', 'factorhumseconds')
    factorTempSeconds = config.getint('PID', 'factortempseconds')
    
    smtp_host = config.get('Notification', 'smtp_host')
    smtp_port = config.get('Notification', 'smtp_port')
    smtp_user = config.get('Notification', 'smtp_user')
    smtp_pass = config.get('Notification', 'smtp_pass')
    email_from = config.get('Notification', 'email_from')
    email_to = config.get('Notification', 'email_to')
    
    numRelays = config.get('Misc', 'numrelays')
    numSensors = config.get('Misc', 'numsensors')
    numTimers = config.get('Misc', 'numtimers')
    cameraLight = config.getint('Misc', 'cameralight')

    relayName[1] = config.get('Relay1', 'relay1name')
    relayPin[1] = config.getint('Relay1', 'relay1pin')
    relayTrigger[1] = config.getint('Relay1', 'relay1trigger')
    
    relayName[2] = config.get('Relay2', 'relay2name')
    relayPin[2] = config.getint('Relay2', 'relay2pin')
    relayTrigger[2] = config.getint('Relay2', 'relay2trigger')
    
    relayName[3] = config.get('Relay3', 'relay3name')
    relayPin[3] = config.getint('Relay3', 'relay3pin')
    relayTrigger[3] = config.getint('Relay3', 'relay3trigger')
    
    relayName[4] = config.get('Relay4', 'relay4name')
    relayPin[4] = config.getint('Relay4', 'relay4pin')
    relayTrigger[4] = config.getint('Relay4', 'relay4trigger')
    
    relayName[5] = config.get('Relay5', 'relay5name')
    relayPin[5] = config.getint('Relay5', 'relay5pin')
    relayTrigger[5] = config.getint('Relay5', 'relay5trigger')
    
    relayName[6] = config.get('Relay6', 'relay6name')
    relayPin[6] = config.getint('Relay6', 'relay6pin')
    relayTrigger[6] = config.getint('Relay6', 'relay6trigger')
    
    relayName[7] = config.get('Relay7', 'relay7name')
    relayPin[7] = config.getint('Relay7', 'relay7pin')
    relayTrigger[7] = config.getint('Relay7', 'relay7trigger')
    
    relayName[8] = config.get('Relay8', 'relay8name')
    relayPin[8] = config.getint('Relay8', 'relay8pin')
    relayTrigger[8] = config.getint('Relay8', 'relay8trigger')
    
    timerState[1] = config.getint('Timer1', 'timer1state')
    timerRelay[1] = config.getint('Timer1', 'timer1relay')
    timerDurationOn[1] = config.getint('Timer1', 'timer1durationon')
    timerDurationOff[1] = config.getint('Timer1', 'timer1durationoff')
    
    timerState[2] = config.getint('Timer2', 'timer2state')
    timerRelay[2] = config.getint('Timer2', 'timer2relay')
    timerDurationOn[2] = config.getint('Timer2', 'timer2durationon')
    timerDurationOff[2] = config.getint('Timer2', 'timer2durationoff')
    
    timerState[3] = config.getint('Timer3', 'timer3state')
    timerRelay[3] = config.getint('Timer3', 'timer3relay')
    timerDurationOn[3] = config.getint('Timer3', 'timer3durationon')
    timerDurationOff[3] = config.getint('Timer3', 'timer3durationoff')
    
    timerState[4] = config.getint('Timer4', 'timer4state')
    timerRelay[4] = config.getint('Timer4', 'timer4relay')
    timerDurationOn[4] = config.getint('Timer4', 'timer4durationon')
    timerDurationOff[4] = config.getint('Timer4', 'timer4durationoff')
    
    timerState[5] = config.getint('Timer5', 'timer5state')
    timerRelay[5] = config.getint('Timer5', 'timer5relay')
    timerDurationOn[5] = config.getint('Timer5', 'timer5durationon')
    timerDurationOff[5] = config.getint('Timer5', 'timer5durationoff')
    
    timerState[6] = config.getint('Timer6', 'timer6state')
    timerRelay[6] = config.getint('Timer6', 'timer6relay')
    timerDurationOn[6] = config.getint('Timer6', 'timer6durationon')
    timerDurationOff[6] = config.getint('Timer6', 'timer6durationoff')
    
    timerState[7] = config.getint('Timer7', 'timer7state')
    timerRelay[7] = config.getint('Timer7', 'timer7relay')
    timerDurationOn[7] = config.getint('Timer7', 'timer7durationon')
    timerDurationOff[7] = config.getint('Timer7', 'timer7durationoff')
    
    timerState[8] = config.getint('Timer8', 'timer8state')
    timerRelay[8] = config.getint('Timer8', 'timer8relay')
    timerDurationOn[8] = config.getint('Timer8', 'timer8durationon')
    timerDurationOff[8] = config.getint('Timer8', 'timer8durationoff')

    if not silent:
        logging.debug("[Read Config] setTemp: %.1f°C, setHum: %.1f%%, TempOR: %s, HumOR: %s", setTemp, setHum, TempOR, HumOR)
        for x in range(1,9):
            logging.debug("[Read Config] RelayNum[Name][Pin]: %s[%s][%s]", x, relayName[x], relayPin[x])

# Write variables to configuration file
def write_config():
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(config_lock_path)
    while not lock.i_am_locking():
        try:
            logging.debug("[Write Config] Waiting, Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write Config] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()
    logging.debug("[Write Config] Gained lock: %s", lock.path)
    logging.debug("[Write Config] Writing config file %s", config_file)
    
    config.add_section('Sensor')
    config.set('Sensor', 'dhtsensor', DHTSensor)
    config.set('Sensor', 'dhtpin', DHTPin)
    config.set('Sensor', 'dhtseconds', DHTSeconds)
    
    config.add_section('PID')
    config.set('PID', 'relaytemp', relayTemp)
    config.set('PID', 'relayhum', relayHum)
    config.set('PID', 'tempor', TempOR)
    config.set('PID', 'humor', HumOR)
    config.set('PID', 'settemp', setTemp)
    config.set('PID', 'sethum', setHum)
    config.set('PID', 'hum_p', Hum_P)
    config.set('PID', 'hum_i', Hum_I)
    config.set('PID', 'hum_d', Hum_D)
    config.set('PID', 'temp_p', Temp_P)
    config.set('PID', 'temp_i', Temp_I)
    config.set('PID', 'temp_d', Temp_D)
    config.set('PID', 'factorhumseconds', factorHumSeconds)
    config.set('PID', 'factortempseconds', factorTempSeconds)
    
    config.add_section('Notification')
    config.set('Notification', 'smtp_host', smtp_host)
    config.set('Notification', 'smtp_port', smtp_port)
    config.set('Notification', 'smtp_user', smtp_user)
    config.set('Notification', 'smtp_pass', smtp_pass)
    config.set('Notification', 'email_from', email_from)
    config.set('Notification', 'email_to', email_to)
    
    config.add_section('Misc')
    config.set('Misc', 'numrelays', numRelays)
    config.set('Misc', 'numsensors', numSensors)
    config.set('Misc', 'numtimers', numTimers)
    config.set('Misc', 'cameralight', cameraLight)
    
    config.add_section('Relay1')
    config.set('Relay1', 'relay1name', relayName[1])
    config.set('Relay1', 'relay1pin', relayPin[1])
    config.set('Relay1', 'relay1trigger', relayTrigger[1])
    
    config.add_section('Relay2')
    config.set('Relay2', 'relay2name', relayName[2])
    config.set('Relay2', 'relay2pin', relayPin[2])
    config.set('Relay2', 'relay2trigger', relayTrigger[2])
    
    config.add_section('Relay3')
    config.set('Relay3', 'relay3name', relayName[3])
    config.set('Relay3', 'relay3pin', relayPin[3])
    config.set('Relay3', 'relay3trigger', relayTrigger[3])
    
    config.add_section('Relay4')
    config.set('Relay4', 'relay4name', relayName[4])
    config.set('Relay4', 'relay4pin', relayPin[4])
    config.set('Relay4', 'relay4trigger', relayTrigger[4])
    
    config.add_section('Relay5')
    config.set('Relay5', 'relay5name', relayName[5])
    config.set('Relay5', 'relay5pin', relayPin[5])
    config.set('Relay5', 'relay5trigger', relayTrigger[5])
    
    config.add_section('Relay6')
    config.set('Relay6', 'relay6name', relayName[6])
    config.set('Relay6', 'relay6pin', relayPin[6])
    config.set('Relay6', 'relay6trigger', relayTrigger[6])
    
    config.add_section('Relay7')
    config.set('Relay7', 'relay7name', relayName[7])
    config.set('Relay7', 'relay7pin', relayPin[7])
    config.set('Relay7', 'relay7trigger', relayTrigger[7])
    
    config.add_section('Relay8')
    config.set('Relay8', 'relay8name', relayName[8])
    config.set('Relay8', 'relay8pin', relayPin[8])
    config.set('Relay8', 'relay8trigger', relayTrigger[8])
    
    config.add_section('Timer1')
    config.set('Timer1', 'timer1state', timerState[1])
    config.set('Timer1', 'timer1relay', timerRelay[1])
    config.set('Timer1', 'timer1durationon', timerDurationOn[1])
    config.set('Timer1', 'timer1durationoff', timerDurationOff[1])
    
    config.add_section('Timer2')
    config.set('Timer2', 'timer2state', timerState[2])
    config.set('Timer2', 'timer2relay', timerRelay[2])
    config.set('Timer2', 'timer2durationon', timerDurationOn[2])
    config.set('Timer2', 'timer2durationoff', timerDurationOff[2])
    
    config.add_section('Timer3')
    config.set('Timer3', 'timer3state', timerState[3])
    config.set('Timer3', 'timer3relay', timerRelay[3])
    config.set('Timer3', 'timer3durationon', timerDurationOn[3])
    config.set('Timer3', 'timer3durationoff', timerDurationOff[3])
    
    config.add_section('Timer4')
    config.set('Timer4', 'timer4state', timerState[4])
    config.set('Timer4', 'timer4relay', timerRelay[4])
    config.set('Timer4', 'timer4durationon', timerDurationOn[4])
    config.set('Timer4', 'timer4durationoff', timerDurationOff[4])
    
    config.add_section('Timer5')
    config.set('Timer5', 'timer5state', timerState[5])
    config.set('Timer5', 'timer5relay', timerRelay[5])
    config.set('Timer5', 'timer5durationon', timerDurationOn[5])
    config.set('Timer5', 'timer5durationoff', timerDurationOff[5])
    
    config.add_section('Timer6')
    config.set('Timer6', 'timer6state', timerState[6])
    config.set('Timer6', 'timer6relay', timerRelay[6])
    config.set('Timer6', 'timer6durationon', timerDurationOn[6])
    config.set('Timer6', 'timer6durationoff', timerDurationOff[6])
    
    config.add_section('Timer7')
    config.set('Timer7', 'timer7state', timerState[7])
    config.set('Timer7', 'timer7relay', timerRelay[7])
    config.set('Timer7', 'timer7durationon', timerDurationOn[7])
    config.set('Timer7', 'timer7durationoff', timerDurationOff[7])
    
    config.add_section('Timer8')
    config.set('Timer8', 'timer8state', timerState[8])
    config.set('Timer8', 'timer8relay', timerRelay[8])
    config.set('Timer8', 'timer8durationon', timerDurationOn[8])
    config.set('Timer8', 'timer8durationoff', timerDurationOff[8])
    
    try:
        with open(config_file, 'wb') as configfile:
            config.write(configfile)
    except:
        logging.warning("[Write Config] Unable to write config: %s", config_lock_path)
        
    logging.debug("[Write Config] Removing lock: %s", lock.path)
    lock.release()

# Initialize GPIO
def gpio_initialize():
    logging.info("[GPIO Initialize] Set GPIO mode to BCM numbering, all as output")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(relayPin[1], GPIO.OUT)
    GPIO.setup(relayPin[2], GPIO.OUT)
    GPIO.setup(relayPin[3], GPIO.OUT)
    GPIO.setup(relayPin[4], GPIO.OUT)
    GPIO.setup(relayPin[5], GPIO.OUT)
    GPIO.setup(relayPin[6], GPIO.OUT)
    GPIO.setup(relayPin[7], GPIO.OUT)
    GPIO.setup(relayPin[8], GPIO.OUT)

# Read states (HIGH/LOW) of GPIO pins
def gpio_read():
    for x in range(1, 9):
        if GPIO.input(relayPin[x]): logging.info("[GPIO Read] Relay %s: OFF", x)
        else: logging.info("[GPIO Read] Relay %s: ON", x)

# Turn relay on or off (accounts for trigger)
def relay_onoff(relay, state):
    if (relayTrigger[relay] == 1 and state == 1):
        gpio_change(relay, 1)
    elif (relayTrigger[relay] == 1 and state == 0):
        gpio_change(relay, 0)
    elif (relayTrigger[relay] == 0 and state == 1):
        gpio_change(relay, 0)
    elif (relayTrigger[relay] == 0 and state == 0):
        gpio_change(relay, 1)
        
# Change GPIO (Select) to a specific state (State)
def gpio_change(relay, State):
    logging.debug("[GPIO Write] Setting relay %s (%s) to %s (was %s)", 
        relay, relayName[relay], 
        State, GPIO.input(relayPin[relay]))
    GPIO.output(relayPin[relay], State)

# Set GPIO LOW (= relay ON) for a specific duration
def relay_on_duration(relay, seconds):
    if (relayTrigger[relay] == 0 and GPIO.input(relayPin[relay]) == 0) or (
            relayTrigger[relay] == 1 and GPIO.input(relayPin[relay]) == 1):
        logging.warning("[Relay Duration] Relay %s (%s) is already On. Turning off in %s seconds.", 
            relay, relayName[relay], seconds)
    else:
        logging.debug("[Relay Duration] Relay %s (%s) ON for %s seconds", 
            relay, relayName[relay], round(seconds, 1))
   
    GPIO.output(relayPin[relay], relayTrigger[relay]) # Turn relay on    
    timer_on = int(time.time()) + seconds
    write_relay_log(relay, seconds)
    
    while (ClientQue != 'TerminateServer' and timer_on > int(time.time())):
        time.sleep(0.1)
        
    if relayTrigger[relay] == 0: GPIO.output(relayPin[relay], 1) # Turn relay off
    else: GPIO.output(relayPin[relay], 0) # Turn relay off
    logging.debug("[Relay Duration] Relay %s (%s) Off (was On for %s sec)", 
        relay, relayName[relay], round(seconds, 1))
    return 1

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

# Check if a variable name in config_file matches a string
def modify_var(*names_and_values):
    global Temp_PID_Down
    global Temp_PID_Up
    global Hum_PID_Down
    global Hum_PID_Up
    global ClientQue
    HumRes = 0
    TempRes = 0

    namesOfVariables = [
    'DHTSensor',
    'DHTPin.'
    'DHTSeconds',
    'relayName',
    'relayPin',
    'relayTrigger',
    'relayTemp',
    'relayHum',
    'setTemp',
    'setHum',
    'TempOR',
    'HumOR',
    'Hum_P',
    'Hum_I',
    'Hum_D',
    'Temp_P',
    'Temp_I',
    'Temp_D',
    'factorHumSeconds',
    'factorTempSeconds',
    'relay1Pin',
    'relay2Pin',
    'relay3Pin',
    'relay4Pin',
    'relay5Pin',
    'relay6Pin',
    'relay7Pin',
    'relay8Pin',
    'relay1Name',
    'relay2Name',
    'relay3Name',
    'relay4Name',
    'relay5Name',
    'relay6Name',
    'relay7Name',
    'relay8Name',
    'numRelays',
    'numSensors',
    'numTimers',
    'smtp_host',
    'smtp_port',
    'smtp_user',
    'smtp_pass',
    'email_from',
    'email_to']
    
    for i in range(1, len(names_and_values), 2):
        for variable in namesOfVariables:
            if names_and_values[i] == variable:
                # Log variable name: previous value -> new value
                logging.info("[Change Variable] %s: %s -> %s", 
                    names_and_values[i], 
                    globals()[names_and_values[i]], 
                    names_and_values[i+1])
                if TempRes == 0 and (names_and_values[i] == 'relayTemp' or names_and_values[i] == 'TempOR' or names_and_values[i] == 'Temp_P' or names_and_values[i] == 'Temp_I' or names_and_values[i] == 'Temp_D' or names_and_values[i] == 'setTemp'):
                    TempRes = 1
                    Temp_PID_Down = 1
                    while Temp_PID_Down == 1:
                        time.sleep(0.1)
                if HumRes == 0 and (names_and_values[i] == 'relayHum' or names_and_values[i] == 'HumOR' or names_and_values[i] == 'Hum_P' or names_and_values[i] == 'Hum_I' or names_and_values[i] == 'Hum_D' or names_and_values[i] == 'setHum'):
                    HumRes = 1
                    Hum_PID_Down = 1
                    while Hum_PID_Down == 1:
                        time.sleep(0.1)
                globals()[names_and_values[i]] = names_and_values[i+1]
                     
    write_config()
    read_config(1)
    
    if TempRes:
        Temp_PID_Up = 1
        while Temp_PID_Up:
            time.sleep(0.1)
        
    if HumRes:
        Hum_PID_Up = 1
        while Hum_PID_Up:
            time.sleep(0.1)
            
    return 1

def email():
    # At First we have to get the current CPU-Temperature with this defined function
    if (smtp_ssl):
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        server.ehlo()
    else:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
    server.ehlo
    server.login(smtp_user, smtp_pass)

    message = "Critical warning!!!"
    
    msg = MIMEText(message)
    msg['Subject'] = "Critical warning!"
    msg['From'] = "Raspberry Pi"
    msg['To'] = email_from
    server.sendmail(email_from, email_to, msg.as_string())
    server.quit()

# Timestamp format used in sensor and relay logs
def timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')

read_config(1)
gpio_initialize()
menu()
usage()
sys.exit(0)