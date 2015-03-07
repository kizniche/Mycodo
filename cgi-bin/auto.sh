#!/bin/bash
#
#  auto.sh - Obtains sensor data and adjusts relays
#  By Kyle Gabriel
#  2012 - 2015
#

while true
do
	/var/www/mycodo/cgi-bin/mycodo `/var/www/mycodo/cgi-bin/sense.py -d`
	wait
done
