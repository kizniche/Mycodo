#!/usr/bin/python
# coding=utf-8

import time

for x in range(0, 10):
    tempFile = open('/sys/class/thermal/thermal_zone0/temp')
    temp = float(tempFile.read())
    tempC = temp / 1000
    print("Raspberry Pi Temperature: %.2fC" % tempC)
    time.sleep(2)
