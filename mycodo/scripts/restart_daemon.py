# -*- coding: utf-8 -*-
import argparse
import logging
import time

import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

from mycodo.config import DAEMON_PID_FILE
from mycodo.config import KEEPUP_LOG_FILE


def check_daemon(print_msg=True, start_daemon=True):
    if os.path.exists(DAEMON_PID_FILE):
        with open(DAEMON_PID_FILE, 'r') as pid_file:
            if not os.path.exists("/proc/{pid}".format(pid=pid_file.read())):
                message = "Daemon is not running, restarting"
                logging.info(message)
                if print_msg:
                    print(message)
                try:
                    os.remove(DAEMON_PID_FILE)
                    if start_daemon:
                        rcode = os.system('/usr/sbin/service mycodo restart')
                        if rcode != 0:
                            logging.error("Unable to execute restart command "
                                          "{}".format(rcode))
                except OSError as e:
                    message = "Unable to remove pid file: {}".format(e)
                    logging.warn(message)
                    if print_msg:
                        print(message)
            else:
                if print_msg:
                    message = "Daemon is currently running"
                    logging.info(message)
                    print(message)
    elif print_msg:
        message = "Mycodo previously shut down properly"
        logging.info(message)
        print(message)


def parseargs(par):
    par.add_argument('-c', '--continuouscheck', action='store_true',
                     help="Continually check if the daemon has crashed and start it")
    par.add_argument('-d', '--deletepid', action='store_true',
                     help="Only delete the PID file if the daemon isn't running. Don't start it.")
    return par.parse_args()


if __name__ == '__main__':
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename=KEEPUP_LOG_FILE, format=log_format, level=logging.DEBUG)
    parser = argparse.ArgumentParser(
        description="Script to check if the Mycodo daemon has crashed and "
                    "restart it if so.")
    args = parseargs(parser)

    if args.continuouscheck:
        print("Beginning monitor of the Mycodo daemon and start it if it is found to not be running")
        while True:
            check_daemon(print_msg=False)
            time.sleep(30)
    elif args.deletepid:
        check_daemon(start_daemon=False)
    else:
        check_daemon()
