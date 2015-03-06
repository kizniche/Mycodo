#!/bin/bash

while true
do
	/var/www/mycodo/cgi-bin/mycodo `/var/www/mycodo/cgi-bin/sense.py -d`
	wait
done
