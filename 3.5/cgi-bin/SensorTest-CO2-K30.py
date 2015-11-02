#!/usr/bin/python

import datetime
import serial
import time

ser = serial.Serial("/dev/ttyAMA0")
ser.flushInput()
time.sleep(2)

def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('[%Y-%m-%d %H:%M:%S]')

while True:
    ser.write("\xFE\x44\x00\x08\x02\x9F\x25")
    time.sleep(.01)
    resp = ser.read(7)
    high = ord(resp[3])
    low = ord(resp[4])
    co2 = (high*256) + low
    print Timestamp() + " CO2 = " + str(co2) + " ppmv = " + str(float(co2)/10000) + " %"
    time.sleep(2)
