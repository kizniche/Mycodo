#!/usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import ConfigParser

#### Configure Install Directory ####
install_directory = "/var/www/mycodo"


config_file = "%s/config/mycodo.cfg" % install_directory

# GPIO pins (BCM numbering) and name of devices attached to relay
relayPin = [0] * 9
relayName = [0] * 9

def ReadCfg():
    global relayPin

    config = ConfigParser.RawConfigParser()
    config.read(config_file)

    relayPin[1] = config.getint('RelayPins', 'relay1pin')
    relayPin[2] = config.getint('RelayPins', 'relay2pin')
    relayPin[3] = config.getint('RelayPins', 'relay3pin')
    relayPin[4] = config.getint('RelayPins', 'relay4pin')
    relayPin[5] = config.getint('RelayPins', 'relay5pin')
    relayPin[6] = config.getint('RelayPins', 'relay6pin')
    relayPin[7] = config.getint('RelayPins', 'relay7pin')
    relayPin[8] = config.getint('RelayPins', 'relay8pin')

ReadCfg()

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

GPIO.output(relayPin[1], 1)
GPIO.output(relayPin[2], 1)
GPIO.output(relayPin[3], 1)
GPIO.output(relayPin[4], 1)
GPIO.output(relayPin[5], 1)
GPIO.output(relayPin[6], 1)
GPIO.output(relayPin[7], 1)
GPIO.output(relayPin[8], 1)