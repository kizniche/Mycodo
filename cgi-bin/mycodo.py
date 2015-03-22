#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo.py - Read sensors, write log, read configuration file, write configuration
#              file, and modulate relays to maintain set environmental conditions
#              (currently temperature and humidity)
#
#  Kyle Gabriel (2012 - 2015)
#

import subprocess
import re
import os
import sys
import time
import datetime
import getopt
import Adafruit_DHT
import RPi.GPIO as GPIO
import ConfigParser
import threading
import rpyc
from rpyc.utils.server import ThreadedServer
from array import *

config_file = '/var/www/mycodo/config/mycodo.cfg'
sensor_log_file = '/var/www/mycodo/log/sensor-2.log'
relay_log_file = '/var/www/mycodo/log/relay-2.log'

# Change the following sensor and pin to your configuration
# Sensor value can be Adafruit_DHT.DHT11, Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302
sensor = Adafruit_DHT.DHT22
dhtPin = 4

# GPIO pins using BCM numbering
# Based on GPOI-relay connection
relayPin = [0] * 9
###### EDIT GPIO PINS BELOW ######
relayPin[1] = 14  # Relay 1: 
relayPin[2] = 15  # Relay 2: 
relayPin[3] = 18  # Relay 3: 
relayPin[4] = 23  # Relay 4: 
relayPin[5] = 24  # Relay 5: 
relayPin[6] = 25  # Relay 6: 
relayPin[7] = 8   # Relay 7: 
relayPin[8] = 7   # Relay 8: 

# Sensor data
chktemp = ''
tempc = ''
tempf = ''
humidity = ''
dewpointc = ''
dewpointf = ''
heatindex =  ''

# Constraints
minTemp = ''
maxTemp = ''
minHum = ''
maxHum = ''

# Relay overrides
relay1o = ''
relay2o = ''
relay3o = ''
relay4o = ''
relay5o = ''
relay6o = ''
relay7o = ''
relay8o = ''

# Control States
tempState = ''
humState = ''

# Timers
RHeatTS = ''
RHumTS = ''
RHepaTS = ''
RFanTS = ''

# Miscellaneous
currentTime = ''
webOR = ''
wfactor = ''
server = ''
serverStop = 0

class MyService(rpyc.Service):
    # My service
    def exposed_echo(self, text):
        print text
        return text
    def exposed_GPIOLow(self, text):
        setup()
        print '%s [Client command] Set Relay %s GPIO LOW' % (Timestamp(), text)
        ChangeRelay(int(float(text)), 0)
        ReadGPIO()
        return 1
    def exposed_GPIOHigh(self, text):
        setup()
        print '%s [Client command] Set Relay %s GPIO HIGH' % (Timestamp(), text)
        ChangeRelay(int(float(text)), 1)
        ReadGPIO()
        return 1
    def exposed_Terminate(self, text):
        print '%s [Client command] Terminate Threads' % Timestamp()
        global serverStop
        serverStop = 1

class BackThread(threading.Thread):
    def run(self):
        global server
        server = ThreadedServer(MyService, port = 18812)
        server.start()


def usage():
    print 'mycodo.py: Reads temperature and humidity from sensors, writes log file, and operates relays as a daemon to maintain set environmental conditions.\n'
    print 'Usage:  ', __file__, '[OPTION] [FILE]...\n'
    print 'Example:', __file__, '-w /var/www/mycodo/log/sensor.log'
    print '        ', __file__, '-c 1 -s 0'
    print '        ', __file__, '--change=1 --state=0'
    print '        ', __file__, '--daemon\n'
    print 'data is presented in the following format for -r:'
    print 'Year Month Day Hour Minute Second Timestamp Humidity TempC DewPointC HeatIndexC\n'
    print 'Options:'
    print '    -r  --read'
    print '           read sensor and display data'
    print '    -p, --pin'
    print '           display status of the GPIO pins (HIGH or LOW)'
    print '    -w, --write=FILE'
    print '           write sensor data to log file'
    print '    -c, --change=RELAY'
    print '           change the state of a relay (must use in conjunction with -s)'
    print '    -s, --state=[0/1]'
    print '           change the state of RELAY to on (1) or off (0)'
    print '    -d, --daemon'
    print '           start program as daemon that monitors conditions and modulates relays'
    print '    -h, --help'
    print '           display this help and exit\n'

def setup():
    # Set up GPIO using BCM numbering
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    print "%s Setting up GPIOs" % Timestamp()
    GPIO.setup(relayPin[1], GPIO.OUT)
    GPIO.setup(relayPin[2], GPIO.OUT)
    GPIO.setup(relayPin[3], GPIO.OUT)
    GPIO.setup(relayPin[4], GPIO.OUT)
    GPIO.setup(relayPin[5], GPIO.OUT)
    GPIO.setup(relayPin[6], GPIO.OUT)
    GPIO.setup(relayPin[7], GPIO.OUT)
    GPIO.setup(relayPin[8], GPIO.OUT)
  
def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'thrpdwc:s:', ["help", "read", "pin", "write=", "change=", "state=", "daemon"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-r", "--read"):
            ReadSensors()
            sys.exit(0)
        elif opt in ("-p", "--pin"):
            setup()
            ReadGPIO()
            sys.exit(0)
        elif opt in ("-w", "--write"):
            global sensor_log_file
            if arg == '': print '%s No log file specified, using default: %s' % (Timestamp(), sensor_log_file)
            else: sensor_log_file = arg
            ReadSensors()
            WriteSensorLog()
            sys.exit(0)
        elif opt in ("-c", "--change"):
            global relaySelect
            relaySelect = int(float(arg))
            if relaySelect > 8 or relaySelect < 1:
                print 'Error: 1 - 8 are the only acceptable options for -c'
                usage()
                sys.exit(0)
        elif opt in ("-s", "--state"):
            global relayState
            relayState = int(float(arg))
            if relayState == 0 or relayState == 1:
                print '%s Requested change of relay %s to' % (Timestamp(), relaySelect)
                if relayState == '1': print 'On'
                elif relayState == '0': print 'Off'
                setup()
                ChangeRelay(relaySelect, relayState)
                ReadGPIO()
                sys.exit(0)
            else:
                print 'Error: 0 or 1 are the only acceptable options for -s'
                usage()
                sys.exit(0)
        elif opt in ("-d", "--daemon"):
            setup()
            Daemon()
        else:
            assert False, "Fail"

bt = BackThread()
def Daemon():
    global bt
    global serverStop
    bt.start()
    print '%s Threaded server activated' % Timestamp()
    print '%s Daemon activated' % Timestamp()
    # the daemon loop
    update = 91
    while True:
        if serverStop == 1:
            global server
            print '%s Terminating background thread' % Timestamp()
            server.close()
            print '%s Terminating forground thread' % Timestamp()
            sys.exit(0)
        if update > 90:
            ReadCfg()
            ReadSensors()
            ConditionsCheck()
            print '%s Sleep 90 seconds' % Timestamp()
            update = 0
        update+=1
        time.sleep(1)

def ChangeRelay(Select, State):
    print '%s Setting relay %s to %s (from %s)' % (Timestamp(), Select, State, GPIO.input(relayPin[Select]))
    GPIO.output(relayPin[Select], State)

def ReadGPIO():
    global relayPin
    print '%s' % Timestamp(),
    for x in range(1, 9):
        print 'Relay %s: %s  ' % (x, GPIO.input(relayPin[x])),
        if x == 4: print '\n%s' % Timestamp(),
        if x == 8: print ''

# Append the data in the file
def WriteSensorLog():
    global sensor_log_file
    try:
        open(sensor_log_file, 'ab').write('{0} {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f}\n'.format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), currentTime, humidity, tempc, dewpointc, heatindex))
        print '%s Data appended to %s' % (Timestamp(), sensor_log_file)
    except:
        print '%s Unable to append data' % Timestamp()

def ReadSensors():
    global tempc
    global tempf
    global humidity
    global dewpointc
    global dewpointf
    global heatindex
    global currentTime
    global chktemp
    chktemp = 1

    print '%s Begin reading sensors' % Timestamp()
    print '%s Temperature/humidity reading one...' % Timestamp(),
    humidity2, tempc2 = Adafruit_DHT.read_retry(sensor, dhtPin)
    print '%.2f°C, %.2f%%' % (tempc2, humidity2)
    time.sleep(3);
    print '%s Temperature/humidity reading two...' % Timestamp(),

    while(chktemp):
        humidity, tempc = Adafruit_DHT.read_retry(sensor, dhtPin)
        print '%.2f°C, %.2f %%' % (tempc2, humidity2)
        print '%s Differences: %.2f°C, %.2f%%' % (Timestamp(), abs(tempc2-tempc), abs(humidity2-humidity))
        if (abs(tempc2-tempc) > 1 and abs(humidity2-humidity) > 1):
            tempc2 = tempc
            humidity2 = humidity
            chktemp = 1
            print "%s Successive readings >1 difference: Wait 3 sec to stabilize: rereading..." % Timestamp(),
            time.sleep(3)
        else:
            chktemp = 0
            print "%s Successive readings <1 difference: keeping." % Timestamp()
            tempf = float(tempc)*9/5+32
            dewpointc = tempc - ((100 - humidity)/ 5)
            dewpointf = (tempc - ((100 - humidity)/ 5))*9/5+32
            heatindex =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
            heatindex = (heatindex - 32) * (5.0 / 9.0)
            currentTime = time.time()-1
            print "{0} {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f}".format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), currentTime-1, humidity, tempc, dewpointc, heatindex)

def ReadCfg():
    global config_file
    global tempc
    global humidity
    global minTemp
    global maxTemp
    global minHum
    global maxHum
    global webOR
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
    global RHeatTS
    global RHumTS
    global RHepaTS
    global RFanTS
    global wfactor

    print '%s Begin reading configuration file' % Timestamp()
    config = ConfigParser.RawConfigParser()
    config.read(config_file)

    minTemp = config.getint('conditions', 'minTemp')
    maxTemp = config.getint('conditions', 'maxTemp')
    minHum = config.getint('conditions', 'minHum')
    maxHum = config.getint('conditions', 'maxHum')
    webOR = config.getint('conditions', 'webOR')
    tempState = config.getint('states', 'tempState')
    humState = config.getint('states', 'humState')
    relay1o = config.getint('states', 'relay1o')
    relay2o = config.getint('states', 'relay2o')
    relay3o = config.getint('states', 'relay3o')
    relay4o = config.getint('states', 'relay4o')
    relay5o = config.getint('states', 'relay5o')
    relay6o = config.getint('states', 'relay6o')
    relay7o = config.getint('states', 'relay7o')
    relay8o = config.getint('states', 'relay8o')
    RHeatTS = config.getint('states', 'RHeatTS')
    RHumTS = config.getint('states', 'RHumTS')
    RHepaTS = config.getint('states', 'RHepaTS')
    RFanTS = config.getint('states', 'RFanTS')
    wfactor = config.getfloat('states', 'wfactor')

    print '%s Reading conditions' % Timestamp()
    print '%s minTemp: %s°C, maxTemp: %s°C, minHum: %s%%, maxHum: %s%%, webOR: %s' % (Timestamp(), minTemp, maxTemp, minHum, maxHum, webOR)
    print '%s Reading states' % Timestamp()
    print '%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %.1f'  % (Timestamp(), tempState, humState, relay1o, relay2o, relay3o, relay4o, relay5o, relay6o, relay7o, relay8o, RHeatTS, RHumTS, RHepaTS, RFanTS, wfactor)

def WriteCfg():
    global config_file
    config = ConfigParser.RawConfigParser()

    config.add_section('conditions')
    config.set('conditions', 'minTemp', minTemp)
    config.set('conditions', 'maxTemp', maxTemp)
    config.set('conditions', 'minHum', minHum)
    config.set('conditions', 'maxHum', maxHum)
    config.set('conditions', 'webOR', webOR)

    config.add_section('states')
    config.set('states', 'tempState', tempState)
    config.set('states', 'humState', humState)
    config.set('states', 'relay1o', relay1o)
    config.set('states', 'relay2o', relay2o)
    config.set('states', 'relay3o', relay3o)
    config.set('states', 'relay4o', relay4o)
    config.set('states', 'relay5o', relay5o)
    config.set('states', 'relay6o', relay6o)
    config.set('states', 'relay7o', relay7o)
    config.set('states', 'relay8o', relay8o)
    config.set('states', 'RHeatTS', RHeatTS)
    config.set('states', 'RHumTS', RHumTS)
    config.set('states', 'RHepaTS', RHepaTS)
    config.set('states', 'RFanTS', RFanTS)
    config.set('states', 'wfactor', wfactor)

    with open(config_file, 'wb') as configfile:
        config.write(configfile)

def ConditionsCheck():
    if not webOR:
        # Temperature check    
        if (tempc < minTemp):
            print '%s Temperature lower than minTemp: %.2f°C < %s°C min' % (Timestamp(), tempc, minTemp)
            print '%s Heating On' % Timestamp()
        elif (tempc > maxTemp):
            print '%s Temperature greater than maxTemp: %.2f°C > %s°C max' % (Timestamp(), tempc, maxTemp)
            print '%s Cooling On' % Timestamp()
        else:
            print '%s Temperature within set range: %s°C min < %.2f°C < %s°C max' % (Timestamp(), minTemp, tempc, maxTemp)

        # Humidity check
        if (humidity < minHum):
            print '%s Humidity lower than minHum: %.2f%% < %s%% min' % (Timestamp(), humidity, minHum)
            print '%s Humidification On' % Timestamp()
        elif (humidity > maxHum):
            print '%s Humidity greater than maxHum: %.2f%% > %s%% max' % (Timestamp(), humidity, maxHum)
            print '%s Exhaust Fan On' % Timestamp()
        else:
            print '%s Humidity within set range: %s%% min < %.2f%% < %s%% max' % (Timestamp(), minHum, humidity, maxHum)
    else:
        print '%s Web Override Activated: Relay manipulation suspended.' % Timestamp()

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')
 
menu()
usage()
sys.exit(0)