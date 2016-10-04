#!/usr/bin/python
# coding=utf-8

from datetime import datetime
import RPi.GPIO as GPIO
import os
import sys
import time

from tentacle_pi.AM2315 import AM2315


if not os.geteuid() == 0:
    print("Error: Script must be executed as root.\n")
    sys.exit(1)

if GPIO.RPI_REVISION in [2, 3]:
    I2C_device = "/dev/i2c-1"
else:
    I2C_device = "/dev/i2c-0"

am = AM2315(0x5c, I2C_device)

now = time.time()
fault = None
faultreset = True
count = 0

date_format = '%Y-%m-%d %H:%M:%S'

while 1:
    temperature, humidity, crc_check = am.sense()
    print("Temperature: {}, Humidity: {}, CRC: {}".format(temperature, humidity, crc_check))

    if count:
        date_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        date_fault = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fault))
        print("Test started: {}, faults: {}, last: {}".format(date_now, count, date_fault))
        print("Total time until fault: {} hours".format((fault-now)/60/60))

    # Only record date of first fault after a successful read
    # Determines time since sensor became completely unresponsive
    if crc_check == 1:
    	faultreset = True
    elif crc_check != 1 and faultreset:
        count += 1
    	faultreset = False
    	fault = time.time()
    
    time.sleep(6)
