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

from io import StringIO
from sqlalchemy import and_
from sqlalchemy import or_

from mycodo.config import OUTPUTS_PWM
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import SMTP
from mycodo.databases.models import Trigger
from mycodo.databases.utils import session_scope
from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import return_measurement_info

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
        self.output_mode = {}
        self.output_interface = {}
        self.output_location = {}
        self.output_i2c_bus = {}
        self.output_baud_rate = {}
        self.output_name = {}
        self.output_pin = {}
        self.output_amps = {}
        self.output_on_state = {}
        self.output_state_startup = {}
        self.output_startup_value = {}
        self.output_state_shutdown = {}
        self.output_shutdown_value = {}
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
        self.pwm_duty_cycle = {}

        # Atlas
        self.output_flow_rate = {}
        self.atlas_command = {}

        self.output_time_turned_on = {}

    def loop(self):
        """ Main loop of the output controller """
        for output_id in self.output_id:
            # Is the current time past the time the output was supposed
            # to turn off?
            if (self.output_on_until[output_id] < datetime.datetime.now() and
                    self.output_on_duration[output_id] and
                    not self.output_off_triggered[output_id] and
                    (self.output_type[output_id] in ['command',
                                                     'command_pwn',
                                                     'python',
                                                     'python_pwm'] or
                     self.output_pin[output_id] is not None)):

                # Use a thread to prevent blocking the loop
                self.output_off_triggered[output_id] = True
                turn_output_off = threading.Thread(
                    target=self.output_on_off,
                    args=(output_id,
                          'off',))
                turn_output_off.start()

    def run_finally(self):
        """ Run when the controller is shutting down """
        # Turn all outputs to their shutdown state
        for each_output_id in self.output_id:
            if self.output_state_shutdown[each_output_id] == '0':
                self.logger.info(
                    "Setting Output {id} shutdown state to OFF".format(
                        id=each_output_id.split('-')[0]))
                self.output_on_off(
                    each_output_id, 'off', trigger_conditionals=False)

            elif self.output_state_shutdown[each_output_id] == '1':
                self.logger.info(
                    "Setting Output {id} shutdown state to ON".format(
                        id=each_output_id.split('-')[0]))
                self.output_on_off(
                    each_output_id, 'on', trigger_conditionals=False)

            elif self.output_state_shutdown[each_output_id] == 'set_duty_cycle':
                self.logger.info(
                    "Setting Output {id} shutdown duty cycle to user-set value "
                    "of {dc} %".format(
                        id=each_output_id.split('-')[0],
                        dc=self.output_shutdown_value[each_output_id]))
                self.output_on_off(
                    each_output_id,
                    'on',
                    duty_cycle=self.output_shutdown_value[each_output_id],
                    trigger_conditionals=self.trigger_functions_at_start[each_output_id])

        self.cleanup_gpio()

    def initialize_variables(self):
        """ Begin initializing output parameters """
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
        """ Initialize all output variables and classes """
        for each_output in outputs:
            self.output_id[each_output.unique_id] = each_output.id
            self.output_unique_id[each_output.unique_id] = each_output.unique_id
            self.output_type[each_output.unique_id] = each_output.output_type
            self.output_mode[each_output.unique_id] = each_output.output_mode
            self.output_interface[each_output.unique_id] = each_output.interface
            self.output_location[each_output.unique_id] = each_output.location
            self.output_i2c_bus[each_output.unique_id] = each_output.i2c_bus
            self.output_baud_rate[each_output.unique_id] = each_output.baud_rate
            self.output_name[each_output.unique_id] = each_output.name
            self.output_pin[each_output.unique_id] = each_output.pin
            self.output_amps[each_output.unique_id] = each_output.amps
            self.output_on_state[each_output.unique_id] = each_output.on_state
            self.output_state_startup[each_output.unique_id] = each_output.state_startup
            self.output_startup_value[each_output.unique_id] = each_output.startup_value
            self.output_state_shutdown[each_output.unique_id] = each_output.state_shutdown
            self.output_shutdown_value[each_output.unique_id] = each_output.shutdown_value
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
            self.pwm_duty_cycle[each_output.unique_id] = 0

            if self.output_pin[each_output.unique_id] is not None:
                self.setup_pin(each_output.unique_id)

            if self.output_type[each_output.unique_id] == 'atlas_ezo_pmp':
                self.setup_atlas_command(each_output.unique_id)

            self.logger.debug("{id} ({name}) Initialized".format(
                id=each_output.unique_id.split('-')[0], name=each_output.name))

    def all_outputs_set_state(self):
        """Turn all outputs on that are set to be on at startup"""
        for each_output_id in self.output_id:
            if self.output_state_startup[each_output_id] is None:
                pass  # Don't turn on or off

            # PWM Outputs
            elif self.output_type[each_output_id] in OUTPUTS_PWM:
                if self.output_state_startup[each_output_id] == '0':
                    self.logger.info(
                        "Setting Output {id} startup duty cycle to 0 %".format(
                            id=each_output_id.split('-')[0]))
                    self.output_on_off(
                        each_output_id,
                        'off',
                        trigger_conditionals=self.trigger_functions_at_start[each_output_id])

                elif self.output_state_startup[each_output_id] == 'set_duty_cycle':
                    self.logger.info(
                        "Setting Output {id} startup duty cycle to user-set"
                        " value of {dc} %".format(
                            id=each_output_id.split('-')[0],
                            dc=self.output_startup_value[each_output_id]))
                    self.output_on_off(
                        each_output_id,
                        'on',
                        duty_cycle=self.output_startup_value[each_output_id],
                        trigger_conditionals=self.trigger_functions_at_start[each_output_id])

                elif self.output_state_startup[each_output_id] == 'last_duty_cycle':
                    device_measurement = db_retrieve_table_daemon(
                        DeviceMeasurements).filter(
                        DeviceMeasurements.device_id == each_output_id).all()
                    measurement = None
                    for each_meas in device_measurement:
                        if each_meas.measurement == 'duty_cycle':
                            measurement = each_meas
                    channel, unit, measurement = return_measurement_info(
                        measurement, None)

                    last_measurement = read_last_influxdb(
                        each_output_id,
                        unit,
                        channel,
                        measure=measurement,
                        duration_sec=None)

                    if last_measurement:
                        self.logger.info(
                            "Setting Output {id} startup duty cycle to last"
                            " known value of {dc} %".format(
                                id=each_output_id.split('-')[0],
                                dc=last_measurement[1]))
                        self.output_on_off(
                            each_output_id,
                            'on',
                            duty_cycle=last_measurement[1],
                            trigger_conditionals=self.trigger_functions_at_start[each_output_id])
                    else:
                        self.logger.error(
                            "Output {id} instructed at startup to be set to"
                            " the last known duty cycle, but a last known "
                            "duty cycle could not be found in the measurement"
                            " database".format(
                                id=each_output_id.split('-')[0]))

            # Non-PWM outputs
            elif self.output_state_startup[each_output_id] == '1':
                self.logger.info(
                    "Setting Output {id} startup state to ON".format(
                        id=each_output_id.split('-')[0]))
                self.output_on_off(
                    each_output_id,
                    'on',
                    trigger_conditionals=self.trigger_functions_at_start[each_output_id])

            elif self.output_state_startup[each_output_id] == '0':
                self.logger.info(
                    "Setting Output {id} startup state to OFF".format(
                        id=each_output_id.split('-')[0]))
                self.output_on_off(
                    each_output_id,
                    'off',
                    trigger_conditionals=False)

    def output_duty_cycle(self, output_id, duty_cycle, trigger_conditionals):
        """
        Sets the output duty_cycle
        :param output_id:
        :param duty_cycle:
        :param trigger_conditionals:
        :return:
        """

        # Check if output exists
        if output_id not in self.output_id:
            self.logger.warning(
                "Cannot set duty cycle of output with ID {id}. "
                "It doesn't exist".format(id=output_id))
            return 1, 'output doe not exist'

        if self.output_type[output_id] not in OUTPUTS_PWM:
            return 1, 'Output is not a PWM output. Can only set a duty cycle for PWM outputs.'
        else:
            return self.output_on_off(
                output_id,
                'on',
                duty_cycle=duty_cycle,
                trigger_conditionals=trigger_conditionals)

    def output_on_off(self, output_id, state,
                      amount=0.0,
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
        :param state: What state is desired? 'on', 1, True or 'off', 0, False
        :type state: str
        :param amount: If state is 'on', an amount can be set to turn the output off after
        :type amount: float
        :param min_off: Don't turn on if not off for at least this amount (0 = disabled)
        :type min_off: float
        :param duty_cycle: Duty cycle of PWM output
        :type duty_cycle: float
        :param trigger_conditionals: Whether to trigger conditionals to act or not
        :type trigger_conditionals: bool
        """
        msg = ''

        self.logger.debug("output_on_off({}, {}, {}, {}, {}, {})".format(
            output_id,
            state,
            amount,
            min_off,
            duty_cycle,
            trigger_conditionals))

        if amount is None:
            amount = 0

        if state not in ['on', 1, True, 'off', 0, False]:
            return 1, 'state not "on", 1, True, "off", 0, or False'
        elif state in ['on', 1, True]:
            state = 'on'
        elif state in ['off', 0, False]:
            state = 'off'

        current_time = datetime.datetime.now()

        output_is_on = self.is_on(output_id)

        # Check if output exists
        if output_id not in self.output_id:
            self.logger.warning(
                "Cannot turn {state} Output with ID {id}. "
                "It doesn't exist".format(
                    state=state, id=output_id))
            return 1, 'output doe not exist'

        # Atlas EZP-PMP
        if self.output_type[output_id] == 'atlas_ezo_pmp':
            volume_ml = amount
            if state == 'on' and volume_ml > 0:
                if self.output_mode[output_id] == 'fastest_flow_rate':
                    minutes_to_run = volume_ml * 105
                    write_cmd = 'D,{ml:.2f}'.format(ml=volume_ml)
                elif self.output_mode[output_id] == 'specify_flow_rate':
                    # Calculate command, given flow rate
                    minutes_to_run = volume_ml / self.output_flow_rate[output_id]
                    write_cmd = 'D,{ml:.2f},{min:.2f}'.format(
                            ml=volume_ml, min=minutes_to_run)
                else:
                    msg = "Invalid output_mode: '{}'".format(
                        self.output_mode[output_id])
                    self.logger.error(msg)
                    return 1, msg

                self.logger.debug("EZO-PMP command: {}".format(write_cmd))
                self.atlas_command[output_id].write(write_cmd)

                msg = 'pump turned on'

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

            elif state == 'off' or volume_ml <= 0:
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
                msg = "Invalid parameters: ID: {id}, " \
                      "State: {state}, " \
                      "Volume: {vol}, " \
                      "Flow Rate: {fr}".format(
                          id=output_id,
                          state=state,
                          vol=volume_ml,
                          fr=self.output_flow_rate[output_id])
                self.logger.error(msg)
                return 1, msg

        #
        # Signaled to turn output on
        #
        elif state == 'on':
            off_until_datetime = db_retrieve_table_daemon(
                Output, unique_id=self.output_unique_id[output_id]).off_until

            # Check if pin is valid
            if (self.output_type[output_id] in ['pwm',
                                                'wired',
                                                'wireless_rpi_rf'] and
                    self.output_pin[output_id] is None):
                msg = "Invalid pin for output {id} ({name}): {pin}.".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        pin=self.output_pin[output_id])
                self.logger.warning(msg)
                return 1, msg

            # Checks if device is not on and instructed to turn on
            if (self.output_type[output_id] in ['command',
                                                'python',
                                                'wired',
                                                'wireless_rpi_rf'] and
                    not output_is_on):
                # Check if max amperage will be exceeded
                current_amps = self.current_amp_load()
                max_amps = db_retrieve_table_daemon(
                    Misc, entry='first').max_amps
                if current_amps + self.output_amps[output_id] > max_amps:
                    msg = "Cannot turn output {} ({}) On. If this output " \
                          "turns on, there will be {} amps being drawn, " \
                          "which exceeds the maximum set draw of {} " \
                          "amps.".format(
                            self.output_id[output_id],
                            self.output_name[output_id],
                            current_amps,
                            max_amps)
                    self.logger.warning(msg)
                    return 1, msg

                # Check if time is greater than off_until to allow an output on
                if off_until_datetime and off_until_datetime > current_time:
                    off_seconds = (
                        off_until_datetime - current_time).total_seconds()
                    msg = "Output {id} ({name}) instructed to turn on, " \
                          "however the output has been instructed to stay " \
                          "off for {off_sec:.2f} more seconds.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            off_sec=off_seconds)
                    self.logger.debug(msg)
                    return 1, msg

            # Turn output on for an amount
            if (self.output_type[output_id] in ['command',
                                                'python',
                                                'wired',
                                                'wireless_rpi_rf'] and
                    amount != 0):

                # Set off_until if min_off is set
                if min_off:
                    dt_off_until = current_time + datetime.timedelta(seconds=abs(amount) + min_off)
                    self.set_off_until(dt_off_until, output_id)

                # Output is already on for an amount
                if output_is_on and self.output_on_duration[output_id]:

                    if self.output_on_until[output_id] > current_time:
                        remaining_time = (self.output_on_until[output_id] -
                                          current_time).total_seconds()
                    else:
                        remaining_time = 0

                    time_on = abs(self.output_last_duration[output_id]) - remaining_time
                    msg = "Output {rid} ({rname}) is already on for an " \
                          "amount of {ron:.2f} seconds (with {rremain:.2f} " \
                          "seconds remaining). Recording the amount of time " \
                          "the output has been on ({rbeenon:.2f} sec) and " \
                          "updating the amount to {rnewon:.2f} " \
                          "seconds.".format(
                            rid=self.output_id[output_id],
                            rname=self.output_name[output_id],
                            ron=abs(self.output_last_duration[output_id]),
                            rremain=remaining_time,
                            rbeenon=time_on,
                            rnewon=abs(amount))
                    self.logger.debug(msg)
                    self.output_on_until[output_id] = (
                        current_time + datetime.timedelta(seconds=abs(amount)))
                    self.output_last_duration[output_id] = amount

                    # Write the amount the output was ON to the
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

                    return 0, msg

                # Output is on, but not for an amount
                elif output_is_on and not self.output_on_duration:

                    self.output_on_duration[output_id] = True
                    self.output_on_until[output_id] = (
                        current_time + datetime.timedelta(seconds=abs(amount)))
                    self.output_last_duration[output_id] = amount
                    msg = "Output {id} ({name}) is currently on without an " \
                          "amount. Turning into an amount of {dur:.1f} " \
                          "seconds.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            dur=abs(amount))
                    self.logger.debug(msg)
                    return 0, msg

                # Output is not already on
                else:
                    msg = "Output {id} ({name}) on for {dur:.1f} " \
                          "seconds.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            dur=abs(amount))
                    self.logger.debug(msg)
                    self.output_switch(output_id, 'on')
                    self.output_on_until[output_id] = (
                            datetime.datetime.now() +
                            datetime.timedelta(seconds=abs(amount)))
                    self.output_last_duration[output_id] = amount
                    self.output_on_duration[output_id] = True

            # Just turn output on
            elif self.output_type[output_id] in ['command',
                                                 'python',
                                                 'wired',
                                                 'wireless_rpi_rf']:

                # Don't turn on if already on, except if it's a radio frequency output
                if output_is_on and self.output_type[output_id] != 'wireless_rpi_rf':
                    msg = "Output {id} ({name}) is already on.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id])
                    self.logger.debug(msg)
                    return 1, msg
                else:
                    # Record the time the output was turned on in order to
                    # calculate and log the total amount is was on, when
                    # it eventually turns off.
                    if not self.output_time_turned_on[output_id]:
                        self.output_time_turned_on[output_id] = datetime.datetime.now()
                    msg = "Output {id} ({name}) ON at {timeon}.".format(
                            id=self.output_id[output_id],
                            name=self.output_name[output_id],
                            timeon=self.output_time_turned_on[output_id])
                    self.logger.debug(msg)
                    self.output_switch(output_id, 'on')

            # PWM output
            elif self.output_type[output_id] in OUTPUTS_PWM:

                if (self.output_type[output_id] == 'pwm' and
                        self.pwm_hertz[output_id] <= 0):
                    msg = 'PWM Hertz must be a positive value'
                    self.logger.warning(msg)
                    return 1, msg

                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0 - abs(duty_cycle)

                self.output_switch(output_id, 'on', duty_cycle=duty_cycle)
                msg = "PWM {id} ({name}) set to a duty cycle of {dc:.2f}% " \
                      "at {hertz} Hz".format(
                        id=self.output_id[output_id],
                        name=self.output_name[output_id],
                        dc=abs(duty_cycle),
                        hertz=self.pwm_hertz[output_id])
                self.logger.debug(msg)

                # Record the time the PWM was turned on
                if duty_cycle:
                    self.pwm_time_turned_on[output_id] = datetime.datetime.now()
                    self.pwm_duty_cycle[output_id] = duty_cycle
                else:
                    self.pwm_time_turned_on[output_id] = None
                    self.pwm_duty_cycle[output_id] = 0

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
                msg = "Cannot turn off Output {id}: Output not set up " \
                      "properly.".format(id=output_id)
                self.logger.error(msg)
                return 1, msg

            if (self.output_type[output_id] in ['pwm',
                                                'wired',
                                                'wireless_rpi_rf'] and
                    self.output_pin[output_id] is None):
                msg = 'pin must be set'
                self.logger.error(msg)
                return 1, msg

            self.output_switch(output_id, 'off')

            msg = "Output {id} ({name}) turned off.".format(
                    id=self.output_id[output_id],
                    name=self.output_name[output_id])
            self.logger.debug(msg)

            # Write PWM duty cycle to database
            if self.output_type[output_id] in OUTPUTS_PWM:

                if self.pwm_invert_signal[output_id]:
                    duty_cycle = 100.0
                else:
                    duty_cycle = 0.0

                self.pwm_time_turned_on[output_id] = None
                self.pwm_duty_cycle[output_id] = 0

                write_db = threading.Thread(
                    target=write_influxdb_value,
                    args=(self.output_unique_id[output_id],
                          'percent',
                          duty_cycle,),
                    kwargs={'measure': 'duty_cycle',
                            'channel': 0})
                write_db.start()

            # Write output amount to database
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

                    # Store negative amount if a negative amount is received
                    if self.output_last_duration[output_id] < 0:
                        duration_sec = -duration_sec

                    self.output_on_duration[output_id] = False
                    self.output_on_until[output_id] = datetime.datetime.now()

                if self.output_time_turned_on[output_id] is not None:
                    # Write the amount the output was ON to the database
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
            self.check_triggers(output_id, on_duration=amount)

        return 0, msg

    def output_switch(self, output_id, state, duty_cycle=None):
        """Conduct the actual execution of GPIO state change, PWM, or command execution"""

        if state not in ['on', 1, True, 'off', 0, False]:
            return 1, 'state not "on", 1, True, "off", 0, or False'
        elif state in ['on', 1, True]:
            state = 'on'
        elif state in ['off', 0, False]:
            state = 'off'

        if self.output_type[output_id] == 'wired':
            try:
                import RPi.GPIO as GPIO
                if state == 'on':
                    GPIO.output(self.output_pin[output_id],
                                self.output_on_state[output_id])
                elif state == 'off':
                    GPIO.output(self.output_pin[output_id],
                                not self.output_on_state[output_id])
            except:
                self.logger.error(
                    "RPi.GPIO and Raspberry Pi required for this action")

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
        try:
            import RPi.GPIO as GPIO
            for each_output_pin in self.output_pin:
                GPIO.cleanup(each_output_pin)
        except:
            self.logger.error("RPi.GPIO and Raspberry Pi required for this action")

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
            self.output_mode[output_id] = output.output_mode
            self.output_interface[output_id] = output.interface
            self.output_i2c_bus[output_id] = output.i2c_bus
            self.output_location[output_id] = output.location
            self.output_baud_rate[output_id] = output.baud_rate
            self.output_name[output_id] = output.name
            self.output_pin[output_id] = output.pin
            self.output_amps[output_id] = output.amps
            self.output_on_state[output_id] = output.on_state
            self.output_state_startup[output_id] = output.state_startup
            self.output_startup_value[output_id] = output.startup_value
            self.output_state_shutdown[output_id] = output.state_shutdown
            self.output_shutdown_value[output_id] = output.shutdown_value
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
            self.output_mode.pop(output_id, None)
            self.output_interface.pop(output_id, None)
            self.output_location.pop(output_id, None)
            self.output_i2c_bus.pop(output_id, None)
            self.output_baud_rate.pop(output_id, None)
            self.output_name.pop(output_id, None)
            self.output_pin.pop(output_id, None)
            self.output_amps.pop(output_id, None)
            self.output_on_state.pop(output_id, None)
            self.output_state_startup.pop(output_id, None)
            self.output_startup_value.pop(output_id, None)
            self.output_state_shutdown.pop(output_id, None)
            self.output_shutdown_value.pop(output_id, None)
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
        """ Initialize the appropriate Atlas Scientific class for th einterface type """
        if self.output_interface[output_id] == 'FTDI':
            self.atlas_command[output_id] = AtlasScientificFTDI(
                self.output_location[output_id])

        elif self.output_interface[output_id] == 'I2C':
            self.atlas_command[output_id] = AtlasScientificI2C(
                i2c_address=int(str(self.output_location[output_id]), 16),
                i2c_bus=self.output_i2c_bus[output_id])

        elif self.output_interface[output_id] == 'UART':
            self.atlas_command[output_id] = AtlasScientificUART(
                self.output_location[output_id],
                baudrate=self.output_baud_rate[output_id])

    def output_sec_currently_on(self, output_id):
        """ Return how many seconds an output has been currently on for """
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
                try:
                    import RPi.GPIO as GPIO
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setwarnings(True)
                    GPIO.setup(self.output_pin[output_id], GPIO.OUT)
                    GPIO.output(self.output_pin[output_id],
                                not self.output_on_state[output_id])
                except:
                    self.logger.error(
                        "RPi.GPIO and Raspberry Pi required for this action")
                state = 'LOW' if self.output_on_state[output_id] else 'HIGH'
                self.logger.info(
                    "Output {id} (GPIO) setup on pin {pin} and turned OFF "
                    "(OFF={state})".format(id=output_id.split('-')[0],
                                           pin=self.output_pin[output_id],
                                           state=state))
            except Exception as except_msg:
                self.logger.exception(
                    "Output {id} (GPIO) was unable to be setup on pin {pin} with "
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
                        self.logger.error("Could not connect to pigpiod")
                self.pwm_state[output_id] = None
                self.logger.info("Output {id} (PWM) setup on pin {pin}".format(
                    id=output_id.split('-')[0], pin=self.output_pin[output_id]))
            except Exception as except_msg:
                self.logger.exception(
                    "Output {id} (PWM) was unable to be setup on pin {pin}: "
                    "{err}".format(id=output_id,
                                   pin=self.output_pin[output_id],
                                   err=except_msg))

    def output_state(self, output_id):
        """
        :param output_id: Unique ID for each output
        :type output_id: str

        :return: Whether the output is currently "on", "off", or duty cycle (for PWM outputs)
        :rtype: str
        """
        if output_id in self.output_type:
            if self.is_on(output_id):
                if self.output_type[output_id] in OUTPUTS_PWM:
                    return self.pwm_duty_cycle[output_id]
                else:
                    return 'on'
            else:
                return 'off'

    def set_off_until(self, dt_off_until, output_id):
        """ Save the datetime of when the output is supposed to stay off until """
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
            try:
                import RPi.GPIO as GPIO
                return self.output_on_state[output_id] == GPIO.input(
                    self.output_pin[output_id])
            except:
                self.logger.error(
                    "RPi.GPIO and Raspberry Pi required for this action")
        elif self.output_type[output_id] in ['command',
                                             'python',
                                             'wireless_rpi_rf']:
            if self.output_time_turned_on[output_id] or self.output_on_duration[output_id]:
                return True
        elif self.output_type[output_id] in OUTPUTS_PWM:
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
                        each_dev_meas.channel,
                        measure=each_dev_meas.measurement,)
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
        if (self.output_type[output_id] == 'wired' and
                self.output_pin[output_id]):
            try:
                import RPi.GPIO as GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.output_pin[output_id], GPIO.OUT)
                return True
            except:
                self.logger.error(
                    "RPi.GPIO and Raspberry Pi required for this action")

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
