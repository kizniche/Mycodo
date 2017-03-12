#!/usr/bin/python
# coding=utf-8
#
# controller_relay.py - Relay controller to manage turning relays on/off
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

import datetime
import logging
import RPi.GPIO as GPIO
import threading
import time
import timeit

# Classes
from databases.mycodo_db.models import (
    Conditional,
    ConditionalActions,
    Relay,
    SMTP
)
from mycodo_client import DaemonControl

# Functions
from utils.database import db_retrieve_table_daemon
from utils.influx import write_influxdb_value
from utils.send_data import send_email
from utils.system_pi import cmd_output

# Config
from config import MAX_AMPS


class RelayController(threading.Thread):
    """
    class for controlling relays

    """
    def __init__(self):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.relay")

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.control = DaemonControl()

        self.relay_id = {}
        self.relay_unique_id = {}
        self.relay_name = {}
        self.relay_pin = {}
        self.relay_amps = {}
        self.relay_trigger = {}
        self.relay_on_at_start = {}
        self.relay_on_until = {}
        self.relay_last_duration = {}
        self.relay_on_duration = {}

        self.relay_time_turned_on = {}

        self.logger.debug("Initializing Relays")
        try:

            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            self.smtp_max_count = smtp.hourly_max
            self.smtp_wait_time = time.time() + 3600
            self.smtp_timer = time.time()
            self.email_count = 0
            self.allowed_to_send_notice = True

            relays = db_retrieve_table_daemon(Relay, entry='all')
            self.all_relays_initialize(relays)
            # Turn all relays off
            self.all_relays_off()
            # Turn relays on that are set to be on at start
            self.all_relays_on()
            self.logger.debug("Relays Initialized")

        except Exception as except_msg:
            self.logger.exception(
                "Problem initializing relays: {err}", err=except_msg)

        self.running = False

    def run(self):
        try:
            self.running = True
            self.logger.info("Relay controller activated in "
                             "{:.1f} ms".format((timeit.default_timer()-self.thread_startup_timer)*1000))
            while self.running:
                current_time = datetime.datetime.now()
                for relay_id in self.relay_id:
                    # Is the current time past the time the relay was supposed
                    # to turn off at?
                    if (self.relay_on_until[relay_id] < current_time and
                            self.relay_on_duration[relay_id] and
                            self.relay_pin[relay_id]):

                        # Use threads to prevent a slow execution of a
                        # process that could slow the loop
                        turn_relay_off = threading.Thread(
                            target=self.relay_on_off,
                            args=(relay_id, 'off',))
                        turn_relay_off.start()

                        if self.relay_last_duration[relay_id] > 0:
                            duration = float(self.relay_last_duration[relay_id])
                            timestamp = datetime.datetime.utcnow()-datetime.timedelta(seconds=duration)
                            write_db = threading.Thread(
                                target=write_influxdb_value,
                                args=(self.relay_unique_id[relay_id],
                                      'duration_sec',
                                      duration,
                                      timestamp,))
                            write_db.start()

                time.sleep(0.10)
        finally:
            self.all_relays_off()
            self.cleanup_gpio()
            self.running = False
            self.logger.info("Relay controller deactivated in "
                             "{:.1f} ms".format((timeit.default_timer()-self.thread_shutdown_timer)*1000))

    def relay_on_off(self, relay_id, state,
                     duration=0.0,
                     trigger_conditionals=True,
                     min_off_duration=0.0):
        """
        Turn a relay on or off
        The GPIO may be either HIGH or LOW to activate a relay. This trigger
        state will be referenced to determine if the GPIO needs to be high or
        low to turn the relay on or off.

        Conditionals will be checked for each action requested of a relay, and
        if true, those conditional actions will be executed. For example:
            'If relay 1 turns on, turn relay 3 off'

        :param relay_id: Unique ID for relay
        :type relay_id: str
        :param state: What state is desired? 'on' or 'off'
        :type state: str
        :param duration: If state is 'on', a duration can be set to turn the relay off after
        :type duration: float
        :param trigger_conditionals: Whether to trigger condionals to act or not
        :type trigger_conditionals: bool
        :param min_off_duration: Don't turn on if not off for at least this duration (0 = disabled)
        :type min_off_duration: float
        """
        # Check if relay exists
        relay_id = int(relay_id)
        if relay_id not in self.relay_id:
            self.logger.warning("Cannot turn {} Relay with ID {}. It "
                                "doesn't exist".format(state, relay_id))
            return 1

        # Signaled to turn relay on
        if state == 'on':
            if not self.relay_pin[relay_id]:
                self.logger.warning(
                    "Invalid pin for relay {id} ({name}): {pin}.".format(
                        id=self.relay_id[relay_id],
                        name=self.relay_name[relay_id],
                        pin=self.relay_pin[relay_id]))
                return 1

            current_amps = self.current_amp_load()
            if current_amps+self.relay_amps[relay_id] > MAX_AMPS:
                self.logger.warning("Cannot turn relay {} "
                                    "({}) On. If this relay turns on, "
                                    "there will be {} amps being drawn, "
                                    "which exceeds the maximum set draw of {}"
                                    " amps.".format(self.relay_id[relay_id],
                                                    self.relay_name[relay_id],
                                                    current_amps,
                                                    MAX_AMPS))
                return 1

            # If the relay is used in a PID, a minimum off duration is set,
            # and if the off duration has surpassed that amount of time (i.e.
            # has it been off for longer then the minimum off duration?).
            current_time = datetime.datetime.now()
            if (min_off_duration and not self.is_on(relay_id) and
                    current_time > self.relay_on_until[relay_id]):
                off_seconds = (current_time - self.relay_on_until[relay_id]).total_seconds()
                if off_seconds < min_off_duration:
                    self.logger.debug(
                        "Relay {id} ({name}) instructed to turn on by PID, "
                        "however the minimum off period of {min_off_sec} "
                        "seconds has not been reached yet (it has only been "
                        "off for {off_sec} seconds).".format(
                            id=self.relay_id[relay_id],
                            name=self.relay_name[relay_id],
                            min_off_sec=min_off_duration,
                            off_sec=off_seconds))
                    return 1

            if duration:
                time_now = datetime.datetime.now()
                if self.is_on(relay_id) and self.relay_on_duration[relay_id]:
                    if self.relay_on_until[relay_id] > time_now:
                        remaining_time = (self.relay_on_until[relay_id]-time_now).total_seconds()
                    else:
                        remaining_time = 0
                    time_on = self.relay_last_duration[relay_id] - remaining_time
                    self.logger.debug("Relay {} ({}) is already "
                                      "on for a duration of {:.1f} seconds (with "
                                      "{:.1f} seconds remaining). Recording the "
                                      "amount of time the relay has been on ({:.1f} "
                                      "sec) and updating the on duration to {:.1f} "
                                      "seconds.".format(self.relay_id[relay_id],
                                                        self.relay_name[relay_id],
                                                        self.relay_last_duration[relay_id],
                                                        remaining_time,
                                                        time_on,
                                                        duration))
                    if time_on > 0:
                        # Write the duration the relay was ON to the
                        # database at the timestamp it turned ON
                        duration = float(time_on)
                        timestamp = datetime.datetime.utcnow()-datetime.timedelta(seconds=duration)
                        write_db = threading.Thread(
                            target=write_influxdb_value,
                            args=(self.relay_unique_id[relay_id],
                                  'duration_sec',
                                  duration,
                                  timestamp,))
                        write_db.start()

                    self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                    self.relay_last_duration[relay_id] = duration
                    return 0
                elif self.is_on(relay_id) and not self.relay_on_duration:
                    self.relay_on_duration[relay_id] = True
                    self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                    self.relay_last_duration[relay_id] = duration

                    self.logger.debug("Relay {} ({}) is currently"
                                      " on without a duration. Turning "
                                      "into a duration  of {:.1f} "
                                      "seconds.".format(self.relay_id[relay_id],
                                                        self.relay_name[relay_id],
                                                        duration))
                    return 0
                else:
                    self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                    self.relay_on_duration[relay_id] = True
                    self.relay_last_duration[relay_id] = duration
                    self.logger.debug("Relay {} ({}) on for {:.1f} "
                                      "seconds.".format(self.relay_id[relay_id],
                                                        self.relay_name[relay_id],
                                                        duration))
                    GPIO.output(self.relay_pin[relay_id], self.relay_trigger[relay_id])

            else:
                if self.is_on(relay_id):
                    self.logger.warning("Relay {} ({}) is already"
                                        " on.".format(self.relay_id[relay_id],
                                                      self.relay_name[relay_id]))
                    return 1
                else:
                    # Record the time the relay was turned on in order to
                    # calculate and log the total duration is was on, when
                    # it eventually turns off.
                    self.relay_time_turned_on[relay_id] = datetime.datetime.now()
                    self.logger.debug("Relay {rid} ({rname}) ON "
                                      "at {timeon}.".format(rid=self.relay_id[relay_id],
                                                            rname=self.relay_name[relay_id],
                                                            timeon=self.relay_time_turned_on[relay_id]))
                    GPIO.output(self.relay_pin[relay_id],
                                self.relay_trigger[relay_id])

        # Signaled to turn relay off
        elif state == 'off':
            if self._is_setup(self.relay_pin[relay_id]) and self.relay_pin[relay_id]:  # if pin not 0
                GPIO.output(self.relay_pin[relay_id], not self.relay_trigger[relay_id])
                self.logger.debug("Relay {} ({}) turned off.".format(
                        self.relay_id[relay_id],
                        self.relay_name[relay_id]))

                if (self.relay_time_turned_on[relay_id] is not None or
                        self.relay_on_duration[relay_id]):
                    duration = 0
                    if self.relay_on_duration[relay_id]:
                        remaining_time = 0
                        time_now = datetime.datetime.now()
                        if self.relay_on_until[relay_id] > time_now:
                            remaining_time = (self.relay_on_until[relay_id] - time_now).total_seconds()
                        duration = self.relay_last_duration[relay_id] - remaining_time
                        self.relay_on_duration[relay_id] = False
                        self.relay_on_until[relay_id] = datetime.datetime.now()

                    if self.relay_time_turned_on[relay_id] is not None:
                        # Write the duration the relay was ON to the database
                        # at the timestamp it turned ON
                        duration = (datetime.datetime.now()-self.relay_time_turned_on[relay_id]).total_seconds()
                        self.relay_time_turned_on[relay_id] = None

                    timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=duration)
                    write_db = threading.Thread(
                        target=write_influxdb_value,
                        args=(self.relay_unique_id[relay_id],
                              'duration_sec',
                              duration,
                              timestamp,))
                    write_db.start()

        if trigger_conditionals:
            if state == 'on' and duration != 0:
                self.check_conditionals(relay_id, 0)
            self.check_conditionals(relay_id, duration)

    def check_conditionals(self, relay_id, on_duration):
        conditionals = db_retrieve_table_daemon(Conditional)
        conditionals = conditionals.filter(Conditional.if_relay_id == relay_id)
        conditionals = conditionals.filter(Conditional.is_activated == True)

        # conditionals = db_retrieve_table_daemon(RelayConditional)
        # conditionals = conditionals.filter(RelayConditional.if_relay_id == relay_id)
        # conditionals = conditionals.filter(RelayConditional.is_activated == True)

        if self.is_on(relay_id):
            conditionals = conditionals.filter(Conditional.if_relay_state == 'on')
            conditionals = conditionals.filter(Conditional.if_relay_duration == on_duration)
        else:
            conditionals = conditionals.filter(Conditional.if_relay_state == 'off')

        for each_conditional in conditionals.all():
            conditional_actions = db_retrieve_table_daemon(ConditionalActions)
            conditional_actions = conditional_actions.filter(
                ConditionalActions.conditional_id == each_conditional.id).all()

            for each_cond_action in conditional_actions:
                now = time.time()
                timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H-%M-%S')
                message = "{}\n[Relay Conditional {}] {}\n".format(
                    timestamp, each_cond_action.id, each_cond_action.name)

                if each_cond_action.do_action == 'relay':
                    message += "If relay {} ({}) turns {}, Then:\n".format(
                        each_cond_action.if_relay_id,
                        self.relay_name[each_cond_action.if_relay_id],
                        each_cond_action.if_relay_state)
                    message += "Turn relay {} ({}) {}".format(
                            each_cond_action.do_relay_id,
                            self.relay_name[each_cond_action.do_relay_id],
                            each_cond_action.do_relay_state)

                    if each_cond_action.do_duration == 0:
                        self.relay_on_off(each_cond_action.do_relay_id,
                                          each_cond_action.do_relay_state)
                    else:
                        message += " for {} seconds".format(each_cond_action.do_duration)
                        self.relay_on_off(each_cond_action.do_relay_id,
                                          each_cond_action.do_relay_state,
                                          each_cond_action.do_relay_duration)
                    message += ".\n"

                elif each_cond_action.do_action == 'command':
                    # Execute command as user mycodo
                    message += "Execute: '{}'. ".format(
                        each_cond_action.do_action_string)
                    _, _, cmd_status = cmd_output(
                        each_cond_action.do_action_string)
                    message += "Status: {}. ".format(cmd_status)

                elif each_cond_action.do_action == 'email':
                    if (self.email_count >= self.smtp_max_count and
                            time.time() < self.smtp_wait_time):
                        self.allowed_to_send_notice = False
                    else:
                        if time.time() > self.smtp_wait_time:
                            self.email_count = 0
                            self.smtp_wait_time = time.time() + 3600
                        self.allowed_to_send_notice = True
                    self.email_count += 1

                    if self.allowed_to_send_notice:
                        message += "Notify {}.".format(
                            each_cond_action.email_notify)

                        smtp = db_retrieve_table_daemon(SMTP, entry='first')
                        send_email(
                            smtp.host, smtp.ssl, smtp.port, smtp.user,
                            smtp.passw, smtp.email_from,
                            each_cond_action.do_action_string, message)
                    else:
                        self.logger.debug(
                            "[Relay Conditional {}] True: {:.0f} seconds "
                            "left to be allowed to email again.".format(
                                each_cond_action.id,
                                self.smtp_wait_time-time.time()))

                elif each_cond_action.do_action == 'flash_lcd':
                    start_flashing = threading.Thread(
                        target=self.control.flash_lcd,
                        args=(each_cond_action.do_lcd_id, 1,))
                    start_flashing.start()

                # TODO: Implement photo/video actions for relay conditionals
                elif each_cond_action.do_action == 'photo':
                    pass

                elif each_cond_action.do_action == 'video':
                    pass

                self.logger.debug("{}".format(message))

    def all_relays_initialize(self, relays):
        for each_relay in relays:
            self.relay_id[each_relay.id] = each_relay.id
            self.relay_unique_id[each_relay.id] = each_relay.unique_id
            self.relay_name[each_relay.id] = each_relay.name
            self.relay_pin[each_relay.id] = each_relay.pin
            self.relay_amps[each_relay.id] = each_relay.amps
            self.relay_trigger[each_relay.id] = each_relay.trigger
            self.relay_on_at_start[each_relay.id] = each_relay.on_at_start
            self.relay_on_until[each_relay.id] = datetime.datetime.now()
            self.relay_last_duration[each_relay.id] = 0
            self.relay_on_duration[each_relay.id] = False
            self.relay_time_turned_on[each_relay.id] = None
            self.setup_pin(each_relay.id, each_relay.pin, each_relay.trigger)
            self.logger.debug("{id} ({name}) Initialized".format(
                id=each_relay.id, name=each_relay.name))

    def all_relays_off(self):
        """Turn all relays off"""
        for each_relay_id in self.relay_id:
            self.relay_on_off(each_relay_id, 'off', 0, False)

    def all_relays_on(self):
        """Turn all relays on that are set to be on at startup"""
        for each_relay_id in self.relay_id:
            if self.relay_on_at_start[each_relay_id]:
                self.relay_on_off(each_relay_id, 'on', 0, False)

    def cleanup_gpio(self):
        for each_relay_pin in self.relay_pin:
            GPIO.cleanup(each_relay_pin)

    def add_mod_relay(self, relay_id, do_setup_pin=False):
        """
        Add or modify local dictionary of relay settings form SQL database

        When a relay is added or modified while the relay controller is
        running, these local variables need to also be modified to
        maintain consistency between the SQL database and running controller.

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        :param do_setup_pin: If True, initialize GPIO (when adding new relay)
        :type do_setup_pin: bool
        """
        relay_id = int(relay_id)
        try:
            relay = db_retrieve_table_daemon(Relay, device_id=relay_id)
            self.relay_id[relay_id] = relay.id
            self.relay_unique_id[relay_id] = relay.unique_id
            self.relay_name[relay_id] = relay.name
            self.relay_pin[relay_id] = relay.pin
            self.relay_amps[relay_id] = relay.amps
            self.relay_trigger[relay_id] = relay.trigger
            self.relay_on_at_start[relay_id] = relay.on_at_start
            self.relay_on_until[relay_id] = datetime.datetime.now()
            self.relay_time_turned_on[relay_id] = None
            self.relay_last_duration[relay_id] = 0
            self.relay_on_duration[relay_id] = False
            message = "Relay {id} ({name}) ".format(
                id=self.relay_id[relay_id], name=self.relay_name[relay_id])
            if do_setup_pin and relay.pin:
                self.setup_pin(relay.id, relay.pin, relay.trigger)
                message += "initialized"
            else:
                message += "added"
            self.logger.debug(message)
            return 0, "success"
        except Exception as except_msg:
            return 1, "Add_Mod_Relay Error: ID {id}: {err}".format(
                id=relay_id, err=except_msg)

    def del_relay(self, relay_id):
        """
        Delete local variables

        The controller local variables must match the SQL database settings.
        Therefore, this is called when a relay has been removed from the SQL
        database.

        :return: 0 for success, 1 for fail (with error message)
        :rtype: int, str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        relay_id = int(relay_id)
        try:
            self.logger.debug("Relay {} ({}) Deleted.".format(
                self.relay_id[relay_id], self.relay_name[relay_id]))
            # Ensure relay is off before removing it, to prevent
            # it from being stuck on
            self.relay_on_off(relay_id, 'off')
            self.relay_id.pop(relay_id, None)
            self.relay_unique_id.pop(relay_id, None)
            self.relay_name.pop(relay_id, None)
            self.relay_pin.pop(relay_id, None)
            self.relay_amps.pop(relay_id, None)
            self.relay_trigger.pop(relay_id, None)
            self.relay_on_at_start.pop(relay_id, None)
            self.relay_on_until.pop(relay_id, None)
            self.relay_last_duration.pop(relay_id, None)
            self.relay_on_duration.pop(relay_id, None)
            return 0, "success"
        except Exception as msg:
            return 1, "Del_Relay Error: ID {}: {}".format(relay_id, msg)

    def relay_sec_currently_on(self, relay_id):
        if not self.is_on(relay_id):
            return 0
        else:
            time_now = datetime.datetime.now()
            sec_currently_on = 0
            if self.relay_on_duration[relay_id]:
                remaining_time = 0
                if self.relay_on_until[relay_id] > time_now:
                    remaining_time = (self.relay_on_until[relay_id] - time_now).total_seconds()
                sec_currently_on = self.relay_last_duration[relay_id] - remaining_time
            elif self.relay_time_turned_on[relay_id]:
                sec_currently_on = (time_now - self.relay_time_turned_on[relay_id]).total_seconds()
            return sec_currently_on

    def relay_setup(self, action, relay_id, setup_pin):
        """ Add, delete, or modify a specific relay """
        if action == 'Add':
            return self.add_mod_relay(relay_id)
        elif action == 'Modify':
            return self.add_mod_relay(relay_id, do_setup_pin=setup_pin)
        elif action == 'Delete':
            return self.del_relay(relay_id)

    def current_amp_load(self):
        """
        Calculate the current amp draw from all the devices connected to
        all relays currently on.

        :return: total amerage draw
        :rtype: float
        """
        amp_load = 0.0
        for each_relay_id, each_relay_amps in self.relay_amps.items():
            if self.is_on(each_relay_id):
                amp_load += each_relay_amps
        return amp_load

    def setup_pin(self, relay_id, pin, trigger):
        """
        Setup pin for this relay
        :rtype: None
        """
        # Setup GPIO (BCM numbering) and initialize relay pin as output
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, not trigger)
            state = 'LOW' if trigger else 'HIGH'
            self.logger.info(
                "Relay {id} setup on pin {pin} and turned OFF "
                "(OFF={state})".format(id=relay_id, pin=pin, state=state))
        except Exception as except_msg:
            self.logger.error(
                "Relay {id} was unable to be setup on pin {pin} with "
                "trigger={trigger}: {err}".format(
                    id=relay_id, pin=pin, trigger=trigger, err=except_msg))

    def relay_state(self, relay_id):
        """
        :return: Whether the relay is currently "ON"
        :rtype: str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        if self.relay_trigger[relay_id] == GPIO.input(self.relay_pin[relay_id]):
            return 'on'
        else:
            return 'off'

    def is_on(self, relay_id):
        """
        :return: Whether the relay is currently "ON"
        :rtype: bool

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        if self._is_setup(self.relay_pin[relay_id]):
            return self.relay_trigger[relay_id] == GPIO.input(self.relay_pin[relay_id])

    @staticmethod
    def _is_setup(pin):
        """
        This function checks to see if the GPIO pin is setup and ready
        to use. This is for safety and to make sure we don't blow anything.

        # TODO Make it do that.

        :return: Is it safe to manipulate this relay?
        :rtype: bool
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        return True

    def is_running(self):
        return self.running

    def stop_controller(self):
        """Signal to stop the controller"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
