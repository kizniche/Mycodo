#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo-client.py - Client for mycodo.py. Communicates with daemonized
#                     mycodo.py to execute commands and receive status.
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

import rpyc
import time
import sys
import getopt
import datetime

c = rpyc.connect("localhost", 18812)

def usage():
    print 'mycodo-client.py: Client for mycodo.py daemon (daemon must be running).\n'
    print 'Usage:  mycodo-client.py [OPTION]...\n'
    print 'Options:'
    print '    -h, --help'
    print '           Display this help and exit'
    print '        --graph Duration ID Sensor'
    print '           See documentation for options'
    print '        --modco2OR sensor state'
    print '           CO2 PID control: 0=enable, 1=disable'
    print '        --modco2PID sensor relay set p i d period'
    print '           Change CO2 PID variables'
    print '        --modhumOR sensor state'
    print '           Humidity PID control: 0=enable, 1=disable'
    print '        --modhumPID sensor relay set p i d period'
    print '           Change Humidity PID variables'
    print '        --modtempOR sensor state'
    print '           Temperature PID control: 0=enable, 1=disable'
    print '        --modtempPID sensor relay set p i d period'
    print '           Change Temperature PID variables'
    print '        --modrelaynames name1 name2 name3 name4 name5 name6 name7 name8'
    print '           Modify relay names (Restrict to a maximum of 12 characters each)'
    print '        --modrelaypins pin1 pin2 pin3 pin4 pin5 pin6 pin7 pin8'
    print '           Modify relay pins Using BCM numbering)'
    print '        --modrelaytrigger trig1 trig2 trig3 trig4 trig5 trig6 trig7 trig8'
    print '           Modify the relay trigger states (0=low, 1=high; turns relay on)'
    print '        --modco2sensor sensor name device pin period activated graph'
    print '           Modify CO2 sensor variables'
    print '        --modhtsensor sensor name device pin period activated graph'
    print '           Modify Humidity/Temperature sensor variables'
    print '        --modtimer timer state relay on off'
    print '           Modify custom timers, State can be 0=off 1=on, on/off durations in seconds'
    print '    -m, --modvar name1 value1 [name2] [value2]...'
    print '           Modify any configuration variable or variables (multiple allowed, must be paired input)'
    print '    -r, --relay relay state'
    print '           Turn a relay on or off. state can be 0, 1, or X.'
    print '           0=OFF, 1=ON, or X number of seconds On'
    print '        --sensorco2 pin device'
    print '           Returns a reading from the CO2 sensor on GPIO pin'
    print '           Device options are K30'
    print '        --sensorht pin device'
    print '           Returns a reading from the temperature and humidity sensor on GPIO pin'
    print '           Device options are DHT22, DHT11, or AM2302'
    print '    -t, --terminate'
    print '           Terminate the communication service and daemon'
    print '        --writeco2log sensor'
    print '           Read from CO2 sensor number and append log file, 0 to write all.'
    print '        --writehtlog sensor'
    print '           Read from HT sensor number and append log file, 0 to write all.'

def menu():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hm:r:t', 
            ["help", "graph", "modtempOR", "modtempPID", "modhumOR", "modhumPID", "modco2OR", "modco2PID", "modrelaynames=", "modrelaypins=", "modrelaytrigger=", "modhtsensor", "modco2sensor", "modtimer=", "modvar=", "relay=", "sensorht", "sensorco2", "terminate", "writehtlog", "writeco2log"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            return 1
        elif opt == "--graph":
            print "%s [Remote command] Graph: %s %s %s" % (
                Timestamp(), sys.argv[2], sys.argv[3], sys.argv[4])
            print "%s [Remote command] Server returned:" % (
                Timestamp()),
            if c.root.GenerateGraph(sys.argv[2], sys.argv[3], sys.argv[4]) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modvar":
            print "%s [Remote command] Mod Vars: %s" % (
                Timestamp(), sys.argv[1:])
            print "%s [Remote command] Server returned:" % (
                Timestamp()),
            if c.root.Modify_Variables(*sys.argv[1:]) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modco2OR":
            print "%s [Remote command] Change CO2OR of sensor %s to %s: Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3]),
            if c.root.ChangeCO2OR(int(float(sys.argv[2])), int(float(sys.argv[3]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modco2PID":
            print "%s [Remote command] Change CO2 PID of sensor %s: relay: %s set: %s P: %s I: %s D: %s Period: %s Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3],
                sys.argv[4], sys.argv[5], sys.argv[6],
                sys.argv[7], sys.argv[8]),
            if c.root.ChangeCO2PID(int(float(sys.argv[2])),
            int(float(sys.argv[3])), int(float(sys.argv[4])),
            float(sys.argv[5]), float(sys.argv[6]),
            float(sys.argv[7]), int(float(sys.argv[8]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modtempOR":
            print "%s [Remote command] Change TempOR of sensor %s to %s: Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3]),
            if c.root.ChangeTempOR(int(float(sys.argv[2])), int(float(sys.argv[3]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modtempPID":
            print "%s [Remote command] Change Temp PID of sensor %s: relay: %s set: %s P: %s I: %s D: %s Period: %s Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3],
                sys.argv[4], sys.argv[5], sys.argv[6],
                sys.argv[7], sys.argv[8]),
            if c.root.ChangeTempPID(int(float(sys.argv[2])),
                int(float(sys.argv[3])), float(sys.argv[4]),
                float(sys.argv[5]), float(sys.argv[6]),
                float(sys.argv[7]), int(float(sys.argv[8]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modhumOR":
            print "%s [Remote command] Change HumOR of sensor %s to %s: Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3]),
            if c.root.ChangeHumOR(int(float(sys.argv[2])), int(float(sys.argv[3]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modhumPID":
            print "%s [Remote command] Change Hum PID of sensor %s: relay: %s set: %s P: %s I: %s D: %s Period: %s Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3],
                sys.argv[4], sys.argv[5], sys.argv[6],
                sys.argv[7], sys.argv[8]),
            if c.root.ChangeHumPID(int(float(sys.argv[2])),
            int(float(sys.argv[3])), float(sys.argv[4]),
            float(sys.argv[5]), float(sys.argv[6]),
            float(sys.argv[7]), int(float(sys.argv[8]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modco2sensor":
            print "%s [Remote command] Set Sensor %s: %s %s %s %s %s %s: Server returned:" % (
                Timestamp(), 
                sys.argv[2], sys.argv[3], sys.argv[4],
                sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]),
            if c.root.ChangeCO2Sensor(
                int(float(sys.argv[2])), sys.argv[3], sys.argv[4],
                int(float(sys.argv[5])), int(float(sys.argv[6])), int(float(sys.argv[7])), int(float(sys.argv[8]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modhtsensor":
            print "%s [Remote command] Set Sensor %s: %s %s %s %s %s %s: Server returned:" % (
                Timestamp(), 
                sys.argv[2], sys.argv[3], sys.argv[4],
                sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]),
            if c.root.ChangeHTSensor(
                int(float(sys.argv[2])), sys.argv[3], sys.argv[4],
                int(float(sys.argv[5])), int(float(sys.argv[6])), int(float(sys.argv[7])), int(float(sys.argv[8]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modrelaynames":
            print "%s [Remote command] Set Relay Names: %s %s %s %s %s %s %s %s: Server returned:" % (
                Timestamp(), 
                sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], 
                sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9]),
            if c.root.ChangeRelayNames(
                sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], 
                sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9]) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modrelaypins":
            print "%s [Remote command] Set Relay Pins: %s %s %s %s %s %s %s %s: Server returned:" % (
                Timestamp(), int(sys.argv[2]), int(sys.argv[3]), 
                int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), 
                int(sys.argv[7]), int(sys.argv[8]), int(sys.argv[9])),
            if c.root.ChangeRelayPins(
                int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), 
                int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), 
                int(sys.argv[8]), int(sys.argv[9])) == 1: 
                print "Success"
            else: 
                print "Fail"
            sys.exit(0)
        elif opt == "--modtimer":
            print "%s [Remote command] Set Timer %s: State: %s Relay: %s DurOn: %s DurOff: %s: Server returned:" % (
                Timestamp(), int(sys.argv[2]), int(sys.argv[3]), 
                int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])),
            if c.root.ChangeTimer(
                int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), 
                int(sys.argv[5]), int(sys.argv[6])) == 1: 
                print "Success"
            else: 
                print "Fail"
            sys.exit(0)
        elif opt == "--modrelaytrigger":
            print "%s [Remote command] Set Relay Triggers: %s %s %s %s %s %s %s %s: Server returned:" % (
                Timestamp(), int(sys.argv[2]), int(sys.argv[3]), 
                int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), 
                int(sys.argv[7]), int(sys.argv[8]), int(sys.argv[9])),
            if c.root.ChangeRelayTriggers(
                int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), 
                int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), 
                int(sys.argv[8]), int(sys.argv[9])) == 1: 
                print "Success"
            else: 
                print "Fail"
            sys.exit(0)
        elif opt in ("-r", "--relay"):
            if RepresentsInt(sys.argv[2]) and \
                int(float(sys.argv[2])) > 0:
                if (sys.argv[3] == '0' or sys.argv[3] == '1'):
                    print "%s [Remote command] Set relay %s to %s: Server returned:" % (
                        Timestamp(), int(float(sys.argv[2])), int(float(sys.argv[3]))),
                    if c.root.ChangeRelay(int(float(sys.argv[2])), 
                            int(float(sys.argv[3]))) == 1:
                        print 'success'
                    else:
                        print 'fail'
                    sys.exit(0)
                if (sys.argv[2] > 1):
                    print '%s [Remote command] Relay %s ON for %s seconds: Server returned:' % (
                        Timestamp(), int(float(sys.argv[2])), int(float(sys.argv[3]))),
                    if c.root.ChangeRelay(int(float(sys.argv[2])),
                            int(float(sys.argv[3]))) == 1:
                        print "Success"
                    else:
                        print "Fail"
                    sys.exit(0)
            else:
                print 'Error: second input must be an integer greater than 0'
                sys.exit(1)
        elif opt in ("--sensorco2"):
            print "%s [Remote command] Read CO2 sensor %s on GPIO pin %s" % (
                Timestamp(), sys.argv[3], int(float(sys.argv[2])))
            temperature, humidity = c.root.ReadCO2Sensor(int(float(sys.argv[2])), sys.argv[3])
            print "%s [Remote Command] Daemon Returned: CO2: %s" % (Timestamp(), co2)
            sys.exit(0)
        elif opt in ("--sensorht"):
            print "%s [Remote command] Read HT sensor %s on GPIO pin %s" % (
                Timestamp(), sys.argv[3], int(float(sys.argv[2])))
            temperature, humidity = c.root.ReadHTSensor(int(float(sys.argv[2])), sys.argv[3])
            print "%s [Remote Command] Daemon Returned: Temperature: %s°C Humidity: %s%%" % (Timestamp(), round(temperature,2), round(humidity,2))
            sys.exit(0)
        elif opt in ("-t", "--terminate"):
            print "%s [Remote command] Terminate all threads and daemon: Server returned:" % (
                Timestamp()),
            if c.root.Terminate(1) == 1: print "Success"
            else: print "Fail"
            sys.exit(0)
        elif opt in ("--writeco2log"):
            if int(float(sys.argv[2])):
                print "%s [Remote Command] Append CO2 sensor log from sensor %s: Server returned:" % (
                    Timestamp(), sys.argv[2]),
            else:
                print "%s [Remote Command] Append CO2 sensor log from all sensors: Server returned:" % (
                    Timestamp()),
            if c.root.WriteCO2SensorLog(int(float(sys.argv[2]))) == 1: print "Success"
            else: print "Fail"
            sys.exit(0)
        elif opt in ("--writehtlog"):
            if int(float(sys.argv[2])):
                print "%s [Remote Command] Append HT sensor log from sensor %s: Server returned:" % (
                    Timestamp(), sys.argv[2]),
            else:
                print "%s [Remote Command] Append HT sensor log from all sensors: Server returned:" % (
                    Timestamp()),
            if c.root.WriteHTSensorLog(int(float(sys.argv[2]))) == 1: print "Success"
            else: print "Fail"
            sys.exit(0)
        else:
            assert False, "Fail"
    usage()
    sys.exit(1)

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')

if len(sys.argv) == 1: # No arguments given
    usage()
    sys.exit(1)

menu()
sys.exit(0)