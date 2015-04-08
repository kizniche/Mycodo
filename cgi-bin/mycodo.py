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
import subprocess
import sys
import threading
import time
from array import *
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
    filename=daemon_log_file_tmp,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s')

lock_directory = "/var/lock/mycodo"
config_lock_path = "%s/config" % lock_directory
daemon_lock_path = "%s/daemon" % lock_directory
sensor_lock_path = "%s/sensor" % lock_directory
relay_lock_path = "%s/relay" % lock_directory

# GPIO pins (BCM numbering) and name of devices attached to relay
relayPin = [0] * 9
relayName = [0] * 9
relayTrigger = [0] * 9

# Sensor data
chktemp = ''
tempc = ''
humidity = ''
dewpointc = ''
heatindexc =  ''

#PID
relayTemp =''
relayHum = ''
setTemp = ''
setHum = ''
Hum_P = ''
Hum_I = ''
Hum_D = ''
Temp_P = ''
Temp_I = ''
Temp_D = ''
factorHumSeconds = ''
factorTempSeconds = ''

# Control States
tempState = ''
humState = ''
TempOR = ''
HumOR = ''

# Timers
DHTSeconds = ''

# Relay overrides
relay1o = ''
relay2o = ''
relay3o = ''
relay4o = ''
relay5o = ''
relay6o = ''
relay7o = ''
relay8o = ''

# Sensor
DHTSensor = ''
DHTPin = ''

# Miscellaneous
cameraLight = ''
server = ''
variableName = ''
variableValue = ''
ClientQue = '0'
ClientArg1 = ''
ClientArg2 = ''
Terminate = False
TAlive = 1
HAlive = 1
holderTempOR = ''
holderHumOR = ''
Temp_PID_restart = 0
Hum_PID_restart = 0

# Threaded server that receives commands from mycodo-client.py
class ComServer(rpyc.Service):
    def exposed_Modify_Variables(self, *variable_list):
        read_config(0)
        logging.info("[Client command] Request to change variables")
        modify_var(*variable_list)
        read_config(0)
        return 1
    def exposed_Terminate(self, remoteCommand):
        global ClientQue
        global Terminate
        Terminate = True
        ClientQue = 'TerminateServer'
        return 1
    def exposed_ChangeGPIO(self, remoteCommand, remoteCommand2):
        global ClientQue
        global ClientArg1
        global ClientArg2
        ClientArg1 = int(float(remoteCommand))
        ClientArg2 = int(float(remoteCommand2))
        ClientQue = 'gpio_change'
        return 1
    def exposed_RelayOnSec(self, remoteCommand, remoteCommand2):
        global ClientQue
        global ClientArg1
        global ClientArg2
        ClientArg1 = remoteCommand
        ClientArg2 = remoteCommand2
        ClientQue = 'RelayOnSec'
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
    print "mycodo.py: Reads temperature and humidity from sensors, " \
        "writes log file, and operates relays as a daemon to maintain " \
        "set environmental conditions.\n"
    print "Usage:   mycodo.py [OPTION]...\n"
    print "Example: mycodo.py -w /var/www/mycodo/log/sensor.log"
    print "         mycodo.py -d s"
    print "         mycodo.py -n relay1Name --value Banana"
    print "         mycodo.py --read\n"
    print "Options:"
    print "    -c, --change [RELAY] [ON/OFF/X]"
    print "           Change the state of a relay RELAY"
    print "           to ON, OFF, or (X) number of seconds on"
    print "    -d, --daemon [v/s]"
    print "           Start program as daemon that monitors conditions and modulates relays"
    print "           If ""v"" is set, then log output is sent tot the console, ""s"" for silent"
    print "    -h, --help"
    print "           Display this help and exit"
    print "    -p, --pin"
    print "           Display status of the GPIO pins (HIGH or LOW)"
    print "    -r  --read"
    print "           Read and display sensor data"
    print "    -s, --set setTemp setHum TempOR HumOR"
    print "           Change operating parameters (must give all options as int, overrides must be 0 or 1)"
    print "    -w, --write=FILE"
    print "           Write sensor data to log file\n"

# Checks user options and arguments for validity
def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:dhprs:tw',
            ["change=", "daemon", "help", "pin",
            "read", "set=", "write="])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c", "--change"):
            if not represents_int(sys.argv[2]) or \
                    int(float(sys.argv[2])) > 8 or \
                    int(float(sys.argv[2])) < 1:
                print "Error: --change only accepts integers 1 though 8"
                sys.exit(1)
            else:
                global relaySelect
                relaySelect = int(float(sys.argv[2]))
            if represents_int(sys.argv[3]) and int(float(sys.argv[3])) > 1 or \
                    (sys.argv[3] == 'OFF' or sys.argv[3] == 'ON'):
                read_config(0)
                if sys.argv[3] == 'ON':
                    print "%s [GPIO Write] Relay %s ON" % (
                        timestamp(), relaySelect)
                    if (relayTrigger[int(float(sys.argv[2]))] == 1): gpio_change(relaySelect, 1)
                    else: gpio_change(relaySelect, 0)
                    gpio_read()
                    sys.exit(0)
                if sys.argv[3] == 'OFF':
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
        elif opt in ("-d", "--daemon"):
            if (sys.argv[2] == '-v'): daemon('verbose')
            else: daemon('silent')
            sys.exit(0)
        elif opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-p", "--pin"):
            read_config(0)
            gpio_read()
            sys.exit(0)
        elif opt in ("-r", "--read"):
            read_sensors(0)
            sys.exit(0)
        elif opt in ("-s", "--set"):
            if len(sys.argv) != 6:
                print "Error: Too many/not enough options"
                sys.exit(1)
            elif not represents_float(sys.argv[2]) and \
                    not represents_float(sys.argv[3]) and \
                    not represents_int(sys.argv[4]) and \
                    not represents_int(sys.argv[5]):
                print "Error: --set: temperature and humidity requires one decimal place and overrides need to be either 1 or 0"
                sys.exit(1)
            elif (sys.argv[4] != '0' and sys.argv[4] != '1') or \
                    (sys.argv[5] != '0' and sys.argv[5] != '1'):
                print "Error: Last option of --set must be 0 or 1"
                sys.exit(0)
            print "[Set Conditions] Desired values: " \
                "setTemp: %s, setHum: %s, TempOR: %s, HumOR: %s" % (
                sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
            read_config(0)
            global setTemp
            global setHum
            global TempOR
            global HumOR
            setTemp = int(float(sys.argv[2]))
            setHum = int(float(sys.argv[3]))
            TempOR = int(float(sys.argv[4]))
            HumOR = int(float(sys.argv[5]))
            write_config()
            print "[Set Conditions] New Values: " \
                "setTemp: %.1f°C, setHum: %.1f%%, TempOR: %s, HumOR: %s" % (
                timestamp(), setTemp, setHum, TempOR, HumOR)
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
def daemon(output):
    global Temp_PID_restart
    global Hum_PID_restart
    global server
    global HAlive
    global TAlive
    global ClientQue
    
    if (output == 'verbose'):
        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
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
   
    tm = threading.Thread(target = temperature_monitor)   
    tm.daemon = True
    tm.start()
    
    hm = threading.Thread(target = humidity_monitor)
    hm.daemon = True
    hm.start()

    while True: # Main loop of the daemon
        if ClientQue != '0': # Run remote commands issued by mycodo-client.py
            if ClientQue == 'write_sensor_log':
                logging.info("[Client command] Write Sensor Log")
                read_sensors(0)
                write_sensor_log()
            elif ClientQue == 'gpio_change':
                logging.info("[Client command] Set Relay %s GPIO to %s", ClientArg1, ClientArg1)
                gpio_change(ClientArg1, ClientArg2)
                gpio_read()
            elif ClientQue == 'RelayOnSec':
                logging.info("[Client command] Set Relay %s on for %s seconds", ClientArg1, ClientArg2)
                relay_on_duration(ClientArg1, ClientArg2)
            elif ClientQue == 'TerminateServer':
                logging.info("[Client command] Terminate threads and shut down")
                Concatenate_Logs()
                logging.info("[Daemon] Backing up logs")
                TAlive = 0
                while TAlive != 2:
                    time.sleep(0.1)
                HAlive = 0
                while HAlive != 2:
                    time.sleep(0.1)
                server.close()
                logging.info("[Daemon] Exiting Python")
                sys.exit(0)

            if Temp_PID_restart == 1:
                if tm.isAlive():
                    logging.info("[Daemon] Restarting Temperature PID thread")
                    TAlive = 0
                    while TAlive != 2:
                        time.sleep(0.1)
                    TAlive = 1
                Temp_PID_restart = 0
                tm = threading.Thread(target = temperature_monitor)  
                tm.daemon = True
                tm.start()
            
            if Hum_PID_restart:
                if hm.isAlive():
                    logging.info("[Daemon] Restarting Humidity PID thread")
                    HAlive = 0
                    while HAlive != 2:
                        time.sleep(0.1)
                    HAlive = 1
                Hum_PID_restart = 0
                hm = threading.Thread(target = humidity_monitor)
                hm.daemon = True
                hm.start()
                
            ClientQue = '0'
        
        # Write sensor log
        if int(time.time()) > timerSensorLog and DHTSensor != 'Other':
            logging.info("[Timer Expiration] Run every %s seconds: Write sensor log", DHTSeconds)
            read_sensors(0)
            write_sensor_log()
            timerSensorLog = int(time.time()) + DHTSeconds
        
        # Concatenate local log with tempfs log every 6 hours
        if int(time.time()) > timerLogBackup:
            Concatenate_Logs()
            timerLogBackup = int(time.time()) + 21600

        time.sleep(0.1)

# Temperature modulation by PID control
def temperature_monitor():
    global tempState
    global TAlive
    timerTemp = 0
    PIDTemp = 0
    logging.info("[PID Temperature] Starting Thread")
    if (tempc < setTemp):
        tempState = 0
    else: 
        tempState = 1
        if (relayTrigger[relayTemp] == 0): gpio_change(relayTemp, 1)
        else: gpio_change(relayTemp, 0)
    p_temp = Temperature_PID(Temp_P, Temp_I, Temp_D)
    p_temp.setPoint(setTemp)
    
    while (TAlive):
        if TempOR == 0 and Temp_PID_restart == 0:
            if int(time.time()) > timerTemp:
                logging.info("[PID Temperature] Reading temperature...")
                read_sensors(1)
                if (tempc >= setTemp): tempState = 1
                if (tempc < setTemp): tempState = 0
                if (tempState == 0):
                    PIDTemp = round(p_temp.update(float(tempc)), 1)
                    logging.info("[PID Temperature] Temperature (%.1f°C) < (%.1f°C) setTemp", tempc, setTemp)
                    logging.info("[PID Temperature] PID = %.1f (seconds)", PIDTemp)
                    if (PIDTemp > 0 and tempc < setTemp):
                        rod = threading.Thread(target = relay_on_duration, 
                            args = (relayTemp, PIDTemp,))
                        rod.start()
                    timerTemp = int(time.time()) + PIDTemp + factorTempSeconds
                else:
                    logging.info("[PID Temperature] Temperature (%.1f°C) >= (%.1f°C) setTemp, waiting 60 seconds", tempc, setTemp)
                    p_temp.update(float(tempc))
                    timerTemp = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID Temperature] Shutting Down Thread")
    TAlive = 2

# Humidity modulation by PID control
def humidity_monitor():
    global humState
    global HAlive
    timerHum = 0
    PIDHum = 0

    logging.info("[PID Humidity] Starting Thread")
    if (humidity < setHum):
        humState = 0
    else:
        humState = 1
        if (relayTrigger[relayHum] == 0): gpio_change(relayHum, 1)
        else: gpio_change(relayHum, 1)
    p_hum = Humidity_PID(Hum_P, Hum_I, Hum_D)
    p_hum.setPoint(setHum)

    while (HAlive):
        if HumOR == 0 and Hum_PID_restart == 0:
            if int(time.time()) > timerHum:
                logging.info("[PID Humidity] Reading humidity...")
                read_sensors(1)
                if (humidity >= setHum): humState = 1
                if (humidity < setHum): humState = 0
                if (humState == 0):
                    PIDHum = round(p_hum.update(float(humidity)), 1)
                    logging.info("[PID Humidity] Humidity (%.1f%%) < (%.1f%%) setHum", humidity, setHum)
                    logging.info("[PID Humidity] PID = %.1f (seconds)", PIDHum)
                    if (PIDHum > 0 and humidity < setHum):
                        rod = threading.Thread(target = relay_on_duration,
                            args=(relayHum, PIDHum,))
                        rod.start()
                    timerHum = int(time.time()) + PIDHum + factorTempSeconds
                else:
                    logging.info("[PID Humidity] Humidity (%.1f%%) >= (%.1f%%) setHum, waiting 60 seconds", humidity, setHum)
                    p_hum.update(float(humidity))
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
                logging.info("[Write Sensor Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Write Sensor Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()
        logging.info("[Write Sensor Log] Gained lock: %s", lock.path)
        try:
            with open(sensor_log_file_tmp, "ab") as sensorlog:
                sensorlog.write('{0} {1:.1f} {2:.1f} {3:.1f}\n'.format(
                    datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                    tempc, humidity, dewpointc))
                logging.info("[Write Sensor Log] Data appended to %s", sensor_log_file_tmp)
        except:
            logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_log_file_tmp)
        logging.info("[Write Sensor Log] Removing lock: %s", lock.path)
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
                logging.info("[Write Relay Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Write Relay Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()
        logging.info("[Write Relay Log] Gained lock: %s", lock.path)
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
        logging.info("[Write Relay Log] Removing lock: %s", lock.path)
        lock.release()

# Combines the logs on the SD card with the logs on the temporary file system
def Concatenate_Logs():
    logging.info("[Timer Expiration] Run every 6 hours: Concatenate logs")
    if not filecmp.cmp(daemon_log_file_tmp, daemon_log_file):
        logging.info("[Daemon Log] Concatenating daemon logs to %s", daemon_log_file)
        lock = LockFile(daemon_lock_path)
        while not lock.i_am_locking():
            try:
                logging.info("[Daemon Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Daemon Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()
        logging.info("[Daemon Log] Gained lock: %s", lock.path)
        try:
            with open(daemon_log_file, 'a') as fout:
                for line in fileinput.input(daemon_log_file_tmp):
                    fout.write(line)
            logging.info("[Daemon Log] Appended data to %s", daemon_log_file)
        except:
            logging.warning("[Daemon Log] Unable to append data to %s", daemon_log_file)
        open(daemon_log_file_tmp, 'w').close()
        logging.info("[Daemon Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.info("[Daemon Log] Daemon logs the same, skipping.")
    if not filecmp.cmp(sensor_log_file_tmp, sensor_log_file):
        logging.info("[Sensor Log] Concatenating sensor logs to %s", sensor_log_file)
        lock = LockFile(sensor_lock_path)
        while not lock.i_am_locking():
            try:
                logging.info("[Sensor Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Sensor Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()
        logging.info("[Sensor Log] Gained lock: %s", lock.path)
        try:
            with open(sensor_log_file, 'a') as fout:
                for line in fileinput.input(sensor_log_file_tmp):
                    fout.write(line)
            logging.info("[Daemon Log] Appended data to %s", sensor_log_file)
        except:
            logging.warning("[Sensor Log] Unable to append data to %s", sensor_log_file)
        open(sensor_log_file_tmp, 'w').close()
        logging.info("[Sensor Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.info("[Sensor Log] Sensor logs the same, skipping.")
    if not filecmp.cmp(relay_log_file_tmp, relay_log_file):
        logging.info("[Relay Log] Concatenating relay logs to %s", relay_log_file)
        lock = LockFile(relay_lock_path)
        while not lock.i_am_locking():
            try:
                logging.info("[Relay Log] Acquiring Lock: %s", lock.path)
                lock.acquire(timeout=60)    # wait up to 60 seconds
            except:
                logging.warning("[Relay Log] Breaking Lock to Acquire: %s", lock.path)
                lock.break_lock()
                lock.acquire()
        logging.info("[Relay Log] Gained lock: %s", lock.path)
        try:
            with open(relay_log_file, 'a') as fout:
                for line in fileinput.input(relay_log_file_tmp):
                    fout.write(line)
            logging.info("[Daemon Log] Appended data to %s", relay_log_file)
        except:
            logging.warning("[Relay Log] Unable to append data to %s", relay_log_file)
        open(relay_log_file_tmp, 'w').close()
        logging.info("[Relay Log] Removing lock: %s", lock.path)
        lock.release()
    else:
        logging.info("[Relay Log] Relay logs the same, skipping.")

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
        logging.info("[Read Sensors] Taking first Temperature/humidity reading")
    if not Terminate:
        humidity2, tempc2 = Adafruit_DHT.read_retry(sensor, DHTPin)
        if not silent:
            logging.info("[Read Sensors] %.1f°C, %.1f%%", tempc2, humidity2)
    if not Terminate:
        time.sleep(2)
        if not silent: 
            logging.info("[Read Sensors] Taking second Temperature/humidity reading")

    while chktemp and not Terminate:
        if not Terminate:
            humidity, tempc = Adafruit_DHT.read_retry(sensor, DHTPin)
        if not silent and not Terminate: 
            logging.info("[Read Sensors] %.1f°C, %.1f%%", tempc, humidity)
            logging.info("[Read Sensors] Differences: %.1f°C, %.1f%%", abs(tempc2-tempc), abs(humidity2-humidity))
        if abs(tempc2-tempc) > 1 or abs(humidity2-humidity) > 1 and not Terminate:
            tempc2 = tempc
            humidity2 = humidity
            chktemp = 1
            if not silent:
                logging.info("[Read Sensors] Successive readings > 1 difference: Rereading")
            time.sleep(2)
        elif not Terminate:
            chktemp = 0
            if not silent: 
                logging.info("[Read Sensors] Successive readings < 1 difference: keeping.")
            tempf = float(tempc)*9.0/5.0 + 32.0
            dewpointc = tempc - ((100-humidity) / 5)
            #dewpointf = dewpointc * 9 / 5 + 32
            #heatindexf =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
            #heatindexc = (heatindexf - 32) * (5 / 9)
            if not silent: 
                logging.info("[Read Sensors] Temp: %.1f°C, Hum: %.1f%%, DP: %.1f°C", tempc, humidity, dewpointc)

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
    global tempState
    global humState
    global relay1o
    global relay2o
    global relay3o
    global relay4o
    global relay5o
    global relay6o
    global relay7o
    global relay8o
    global cameraLight

    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    
    DHTSensor = config.get('Sensor', 'dhtsensor')
    DHTPin = config.getint('Sensor', 'dhtpin')
    DHTSeconds = config.getint('Sensor', 'dhtseconds')

    relayName[1] = config.get('RelayNames', 'relay1name')
    relayName[2] = config.get('RelayNames', 'relay2name')
    relayName[3] = config.get('RelayNames', 'relay3name')
    relayName[4] = config.get('RelayNames', 'relay4name')
    relayName[5] = config.get('RelayNames', 'relay5name')
    relayName[6] = config.get('RelayNames', 'relay6name')
    relayName[7] = config.get('RelayNames', 'relay7name')
    relayName[8] = config.get('RelayNames', 'relay8name')

    relayPin[1] = config.getint('RelayPins', 'relay1pin')
    relayPin[2] = config.getint('RelayPins', 'relay2pin')
    relayPin[3] = config.getint('RelayPins', 'relay3pin')
    relayPin[4] = config.getint('RelayPins', 'relay4pin')
    relayPin[5] = config.getint('RelayPins', 'relay5pin')
    relayPin[6] = config.getint('RelayPins', 'relay6pin')
    relayPin[7] = config.getint('RelayPins', 'relay7pin')
    relayPin[8] = config.getint('RelayPins', 'relay8pin')
    
    relayTrigger[1] = config.getint('RelayTriggers', 'relay1trigger')
    relayTrigger[2] = config.getint('RelayTriggers', 'relay2trigger')
    relayTrigger[3] = config.getint('RelayTriggers', 'relay3trigger')
    relayTrigger[4] = config.getint('RelayTriggers', 'relay4trigger')
    relayTrigger[5] = config.getint('RelayTriggers', 'relay5trigger')
    relayTrigger[6] = config.getint('RelayTriggers', 'relay6trigger')
    relayTrigger[7] = config.getint('RelayTriggers', 'relay7trigger')
    relayTrigger[8] = config.getint('RelayTriggers', 'relay8trigger')

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
    
    tempState = config.getint('States', 'tempstate')
    humState = config.getint('States', 'humstate')
    relay1o = config.getint('States', 'relay1o')
    relay2o = config.getint('States', 'relay2o')
    relay3o = config.getint('States', 'relay3o')
    relay4o = config.getint('States', 'relay4o')
    relay5o = config.getint('States', 'relay5o')
    relay6o = config.getint('States', 'relay6o')
    relay7o = config.getint('States', 'relay7o')
    relay8o = config.getint('States', 'relay8o')
    
    cameraLight = config.getint('Misc', 'cameralight')

    if not silent:
        logging.info("[Read Config] setTemp: %.1f°C, setHum: %.1f%%, TempOR: %s, HumOR: %s", setTemp, setHum, TempOR, HumOR)
        for x in range(1,9):
            logging.info("[Read Config] RelayNum[Name][Pin]: %s[%s][%s]", x, relayName[x], relayPin[x])
        logging.info("[Read Config] %s %s %s %s %s %s %s %s %s %s %s", 
            tempState, humState, 
            relay1o, relay2o, relay3o, relay4o, 
            relay5o, relay6o, relay7o, relay8o, 
            DHTSeconds)

# Write variables to configuration file
def write_config():
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    lock = LockFile(config_lock_path)
    while not lock.i_am_locking():
        try:
            logging.info("[Write Config] Waiting, Acquiring Lock: %s", lock.path)
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except:
            logging.warning("[Write Config] Breaking Lock to Acquire: %s", lock.path)
            lock.break_lock()
            lock.acquire()
    logging.info("[Write Config] Gained lock: %s", lock.path)
    logging.info("[Write Config] Writing config file %s", config_file)
    
    config.add_section('Sensor')
    config.set('Sensor', 'dhtsensor', DHTSensor)
    config.set('Sensor', 'dhtpin', DHTPin)
    config.set('Sensor', 'dhtseconds', DHTSeconds)
    
    config.add_section('RelayNames')
    config.set('RelayNames', 'relay1name', relayName[1])
    config.set('RelayNames', 'relay2name', relayName[2])
    config.set('RelayNames', 'relay3name', relayName[3])
    config.set('RelayNames', 'relay4name', relayName[4])
    config.set('RelayNames', 'relay5name', relayName[5])
    config.set('RelayNames', 'relay6name', relayName[6])
    config.set('RelayNames', 'relay7name', relayName[7])
    config.set('RelayNames', 'relay8name', relayName[8])
    
    config.add_section('RelayPins')
    config.set('RelayPins', 'relay1pin', relayPin[1])
    config.set('RelayPins', 'relay2pin', relayPin[2])
    config.set('RelayPins', 'relay3pin', relayPin[3])
    config.set('RelayPins', 'relay4pin', relayPin[4])
    config.set('RelayPins', 'relay5pin', relayPin[5])
    config.set('RelayPins', 'relay6pin', relayPin[6])
    config.set('RelayPins', 'relay7pin', relayPin[7])
    config.set('RelayPins', 'relay8pin', relayPin[8])
    
    config.add_section('RelayTriggers')
    config.set('RelayTriggers', 'relay1trigger', relayTrigger[1])
    config.set('RelayTriggers', 'relay2trigger', relayTrigger[2])
    config.set('RelayTriggers', 'relay3trigger', relayTrigger[3])
    config.set('RelayTriggers', 'relay4trigger', relayTrigger[4])
    config.set('RelayTriggers', 'relay5trigger', relayTrigger[5])
    config.set('RelayTriggers', 'relay6trigger', relayTrigger[6])
    config.set('RelayTriggers', 'relay7trigger', relayTrigger[7])
    config.set('RelayTriggers', 'relay8trigger', relayTrigger[8])

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

    config.add_section('States')
    config.set('States', 'tempstate', tempState)
    config.set('States', 'humstate', humState)
    config.set('States', 'relay1o', relay1o)
    config.set('States', 'relay2o', relay2o)
    config.set('States', 'relay3o', relay3o)
    config.set('States', 'relay4o', relay4o)
    config.set('States', 'relay5o', relay5o)
    config.set('States', 'relay6o', relay6o)
    config.set('States', 'relay7o', relay7o)
    config.set('States', 'relay8o', relay8o)
    
    config.add_section('Misc')
    config.set('Misc', 'cameralight', cameraLight)
    
    try:
        with open(config_file, 'wb') as configfile:
            config.write(configfile)
    except:
        logging.warning("[Write Config] Unable to write config: %s", config_lock_path)
        
    logging.info("[Write Config] Removing lock: %s", lock.path)
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

# Change GPIO (Select) to a specific state (State)
def gpio_change(Select, State):
    logging.info("[GPIO Write] Setting relay %s (%s) to %s (was %s)", 
        Select, relayName[Select], 
        State, GPIO.input(relayPin[Select]))
    GPIO.output(relayPin[Select], State)

# Set GPIO LOW (= relay ON) for a specific duration
def relay_on_duration(relay, seconds):
    if GPIO.input(relayPin[relay]) == 1:
        write_relay_log(relay, seconds)
        logging.info("[Relay Duration] Relay %s (%s) ON for %s seconds", 
            relay, relayName[relay], seconds)
        GPIO.output(relayPin[relay], relayTrigger[relay])
        time.sleep(seconds)
        if relayTrigger[relay] == 0: GPIO.output(relayPin[relay], 1)
        else: GPIO.output(relayPin[relay], 0)
        logging.info("[Relay Duration] Relay %s (%s) OFF (was ON for %s sec)", 
            relay, relayName[relay], seconds)
        return 1
    else:
        logging.warning("[Relay Duration] Abort: Requested relay %s (%s) ON for %s seconds, but it's already on!", 
            relay, relayName[relay], seconds)
        return 0

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
    global Temp_PID_restart
    global Hum_PID_restart
    global ClientQue

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
    'tempState',
    'humState',
    'relay1o',
    'relay2o',
    'relay3o',
    'relay4o',
    'relay5o',
    'relay6o',
    'relay7o',
    'relay8o',
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
    'relay8Name',]
    
    for i in range(1, len(names_and_values), 2):
        for variable in namesOfVariables:
            if names_and_values[i] == variable:
                #print "Variable:", names_and_values[i], "Value:", names_and_values[i+1]
                if names_and_values[i] == 'TempOR' or names_and_values[i] == 'Temp_P' or names_and_values[i] == 'Temp_I' or names_and_values[i] == 'Temp_D' or names_and_values[i] == 'setTemp':
                    ClientQue = '1'
                    Temp_PID_restart = 1
                    time.sleep(1)
                if names_and_values[i] == 'HumOR' or names_and_values[i] == 'Hum_P' or names_and_values[i] == 'Hum_I' or names_and_values[i] == 'Hum_D' or names_and_values[i] == 'setHum':
                    ClientQue = '1'
                    Hum_PID_restart = 1
                    time.sleep(1)
                globals()[names_and_values[i]] = names_and_values[i+1]
                    
    write_config()
    return 1

# Timestamp format used in sensor and relay logs
def timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')

read_config(1)
gpio_initialize()
menu()
usage()
sys.exit(0)