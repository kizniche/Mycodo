#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  camera-hdr.py - 
#
#  Kyle Gabriel (2012 - 2015)
#

#### Configure Install Directory ####
install_directory = "/var/www/mycodo"


hdr_dir = "%s/camera-hdr/" % install_directory

import sys
import time
import datetime
import picamera
from fractions import Fraction

# Timestamp format used in sensor and relay logs
def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')

def main():
    timest = Timestamp()
    
    for i in range(1, 31, 10):
        print i * 100000
        with picamera.PiCamera() as camera:
            camera.resolution = (1280, 720)
            camera.hflip = True
            camera.vflip = True
            camera.framerate = Fraction(1, 6)
            camera.shutter_speed = i * 100000
            camera.exposure_mode = 'off'
            camera.iso = 800
            #camera.exposure_compensation = 3
            #camera.exposure_mode = 'spotlight'
            #camera.meter_mode = 'matrix'
            #camera.image_effect = 'gpen'
            # Give the camera some time to adjust to conditions
            time.sleep(5)
            hdr_file = "%s%s-%s-hdr.jpg" % (hdr_dir, timest, i)
            camera.capture(hdr_file)
            camera.close()

main()
sys.exit(0)

