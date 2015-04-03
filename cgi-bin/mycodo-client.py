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
    print 'Usage:  mycodo-client.py [OPTION]...\n'
    print 'Options:'
    print '        --modnames [r1NAME] [r2NAME] [r3NAME] [r4NAME] [r5NAME] [r6NAME] [r7NAME] [r8NAME]'
    print '           Modify relay names (Restrict to a maximum of 5 characters each)'
    print '        --modpins [r1PIN] [r2PIN] [r3PIN] [r4PIN] [r5PIN] [r6PIN] [r7PIN] [r8PIN]'
    print '           Modify relay pins (Using BCM numbering)'
    print '        --modtrigger [r1T] [r2T] [r3T] [r4T] [r5T] [r6T] [r7T] [r8T]'
    print '           Modify the trigger state of relays'
    print '    -r, --relay [RELAY] [1/0]'
    print '           Set RELAY pin high (1) or low (0)'
    print '    -s, --set [RELAY] [SECONDS] [TRIGGER]'
    print '           Set relay on for a number of seconds'
    print '           for [TRIGGER], if ON is High/5vDC set to 1, if on is LOW-0vDC set to 0)'
    print '    -t, --terminate'
    print '           Terminate the communication service and daemon\n'
    print '    -w, --writelog'
    print '           Read sensor and append log file'    

def menu():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'o:p:r:s:tw', 
            ["modnames=", "modpins=", "modtrigger=",
            "modvar=", "pid=", "relay=", "set=", "terminate",
            "writelog"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "--modvar":
            print "%s [Remote command] Mod Vars: %s" % (
                Timestamp(), sys.argv[1:])
            print "%s [Remote command] Server returned:" % (
                Timestamp()),
            if c.root.Modify_Variables(*sys.argv[1:]) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--changetempor":
            print "%s [Remote command] Change TempOR to %s: Server returned:" % (
                Timestamp(), sys.argv[2]),
            if c.root.ChangeTempOR(int(float(sys.argv[2]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--changehumor":
            print "%s [Remote command] Change HumOR to %s: Server returned:" % (
                Timestamp(), sys.argv[2]),
            if c.root.ChangeHumOR(int(float(sys.argv[2]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt == "--modnames":
            print "%s [Remote command] Set Names: %s %s %s %s %s %s %s %s: Server returned:" % (
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
        elif opt == "--modpins":
            print "%s [Remote command] Set Pins: %s %s %s %s %s %s %s %s: Server returned:" % (
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
        elif opt == "--modtrigger":
            print "%s [Remote command] Set Triggers: %s %s %s %s %s %s %s %s: Server returned:" % (
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
                int(float(sys.argv[2])) < 9 and \
                int(float(sys.argv[2])) > 0:
                print sys.argv[2]
                print sys.argv[3]
                print "%s [Remote command] Set relay %s GPIO to %s: Server returned:" % (
                    Timestamp(), int(float(sys.argv[2])), int(float(sys.argv[3]))),
                if c.root.ChangeRelay(int(float(sys.argv[2])), 
                    int(float(sys.argv[3]))) == 1: print 'success'
                else: print 'fail'
                sys.exit(0)
            else:
                print 'Error: input must be an integer between 1 and 8'
                sys.exit(1)
        elif opt in ("-s", "--set"):
            relaySelect = int(float(sys.argv[2]))
            relaySeconds = int(float(sys.argv[3]))
            print '%s [Remote command] Relay %s ON for %s seconds: Server returned:' % (
                Timestamp(), int(float(sys.argv[2])), int(float(sys.argv[3]))),
            if c.root.RelayOnSec(int(float(sys.argv[2])),
                    int(float(sys.argv[3]))) == 1:
                print "Success"
            else:
                print "Fail"
            sys.exit(0)
        elif opt in ("-t", "--terminate"):
            print "%s [Remote command] Terminate all threads and daemon: Server returned:" % (
                Timestamp()),
            if c.root.Terminate(1) == 1: print "Success"
            else: print "Fail"
            sys.exit(0)
        elif opt in ("-w", "--logwrite"):
            print "%s [Remote Command] Append sensor log: Server returned:" % (
                Timestamp()), 
            if c.root.WriteSensorLog() == 1: print "Success"
            else: print "Fail"
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

if len(sys.argv) == 1: # No arguments given
    usage()
    sys.exit(1)

menu()
usage()
sys.exit(0)