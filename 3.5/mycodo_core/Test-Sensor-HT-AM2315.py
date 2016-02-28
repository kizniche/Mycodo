#!/usr/bin/python

import datetime
import time
from tentacle_pi.AM2315 import AM2315
am = AM2315(0x5c,"/dev/i2c-1")

for x in range(0,10):
    temperature, humidity, crc_check = am.sense()
    print "Temperature: %s" % temperature
    print "Humidity: %s" % humidity
    print "CRC: %s" % crc_check
    time.sleep(2)
