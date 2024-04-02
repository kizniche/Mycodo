#!/opt/Mycodo/env/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo_client.py - Client to communicate with the Mycodo daemon.
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
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
import os
import sys
import traceback

import Pyro5.errors
from Pyro5.api import Proxy

sys.path.append(os.path.abspath(os.path.join(os.path.realpath(__file__), '../..')))

from mycodo.config import PYRO_URI
from mycodo.databases.models import SMTP, Misc
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.send_data import send_email as send_email_notification
from mycodo.utils.widget_generate_html import generate_widget_html

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)
logger = logging.getLogger(__name__)


class DaemonControl:
    """Communicate with the daemon to execute commands or retrieve information."""
    def __init__(self, pyro_uri=PYRO_URI, pyro_timeout=None):
        self.pyro_timeout = 30
        try:
            if pyro_timeout:
                self.pyro_timeout = pyro_timeout
            else:
                misc = db_retrieve_table_daemon(Misc, entry='first')
                self.pyro_timeout = misc.rpyc_timeout  # TODO: Rename to rpc_timeout at next major revision
        except Exception:
            logger.exception("Could not access SQL table to determine Pyro Timeout. Using 30 seconds.")

        self.uri= pyro_uri

    def proxy(self, timeout=None):
        try:
            proxy = Proxy(self.uri)
            if timeout:
                proxy._pyroTimeout = timeout
            else:
                proxy._pyroTimeout = self.pyro_timeout
            return proxy
        except Exception as e:
            logger.error(f"Pyro5 proxy error: {e}")

    #
    # Status functions
    #

    def check_daemon(self):
        proxy = self.proxy()
        old_timeout = proxy._pyroTimeout
        try:
            proxy._pyroTimeout = 10
            result = proxy.check_daemon()
            if result:
                return result
            else:
                return "GOOD"
        except Pyro5.errors.TimeoutError as err:
            msg = f"Pyro5 TimeoutError: {err}"
            logger.error(msg)
            return msg
        except Pyro5.errors.CommunicationError as err:
            msg = f"Pyro5 Communication error: {err}"
            logger.error(msg)
            return msg
        except Pyro5.errors.NamingError as err:
            msg = f"Failed to locate Pyro5 Nameserver: {err}"
            logger.error(msg)
            return msg
        except Exception as err:
            msg = f"Pyro Exception: {err}"
            logger.error(msg)
            return msg
        finally:
            proxy._pyroTimeout = old_timeout

    def controller_is_active(self, controller_id):
        return self.proxy().controller_is_active(controller_id)

    def daemon_status(self):
        return self.proxy().daemon_status()

    def is_in_virtualenv(self):
        return self.proxy().is_in_virtualenv()

    def ram_use(self):
        return self.proxy().ram_use()

    #
    # Daemon
    #

    def controller_activate(self, controller_id):
        return self.proxy().controller_activate(controller_id)

    def controller_deactivate(self, controller_id):
        return self.proxy().controller_deactivate(controller_id)

    def controller_restart(self, controller_id):
        return self.proxy().controller_restart(controller_id)

    def refresh_daemon_conditional_settings(self, unique_id):
        return self.proxy().refresh_daemon_conditional_settings(unique_id)

    def refresh_daemon_misc_settings(self):
        return self.proxy().refresh_daemon_misc_settings()

    def refresh_daemon_trigger_settings(self, unique_id):
        return self.proxy().refresh_daemon_trigger_settings(unique_id)

    def terminate_daemon(self):
        return self.proxy().terminate_daemon()

    #
    # Function Actions
    #

    def trigger_action(
            self, action_id, value={}, debug=False):
        return self.proxy().trigger_action(
            action_id, value=value, debug=debug)

    def trigger_all_actions(self, function_id, message='', debug=False):
        return self.proxy().trigger_all_actions(
            function_id, message=message, debug=debug)

    #
    # Input Controller
    #

    def input_force_measurements(self, input_id):
        try:
            return self.proxy().input_force_measurements(input_id)
        except Exception:
            return 0, traceback.format_exc()

    #
    # Display
    #

    def lcd_backlight(self, lcd_id, state):
        return self.proxy().lcd_backlight(lcd_id, state)

    def display_backlight_color(self, lcd_id, color):
        return self.proxy().display_backlight_color(lcd_id, color)

    def lcd_flash(self, lcd_id, state):
        return self.proxy().lcd_flash(lcd_id, state)

    def lcd_reset(self, lcd_id):
        return self.proxy().lcd_reset(lcd_id)

    #
    # Measurements
    #

    def get_condition_measurement(self, condition_id, function_id=None):
        return self.proxy().get_condition_measurement(condition_id)

    def get_condition_measurement_dict(self, condition_id):
        return self.proxy().get_condition_measurement_dict(condition_id)

    #
    # Output Controller
    #

    def output_off(self, output_id, output_channel=None, trigger_conditionals=True):
        return self.proxy().output_off(
            output_id, output_channel=output_channel, trigger_conditionals=trigger_conditionals)

    def output_on(self,
                  output_id,
                  output_type=None,
                  amount=0.0,
                  min_off=0.0,
                  output_channel=None,
                  trigger_conditionals=True):
        return self.proxy().output_on(
            output_id, output_type=output_type, amount=amount, min_off=min_off,
            output_channel=output_channel, trigger_conditionals=trigger_conditionals)

    def output_on_off(self, output_id, state, output_type=None, amount=0.0, output_channel=None):
        """Turn an output on or off."""
        if state in ['on', 1, True]:
            return self.output_on(
                output_id, amount=amount, output_type=output_type, output_channel=output_channel)
        elif state in ['off', 0, False]:
            return self.output_off(output_id, output_channel=output_channel)
        else:
            return 1, f'state not "on", 1, True, "off", 0, or False. Found: "{state}"'

    def output_sec_currently_on(self, output_id, output_channel=None):
        """Return the amount of seconds an on/off output channel has been on."""
        return self.proxy().output_sec_currently_on(output_id, output_channel)

    def output_setup(self, action, output_id):
        return self.proxy().output_setup(action, output_id)

    def output_state(self, output_id, output_channel):
        return self.proxy().output_state(output_id, output_channel)

    def output_states_all(self):
        return self.proxy().output_states_all()

    #
    # PID Controller
    #

    def pid_hold(self, pid_id):
        return self.proxy().pid_hold(pid_id)

    def pid_mod(self, pid_id):
        return self.proxy().pid_mod(pid_id)

    def pid_pause(self, pid_id):
        return self.proxy().pid_pause(pid_id)

    def pid_resume(self, pid_id):
        return self.proxy().pid_resume(pid_id)

    def pid_get(self, pid_id, setting):
        return self.proxy().pid_get(pid_id, setting)

    def pid_set(self, pid_id, setting, value):
        return self.proxy().pid_set(pid_id, setting, value)

    #
    # Functions
    #

    def function_status(self, function_id):
        return self.proxy().function_status(function_id)

    #
    # Miscellaneous
    #

    @staticmethod
    def send_email(recipients, message, subject=''):
        smtp = db_retrieve_table_daemon(SMTP, entry='first')
        send_email_notification(
            smtp.host, smtp.protocol, smtp.port,
            smtp.user, smtp.passw, smtp.email_from,
            recipients, message, subject=subject)

    def module_function(self, controller_type, unique_id, button_id, args_dict, thread=True, return_from_function=False, timeout=None):
        try:
            return self.proxy(timeout=timeout).module_function(
                controller_type, unique_id, button_id, args_dict, thread=thread, return_from_function=return_from_function)
        except Exception:
            return 1, traceback.format_exc()

    def widget_add_refresh(self, unique_id):
        return self.proxy().widget_add_refresh(unique_id)

    def widget_remove(self, unique_id):
        return self.proxy().widget_remove(unique_id)

    def widget_execute(self, unique_id):
        return self.proxy().widget_execute(unique_id)

def daemon_active():
    """Used to determine if the daemon is reachable to communicate."""
    try:
        daemon = DaemonControl()
        if daemon.check_daemon() != 'GOOD':
            return False
        return True
    except Exception:
        return False


def parseargs(parser):
    # Daemon
    parser.add_argument('-c', '--checkdaemon', action='store_true',
                        help="Check if all active daemon controllers are running")
    parser.add_argument('--activatecontroller', nargs=2,
                        metavar=('CONTROLLER', 'ID'), type=str,
                        help='Activate controller. Options: Conditional, PID, Input',
                        required=False)
    parser.add_argument('--deactivatecontroller', nargs=2,
                        metavar=('CONTROLLER', 'ID'), type=str,
                        help='Deactivate controller. Options: Conditional, PID, Input',
                        required=False)
    parser.add_argument('--ramuse', action='store_true',
                        help="Return the amount of ram used by the Mycodo daemon")
    parser.add_argument('-t', '--terminate', action='store_true',
                        help="Terminate the daemon")

    # Function Actions
    parser.add_argument('--trigger_action', metavar='ACTIONID', type=str,
                        help='Trigger action with Action ID',
                        required=False)
    parser.add_argument('--trigger_all_actions', metavar='FUNCTIONID', type=str,
                        help='Trigger all actions belonging to Function with ID',
                        required=False)

    # Input Controller
    parser.add_argument('--input_force_measurements', metavar='INPUTID', type=str,
                        help='Force acquiring measurements for Input ID',
                        required=False)

    # LCD Controller
    parser.add_argument('--backlight_on', metavar='LCDID', type=str,
                        help='Turn on LCD backlight with LCD ID',
                        required=False)
    parser.add_argument('--backlight_off', metavar='LCDID', type=str,
                        help='Turn off LCD backlight with LCD ID',
                        required=False)
    parser.add_argument('--lcd_reset', metavar='LCDID', type=str,
                        help='Reset LCD with LCD ID',
                        required=False)

    # Output Controller
    parser.add_argument('--output_state', metavar='OUTPUTID', type=str,
                        help='State of output with output ID',
                        required=False)
    parser.add_argument('--output_currently_on', metavar='OUTPUTID', type=str,
                        help='How many seconds an output has currently been active for',
                        required=False)
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
    parser.add_argument('--output_channel', metavar='OUTPUTCHANNEL', type=int,
                        help='The output channel to modulate',
                        required=False)

    # PID Controller
    parser.add_argument('--pid_pause', nargs=1,
                        metavar='ID', type=str,
                        help='Pause PID controller.',
                        required=False)
    parser.add_argument('--pid_hold', nargs=1,
                        metavar='ID', type=str,
                        help='Hold PID controller.',
                        required=False)
    parser.add_argument('--pid_resume', nargs=1,
                        metavar='ID', type=str,
                        help='Resume PID controller.',
                        required=False)
    parser.add_argument('--pid_get_setpoint', nargs=1,
                        metavar='ID', type=str,
                        help='Get the setpoint value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_error', nargs=1,
                        metavar='ID', type=str,
                        help='Get the error value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_integrator', nargs=1,
                        metavar='ID', type=str,
                        help='Get the integrator value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_derivator', nargs=1,
                        metavar='ID', type=str,
                        help='Get the derivator value of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_kp', nargs=1,
                        metavar='ID', type=str,
                        help='Get the Kp gain of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_ki', nargs=1,
                        metavar='ID', type=str,
                        help='Get the Ki gain of the PID controller.',
                        required=False)
    parser.add_argument('--pid_get_kd', nargs=1,
                        metavar='ID', type=str,
                        help='Get the Kd gain of the PID controller.',
                        required=False)
    parser.add_argument('--pid_set_setpoint', nargs=2,
                        metavar=('ID', 'SETPOINT'), type=str,
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

    # Widgets
    parser.add_argument('--gen_widget_html', action='store_true',
                        help="Generate all widget HTML files")

    return parser.parse_args()


if __name__ == "__main__":
    now = datetime.datetime.now
    parser = argparse.ArgumentParser(description="Client for Mycodo daemon.")
    args = parseargs(parser)
    daemon = DaemonControl()

    if args.checkdaemon:
        return_msg = daemon.check_daemon()
        logger.info(f"[Remote command] Check Daemon: {return_msg}")

    elif args.ramuse:
        return_msg = daemon.ram_use()
        logger.info(f"[Remote command] Daemon Ram in Use: {return_msg} MB")

    elif args.input_force_measurements:
        return_msg = daemon.input_force_measurements(args.input_force_measurements)
        logger.info(
            "[Remote command] Force acquiring measurements for Input with "
            f"ID '{args.input_force_measurements}': Server returned: {return_msg[1]}")

    elif args.lcd_reset:
        return_msg = daemon.lcd_reset(args.lcd_reset)
        logger.info(f"[Remote command] Reset LCD with ID '{args.lcd_reset}': Server returned: {return_msg}")

    elif args.backlight_off:
        return_msg = daemon.lcd_backlight(args.backlight_off, 0)
        logger.info("[Remote command] Turn off LCD backlight with "
                    f"ID '{args.backlight_off}': Server returned: {return_msg}")

    elif args.backlight_on:
        return_msg = daemon.lcd_backlight(args.backlight_on, 1)
        logger.info("[Remote command] Turn on LCD backlight with "
                    f"ID '{args.backlight_on}': Server returned: {return_msg}")

    elif args.output_currently_on and args.output_channel is None:
        parser.error("--output_currently_on requires --output_channel")

    elif args.output_currently_on:
        return_msg = daemon.output_sec_currently_on(
            args.output_currently_on, output_channel=args.output_channel)
        logger.info("[Remote command] How many seconds output has been on. "
                    f"ID '{args.output_currently_on}' CH{args.output_channel}: "
                    f"Server returned: {return_msg}")

    elif args.output_state and args.output_channel is None:
        parser.error("--output_state requires --output_channel")

    elif args.output_state:
        return_msg = daemon.output_state(args.output_state, args.output_channel)
        logger.info("[Remote command] State of output with "
                    f"ID '{args.output_state}' CH{args.output_channel}: "
                    f"Server returned: {return_msg}")

    elif args.outputoff and args.output_channel is None:
        parser.error("--outputoff requires --output_channel")

    elif args.outputoff:
        return_msg = daemon.output_off(args.outputoff, args.output_channel)
        logger.info("[Remote command] Turn off output with "
                    f"ID '{args.outputoff}': Server returned: {return_msg}")

    elif args.duration and args.outputon is None:
        parser.error("--duration requires --outputon")

    elif args.outputon and args.output_channel is None:
        parser.error("--outputon requires --output_channel")

    elif args.outputon:
        if args.duration:
            return_msg = daemon.output_on(
                args.outputon,
                output_type='sec',
                amount=args.duration,
                output_channel=args.output_channel)
        elif args.dutycycle:
            return_msg = daemon.output_on(
                args.outputon,
                output_type='pwm',
                amount=args.dutycycle,
                output_channel=args.output_channel)
        else:
            return_msg = daemon.output_on(
                args.outputon,
                output_channel=args.output_channel)
        logger.info(f"[Remote command] Turn on output with ID '{args.outputon}': Server returned: {return_msg}")

    elif args.activatecontroller:
        return_msg = daemon.controller_activate(
            args.activatecontroller[0])
        logger.info("[Remote command] Activate controller with "
                    f"ID '{args.activatecontroller[0]}': Server returned: {return_msg}")

    elif args.deactivatecontroller:
        return_msg = daemon.controller_deactivate(
            args.deactivatecontroller[0])
        logger.info("[Remote command] Deactivate controller with "
                    f"ID '{args.deactivatecontroller[0]}': Server returned: {return_msg}")

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
        print(daemon.pid_set(args.pid_set_setpoint[0], 'setpoint', args.pid_set_setpoint[1]))
    elif args.pid_set_integrator:
        print(daemon.pid_set(args.pid_set_integrator[0], 'integrator', args.pid_set_integrator[1]))
    elif args.pid_set_derivator:
        print(daemon.pid_set(args.pid_set_derivator[0], 'derivator', args.pid_set_derivator[1]))
    elif args.pid_set_kp:
        print(daemon.pid_set(args.pid_set_kp[0], 'kp', args.pid_set_kp[1]))
    elif args.pid_set_ki:
        print(daemon.pid_set(args.pid_set_ki[0], 'ki', args.pid_set_ki[1]))
    elif args.pid_set_kd:
        print(daemon.pid_set(args.pid_set_kd[0], 'kd', args.pid_set_kd[1]))

    elif args.trigger_action:
        print(daemon.trigger_action(args.trigger_action))
    elif args.trigger_all_actions:
        print(daemon.trigger_all_actions(args.trigger_all_actions))

    elif args.gen_widget_html:
        generate_widget_html()

    elif args.terminate:
        logger.info("[Remote command] Terminate daemon...")
        if daemon.terminate_daemon():
            logger.info("Daemon response: Terminated.")
        else:
            logger.info("Unknown daemon response.")

    sys.exit(0)
