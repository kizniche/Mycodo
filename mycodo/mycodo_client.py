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

    def input_information_get(self):
        return self.rpyc_client.root.input_information_get()

    def input_information_update(self):
        return self.rpyc_client.root.input_information_update()

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

    def pid_get(self, pid_id, setting):
        return self.rpyc_client.root.pid_get(pid_id, setting)

    def pid_set(self, pid_id, setting, value):
        return self.rpyc_client.root.pid_set(pid_id, setting, value)

    def ram_use(self):
        return self.rpyc_client.root.ram_use()

    def output_off(self, output_id, trigger_conditionals=True):
        return self.rpyc_client.root.output_off(output_id, trigger_conditionals)

    def output_on(self, output_id, duration=0.0, min_off=0.0,
                 duty_cycle=0.0, trigger_conditionals=True):
        return self.rpyc_client.root.output_on(
            output_id, duration=duration, min_off=min_off,
            duty_cycle=duty_cycle, trigger_conditionals=trigger_conditionals)

    def output_on_off(self, output_id, state, duration=0.0):
        if state == 'on':
            return self.output_on(output_id, duration)
        else:
            return self.output_off(output_id)

    def output_sec_currently_on(self, output_id):
        return self.rpyc_client.root.output_sec_currently_on(output_id)

    def output_setup(self, action, output_id):
        return self.rpyc_client.root.output_setup(action, output_id)

    def output_state(self, output_id):
        return self.rpyc_client.root.output_state(output_id)

    def refresh_daemon_camera_settings(self):
        return self.rpyc_client.root.refresh_daemon_camera_settings()

    def refresh_daemon_conditional_settings(self, unique_id):
        return self.rpyc_client.root.refresh_daemon_conditional_settings(unique_id)

    def refresh_daemon_misc_settings(self):
        return self.rpyc_client.root.refresh_daemon_misc_settings()

    def refresh_daemon_trigger_settings(self, unique_id):
        return self.rpyc_client.root.refresh_daemon_trigger_settings(unique_id)

    def test_trigger_actions(self, function_id, message=''):
        return self.rpyc_client.root.test_trigger_actions(function_id, message)

    def trigger_trigger_actions(
            self, trigger_id, message='', edge=None,
            output_state=None, on_duration=None, duty_cycle=None):
        return self.rpyc_client.root.trigger_trigger_actions(
            trigger_id, message, edge=edge, output_state=output_state,
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
                        help='Activate controller. Options: Conditional, LCD, Math, PID, Input',
                        required=False)
    parser.add_argument('--deactivatecontroller', nargs=2,
                        metavar=('CONTROLLER', 'ID'), type=str,
                        help='Deactivate controller. Options: Conditional, LCD, Math, PID, Input',
                        required=False)

    # PID manipulate
    parser.add_argument('--pid_pause', nargs=1,
                        metavar=('ID'), type=str,
                        help='Pause PID controller.',
                        required=False)
    parser.add_argument('--pid_hold', nargs=1,
                        metavar=('ID'), type=str,
                        help='Hold PID controller.',
                        required=False)
    parser.add_argument('--pid_resume', nargs=1,
                        metavar=('ID'), type=str,
                        help='Resume PID controller.',
                        required=False)

    # PID get
    parser.add_argument('--pid_get_setpoint', nargs=1,
                        metavar=('ID'), type=str,
                        help='Get the setpoint value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_error', nargs=1,
                        metavar=('ID'), type=str,
                        help='Get the error value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_integrator', nargs=1,
                        metavar=('ID'), type=str,
                        help='Get the integrator value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_derivator', nargs=1,
                        metavar=('ID'), type=str,
                        help='Get the derivator value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_kp', nargs=1,
                        metavar=('ID'), type=str,
                        help='Get the Kp gain of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_ki', nargs=1,
                        metavar=('ID'), type=str,
                        help='Get the Ki gain of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_kd', nargs=1,
                        metavar=('ID'), type=str,
                        help='Get the Kd gain of the PID controller.',
                        required=False)

    # PID set
    parser.add_argument('--pid_set_setpoint', nargs=2,
                        metavar=('ID','SETPOINT'), type=str,
                        help='Set the setpoint value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_set_integrator', nargs=2,
                        metavar=('ID', 'INTEGRATOR'), type=str,
                        help='Set the integrator value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_set_derivator', nargs=2,
                        metavar=('ID', 'DERIVATOR'), type=str,
                        help='Set the derivator value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_set_kp', nargs=2,
                        metavar=('ID', 'KP'), type=str,
                        help='Set the Kp gain of the PID controller.',
                        required=False)
    parser.add_argument('--pid_set_ki', nargs=2,
                        metavar=('ID', 'KI'), type=str,
                        help='Set the Ki gain of the PID controller.',
                        required=False)
    parser.add_argument('--pid_set_kd', nargs=2,
                        metavar=('ID', 'KD'), type=str,
                        help='Set the Kd gain of the PID controller.',
                        required=False)

    parser.add_argument('-c', '--checkdaemon', action='store_true',
                        help="Check if all active daemon controllers are running")
    parser.add_argument('--ramuse', action='store_true',
                        help="Return the amount of ram used by the Mycodo daemon")

    # Output
    parser.add_argument('--outputoff', metavar='OUTPUTID', type=str,
                        help='Turn off output with output ID',
                        required=False)
    parser.add_argument('--outputon', metavar='OUTPUTID', type=str,
                        help='Turn on output with output ID',
                        required=False)
    parser.add_argument('--duration', metavar='SECONDS', type=float,
                        help='Turn on output for a duration of time (seconds)',
                        required=False)
    parser.add_argument('--dutycycle', metavar='DUTYCYCLE', type=float,
                        help='Turn on PWM output for a duty cycle (%%)',
                        required=False)

    parser.add_argument('-t', '--terminate', action='store_true',
                        help="Terminate the daemon")

    return parser.parse_args()


if __name__ == "__main__":
    now = datetime.datetime.now
    parser = argparse.ArgumentParser(description="Client for Mycodo daemon.")
    args = parseargs(parser)
    daemon = DaemonControl()

    if args.checkdaemon:
        return_msg = daemon.check_daemon()
        logger.info(
            "[Remote command] Check Daemon: {msg}".format(msg=return_msg))

    elif args.ramuse:
        return_msg = daemon.ram_use()
        logger.info(
            "[Remote command] Daemon Ram in Use: {msg} MB".format(
                msg=return_msg))

    elif args.outputoff:
        return_msg = daemon.output_off(args.outputoff)
        logger.info("[Remote command] Turn off output with ID '{id}': "
                    "Server returned: {msg}".format(
                        id=args.outputoff,
                        msg=return_msg))

    elif args.duration and args.outputon is None:
        parser.error("--duration requires --outputon")

    elif args.outputon:
        if args.duration:
            return_msg = daemon.output_on(
                args.outputon, duration=args.duration)
        elif args.duty_cycle:
            return_msg = daemon.output_on(
                args.outputon, duty_cycle=args.duty_cycle)
        else:
            return_msg = daemon.output_on(args.outputon)
        logger.info("[Remote command] Turn on output with ID '{id}': "
                    "Server returned:".format(
                        id=args.outputon,
                        msg=return_msg))

    elif args.activatecontroller:
        if args.activatecontroller[0] not in ['Conditional', 'LCD', 'Math', 'PID', 'Input']:
            logger.info("Invalid controller type. Options: Conditional, LCD, Math, PID, "
                        "Input.")
        else:
            return_msg = daemon.controller_activate(
                args.activatecontroller[0], args.activatecontroller[1])
            logger.info("[Remote command] Activate {type} controller with "
                        "ID '{id}': Server returned: {msg}".format(
                            type=args.activatecontroller[0],
                            id=args.activatecontroller[1],
                            msg=return_msg))

    elif args.deactivatecontroller:
        if args.deactivatecontroller[0] not in ['Conditional', 'LCD', 'Math', 'PID', 'Input']:
            logger.info("Invalid controller type. Options: Conditional, LCD, Math, PID, "
                        "Input.")
        else:
            return_msg = daemon.controller_deactivate(
                args.deactivatecontroller[0], args.deactivatecontroller[1])
            logger.info("[Remote command] Deactivate {type} controller with "
                        "ID '{id}': Server returned: {msg}".format(
                            type=args.deactivatecontroller[0],
                            id=args.deactivatecontroller[1],
                            msg=return_msg))

    elif args.pid_pause:
        daemon.pid_pause(args.pid_pause[0])

    elif args.pid_hold:
        daemon.pid_pause(args.pid_hold[0])

    elif args.pid_resume:
        daemon.pid_pause(args.pid_resume[0])

    elif args.pid_get_setpoint:
        print(daemon.pid_get(args.pid_get_setpoint[0], 'setpoint'))
    elif args.pid_get_error:
        print(daemon.pid_get(args.pid_get_error[0], 'error'))
    elif args.pid_get_integrator:
        print(daemon.pid_get(args.pid_get_integrator[0], 'integrator'))
    elif args.pid_get_derivator:
        print(daemon.pid_get(args.pid_get_derivator[0], 'derivator'))
    elif args.pid_get_kp:
        print(daemon.pid_get(args.pid_get_kp[0], 'kp'))
    elif args.pid_get_ki:
        print(daemon.pid_get(args.pid_get_ki[0], 'ki'))
    elif args.pid_get_kd:
        print(daemon.pid_get(args.pid_get_kd[0], 'kd'))

    elif args.pid_set_setpoint:
        print(daemon.pid_set(args.pid_set_setpoint[0],
                             'setpoint', args.pid_set_setpoint[1]))
    elif args.pid_set_integrator:
        print(daemon.pid_set(args.pid_set_integrator[0],
                             'integrator', args.pid_set_integrator[1]))
    elif args.pid_set_derivator:
        print(daemon.pid_set(args.pid_set_derivator[0],
                             'derivator', args.pid_set_derivator[1]))
    elif args.pid_set_kp:
        print(daemon.pid_set(args.pid_set_kp[0], 'kp', args.pid_set_kp[1]))
    elif args.pid_set_ki:
        print(daemon.pid_set(args.pid_set_ki[0], 'ki', args.pid_set_ki[1]))
    elif args.pid_set_kd:
        print(daemon.pid_set(args.pid_set_kd[0], 'kd', args.pid_set_kd[1]))

    elif args.terminate:
        logger.info("[Remote command] Terminate daemon...")
        if daemon.terminate_daemon():
            logger.info("Daemon response: Terminated.")
        else:
            logger.info("Unknown daemon response.")

    sys.exit(0)
