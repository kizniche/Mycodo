#!/usr/bin/python
# coding=utf-8

import time
from datetime import datetime

import serial

ser = serial.Serial("/dev/ttyS0")
ser.flushInput()
time.sleep(2)

while True:
    ser.write(bytearray([0xfe, 0x44, 0x00, 0x08, 0x02, 0x9f, 0x25]))
    time.sleep(.01)
    resp = ser.read(7)
    high = resp[3]
    low = resp[4]
    co2 = (high * 256) + low
    print("[{:%Y-%m-%d %H:%M:%S}] CO2 = {} ppmv = {} %".format(datetime.now(), co2, co2 / 10000))
    time.sleep(2)
