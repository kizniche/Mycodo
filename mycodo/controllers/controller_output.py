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
import sys
import threading
import time

import RPi.GPIO as GPIO
from io import StringIO
from sqlalchemy import and_
from sqlalchemy import or_

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import SMTP
from mycodo.databases.models import Trigger
from mycodo.databases.utils import session_scope
from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.system_pi import cmd_output

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class OutputController(AbstractController, threading.Thread):
    """
    class for controlling outputs

    """
    def __init__(self, ready, debug):
        threading.Thread.__init__(self)
        super(OutputController, self).__init__(ready, unique_id=None, name=__name__)

        self.sample_rate = None

        self.control = DaemonControl()

        self.set_log_level_debug(debug)

        # SMTP options
        self.smtp_max_count = None
        self.smtp_wait_time = None
        self.smtp_timer = None
        self.email_count = None
        self.allowed_to_send_notice = None

        self.output_id = {}
        self.output_unique_id = {}
        self.output_type = {}
        self.output_interface = {}
        self.output_location = {}
        self.output_i2c_bus = {}
        self.output_baud_rate = {}
        self.output_name = {}
        self.output_pin = {}
        self.output_amps = {}
        self.output_on_state = {}
        self.output_state_at_startup = {}
        self.output_state_at_shutdown = {}
        self.trigger_functions_at_start = {}

        self.output_on_until = {}
        self.output_last_duration = {}
        self.output_on_duration = {}
        self.output_off_triggered = {}

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

        # Atlas
        self.output_flow_rate = {}
        self.atlas_command = {}

        self.output_time_turned_on = {}

    def loop(self):
        current_time = datetime.datetime.now()
        for output_id in self.output_id:
            # Is the current time past the time the output was supposed
            # to turn off?
            if (self.output_on_until[output_id] < current_time and
                    self.output_on_duration[output_id] and
                    not self.output_off_triggered[output_id] and
                    (self.output_type[output_id] in ['command',
                                                     'command_pwn',
                                                     'python',
                                                     'python_pwm'] or
                     self.output_pin[output_id] is not None)):

                # Use threads to prevent a slow execution of a
                # process that could slow the loop
                self.output_off_triggered[output_id] = True
                turn_output_off = threading.Thread(
                    target=self.output_on_off,
                    args=(output_id,
                          'off',))
                turn_output_off.start()

    def run_finally(self):
        # Turn all outputs off
        for each_output_id in self.output_id:
            if self.output_state_at_shutdown[each_output_id] is False:
                self.output_on_off(
                    each_output_id, 'off', trigger_conditionals=False)
            elif self.output_state_at_shutdown[each_output_id]:
                self.output_on_off(
                    each_output_id, 'on', trigger_conditionals=False)
        self.cleanup_gpio()

    def initialize_variables(self):
        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_output

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

    def all_outputs_initialize(self, outputs):
        for each_output in outputs:
            self.output_id[each_output.unique_id] = each_output.id
            self.output_unique_id[each_output.unique_id] = each_output.unique_id
            self.output_type[each_output.unique_id] = each_output.output_type
            self.output_interface[each_output.unique_id] = each_output.interface
            self.output_location[each_output.unique_id] = each_output.location
            self.output_i2c_bus[each_output.unique_id] = each_output.i2c_bus
            self.output_baud_rate[each_output.unique_id] = each_output.baud_rate
            self.output_name[each_output.unique_id] = each_output.name
            self.output_pin[each_output.unique_id] = each_output.pin
            self.output_amps[each_output.unique_id] = each_output.amps
            self.output_on_state[each_output.unique_id] = each_output.on_state
            self.output_state_at_startup[each_output.unique_id] = each_output.state_at_startup
            self.output_state_at_shutdown[each_output.unique_id] = each_output.state_at_shutdown
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
            self.output_flow_rate[each_output.unique_id] = each_output.flow_rate
            self.trigger_functions_at_start[each_output.unique_id] = each_output.trigger_functions_at_start

            self.pwm_hertz[each_output.unique_id] = each_output.pwm_hertz
            self.pwm_library[each_output.unique_id] = each_output.pwm_library
            self.pwm_invert_signal[each_output.unique_id] = each_output.pwm_invert_signal
            self.pwm_time_turned_on[each_output.unique_id] = None

            if self.output_pin[each_output.unique_id] is not None:
                self.setup_pin(each_output.unique_id)

            if self.output_type[each_output.unique_id] == 'atlas_ezo_pmp':
                self.setup_atlas_command(each_output.unique_id)

            self.logger.debug("{id} ({name}) Initialized".format(
                id=each_output.unique_id.split('-')[0], name=each_output.name))

    def all_outputs_set_state(self):
        """Turn all outputs on that are set to be on at startup"""
        for each_output_id in self.output_id:
            if (self.output_state_at_startup[each_output_id] is None or
                    self.output_type[each_output_id] == 'pwm'):
                pass  # Don't turn on or off
            elif self.output_state_at_startup[each_output_id]:
                self.output_on_off(
                    each_output_id,
                    'on',
                    trigger_conditionals=self.trigger_functions_at_start[each_output_id])
            else:
                self.output_on_off(
                    each_output_id,
                    'off',
                    trigger_conditionals=False)

    def output_on_off(self, output_id, state,
                      duration=0.0,
                      min_off=0.0,
                      duty_cycle=0.0,
                      trigger_conditionals=True):
        """
        Turn a output on or off
        The GPIO may be either HIGH or LOW to activate a output. This on
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
        self.logger.debug("output_on_off({}, {}, {}, {}, {}, {})".format(
            output_id,
            state,
            duration,
            min_off,
            duty_cycle,
            trigger_conditionals))

        current_time = datetime.datetime.now()

        # Check if output exists
        if output_id not in self.output_id:
            self.logger.warning(
                "Cannot turn {state} Output with ID {id}. "
                "It doesn't exist".format(
                    state=state, id=output_id))
            return 1

        # Atlas EZP-PMP
        if self.output_type[output_id] == 'atlas_ezo_pmp':
            volume_ml = duration
            if state == 'on' and volume_ml > 0:
                # Calculate command, given flow rate
                minutes_to_run = volume_ml / self.output_flow_rate[output_id]

                write_cmd = 'D,{ml:.2f},{min:.2f}'.format(
                        ml=volume_ml, min=minutes_to_run)
                self.logger.debug("EZO-PMP command: {}".format(write_cmd))

                self.atlas_command[output_id].write(write_cmd)

                measurement_dict = {
                    0: {
                        'measurement': 'volume',
                        'unit': 'ml',
                        'value': volume_ml
                    },
                    1: {
                        'measurement': 'time',
                        'unit': 'minute',
                        'value': minutes_to_run
                    }
                }
                add_measurements_influxdb(
                    self.output_unique_id[output_id], measurement_dict)

            elif state == 'off' or volume_ml == 0:
                write_cmd = 'X'
                self.logger.debug("EZO-PMP command: {}".format(write_cmd))
                self.atlas_command[output_id].write(write_cmd)
                measurement_dict = {
                    0: {
                        'measurement': 'volume',
                        'unit': 'ml',
                        'value': 0
                    },
                    1: {
                        'measurement': 'time',
                        'unit': 'minute',
                        'value': 0
                    }
                }
                add_measurements_influxdb(
                    self.output_unique_id[output_id], measurement_dict)

            else:
                self.logger.error(
                    "Invalid parameters: ID: {id}, "
                    "State: {state}, "
                    "Volume: {vol}, "
                    "Flow Rate: {fr}".format(
                        id=output_id,
                        state=state,
                        vol=volume_ml,
                        fr=self.output_flow_rate[output_id]))

        #
        # Signaled to turn output on
        #
        if state == 'on':
            off_until_datetime = db_retrieve_table_daemon(
                Output, unique_id=self.output_unique_id[output_id]).off_until

            # Check if pin is valid
            if (self.output_type[output_id] in [
                    'pwm', 'wired', 'wireless_rpi_rf'] and
                    self.output_pin[output_id] is None):
                self.logger.warning(
                    "Invalid pin for output {id} ({name}): {pin}.".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        pin=self.output_pin[output_id]))
                return 1

            # Check if max amperage will be exceeded
            if self.output_type[output_id] in ['command',
                                               'python',
                                               'wired',
                                               'wireless_rpi_rf']:
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

                # Check if time is greater than off_until to allow an output on
                if off_until_datetime and off_until_datetime > current_time and not self.is_on(output_id):
                    off_seconds = (
                        off_until_datetime - current_time).total_seconds()
                    self.logger.debug(
                        "Output {id} ({name}) instructed to turn on, however "
                        "the output has been instructed to stay off for "
                        "{off_sec:.2f} more seconds.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            off_sec=off_seconds))
                    return 1

            # Turn output on for a duration
            if (self.output_type[output_id] in ['command',
                                                'python',
                                                'wired',
                                                'wireless_rpi_rf'] and
                    duration != 0):

                # Set off_until if min_off is set
                if min_off:
                    dt_off_until = current_time + datetime.timedelta(seconds=abs(duration) + min_off)
                    self.set_off_until(dt_off_until, output_id)

                # Output is already on for a duration
                if self.is_on(output_id) and self.output_on_duration[output_id]:

                    if self.output_on_until[output_id] > current_time:
                        remaining_time = (self.output_on_until[output_id] -
                                          current_time).total_seconds()
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
                        current_time + datetime.timedelta(seconds=abs(duration)))
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
                                  's',
                                  duration_on,),
                            kwargs={'measure': 'duration_time',
                                    'channel': 0,
                                    'timestamp': timestamp})
                        write_db.start()

                    return 0

                # Output is on, but not for a duration
                elif self.is_on(output_id) and not self.output_on_duration:
                    self.output_on_duration[output_id] = True
                    self.output_on_until[output_id] = (
                        current_time + datetime.timedelta(seconds=abs(duration)))
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
            elif self.output_type[output_id] in ['command',
                                                 'python',
                                                 'wired',
                                                 'wireless_rpi_rf']:
                # Don't turn on if already on, except if it's a radio frequency output
                if self.is_on(output_id) and self.output_type[output_id] != 'wireless_rpi_rf':
                    self.logger.debug(
                        "Output {id} ({name}) is already on.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id]))
                    return 1
                else:
                    # Record the time the output was turned on in order to
                    # calculate and log the total duration is was on, when
                    # it eventually turns off.
                    if not self.output_time_turned_on[output_id]:
                        self.output_time_turned_on[output_id] = datetime.datetime.now()
                    self.logger.debug(
                        "Output {id} ({name}) ON at {timeon}.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            timeon=self.output_time_turned_on[output_id]))
                    self.output_switch(output_id, 'on')

            # PWM command output
            elif self.output_type[output_id] in ['command_pwm',
                                                 'python_pwm']:
                self.output_switch(output_id, 'on', duty_cycle=duty_cycle)
                self.logger.debug(
                    "PWM command {id} ({name}) executed with a duty cycle of {dc:.2f}%".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        dc=abs(duty_cycle)))

                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0 - abs(duty_cycle)

                if duty_cycle:
                    self.pwm_time_turned_on[output_id] = datetime.datetime.now()
                else:
                    self.pwm_time_turned_on[output_id] = None

                # Write the duty cycle of the PWM to the database
                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'percent',
                          duty_cycle,),
                    kwargs={'measure': 'duty_cycle',
                            'channel': 0})
                write_db.start()

            # PWM output
            elif self.output_type[output_id] == 'pwm':
                if self.pwm_hertz[output_id] <= 0:
                    self.logger.warning("PWM Hertz must be a positive value")
                    return 1

                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0 - abs(duty_cycle)

                self.output_switch(output_id, 'on', duty_cycle=duty_cycle)
                self.logger.debug(
                    "PWM {id} ({name}) set to a duty cycle of {dc:.2f}% at {hertz} Hz".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        dc=abs(duty_cycle),
                        hertz=self.pwm_hertz[output_id]))

                # Record the time the PWM was turned on
                if duty_cycle:
                    self.pwm_time_turned_on[output_id] = datetime.datetime.now()
                else:
                    self.pwm_time_turned_on[output_id] = None

                # Write the duty cycle of the PWM to the database
                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'percent',
                          duty_cycle,),
                    kwargs={'measure': 'duty_cycle',
                            'channel': 0})
                write_db.start()

        #
        # Signaled to turn output off
        #
        elif state == 'off':

            if not self._is_setup(output_id):
                self.logger.error("Cannot turn off Output {id}: Output not "
                                  "set up properly.".format(id=output_id))
                return

            if (self.output_type[output_id] in ['pwm',
                                                'wired',
                                                'wireless_rpi_rf'] and
                    self.output_pin[output_id] is None):
                return

            self.output_switch(output_id, 'off')

            self.logger.debug("Output {id} ({name}) turned off.".format(
                    id=self.output_id[output_id],
                    name=self.output_name[output_id]))

            # Write PWM duty cycle to database
            if self.output_type[output_id] in ['pwm',
                                               'command_pwm',
                                               'python_pwm']:
                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0
                else:
                    duty_cycle = 0.0

                self.pwm_time_turned_on[output_id] = None

                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'percent',
                          duty_cycle,),
                    kwargs={'measure': 'duty_cycle',
                            'channel': 0})
                write_db.start()

            # Write output duration on to database
            elif (self.output_time_turned_on[output_id] is not None or
                    self.output_on_duration[output_id]):
                duration_sec = None
                timestamp = None
                if self.output_on_duration[output_id]:
                    remaining_time = 0

                    if self.output_on_until[output_id] > current_time:
                        remaining_time = (self.output_on_until[output_id] -
                                          current_time).total_seconds()
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
                          's',
                          duration_sec,),
                    kwargs={'measure': 'duration_time',
                            'channel': 0,
                            'timestamp': timestamp})
                write_db.start()

            self.output_off_triggered[output_id] = False

        if trigger_conditionals:
            self.check_triggers(output_id, on_duration=duration)

    def output_switch(self, output_id, state, duty_cycle=None):
        """Conduct the actual execution of GPIO state change, PWM, or command execution"""
        if self.output_type[output_id] == 'wired':
            if state == 'on':
                GPIO.output(self.output_pin[output_id],
                            self.output_on_state[output_id])
            elif state == 'off':
                GPIO.output(self.output_pin[output_id],
                            not self.output_on_state[output_id])

        elif self.output_type[output_id] == 'wireless_rpi_rf':
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

        elif self.output_type[output_id] == 'python':
            # create file-like string to capture output
            codeOut = StringIO()
            codeErr = StringIO()
            # capture output and errors
            sys.stdout = codeOut
            sys.stderr = codeErr

            pre_command = """
output_id = '{}'
""".format(output_id)

            if state == 'on' and self.output_on_command[output_id]:
                full_command = pre_command + self.output_on_command[output_id]
                exec(full_command, globals())
            elif state == 'off' and self.output_off_command[output_id]:
                full_command = pre_command + self.output_off_command[output_id]
                exec(full_command, globals())
            else:
                return

            # restore stdout and stderr
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            py_error = codeErr.getvalue()
            py_output = codeOut.getvalue()

            self.logger.debug(
                "Output {state} command returned: "
                "Error: {err}, Output: {out}".format(
                    state=state,
                    err=py_error,
                    out=py_output))

            codeOut.close()
            codeErr.close()

        elif self.output_type[output_id] == 'python_pwm':
            if self.output_pwm_command[output_id]:
                # create file-like string to capture output
                codeOut = StringIO()
                codeErr = StringIO()
                # capture output and errors
                sys.stdout = codeOut
                sys.stderr = codeErr

                pre_command = """
output_id = '{}'
""".format(output_id)

                if state == 'on' and 100 >= duty_cycle >= 0:
                    full_command = (pre_command +
                                    self.output_pwm_command[output_id].replace(
                                        '((duty_cycle))', str(duty_cycle)))
                    exec(full_command, globals())
                    self.pwm_state[output_id] = abs(duty_cycle)
                elif state == 'off' or duty_cycle == 0:
                    full_command = (pre_command +
                                    self.output_pwm_command[output_id].replace(
                                        '((duty_cycle))', str(0.0)))
                    exec(full_command, globals())
                    self.pwm_state[output_id] = None
                else:
                    return

                # restore stdout and stderr
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                py_error = codeErr.getvalue()
                py_output = codeOut.getvalue()

                self.logger.debug(
                    "Output duty cycle {duty_cycle} command returned: "
                    "Error: {err}, Output: {out}".format(
                        duty_cycle=duty_cycle,
                        err=py_error,
                        out=py_output))

                codeOut.close()
                codeErr.close()

    def check_triggers(self, output_id, on_duration=None):
        """
        This function is executed whenever an output is turned on or off
        It is responsible for executing Output Triggers
        """
        #
        # Check On/Off Outputs
        #
        trigger_output = db_retrieve_table_daemon(Trigger)
        trigger_output = trigger_output.filter(
            Trigger.trigger_type == 'trigger_output')
        trigger_output = trigger_output.filter(
            Trigger.unique_id_1 == output_id)
        trigger_output = trigger_output.filter(
            Trigger.is_activated == True)

        # Find any Output Triggers with the output_id of the output that
        # just changed its state
        if self.is_on(output_id):
            trigger_output = trigger_output.filter(
                or_(Trigger.output_state == 'on_duration_none',
                    Trigger.output_state == 'on_duration_any',
                    Trigger.output_state == 'on_duration_none_any',
                    Trigger.output_state == 'on_duration_equal',
                    Trigger.output_state == 'on_duration_greater_than',
                    Trigger.output_state == 'on_duration_equal_greater_than',
                    Trigger.output_state == 'on_duration_less_than',
                    Trigger.output_state == 'on_duration_equal_less_than'))

            on_duration_none = and_(
                Trigger.output_state == 'on_duration_none',
                on_duration == 0.0)

            on_duration_any = and_(
                Trigger.output_state == 'on_duration_any',
                bool(on_duration))

            on_duration_none_any = Trigger.output_state == 'on_duration_none_any'

            on_duration_equal = and_(
                Trigger.output_state == 'on_duration_equal',
                Trigger.output_duration == on_duration)

            on_duration_greater_than = and_(
                Trigger.output_state == 'on_duration_greater_than',
                on_duration > Trigger.output_duration)

            on_duration_equal_greater_than = and_(
                Trigger.output_state == 'on_duration_equal_greater_than',
                on_duration >= Trigger.output_duration)

            on_duration_less_than = and_(
                Trigger.output_state == 'on_duration_less_than',
                on_duration < Trigger.output_duration)

            on_duration_equal_less_than = and_(
                Trigger.output_state == 'on_duration_equal_less_than',
                on_duration <= Trigger.output_duration)

            trigger_output = trigger_output.filter(
                or_(on_duration_none,
                    on_duration_any,
                    on_duration_none_any,
                    on_duration_equal,
                    on_duration_greater_than,
                    on_duration_equal_greater_than,
                    on_duration_less_than,
                    on_duration_equal_less_than))
        else:
            trigger_output = trigger_output.filter(
                Trigger.output_state == 'off')

        # Execute the Trigger Actions for each Output Trigger
        # for this particular Output device
        for each_trigger in trigger_output.all():
            now = time.time()
            timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
            message = "{ts}\n[Trigger {cid} ({cname})] Output {oid} ({name}) {state}".format(
                ts=timestamp,
                cid=each_trigger.unique_id.split('-')[0],
                cname=each_trigger.name,
                name=each_trigger.name,
                oid=output_id,
                state=each_trigger.output_state)

            self.control.trigger_all_actions(
                each_trigger.unique_id,
                message=message)

        #
        # Check PWM Outputs
        #
        trigger_output_pwm = db_retrieve_table_daemon(Trigger)
        trigger_output_pwm = trigger_output_pwm.filter(
            Trigger.trigger_type == 'trigger_output_pwm')
        trigger_output_pwm = trigger_output_pwm.filter(
            Trigger.unique_id_1 == output_id)
        trigger_output_pwm = trigger_output_pwm.filter(
            Trigger.is_activated == True)

        # Execute the Trigger Actions for each Output Trigger
        # for this particular Output device
        for each_trigger in trigger_output_pwm.all():
            trigger_trigger = False
            duty_cycle = self.output_state(output_id)

            if duty_cycle == 'off':
                if (each_trigger.output_state == 'equal' and
                        each_trigger.output_duty_cycle == 0):
                    trigger_trigger = True
            elif (
                    (each_trigger.output_state == 'above' and
                     duty_cycle > each_trigger.output_duty_cycle) or
                    (each_trigger.output_state == 'below' and
                     duty_cycle < each_trigger.output_duty_cycle) or
                    (each_trigger.output_state == 'equal' and
                     duty_cycle == each_trigger.output_duty_cycle)
                    ):
                trigger_trigger = True

            if not trigger_trigger:
                continue

            now = time.time()
            timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
            message = "{ts}\n[Trigger {cid} ({cname})] Output {oid} " \
                      "({name}) Duty Cycle {actual_dc} {state} {duty_cycle}".format(
                        ts=timestamp,
                        cid=each_trigger.unique_id.split('-')[0],
                        cname=each_trigger.name,
                        name=each_trigger.name,
                        oid=output_id,
                        actual_dc=duty_cycle,
                        state=each_trigger.output_state,
                        duty_cycle=each_trigger.output_duty_cycle)

            self.control.trigger_all_actions(
                each_trigger.unique_id, message=message)

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
                self.output_on_off(output_id, 'off')

            self.output_id[output_id] = output.id
            self.output_unique_id[output_id] = output.unique_id
            self.output_type[output_id] = output.output_type
            self.output_interface[output_id] = output.interface
            self.output_i2c_bus[output_id] = output.i2c_bus
            self.output_location[output_id] = output.location
            self.output_baud_rate[output_id] = output.baud_rate
            self.output_name[output_id] = output.name
            self.output_pin[output_id] = output.pin
            self.output_amps[output_id] = output.amps
            self.output_on_state[output_id] = output.on_state
            self.output_state_at_startup[output_id] = output.state_at_startup
            self.output_state_at_shutdown[output_id] = output.state_at_shutdown
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
            self.output_flow_rate[output_id] = output.flow_rate
            self.trigger_functions_at_start[output_id] = output.trigger_functions_at_start

            self.pwm_hertz[output_id] = output.pwm_hertz
            self.pwm_library[output_id] = output.pwm_library
            self.pwm_invert_signal[output_id] = output.pwm_invert_signal
            self.pwm_time_turned_on[output_id] = None

            if self.output_pin[output_id]:
                self.setup_pin(output.unique_id)

            if self.output_type[output.unique_id] == 'atlas_ezo_pmp':
                self.setup_atlas_command(output.unique_id)

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
            self.output_interface.pop(output_id, None)
            self.output_location.pop(output_id, None)
            self.output_i2c_bus.pop(output_id, None)
            self.output_baud_rate.pop(output_id, None)
            self.output_name.pop(output_id, None)
            self.output_pin.pop(output_id, None)
            self.output_amps.pop(output_id, None)
            self.output_on_state.pop(output_id, None)
            self.output_state_at_startup.pop(output_id, None)
            self.output_state_at_shutdown.pop(output_id, None)
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
            self.trigger_functions_at_start.pop(output_id, None)

            self.pwm_hertz.pop(output_id, None)
            self.pwm_library.pop(output_id, None)
            self.pwm_invert_signal.pop(output_id, None)
            self.pwm_output.pop(output_id, None)
            self.pwm_state.pop(output_id, None)
            self.pwm_time_turned_on.pop(output_id, None)

            self.output_flow_rate.pop(output_id, None)
            self.atlas_command.pop(output_id, None)

            return 0, "success"
        except Exception as msg:
            return 1, "Del_Output Error: ID {id}: {msg}".format(
                id=output_id, msg=msg)

    def setup_atlas_command(self, output_id):
        if self.output_interface[output_id] == 'I2C':
            self.atlas_command[output_id] = AtlasScientificI2C(
                i2c_address=int(str(self.output_location[output_id]), 16),
                i2c_bus=self.output_i2c_bus[output_id])
        elif self.output_interface[output_id] == 'UART':
            self.atlas_command[output_id] = AtlasScientificUART(
                self.output_location[output_id],
                baudrate=self.output_baud_rate[output_id])

    def output_sec_currently_on(self, output_id):
        if not self.is_on(output_id):
            return 0
        else:
            current_time = datetime.datetime.now()
            sec_currently_on = 0
            if self.output_on_duration[output_id]:
                remaining_time = 0
                if self.output_on_until[output_id] > current_time:
                    remaining_time = (
                        self.output_on_until[output_id] -
                        current_time).total_seconds()
                sec_currently_on = (
                    abs(self.output_last_duration[output_id]) -
                    remaining_time)
            elif self.output_time_turned_on[output_id]:
                sec_currently_on = (
                    current_time -
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
                            not self.output_on_state[output_id])
                state = 'LOW' if self.output_on_state[output_id] else 'HIGH'
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
                        trigger=self.output_on_state[output_id],
                        err=except_msg))

        elif self.output_type[output_id] == 'wireless_rpi_rf':
            from mycodo.devices.wireless_rpi_rf import Transmit433MHz
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
                        self.output_on_state[output_id] == GPIO.input(self.output_pin[output_id])):
                    return 'on'
            elif self.output_type[output_id] in ['command',
                                                 'python',
                                                 'wireless_rpi_rf']:
                if (self.output_time_turned_on[output_id] or
                        self.output_on_until[output_id] > datetime.datetime.now()):
                    return 'on'
            elif self.output_type[output_id] in ['pwm',
                                                 'command_pwm',
                                                 'python_pwm']:
                if output_id in self.pwm_state and self.pwm_state[output_id]:
                    return self.pwm_state[output_id]
            elif self.output_type[output_id] == 'atlas_ezo_pmp':
                device_measurements = db_retrieve_table_daemon(
                    DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == output_id)
                for each_dev_meas in device_measurements:
                    if each_dev_meas.unit == 'minute':
                        last_measurement = read_last_influxdb(
                            output_id,
                            each_dev_meas.unit,
                            each_dev_meas.measurement,
                            each_dev_meas.channel)
                        if last_measurement:
                            datetime_ts = datetime.datetime.strptime(
                                last_measurement[0][:-7], '%Y-%m-%dT%H:%M:%S.%f')
                            minutes_on = last_measurement[1]
                            ts_pmp_off = datetime_ts + datetime.timedelta(minutes=minutes_on)
                            now = datetime.datetime.utcnow()
                            is_on = bool(now < ts_pmp_off)
                            if is_on:
                                return 'on'
        return 'off'

    def output_on_duration(self, output_id):
        """
        :param output_id: Unique ID for each output
        :type output_id: str

        :return: How long the output has been on for
        :rtype: float
        """
        if output_id in self.output_type:
            if self.output_type[output_id] == 'wired':
                if (self.output_pin[output_id] is not None and
                        self.output_on_state[output_id] == GPIO.input(self.output_pin[output_id])):
                    return 'on'
            elif self.output_type[output_id] in ['command',
                                                 'python',
                                                 'wireless_rpi_rf']:
                if (self.output_time_turned_on[output_id] or
                        self.output_on_until[output_id] > datetime.datetime.now()):
                    return 'on'
            elif self.output_type[output_id] in ['pwm',
                                                 'command_pwm',
                                                 'python_pwm']:
                if output_id in self.pwm_state and self.pwm_state[output_id]:
                    return self.pwm_state[output_id]
        return 0

    def set_off_until(self, dt_off_until, output_id):
        with session_scope(MYCODO_DB_PATH) as new_session:
            mod_cont = new_session.query(Output).filter(
                Output.unique_id == self.output_unique_id[output_id]).first()
            mod_cont.off_until = dt_off_until
            new_session.commit()

    def is_on(self, output_id):
        """
        :param output_id: Unique ID for each output
        :type output_id: str

        :return: Whether the output is currently "ON"
        :rtype: bool
        """
        if (self.output_type[output_id] == 'wired' and
                self._is_setup(output_id)):
            return self.output_on_state[output_id] == GPIO.input(
                self.output_pin[output_id])
        elif self.output_type[output_id] in ['command',
                                             'command_pwm',
                                             'python',
                                             'python_pwm',
                                             'wireless_rpi_rf']:
            if self.output_time_turned_on[output_id] or self.output_on_duration[output_id]:
                return True
        elif self.output_type[output_id] == 'pwm':
            if self.pwm_time_turned_on[output_id]:
                return True
        elif self.output_type[output_id] == 'atlas_ezo_pmp':
            device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == output_id)
            for each_dev_meas in device_measurements:
                if each_dev_meas.unit == 'minute':
                    last_measurement = read_last_influxdb(
                        output_id,
                        each_dev_meas.unit,
                        each_dev_meas.measurement,
                        each_dev_meas.channel)
                    if last_measurement:
                        datetime_ts = datetime.datetime.strptime(
                            last_measurement[0][:-7], '%Y-%m-%dT%H:%M:%S.%f')
                        minutes_on = last_measurement[1]
                        ts_pmp_off = datetime_ts + datetime.timedelta(minutes=minutes_on)
                        now = datetime.datetime.utcnow()
                        is_on = bool(now < ts_pmp_off)
                        if is_on:
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
                                             'python',
                                             'python_pwm',
                                             'wireless_rpi_rf',
                                             'atlas_ezo_pmp']:
            return True
        elif self.output_type[output_id] == 'pwm':
            if output_id in self.pwm_output:
                return True
        return False
