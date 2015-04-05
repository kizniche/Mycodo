#!/bin/bash

DATE=$(date +"%Y-%m-%d_%H%M%S")

if [ "$1" != 0 ]; then
/usr/local/bin/gpio -g write $1 $2
fi

sleep 1

raspistill -vf -hf -w 800 -h 600 -o /var/www/mycodo/camera-stills/$DATE.jpg

if [ "$2" == 0 ]; then
TRIGGEROFF=1
else
TRIGGEROFF=0
fi

if [ "$1" != 0 ]; then
/usr/local/bin/gpio -g write $1 $TRIGGEROFF
fi

convert /var/www/mycodo/camera-stills/$DATE.jpg -pointsize 14 -fill white -annotate +20+20 %[exif:DateTimeOriginal] /var/www/mycodo/camera-stills/$DATE.jpg
