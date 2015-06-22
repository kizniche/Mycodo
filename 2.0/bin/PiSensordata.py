#!/usr/bin/python

import subprocess
import re
import os
import sys
import time
import datetime
import getopt

def usage():
  print "Usage:", __file__, "[OPTION] [FILE]..."
  print "Reads temperature and humidity from sensors.\n"
  print "data is presented in the following format:"
  print "Year Month Day Hour Minute Second Timestamp Humidity TempC TempF DewPoint HeatIndex\n"
  print "Options:\n"
  print "    -d     display calculated data"
  print "    -w, --write=FILE"
  print "           write data to file and print to screen"
  print "    -h, --help"
  print "           display this help and exit\n"

if len(sys.argv) == 1:
  usage()
  sys.exit(1)

def main(argv):
  try:                                
    opts, args = getopt.getopt(argv, "hw:d", ["help", "write="])
  except getopt.GetoptError:          
    usage()                         
    sys.exit(2)                     
  for opt, arg in opts:                
    if opt in ("-h", "--help"):      
      usage()                     
      sys.exit(0)                  
    elif opt == '-d':                
      global disp               
      disp = 0                  
    elif opt in ("-w", "--write"): 
      disp = 1
      global writefile
      writefile = arg

main(sys.argv[1:])

if not os.geteuid() == 0:
  print __file__, "-h for help options"
  sys.exit('Script must be run as root.')

loop = 1
chktemp = 0
while(loop):
  # Run the DHT program to get the humidity and temperature readings!
  # if two temperature readings aren't within a few degrees, compare two more times until they do
  # catches the majority of errors

  output = subprocess.check_output(["/var/www/bin/DHT_Read", "2302", "4"]);
  if (disp): print output
  matches = re.search("Temp =\s+([0-9.]+)", output)
  if (not matches):
        chktemp = 0
	time.sleep(3)
	continue
  tempc = float(matches.group(1))
  tempf = float(matches.group(1))*9/5+32

  # search for humidity printout
  matches = re.search("Hum =\s+([0-9.]+)", output)
  if (not matches):
        chktemp = 0
	time.sleep(3)
	continue
  humidity = float(matches.group(1))
  dewpoint = (tempc - ((100 - humidity)/ 5))*9/5+32
  heatindex =  -42.379 + 2.04901523 * tempf + 10.14333127 * humidity - 0.22475541 * tempf * humidity - 6.83783 * 10**-3 * tempf**2 - 5.481717 * 10**-2 * humidity**2 + 1.22874 * 10**-3 * tempf**2 * humidity + 8.5282 * 10**-4 * tempf * humidity**2 - 1.99 * 10**-6 * tempf**2 * humidity**2
  timestamp = time.time()-1

  if (not chktemp):
    tempf2 = tempf
    chktemp = 1
    time.sleep(3)
    continue

  if (abs(tempf2-tempf) > 4):
    chktemp = 0
    print "sucessive Temp readings more than 4 degrees apart- reread until less than 3\n"
    time.sleep(3)
    continue

  if (disp):
    print datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    print "%.0f" % timestamp
    print "Humidity:    %.1f %%" % humidity
    print "Temperature: %.1f C" % tempc
    print "Temperature: %.1f F" % tempf
    print "Heat Index:  %.1f F" % heatindex
    print "Dew Point:   %.1f F" % dewpoint

    # Append the data in the file, including a timestamp
    try:
      open(writefile, 'ab').write('{0} {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f} {6:.1f}\n'.format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), timestamp, humidity, tempc, tempf, dewpoint, heatindex))
      print "Data appended to", writefile
    except:
      print "Unable to append data."
      sys.exit()
  else:
    print "{0} {1:.0f} {2:.1f} {3:.1f} {4:.1f} {5:.1f} {6:.1f}".format(datetime.datetime.now().strftime("%Y %m %d %H %M %S"), timestamp-1, humidity, tempc, tempf, dewpoint, heatindex)
  loop = 0
