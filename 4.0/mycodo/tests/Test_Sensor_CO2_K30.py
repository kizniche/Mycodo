#!/usr/bin/python
# coding=utf-8

import time
from datetime import datetime

import serial

ser = serial.Serial("/dev/ttyAMA0")
ser.flushInput()
time.sleep(2)

while True:
    ser.write("\xFE\x44\x00\x08\x02\x9F\x25")
    time.sleep(.01)
    resp = ser.read(7)
    high = ord(resp[3])
    low = ord(resp[4])
    co2 = (high * 256) + low
    print("[{:%Y-%m-%d %H:%M:%S}] CO2 = {} ppmv = {} %".format(datetime.now(), co2, co2 / 10000))
    time.sleep(2)
