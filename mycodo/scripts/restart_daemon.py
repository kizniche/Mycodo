#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import os
import logging
import time

DAEMON_PID_FILE = '/var/lock/mycodo.pid'
LOG_FILE = '/var/log/mycodo/mycodokeepup.log'


def check_daemon(print_msg=True):
    if os.path.exists(DAEMON_PID_FILE):
        with open(DAEMON_PID_FILE, 'r') as pid_file:
            if not os.path.exists("/proc/{pid}".format(pid=pid_file.read())):
                message = "Daemon is not running, restarting"
                logging.info(message)
                print(message)
                try:
                    os.remove(DAEMON_PID_FILE)
                    rcode = os.system('/usr/sbin/service mycodo restart')
                    if rcode != 0:
                        logging.error("Unable to execute restart command {}".format(rcode))
                except OSError as e:
                    logging.warn("Unable to remove pid file: {}".format(e))
            else:
                if print_msg:
                    message = "Daemon is currently running"
                    logging.info(message)
                    print(message)
    elif print_msg:
        print("Mycodo previously shut down properly")


def parseargs(parser):
    parser.add_argument('-c', '--continuouscheck', action='store_true',
                        help="Continually check if the daemon has crashed and start it")
    return parser.parse_args()


if __name__ == '__main__':
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename=LOG_FILE, format=format, level=logging.DEBUG)
    parser = argparse.ArgumentParser(
        description="Script to check if the Mycodo daemon has crashed and "
                    "restart it if so.")
    args = parseargs(parser)

    if args.continuouscheck:
        while True:
            check_daemon()
            time.sleep(5)
    else:
        check_daemon(print_msg=True)
