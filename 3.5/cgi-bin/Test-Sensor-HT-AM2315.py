#!/usr/bin/python

import datetime
import time
from tentacle_pi.AM2315 import AM2315
am = AM2315(0x5c,"/dev/i2c-1")

def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('[%Y-%m-%d %H:%M:%S]')

for x in range(0,10):
    temperature, humidity, crc_check = am.sense()
    print "temperature: %s" % temperature
    print "humidity: %s" % humidity
    print "crc: %s" % crc_check
    time.sleep(2)
