#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo.py - A temperature and humidity regulation system that allows
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
import subprocess
import sys
import threading
import time
from array import *
from email.mime.text import MIMEText
from lockfile import LockFile
from rpyc.utils.server import ThreadedServer

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
config_lock_path = "%s/config" % lock_directory
daemon_lock_path = "%s/daemon" % lock_directory
sensor_ht_lock_path = "%s/sensor-ht" % lock_directory
sensor_co2_lock_path = "%s/sensor-co2" % lock_directory
relay_lock_path = "%s/relay" % lock_directory
logs_lock_path = "%s/logs" % lock_directory

# GPIO pins (BCM numbering) and name of devices attached to relay
numRelays = None
relayPin = [0] * 9
relayName = [0] * 9
relayTrigger = [0] * 9

# Temperature & Humidity Sensors
numHTSensors = 0
sensorHTName = [0] * 5
sensorHTDevice = [0] * 5
sensorHTPin = [0] * 5
sensorHTPeriod = [0] * 5
sensorHTActivated = [0] * 5
sensorHTGraph = [0] * 5
chktemp = None
tempc = [0] * 5
humidity = [0] * 5
dewpointc = [0] * 5
heatindexc =  [0] * 5

# Temperature PID
relayTemp = [0] * 5
setTemp = [0] * 5
TempPeriod = [0] * 5
Temp_P = [0] * 5
Temp_I = [0] * 5
Temp_D = [0] * 5
TempOR = [0] * 5
TAlive = [1] * 5
Temp_PID_Down = 0
Temp_PID_Up = 0
Temp_PID_number = None

# Humidity PID
relayHum = [0] * 5
setHum = [0] * 5
HumPeriod = [0] * 5
Hum_P = [0] * 5
Hum_I = [0] * 5
Hum_D = [0] * 5
HumOR = [0] * 5
HAlive = [1] * 5
Hum_PID_Down = 0
Hum_PID_Up = 0
Hum_PID_number = None

# CO2 Sensors
numCo2Sensors = 0
sensorCo2Name = [0] * 5
sensorCo2Device = [0] * 5
sensorCo2Pin = [0] * 5
sensorCo2Period = [0] * 5
sensorCo2Activated = [0] * 5
sensorCo2Graph = [0] * 5
co2 = [0] * 5

# CO2 PID
relayCo2 = [0] * 5
setCo2 = [0] * 5
Co2Period = [0] * 5
Co2_P = [0] * 5
Co2_I = [0] * 5
Co2_D = [0] * 5
Co2OR = [0] * 5
CAlive = [1] * 5
Co2_PID_Down = 0
Co2_PID_Up = 0
Co2_PID_number = None

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

# Miscellaneous
cameraLight = None
server = None
variableName = None
variableValue = None
ClientQue = '0'
ClientVar1 = None
Terminate = False
#Terminate_final = 1

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
    def exposed_ChangeCO2Sensor(self, sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph):
        global sensorCo2Name
        global sensorCo2Device
        global sensorCo2Pin
        global sensorCo2Period
        global sensorCo2Activated
        global sensorCo2Graph
        logging.info("[Client command] Change CO2 sensor %s: %s: Device: %s Pin: %s Period: %s sec. Activated: %s Graph: %s",
            sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph)
        sensorCo2Name[sensornumber] = sensorname
        sensorCo2Device[sensornumber] = sensordevice
        sensorCo2Pin[sensornumber] = sensorpin
        sensorCo2Period[sensornumber] = sensorperiod
        sensorCo2Activated[sensornumber] = sensoractivated
        sensorCo2Graph[sensornumber] = sensorgraph
        write_config()
        return 1
    def exposed_ChangeHTSensor(self, sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph):
        global sensorHTName
        global sensorHTDevice
        global sensorHTPin
        global sensorHTPeriod
        global sensorHTActivated
        global sensorHTGraph
        logging.info("[Client command] Change HT sensor %s: %s: Device: %s Pin: %s Period: %s sec. Activated: %s Graph: %s",
            sensornumber, sensorname, sensordevice, sensorpin, sensorperiod, sensoractivated, sensorgraph)
        sensorHTName[sensornumber] = sensorname
        sensorHTDevice[sensornumber] = sensordevice
        sensorHTPin[sensornumber] = sensorpin
        sensorHTPeriod[sensornumber] = sensorperiod
        sensorHTActivated[sensornumber] = sensoractivated
        sensorHTGraph[sensornumber] = sensorgraph
        write_config()
        return 1
    def exposed_ChangeCO2OR(self, sensornum, override):
        global Co2OR
        global Co2_PID_number
        global Co2_PID_Down
        global Co2_PID_Up
        logging.info("[Client command] Change CO2OR for sensor %s to %s",
            sensornum, override)
        Co2OR[sensornum] = override
        Co2_PID_number = sensornum
        Co2Res = 1
        Co2_PID_Down = 1
        while Co2_PID_Down == 1:
            time.sleep(0.1)
        write_config()
        read_config(1)
        if Co2Res:
            Co2_PID_Up = 1
            while Co2_PID_Up:
                time.sleep(0.1)
        return 1
    def exposed_ChangeCO2PID(self, sensornum, relay, set, p, i, d, period):
        global relayCo2
        global setCo2
        global Co2Period
        global Co2_P
        global Co2_I
        global Co2_D
        global Co2OR
        global Co2_PID_number
        global Co2_PID_Down
        global Co2_PID_Up
        logging.info("[Client command] Change Co2 PID for sensor %s: Relay: %s Set: %s P: %s I: %s D: %s Period: %s",
            sensornum, relay, set, p , i, d, period)
        relayCo2[sensornum] = relay
        setCo2[sensornum] = set
        Co2Period[sensornum] = period
        Co2_P[sensornum] = p
        Co2_I[sensornum] = i
        Co2_D[sensornum] = d

        Co2_PID_number = sensornum
        Co2Res = 1
        Co2_PID_Down = 1
        while Co2_PID_Down == 1:
            time.sleep(0.1)
        write_config()
        read_config(1)
        if Co2Res:
            Co2_PID_Up = 1
            while Co2_PID_Up:
                time.sleep(0.1)
        return 1
    def exposed_ChangeTempOR(self, sensornum, override):
        global TempOR
        global Temp_PID_number
        global Temp_PID_Down
        global Temp_PID_Up
        logging.info("[Client command] Change TempOR for sensor %s to %s",
            sensornum, override)
        TempOR[sensornum] = override
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
            return (co2)
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
        global ClientQue
        global Terminate
        #global Terminate_final
        Terminate = True
        ClientQue = 'TerminateServer'
        logging.info("[Client command] Terminate threads and shut down")
        #while Terminate_final: # Wait for program to actually terminate
        #    time.sleep(0.1)
        return 1
    def exposed_WriteHTSensorLog(self, sensor):
        global ClientQue
        global ClientVar1
        ClientVar1 = sensor
        ClientQue = 'write_ht_sensor_log'
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
        global ClientQue
        global ClientVar1
        ClientVar1 = sensor
        ClientQue = 'write_co2_sensor_log'
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
    print "mycodo.py: Reads sensors, writes logs, and operates relays to" \
        " maintain set environmental conditions.\n"
    print "Usage:  mycodo.py [OPTION]...\n"
    print "Options:"
    print "    -d, --daemon v/s w/i/d"
    print "           Start program as daemon that monitors conditions and modulates relays"
    print "           ""v"" enables log output to the console, ""s"" silences"
    print "           Log level: ""w"": >= warnings, ""i"": >= info, ""d"": >= debug"
    print "    -h, --help"
    print "           Display this help and exit\n"
    print "Default: mycodo.py -d s w"
    print "Debugging: mycodo.py -d v d\n"

# Checks user options and arguments for validity
def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        return 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dh',
            ["daemon", "help"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        return 2

    for opt, arg in opts:
        if opt in ("-d", "--daemon"):
            if (sys.argv[2] == 'v'): a = 'verbose'
            else: a = 'silent'
            if (sys.argv[3] == 'w'): b = 'warning'
            elif (sys.argv[3] == 'i'): b = 'info'
            else: b = 'debug'
            daemon(a, b)
            return 0
        elif opt in ("-h", "--help"):
            usage()
            return 1
        else:
            assert False, "Fail"

# Main loop that reads sensors, modifies relays based on sensor values, writes
# sensor/relay logs, and receives/executes certain commands via mycodo-client.py
def daemon(output, log):
    global TAlive
    global Temp_PID_Down
    global Temp_PID_Up
    global HAlive
    global Hum_PID_Down
    global Hum_PID_Up
    global CAlive
    global Co2_PID_Down
    global Co2_PID_Up
    global change_sensor_log
    global server
    global ClientQue
    #global Terminate_final
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
    
    logging.info("[Daemon] Reading configuration file and initializing variables")
    read_config(1)
    
    # Initial sensor readings
    logging.info("[Daemon] Conducting initial sensor readings from %s HT and %s CO2 sensors", sum(sensorHTActivated), sum(sensorCo2Activated))
    for i in range(1, numHTSensors+1):
        if sensorHTDevice[i] != 'Other' and sensorHTActivated[i] == 1:
            read_dht_sensor(0, i)
            time.sleep(2) # Ensure a minimum of 2 seconds between sensor reads
    
    for i in range(1, numCo2Sensors+1):
        if sensorCo2Device[i] != 'Other' and sensorCo2Activated[i] == 1:
            read_co2_sensor(i)
            time.sleep(2) # Ensure a minimum of 2 seconds between sensor reads
    
    timerLogBackup = int(time.time()) + 21600 # 21600 seconds = 6 hours
    
    for i in range(1, numHTSensors+1):
        timerHTSensorLog[i] = int(time.time()) + sensorHTPeriod[i]
        
    for i in range(1, numCo2Sensors+1):
        timerCo2SensorLog[i] = int(time.time()) + sensorCo2Period[i]
    
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
        if ClientQue != '0': # Run remote commands issued by mycodo-client.py
            if ClientQue == 'write_co2_sensor_log':
                logging.debug("[Client command] Write CO2 Sensor Log")
                if (ClientVar1 != 0):
                    read_co2_sensor(0, ClientVar1)
                    write_co2_sensor_log(ClientVar1)
                else:
                    for i in range(1, int(numCo2Sensors)+1): 
                        read_co2_sensor(0, i)
                        write_co2_sensor_log(i)
                        time.sleep(2)
                change_sensor_log = 0
            elif ClientQue == 'write_ht_sensor_log':
                logging.debug("[Client command] Write HT Sensor Log")
                if (ClientVar1 != 0):
                    read_dht_sensor(0, ClientVar1)
                    write_dht_sensor_log(ClientVar1)
                else:
                    for i in range(1, int(numHTSensors)+1): 
                        read_dht_sensor(0, i)
                        write_dht_sensor_log(i)
                        time.sleep(2)
                change_sensor_log = 0
            elif ClientQue == 'TerminateServer':
                logging.info("[Daemon] Turning off relays")
                Relays_Off()
                logging.info("[Daemon] Backing up logs")
                Concatenate_Logs()
                TAlive = [0] * 5
                for t in threadst:
                    t.join()
                HAlive = [0] * 5
                for t in threadsh:
                    t.join()
                CAlive = [0] * 5
                for t in threadsc:
                    t.join()
                #Terminate_final = 0
                #time.sleep(0.5)
                server.close()
                logging.info("[Daemon] Exiting Python")
                return 0
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
            
        if Co2_PID_Down:
            logging.info("[Daemon] Shutting Down CO2 PID Thread-%s", Co2_PID_number)
            CAlive[Co2_PID_number] = 0
            while CAlive[Co2_PID_number] != 2:
                time.sleep(0.1)
            if (relayTrigger[int(relayCo2[1])] == 0): gpio_change(int(relayCo2[1]), 1)
            else: gpio_change(int(relayCo2[1]), 0)
            CAlive[Co2_PID_number] = 1
            Co2_PID_Down = 0
        if Co2_PID_Up == 1:
            logging.info("[Daemon] Starting CO2 PID Thread-%s", Co2_PID_number)
            rod = threading.Thread(target = co2_monitor, 
                args = ('Thread-%d' % Co2_PID_number, Co2_PID_number,))
            rod.start()
            Co2_PID_Up = 0

        # Write temperature and humidity to sensor log
        for i in range(1, int(numHTSensors)+1):
            if int(time.time()) > timerHTSensorLog[i] and sensorHTDevice[i] != 'Other' and sensorHTActivated[i] == 1:
                logging.debug("[Timer Expiration] Read sensor %s every %s seconds: Write sensor log", i, sensorHTPeriod[i])
                read_dht_sensor(0, i)
                write_dht_sensor_log(i)
                timerHTSensorLog[i] = int(time.time()) + sensorHTPeriod[i]

        # Write CO2 to sensor log
        for i in range(1, int(numCo2Sensors)+1):
            if int(time.time()) > timerCo2SensorLog[i] and sensorCo2Device[i] != 'Other' and sensorCo2Activated[i] == 1:
                read_co2_sensor(i)
                write_co2_sensor_log(i)
                timerCo2SensorLog[i] = int(time.time()) + sensorCo2Period[i]
        
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
        if TempOR[sensor] == 0 and Temp_PID_Down == 0 and relayTemp[sensor] != 0 and sensorHTActivated[sensor] == 1:
            if int(time.time()) > timerTemp:
                logging.debug("[PID Temperature-%s] Reading temperature...", sensor)
                read_dht_sensor(1, sensor)
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
        if HumOR[sensor] == 0 and Hum_PID_Down == 0 and relayHum[sensor] != 0 and sensorHTActivated[sensor] == 1:
            if int(time.time()) > timerHum:
                logging.debug("[PID Humidity-%s] Reading humidity...", sensor)
                read_dht_sensor(1, sensor)
                PIDHum = p_hum.update(float(humidity[sensor]))
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

# CO2 modulation by PID control
def co2_monitor(ThreadName, sensor):
    global CAlive
    timerCo2 = 0
    PIDCo2 = 0

    logging.info("[PID CO2-%s] Starting %s", sensor, ThreadName)

    if relayCo2[sensor] != 0:
        if relayTrigger[int(relayCo2[sensor])] == 0: gpio_change(int(relayCo2[sensor]), 1)
        else: gpio_change(int(relayCo2[sensor]), 1)
    
    p_co2 = CO2_PID(Co2_P[sensor], Co2_I[sensor], Co2_D[sensor])
    p_co2.setPoint(setCo2[sensor])

    while (CAlive[sensor]):
        if Co2OR[sensor] == 0 and Co2_PID_Down == 0 and relayCo2[sensor] != 0 and sensorCo2Activated[sensor] == 1:
            if int(time.time()) > timerCo2:
                logging.debug("[PID CO2-%s] Reading CO2...", sensor)
                read_co2_sensor(1, sensor)
                PIDCo2 = p_co2.update(float(co2[sensor]))
                if (co2[sensor] > setCo2[sensor]):
                    logging.debug("[PID CO2-%s] CO2 (%.1f%%) > (%.1f%%) setCO2", sensor, co2[sensor], setCo2[sensor])
                    logging.debug("[PID CO2-%s] PID = %.1f (seconds)", sensor, PIDCo2)
                    if (PIDCo2 > 0 and co2[sensor] > setCo2[sensor]):
                        rod = threading.Thread(target = relay_on_duration,
                            args=(relayCo2[sensor], round(PIDCo2,2), sensor,))
                        rod.start()
                    timerCo2 = int(time.time()) + int(PIDCo2) + int(Co2Period[sensor])
                else:
                    logging.debug("[PID CO2-%s] CO2 (%.1f%%) <= (%.1f%%) setCo2, waiting 60 seconds", sensor, co2[sensor], setCo2[sensor])
                    logging.debug("[PID CO2-%s] PID = %.1f (seconds)", sensor, PIDCo2)
                    timerCo2 = int(time.time()) + 60
        time.sleep(0.1)
    logging.info("[PID CO2-%s] Shutting Down %s", sensor,  ThreadName)
    CAlive[sensor] = 2

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
    date_now_disp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") 
    date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
    date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y/%m/%d %H:%M:%S") 

    # Combine sensor and relay logs on SD card with sensor and relay logs in /tmp
    sensor_ht_log_files_combine = [sensor_ht_log_file, sensor_ht_log_file_tmp]
    sensor_log_generate = "%s/sensor-logs-combined.log" % tmp_path
    relay_log_files_combine = [relay_log_file, relay_log_file_tmp]
    relay_log_generate = "%s/relay-logs-combined.log" % tmp_path
    with open(sensor_log_generate, 'w') as fout:
        for line in fileinput.input(sensor_ht_log_files_combine):
            fout.write(line)
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
    y2_min = '0'
    y2_max = '35'
    
    # Line colors (see comments further down with their use)
    graph_colors = ['#FF3100', '#0772A1', '#00B74A', '#91180B',
                    '#582557', '#04834C', '#DC32E6', '#957EF9',
                    '#CC8D9C', '#717412', '#0B479B',
                    '#7164a3', '#599e86', '#c3ae4f', '#c3744f',
                    ]

    # Write the following output to a file that will be executed with gnuplot 
    gnuplot_graph = "%s/plot-%s.gnuplot" % (tmp_path, sensorn)
    plot = open(gnuplot_graph, 'w')
    
    plot.write('reset\n') 
    plot.write('set xdata time\n')
    plot.write('set timefmt \"%Y %m %d %H %M %S\"\n')
    
    if "combined" in graph_out_file:
        plot.write('set terminal png size 1000,1000\n')
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
    
    if "day-week" in graph_out_file:
        plot.write('set mytics 10\n')
        plot.write('set my2tics 5\n')
        plot.write('set ytics 0,20\n')
        plot.write('set y2tics 0,5\n')
    else:
        plot.write('set my2tics 10\n')
        plot.write('set ytics 10\n')
        plot.write('set y2tics 5\n') 
    
    plot.write('set style line 11 lc rgb \'#808080\' lt 1\n')
    plot.write('set border 3 back ls 11\n')
    plot.write('set tics nomirror\n')
    plot.write('set style line 12 lc rgb \'#808080\' lt 0 lw 1\n')
    plot.write('set grid xtics ytics back ls 12\n')
       
    # Horizontal lines: separate temperature, humidity, and dewpoint
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
        plot.write('set origin 0.0,0.0\n')
        plot.write('set multiplot\n')
        plot.write('set size 1.0,0.5\n')
        plot.write('set origin 0.0,0.5\n')
        plot.write('set title \"Combined Temperatures: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot ')
        if sensorHTGraph[1]:
            plot.write('\"<awk \'$10 == 1\' ' + sensor_log_generate + sensor_head + '" using 1:7 index 0 title \"T1\" w lp ls 12 axes x1y2')
            if sensorHTGraph[2] or sensorHTGraph[3] or sensorHTGraph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensorHTGraph[2]:
            plot.write('\"<awk \'$10 == 2\' ' + sensor_log_generate + sensor_head + '" u 1:7 index 0 title \"T2\" w lp ls 13 axes x1y2')
            if sensorHTGraph[3] or sensorHTGraph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensorHTGraph[3]:
            plot.write('\"<awk \'$10 == 3\' ' + sensor_log_generate + sensor_head + '" u 1:7 index 0 title \"T3\" w lp ls 14 axes x1y2')
            if sensorHTGraph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensorHTGraph[4]:
            plot.write('\"<awk \'$10 == 4\' ' + sensor_log_generate + sensor_head + '" u 1:7 index 0 title \"T4\" w lp ls 15 axes x1y2\n')
        plot.write('set size 1.0,0.5\n')
        plot.write('set origin 0.0,0.0\n')
        plot.write('set title \"Combined Humidities: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
        plot.write('set format x \"%H:%M\\n%m/%d\"\n')
        plot.write('plot ')
        if sensorHTGraph[1]:
            plot.write('\"<awk \'$10 == 1\' ' + sensor_log_generate + sensor_head + '" using 1:8 index 0 title \"H1\" w lp ls 12 axes x1y1')
            if sensorHTGraph[2] or sensorHTGraph[3] or sensorHTGraph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensorHTGraph[2]:
            plot.write('\"<awk \'$10 == 2\' ' + sensor_log_generate + sensor_head + '" u 1:8 index 0 title \"H2\" w lp ls 13 axes x1y1')
            if sensorHTGraph[3] or sensorHTGraph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensorHTGraph[3]:
            plot.write('\"<awk \'$10 == 3\' ' + sensor_log_generate + sensor_head + '" u 1:8 index 0 title \"H3\" w lp ls 14 axes x1y1')
            if sensorHTGraph[4]: plot.write(', ')
            else: plot.write('\n')
        if sensorHTGraph[4]:
            plot.write('\"<awk \'$10 == 4\' ' + sensor_log_generate + sensor_head + '" u 1:8 index 0 title \"H4\" w lp ls 15 axes x1y1\n')
        plot.write('unset multiplot\n')

    # Generate a graph with temp, hum, and dew point for a specific sensor
    if "separate" in graph_out_file:
        plot.write('set title \"Sensor ' + sensorn + ': ' + sensorHTName[int(float(sensorn))] + '\\n\\n' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot \"<awk \'$10 == ' + sensorn + '\' ' + sensor_log_generate + sensor_head + '" using 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, ')
        plot.write('\"\" u 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, ')
        plot.write('\"\" u 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, ')
        
        plot.write('\"<awk \'$15 == ' + sensorn + '\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relayName[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" u 1:8 index 0 title \"' + relayName[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" u 1:9 index 0 title \"' + relayName[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" u 1:10 index 0 title \"' + relayName[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" u 1:11 index 0 title \"' + relayName[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" u 1:12 index 0 title \"' + relayName[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" u 1:13 index 0 title \"' + relayName[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" u 1:14 index 0 title \"' + relayName[8] + '\" w impulses ls 11 axes x1y1\n')

    # Generate a graph of the past day and week periods for each sensor 
    if "dayweek" in graph_out_file:
        plot.write('set origin 0.0,0.0\n')
        plot.write('set multiplot\n')
        # Top graph - day
        plot.write('set size 1.0,0.5\n')
        plot.write('set origin 0.0,0.5\n')
        plot.write('set title \"Sensor ' + sensorn + ': ' + sensorHTName[int(float(sensorn))] + '\\n\\nPast Day: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
        plot.write('plot \"<awk \'$10 == ' + sensorn + '\' ' + sensor_log_generate + sensor_head + '" using 1:7 index 0 title \"T\" w lp ls 1 axes x1y2, ')
        plot.write('\"\" using 1:8 index 0 title \"RH\" w lp ls 2 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"DP\" w lp ls 3 axes x1y2, ')
        plot.write('\"<awk \'$15 == ' + sensorn + '\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relayName[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" using 1:8 index 0 title \"' + relayName[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"' + relayName[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" using 1:10 index 0 title \"' + relayName[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" using 1:11 index 0 title \"' + relayName[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" using 1:12 index 0 title \"' + relayName[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" using 1:13 index 0 title \"' + relayName[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" using 1:14 index 0 title \"' + relayName[8] + '\" w impulses ls 11 axes x1y1\n')
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
        plot.write('plot \"<awk \'$10 == ' + sensorn + '\' ' + sensor_log_generate + sensor_head + '" using 1:7 index 0 notitle w lp ls 1 axes x1y2, ')
        plot.write('\"\" using 1:8 index 0 notitle w lp ls 2 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 notitle w lp ls 3 axes x1y2\n')
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
        plot.write('sqrt(-1) title \"' + relayName[1] + '\" w impulses ls 4, ')
        plot.write('sqrt(-1) title \"' + relayName[2] + '\" w impulses ls 5, ')
        plot.write('sqrt(-1) title \"' + relayName[3] + '\" w impulses ls 6, ')
        plot.write('sqrt(-1) title \"' + relayName[4] + '\" w impulses ls 7, ')
        plot.write('sqrt(-1) title \"' + relayName[5] + '\" w impulses ls 8, ')
        plot.write('sqrt(-1) title \"' + relayName[6] + '\" w impulses ls 9, ')
        plot.write('sqrt(-1) title \"' + relayName[7] + '\" w impulses ls 10, ')
        plot.write('sqrt(-1) title \"' + relayName[8] + '\" w impulses ls 11\n')
        
    if "legend-full" in graph_out_file:
        plot.write('set xlabel \"Date and Time\"\n')
        plot.write('set ylabel \"# Seconds Relays On and % Humidity\"\n')
        plot.write('set y2label \"Temperature and Dew Point\"\n')
        plot.write('set border 3 back ls 11\n')
        plot.write('set tics nomirror\n')
        plot.write('set key outside\n')
        plot.write('plot \"<awk \'$10 == 1\' ' + sensor_log_generate + sensor_head + '" using 1:7 index 0 title \"Temperature\" w lp ls 1 axes x1y2, ')
        plot.write('\"\" using 1:8 index 0 title \"Rel. Humidity\" w lp ls 2 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"Dew Point\" w lp ls 3 axes x1y2, ')
        plot.write('\"<awk \'$15 == 1\' ' + relay_log_generate + relay_head + '" u 1:7 index 0 title \"' + relayName[1] + '\" w impulses ls 4 axes x1y1, ')
        plot.write('\"\" using 1:8 index 0 title \"' + relayName[2] + '\" w impulses ls 5 axes x1y1, ')
        plot.write('\"\" using 1:9 index 0 title \"' + relayName[3] + '\" w impulses ls 6 axes x1y1, ')
        plot.write('\"\" using 1:10 index 0 title \"' + relayName[4] + '\" w impulses ls 7 axes x1y1, ')
        plot.write('\"\" using 1:11 index 0 title \"' + relayName[5] + '\" w impulses ls 8 axes x1y1, ')
        plot.write('\"\" using 1:12 index 0 title \"' + relayName[6] + '\" w impulses ls 9 axes x1y1, ')
        plot.write('\"\" using 1:13 index 0 title \"' + relayName[7] + '\" w impulses ls 10 axes x1y1, ')
        plot.write('\"\" using 1:14 index 0 title \"' + relayName[8] + '\" w impulses ls 11 axes x1y1\n')
    plot.close()

    # Generate graph with gnuplot with the above generated command sequence
    if logging.getLogger().isEnabledFor(logging.DEBUG) is False:
        subprocess.call(['gnuplot', gnuplot_graph])
        os.remove(gnuplot_graph)
        os.remove(sensor_log_generate)
        os.remove(relay_log_generate)
    else:
        gnuplot_log = "%s/plot-%s.log" % (log_path, sensorn)
        with open(gnuplot_log, 'ab') as errfile:
            subprocess.call(['gnuplot', gnuplot_graph], stderr=errfile)

# Read CO2 from sensor
def read_co2_sensor(sensor):
    global co2
    
    logging.info("[Read CO2 Sensor-%s] Taking CO2 reading", sensor)
    ser = serial.Serial("/dev/ttyAMA0")
    ser.flushInput()
    time.sleep(1)
    ser.write("\xFE\x44\x00\x08\x02\x9F\x25")
    time.sleep(.01)
    resp = ser.read(7)
    high = ord(resp[3])
    low = ord(resp[4])
    co2[sensor] = (high*256) + low
    logging.info("[Read CO2 Sensor] CO2: %s", str(co2[sensor]))
	
# Append co2 sensor data to the log file
def write_co2_sensor_log(sensor):
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)
        
    if not Terminate:
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
                    co2[sensor], sensor))
                logging.debug("[Write CO2 Sensor Log] Data appended to %s", sensor_co2_log_file_tmp)
        except:
            logging.warning("[Write CO2 Sensor Log] Unable to append data to %s", sensor_co2_log_file_tmp)

        logging.debug("[Write CO2 Sensor Log] Removing lock: %s", lock.path)
        lock.release()

# Read the temperature and humidity from sensor
def read_dht_sensor(silent, sensor):
    global tempc
    global humidity
    global dewpointc
    #global heatindexc
    global chktemp
    chktemp = 1
    
    if (sensorHTDevice[1] == 'DHT11'): device = Adafruit_DHT.DHT11
    elif (sensorHTDevice[1] == 'DHT22'): device = Adafruit_DHT.DHT22
    elif (sensorHTDevice[1] == 'AM2302'): device = Adafruit_DHT.AM2302
    else: device = 'Other'

    if not silent and not Terminate:
        logging.debug("[Read HT Sensor-%s] Taking first Temperature/humidity reading", sensor)
        
    if not Terminate:
        humidity2, tempc2 = Adafruit_DHT.read_retry(device, sensorHTPin[sensor])
        
        if humidity2 == None or tempc2 == None:
            logging.warning("[Read HT Sensor-%s] Could not read temperature/humidity!", sensor)
            
        if not silent and humidity2 != None and tempc2 != None:
            logging.debug("[Read HT Sensor-%s] %.1f°C, %.1f%%", sensor, tempc2, humidity2)

        time.sleep(2) # Wait 2 seconds between sensor reads
        
        if not silent: 
            logging.debug("[Read HT Sensor-%s] Taking second Temperature/humidity reading", sensor)
            
    while chktemp and not Terminate and humidity2 != None and tempc2 != None:
        if not Terminate:
            humidity[sensor], tempc[sensor] = Adafruit_DHT.read_retry(device, sensorHTPin[sensor])
            
        if humidity[sensor] != 'None' or tempc[sensor] != 'None':
            if not silent and not Terminate: 
                logging.debug("[Read HT Sensor-%s] %.1f°C, %.1f%%", sensor, tempc[sensor], humidity[sensor])
                logging.debug("[Read HT Sensor-%s] Differences: %.1f°C, %.1f%%", sensor, abs(tempc2-tempc[sensor]), abs(humidity2-humidity[sensor]))
                
            if abs(tempc2-tempc[sensor]) > 1 or abs(humidity2-humidity[sensor]) > 1 and not Terminate:
                tempc2 = tempc[sensor]
                humidity2 = humidity[sensor]
                chktemp = 1
                
                if not silent:
                    logging.debug("[Read HT Sensor-%s] Successive readings > 1 difference: Rereading", sensor)
                    
                time.sleep(2)
            elif not Terminate:
                chktemp = 0

                if not silent: 
                    logging.debug("[Read HT Sensor-%s] Successive readings < 1 difference: keeping.", sensor)

                tempf = float(tempc[sensor])*9.0/5.0 + 32.0
                dewpointc[sensor] = tempc[sensor] - ((100-humidity[sensor]) / 5)
                #dewpointf[sensor] = dewpointc[sensor] * 9 / 5 + 32
                #heatindexf =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
                #heatindexc[sensor] = (heatindexf - 32) * (5 / 9)
                
                if not silent: 
                    logging.debug("[Read HT Sensor-%s] Temp: %.1f°C, Hum: %.1f%%, DP: %.1f°C", sensor, tempc[sensor], humidity[sensor], dewpointc[sensor])
                   
        else:
            logging.warning("[Read Sensor-%s] Could not read temperature/humidity!", sensor)
            time.sleep(2) # Wait 2 seconds between sensor reads
           
# Append HT sensor data to the log file
def write_dht_sensor_log(sensor):
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)
        
    if not Terminate:
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
                    tempc[sensor], humidity[sensor], dewpointc[sensor], sensor))
                logging.debug("[Write Sensor Log] Data appended to %s", sensor_ht_log_file_tmp)
        except:
            logging.warning("[Write Sensor Log] Unable to append data to %s", sensor_ht_log_file_tmp)

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

# Read variables from the configuration file
def read_config(silent):
    global config_file
    global sensorHTName
    global sensorHTDevice
    global sensorHTPin
    global sensorHTPeriod
    global sensorHTActivated
    global sensorHTGraph
    
    global sensorCo2Name
    global sensorCo2Device
    global sensorCo2Pin
    global sensorCo2Period
    global sensorCo2Activated
    global sensorCo2Graph
    
    global Co2Period
    global relayCo2
    global setCo2
    global Co2OR
    global Co2_P
    global Co2_I
    global Co2_D
    
    global relayName
    global relayPin
    global relayTrigger
    
    global relayHum
    global setHum
    global HumOR
    global Hum_P
    global Hum_I
    global Hum_D
    
    global relayTemp
    global setTemp
    global TempOR
    global Temp_P
    global Temp_I
    global Temp_D
    
    global factorHumSeconds
    global factorTempSeconds
    global cameraLight
    global numRelays
    global numHTSensors
    global numCo2Sensors
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
    numCo2Sensors = config.getint('Misc', 'numco2sensors')
    numHTSensors = config.getint('Misc', 'numhtsensors')
    numTimers = config.getint('Misc', 'numtimers')
    cameraLight = config.getint('Misc', 'cameralight')
    
    for i in range(1, 5):
        sensorCo2Name[i] = config.get('CO2Sensor%d' % i, 'sensorco2%dname' % i)
        sensorCo2Device[i] = config.get('CO2Sensor%d' % i, 'sensorco2%ddevice' % i)
        sensorCo2Pin[i] = config.getint('CO2Sensor%d' % i, 'sensorco2%dpin' % i)
        sensorCo2Period[i] = config.getint('CO2Sensor%d' % i, 'sensorco2%dperiod' % i)
        sensorCo2Activated[i] = config.getint('CO2Sensor%d' % i, 'sensorco2%dactivated' % i)
        sensorCo2Graph[i] = config.getint('CO2Sensor%d' % i, 'sensorco2%dgraph' % i)
        
        Co2Period[i] = config.getint('Co2PID%d' % i, 'co2%dperiod' % i)
        relayCo2[i] = config.getint('Co2PID%d' % i, 'co2%drelay' % i)
        setCo2[i] = config.getfloat('Co2PID%d' % i, 'co2%dset' % i)
        Co2OR[i] = config.getint('Co2PID%d' % i, 'co2%dor' % i)
        Co2_P[i] = config.getfloat('Co2PID%d' % i, 'co2%dp' % i)
        Co2_I[i] = config.getfloat('Co2PID%d' % i, 'co2%di' % i)
        Co2_D[i] = config.getfloat('Co2PID%d' % i, 'co2%dd' % i)
        
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
        sensorHTName[i] = config.get('HTSensor%d' % i, 'sensorht%dname' % i)
        sensorHTDevice[i] = config.get('HTSensor%d' % i, 'sensorht%ddevice' % i)
        sensorHTPin[i] = config.getint('HTSensor%d' % i, 'sensorht%dpin' % i)
        sensorHTPeriod[i] = config.getint('HTSensor%d' % i, 'sensorht%dperiod' % i)
        sensorHTActivated[i] = config.getint('HTSensor%d' % i, 'sensorht%dactivated' % i)
        sensorHTGraph[i] = config.getint('HTSensor%d' % i, 'sensorht%dgraph' % i)
        
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
    config.set('Misc', 'numco2sensors', numCo2Sensors)
    config.set('Misc', 'numhtsensors', numHTSensors)
    config.set('Misc', 'numtimers', numTimers)
    config.set('Misc', 'cameralight', cameraLight)
    
    for i in range(1, 5):
        config.add_section('CO2Sensor%d' % i)
        config.set('CO2Sensor%d' % i, 'sensorco2%dname' % i, sensorCo2Name[i])
        config.set('CO2Sensor%d' % i, 'sensorco2%ddevice' % i, sensorCo2Device[i])
        config.set('CO2Sensor%d' % i, 'sensorco2%dpin' % i, sensorCo2Pin[i])
        config.set('CO2Sensor%d' % i, 'sensorco2%dperiod' % i, sensorCo2Period[i])
        config.set('CO2Sensor%d' % i, 'sensorco2%dactivated' % i, sensorCo2Activated[i])
        config.set('CO2Sensor%d' % i, 'sensorco2%dgraph' % i, sensorCo2Graph[i])
        
        config.add_section('Co2PID%d' % i)
        config.set('Co2PID%d' % i, 'co2%dperiod' % i, Co2Period[i])
        config.set('Co2PID%d' % i, 'co2%drelay' % i, relayCo2[i])
        config.set('Co2PID%d' % i, 'co2%dset' % i, setCo2[i])
        config.set('Co2PID%d' % i, 'co2%dor' % i, Co2OR[i])
        config.set('Co2PID%d' % i, 'co2%dp' % i, Co2_P[i])
        config.set('Co2PID%d' % i, 'co2%di' % i, Co2_I[i])
        config.set('Co2PID%d' % i, 'co2%dd' % i, Co2_D[i])
    
    for i in range(1, 5):
        config.add_section('HTSensor%d' % i)
        config.set('HTSensor%d' % i, 'sensorht%dname' % i, sensorHTName[i])
        config.set('HTSensor%d' % i, 'sensorht%ddevice' % i, sensorHTDevice[i])
        config.set('HTSensor%d' % i, 'sensorht%dpin' % i, sensorHTPin[i])
        config.set('HTSensor%d' % i, 'sensorht%dperiod' % i, sensorHTPeriod[i])
        config.set('HTSensor%d' % i, 'sensorht%dactivated' % i, sensorHTActivated[i])
        config.set('HTSensor%d' % i, 'sensorht%dgraph' % i, sensorHTGraph[i])
        
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
    
    # Initialize
    for i in range(1, 9):
        GPIO.setup(relayPin[i], GPIO.OUT)
    
    Relays_Off()

# Turn Relays Off
def Relays_Off():
    for i in range(1, 9):
        if relayTrigger[i] == 0: GPIO.output(relayPin[i], 1)
        else: GPIO.output(relayPin[i], 0)

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

# Set relay on for a specific duration
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
        
    # Turn relay off
    if relayTrigger[relay] == 0: GPIO.output(relayPin[relay], 1)
    else: GPIO.output(relayPin[relay], 0)
    
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
    'numHTSensors',
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

# Email if temperature or humidity is outside of critical range (Not yet implemented)
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

    # Body of email
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

read_config(1)
gpio_initialize()
menu()

runlock.release()
sys.exit(0)