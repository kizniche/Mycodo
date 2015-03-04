#!/bin/bash

while true
do
	/var/www/mycodo/mycodo `/var/www/mycodo/mycodo-sense.py -d`
	wait
done
