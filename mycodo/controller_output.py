# coding=utf-8
#
# controller_output.py - Output controller to manage turning outputs on/off
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
import threading
import time
import timeit

import RPi.GPIO as GPIO
from sqlalchemy import and_
from sqlalchemy import or_

from mycodo.databases.models import Conditional
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import SMTP
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.system_pi import cmd_output


class OutputController(threading.Thread):
    """
    class for controlling outputs

    """
    def __init__(self):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.output")

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.control = DaemonControl()

        self.output_id = {}
        self.output_unique_id = {}
        self.output_type = {}
        self.output_name = {}
        self.output_pin = {}
        self.output_amps = {}
        self.output_trigger = {}
        self.output_on_at_start = {}
        self.output_on_until = {}
        self.output_last_duration = {}
        self.output_on_duration = {}
        self.output_off_triggered = {}

        # wireless
        self.output_protocol = {}
        self.output_pulse_length = {}
        self.output_on_command = {}
        self.output_off_command = {}
        self.output_pwm_command = {}
        self.wireless_pi_switch = {}

        # PWM
        self.pwm_hertz = {}
        self.pwm_library = {}
        self.pwm_output = {}
        self.pwm_invert_signal = {}
        self.pwm_state = {}
        self.pwm_time_turned_on = {}

        self.output_time_turned_on = {}

        self.logger.debug("Initializing Outputs")
        try:
            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            self.smtp_max_count = smtp.hourly_max
            self.smtp_wait_time = time.time() + 3600
            self.smtp_timer = time.time()
            self.email_count = 0
            self.allowed_to_send_notice = True

            outputs = db_retrieve_table_daemon(Output, entry='all')
            self.all_outputs_initialize(outputs)
            self.all_outputs_set_state()  # Turn outputs on that are set to be on at start
            self.logger.debug("Outputs Initialized")

        except Exception as except_msg:
            self.logger.exception(
                "Problem initializing outputs: {err}".format(err=except_msg))

        self.running = False

    def run(self):
        try:
            self.running = True
            self.logger.info(
                "Output controller activated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_startup_timer)*1000))

            while self.running:
                current_time = datetime.datetime.now()
                for output_id in self.output_id:
                    # Is the current time past the time the output was supposed
                    # to turn off?
                    if (self.output_on_until[output_id] < current_time and
                            self.output_on_duration[output_id] and
                            not self.output_off_triggered[output_id] and
                            ('command' in self.output_type[output_id] or
                             self.output_pin[output_id] is not None)):

                        # Use threads to prevent a slow execution of a
                        # process that could slow the loop
                        self.output_off_triggered[output_id] = True
                        turn_output_off = threading.Thread(
                            target=self.output_on_off,
                            args=(output_id,
                                  'off',))
                        turn_output_off.start()

                time.sleep(0.01)
        finally:
            # Turn all outputs off
            for each_output_id in self.output_id:
                self.output_on_off(
                    each_output_id, 'off', trigger_conditionals=False)
            self.cleanup_gpio()
            self.running = False
            self.logger.info(
                "Output controller deactivated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_shutdown_timer)*1000))

    def output_on_off(self, output_id, state,
                      duration=0.0,
                      min_off=0.0,
                      duty_cycle=0.0,
                      trigger_conditionals=True):
        """
        Turn a output on or off
        The GPIO may be either HIGH or LOW to activate a output. This trigger
        state will be referenced to determine if the GPIO needs to be high or
        low to turn the output on or off.

        Conditionals will be checked for each action requested of a output, and
        if true, those conditional actions will be executed. For example:
            'If output 1 turns on, turn output 3 off'

        :param output_id: ID for output
        :type output_id: str
        :param state: What state is desired? 'on' or 'off'
        :type state: str
        :param duration: If state is 'on', a duration can be set to turn the output off after
        :type duration: float
        :param min_off: Don't turn on if not off for at least this duration (0 = disabled)
        :type min_off: float
        :param duty_cycle: Duty cycle of PWM output
        :type duty_cycle: float
        :param trigger_conditionals: Whether to trigger conditionals to act or not
        :type trigger_conditionals: bool
        """
        # Check if output exists
        if output_id not in self.output_id:
            self.logger.warning(
                "Cannot turn {state} Output with ID {id}. "
                "It doesn't exist".format(
                    state=state, id=output_id))
            return 1

        # Signaled to turn output on
        if state == 'on':

            # Check if pin is valid
            if (self.output_type[output_id] in [
                    'pwm', 'wired', 'wireless_433MHz_pi_switch'] and
                    self.output_pin[output_id] is None):
                self.logger.warning(
                    "Invalid pin for output {id} ({name}): {pin}.".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        pin=self.output_pin[output_id]))
                return 1

            # Check if max amperage will be exceeded
            if self.output_type[output_id] in [
                    'command', 'wired', 'wireless_433MHz_pi_switch']:
                current_amps = self.current_amp_load()
                max_amps = db_retrieve_table_daemon(Misc, entry='first').max_amps
                if current_amps + self.output_amps[output_id] > max_amps:
                    self.logger.warning(
                        "Cannot turn output {} ({}) On. If this output turns on, "
                        "there will be {} amps being drawn, which exceeds the "
                        "maximum set draw of {} amps.".format(
                            self.output_id[output_id],
                            self.output_name[output_id],
                            current_amps,
                            max_amps))
                    return 1

                # If the output is used in a PID, a minimum off duration is set,
                # and if the off duration has surpassed that amount of time (i.e.
                # has it been off for longer then the minimum off duration?).
                current_time = datetime.datetime.now()
                if (min_off and not self.is_on(output_id) and
                        current_time > self.output_on_until[output_id]):
                    off_seconds = (current_time -
                                   self.output_on_until[output_id]).total_seconds()
                    if off_seconds < min_off:
                        self.logger.debug(
                            "Output {id} ({name}) instructed to turn on by PID, "
                            "however the minimum off period of {min_off_sec} "
                            "seconds has not been reached yet (it has only been "
                            "off for {off_sec} seconds).".format(
                                id=self.output_id[output_id],
                                name=self.output_name[output_id],
                                min_off_sec=min_off,
                                off_sec=off_seconds))
                        return 1

            # Turn output on for a duration
            if (self.output_type[output_id] in [
                    'command', 'wired', 'wireless_433MHz_pi_switch'] and
                    duration != 0):
                time_now = datetime.datetime.now()

                # Output is already on for a duration
                if self.is_on(output_id) and self.output_on_duration[output_id]:

                    if self.output_on_until[output_id] > time_now:
                        remaining_time = (self.output_on_until[output_id] -
                                          time_now).total_seconds()
                    else:
                        remaining_time = 0

                    time_on = abs(self.output_last_duration[output_id]) - remaining_time
                    self.logger.debug(
                        "Output {rid} ({rname}) is already on for a duration "
                        "of {ron:.2f} seconds (with {rremain:.2f} seconds "
                        "remaining). Recording the amount of time the output "
                        "has been on ({rbeenon:.2f} sec) and updating the on "
                        "duration to {rnewon:.2f} seconds.".format(
                            rid=self.output_id[output_id],
                            rname=self.output_name[output_id],
                            ron=abs(self.output_last_duration[output_id]),
                            rremain=remaining_time,
                            rbeenon=time_on,
                            rnewon=abs(duration)))
                    self.output_on_until[output_id] = (
                            time_now + datetime.timedelta(seconds=abs(duration)))
                    self.output_last_duration[output_id] = duration

                    # Write the duration the output was ON to the
                    # database at the timestamp it turned ON
                    if time_on > 0:
                        # Make sure the recorded value is recorded negative
                        # if instructed to do so
                        if self.output_last_duration[output_id] < 0:
                            duration_on = float(-time_on)
                        else:
                            duration_on = float(time_on)
                        timestamp = (datetime.datetime.utcnow() -
                                     datetime.timedelta(seconds=abs(duration_on)))
                        write_db = threading.Thread(
                            target=write_influxdb_value,
                            args=(self.output_unique_id[output_id],
                                  'duration_sec',
                                  duration_on,
                                  timestamp,))
                        write_db.start()

                    return 0

                # Output is on, but not for a duration
                elif self.is_on(output_id) and not self.output_on_duration:
                    self.output_on_duration[output_id] = True
                    self.output_on_until[output_id] = (
                            time_now + datetime.timedelta(seconds=abs(duration)))
                    self.output_last_duration[output_id] = duration
                    self.logger.debug(
                        "Output {id} ({name}) is currently on without a "
                        "duration. Turning into a duration of {dur:.1f} "
                        "seconds.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            dur=abs(duration)))
                    return 0

                # Output is not already on
                else:
                    self.logger.debug(
                        "Output {id} ({name}) on for {dur:.1f} "
                        "seconds.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            dur=abs(duration)))
                    self.output_switch(output_id, 'on')
                    self.output_on_until[output_id] = (
                            datetime.datetime.now() +
                            datetime.timedelta(seconds=abs(duration)))
                    self.output_last_duration[output_id] = duration
                    self.output_on_duration[output_id] = True

            # Just turn output on
            elif self.output_type[output_id] in [
                    'command', 'wired', 'wireless_433MHz_pi_switch']:
                if self.is_on(output_id):
                    self.logger.debug(
                        "Output {id} ({name}) is already on.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id]))
                    return 1
                else:
                    # Record the time the output was turned on in order to
                    # calculate and log the total duration is was on, when
                    # it eventually turns off.
                    self.output_time_turned_on[output_id] = datetime.datetime.now()
                    self.logger.debug(
                        "Output {id} ({name}) ON at {timeon}.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            timeon=self.output_time_turned_on[output_id]))
                    self.output_switch(output_id, 'on')

            # PWM command output
            elif self.output_type[output_id] == 'command_pwm':
                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0 - abs(duty_cycle)

                if duty_cycle:
                    self.pwm_time_turned_on[output_id] = datetime.datetime.now()
                else:
                    self.pwm_time_turned_on[output_id] = None

                self.logger.debug(
                    "PWM command {id} ({name}) executed with a duty cycle of {dc:.2f}%".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        dc=abs(duty_cycle)))
                self.output_switch(output_id, 'on', duty_cycle=duty_cycle)

                # Write the duty cycle of the PWM to the database
                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'duty_cycle',
                          duty_cycle,))
                write_db.start()

            # PWM output
            elif self.output_type[output_id] == 'pwm':
                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0 - abs(duty_cycle)

                if duty_cycle:
                    self.pwm_time_turned_on[output_id] = datetime.datetime.now()
                else:
                    self.pwm_time_turned_on[output_id] = None

                # Record the time the PWM was turned on
                if self.pwm_hertz[output_id] <= 0:
                    self.logger.warning("PWM Hertz must be a positive value")
                    return 1

                self.logger.debug(
                    "PWM {id} ({name}) set to a duty cycle of {dc:.2f}% at {hertz} Hz".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        dc=abs(duty_cycle),
                        hertz=self.pwm_hertz[output_id]))
                self.output_switch(output_id, 'on', duty_cycle=duty_cycle)

                # Write the duty cycle of the PWM to the database
                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'duty_cycle',
                          duty_cycle,))
                write_db.start()

        # Signaled to turn output off
        elif state == 'off':

            if not self._is_setup(output_id):
                self.logger.error("Cannot turn off Output {id}: Output not "
                                  "set up properly.".format(id=output_id))
                return

            if (self.output_type[output_id] in [
                    'pwm', 'wired', 'wireless_433MHz_pi_switch'] and
                    self.output_pin[output_id] is None):
                return

            self.output_switch(output_id, 'off')

            self.logger.debug("Output {id} ({name}) turned off.".format(
                    id=self.output_id[output_id],
                    name=self.output_name[output_id]))

            # Write PWM duty cycle to database
            if self.output_type[output_id] in ['pwm', 'command_pwm']:
                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0
                else:
                    duty_cycle = 0.0

                self.pwm_time_turned_on[output_id] = None

                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'duty_cycle',
                          duty_cycle,))
                write_db.start()

            # Write output duration on to database
            elif (self.output_time_turned_on[output_id] is not None or
                    self.output_on_duration[output_id]):
                duration_sec = None
                timestamp = None
                if self.output_on_duration[output_id]:
                    remaining_time = 0
                    time_now = datetime.datetime.now()

                    if self.output_on_until[output_id] > time_now:
                        remaining_time = (self.output_on_until[output_id] -
                                          time_now).total_seconds()
                    duration_sec = (abs(self.output_last_duration[output_id]) -
                                    remaining_time)
                    timestamp = (datetime.datetime.utcnow() -
                                 datetime.timedelta(seconds=duration_sec))

                    # Store negative duration if a negative duration is received
                    if self.output_last_duration[output_id] < 0:
                        duration_sec = -duration_sec

                    self.output_on_duration[output_id] = False
                    self.output_on_until[output_id] = datetime.datetime.now()

                if self.output_time_turned_on[output_id] is not None:
                    # Write the duration the output was ON to the database
                    # at the timestamp it turned ON
                    duration_sec = (datetime.datetime.now() -
                                    self.output_time_turned_on[output_id]).total_seconds()
                    timestamp = (datetime.datetime.utcnow() -
                                 datetime.timedelta(seconds=duration_sec))
                    self.output_time_turned_on[output_id] = None

                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'duration_sec',
                          duration_sec,
                          timestamp,))
                write_db.start()

            self.output_off_triggered[output_id] = False

        if trigger_conditionals:
            self.check_conditionals(output_id,
                                    state=state,
                                    on_duration=duration,
                                    duty_cycle=duty_cycle)

    def output_switch(self, output_id, state, duty_cycle=None):
        """Conduct the actual execution of GPIO state change, PWM, or command execution"""
        if self.output_type[output_id] == 'wired':
            if state == 'on':
                GPIO.output(self.output_pin[output_id],
                            self.output_trigger[output_id])
            elif state == 'off':
                GPIO.output(self.output_pin[output_id],
                            not self.output_trigger[output_id])

        elif self.output_type[output_id] == 'wireless_433MHz_pi_switch':
            if state == 'on':
                self.wireless_pi_switch[output_id].transmit(
                    int(self.output_on_command[output_id]))
            elif state == 'off':
                self.wireless_pi_switch[output_id].transmit(
                    int(self.output_off_command[output_id]))

        elif self.output_type[output_id] == 'command':
            if state == 'on' and self.output_on_command[output_id]:
                cmd_return, _, cmd_status = cmd_output(
                    self.output_on_command[output_id])
            elif state == 'off' and self.output_off_command[output_id]:
                cmd_return, _, cmd_status = cmd_output(
                    self.output_off_command[output_id])
            else:
                return
            self.logger.debug(
                "Output {state} command returned: "
                "{stat}: '{ret}'".format(
                    state=state,
                    stat=cmd_status,
                    ret=cmd_return))

        elif self.output_type[output_id] == 'command_pwm':
            if self.output_pwm_command[output_id]:
                if state == 'on' and 100 >= duty_cycle >= 0:
                    cmd = self.output_pwm_command[output_id].replace('((duty_cycle))', str(duty_cycle))
                    cmd_return, _, cmd_status = cmd_output(cmd)
                    self.pwm_state[output_id] = abs(duty_cycle)
                elif state == 'off':
                    cmd = self.output_pwm_command[output_id].replace('((duty_cycle))', str(0))
                    cmd_return, _, cmd_status = cmd_output(cmd)
                    self.pwm_state[output_id] = None
                else:
                    return
                self.logger.debug(
                    "Output duty cycle {duty_cycle} command returned: "
                    "{stat}: '{ret}'".format(
                        duty_cycle=duty_cycle,
                        stat=cmd_status,
                        ret=cmd_return))

        elif self.output_type[output_id] == 'pwm':
            import pigpio
            if state == 'on':
                if self.pwm_library[output_id] == 'pigpio_hardware':
                    self.pwm_output[output_id].hardware_PWM(
                        self.output_pin[output_id],
                        self.pwm_hertz[output_id],
                        int(abs(duty_cycle) * 10000))
                elif self.pwm_library[output_id] == 'pigpio_any':
                    self.pwm_output[output_id].set_PWM_frequency(
                        self.output_pin[output_id],
                        self.pwm_hertz[output_id])
                    calc_duty_cycle = int((abs(duty_cycle) / 100.0) * 255)
                    if calc_duty_cycle > 255:
                        calc_duty_cycle = 255
                    if calc_duty_cycle < 0:
                        calc_duty_cycle = 0
                    self.pwm_output[output_id].set_PWM_dutycycle(
                        self.output_pin[output_id],
                        calc_duty_cycle)
                self.pwm_state[output_id] = abs(duty_cycle)
            elif state == 'off':
                if self.pwm_library[output_id] == 'pigpio_hardware':
                    self.pwm_output[output_id].hardware_PWM(
                        self.output_pin[output_id],
                        self.pwm_hertz[output_id], 0)
                elif self.pwm_library[output_id] == 'pigpio_any':
                    self.pwm_output[output_id].set_PWM_frequency(
                        self.output_pin[output_id],
                        self.pwm_hertz[output_id])
                    self.pwm_output[output_id].set_PWM_dutycycle(
                        self.output_pin[output_id], 0)
                self.pwm_state[output_id] = None

    def check_conditionals(self, output_id, state=None, on_duration=None, duty_cycle=None):
        """
        This function is executed whenever an output is turned on or off
        It is responsible for executing Output Conditionals
        """

        # Check On/Off Outputs
        conditionals_output = db_retrieve_table_daemon(Conditional)
        conditionals_output = conditionals_output.filter(
            Conditional.conditional_type == 'conditional_output')
        conditionals_output = conditionals_output.filter(
            Conditional.unique_id_1 == output_id)
        conditionals_output = conditionals_output.filter(
            Conditional.is_activated == True)

        # Find any Output Conditionals with the output_id of the output that
        # just changed its state
        if self.is_on(output_id):
            conditionals_output = conditionals_output.filter(
                or_(Conditional.output_state == 'on',
                    Conditional.output_state == 'on_any'))

            on_with_duration = and_(
                Conditional.output_state == 'on',
                Conditional.output_duration == on_duration)
            conditionals_output = conditionals_output.filter(
                or_(Conditional.output_state == 'on_any',
                    on_with_duration))

        else:
            conditionals_output = conditionals_output.filter(
                Conditional.output_state == 'off')

        # Execute the Conditional Actions for each Output Conditional
        # for this particular Output device
        for each_conditional in conditionals_output.all():
            now = time.time()
            timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
            message = "{ts}\n[Conditional {cid} ({cname})] Output {oid} ({name}) {state}".format(
                ts=timestamp,
                cid=each_conditional.unique_id.split('-')[0],
                cname=each_conditional.name,
                name=each_conditional.name,
                oid=output_id,
                state=each_conditional.output_state)

            self.control.trigger_conditional_actions(
                each_conditional.unique_id, message=message,
                output_state=state, on_duration=on_duration, duty_cycle=duty_cycle)

        # Check PWM Outputs
        conditionals_output_pwm = db_retrieve_table_daemon(Conditional)
        conditionals_output_pwm = conditionals_output_pwm.filter(
            Conditional.conditional_type == 'conditional_output_pwm')
        conditionals_output_pwm = conditionals_output_pwm.filter(
            Conditional.unique_id_1 == output_id)
        conditionals_output_pwm = conditionals_output_pwm.filter(
            Conditional.is_activated == True)

        # Execute the Conditional Actions for each Output Conditional
        # for this particular Output device
        for each_conditional in conditionals_output_pwm.all():
            trigger_conditional = False
            duty_cycle = self.output_state(output_id)

            if duty_cycle == 'off':
                if (each_conditional.direction == 'equal' and
                        each_conditional.output_duty_cycle == 0):
                    trigger_conditional = True
            elif (
                    (each_conditional.direction == 'above' and
                     duty_cycle > each_conditional.output_duty_cycle) or
                    (each_conditional.direction == 'below' and
                     duty_cycle < each_conditional.output_duty_cycle) or
                    (each_conditional.direction == 'equal' and
                     duty_cycle == each_conditional.output_duty_cycle)
                    ):
                trigger_conditional = True

            if not trigger_conditional:
                continue

            now = time.time()
            timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
            message = "{ts}\n[Conditional {cid} ({cname})] Output {oid} " \
                      "({name}) Duty Cycle {actual_dc} {state} {duty_cycle}".format(
                ts=timestamp,
                cid=each_conditional.unique_id.split('-')[0],
                cname=each_conditional.name,
                name=each_conditional.name,
                oid=output_id,
                actual_dc=duty_cycle,
                state = each_conditional.direction,
                duty_cycle = each_conditional.output_duty_cycle)

            self.control.trigger_conditional_actions(
                each_conditional.unique_id, message=message, duty_cycle=duty_cycle)

    def all_outputs_initialize(self, outputs):
        for each_output in outputs:
            self.output_id[each_output.unique_id] = each_output.id
            self.output_unique_id[each_output.unique_id] = each_output.unique_id
            self.output_type[each_output.unique_id] = each_output.output_type
            self.output_name[each_output.unique_id] = each_output.name
            self.output_pin[each_output.unique_id] = each_output.pin
            self.output_amps[each_output.unique_id] = each_output.amps
            self.output_trigger[each_output.unique_id] = each_output.trigger
            self.output_on_at_start[each_output.unique_id] = each_output.on_at_start
            self.output_on_until[each_output.unique_id] = datetime.datetime.now()
            self.output_last_duration[each_output.unique_id] = 0
            self.output_on_duration[each_output.unique_id] = False
            self.output_off_triggered[each_output.unique_id] = False
            self.output_time_turned_on[each_output.unique_id] = None
            self.output_protocol[each_output.unique_id] = each_output.protocol
            self.output_pulse_length[each_output.unique_id] = each_output.pulse_length
            self.output_on_command[each_output.unique_id] = each_output.on_command
            self.output_off_command[each_output.unique_id] = each_output.off_command
            self.output_pwm_command[each_output.unique_id] = each_output.pwm_command

            self.pwm_hertz[each_output.unique_id] = each_output.pwm_hertz
            self.pwm_library[each_output.unique_id] = each_output.pwm_library
            self.pwm_invert_signal[each_output.unique_id] = each_output.pwm_invert_signal
            self.pwm_time_turned_on[each_output.unique_id] = None

            if self.output_pin[each_output.unique_id] is not None:
                self.setup_pin(each_output.unique_id)

            self.logger.debug("{id} ({name}) Initialized".format(
                id=each_output.unique_id.split('-')[0], name=each_output.name))

    def all_outputs_set_state(self):
        """Turn all outputs on that are set to be on at startup"""
        for each_output_id in self.output_id:
            if (self.output_on_at_start[each_output_id] is None or
                    self.output_type[each_output_id] == 'pwm'):
                pass  # Don't turn on or off
            elif self.output_on_at_start[each_output_id]:
                self.output_on_off(each_output_id, 'on',
                                   trigger_conditionals=False)
            else:
                self.output_on_off(each_output_id, 'off',
                                   trigger_conditionals=False)

    def cleanup_gpio(self):
        for each_output_pin in self.output_pin:
            GPIO.cleanup(each_output_pin)

    def add_mod_output(self, output_id):
        """
        Add or modify local dictionary of output settings form SQL database

        When a output is added or modified while the output controller is
        running, these local variables need to also be modified to
        maintain consistency between the SQL database and running controller.

        :param output_id: Unique ID for each output
        :type output_id: str

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str
        """
        try:
            output = db_retrieve_table_daemon(Output, unique_id=output_id)

            self.output_type[output_id] = output.output_type

            # Turn current pin off
            if output_id in self.output_pin and self.output_state(output_id) != 'off':
                self.output_switch(output_id, 'off')

            self.output_id[output_id] = output.id
            self.output_unique_id[output_id] = output.unique_id
            self.output_type[output_id] = output.output_type
            self.output_name[output_id] = output.name
            self.output_pin[output_id] = output.pin
            self.output_amps[output_id] = output.amps
            self.output_trigger[output_id] = output.trigger
            self.output_on_at_start[output_id] = output.on_at_start
            self.output_on_until[output_id] = datetime.datetime.now()
            self.output_time_turned_on[output_id] = None
            self.output_last_duration[output_id] = 0
            self.output_on_duration[output_id] = False
            self.output_off_triggered[output_id] = False
            self.output_protocol[output_id] = output.protocol
            self.output_pulse_length[output_id] = output.pulse_length
            self.output_on_command[output_id] = output.on_command
            self.output_off_command[output_id] = output.off_command
            self.output_pwm_command[output_id] = output.pwm_command

            self.pwm_hertz[output_id] = output.pwm_hertz
            self.pwm_library[output_id] = output.pwm_library
            self.pwm_invert_signal[output_id] = output.pwm_invert_signal

            if self.output_pin[output_id]:
                self.setup_pin(output.unique_id)

            message = "Output {id} ({name}) initialized".format(
                id=self.output_unique_id[output_id].split('-')[0],
                name=self.output_name[output_id])
            self.logger.debug(message)

            return 0, "success"
        except Exception as except_msg:
            self.logger.exception(1)
            return 1, "Add_Mod_Output Error: ID {id}: {err}".format(
                id=output_id, err=except_msg)

    def del_output(self, output_id):
        """
        Delete local variables

        The controller local variables must match the SQL database settings.
        Therefore, this is called when a output has been removed from the SQL
        database.

        :param output_id: Unique ID for each output
        :type output_id: str

        :return: 0 for success, 1 for fail (with error message)
        :rtype: int, str
        """

        # Turn current pin off
        if output_id in self.output_pin and self.output_state(output_id) != 'off':
            self.output_switch(output_id, 'off')

        try:
            self.logger.debug("Output {id} ({name}) Deleted.".format(
                id=self.output_id[output_id], name=self.output_name[output_id]))
            self.output_id.pop(output_id, None)
            self.output_unique_id.pop(output_id, None)
            self.output_type.pop(output_id, None)
            self.output_name.pop(output_id, None)
            self.output_pin.pop(output_id, None)
            self.output_amps.pop(output_id, None)
            self.output_trigger.pop(output_id, None)
            self.output_on_at_start.pop(output_id, None)
            self.output_on_until.pop(output_id, None)
            self.output_last_duration.pop(output_id, None)
            self.output_on_duration.pop(output_id, None)
            self.output_off_triggered.pop(output_id, None)
            self.output_protocol.pop(output_id, None)
            self.output_pulse_length.pop(output_id, None)
            self.output_on_command.pop(output_id, None)
            self.output_off_command.pop(output_id, None)
            self.output_pwm_command.pop(output_id, None)
            self.wireless_pi_switch.pop(output_id, None)

            self.pwm_hertz.pop(output_id, None)
            self.pwm_library.pop(output_id, None)
            self.pwm_invert_signal.pop(output_id, None)
            self.pwm_output.pop(output_id, None)
            self.pwm_state.pop(output_id, None)
            self.pwm_time_turned_on.pop(output_id, None)

            return 0, "success"
        except Exception as msg:
            return 1, "Del_Output Error: ID {id}: {msg}".format(
                id=output_id, msg=msg)

    def output_sec_currently_on(self, output_id):
        if not self.is_on(output_id):
            return 0
        else:
            time_now = datetime.datetime.now()
            sec_currently_on = 0
            if self.output_on_duration[output_id]:
                remaining_time = 0
                if self.output_on_until[output_id] > time_now:
                    remaining_time = (self.output_on_until[output_id] -
                                      time_now).total_seconds()
                sec_currently_on = (
                        abs(self.output_last_duration[output_id]) -
                        remaining_time)
            elif self.output_time_turned_on[output_id]:
                sec_currently_on = (
                        time_now -
                        self.output_time_turned_on[output_id]).total_seconds()
            return sec_currently_on

    def output_setup(self, action, output_id):
        """ Add, delete, or modify a specific output """
        if action in ['Add', 'Modify']:
            return self.add_mod_output(output_id)
        elif action == 'Delete':
            return self.del_output(output_id)
        else:
            return [1, 'Invalid output_setup action']

    def current_amp_load(self):
        """
        Calculate the current amp draw from all the devices connected to
        all outputs currently on.

        :return: total amerage draw
        :rtype: float
        """
        amp_load = 0.0
        for each_output_id, each_output_amps in self.output_amps.items():
            if self.is_on(each_output_id):
                amp_load += each_output_amps
        return amp_load

    def setup_pin(self, output_id):
        """
        Setup pin for this output

        :param output_id: Unique ID for each output
        :type output_id: str

        :rtype: None
        """
        if self.output_type[output_id] == 'wired':
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(True)
                GPIO.setup(self.output_pin[output_id], GPIO.OUT)
                GPIO.output(self.output_pin[output_id],
                            not self.output_trigger[output_id])
                state = 'LOW' if self.output_trigger[output_id] else 'HIGH'
                self.logger.info(
                    "Output {id} setup on pin {pin} and turned OFF "
                    "(OFF={state})".format(id=output_id.split('-')[0],
                                           pin=self.output_pin[output_id],
                                           state=state))
            except Exception as except_msg:
                self.logger.exception(
                    "Output {id} was unable to be setup on pin {pin} with "
                    "trigger={trigger}: {err}".format(
                        id=output_id.split('-')[0],
                        pin=self.output_pin[output_id],
                        trigger=self.output_trigger[output_id],
                        err=except_msg))

        elif self.output_type[output_id] == 'wireless_433MHz_pi_switch':
            from mycodo.devices.wireless_433mhz_pi_switch import Transmit433MHz
            self.wireless_pi_switch[output_id] = Transmit433MHz(
                self.output_pin[output_id],
                protocol=int(self.output_protocol[output_id]),
                pulse_length=int(self.output_pulse_length[output_id]))

        elif self.output_type[output_id] == 'pwm':
            try:
                import pigpio
                self.pwm_output[output_id] = pigpio.pi()
                if self.pwm_library[output_id] == 'pigpio_hardware':
                    self.pwm_output[output_id].hardware_PWM(
                        self.output_pin[output_id], self.pwm_hertz[output_id], 0)
                elif self.pwm_library[output_id] == 'pigpio_any':
                    if self.pwm_output[output_id].connected:
                        self.pwm_output[output_id].set_PWM_frequency(
                            self.output_pin[output_id], self.pwm_hertz[output_id])
                        self.pwm_output[output_id].set_PWM_dutycycle(
                            self.output_pin[output_id], 0)
                    else:
                        self.logger.error("Cound not connect to pigpiod")
                self.pwm_state[output_id] = None
                self.logger.info("PWM {id} setup on pin {pin}".format(
                    id=output_id.split('-')[0], pin=self.output_pin[output_id]))
            except Exception as except_msg:
                self.logger.exception(
                    "PWM {id} was unable to be setup on pin {pin}: "
                    "{err}".format(id=output_id,
                                   pin=self.output_pin[output_id],
                                   err=except_msg))

    def output_state(self, output_id):
        """
        :param output_id: Unique ID for each output
        :type output_id: str

        :return: Whether the output is currently "on" or "off"
        :rtype: str
        """
        if output_id in self.output_type:
            if self.output_type[output_id] == 'wired':
                if (self.output_pin[output_id] is not None and
                        self.output_trigger[output_id] == GPIO.input(self.output_pin[output_id])):
                    return 'on'
            elif self.output_type[output_id] in ['command',
                                                 'wireless_433MHz_pi_switch']:
                if (self.output_time_turned_on[output_id] or
                        self.output_on_until[output_id] > datetime.datetime.now()):
                    return 'on'
            elif self.output_type[output_id] in ['pwm', 'command_pwm']:
                if output_id in self.pwm_state and self.pwm_state[output_id]:
                    return self.pwm_state[output_id]
        return 'off'

    def is_on(self, output_id):
        """
        :param output_id: Unique ID for each output
        :type output_id: str

        :return: Whether the output is currently "ON"
        :rtype: bool
        """
        if (self.output_type[output_id] == 'wired' and
                self._is_setup(output_id)):
            return self.output_trigger[output_id] == GPIO.input(self.output_pin[output_id])
        elif self.output_type[output_id] in ['command',
                                             'command_pwm',
                                             'wireless_433MHz_pi_switch']:
            if self.output_time_turned_on[output_id]:
                return True
        elif self.output_type[output_id] == 'pwm':
            if self.pwm_time_turned_on[output_id]:
                return True
        return False

    def _is_setup(self, output_id):
        """
        This function checks to see if the GPIO pin is setup and ready
        to use. This is for safety and to make sure we don't blow anything.

        :param output_id: Unique ID for each output
        :type output_id: str

        :return: Is it safe to manipulate this output?
        :rtype: bool
        """
        if self.output_type[output_id] == 'wired' and self.output_pin[output_id]:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.output_pin[output_id], GPIO.OUT)
            return True
        elif self.output_type[output_id] in ['command',
                                             'command_pwm',
                                             'wireless_433MHz_pi_switch']:
            return True
        elif self.output_type[output_id] == 'pwm':
            if output_id in self.pwm_output:
                return True
        return False

    def is_running(self):
        return self.running

    def stop_controller(self):
        """Signal to stop the controller"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
