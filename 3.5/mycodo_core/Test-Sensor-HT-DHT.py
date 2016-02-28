#!/usr/bin/python
#
# Test-Sensor-HT-DHT.py - Read from the DHT sensor
#
# Usage:
# ./Test-Sensor-HT-DHT.py [sensor] [pin]
#
# Where sensor can be DHT11, DHT22, or AM2302
# Where pin is the GPIO (BCM numbering) connected to the sensor data pin

import os
import sys
import time
import Adafruit_DHT

def usage():
    print 'Test-Sensor-HT-DHT.py - Read from the DHT sensor\n'
    print 'Usage: Test-Sensor-HT-DHT.py sensor pin'
    print 'Where sensor can be DHT11, DHT22, or AM2302'
    print 'Where pin is the GPIO (BCM numbering) connected to the sensor data pin\n'
    print 'Example:'
    print '    ./Test-Sensor-HT-DHT.py DHT22 4'

def read_ht(sensor, pin):
    if (sensor == 'DHT11'): device = Adafruit_DHT.DHT11
    elif (sensor == 'DHT22'): device = Adafruit_DHT.DHT22
    elif (sensor == 'AM2302'): device = Adafruit_DHT.AM2302
    if device == Adafruit_DHT.DHT11 or device == Adafruit_DHT.DHT22 or device == Adafruit_DHT.AM2302:
        for x in range(0,10):
            humidity, temperature = Adafruit_DHT.read_retry(device, pin)
            print "Temperature: %s" % temperature
            print "Humidity: %s" % humidity
            time.sleep(2)
    else:
        return 'Invalid Sensor Name'

if not os.geteuid() == 0:
    print "Error: Script must be executed as root.\n"
    usage()
    sys.exit(1)

elif len(sys.argv) < 3:
    print 'Error: Not enough arguments.\n'
    usage()
    sys.exit(1)
elif sys.argv[1] != 'DHT11' and sys.argv[1] != 'DHT22' and sys.argv[1] != 'AM2302':
    print 'Error: Invalid sensor.\n'
    usage()
    sys.exit(1)
else:
    try:
        pin = int(sys.argv[2])
    except ValueError:
        print 'Error: Invalid GPIO pin.\n'
        usage()
        sys.exit(1)
    if pin < 0 or pin > 40:
        print 'Error: Invalid sGPIO pin.\n'
        usage()
        sys.exit(1)

read_ht(sys.argv[1], int(sys.argv[2]))
