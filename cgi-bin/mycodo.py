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
import fcntl
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
sensor_log_file = '/var/www/mycodo/log/sensor.log'
relay_log_file = '/var/www/mycodo/log/relay.log'

relay_script = '/var/www/mycodo/cgi-bin/relay.sh'

lock_directory = '/var/lock/mycodo/'
config_lock = 'config.lock'
sensor_log_lock = 'sensorlog.lock'
relay_log_lock = 'relaylog.lock'

# Change the following sensor and pin to your configuration
# Sensor value can be Adafruit_DHT.DHT11, Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302
sensor = Adafruit_DHT.DHT22
dhtPin = 4

# GPIO pins (BCM numbering) and name of devices attached to relay
relayPin = [0] * 9
relayName = [0] * 9

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
timerOneSeconds = ''
timerTwoSeconds = ''

# Miscellaneous
currentTime = ''
webOR = ''
wfactor = ''
server = ''
terminateServer = 0
variableName = ''
variableValue = ''

class ComServer(rpyc.Service):
    def exposed_GPIOLow(self, remoteCommand):
        GPIOSetup()
        print '%s [Client command] Set Relay %s GPIO LOW' % (Timestamp(), remoteCommand)
        ChangeRelay(int(float(remoteCommand)), 0)
        GPIORead()
        return 1
    def exposed_GPIOHigh(self, remoteCommand):
        GPIOSetup()
        print '%s [Client command] Set Relay %s GPIO HIGH' % (Timestamp(), remoteCommand)
        ChangeRelay(int(float(remoteCommand)), 1)
        GPIORead()
        return 1
    def exposed_Terminate(self, remoteCommand):
        print '%s [Client command] Terminate threads and shut down' % Timestamp()
        global terminateServer
        terminateServer = 1
        return 1

class ComThread(threading.Thread):
    def run(self):
        global server
        server = ThreadedServer(ComServer, port = 18812)
        server.start()

class RelayOnSecThread(threading.Thread):
    def __init__(self, relaySelect, relaySeconds):
        threading.Thread.__init__(self)
        self.relaySelect = relaySelect
        self.relaySeconds = relaySeconds
    def run(self):
        if GPIO.input(relayPin[self.relaySelect]) == 0:
            WriteRelayLog(self.relaySelect, self.relaySeconds)
            print '%s [Relay Duration] Turning relay %s (%s) on for %s seconds' % (Timestamp(), self.relaySelect, relayName[self.relaySelect], self.relaySeconds)
            GPIO.output(relayPin[self.relaySelect], 1)
            time.sleep(self.relaySeconds)
            GPIO.output(relayPin[self.relaySelect], 0)
            print '%s [Relay Duration] Turning relay %s (%s) off (was on for %s seconds)' % (Timestamp(), self.relaySelect, relayName[self.relaySelect], self.relaySeconds)
        else:
            print "%s [Relay Duration] Abort: Requested relay %s (%s) on for %s seconds, but it's already on!" % (Timestamp(), self.relaySelect, relayName[self.relaySelect], self.relaySeconds)

def usage():
    print 'mycodo.py: Reads temperature and humidity from sensors, writes log file, and operates relays as a daemon to maintain set environmental conditions.\n'
    print 'Usage:  ', __file__, '[OPTION]...\n'
    print 'Example:', __file__, '-w /var/www/mycodo/log/sensor.log'
    print '        ', __file__, '-c 1 -s 0'
    print '        ', __file__, '-n relay1Name --value Banana'
    print '        ', __file__, '--daemon\n'
    print 'Options:'
    print '    -c, --change=RELAY'
    print '           Change the state of a relay (--state required)'
    print '        --state=[0/1/X]'
    print '           Change the state of RELAY to on (1), off (0), or (X) number of seconds on'
    print '    -d, --daemon'
    print '           Start program as daemon that monitors conditions and modulates relays'
    print '    -h, --help'
    print '           Display this help and exit'
    print '    -n, --name=VARIABLE'
    print '           Change the VALUE of a single VARIABLE (--value required)'
    print '        --value=VALUE'
    print '           Change the VALUE of variable NAME (-n required)'
    print '    -p, --pin'
    print '           Display status of the GPIO pins (HIGH or LOW)'
    print '    -r  --read=[SENSOR/CONFIG]'
    print '           Read and display sensor data or config settings'
    print '    -s, --set minTemp maxTemp minHum MaxHum webOV'
    print '           Change operating parameters (must give all options as int, the last must be 0 or 1)'
    print '    -w, --write=FILE'
    print '           Write sensor data to log file\n'

def GPIOSetup():
    # Set up GPIO using BCM numbering
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    print "%s [GPIO Initialize] GPIO setode to BCM numbering, setup to output" % Timestamp()
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
        opts, args = getopt.getopt(sys.argv[1:], 'c:dhpr:s:tn:w', ["change=", "daemon", "help", "name=", "pin", "read=", "set=", "state=", "value=", "write="])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c", "--change"):
            if not RepresentsInt(arg) or int(float(arg)) > 8 or int(float(arg)) < 1:
                print 'Error: --change only accepts integrers 1 though 8'
                sys.exit(1)
            else:
                global relaySelect
                relaySelect = arg
        elif opt == "--state":
            if not RepresentsInt(arg) or int(float(arg)) < 0:
                print 'Error: --state only accepts integrers'
            else:
                global relayState
                relayState = arg
            if relayState == '0' or relayState == '1':
                print '%s [GPIO Write] Requested change of relay %s to' % (Timestamp(), relaySelect)
                if relayState == '1': print 'On'
                elif relayState == '0': print 'Off'
                ReadCfg(0)
                GPIOSetup()
                ChangeRelay(int(float(relaySelect)), int(float(relayState)))
                GPIORead()
                sys.exit(0)
            elif relayState > 1:
                ReadCfg(0)
                GPIOSetup()
                RelayOnDuration(int(float(relaySelect)), int(float(relayState)))
                sys.exit(0)
            else:
                print 'Error: 0 and positive integers are the only acceptable options for --state'
                usage()
                sys.exit(1)
        elif opt in ("-d", "--daemon"):
            Daemon()
            sys.exit(0)
        elif opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-n", "--name"):
            global variableName
            variableName = arg
        elif opt == "--value":
            global variableValue
            variableValue = arg
            if not CheckVariableName():
                print "Error: Variable '%s' does not exist" % variableName
                sys.exit(1)
            else:
                print "%s [Change Value] Changing variable '%s' value to %s" % (Timestamp(), variableName, variableValue)
                ReadCfg(0)
                globals()[variableName] = variableValue
                WriteCfg()
                print "%s [Change Value] Variable '%s' value changed to %s" % (Timestamp(), variableName, variableValue)
                sys.exit(0)
        elif opt in ("-p", "--pin"):
            ReadCfg(0)
            GPIOSetup()
            GPIORead()
            sys.exit(0)
        elif opt in ("-r", "--read"):
            if arg == 'SENSOR':
                ReadSensors()
                sys.exit(0)
            elif arg == 'CONFIG':
                ReadCfg(0)
                sys.exit(0)
            else:
                print 'Error: Invalid option for --read'
                usage()
                sys.exit(1)
        elif opt in ("-s", "--set"):
            if len(sys.argv) != 7:
                print 'Error: Too many or not enough options. --set only accepts 5 options'
                sys.exit(1)
            elif not RepresentsInt(sys.argv[2]) and not RepresentsInt(sys.argv[3]) and not RepresentsInt(sys.argv[4]) and not RepresentsInt(sys.argv[5]) and not RepresentsInt(sys.argv[6]):
                print 'Error: --set only accepts integers'
                sys.exit(1)
            elif sys.argv[6] != '0' and sys.argv[6] != '1':
                print 'Error: The last option of --set must be 0 or 1'
                sys.exit(0)
            print '%s [Set Conditions] Desired vvalues: minTemp: %s, maxTemp: %s, minHum: %s, maxHum: %s, WebOR: %s' % (Timestamp(), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]) 
            ReadCfg(0)
            global minTemp
            global maxTemp
            global minHum
            global maxHum
            global webOR
            minTemp = int(float(sys.argv[2]))
            maxTemp = int(float(sys.argv[3]))
            minHum = int(float(sys.argv[4]))
            maxHum = int(float(sys.argv[5]))
            webOR = int(float(sys.argv[6]))
            WriteCfg()
            print '%s [Set Conditions] New Values: minTemp: %s, maxTemp: %s, minHum: %s, maxHum: %s, WebOR: %s' % (Timestamp(), minTemp, maxTemp, minHum, maxHum, webOR)
            sys.exit(0)
        elif opt in ("-w", "--write"):
            global sensor_log_file
            if arg == '':
                print '%s [Write Log] No log file specified, using default: %s' % (Timestamp(), sensor_log_file)
            else:
                sensor_log_file = arg
            ReadSensors()
            WriteSensorLog()
            sys.exit(0)
        else:
            assert False, "Fail"

def Daemon():
    global terminateServer
    print '%s [Daemon] Daemon started' % Timestamp()
    ct = ComThread()
    ct.start()
    print '%s [Daemon] Communication server started as thread' % Timestamp()
    ReadCfg(1)
    print '%s [Daemon] Initial configuration read to set variables' % Timestamp()
    GPIOSetup()
    # the daemon loop
    timerOne = 0
    timerTwo = 0
    while True:
        if terminateServer == 1: # Check if variable set to terminate the server
            global server
            print '%s [Shutdown] Terminating server thread' % Timestamp()
            server.close()
            print '%s [Shutdown] Exiting Python' % Timestamp()
            sys.exit(0)
        
        if timerOne > timerOneSeconds:
            print '%s [Daemon] %s-second timer expired: Sensor Read and Condition Check' % (Timestamp(), timerOneSeconds)
            print '%s [Daemon] Reread config to make sure variables are current' % Timestamp()
            ReadCfg(0)
            ReadSensors()
            ConditionsCheck()
            timerOne = 0
            
        if timerTwo > timerTwoSeconds:
            print '%s [Daemon] %s-second timer expired: Sensor Log Write' % (Timestamp(), timerTwoSeconds)
            WriteSensorLog()
            timerTwo = 0

        timerOne+=1
        timerTwo+=1
        time.sleep(1)

def RelayOnDuration(number, seconds):
    #jobs=[]
    ros = RelayOnSecThread(number, seconds)
    #jobs.append(ros)
    ros.start()
        
def ChangeRelay(Select, State):
    print '%s [GPIO Write] Setting relay %s (%s) to %s (was %s)' % (Timestamp(), Select, relayName[Select], State, GPIO.input(relayPin[Select]))
    GPIO.output(relayPin[Select], State)

def GPIORead():
    print '%s [GPIO Read]' % Timestamp(),
    for x in range(1, 9):
        print 'Relay %s: %s  ' % (x, GPIO.input(relayPin[x])),
        if x == 4: print '\n%s [GPIO Read]' % Timestamp(),
        if x == 8: print ''

# Append sensor data to log file
def WriteSensorLog():
    try:
        open(sensor_log_file, 'ab').write('{0} {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f}\n'.format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), currentTime, humidity, tempc, dewpointc, heatindex))
        print '%s [Write Sensor Log] Data appended to %s' % (Timestamp(), sensor_log_file)
    except:
        print '%s [Write Sensor Log] Unable to append data to %s' % (Timestamp(), sensor_log_file)

# Append relay  duration to log file
def WriteRelayLog(relayNumber, relaySeconds):
    relay = [0] * 9
    for n in range(1, 9):
        if n == relayNumber:
            relay[relayNumber] = relaySeconds
    try:
        open(relay_log_file, 'ab').write('{0} {1} {2} {3} {4} {5} {6} {7} {8}\n'.format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), relay[1], relay[2], relay[3], relay[4], relay[5], relay[6], relay[7], relay[8]))
        print '%s [Write Relay Log] Data appended to %s' % (Timestamp(), relay_log_file)
    except:
        print '%s [Write Relay Log] Unable to append data to %s' % (Timestamp(), relay_log_file)

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

    print '%s [Read Sensors] Temperature/humidity reading one:' % Timestamp(),
    humidity2, tempc2 = Adafruit_DHT.read_retry(sensor, dhtPin)
    print '%.2f°C, %.2f%%' % (tempc2, humidity2)
    time.sleep(3);
    print '%s [Read Sensors] Temperature/humidity reading two:' % Timestamp(),

    while(chktemp):
        humidity, tempc = Adafruit_DHT.read_retry(sensor, dhtPin)
        print '%.2f°C, %.2f%%' % (tempc2, humidity2)
        print '%s [Read Sensors] Differences: %.2f°C, %.2f%%' % (Timestamp(), abs(tempc2-tempc), abs(humidity2-humidity))
        if (abs(tempc2-tempc) > 1 and abs(humidity2-humidity) > 1):
            tempc2 = tempc
            humidity2 = humidity
            chktemp = 1
            print "%s [Read Sensors] Successive readings >1 difference: Wait 3 sec to stabilize: rereading..." % Timestamp(),
            time.sleep(3)
        else:
            chktemp = 0
            print "%s [Read Sensors] Successive readings <1 difference: keeping." % Timestamp()
            tempf = float(tempc) * 9 / 5 + 32
            dewpointc = tempc - ((100 - humidity)/ 5)
            dewpointf = (tempc - ((100 - humidity)/ 5)) * 9 / 5 + 32
            heatindex =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
            heatindex = (heatindex - 32) * (5.0 / 9.0)
            currentTime = time.time()
            print "{0} [Read Sensors] {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f}".format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), currentTime, humidity, tempc, dewpointc, heatindex)

def ReadCfg(silent):
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
    global timerOneSeconds
    global timerTwoSeconds
    global relayPin
    global relayName

    config = ConfigParser.RawConfigParser()
    config.read(config_file)

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
    minTemp = config.getint('Conditions', 'mintemp')
    maxTemp = config.getint('Conditions', 'maxtemp')
    minHum = config.getint('Conditions', 'minhum')
    maxHum = config.getint('Conditions', 'maxhum')
    webOR = config.getint('Conditions', 'webor')
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
    RHeatTS = config.getint('States', 'rheatts')
    RHumTS = config.getint('States', 'rhumts')
    RHepaTS = config.getint('States', 'rhepats')
    RFanTS = config.getint('States', 'rfants')
    wfactor = config.getfloat('States', 'wfactor')
    timerOneSeconds = config.getint('States', 'timeroneseconds')
    timerTwoSeconds = config.getint('States', 'timertwoseconds')

    if not silent:
        print '%s [Read Config] minTemp: %s°C, maxTemp: %s°C, minHum: %s%%, maxHum: %s%%, webOR: %s' % (Timestamp(), minTemp, maxTemp, minHum, maxHum, webOR)
        print '%s [Read Config] RelayNum[Name][Pin]:' % Timestamp(),
        for x in range(1,9):
            if x == 5:
                print '\n%s [Read Config] RelayNum[Name][Pin]:' % Timestamp(),
            if relayPin[x] < 10:
                print '%s[%s][%s ]' % (x, relayName[x], relayPin[x]),
            else:
                print '%s[%s][%s]' % (x, relayName[x], relayPin[x]),
        print '\n%s [Read Config] %s %s %s %s %s %s %s %s %s %s %s %s %s %s %.1f %s %s'  % (Timestamp(), tempState, humState, relay1o, relay2o, relay3o, relay4o, relay5o, relay6o, relay7o, relay8o, RHeatTS, RHumTS, RHepaTS, RFanTS, wfactor, timerOneSeconds, timerTwoSeconds)

def WriteCfg():
    config_lock_path = lock_directory + config_lock
    config = ConfigParser.RawConfigParser()

    if not os.path.exists(lock_directory):
        os.makedirs(lock_directory)

    waitingForLock = 1
    errorOnce = 1
    lockWaitCount = 1
    while waitingForLock:
        if not lockFile(config_lock_path):
            if errorOnce:
                print '%s [Write Config] Cannot gain config lock (already locked): Waiting to gain lock...' % Timestamp()
                errorOnce = 0
            if lockWaitCount == 60:
                print '%s [Write Config] 60 seconds waiting to gain config lock (too long): Breaking lock.' % Timestamp()
                os.remove(config_lock_path)
                lockWaitCount+=1
            if lockWaitCount % 10 == 0:
                print '%s [Write Config] Waiting to gain config lock for %s seconds...' % (Timestamp(), lockWaitCount)
            time.sleep(1)
            lockWaitCount+=1
        else:
            waitingForLock = 0
            print '%s [Write Config] Gained lock, writing lock file %s' % (Timestamp(), config_lock_path)
            print '%s [Write Config] Writing config file %s' % (Timestamp(), config_file)
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

            config.add_section('Conditions')
            config.set('Conditions', 'mintemp', minTemp)
            config.set('Conditions', 'maxtemp', maxTemp)
            config.set('Conditions', 'minhum', minHum)
            config.set('Conditions', 'maxhum', maxHum)
            config.set('Conditions', 'webor', webOR)

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
            config.set('States', 'rheatts', RHeatTS)
            config.set('States', 'rhumts', RHumTS)
            config.set('States', 'rhepats', RHepaTS)
            config.set('States', 'rfants', RFanTS)
            config.set('States', 'wfactor', wfactor)
            config.set('States', 'timeroneseconds', timerOneSeconds)
            config.set('States', 'timertwoseconds', timerTwoSeconds)

            with open(config_file, 'wb') as configfile:
                config.write(configfile)

    if os.path.isfile(config_lock_path):
        print '%s [Write Config] Removing lock file %s' % (Timestamp(), config_lock_path)
        os.remove(config_lock_path)
    else:
        print "%s [Write Config] Unable to remove lock file %s because it doesn't exist!" % (Timestamp(), config_lock_path)

def ConditionsCheck():
    if not webOR:
        # Temperature check    
        if (tempc < minTemp):
            print '%s [Check Conditions] Temperature lower than minTemp: %.2f°C < %s°C min' % (Timestamp(), tempc, minTemp)
            print '%s [Check Conditions] Heating On' % Timestamp()
        elif (tempc > maxTemp):
            print '%s [Check Conditions] Temperature greater than maxTemp: %.2f°C > %s°C max' % (Timestamp(), tempc, maxTemp)
            print '%s [Check Conditions] Cooling On' % Timestamp()
        else:
            print '%s [Check Conditions] Temperature within set range: %s°C min < %.2f°C < %s°C max' % (Timestamp(), minTemp, tempc, maxTemp)

        # Humidity check
        if (humidity < minHum):
            print '%s [Check Conditions] Humidity lower than minHum: %.2f%% < %s%% min' % (Timestamp(), humidity, minHum)
            print '%s [Check Conditions] Humidification On' % Timestamp()
            
        elif (humidity > maxHum):
            print '%s [Check Conditions] Humidity greater than maxHum: %.2f%% > %s%% max' % (Timestamp(), humidity, maxHum)
            print '%s [Check Conditions] Exhaust Fan On' % Timestamp()
        else:
            print '%s [Check Conditions] Humidity within set range: %s%% min < %.2f%% < %s%% max' % (Timestamp(), minHum, humidity, maxHum)
    else:
        print '%s [Check Conditions] Web Override Activated: Relay manipulation suspended.' % Timestamp()

def lockFile(lockfile):
    fd = os.open(lockfile, os.O_CREAT | os.O_TRUNC | os.O_WRONLY)
    try:
        # Request exclusive (EX) non-blocking (NB) advisory lock.
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def CheckVariableName():
    namesOfVariables = ['config_file',
    'tempc',
    'humidity',
    'minTemp',
    'maxTemp',
    'minHum',
    'maxHum',
    'webOR',
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
    'RHeatTS',
    'RHumTS',
    'RHepaTS',
    'RFanTS',
    'wfactor',
    'timerOneSeconds',
    'timerTwoSeconds',
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

    for variable in namesOfVariables:
        if variableName == variable:
            return 1
    
    return 0

def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')
 
menu()
usage()
sys.exit(0)