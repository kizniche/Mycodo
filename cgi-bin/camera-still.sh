#!/bin/bash

DATE=$(date +"%Y-%m-%d_%H%M%S")

raspistill -vf -hf -w 800 -h 600 -o /var/www/mycodo/camera-stills/$DATE.jpg

convert /var/www/mycodo/camera-stills/$DATE.jpg -pointsize 14 -fill white -annotate +20+20 %[exif:DateTimeOriginal] /var/www/mycodo/camera-stills/$DATE.jpg
