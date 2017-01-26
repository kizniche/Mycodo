#!/usr/bin/python
# coding=utf-8
#
# Test-Sensor-HT-DHT.py - Read from the DHT sensor
#
#

import sys
import time
import RPi.GPIO as GPIO

location = 26

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(location, GPIO.OUT)
    GPIO.output(location, 1)

    on = 0
    off = 0

    while True:
        try:
            if GPIO.input(location):
                on += 1
            else:
                off += 1
            print("Off: {}, On: {}".format(off, on))
            time.sleep(0.1)
        except Exception as e:
            print("Program terminated. Cleaning up GPIOs. Exception: "
                  "{err}".format(err=e))
            GPIO.cleanup(location)
            sys.exit()

except Exception as e:
    print("ERROR: {err}".format(err=e))
