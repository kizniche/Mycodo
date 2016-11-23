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

location = 25

def edge_detected(test):
    print("Detected Edge {}".format(test))

try:
    GPIO.setmode(GPIO.BCM)
    # GPIO.setwarnings(False)
    GPIO.setup(location, GPIO.IN)
    GPIO.add_event_detect(location,
                          GPIO.BOTH,
                          callback=edge_detected,
                          bouncetime=1)

    while(1):
        try:
            time.sleep(1)
        except:
            print("Program terminated. Cleaning up GPIOs.")
            GPIO.cleanup(location)
            sys.exit()

except Exception as msg:
    print("ERROR: {}".format(msg))
