#!/usr/bin/python
# rpyc client
import rpyc
import time
import sys
import getopt
import datetime

conn = rpyc.connect("localhost", 12345)
c = conn.root

def usage():
    print 'l for all GPIO Low'

def menu():
    if len(sys.argv) == 1: # No arguments given
        usage()
        sys.exit(1)
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'lt', ["low", "time"])
    except getopt.GetoptError as err:
        print(err) # will print "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-l", "--low"):
            print '%s [Remote command] All GPIOs Low' % Timestamp()
            print '%s [Remote response] Returned:' % Timestamp(),
            if c.GPIOLow(lambda x: x) == 1: print 'Success'
            else: print 'Fail'
            sys.exit(0)
        elif opt in ("-t", "--time"):
            print '%s [Remote command] What second timer on?' % Timestamp()
            print '%s [Remote response] update = %s' % (Timestamp(), c.get_main_update())
            sys.exit(0)
        else:
            assert False, "Fail"


def Timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d %H %M %S')

menu()
usage()
sys.exit(0)