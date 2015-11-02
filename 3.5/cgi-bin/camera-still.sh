#!/bin/bash
#
#  camera-still.sh - Capture image from the raspberry pi camera and
#                    apply a timestamp.
#
#  Copyright (C) 2015  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

DATE=$(date +"%Y-%m-%d_%H%M%S")

if [ "$1" > 0 ]; then # Turn relay on
	/usr/local/bin/gpio -g write $1 $2
fi

sleep 1

# Getting extra command options
DATABASE="/var/www/mycodo/config/mycodo.db"
EXTRA=`sqlite3 $DATABASE "SELECT Extra_Parameters FROM CameraStill;"`;

if [ ! -z "$EXTRA" ]; then
	/usr/bin/raspistill $EXTRA -o /var/www/mycodo/camera-stills/$DATE.jpg
else
	/usr/bin/raspistill -o /var/www/mycodo/camera-stills/$DATE.jpg
fi


if [ "$1" > 0 ]; then # Turn relay off
	if [ "$2" == 0 ]; then
		TRIGGEROFF=1
	else
		TRIGGEROFF=0
	fi
	/usr/local/bin/gpio -g write $1 $TRIGGEROFF
fi

if [ "$3" == 1 ]; then
	convert /var/www/mycodo/camera-stills/$DATE.jpg -pointsize 14 -fill white \
    	-annotate +20+20 %[exif:DateTimeOriginal] \
    	/var/www/mycodo/camera-stills/$DATE.jpg
else
	convert /var/www/mycodo/camera-stills/$DATE.jpg -pointsize 14 -fill white \
    	/var/www/mycodo/camera-stills/$DATE.jpg
fi
