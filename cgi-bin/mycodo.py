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

# Sensors
numSensors = None
sensorName = [0] * 5
sensorDevice = [0] * 5
sensorPin = [0] * 5
sensorPeriod = [0] * 5

# Temperature PID
relayTemp = [0] * 5
setTemp = [0] * 5
TempPeriod = [0] * 5
Temp_P = [0] * 5
Temp_I = [0] * 5
Temp_D = [0] * 5
TempOR = [0] * 5

# Humidity PID
relayHum = [0] * 5
setHum = [0] * 5
HumPeriod = [0] * 5
Hum_P = [0] * 5
Hum_I = [0] * 5
Hum_D = [0] * 5
HumOR = [0] * 5

# Timers
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

# Sensor data
chktemp = None
tempc = [0] * 5
humidity = [0] * 5
dewpointc = [0] * 5
heatindexc =  [0] * 5

# Miscellaneous
cameraLight = None
server = None
variableName = None
variableValue = None
ClientQue = '0'
ClientVar1 = None
Terminate = False
TAlive = [1] * 5
HAlive = [1] * 5
Temp_PID_Down = 0
Temp_PID_Up = 0
Hum_PID_Down = 0
Hum_PID_Up = 0
Temp_PID_number = None
Hum_PID_number = None

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
                args = (int(relay), int(state), 0,))
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
    def exposed_ChangeTempOR(self, sensornum, override):
        global TempOR
        global Temp_PID_number
        global Temp_PID_Down
        global Temp_PID_Up
        
        TempOR[sensornum] = override
        logging.info("[Client command] Change TempOR for sensor %s to %s",
            sensornum, override)
        
        Temp_PID_number = sensornum
        TempRes = 1
        Temp_PID_Down = 1
        while Temp_PID_Down == 1:
            time.sleep(0.1)
        write_config()
        read_config(1)
        if TempRes:
            Temp_PID_Up = 1
            while Temp_PID_Up:
                time.sleep(0.1)
        return 1
    def exposed_ChangeTempPID(self, sensornum, relay, set, p, i, d, period):
        global relayTemp
        global setTemp
        global TempPeriod
        global Temp_P
        global Temp_I
        global Temp_D
        global TempOR
        global Temp_PID_number
        global Temp_PID_Down
        global Temp_PID_Up
        
        logging.info("[Client command] Change Temp PID for sensor %s: Relay: %s Set: %s P: %s I: %s D: %s Period: %s",
            sensornum, relay, set, p , i, d, period)
        relayTemp[sensornum] = relay
        setTemp[sensornum] = set
        TempPeriod[sensornum] = period
        Temp_P[sensornum] = p
        Temp_I[sensornum] = i
        Temp_D[sensornum] = d

        Temp_PID_number = sensornum
        TempRes = 1
        Temp_PID_Down = 1
        while Temp_PID_Down == 1:
            time.sleep(0.1)
        write_config()
        read_config(1)
        if TempRes:
            Temp_PID_Up = 1
            while Temp_PID_Up:
                time.sleep(0.1)

        return 1
    def exposed_ChangeHumOR(self, sensornum, override):
        global HumOR
        global Hum_PID_number
        global Hum_PID_Down
        global Hum_PID_Up
        
        HumOR[sensornum] = override
        logging.info("[Client command] Change HumOR for sensor %s to %s",
            sensornum, override)
        
        Hum_PID_number = sensornum
        HumRes = 1
        Hum_PID_Down = 1
        while Hum_PID_Down == 1:
            time.sleep(0.1)
        write_config()
        read_config(1)
        if HumRes:
            Hum_PID_Up = 1
            while Hum_PID_Up:
                time.sleep(0.1)
        return 1
    def exposed_ChangeHumPID(self, sensornum, relay, set, p, i, d, period):
        global relayHum
        global setHum
        global HumPeriod
        global Hum_P
        global Hum_I
        global Hum_D
        global HumOR
        global Hum_PID_number
        global Hum_PID_Down
        global Hum_PID_Up
        
        logging.info("[Client command] Change Hum PID for sensor %s: Relay: %s Set: %s P: %s I: %s D: %s Period: %s",
            sensornum, relay, set, p , i, d, period)
        relayHum[sensornum] = relay
        setHum[sensornum] = set
        HumPeriod[sensornum] = period
        Hum_P[sensornum] = p
        Hum_I[sensornum] = i
        Hum_D[sensornum] = d
        
        Hum_PID_number = sensornum
        HumRes = 1
        Hum_PID_Down = 1
        while Hum_PID_Down == 1:
            time.sleep(0.1)
        write_config()
        read_config(1)
        if HumRes:
            Hum_PID_Up = 1
            while Hum_PID_Up:
                time.sleep(0.1)
                
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
    def exposed_ChangeSensorNames(self, sensorname1, sensorname2, sensorname3,
            sensorname4, sensorname5, sensorname6, sensorname7, sensorname8):
        global sensorName
        sensorName[1] = sensorname1
        sensorName[2] = sensorname2
        sensorName[3] = sensorname3
        sensorName[4] = sensorname4
        sensorName[5] = sensorname5
        sensorName[6] = sensorname6
        sensorName[7] = sensorname7
        sensorName[8] = sensorname8
        logging.info("[Client command] Change Sensor Names: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            sensorName[1], sensorName[2], sensorName[3], sensorName[4],
            sensorName[5], sensorName[6], sensorName[7], sensorName[8])
        write_config()
        return 1
    def exposed_ChangeSensorDevices(self, sensordevice1, sensordevice2, sensordevice3,
            sensordevice4, sensordevice5, sensordevice6, sensordevice7, sensordevice8):
        global sensorDevice
        sensorDevice[1] = sensordevice1
        sensorDevice[2] = sensordevice2
        sensorDevice[3] = sensordevice3
        sensorDevice[4] = sensordevice4
        sensorDevice[5] = sensordevice5
        sensorDevice[6] = sensordevice6
        sensorDevice[7] = sensordevice7
        sensorDevice[8] = sensordevice8
        logging.info("[Client command] Change Sensor Devices: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            sensorDevice[1], sensorDevice[2], sensorDevice[3], sensorDevice[4],
            sensorDevice[5], sensorDevice[6], sensorDevice[7], sensorDevice[8])
        write_config()
        return 1
    def exposed_ChangeSensorPins(self, sensorpin1, sensorpin2, sensorpin3,
            sensorpin4, sensorpin5, sensorpin6, sensorpin7, sensorpin8):
        global sensorPin
        sensorPin[1] = sensorpin1
        sensorPin[2] = sensorpin2
        sensorPin[3] = sensorpin3
        sensorPin[4] = sensorpin4
        sensorPin[5] = sensorpin5
        sensorPin[6] = sensorpin6
        sensorPin[7] = sensorpin7
        sensorPin[8] = sensorpin8
        logging.info("[Client command] Change Sensor Pins: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            sensorPin[1], sensorPin[2], sensorPin[3], sensorPin[4],
            sensorPin[5], sensorPin[6], sensorPin[7], sensorPin[8])
        write_config()
        return 1   
    def exposed_ChangeSensorPeriods(self, sensorperiod1, sensorperiod2, sensorperiod3,
            sensorperiod4, sensorperiod5, sensorperiod6, sensorperiod7, sensorperiod8):
        global sensorPeriod
        sensorPeriod[1] = sensorperiod1
        sensorPeriod[2] = sensorperiod2
        sensorPeriod[3] = sensorperiod3
        sensorPeriod[4] = sensorperiod4
        sensorPeriod[5] = sensorperiod5
        sensorPeriod[6] = sensorperiod6
        sensorPeriod[7] = sensorperiod7
        sensorPeriod[8] = sensorperiod8
        logging.info("[Client command] Change Sensor Periods: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s",
            sensorPeriod[1], sensorPeriod[2], sensorPeriod[3], sensorPeriod[4],
            sensorPeriod[5], sensorPeriod[6], sensorPeriod[7], sensorPeriod[8])
        write_config()
        return 1
    def exposed_WriteSensorLog(self, sensor):
        global ClientQue
        global ClientVar1
        ClientVar1 = sensor
        ClientQue = 'write_sensor_log'
        logging.info("[Client command] Read sensor number %s and append log", sensor)
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
    print "    -d, --daemon v/s w/i/d"
    print "           Start program as daemon that monitors conditions and modulates relays"
    print "           ""v"" enables log output to the console, ""s"" silences"
    print "           Log leve: ""w"": >= warnings, ""i"": >= info, ""d"": >= debug"
    print "    -h, --help"
    print "           Display this help and exit"
    print "    -p, --pin"
    print "           Display status of the GPIO pins (HIGH or LOW)"
    print "    -r, --relay RELAY_NUMBER 0/1/X"
    print "           Change the state of a relay"
    print "           0=OFF, 1=ON, or X number of seconds On"
    print "    -s,  --sensor SENSOR_NUMBER"
    print "           Read and display sensor data from SENSOR_NUMBER"
    print "    -w, --write SENSOR_NUMBER [FILE]"
    print "           Write sensor data from SENSOR_NUMBER to log FILE\n"
    print "Examples: mycodo.py -w 2 /var/www/mycodo/log/sensor.log"
    print "          mycodo.py -d s w\n"

# Checks user options and arguments for validity
def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'r:dhps:tw:',
            ["relay=", "daemon", "help", "pin",
            "sensor=", "write="])
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
                    relay_on_duration(int(float(sys.argv[2])), int(float(sys.argv[3])), 0)
                    sys.exit(0)
                else:
                    print "--state only accepts ON, OFF, integers > 1"
                    usage()
                    sys.exit(1)
        elif opt in ("-s", "--sensor"):
            read_sensors(0, sys.argv[2])
            sys.exit(0)
        elif opt in ("-w", "--write"):
            global sensor_log_file_tmp
            if sys.argv[3] == '':
                print "[Write Log] No file specified, using default: %s" % (
                    sensor_log_file_tmp)
            else:
                sensor_log_file_tmp = sys.argv[3]
            read_sensors(0, sys.argv[2])
            write_sensor_log(sys.argv[2])
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
    timerSensorLog  = [0] * 5
    
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
    
    # Initial sensor readings
    logging.info("[Daemon] Conducting initial temperature/humidity sensor readings with %s sensors", numSensors)
    for i in range(1, numSensors+1):
        if sensorDevice[i] != 'Other':
            read_sensors(0, i)
    
    timerLogBackup = int(time.time()) + 21600 # 21600 seconds = 6 hours
    
    for i in range(1, numSensors+1):
        timerSensorLog[i] = int(time.time()) + sensorPeriod[i]
    
    for i in range(1, 9):
        timer_time[i] = int(time.time())
    
    threadst = []
    threadsh = []
    
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

    while True: # Main loop of the daemon
        if ClientQue != '0': # Run remote commands issued by mycodo-client.py
            if ClientQue == 'write_sensor_log':
                logging.debug("[Client command] Write Sensor Log")
                read_sensors(0, ClientVar1)
                write_sensor_log(ClientVar1)
                change_sensor_log = 0
            elif ClientQue == 'TerminateServer':
                logging.info("[Daemon] Backing up logs")
                Concatenate_Logs()
                TAlive = [0] * 5
                for t in threadst:
                    t.join()
                HAlive = [0] * 5
                for t in threadsh:
                    t.join()
                server.close()
                logging.info("[Daemon] Exiting Python")
                sys.exit(0)
            elif ClientQue == 'TimerChange':
                timer_time[timerChange] = 0
                if (timerState[timerChange] == 0 and timerRelay[timerChange] != 0):
                    relay_onoff(timerRelay[timerChange], 0)
                    
            ClientQue = '0'

        if Temp_PID_Down:
            logging.info("[Daemon] Shutting Down Temperature PID Thread-%s", Temp_PID_number)
            TAlive[Temp_PID_number] = 0
            while TAlive[Temp_PID_number] != 2:
                time.sleep(0.1)
            if (relayTrigger[int(relayTemp[1])] == 0): gpio_change(int(relayTemp[1]), 1)
            else: gpio_change(int(relayTemp[1]), 0)
            TAlive[Temp_PID_number] = 1
            Temp_PID_Down = 0
        if Temp_PID_Up == 1:
            logging.info("[Daemon] Starting Temperature PID Thread-%s", Temp_PID_number)
            rod = threading.Thread(target = temperature_monitor, 
                args = ('Thread-%d' % Temp_PID_number, Temp_PID_number,))
            rod.start()
            Temp_PID_Up = 0
            
        if Hum_PID_Down:
            logging.info("[Daemon] Shutting Down Humidity PID Thread-%s", Hum_PID_number)
            HAlive[Hum_PID_number] = 0
            while HAlive[Hum_PID_number] != 2:
                time.sleep(0.1)
            if (relayTrigger[int(relayHum[1])] == 0): gpio_change(int(relayHum[1]), 1)
            else: gpio_change(int(relayHum[1]), 1)
            HAlive[Hum_PID_number] = 1
            Hum_PID_Down = 0
        if Hum_PID_Up == 1:
            logging.info("[Daemon] Starting Temperature PID Thread-%s", Hum_PID_number)
            rod = threading.Thread(target = humidity_monitor, 
                args = ('Thread-%d' % Hum_PID_number, Hum_PID_number,))
            rod.start()
            Hum_PID_Up = 0
        
        # Write sensor log
        for i in range(1, numSensors+1):
            if int(time.time()) > timerSensorLog[i] and sensorDevice[i] != 'Other':
                logging.debug("[Timer Expiration] Read sensor %s every %s seconds: Write sensor log", i, sensorPeriod[i])
                read_sensors(0, i)
                write_sensor_log(i)
                timerSensorLog[i] = int(time.time()) + sensorPeriod[i]
        
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
                        args = (timerRelay[i], timerDurationOn[i], 0,))
                    rod.start()
                    timer_time[i] = int(time.time()) + timerDurationOn[i] + timerDurationOff[i]
                

        time.sleep(0.1)

# Temperature modulation by PID control
def temperature_monitor(ThreadName, sensor):
    global TAlive
    timerTemp = 0
    PIDTemp = 0
    logging.info("[PID Temperature-%s] Starting %s", sensor, ThreadName)
    
    if relayTemp[sensor] != 0:
        if relayTrigger[int(relayTemp[sensor])] == 0: gpio_change(int(relayTemp[sensor]), 1)
        else: gpio_change(int(relayTemp[sensor]), 0)
    
    p_temp = Temperature_PID(Temp_P[sensor], Temp_I[sensor], Temp_D[sensor])
    p_temp.setPoint(setTemp[sensor])
    
    while (TAlive[sensor]):
        if TempOR[sensor] == 0 and Temp_PID_Down == 0 and relayTemp[sensor] != 0:
            if int(time.time()) > timerTemp:
                logging.debug("[PID Temperature-%s] Reading temperature...", sensor)
                read_sensors(1, sensor)
                PIDTemp = p_temp.update(float(tempc[sensor]))
                if (tempc[sensor] < setTemp[sensor]):
                    logging.debug("[PID Temperature-%s] Temperature (%.1f°C) < (%.1f°C) setTemp", sensor, tempc[sensor], float(setTemp[sensor]))
                    logging.debug("[PID Temperature-%s] PID = %.1f (seconds)", sensor, PIDTemp)
                    if (PIDTemp > 0 and tempc[sensor] < setTemp[sensor]):
                        rod = threading.Thread(target = relay_on_duration, 
                            args = (relayTemp[sensor], round(PIDTemp,2), sensor,))
                        rod.start()
                    timerTemp = int(time.time()) + int(PIDTemp) + int(TempPeriod[sensor])
                else:
                    logging.debug("[PID Temperature-%s] Temperature (%.1f°C) >= (%.1f°C) setTemp, waiting 60 seconds", sensor, tempc[sensor], setTemp[sensor])
                    logging.debug("[PID Temperature-%s] PID = %.1f (seconds)", sensor, PIDTemp)
                    timerTemp = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID Temperature-%s] Shutting Down %s", sensor, ThreadName)
    TAlive[sensor] = 2

# Humidity modulation by PID control
def humidity_monitor(ThreadName, sensor):
    global HAlive
    timerHum = 0
    PIDHum = 0

    logging.info("[PID Humidity-%s] Starting %s", sensor, ThreadName)

    if relayHum[sensor] != 0:
        if relayTrigger[int(relayHum[sensor])] == 0: gpio_change(int(relayHum[sensor]), 1)
        else: gpio_change(int(relayHum[sensor]), 1)
    
    p_hum = Humidity_PID(Hum_P[sensor], Hum_I[sensor], Hum_D[sensor])
    p_hum.setPoint(setHum[sensor])

    while (HAlive[sensor]):
        if HumOR[sensor] == 0 and Hum_PID_Down == 0 and relayHum[sensor] != 0:
            if int(time.time()) > timerHum:
                logging.debug("[PID Humidity-%s] Reading humidity...", sensor)
                read_sensors(1, sensor)
                PIDHum = p_hum.update(float(humidity))
                if (humidity[sensor] < setHum[sensor]):
                    logging.debug("[PID Humidity-%s] Humidity (%.1f%%) < (%.1f%%) setHum", sensor, humidity[sensor], float(setHum[sensor]))
                    logging.debug("[PID Humidity-%s] PID = %.1f (seconds)", sensor, PIDHum)
                    if (PIDHum > 0 and humidity[sensor] < setHum[sensor]):
                        rod = threading.Thread(target = relay_on_duration,
                            args=(relayHum[sensor], round(PIDHum,2), sensor,))
                        rod.start()
                    timerHum = int(time.time()) + int(PIDHum) + int(HumPeriod[sensor])
                else:
                    logging.debug("[PID Humidity-%s] Humidity (%.1f%%) >= (%.1f%%) setHum, waiting 60 seconds", sensor, humidity[sensor], setHum[sensor])
                    logging.debug("[PID Humidity-%s] PID = %.1f (seconds)", sensor, PIDHum)
                    timerHum = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID Humidity-%s] Shutting Down %s", sensor,  ThreadName)
    HAlive[sensor] = 2

# Append sensor data to the log file
def write_sensor_log(sensor):
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
                sensorlog.write('{0} {1:.1f} {2:.1f} {3:.1f} {4}\n'.format(
                    datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                    tempc[sensor], humidity[sensor], dewpointc[sensor], sensor))
                logging.debug("[Write Sensor Log] Data appended to %s", sensor_log_file_tmp)
        except:
            logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_log_file_tmp)
        logging.debug("[Write Sensor Log] Removing lock: %s", lock.path)
        lock.release()

# Append the duration the relay has been on to the log file
def write_relay_log(relayNumber, relaySeconds, sensor):
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
def read_sensors(silent, sensor):
    global tempc
    global humidity
    global dewpointc
    #global heatindexc
    global chktemp
    chktemp = 1
    
    if (sensorDevice[1] == 'DHT11'): device = Adafruit_DHT.DHT11
    elif (sensorDevice[1] == 'DHT22'): device = Adafruit_DHT.DHT22
    elif (sensorDevice[1] == 'AM2302'): device = Adafruit_DHT.AM2302
    else: device = 'Other'

    if not silent and not Terminate:
        logging.debug("[Read Sensor-%s] Taking first Temperature/humidity reading", sensor)
    if not Terminate:
        humidity2, tempc2 = Adafruit_DHT.read_retry(device, sensorPin[1])
        if humidity2 == None or tempc2 == None:
            logging.warning("[Read Sensor-%s] Could not read temperature/humidity!", sensor)
        if not silent and humidity2 != None and tempc2 != None:
            logging.debug("[Read Sensor-%s] %.1f°C, %.1f%%", sensor, tempc2, humidity2)
    if not Terminate:
        time.sleep(2)
        if not silent: 
            logging.debug("[Read Sensor-%s] Taking second Temperature/humidity reading", sensor)
    while chktemp and not Terminate and humidity2 != None and tempc2 != None:
        if not Terminate:
            humidity[sensor], tempc[sensor] = Adafruit_DHT.read_retry(device, sensorPin[1])
        if humidity[sensor] != 'None' or tempc[sensor] != 'None':
            if not silent and not Terminate: 
                logging.debug("[Read Sensor-%s] %.1f°C, %.1f%%", sensor, tempc[sensor], humidity[sensor])
                logging.debug("[Read Sensor-%s] Differences: %.1f°C, %.1f%%", sensor, abs(tempc2-tempc[sensor]), abs(humidity2-humidity[sensor]))
            if abs(tempc2-tempc[sensor]) > 1 or abs(humidity2-humidity[sensor]) > 1 and not Terminate:
                tempc2 = tempc[sensor]
                humidity2 = humidity[sensor]
                chktemp = 1
                if not silent:
                    logging.debug("[Read Sensor-%s] Successive readings > 1 difference: Rereading", sensor)
                time.sleep(2)
            elif not Terminate:
                chktemp = 0
                if not silent: 
                    logging.debug("[Read Sensor-%s] Successive readings < 1 difference: keeping.", sensor)
                tempf = float(tempc[sensor])*9.0/5.0 + 32.0
                dewpointc[sensor] = tempc[sensor] - ((100-humidity[sensor]) / 5)
                #dewpointf[sensor] = dewpointc[sensor] * 9 / 5 + 32
                #heatindexf =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
                #heatindexc[sensor] = (heatindexf - 32) * (5 / 9)
                if not silent: 
                    logging.debug("[Read Sensor-%s] Temp: %.1f°C, Hum: %.1f%%, DP: %.1f°C", sensor, tempc[sensor], humidity[sensor], dewpointc[sensor])
        else: logging.warning("[Read Sensor-%s] Could not read temperature/humidity!", sensor)

# Read variables from the configuration file
def read_config(silent):
    global config_file
    global sensorName
    global sensorDevice
    global sensorPin
    global sensorPeriod
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
    
    smtp_host = config.get('Notification', 'smtp_host')
    smtp_port = config.get('Notification', 'smtp_port')
    smtp_user = config.get('Notification', 'smtp_user')
    smtp_pass = config.get('Notification', 'smtp_pass')
    email_from = config.get('Notification', 'email_from')
    email_to = config.get('Notification', 'email_to')
    
    numRelays = config.getint('Misc', 'numrelays')
    numSensors = config.getint('Misc', 'numsensors')
    numTimers = config.getint('Misc', 'numtimers')
    cameraLight = config.getint('Misc', 'cameralight')
    
    for i in range(1, 5):
        TempPeriod[i] = config.getint('TempPID%d' % i, 'temp%dperiod' % i)
        relayTemp[i] = config.getint('TempPID%d' % i, 'temp%drelay' % i)
        setTemp[i] = config.getfloat('TempPID%d' % i, 'temp%dset' % i)
        TempOR[i] = config.getint('TempPID%d' % i, 'temp%dor' % i)
        Temp_P[i] = config.getfloat('TempPID%d' % i, 'temp%dp' % i)
        Temp_I[i] = config.getfloat('TempPID%d' % i, 'temp%di' % i)
        Temp_D[i] = config.getfloat('TempPID%d' % i, 'temp%dd' % i)
        
        HumPeriod[i] = config.getint('HumPID%d' % i, 'hum%dperiod' % i)
        relayHum[i] = config.getint('HumPID%d' % i, 'hum%drelay' % i)
        setHum[i] = config.getfloat('HumPID%d' % i, 'hum%dset' % i)
        HumOR[i] = config.getint('HumPID%d' % i, 'hum%dor' % i)
        Hum_P[i] = config.getfloat('HumPID%d' % i, 'hum%dp' % i)
        Hum_I[i] = config.getfloat('HumPID%d' % i, 'hum%di' % i)
        Hum_D[1] = config.getfloat('HumPID%d' % i, 'hum%dd' % i)

    for i in range(1, 5):
        sensorName[i] = config.get('Sensor%d' % i, 'sensor%dname' % i)
        sensorDevice[i] = config.get('Sensor%d' % i, 'sensor%ddevice' % i)
        sensorPin[i] = config.getint('Sensor%d' % i, 'sensor%dpin' % i)
        sensorPeriod[i] = config.getint('Sensor%d' % i, 'sensor%dperiod' % i)
        
        TempPeriod[i] = config.getint('TempPID%d' % i, 'temp%dperiod' % i)
        relayTemp[i] = config.getint('TempPID%d' % i, 'temp%drelay' % i)
        setTemp[i] = config.getfloat('TempPID%d' % i, 'temp%dset' % i)
        TempOR[i] = config.getint('TempPID%d' % i, 'temp%dor' % i)
        Temp_P[i] = config.getfloat('TempPID%d' % i, 'temp%dp' % i)
        Temp_I[i] = config.getfloat('TempPID%d' % i, 'temp%di' % i)
        Temp_D[i] = config.getfloat('TempPID%d' % i, 'temp%dd' % i)
        
        HumPeriod[i] = config.getint('HumPID%d' % i, 'hum%dperiod' % i)
        relayHum[i] = config.getint('HumPID%d' % i, 'hum%drelay' % i)
        setHum[i] = config.getfloat('HumPID%d' % i, 'hum%dset' % i)
        HumOR[i] = config.getint('HumPID%d' % i, 'hum%dor' % i)
        Hum_P[i] = config.getfloat('HumPID%d' % i, 'hum%dp' % i)
        Hum_I[i] = config.getfloat('HumPID%d' % i, 'hum%di' % i)
        Hum_D[i] = config.getfloat('HumPID%d' % i, 'hum%dd' % i)
        
    for i in range(1, 9):
        relayName[i] = config.get('Relay%d' % i, 'relay%dname' % i)
        relayPin[i] = config.getint('Relay%d' % i, 'relay%dpin' % i)
        relayTrigger[i] = config.getint('Relay%d' % i, 'relay%dtrigger' % i)
    
    for i in range(1, 9):
        timerState[i] = config.getint('Timer%d' % i, 'timer%dstate' % i)
        timerRelay[i] = config.getint('Timer%d' % i, 'timer%drelay' % i)
        timerDurationOn[i] = config.getint('Timer%d' % i, 'timer%ddurationon' % i)
        timerDurationOff[i] = config.getint('Timer%d' % i, 'timer%ddurationoff' % i)

    if not silent:
        logging.debug("[Read Config] setTemp: %.1f°C, setHum: %.1f%%, TempOR: %s, HumOR: %s", setTemp[1], setHum[1], TempOR[1], HumOR[1])
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
    
    for i in range(1, 5):
        config.add_section('Sensor%d' % i)
        config.set('Sensor%d' % i, 'sensor%dname' % i, sensorName[i])
        config.set('Sensor%d' % i, 'sensor%ddevice' % i, sensorDevice[i])
        config.set('Sensor%d' % i, 'sensor%dpin' % i, sensorPin[i])
        config.set('Sensor%d' % i, 'sensor%dperiod' % i, sensorPeriod[i])
        
        config.add_section('TempPID%d' % i)
        config.set('TempPID%d' % i, 'temp%dperiod' % i, TempPeriod[i])
        config.set('TempPID%d' % i, 'temp%drelay' % i, relayTemp[i])
        config.set('TempPID%d' % i, 'temp%dset' % i, setTemp[i])
        config.set('TempPID%d' % i, 'temp%dor' % i, TempOR[i])
        config.set('TempPID%d' % i, 'temp%dp' % i, Temp_P[i])
        config.set('TempPID%d' % i, 'temp%di' % i, Temp_I[i])
        config.set('TempPID%d' % i, 'temp%dd' % i, Temp_D[i])
        
        config.add_section('HumPID%d' % i)
        config.set('HumPID%d' % i, 'hum%dperiod' % i, HumPeriod[i])
        config.set('HumPID%d' % i, 'hum%drelay' % i, relayHum[i])
        config.set('HumPID%d' % i, 'hum%dor' % i, HumOR[i])
        config.set('HumPID%d' % i, 'hum%dset' % i, setHum[i])
        config.set('HumPID%d' % i, 'hum%dp' % i, Hum_P[i])
        config.set('HumPID%d' % i, 'hum%di' % i, Hum_I[i])
        config.set('HumPID%d' % i, 'hum%dd' % i, Hum_D[i])
    
    for i in range(1, 9):
        config.add_section('Relay%d' % i)
        config.set('Relay%d' % i, 'relay%dname' % i, relayName[i])
        config.set('Relay%d' % i, 'relay%dpin' % i, relayPin[i])
        config.set('Relay%d' % i, 'relay%dtrigger' % i, relayTrigger[i])
    
    for i in range(1, 9):
        config.add_section('Timer%d' % i)
        config.set('Timer%d' % i, 'timer%dstate' % i, timerState[i])
        config.set('Timer%d' % i, 'timer%drelay' % i, timerRelay[i])
        config.set('Timer%d' % i, 'timer%ddurationon' % i, timerDurationOn[i])
        config.set('Timer%d' % i, 'timer%ddurationoff' % i, timerDurationOff[i])
    
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
def relay_on_duration(relay, seconds, sensor):
    if (relayTrigger[relay] == 0 and GPIO.input(relayPin[relay]) == 0) or (
            relayTrigger[relay] == 1 and GPIO.input(relayPin[relay]) == 1):
        logging.warning("[Relay Duration] Relay %s (%s) is already On. Turning off in %s seconds.", 
            relay, relayName[relay], seconds)
    else:
        logging.debug("[Relay Duration] Relay %s (%s) ON for %s seconds", 
            relay, relayName[relay], round(seconds, 1))
   
    GPIO.output(relayPin[relay], relayTrigger[relay]) # Turn relay on    
    timer_on = int(time.time()) + seconds
    write_relay_log(relay, seconds, sensor)
    
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
    namesOfVariables = [
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
                globals()[names_and_values[i]] = names_and_values[i+1]
                     
    write_config()
    read_config(1)
    
    return 1

# Email if temperature or humidity is outside of critical range
def email():
    if (smtp_ssl):
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        server.ehlo()
    else:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
    server.ehlo
    server.login(smtp_user, smtp_pass)

    message = "Critical warning!"
    
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