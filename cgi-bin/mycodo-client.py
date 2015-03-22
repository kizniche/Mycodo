#!/usr/bin/python

import rpyc
import time
import sys
import getopt
import datetime

c = rpyc.connect("localhost", 18812)

def usage():
    print 'mycodo-client.py: Communicates with the daemonized mycodo.py.\n'
    print 'Usage:  ', __file__, '[OPTION] [FILE]...\n'
    print 'Options:'
    print '    -l  --low'
    print '           Set all relay GPIOs Low'
    print '    -t, --time'
    print '           Return the current timer value of the daemon\n'

def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'tl:h:', ["low", "high", "terminate"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-l", "--low"):
            relay = arg
            print '%s [Remote command] Relay %s GPIO Low' % (Timestamp(), relay)
            print '%s [Remote response] Returned:' % Timestamp(),
            if c.root.GPIOLow(relay) == 1: print 'Success'
            else: print 'Fail'
            sys.exit(0)
        elif opt in ("-h", "--high"):
            relay = arg
            print '%s [Remote command] Relay %s GPIO Low' % (Timestamp(), relay)
            print '%s [Remote response] Returned:' % Timestamp(),
            if c.root.GPIOHigh(relay) == 1: print 'Success'
            else: print 'Fail'
            sys.exit(0)
        elif opt in ("-t", "--terminate"):
            c.root.Terminate(1)
            sys.exit(0)
        else:
            assert False, "Fail"


def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')

menu()
usage()
sys.exit(0)