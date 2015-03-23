#!/usr/bin/python
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
    print '    -c  --configure='
    print '           Set '
    print '    -l  --low=RELAY'
    print '           Set RELAY GPIO Low'
    print '    -h  --high=RELAY'
    print '           Set RELAY GPIO High'
    print '    -s  --set='
    print '           Set'
    print '        --seconds='
    print '           Set'
    print '    -t, --terminate'
    print '           Terminate the communication service and daemon\n'

def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:h:l:s:t', ["configure=", "high", "low", "seconds=", "set=", "terminate"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c", "--configure"):
            c.root.ChangeConditions(int(float(sys.argv[2])), int(float(sys.argv[3])), int(float(sys.argv[4])), int(float(sys.argv[5])), int(float(sys.argv[6])))
            sys.exit(0)
        elif opt in ("-h", "--high"):
            if RepresentsInt(arg) and int(float(arg)) < 9 and int(float(arg)) > 0:
                print '%s [Remote command] Set relay %s GPIO High: Server returned:' % (Timestamp(), arg),
                if c.root.GPIOHigh(arg) == 1:
                    print 'success'
                else:
                    print 'fail'
                sys.exit(0)
            else:
                print 'Error: input must be an integer between 1 and 8'
                sys.exit(1)
        elif opt in ("-l", "--low"):
            if RepresentsInt(arg) and int(float(arg)) < 9 and int(float(arg)) > 0:
                print '%s [Remote command] Set relay %s GPIO Low: Server returned:' % (Timestamp(), arg),
                if c.root.GPIOLow(arg) == 1:
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