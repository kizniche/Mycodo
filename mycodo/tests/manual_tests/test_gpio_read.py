#!/usr/bin/python
# coding=utf-8
#
# Test-Sensor-HT-DHT.py - Read from the DHT sensor
#
# Usage:
# ./Test-Sensor-HT-DHT.py [sensor] [pin]
#
# Where sensor can be DHT11, DHT22, or AM2302
# Where pin is the GPIO (BCM numbering) connected to the sensor data pin

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

    while(1):
        state = GPIO.input(location)
        if state == 0:
            off += 1
        else:
            on += 1

        print("Off: {}, On: {}".format(off, on))
        try:
            time.sleep(0.1)
        except:
            print("Program terminated. Cleaning up GPIOs.")
            GPIO.cleanup(location)
            sys.exit()

except Exception as msg:
    print("ERROR: {}".format(msg))
