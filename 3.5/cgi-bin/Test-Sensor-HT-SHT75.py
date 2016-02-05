#!/usr/bin/python

import datetime
import time
from sht_sensor import Sht

sht = Sht(4, 17)

for x in range(0, 10):

    temperature = sht.read_t()
    humidity = sht.read_rh(temperature)
    dew_point = sht.read_dew_point(temperature, humidity)

    print "Temperature: %s" % temperature
    print "Humidity: %s" % humidity
    print "Dew Point: " % dew_point
    time.sleep(2)