# coding=utf-8
#
# controller_relay.py - Output controller to manage turning relays on/off
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
import pigpio
import RPi.GPIO as GPIO
import threading
import time
import timeit

from mycodo_client import DaemonControl
from databases.models import Conditional
from databases.models import ConditionalActions
from databases.models import Misc
from databases.models import Relay
from databases.models import SMTP
from devices.wireless_433mhz_pi_switch import Transmit433MHz
from utils.database import db_retrieve_table_daemon
from utils.influx import write_influxdb_value
from utils.send_data import send_email
from utils.system_pi import cmd_output


class RelayController(threading.Thread):
    """
    class for controlling relays

    """
    def __init__(self):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.output")

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.control = DaemonControl()

        self.relay_id = {}
        self.relay_unique_id = {}
        self.relay_type = {}
        self.relay_name = {}
        self.relay_pin = {}
        self.relay_amps = {}
        self.relay_trigger = {}
        self.relay_on_at_start = {}
        self.relay_on_until = {}
        self.relay_last_duration = {}
        self.relay_on_duration = {}

        # wireless
        self.relay_protocol = {}
        self.relay_pulse_length = {}
        self.relay_bit_length = {}
        self.relay_on_command = {}
        self.relay_off_command = {}
        self.wireless_pi_switch = {}

        # PWM
        self.pwm_hertz = {}
        self.pwm_library = {}
        self.pwm_output = {}
        self.pwm_state = {}
        self.pwm_time_turned_on = {}

        self.relay_time_turned_on = {}

        self.logger.debug("Initializing Outputs")
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
            self.logger.debug("Outputs Initialized")

        except Exception as except_msg:
            self.logger.exception(
                "Problem initializing relays: {err}".format(err=except_msg))

        self.running = False

    def run(self):
        try:
            self.running = True
            self.logger.info(
                "Output controller activated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_startup_timer)*1000))
            while self.running:
                current_time = datetime.datetime.now()
                for relay_id in self.relay_id:
                    # Is the current time past the time the relay was supposed
                    # to turn off at?
                    if (self.relay_on_until[relay_id] < current_time and
                            self.relay_on_duration[relay_id] and
                            self.relay_pin[relay_id] is not None):

                        # Use threads to prevent a slow execution of a
                        # process that could slow the loop
                        turn_relay_off = threading.Thread(
                            target=self.relay_on_off,
                            args=(relay_id,
                                  'off',))
                        turn_relay_off.start()

                        if self.relay_last_duration[relay_id] > 0:
                            duration = float(self.relay_last_duration[relay_id])
                            timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=duration)
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
            self.logger.info(
                "Output controller deactivated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_shutdown_timer)*1000))

    def relay_on_off(self, relay_id, state,
                     duration=0.0,
                     min_off=0.0,
                     duty_cycle=0.0,
                     trigger_conditionals=True):
        """
        Turn a relay on or off
        The GPIO may be either HIGH or LOW to activate a relay. This trigger
        state will be referenced to determine if the GPIO needs to be high or
        low to turn the relay on or off.

        Conditionals will be checked for each action requested of a relay, and
        if true, those conditional actions will be executed. For example:
            'If relay 1 turns on, turn relay 3 off'

        :param relay_id: Unique ID for relay
        :type relay_id: int
        :param state: What state is desired? 'on' or 'off'
        :type state: str
        :param duration: If state is 'on', a duration can be set to turn the relay off after
        :type duration: float
        :param min_off: Don't turn on if not off for at least this duration (0 = disabled)
        :type min_off: float
        :param duty_cycle: Duty cycle of PWM output
        :type duty_cycle: float
        :param trigger_conditionals: Whether to trigger conditionals to act or not
        :type trigger_conditionals: bool
        """
        # Check if relay exists
        relay_id = int(relay_id)
        if relay_id not in self.relay_id:
            self.logger.warning(
                "Cannot turn {state} Output with ID {id}. "
                "It doesn't exist".format(
                    state=state, id=relay_id))
            return 1

        # Signaled to turn relay on
        if state == 'on':

            # Check if pin is valid
            if (self.relay_type[relay_id] in ['pwm',
                                              'wired',
                                              'wireless_433MHz_pi_switch'] and
                    self.relay_pin[relay_id] is None):
                self.logger.warning(
                    u"Invalid pin for relay {id} ({name}): {pin}.".format(
                        id=self.relay_id[relay_id],
                        name=self.relay_name[relay_id],
                        pin=self.relay_pin[relay_id]))
                return 1

            # Check if max amperage will be exceeded
            if self.relay_type[relay_id] in ['command',
                                             'wired',
                                             'wireless_433MHz_pi_switch']:
                current_amps = self.current_amp_load()
                max_amps = db_retrieve_table_daemon(Misc, entry='first').max_amps
                if current_amps + self.relay_amps[relay_id] > max_amps:
                    self.logger.warning(
                        u"Cannot turn relay {} ({}) On. If this relay turns on, "
                        u"there will be {} amps being drawn, which exceeds the "
                        u"maximum set draw of {} amps.".format(
                            self.relay_id[relay_id],
                            self.relay_name[relay_id],
                            current_amps,
                            max_amps))
                    return 1

                # If the relay is used in a PID, a minimum off duration is set,
                # and if the off duration has surpassed that amount of time (i.e.
                # has it been off for longer then the minimum off duration?).
                current_time = datetime.datetime.now()
                if (min_off and not self.is_on(relay_id) and
                        current_time > self.relay_on_until[relay_id]):
                    off_seconds = (current_time - self.relay_on_until[relay_id]).total_seconds()
                    if off_seconds < min_off:
                        self.logger.debug(
                            u"Relay {id} ({name}) instructed to turn on by PID, "
                            u"however the minimum off period of {min_off_sec} "
                            u"seconds has not been reached yet (it has only been "
                            u"off for {off_sec} seconds).".format(
                                id=self.relay_id[relay_id],
                                name=self.relay_name[relay_id],
                                min_off_sec=min_off,
                                off_sec=off_seconds))
                        return 1

            # Turn relay on for a duration
            if (self.relay_type[relay_id] in ['command',
                                              'wired',
                                              'wireless_433MHz_pi_switch'] and
                    duration):
                time_now = datetime.datetime.now()
                if self.is_on(relay_id) and self.relay_on_duration[relay_id]:
                    if self.relay_on_until[relay_id] > time_now:
                        remaining_time = (self.relay_on_until[relay_id] - time_now).total_seconds()
                    else:
                        remaining_time = 0
                    time_on = self.relay_last_duration[relay_id] - remaining_time
                    self.logger.debug(
                        u"Relay {rid} ({rname}) is already on for a duration "
                        u"of {ron:.2f} seconds (with {rremain:.2f} seconds "
                        u"remaining). Recording the amount of time the relay "
                        u"has been on ({rbeenon:.2f} sec) and updating the on "
                        u"duration to {rnewon:.2f} seconds.".format(
                            rid=self.relay_id[relay_id],
                            rname=self.relay_name[relay_id],
                            ron=self.relay_last_duration[relay_id],
                            rremain=remaining_time,
                            rbeenon=time_on,
                            rnewon=duration))
                    self.relay_on_until[relay_id] = time_now + datetime.timedelta(seconds=duration)
                    self.relay_last_duration[relay_id] = duration

                    if time_on > 0:
                        # Write the duration the relay was ON to the
                        # database at the timestamp it turned ON
                        duration = float(time_on)
                        timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=duration)
                        write_db = threading.Thread(
                            target=write_influxdb_value,
                            args=(self.relay_unique_id[relay_id],
                                  'duration_sec',
                                  duration,
                                  timestamp,))
                        write_db.start()

                    return 0
                elif self.is_on(relay_id) and not self.relay_on_duration:
                    self.relay_on_duration[relay_id] = True
                    self.relay_on_until[relay_id] = time_now + datetime.timedelta(seconds=duration)
                    self.relay_last_duration[relay_id] = duration
                    self.logger.debug(
                        u"Relay {id} ({name}) is currently on without a "
                        u"duration. Turning into a duration  of {dur:.1f} "
                        u"seconds.".format(
                            id=self.relay_id[relay_id],
                            name=self.relay_name[relay_id],
                            dur=duration))
                    return 0
                else:
                    self.relay_on_until[relay_id] = time_now + datetime.timedelta(seconds=duration)
                    self.relay_on_duration[relay_id] = True
                    self.relay_last_duration[relay_id] = duration
                    self.logger.debug(
                        u"Relay {id} ({name}) on for {dur:.1f} "
                        u"seconds.".format(
                            id=self.relay_id[relay_id],
                            name=self.relay_name[relay_id],
                            dur=duration))
                    self.relay_switch(relay_id, 'on')

            # Just turn relay on
            elif self.relay_type[relay_id] in ['command',
                                               'wired',
                                               'wireless_433MHz_pi_switch']:
                if self.is_on(relay_id):
                    self.logger.warning(
                        u"Relay {id} ({name}) is already on.".format(
                            id=self.relay_id[relay_id],
                            name=self.relay_name[relay_id]))
                    return 1
                else:
                    # Record the time the relay was turned on in order to
                    # calculate and log the total duration is was on, when
                    # it eventually turns off.
                    self.relay_time_turned_on[relay_id] = datetime.datetime.now()
                    self.logger.debug(
                        u"Relay {id} ({name}) ON at {timeon}.".format(
                            id=self.relay_id[relay_id],
                            name=self.relay_name[relay_id],
                            timeon=self.relay_time_turned_on[relay_id]))
                    self.relay_switch(relay_id, 'on')

            # PWM output
            elif self.relay_type[relay_id] == 'pwm':
                # Record the time the PWM was turned on
                if self.pwm_hertz[relay_id] <= 0:
                    self.logger.warning(u"PWM Hertz must be a positive value")
                    return 1
                self.pwm_time_turned_on[relay_id] = datetime.datetime.now()
                self.logger.debug(
                    u"PWM {id} ({name}) ON with a duty cycle of {dc:.2f}% at {hertz} Hz".format(
                        id=self.relay_id[relay_id],
                        name=self.relay_name[relay_id],
                        dc=abs(duty_cycle),
                        hertz=self.pwm_hertz[relay_id]))
                self.relay_switch(relay_id, 'on', duty_cycle=duty_cycle)

                # Write the duty cycle of the PWM to the database
                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.relay_unique_id[relay_id],
                          'duty_cycle',
                          duty_cycle,))
                write_db.start()

        # Signaled to turn relay off
        elif state == 'off':
            if not self._is_setup(relay_id):
                return
            if (self.relay_type[relay_id] in ['pwm',
                                              'wired',
                                              'wireless_433MHz_pi_switch'] and
                    self.relay_pin[relay_id] is None):
                return

            self.relay_switch(relay_id, 'off')

            self.logger.debug(u"Output {id} ({name}) turned off.".format(
                    id=self.relay_id[relay_id],
                    name=self.relay_name[relay_id]))

            # Write PWM duty cycle to database
            if (self.relay_type[relay_id] == 'pwm' and
                    self.pwm_time_turned_on[relay_id] is not None):
                # Write the duration the PWM was ON to the database
                # at the timestamp it turned ON
                duration = (datetime.datetime.now() - self.pwm_time_turned_on[relay_id]).total_seconds()
                self.pwm_time_turned_on[relay_id] = None
                timestamp = datetime.datetime.utcnow() - datetime.timedelta(seconds=duration)
                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.relay_unique_id[relay_id],
                          'duty_cycle',
                          duty_cycle,
                          timestamp,))
                write_db.start()

            # Write relay duration on to database
            elif (self.relay_time_turned_on[relay_id] is not None or
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
                    duration = (datetime.datetime.now() - self.relay_time_turned_on[relay_id]).total_seconds()
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
            self.check_conditionals(relay_id,
                                    state=state,
                                    on_duration=duration,
                                    duty_cycle=duty_cycle)

    def relay_switch(self, relay_id, state, duty_cycle=None):
        if self.relay_type[relay_id] == 'wired':
            if state == 'on':
                GPIO.output(self.relay_pin[relay_id],
                            self.relay_trigger[relay_id])
            elif state == 'off':
                GPIO.output(self.relay_pin[relay_id],
                            not self.relay_trigger[relay_id])

        elif self.relay_type[relay_id] == 'wireless_433MHz_pi_switch':
            if state == 'on':
                self.wireless_pi_switch[relay_id].transmit(
                    int(self.relay_on_command[relay_id]))
            elif state == 'off':
                self.wireless_pi_switch[relay_id].transmit(
                    int(self.relay_off_command[relay_id]))

        elif self.relay_type[relay_id] == 'command':
            if state == 'on' and self.relay_on_command[relay_id]:
                cmd_return, _, cmd_status = cmd_output(
                    self.relay_on_command[relay_id])
            elif state == 'off' and self.relay_off_command[relay_id]:
                cmd_return, _, cmd_status = cmd_output(
                    self.relay_off_command[relay_id])
            else:
                return
            self.logger.debug(
                u"Relay {state} command returned: "
                u"{stat}: '{ret}'".format(
                    state=state,
                    stat=cmd_status,
                    ret=cmd_return))

        elif self.relay_type[relay_id] == 'pwm':
            if state == 'on':
                if self.pwm_library[relay_id] == 'pigpio_hardware':
                    self.pwm_output[relay_id].hardware_PWM(
                        self.relay_pin[relay_id],
                        self.pwm_hertz[relay_id],
                        abs(duty_cycle) * 10000)
                elif self.pwm_library[relay_id] == 'pigpio_any':
                    self.pwm_output[relay_id].set_PWM_frequency(
                        self.relay_pin[relay_id],
                        self.pwm_hertz[relay_id])
                    calc_duty_cycle = int((abs(duty_cycle) / 100.0) * 255)
                    if calc_duty_cycle > 255:
                        calc_duty_cycle = 255
                    if calc_duty_cycle < 0:
                        calc_duty_cycle = 0
                    self.pwm_output[relay_id].set_PWM_dutycycle(
                        self.relay_pin[relay_id],
                        calc_duty_cycle)
                self.pwm_state[relay_id] = abs(duty_cycle)
            elif state == 'off':
                if self.pwm_library[relay_id] == 'pigpio_hardware':
                    self.pwm_output[relay_id].hardware_PWM(
                        self.relay_pin[relay_id],
                        self.pwm_hertz[relay_id], 0)
                elif self.pwm_library[relay_id] == 'pigpio_any':
                    self.pwm_output[relay_id].set_PWM_frequency(
                        self.relay_pin[relay_id],
                        self.pwm_hertz[relay_id])
                    self.pwm_output[relay_id].set_PWM_dutycycle(
                        self.relay_pin[relay_id], 0)
                self.pwm_state[relay_id] = None

    def check_conditionals(self, relay_id, state=None, on_duration=None, duty_cycle=None):
        conditionals = db_retrieve_table_daemon(Conditional)
        conditionals = conditionals.filter(
            Conditional.if_relay_id == relay_id)
        conditionals = conditionals.filter(
            Conditional.is_activated == True)

        if self.is_on(relay_id):
            conditionals = conditionals.filter(
                Conditional.if_relay_state == 'on')
            conditionals = conditionals.filter(
                Conditional.if_relay_duration == on_duration)
        else:
            conditionals = conditionals.filter(
                Conditional.if_relay_state == 'off')

        for each_conditional in conditionals.all():
            conditional_actions = db_retrieve_table_daemon(ConditionalActions)
            conditional_actions = conditional_actions.filter(
                ConditionalActions.conditional_id == each_conditional.id).all()

            for each_cond_action in conditional_actions:
                now = time.time()
                timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H-%M-%S')
                message = u"{ts}\n[Relay Conditional {id}] {name}\n".format(
                    ts=timestamp,
                    id=each_cond_action.id,
                    name=each_conditional.name)

                if each_cond_action.do_action == 'relay':
                    if each_cond_action.do_relay_id not in self.relay_name:
                        message += u"Error: Invalid relay ID {id}.".format(
                            id=each_cond_action.do_relay_id)
                    else:
                        message += u"If relay {id} ({name}) turns {state}, Then ".format(
                            id=each_conditional.if_relay_id,
                            name=self.relay_name[each_conditional.if_relay_id],
                            state=each_conditional.if_relay_state)
                        message += u"turn relay {id} ({name}) {state}".format(
                            id=each_cond_action.do_relay_id,
                            name=self.relay_name[each_cond_action.do_relay_id],
                            state=each_cond_action.do_relay_state)

                        if each_cond_action.do_relay_duration == 0:
                            self.relay_on_off(each_cond_action.do_relay_id,
                                              each_cond_action.do_relay_state)
                        else:
                            message += u" for {dur} seconds".format(
                                dur=each_cond_action.do_relay_duration)
                            self.relay_on_off(each_cond_action.do_relay_id,
                                              each_cond_action.do_relay_state,
                                              duration=each_cond_action.do_relay_duration)
                    message += ".\n"

                elif each_cond_action.do_action == 'command':
                    # Execute command as user mycodo
                    message += u"Execute: '{}'. ".format(
                        each_cond_action.do_action_string)

                    # Check command for variables to replace with values
                    command_str = each_cond_action.do_action_string
                    command_str = command_str.replace(
                        "((output_pin))", str(self.relay_pin[relay_id]))
                    command_str = command_str.replace(
                        "((output_action))", str(state))
                    command_str = command_str.replace(
                        "((output_duration))", str(on_duration))
                    command_str = command_str.replace(
                        "((output_pwm))", str(duty_cycle))
                    _, _, cmd_status = cmd_output(command_str)

                    message += u"Status: {}. ".format(cmd_status)

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
                        message += u"Notify {}.".format(
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
                                each_conditional.id,
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

                self.logger.debug(u"{}".format(message))

    def all_relays_initialize(self, relays):
        for each_relay in relays:
            self.relay_id[each_relay.id] = each_relay.id
            self.relay_unique_id[each_relay.id] = each_relay.unique_id
            self.relay_type[each_relay.id] = each_relay.relay_type
            self.relay_name[each_relay.id] = each_relay.name
            self.relay_pin[each_relay.id] = each_relay.pin
            self.relay_amps[each_relay.id] = each_relay.amps
            self.relay_trigger[each_relay.id] = each_relay.trigger
            self.relay_on_at_start[each_relay.id] = each_relay.on_at_start
            self.relay_on_until[each_relay.id] = datetime.datetime.now()
            self.relay_last_duration[each_relay.id] = 0
            self.relay_on_duration[each_relay.id] = False
            self.relay_time_turned_on[each_relay.id] = None
            self.relay_protocol[each_relay.id] = each_relay.protocol
            self.relay_pulse_length[each_relay.id] = each_relay.pulse_length
            self.relay_bit_length[each_relay.id] = each_relay.bit_length
            self.relay_on_command[each_relay.id] = each_relay.on_command
            self.relay_off_command[each_relay.id] = each_relay.off_command

            self.pwm_hertz[each_relay.id] = each_relay.pwm_hertz
            self.pwm_library[each_relay.id] = each_relay.pwm_library
            self.pwm_time_turned_on[each_relay.id] = None

            if self.relay_pin[each_relay.id] is not None:
                self.setup_pin(each_relay.id)

            self.logger.debug(u"{id} ({name}) Initialized".format(
                id=each_relay.id, name=each_relay.name))

    def all_relays_off(self):
        """Turn all relays off"""
        for each_relay_id in self.relay_id:
            if (self.relay_on_at_start[each_relay_id] is None or
                    self.relay_type[each_relay_id] == 'pwm'):
                pass  # Don't turn off
            else:
                self.relay_on_off(each_relay_id, 'off',
                                  trigger_conditionals=False)

    def all_relays_on(self):
        """Turn all relays on that are set to be on at startup"""
        for each_relay_id in self.relay_id:
            if (self.relay_on_at_start[each_relay_id] is None or
                    self.relay_type[each_relay_id] == 'pwm'):
                pass  # Don't turn on or off
            elif self.relay_on_at_start[each_relay_id]:
                self.relay_on_off(each_relay_id, 'on',
                                  trigger_conditionals=False)
            elif not self.relay_on_at_start[each_relay_id]:
                self.relay_on_off(each_relay_id, 'off',
                                  trigger_conditionals=False)

    def cleanup_gpio(self):
        for each_relay_pin in self.relay_pin:
            GPIO.cleanup(each_relay_pin)

    def add_mod_relay(self, relay_id):
        """
        Add or modify local dictionary of relay settings form SQL database

        When a relay is added or modified while the relay controller is
        running, these local variables need to also be modified to
        maintain consistency between the SQL database and running controller.

        :param relay_id: Unique ID for each relay
        :type relay_id: int

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str
        """
        relay_id = int(relay_id)
        try:
            relay = db_retrieve_table_daemon(Relay, device_id=relay_id)

            self.relay_type[relay_id] = relay.relay_type

            # Turn current pin off
            if relay_id in self.relay_pin and self.relay_state(relay_id) != 'off':
                self.relay_switch(relay_id, 'off')

            self.relay_id[relay_id] = relay.id
            self.relay_unique_id[relay_id] = relay.unique_id
            self.relay_type[relay_id] = relay.relay_type
            self.relay_name[relay_id] = relay.name
            self.relay_pin[relay_id] = relay.pin
            self.relay_amps[relay_id] = relay.amps
            self.relay_trigger[relay_id] = relay.trigger
            self.relay_on_at_start[relay_id] = relay.on_at_start
            self.relay_on_until[relay_id] = datetime.datetime.now()
            self.relay_time_turned_on[relay_id] = None
            self.relay_last_duration[relay_id] = 0
            self.relay_on_duration[relay_id] = False
            self.relay_protocol[relay_id] = relay.protocol
            self.relay_pulse_length[relay_id] = relay.pulse_length
            self.relay_bit_length[relay_id] = relay.bit_length
            self.relay_on_command[relay_id] = relay.on_command
            self.relay_off_command[relay_id] = relay.off_command

            self.pwm_hertz[relay_id] = relay.pwm_hertz
            self.pwm_library[relay_id] = relay.pwm_library

            if self.relay_pin[relay_id]:
                self.setup_pin(relay.id)

            message = u"Output {id} ({name}) initialized".format(
                id=self.relay_id[relay_id],
                name=self.relay_name[relay_id])
            self.logger.debug(message)

            return 0, "success"
        except Exception as except_msg:
            self.logger.exception(1)
            return 1, "Add_Mod_Output Error: ID {id}: {err}".format(
                id=relay_id, err=except_msg)

    def del_relay(self, relay_id):
        """
        Delete local variables

        The controller local variables must match the SQL database settings.
        Therefore, this is called when a relay has been removed from the SQL
        database.

        :param relay_id: Unique ID for each relay
        :type relay_id: str

        :return: 0 for success, 1 for fail (with error message)
        :rtype: int, str
        """
        relay_id = int(relay_id)

        # Turn current pin off
        if relay_id in self.relay_pin and self.relay_state(relay_id) != 'off':
            self.relay_switch(relay_id, 'off')

        try:
            self.logger.debug(u"Output {id} ({name}) Deleted.".format(
                id=self.relay_id[relay_id], name=self.relay_name[relay_id]))
            self.relay_id.pop(relay_id, None)
            self.relay_unique_id.pop(relay_id, None)
            self.relay_type.pop(relay_id, None)
            self.relay_name.pop(relay_id, None)
            self.relay_pin.pop(relay_id, None)
            self.relay_amps.pop(relay_id, None)
            self.relay_trigger.pop(relay_id, None)
            self.relay_on_at_start.pop(relay_id, None)
            self.relay_on_until.pop(relay_id, None)
            self.relay_last_duration.pop(relay_id, None)
            self.relay_on_duration.pop(relay_id, None)
            self.relay_protocol.pop(relay_id, None)
            self.relay_pulse_length.pop(relay_id, None)
            self.relay_bit_length.pop(relay_id, None)
            self.relay_on_command.pop(relay_id, None)
            self.relay_off_command.pop(relay_id, None)
            self.wireless_pi_switch.pop(relay_id, None)

            self.pwm_hertz.pop(relay_id, None)
            self.pwm_library.pop(relay_id, None)
            self.pwm_output.pop(relay_id, None)
            self.pwm_state.pop(relay_id, None)
            self.pwm_time_turned_on.pop(relay_id, None)

            return 0, "success"
        except Exception as msg:
            return 1, "Del_Output Error: ID {id}: {msg}".format(
                id=relay_id, msg=msg)

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

    def relay_setup(self, action, relay_id):
        """ Add, delete, or modify a specific relay """
        if action in ['Add', 'Modify']:
            return self.add_mod_relay(relay_id)
        elif action == 'Delete':
            return self.del_relay(relay_id)
        else:
            return [1, 'Invalid relay_setup action']

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

    def setup_pin(self, relay_id):
        """
        Setup pin for this relay

        :param relay_id: Unique ID for each relay
        :type relay_id: int

        :rtype: None
        """
        if self.relay_type[relay_id] == 'wired':
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(True)
                GPIO.setup(self.relay_pin[relay_id], GPIO.OUT)
                GPIO.output(self.relay_pin[relay_id], not self.relay_trigger[relay_id])
                state = 'LOW' if self.relay_trigger[relay_id] else 'HIGH'
                self.logger.info(
                    "Relay {id} setup on pin {pin} and turned OFF "
                    "(OFF={state})".format(id=relay_id, pin=self.relay_pin[relay_id], state=state))
            except Exception as except_msg:
                self.logger.exception(
                    "Relay {id} was unable to be setup on pin {pin} with "
                    "trigger={trigger}: {err}".format(
                        id=relay_id, pin=self.relay_pin[relay_id],
                        trigger=self.relay_trigger[relay_id], err=except_msg))

        elif self.relay_type[relay_id] == 'wireless_433MHz_pi_switch':
            self.wireless_pi_switch[relay_id] = Transmit433MHz(
                self.relay_pin[relay_id],
                protocol=int(self.relay_protocol[relay_id]),
                pulse_length=int(self.relay_pulse_length[relay_id]),
                bit_length=int(self.relay_bit_length[relay_id]))

        elif self.relay_type[relay_id] == 'pwm':
            try:
                self.pwm_output[relay_id] = pigpio.pi()
                if self.pwm_library[relay_id] == 'pigpio_hardware':
                    self.pwm_output[relay_id].hardware_PWM(
                        self.relay_pin[relay_id], self.pwm_hertz[relay_id], 0)
                elif self.pwm_library[relay_id] == 'pigpio_any':
                    self.pwm_output[relay_id].set_PWM_frequency(
                        self.relay_pin[relay_id], self.pwm_hertz[relay_id])
                    self.pwm_output[relay_id].set_PWM_dutycycle(
                        self.relay_pin[relay_id], 0)
                self.pwm_state[relay_id] = None
                self.logger.info("PWM {id} setup on pin {pin}".format(
                    id=relay_id, pin=self.relay_pin[relay_id]))
            except Exception as except_msg:
                self.logger.exception(
                    "PWM {id} was unable to be setup on pin {pin}: "
                    "{err}".format(id=relay_id, pin=self.relay_pin[relay_id], err=except_msg))

    def relay_state(self, relay_id):
        """
        :param relay_id: Unique ID for each relay
        :type relay_id: int

        :return: Whether the relay is currently "ON"
        :rtype: str
        """
        if relay_id in self.relay_type:
            if self.relay_type[relay_id] == 'wired':
                if (self.relay_pin[relay_id] is not None and
                        self.relay_trigger[relay_id] == GPIO.input(self.relay_pin[relay_id])):
                    return 'on'
            elif self.relay_type[relay_id] in ['command',
                                               'wireless_433MHz_pi_switch']:
                if self.relay_time_turned_on[relay_id]:
                    return 'on'
            elif self.relay_type[relay_id] == 'pwm':
                if relay_id in self.pwm_state and self.pwm_state[relay_id]:
                    return self.pwm_state[relay_id]
        return 'off'

    def is_on(self, relay_id):
        """
        :param relay_id: Unique ID for each relay
        :type relay_id: int

        :return: Whether the relay is currently "ON"
        :rtype: bool
        """
        if (self.relay_type[relay_id] == 'wired' and
                self._is_setup(relay_id)):
            return self.relay_trigger[relay_id] == GPIO.input(self.relay_pin[relay_id])
        elif self.relay_type[relay_id] in ['command',
                                           'wireless_433MHz_pi_switch']:
            if self.relay_time_turned_on[relay_id]:
                return True
        elif self.relay_type[relay_id] == 'pwm':
            if self.pwm_time_turned_on[relay_id]:
                return True
        return False

    def _is_setup(self, relay_id):
        """
        This function checks to see if the GPIO pin is setup and ready
        to use. This is for safety and to make sure we don't blow anything.

        :param relay_id: Unique ID for each relay
        :type relay_id: int

        :return: Is it safe to manipulate this relay?
        :rtype: bool
        """
        if self.relay_type[relay_id] == 'wired' and self.relay_pin[relay_id]:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay_pin[relay_id], GPIO.OUT)
            return True
        elif self.relay_type[relay_id] in ['command',
                                           'wireless_433MHz_pi_switch']:
            return True
        elif self.relay_type[relay_id] == 'pwm':
            if relay_id in self.pwm_output:
                return True
        return False

    def is_running(self):
        return self.running

    def stop_controller(self):
        """Signal to stop the controller"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
