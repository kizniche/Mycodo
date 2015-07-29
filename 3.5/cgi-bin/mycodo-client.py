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

# Server status check

import rpyc
import time
import sys
import getopt
import datetime

def usage():
    print 'mycodo-client.py: Client for mycodo.py daemon (daemon must be running).\n'
    print 'Usage:  mycodo-client.py [OPTION]...\n'
    print 'Options:'
    print '    -h, --help'
    print '           Display this help and exit'
    print '        --graph Duration ID Sensor'
    print '           See documentation for options'
    print '        --pidstart Coctroller Number'
    print '           Start PID Controller, Controller=Temp, Hum, CO2 and Number=1-4'
    print '        --pidstop Coctroller Number'
    print '           Stop PID Controller, Controller=Temp, Hum, CO2 and Number=1-4'
    print '    -r, --relay relay state'
    print '           Turn a relay on or off. state can be 0, 1, or X.'
    print '           0=OFF, 1=ON, or X number of seconds On'
    print '        --sensorco2 pin device'
    print '           Returns a reading from the CO2 sensor on GPIO pin'
    print '           Device options: K30'
    print '        --sensorht pin device'
    print '           Returns a reading from the temperature and humidity sensor on GPIO pin'
    print '           Device options: DHT22, DHT11, or AM2302'
    print '        --sensort pin device'
    print '           Returns a reading from the temperature and humidity sensor on GPIO pin'
    print '           Device options: DS18B20'
    print '        --sqlreload relay'
    print '           Reload the SQLite database, initialize GPIO if relay=1-8'
    print '    -s, --status'
    print '           Return the status of the server'
    print '    -t, --terminate'
    print '           Terminate the communication service and daemon'
    print '        --writeco2log sensor'
    print '           Read from CO2 sensor number and append log file, 0 to write all.'
    print '        --writetlog sensor'
    print '           Read from T sensor number and append log file, 0 to write all.'
    print '        --writehtlog sensor'
    print '           Read from HT sensor number and append log file, 0 to write all.'

def menu():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hr:st',
            ["help", "graph", "pidstart=", "pidstop=", "relay=", "sensorco2", "sensorht", "sensort", "sqlreload", "status", "terminate", "writetlog", "writehtlog", "writeco2log"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)

    c = rpyc.connect("localhost", 18812)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            return 1
        elif opt == "--graph":
            print "%s [Remote command] Graph: %s %s %s %s %s" % (
                Timestamp(), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
            print "%s [Remote command] Server returned:" % (
                Timestamp()),
            if c.root.GenerateGraph(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--pidstart":
            if (sys.argv[2] != 'TTemp' and sys.argv[2] != 'HTTemp' and sys.argv[2] != 'HTHum' and sys.argv[2] != 'CO2'):
                print "'%s' is not a valid option. Use 'TTemp', 'HTTemp', 'HTHum', or 'CO2'" % sys.argv[2]
                sys.exit(0)
            if (int(float(sys.argv[3])) > 4 or int(float(sys.argv[3])) < 1):
                print "'%s' is not a valid option. Options are 1-4." % sys.argv[3]
                sys.exit(0)
            print "%s [Remote command] Start %s PID controller number %s: Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3]),
            reload_status = c.root.PID_start(sys.argv[2], int(float(sys.argv[3])))
            if reload_status == 1:
                print "Success"
            else:
                print "Fail, %s" % reload_status
            sys.exit(1)
        elif opt == "--pidstop":
            if (sys.argv[2] != 'TTemp' and sys.argv[2] != 'HTTemp' and sys.argv[2] != 'HTHum' and sys.argv[2] != 'CO2'):
                print "'%s' is not a valid option. Use 'TTemp', 'HTTemp', 'HTHum', or 'CO2'" % sys.argv[2]
                sys.exit(0)
            if (int(float(sys.argv[3])) > 4 or int(float(sys.argv[3])) < 1):
                print "'%s' is not a valid option. Options are 1-4." % sys.argv[3]
                sys.exit(0)
            print "%s [Remote command] Stop %s PID controller number %s: Server returned:" % (
                Timestamp(), sys.argv[2], sys.argv[3]),
            reload_status = c.root.PID_stop(sys.argv[2], int(float(sys.argv[3])))
            if reload_status == 1:
                print "Success"
            else:
                print "Fail, %s" % reload_status
            sys.exit(1)
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
        elif opt == "--sensorco2":
            print "%s [Remote command] Read CO2 sensor %s on GPIO pin %s" % (
                Timestamp(), sys.argv[3], int(float(sys.argv[2])))
            temperature, humidity = c.root.ReadCO2Sensor(int(float(sys.argv[2])), sys.argv[3])
            print "%s [Remote Command] Daemon Returned: CO2: %s" % (Timestamp(), co2)
            sys.exit(0)
        elif opt == "--sensorht":
            print "%s [Remote command] Read HT sensor %s on GPIO pin %s" % (
                Timestamp(), sys.argv[3], int(float(sys.argv[2])))
            temperature, humidity = c.root.ReadHTSensor(int(float(sys.argv[2])), sys.argv[3])
            print "%s [Remote Command] Daemon Returned: Temperature: %s°C Humidity: %s%%" % (Timestamp(), round(temperature,2), round(humidity,2))
            sys.exit(0)
        elif opt == "--sensort":
            print "%s [Remote command] Read T sensor %s on GPIO pin %s" % (
                Timestamp(), sys.argv[3], int(float(sys.argv[2])))
            temperature, humidity = c.root.ReadHTSensor(int(float(sys.argv[2])), sys.argv[3])
            print "%s [Remote Command] Daemon Returned: Temperature: %s°C" % (Timestamp(), round(temperature,2))
            sys.exit(0)
        elif opt == "--sqlreload":
            if int(float(sys.argv[2])):
                if int(float(sys.argv[2])) > 8:
                    print "Error: Relay selection out of range. Must be 1-8."
                else:
                    print "%s [Remote command] Reload SQLite database and initialize relay %s: Server returned:" % (
                        Timestamp(), int(float(sys.argv[2]))),
                    if c.root.SQLReload(int(float(sys.argv[2]))) == 1:
                        print "Success"
                    else:
                        print "Fail"
            else:
                print "%s [Remote command] Reload SQLite database: Server returned:" % (
                    Timestamp()),
                if c.root.SQLReload(0) == 1:
                    print "Success"
                else:
                    print "Fail"
            sys.exit(0)
        elif opt in ("-s", "--status"):
            print "%s [Remote command] Request Status Report: Server returned:" % (
                Timestamp()),
            output = c.root.Status(1)
            if output[:1] == '1': print "Success"
            else: print "Fail"
            print output
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
        elif opt in ("--writetlog"):
            if int(float(sys.argv[2])):
                print "%s [Remote Command] Append T sensor log from sensor %s: Server returned:" % (
                    Timestamp(), sys.argv[2]),
            else:
                print "%s [Remote Command] Append T sensor log from all sensors: Server returned:" % (
                    Timestamp()),
            if c.root.WriteTSensorLog(int(float(sys.argv[2]))) == 1: print "Success"
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
