#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo-client.py - Client for mycodo.py. Communicates with daemonized mycodo.py to
#                     execute commands and receive status. This allows only one
#                     program to run, preventing possible "double-editing" of files
#                     and other risky behavior.
#
#  Kyle Gabriel (2012 - 2015)
#

import rpyc
import time
import sys
import getopt
import datetime

c = rpyc.connect("localhost", 18812)

def usage():
    print 'mycodo-client.py: Communicates with the daemonized mycodo.py.\n'
    print 'Usage:  ', __file__, '[OPTION]...\n'
    print 'Options:'
    print '    -c, --conditions [relayT] [setTemp] [T_P] [T_I] [T_D] [T_sec] [relayHum] [setHum] [H_P] [H_I] [H_D] [H_Sec]'
    print '           Set P, I, I'
    print '        --modnames [r1NAME] [r2NAME] [r3NAME] [r4NAME] [r5NAME] [r6NAME] [r7NAME] [r8NAME]'
    print '           Modify relay names (Restrict to a maximum of 5 characters each)'
    print '        --modpins [r1PIN] [r2PIN] [r3PIN] [r4PIN] [r5PIN] [r6PIN] [r7PIN] [r8PIN]'
    print '           Modify relay pins (Using BCM numbering)'
    print '        --modsensor [SENSOR] [PIN]'
    print '           Modify the DHT sensor and pin'
    print '    -o, --override [TempOR] [HumOR]'
    print '           Set Temperature and Humidity overrides. PID controller stops operating when set to 1'
    print '    -r, --relay [RELAY] [1/0]'
    print '           Set RELAY pin high (1) or low (0)'
    print '    -s, --set='
    print '           Set'
    print '        --seconds='
    print '           Set'
    print '    -t, --terminate'
    print '           Terminate the communication service and daemon\n'
    print '    -w, --writelog'
    print '           Read sensor and append log file'    

def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:o:p:r:s:tw', ["conditions=", "modnames=", "modpins=", "modsensor=", "override=", "pid=", "relay=", "seconds=", "set=", "terminate", "writelog"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-p", "--conditions"):
            print '%s [Remote command] Set conditions: relayT: %s, set: %.1f°C, P: %.1f, I: %.1f, D: %.1f, sec: %s' % (Timestamp(), int(float(sys.argv[2])), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), int(float(sys.argv[7])))
            print '%s [Remote command] Set conditions: relayH: %s, set: %.1f%%,  P: %.1f, I: %.1f, D: %.1f, Sec: %s' % (Timestamp(), int(float(sys.argv[8])), float(sys.argv[9]), float(sys.argv[10]), float(sys.argv[11]), float(sys.argv[12]), int(float(sys.argv[13])))
            print '%s [Remote command] Server returned:' % Timestamp(),
            if c.root.ChangeConditions(int(float(sys.argv[2])), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), int(float(sys.argv[7])), int(float(sys.argv[8])), float(sys.argv[9]), float(sys.argv[10]), float(sys.argv[11]), float(sys.argv[12]), int(float(sys.argv[13]))) == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        elif opt == "--modnames":
            print '%s [Remote command] Set Names: %s %s %s %s %s %s %s %s: Server returned:' % (Timestamp(), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9]),
            if c.root.ChangeRelayNames(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9]) == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        elif opt == "--modpins":
            print '%s [Remote command] Set Pins: %s %s %s %s %s %s %s %s: Server returned:' % (Timestamp(), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]), int(sys.argv[9])),
            if c.root.ChangeRelayPins(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]), int(sys.argv[9])) == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        elif opt == "--modsensor":
            print '%s [Remote command] Set DHT Sensor: %s, Pin: %s: Server returned:' % (Timestamp(), sys.argv[2], int(sys.argv[3]))
            if c.root.ChangeSensor(sys.argv[2], int(sys.argv[3])) == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        elif opt in ("-o", "--override"):
            print '%s [Remote command] Set overrides: TempOR: %s, HumOR: %s: Server returned:' % (Timestamp(), int(float(sys.argv[2])), int(float(sys.argv[3])))
            if c.root.ChangeOverride(int(float(sys.argv[2])), int(float(sys.argv[3]))) == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        elif opt in ("-r", "--relay"):
            if RepresentsInt(sys.argv[2]) and int(float(sys.argv[2])) < 9 and int(float(sys.argv[2])) > 0:
                print sys.argv[2]
                print sys.argv[3]
                print '%s [Remote command] Set relay %s GPIO to %s: Server returned:' % (Timestamp(), int(float(sys.argv[2])), int(float(sys.argv[3]))),
                if c.root.ChangeRelay(int(float(sys.argv[2])), int(float(sys.argv[3]))) == 1:
                    print 'success'
                else:
                    print 'fail'
                sys.exit(0)
            else:
                print 'Error: input must be an integer between 1 and 8'
                sys.exit(1)
        elif opt in ("-s", "--set"):
            relaySelect = arg
        elif opt == "--seconds":
            relaySeconds = arg
            print '%s [Remote command] Relay %s on for %s seconds: Server returned:' % (Timestamp(), relaySelect, relaySeconds),
            if c.root.RelayOnSec(int(float(relaySelect)), int(float(relaySeconds))) == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        elif opt in ("-t", "--terminate"):
            print '%s [Remote command] Terminate all threads and daemon: Server returned:' % Timestamp(),
            if c.root.Terminate(1) == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        elif opt in ("-w", "--logwrite"):
            print '%s [Remote Command] Append sensor log: Server returned:' % Timestamp(), 
            if c.root.WriteSensorLog() == 1:
                print 'Success'
            else:
                print 'Fail'
            sys.exit(0)
        else:
            assert False, "Fail"

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')

menu()
usage()
sys.exit(0)