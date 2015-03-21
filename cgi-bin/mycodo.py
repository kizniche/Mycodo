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

config_file = '/var/www/mycodo/config/mycodo.cfg'
sensor_log_file = '/var/www/mycodo/log/sensor.log'
relay_log_file = '/var/www/mycodo/log/relay.log'

# Change the following sensor and pin to your configuration
# Sensor value can be Adafruit_DHT.DHT11, Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302
sensor = Adafruit_DHT.DHT22
DHTpin = 4

# GPIO pins using BCM numbering
relay1Pin = 14
relay2Pin = 15
relay3Pin = 18
relay4Pin = 23
relay5Pin = 24
relay6Pin = 25
relay7Pin = 8
relay8Pin = 7

log_file = ''
chktemp = ''
tempc = ''
tempf = ''
humidity = ''
dewpointc = ''
dewpointf = ''
heatindex =  ''
tstamp = ''
minTemp = ''
maxTemp = ''
minHum = ''
maxHum = ''
webOR = ''
tempState = ''
humState = ''
relay1o = ''
relay2o = ''
relay3o = ''
relay4o = ''
relay5o = ''
relay6o = ''
relay7o = ''
relay8o = ''
RHeatTS = ''
RHumTS = ''
RHepaTS = ''
RFanTS = ''
wfactor = ''

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
  print '    -w, --write=FILE'
  print '           write sensor data to log file'
  print '    -c, --change=RELAY'
  print '           change the state of a relay (must use with -s)'
  print '    -s, --state=[0][1]'
  print '           change the state of RELAY to on(1) or off(0)'
  print '    -d, --daemon'
  print '           start program as daemon that monitors conditions and modulates relays'
  print '    -h, --help'
  print '           display this help and exit\n'

def setup():
  # Set up GPIO using BCM numbering
  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)

  print "%s Setting GPIOs as outputs" % timestamp()
  GPIO.setup(relay1Pin, GPIO.OUT)
  GPIO.setup(relay2Pin, GPIO.OUT)
  GPIO.setup(relay3Pin, GPIO.OUT)
  GPIO.setup(relay4Pin, GPIO.OUT)
  GPIO.setup(relay5Pin, GPIO.OUT)
  GPIO.setup(relay6Pin, GPIO.OUT)
  GPIO.setup(relay7Pin, GPIO.OUT)
  GPIO.setup(relay8Pin, GPIO.OUT)

  print "%s Setting GPIOs LOW" % timestamp()
  GPIO.output(relay1Pin, GPIO.LOW)
  GPIO.output(relay2Pin, GPIO.LOW)
  GPIO.output(relay3Pin, GPIO.LOW)
  GPIO.output(relay4Pin, GPIO.LOW)
  GPIO.output(relay5Pin, GPIO.LOW)
  GPIO.output(relay6Pin, GPIO.LOW)
  GPIO.output(relay7Pin, GPIO.LOW)
  GPIO.output(relay8Pin, GPIO.LOW)
  
def main():
  # No arguments given
  if len(sys.argv) == 1:
    usage()
    sys.exit(1)
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], 'thrdw:c:s:', ["help", "read", "write=", "change=", "state=", "daemon"])
  except getopt.GetoptError as err:
    print(err) # will print "option -a not recognized"
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit(0)
    elif opt in ("-r", "--read"):
      readSensors()
      sys.exit(0)
    elif opt in ("-w", "--write"):
      global log_file
      log_file = arg
      readSensors()
      writeSensorLog()
      sys.exit(0)
    elif opt in ("-c", "--change"):
      global relay_change
      relay_change = arg
      if relay_change > '8' or relay_change < '1':
        print 'Error: 1 - 8 are the only acceptable options for -c'
        usage()
        sys.exit(0)
    elif opt in ("-s", "--state"):
      global relay_state
      relay_state = arg
      if relay_state == '0' or relay_state == '1':
        print '%s Requested change of relay %s to' % (timestamp(), relay_change),
        if relay_state == '1':
          print 'On'
        elif relay_state == '0':
          print 'Off'
      else:
        print 'Error: 0 or 1 are the only acceptable options for -s'
        usage()
      sys.exit(0)
    elif opt in ("-d", "--daemon"):
      setup()
      runDaemon()
    else:
      assert False, "Fail"

def runDaemon():
  loop = 1
  print '%s Daemon activated' % timestamp()
  while(loop):
    readCfg()
    readSensors()
    conditionsCheck()
    print '%s Sleep 90 seconds' % timestamp()
    time.sleep(90)

# Append the data in the file
def writeSensorLog():
  global sensor_log_file
  try:
    open(log_file, 'ab').write('{0} {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f}\n'.format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), tstamp, humidity, tempc, dewpointc, heatindex))
    print '%s Data appended to %s' % (timestamp(), sensor_log_file)
  except:
    print '%s Unable to append data' % timestamp()

def readSensors():
  global tempc
  global tempf
  global humidity
  global dewpointc
  global dewpointf
  global heatindex
  global tstamp
  global chktemp
  chktemp = 1

  print '%s Begin reading sensors' % timestamp()
  print '%s Temperature/humidity reading one...' % timestamp(),
  humidity2, tempc2 = Adafruit_DHT.read_retry(sensor, DHTpin)
  print '%.2f°C, %.2f%%' % (tempc2, humidity2)
  time.sleep(3);
  print '%s Temperature/humidity reading two...' % timestamp(),

  while(chktemp):
    humidity, tempc = Adafruit_DHT.read_retry(sensor, DHTpin)
    print '%.2f°C, %.2f %%' % (tempc2, humidity2)
    print '%s Differences: %.2f°C, %.2f%%' % (timestamp(), abs(tempc2-tempc), abs(humidity2-humidity))
    if (abs(tempc2-tempc) > 1 and abs(humidity2-humidity) > 1):
      tempc2 = tempc
      humidity2 = humidity
      chktemp = 1
      print "%s Successive readings >1 difference: Wait 3 sec to stabilize: rereading..." % timestamp(),
      time.sleep(3)
    else:
      chktemp = 0
      print "%s Successive readings <1 difference: keeping." % timestamp()
      tempf = float(tempc)*9/5+32
      dewpointc = tempc - ((100 - humidity)/ 5)
      dewpointf = (tempc - ((100 - humidity)/ 5))*9/5+32
      heatindex =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
      heatindex = (heatindex - 32) * (5.0 / 9.0)
      tstamp = time.time()-1
      print "{0} {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f}".format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), tstamp-1, humidity, tempc, dewpointc, heatindex)

def readCfg():
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

  print '%s Begin reading configuration file' % timestamp()
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

  print '%s Reading conditions' % timestamp()
  print '%s minTemp: %s°C, maxTemp: %s°C, minHum: %s%%, maxHum: %s%%, webOR: %s' % (timestamp(), minTemp, maxTemp, minHum, maxHum, webOR)
  print '%s Reading states' % timestamp()
  print '%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %.1f'  % (timestamp(), tempState, humState, relay1o, relay2o, relay3o, relay4o, relay5o, relay6o, relay7o, relay8o, RHeatTS, RHumTS, RHepaTS, RFanTS, wfactor)

def writeCfg():
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

def conditionsCheck():
  if not webOR:
    # Temperature check
    if (tempc < minTemp):
      print '%s Temperature lower than minTemp: %.2f°C < %s°C min' % (timestamp(), tempc, minTemp)
      print '%s Heating On' % timestamp()
    elif (tempc > maxTemp):
      print '%s Temperature greater than maxTemp: %.2f°C > %s°C max' % (timestamp(), tempc, maxTemp)
      print '%s Cooling On' % timestamp()
    else:
      print '%s Temperature within set range: %s°C min < %.2f°C < %s°C max' % (timestamp(), minTemp, tempc, maxTemp)

    # Humidity check
    if (humidity < minHum):
      print '%s Humidity lower than minHum: %.2f%% < %s%% min' % (timestamp(), humidity, minHum)
      print '%s Humidification On' % timestamp()
    elif (humidity > maxHum):
      print '%s Humidity greater than maxHum: %.2f%% > %s%% max' % (timestamp(), humidity, maxHum)
      print '%s Exhaust Fan On' % timestamp()
    else:
      print '%s Humidity within set range: %s%% min < %.2f%% < %s%% max' % (timestamp(), minHum, humidity, maxHum)
  else:
    print '%s Web Override Activated: Relay manipulation suspended.' % timestamp()

def timestamp():
  return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')
 
main()
usage()
sys.exit(0)