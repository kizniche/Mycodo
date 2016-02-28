#!/usr/bin/python

import subprocess
import time

for x in range(0,10):
    CPUtempFile = open('/sys/class/thermal/thermal_zone0/temp')
    CPUtempF = float(CPUtempFile.read())
    CPUtempC = CPUtempF/1000
    GPUtempStr = subprocess.check_output(('/opt/vc/bin/vcgencmd','measure_temp'))
    GPUtempC = float(GPUtempStr.split('=')[1].split("'")[0])
    print "CPU Temperature: %.1fC GPU Temperature: %.1fC" % (CPUtempC, GPUtempC)
    time.sleep(2)