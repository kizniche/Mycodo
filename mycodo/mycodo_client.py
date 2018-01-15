#!/usr/bin/mycodo-python
# -*- coding: utf-8 -*-
#
#  mycodo_client.py - Client for mycodo daemon. Communicates with daemon
#                     to execute commands and receive status.
#
#  Copyright (C) 2017  Kyle T. Gabriel
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

import argparse
import datetime
import logging
import signal
import socket
import sys

import rpyc

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):  # Custom exception class
    pass


class DaemonControl:
    """
    Communicate with the daemon to execute commands or retrieve information.

    """
    def __init__(self):
        try:
            self.rpyc_client = rpyc.connect("localhost", 18813)
        except socket.error:
            raise Exception("Connection refused. Is the daemon running?")

    def check_daemon(self):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10 second timeout while checking the daemon status
        try:
            result = self.rpyc_client.root.check_daemon()
            if result:
                return result
            else:
                return "GOOD"
        except TimeoutException:
            return "Error: Timeout"

    def controller_activate(self, controller_type, controller_id):
        return self.rpyc_client.root.controller_activate(
            controller_type, controller_id)

    def controller_deactivate(self, controller_type, controller_id):
        return self.rpyc_client.root.controller_deactivate(
            controller_type, controller_id)

    def daemon_status(self):
        return self.rpyc_client.root.daemon_status()

    def lcd_backlight(self, lcd_id, state):
        return self.rpyc_client.root.lcd_backlight(lcd_id, state)

    def lcd_flash(self, lcd_id, state):
        return self.rpyc_client.root.lcd_flash(lcd_id, state)

    def is_in_virtualenv(self):
        return self.rpyc_client.root.is_in_virtualenv()

    def pid_hold(self, pid_id):
        return self.rpyc_client.root.pid_hold(pid_id)

    def pid_mod(self, pid_id):
        return self.rpyc_client.root.pid_mod(pid_id)

    def pid_pause(self, pid_id):
        return self.rpyc_client.root.pid_pause(pid_id)

    def pid_resume(self, pid_id):
        return self.rpyc_client.root.pid_resume(pid_id)

    def ram_use(self):
        return self.rpyc_client.root.ram_use()

    def relay_off(self, relay_id, trigger_conditionals=True):
        return self.rpyc_client.root.relay_off(relay_id, trigger_conditionals)

    def relay_on(self, relay_id, duration=0.0, min_off=0.0,
                 duty_cycle=0.0, trigger_conditionals=True):
        return self.rpyc_client.root.relay_on(
            relay_id, duration=duration, min_off=min_off,
            duty_cycle=duty_cycle, trigger_conditionals=trigger_conditionals)

    def output_on_off(self, relay_id, state, duration=0.0):
        if state == 'on':
            return self.relay_on(relay_id, duration)
        else:
            return self.relay_off(relay_id)

    def output_sec_currently_on(self, relay_id):
        return self.rpyc_client.root.output_sec_currently_on(relay_id)

    def relay_setup(self, action, relay_id):
        return self.rpyc_client.root.relay_setup(action, relay_id)

    def relay_state(self, relay_id):
        return self.rpyc_client.root.relay_state(relay_id)

    def refresh_daemon_camera_settings(self):
        return self.rpyc_client.root.refresh_daemon_camera_settings()

    def refresh_daemon_misc_settings(self):
        return self.rpyc_client.root.refresh_daemon_misc_settings()

    def refresh_conditionals(self):
        return self.rpyc_client.root.refresh_conditionals()

    def trigger_conditional_actions(
            self, conditional_id, message='', edge=None,
            output_state=None, on_duration=None, duty_cycle=None):
        return self.rpyc_client.root.trigger_conditional_actions(
            conditional_id, message, edge=edge, output_state=output_state,
            on_duration=on_duration, duty_cycle=duty_cycle)

    def terminate_daemon(self):
        return self.rpyc_client.root.terminate_daemon()


def daemon_active():
    """ Used to determine if the daemon is reachable to communicate """
    try:
        rpyc.connect("localhost", 18813)
        return True
    except socket.error:
        return False


def timeout_handler(signum, frame):  # Custom signal handler
    raise TimeoutException


def parseargs(parser):
    parser.add_argument('--activatecontroller', nargs=2,
                        metavar=('CONTROLLER', 'ID'), type=str,
                        help='Activate controller. Options: LCD, PID, Input, Timer',
                        required=False)
    parser.add_argument('--deactivatecontroller', nargs=2,
                        metavar=('CONTROLLER', 'ID'), type=str,
                        help='Deactivate controller. Options: LCD, PID, Input, Timer',
                        required=False)
    parser.add_argument('-c', '--checkdaemon', action='store_true',
                        help="Check if all active daemon controllers are running")
    parser.add_argument('--ramuse', action='store_true',
                        help="Return the amount of ram used by the Mycodo daemon")
    parser.add_argument('--relayoff', metavar='RELAYID', type=str,
                        help='Turn off relay with relay ID',
                        required=False)
    parser.add_argument('--relayon', metavar='RELAYID', type=str,
                        help='Turn on relay with relay ID',
                        required=False)
    parser.add_argument('--duration', metavar='SECONDS', type=float,
                        help='Turn on relay for a duration of time (seconds)',
                        required=False)
    parser.add_argument('-t', '--terminate', action='store_true',
                        help="Terminate the daemon")
    return parser.parse_args()


if __name__ == "__main__":
    now = datetime.datetime.now
    parser = argparse.ArgumentParser(description="Client for Mycodo daemon.")
    args = parseargs(parser)
    daemon_control = DaemonControl()

    if args.checkdaemon:
        return_msg = daemon_control.check_daemon()
        logger.info(
            "[Remote command] Check Daemon: {msg}".format(msg=return_msg))

    elif args.ramuse:
        return_msg = daemon_control.ram_use()
        logger.info(
            "[Remote command] Daemon Ram in Use: {msg} MB".format(msg=return_msg))

    elif args.relayoff:
        return_msg = daemon_control.relay_off(args.relayoff)
        logger.info("[Remote command] Turn off relay with ID '{id}': "
                    "Server returned: {msg}".format(
                        id=args.relayoff,
                        msg=return_msg))

    elif args.duration and args.relayon is None:
        parser.error("--duration requires --relayon")

    elif args.relayon:
        duration = 0
        if args.duration:
            duration = args.duration
        return_msg = daemon_control.relay_on(args.relayon, duration)
        logger.info("[Remote command] Turn on relay with ID '{id}': "
                    "Server returned:".format(
                        id=args.relayon,
                        msg=return_msg))

    elif args.activatecontroller:
        if args.activatecontroller[0] not in ['LCD', 'Log', 'PID',
                                              'Input', 'Timer']:
            logger.info("Invalid controller type. Options are LCD, Log, PID, "
                        "Input, and Timer.")
        else:
            return_msg = daemon_control.controller_activate(
                args.activatecontroller[0], args.activatecontroller[1])
            logger.info("[Remote command] Activate {type} controller with "
                        "ID '{id}': Server returned: {msg}".format(
                            type=args.activatecontroller[0],
                            id=args.activatecontroller[1],
                            msg=return_msg))

    elif args.deactivatecontroller:
        if args.deactivatecontroller[0] not in ['LCD', 'Log', 'PID',
                                                'Input', 'Timer']:
            logger.info("Invalid controller type. Options are LCD, Log, PID, "
                        "Input, and Timer.")
        else:
            return_msg = daemon_control.controller_deactivate(
                args.deactivatecontroller[0], args.deactivatecontroller[1])
            logger.info("[Remote command] Deactivate {type} controller with "
                        "ID '{id}': Server returned: {msg}".format(
                            type=args.deactivatecontroller[0],
                            id=args.deactivatecontroller[1],
                            msg=return_msg))

    elif args.terminate:
        logger.info("[Remote command] Terminate daemon...")
        if daemon_control.terminate_daemon():
            logger.info("Daemon response: Terminated.")
        else:
            logger.info("Unknown daemon response.")

    sys.exit(0)
