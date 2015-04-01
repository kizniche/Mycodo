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
import subprocess
import re
import os
import fcntl
import sys
import time
import datetime
import getopt
import RPi.GPIO as GPIO
import ConfigParser
import threading
import rpyc
from rpyc.utils.server import ThreadedServer
from array import *

config_file = "%s/config/mycodo.cfg" % install_directory
sensor_log_file = "%s/log/sensor.log" % install_directory
relay_log_file = "%s/log/relay.log" % install_directory
relay_script = "%s/cgi-bin/relay.sh" % install_directory

lock_directory = "/var/lock/mycodo/"
config_lock = "config.lock"
sensor_log_lock = "sensorlog.lock"
relay_log_lock = "relaylog.lock"

# GPIO pins (BCM numbering) and name of devices attached to relay
relayPin = [0] * 9
relayName = [0] * 9

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
        print_sync("%s [Client command] Request to change variables" % (
            timestamp()), 1)
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
        ClientArg1 = int(float(remoteCommand))
        ClientArg2 = int(float(remoteCommand2))
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
        print_sync("%s [Client command] Change Relay Names: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s" % (
            timestamp(),
            relayName[1], relayName[2], relayName[3], relayName[4],
            relayName[5], relayName[6], relayName[7], relayName[8]), 1)
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
        print_sync("%s [Client command] Change Relay Pins: 1 %s, 2 %s, 3 %s, 4 %s, 5 %s, 6 %s, 7 %s, 8 %s" % (
            timestamp(),
            relayPin[1], relayPin[2], relayPin[3], relayPin[4],
            relayPin[5], relayPin[6], relayPin[7], relayPin[8]), 1)
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
    print_sync("mycodo.py: Reads temperature and humidity from sensors, "
        "writes log file, and operates relays as a daemon to maintain "
        "set environmental conditions.\n", 1)
    print_sync("Usage:   mycodo.py [OPTION]...\n", 1)
    print_sync("Example: mycodo.py -w /var/www/mycodo/log/sensor.log", 1)
    print_sync("         mycodo.py -c 1 -s 0", 1)
    print_sync("         mycodo.py -n relay1Name --value Banana", 1)
    print_sync("         mycodo.py --daemon\n", 1)
    print_sync("Options:", 1)
    print_sync("    -c, --change=RELAY", 1)
    print_sync("           Change the state of a relay (--state required)", 1)
    print_sync("        --state=[ON/OFF/X]", 1)
    print_sync("           Change the state of RELAY to ON, OFF, or (X) number of seconds on", 1)
    print_sync("    -d, --daemon", 1)
    print_sync("           Start program as daemon that monitors conditions and modulates relays", 1)
    print_sync("    -h, --help", 1)
    print_sync("           Display this help and exit", 1)
    print_sync("    -n, --name=VARIABLE", 1)
    print_sync("           Change the VALUE of a single VARIABLE (--value required)", 1)
    print_sync("        --value=VALUE", 1)
    print_sync("           Change the VALUE of variable NAME (-n required)", 1)
    print_sync("    -p, --pin", 1)
    print_sync("           Display status of the GPIO pins (HIGH or LOW)", 1)
    print_sync("    -r  --read=[SENSOR/CONFIG]", 1)
    print_sync("           Read and display sensor data or config settings", 1)
    print_sync("    -s, --set setTemp setHum TempOR HumOR", 1)
    print_sync("           Change operating parameters (must give all options as int, overrides must be 0 or 1)", 1)
    print_sync("    -w, --write=FILE", 1)
    print_sync("           Write sensor data to log file\n", 1)

# Checks user options and arguments for validity
def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:dhpr:s:tw',
            ["change=", "daemon", "help", "pin",
            "read=", "set=", "state=", "write="])
    except getopt.GetoptError as err:
        print(err) # will print_sync("option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c", "--change"):
            if not represents_int(arg) or \
                    int(float(arg)) > 8 or \
                    int(float(arg)) < 1:
                print_sync("Error: --change only accepts integers 1 though 8", 1)
                sys.exit(1)
            else:
                global relaySelect
                relaySelect = arg
        elif opt == "--state":
            if represents_int(arg) and int(float(arg)) > 1 or \
                    (arg == 'OFF' or arg == 'ON'):
                read_config(0)
                if arg == 'ON':
                    print_sync("%s [GPIO Write] Relay %s ON" % (
                        timestamp(), relaySelect), 1)
                    gpio_change(int(float(relaySelect)), 0)
                    gpio_read()
                    sys.exit(0)
                if arg == 'OFF':
                    print_sync("%s [GPIO Write] Relay %s OFF" % (
                        timestamp(), relaySelect), 1)
                    gpio_change(int(float(relaySelect)), 1)
                    gpio_read()
                    sys.exit(0)
                elif int(float(arg)) > 1:
                    print_sync("%s [GPIO Write] Relay %s ON for %s seconds" % (
                        timestamp(), int(float(arg))), 1)
                    relay_on_duration(int(float(relaySelect)), int(float(arg)))
                    sys.exit(0)
                else:
                    print_sync("--state only accepts ON, OFF, integers > 1", 1)
                    usage()
                    sys.exit(1)
        elif opt in ("-d", "--daemon"):
            daemon()
            sys.exit(0)
        elif opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-p", "--pin"):
            read_config(0)
            gpio_read()
            sys.exit(0)
        elif opt in ("-r", "--read"):
            if arg == 'SENSOR':
                read_sensors(0)
                sys.exit(0)
            elif arg == 'CONFIG':
                read_config(0)
                sys.exit(0)
            else:
                print_sync("Error: Invalid option for --read", 1)
                usage()
                sys.exit(1)
        elif opt in ("-s", "--set"):
            if len(sys.argv) != 6:
                print_sync("Error: Too many/not enough options", 1)
                sys.exit(1)
            elif not represents_float(sys.argv[2]) and \
                    not represents_float(sys.argv[3]) and \
                    not represents_int(sys.argv[4]) and \
                    not represents_int(sys.argv[5]):
                print_sync("Error: --set: temperature and humidity requires one decimal place and overrides need to be either 1 or 0", 1)
                sys.exit(1)
            elif (sys.argv[4] != '0' and sys.argv[4] != '1') or \
                    (sys.argv[5] != '0' and sys.argv[5] != '1'):
                print_sync("Error: Last option of --set must be 0 or 1", 1)
                sys.exit(0)
            print_sync("%s [Set Conditions] Desired values: "
                    "setTemp: %s, setHum: %s, TempOR: %s, HumOR: %s" 
                    % (timestamp(),
                    sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]), 1)
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
            print_sync("%s [Set Conditions] New Values: "
                "setTemp: %.1f°C, setHum: %.1f%%, TempOR: %s, HumOR: %s" 
                % (timestamp(), setTemp, setHum, TempOR, HumOR), 1)
            sys.exit(0)
        elif opt in ("-w", "--write"):
            global sensor_log_file
            if arg == '':
                print_sync("%s [Write Log] No file specified, using default: %s" 
                    % (timestamp(), sensor_log_file), 1)
            else:
                sensor_log_file = arg
            read_sensors(0)
            write_sensor_log()
            sys.exit(0)
        else:
            assert False, "Fail"

# Main loop that reads sensors, modifies relays based on sensor values, writes
# sensor/relay logs, and receives/executes commands from mycodo-client.py
def daemon():
    global Temp_PID_restart
    global Hum_PID_restart
    global server
    global HAlive
    global TAlive
    global ClientQue
    
    print_sync("%s [Daemon] Daemon Started" % timestamp(), 1)
    print_sync("%s [Comm Server] Starting Thread"
        % timestamp(), 1)
    ct = ComThread()
    ct.daemon = True
    ct.start()

    print_sync("%s [Daemon] Initial configuration read to set variables"
        % timestamp(), 1)
    read_config(1)
    
    if DHTSensor != 'Other':
        read_sensors(0)
    
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
                print_sync("%s [Client command] Write Sensor Log" % (
                    timestamp()), 1)
                read_sensors(0)
                write_sensor_log()
            elif ClientQue == 'gpio_change':
                print_sync("%s [Client command] Set Relay %s GPIO to %s" % (
                    timestamp(), ClientArg1, ClientArg1), 1)
                gpio_change(ClientArg1, ClientArg2)
                gpio_read()
            elif ClientQue == 'RelayOnSec':
                print_sync("%s [Client command] Set Relay %s on for %s seconds"
                    % (timestamp(), ClientArg1, ClientArg2), 1)
                relay_on_duration(ClientArg1, ClientArg2)
            elif ClientQue == 'TerminateServer':
                print_sync("%s [Client command] Terminate threads and shut down"
                    % timestamp(), 1)
                TAlive = 0
                while TAlive != 2:
                    time.sleep(0.1)
                HAlive = 0
                while HAlive != 2:
                    time.sleep(0.1)
                server.close()
                print_sync("%s [Daemon] Exiting Python" % timestamp(), 1)
                sys.exit(0)

            if Temp_PID_restart == 1:
                if tm.isAlive():
                    print_sync("%s [Daemon] Restarting Temperature PID thread" 
                        % timestamp(), 1)
                    TAlive = 0
                    while TAlive != 2:
                        time.sleep(0.1)
                    TAlive = 1
                tm = threading.Thread(target = temperature_monitor)  
                tm.daemon = True
                tm.start()
                Temp_PID_restart = 0
            
            if Hum_PID_restart:
                if hm.isAlive():
                    print_sync("%s [Daemon] Restarting Humidity PID thread" 
                        % timestamp(), 1)
                    HAlive = 0
                    while HAlive != 2:
                        time.sleep(0.1)
                    HAlive = 1
                hm = threading.Thread(target = humidity_monitor)
                hm.daemon = True
                hm.start()
                Hum_PID_restart = 0
                
            ClientQue = '0'
        
        # Write sensor log
        if int(time.time()) > timerSensorLog and DHTSensor != 'Other':
            print_sync("%s [Timer Expiration] Run every %s seconds: Write sensor log" 
                % (timestamp(), DHTSeconds), 1)
            read_sensors(0)
            write_sensor_log()
            timerSensorLog = int(time.time()) + DHTSeconds

        time.sleep(1)

# Temperature modulation by PID control
def temperature_monitor():
    global tempState
    global TAlive
    timerTemp = 0
    PIDTemp = 0
    print_sync("%s [PID Temperature] Starting Thread"
                    % timestamp(), 1)
    if (tempc < setTemp):
        tempState = 0
    else: 
        tempState = 1
        gpio_change(relayTemp, 1)
    p_temp = Temperature_PID(Temp_P, Temp_I, Temp_D)
    p_temp.setPoint(setTemp)
    
    while TAlive == 1:
        if TempOR == 0 and Temp_PID_restart == 0:
            if int(time.time()) > timerTemp:
                print_sync("%s [PID Temperature] Reading temperature..."
                    % timestamp(), 1)
                read_sensors(1)
                if (tempc >= setTemp): tempState = 1
                if (tempc < setTemp): tempState = 0
                if (tempState == 0):
                    PIDTemp = round(p_temp.update(float(tempc)), 1)
                    print_sync("%s [PID Temperature] Temperature (%.1f°C) < setTemp (%.1f°C)" 
                        % (timestamp(), tempc, setTemp), 1)
                    print_sync("%s [PID Temperature] PID = %.1f (seconds)" 
                        % (timestamp(), PIDTemp), 1)
                    if (PIDTemp > 0 and tempc < setTemp):
                        rod = threading.Thread(target = relay_on_duration, 
                            args = (relayTemp, PIDTemp,))
                        rod.start()
                    timerTemp = int(time.time()) + PIDTemp + factorTempSeconds
                else:
                    print_sync("%s [PID Temperature] Temperature (%.1f°C) > setTemp (%.1f°C), waiting 60 seconds" 
                        % (timestamp(), tempc, setTemp), 1)
                    p_temp.update(float(tempc))
                    timerTemp = int(time.time()) + 60
    print_sync("%s [PID Temperature] Shutting Down Thread" % timestamp(), 1)
    TAlive = 2

# Humidity modulation by PID control
def humidity_monitor():
    global humState
    global HAlive
    timerHum = 0
    PIDHum = 0

    print_sync("%s [PID Humidity] Starting Thread" 
        % timestamp(), 1)
    if (humidity < setHum):
        humState = 0
    else:
        humState = 1
        gpio_change(relayHum, 1)
    p_hum = Humidity_PID(Hum_P, Hum_I, Hum_D)
    p_hum.setPoint(setHum)

    while HAlive == 1:
        if HumOR == 0 and Hum_PID_restart == 0:
            if int(time.time()) > timerHum:
                print_sync("%s [PID Humidity] Reading humidity..." 
                    % timestamp(), 1)
                read_sensors(1)
                if (humidity >= setHum): humState = 1
                if (humidity < setHum): humState = 0
                if (humState == 0):
                    PIDHum = round(p_hum.update(float(humidity)), 1)
                    print_sync("%s [PID Humidity] Humidity (%.1f%%) < setHum (%.1f%%)" 
                        % (timestamp(), humidity, setHum), 1)
                    print_sync("%s [PID Humidity] PID = %.1f (seconds)" 
                        % (timestamp(), PIDHum), 1)
                    if (PIDHum > 0 and humidity < setHum):
                        rod = threading.Thread(
                            target = relay_on_duration, args=(relayHum, PIDHum,))
                        rod.start()
                    timerHum = int(time.time()) + PIDHum + factorTempSeconds
                else:
                    print_sync("%s [PID Humidity] Humidity (%.1f%%) > setHum (%.1f%%), waiting 60 seconds" 
                        % (timestamp(), humidity, setHum), 1)
                    p_hum.update(float(humidity))
                    timerHum = int(time.time()) + 60
    print_sync("%s [PID Humidity] Shutting Down Thread" % timestamp(), 1)
    HAlive = 2

# Append sensor data to the log file
def write_sensor_log():
    sensor_lock_path = lock_directory + sensor_log_lock
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    waitingForLock = 1
    errorOnce = 1
    lockWaitCount = 1
    while waitingForLock and not Terminate:
        if not lock_file(sensor_lock_path) and not Terminate:
            if errorOnce:
                print_sync("%s [Write Sensor Log] Cannot gain lock (already locked): Waiting to gain lock..." 
                    % timestamp(), 1)
                errorOnce = 0
            if lockWaitCount == 60:
                print_sync("%s [Write Sensor Log] 60 seconds waiting to gain lock (too long): Breaking lock."
                    % timestamp(), 1)
                os.remove(sensor_lock_path)
                lockWaitCount+=1
            if lockWaitCount % 10 == 0:
                print_sync("%s [Write Sensor Log] Waiting to gain lock for %s seconds..." 
                    % (timestamp(), lockWaitCount), 1)
            time.sleep(1)
            lockWaitCount+=1
        elif not Terminate:
            waitingForLock = 0
            print_sync("%s [Write Sensor Log] Gained lock: %s" 
                % (timestamp(), sensor_lock_path), 1)
            try:
                with open(sensor_log_file, "ab") as sensorlog:
                    relaylog.write('{0} {1:.1f} {2:.1f} {3:.1f}\n'.format(
                        datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                        tempc, humidity, dewpointc))
                    print_sync("%s [Write Sensor Log] Data appended to %s" 
                        % (timestamp(), sensor_log_file), 1)
            except:
                print_sync("%s [Write Sensor Log] Unable to append data to %s" 
                    % (timestamp(), sensor_log_file), 1)
                
    if os.path.isfile(sensor_lock_path):
        print_sync("%s [Write Sensor Log] Removing lock: %s" 
            % (timestamp(), sensor_lock_path), 1)
        os.remove(sensor_lock_path)
    else:
        print_sync("%s [Write Sensor Log] Unable to remove lock file %s: It doesn't exist!" 
            % (timestamp(), sensor_lock_path), 1)

# Append the duration the relay has been on to the log file
def write_relay_log(relayNumber, relaySeconds):
    relay_lock_path = lock_directory + relay_log_lock
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    waitingForLock = 1
    errorOnce = 1
    lockWaitCount = 1
    while waitingForLock and not Terminate:
        if not lock_file(relay_lock_path) and not Terminate:
            if errorOnce:
                print_sync("%s [Write Relay Log] Cannot gain lock: Already locked: Waiting to gain lock..." 
                    % timestamp(), 1)
                errorOnce = 0
            if lockWaitCount == 60:
                print_sync("%s [Write Relay Log] 60 sec waiting to gain lock (too long): Breaking lock." 
                    % timestamp(), 1)
                os.remove(relay_lock_path)
                lockWaitCount+=1
            if lockWaitCount % 10 == 0:
                print_sync("%s [Write Relay Log] Waiting to gain lock for %s seconds..." 
                    % (timestamp(), lockWaitCount), 1)
            time.sleep(1)
            lockWaitCount+=1
        elif not Terminate:
            waitingForLock = 0
            print_sync("%s [Write Relay Log] Gained lock: %s" 
                % (timestamp(), relay_lock_path), 1)
            relay = [0] * 9
            for n in range(1, 9):
                if n == relayNumber:
                    relay[relayNumber] = relaySeconds
            try:
                with open(relay_log_file, "ab") as relaylog:
                    relaylog.write('{0} {1} {2} {3} {4} {5} {6} {7} {8}\n'.format(
                        datetime.datetime.now().strftime("%Y %m %d %H %M %S"), 
                        relay[1], relay[2], relay[3], relay[4],
                        relay[5], relay[6], relay[7], relay[8]))
            except:
                print_sync("%s [Write Relay Log] Unable to append data to %s" 
                    % (timestamp(), relay_log_file), 1)
                
    if os.path.isfile(relay_lock_path):
        print_sync("%s [Write Relay Log] Removing lock file %s" 
            % (timestamp(), relay_lock_path), 1)
        os.remove(relay_lock_path)
    else:
        print_sync("%s [Write Relay Log] Unable to remove lock file %s: It doesn't exist!" 
            % (timestamp(), relay_lock_path), 1)

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
        print_sync("%s [Read Sensors] Taking first Temperature/humidity reading" 
            % timestamp(), 1)
    if not Terminate:
        humidity2, tempc2 = Adafruit_DHT.read_retry(sensor, DHTPin)
        if not silent:
            print_sync("%s [Read Sensors] %.1f°C, %.1f%%" 
                % (timestamp(), tempc2, humidity2), 1)
    if not Terminate:
        time.sleep(2);
        if not silent: 
            print_sync("%s [Read Sensors] Taking second Temperature/humidity reading" 
                % timestamp(), 1)

    while chktemp and not Terminate:
        if not Terminate:
            humidity, tempc = Adafruit_DHT.read_retry(sensor, DHTPin)
        if not silent and not Terminate: 
            print_sync("%s [Read Sensors] %.1f°C, %.1f%%" 
                % (timestamp(), tempc, humidity), 1)
            print_sync("%s [Read Sensors] Differences: %.1f°C, %.1f%%" 
                % (timestamp(), abs(tempc2-tempc), abs(humidity2-humidity)), 1)
        if abs(tempc2-tempc) > 1 or abs(humidity2-humidity) > 1 and not Terminate:
            tempc2 = tempc
            humidity2 = humidity
            chktemp = 1
            if not silent:
                print_sync("%s [Read Sensors] Successive readings > 1 difference: Rereading" 
                    % timestamp(), 1)
            time.sleep(2)
        elif not Terminate:
            chktemp = 0
            if not silent: 
                print_sync("%s [Read Sensors] Successive readings < 1 difference: keeping." 
                    % timestamp(), 1)
            tempf = float(tempc)*9.0/5.0 + 32.0
            dewpointc = tempc - ((100-humidity) / 5)
            #dewpointf = dewpointc * 9 / 5 + 32
            #heatindexf =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
            #heatindexc = (heatindexf - 32) * (5 / 9)
            if not silent: 
                print_sync("%s [Read Sensors] Temp: %.2f°C, Hum: %.2f%%, DP: %.2f°C" 
                    % (timestamp(), tempc, humidity, dewpointc), 1)

# Read variables from the configuration file
def read_config(silent):
    global config_file
    global DHTSensor
    global DHTPin
    global DHTSeconds
    global relayName
    global relayPin
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

    if not silent:
        print_sync("%s [Read Config] setTemp: %.1f°C, setHum: %.1f%%, TempOR: %s, HumOR: %s" 
            % (timestamp(), setTemp, setHum, TempOR, HumOR), 1)
        print_sync("%s [Read Config] RelayNum[Name][Pin]:" % timestamp(), 0)
        for x in range(1,9):
            if x == 5:
                print_sync("\n%s [Read Config] RelayNum[Name][Pin]:" 
                    % timestamp(), 0)
            if relayPin[x] < 10:
                print_sync("%s[%s][%s ]" % (x, relayName[x], relayPin[x]), 0)
            else:
                print_sync("%s[%s][%s]" % (x, relayName[x], relayPin[x]), 0)
        print_sync("\n%s [Read Config] %s %s %s %s %s %s %s %s %s %s %s" 
            % (timestamp(), tempState, humState, 
            relay1o, relay2o, relay3o, relay4o, 
            relay5o, relay6o, relay7o, relay8o, 
            DHTSeconds), 1)

# Write variables to configuration file
def write_config():
    config_lock_path = lock_directory + config_lock
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    waitingForLock = 1
    errorOnce = 1
    lockWaitCount = 1
    while waitingForLock:
        if not lock_file(config_lock_path):
            if errorOnce:
                print_sync("%s [Write Config] Cannot gain lock: Already locked: Waiting to gain lock..."
                    % timestamp(), 1)
                errorOnce = 0
            if lockWaitCount == 60:
                print_sync("%s [Write Config] 60 sec waiting to gain lock: Breaking lock." 
                    % timestamp(), 1)
                os.remove(config_lock_path)
                lockWaitCount+=1
            if lockWaitCount % 10 == 0:
                print_sync("%s [Write Config] Waiting to gain lock for %s seconds..." 
                    % (timestamp(), lockWaitCount), 1)
            time.sleep(1)
            lockWaitCount+=1
        else:
            waitingForLock = 0
            print_sync("%s [Write Config] Gained lock: %s" 
                % (timestamp(), config_lock_path), 1)
            print_sync("%s [Write Config] Writing config file %s" 
                % (timestamp(), config_file), 1)
            
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
            
            with open(config_file, 'wb') as configfile:
                config.write(configfile)

    if os.path.isfile(config_lock_path):
        print_sync("%s [Write Config] Removing lock file %s" 
            % (timestamp(), config_lock_path), 1)
        os.remove(config_lock_path)
    else:
        print_sync("%s [Write Config] Unable to remove lock file %s: It doesn't exist!" 
            % (timestamp(), config_lock_path), 1)

# Initialize GPIO
def gpio_initialize():
    print_sync("%s [GPIO Initialize] Set GPIO mode to BCM numbering, all as output" 
        % timestamp(), 1)
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
    print_sync("%s [GPIO Read]" % timestamp(), 0)
    for x in range(1, 9):
        print_sync("Relay %s:" % x, 0)
        if GPIO.input(relayPin[x]): print_sync("OFF,", 0)
        else: print_sync("ON, ", 0)
        if x == 4: print_sync("\n%s [GPIO Read]" % timestamp(), 0)
        if x == 8: print_sync("", 1)

# Change GPIO (Select) to a specific state (State)
def gpio_change(Select, State):
    print_sync("%s [GPIO Write] Setting relay %s (%s) to %s (was %s)" 
        % (timestamp(), Select, relayName[Select], 
        State, GPIO.input(relayPin[Select])), 1)
    GPIO.output(relayPin[Select], State)

# Set GPIO LOW (= relay ON) for a specific duration
def relay_on_duration(relay, seconds):
    if GPIO.input(relayPin[relay]) == 1:
        write_relay_log(relay, seconds)
        print_sync("%s [Relay Duration] Relay %s (%s) ON for %s seconds" 
            % (timestamp(), relay, relayName[relay], seconds), 1)
        GPIO.output(relayPin[relay], 0)
        time.sleep(seconds)
        GPIO.output(relayPin[relay], 1)
        print_sync("%s [Relay Duration] Relay %s (%s) OFF (was ON for %s sec)"
            % (timestamp(), relay, relayName[relay], seconds), 1)
        return 1
    else:
        print_sync("%s [Relay Duration] Abort: Requested relay %s (%s) ON for %s seconds, but it's already on!" 
            % (timestamp(), relay, relayName[relay], seconds), 1)
        return 0

# all terminal/log output is piped through to ensure prints are synchronized
def print_sync(msg, newline):
    thread_name = threading.current_thread().name
    if newline: line = '%s\n' % msg
    else: line = '%s' % msg
    print >>sys.stderr, line, # Trailing , indicates no implicit end-of-line

# Lock file to prevent other instances from writing while file is open
def lock_file(lockfile):
    fd = os.open(lockfile, os.O_CREAT | os.O_TRUNC | os.O_WRONLY)
    try: # Request exclusive (EX) non-blocking (NB) advisory lock.
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True

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