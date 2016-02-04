#!/usr/bin/python

import datetime
import time
from sht_sensor import Sht

sht = Sht(4, 17)

for x in range(0, 10):

    temperature = sht.read_t()
    humidity = sht.read_rh()

    print "Temperature: %s" % temperature
    print "Humidity: %s" % humidity
    time.sleep(2)