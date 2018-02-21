# coding=utf-8
#
# controller_pid.py - PID controller that manages discrete control of a
#                     regulation system of inputs, outputs, and devices
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
#
# PID controller code was used from the source below, with modifications.
#
# <http://code.activestate.com/recipes/577231-discrete-pid-controller/>
# Copyright (c) 2010 cnr437@gmail.com
#
# Licensed under the MIT License <http://opensource.org/licenses/MIT>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import calendar
import datetime
import logging
import threading
import time as t
import timeit

import requests

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.utils import session_scope
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.method import calculate_method_setpoint

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class PIDController(threading.Thread):
    """
    Class to operate discrete PID controller

    """
    def __init__(self, ready, pid_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("mycodo.pid_{id}".format(id=pid_id))

        self.running = False
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.pid_id = pid_id
        self.pid_unique_id = db_retrieve_table_daemon(
            PID, device_id=self.pid_id).unique_id
        self.control = DaemonControl()

        self.control_variable = 0.0
        self.derivator = 0.0
        self.integrator = 0.0
        self.error = 0.0
        self.P_value = None
        self.I_value = None
        self.D_value = None
        self.lower_seconds_on = 0.0
        self.raise_seconds_on = 0.0
        self.lower_duty_cycle = 0.0
        self.raise_duty_cycle = 0.0
        self.last_time = None
        self.last_measurement = None
        self.last_measurement_success = False

        self.is_activated = None
        self.is_held = None
        self.is_paused = None
        self.measurement = None
        self.method_id = None
        self.direction = None
        self.raise_output_id = None
        self.raise_min_duration = None
        self.raise_max_duration = None
        self.raise_min_off_duration = None
        self.lower_output_id = None
        self.lower_min_duration = None
        self.lower_max_duration = None
        self.lower_min_off_duration = None
        self.Kp = None
        self.Ki = None
        self.Kd = None
        self.integrator_min = None
        self.integrator_max = None
        self.period = None
        self.max_measure_age = None
        self.default_setpoint = None
        self.setpoint = None

        # Hysteresis options
        self.band = None
        self.allow_raising = False
        self.allow_lowering = False

        self.dev_unique_id = None
        self.input_duration = None

        self.raise_output_type = None
        self.lower_output_type = None

        self.first_start = True

        self.initialize_values()

        self.timer = t.time() + self.period

        # Check if a method is set for this PID
        self.method_start_act = None
        if self.method_id:
            method = db_retrieve_table_daemon(Method, device_id=self.method_id)
            method_data = db_retrieve_table_daemon(MethodData)
            method_data = method_data.filter(MethodData.method_id == self.method_id)
            method_data_repeat = method_data.filter(MethodData.duration_sec == 0).first()
            pid = db_retrieve_table_daemon(PID, device_id=self.pid_id)
            self.method_type = method.method_type
            self.method_start_act = pid.method_start_time
            self.method_start_time = None
            self.method_end_time = None

            if self.method_type == 'Duration':
                if self.method_start_act == 'Ended':
                    # Method has ended and hasn't been instructed to begin again
                    pass
                elif self.method_start_act == 'Ready' or self.method_start_act is None:
                    # Method has been instructed to begin
                    now = datetime.datetime.now()
                    self.method_start_time = now
                    if method_data_repeat and method_data_repeat.duration_end:
                        self.method_end_time = now + datetime.timedelta(
                            seconds=float(method_data_repeat.duration_end))

                    with session_scope(MYCODO_DB_PATH) as db_session:
                        mod_pid = db_session.query(PID)
                        mod_pid = mod_pid.filter(PID.id == self.pid_id).first()
                        mod_pid.method_start_time = self.method_start_time
                        mod_pid.method_end_time = self.method_end_time
                        db_session.commit()
                else:
                    # Method neither instructed to begin or not to
                    # Likely there was a daemon restart ot power failure
                    # Resume method with saved start_time
                    self.method_start_time = datetime.datetime.strptime(
                        str(pid.method_start_time), '%Y-%m-%d %H:%M:%S.%f')
                    if method_data_repeat and method_data_repeat.duration_end:
                        self.method_end_time = datetime.datetime.strptime(
                            str(pid.method_end_time), '%Y-%m-%d %H:%M:%S.%f')
                        if self.method_end_time > datetime.datetime.now():
                            self.logger.warning(
                                "Resuming method {id}: started {start}, "
                                "ends {end}".format(
                                    id=self.method_id,
                                    start=self.method_start_time,
                                    end=self.method_end_time))
                        else:
                            self.method_start_act = 'Ended'
                    else:
                        self.method_start_act = 'Ended'

    def run(self):
        try:
            self.running = True
            startup_str = "Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000)
            if self.is_paused:
                startup_str += ", started Paused"
            elif self.is_held:
                startup_str += ", started Held"
            self.logger.info(startup_str)
            self.ready.set()

            while self.running:

                if (self.method_start_act == 'Ended' and
                        self.method_type == 'Duration'):
                    self.stop_controller(ended_normally=False,
                                         deactivate_pid=True)
                    self.logger.warning(
                        "Method has ended. "
                        "Activate the PID controller to start it again.")

                elif t.time() > self.timer:
                    # Ensure the timer ends in the future
                    while t.time() > self.timer:
                        self.timer = self.timer + self.period

                    # If PID is active, retrieve input measurement and update PID output
                    if self.is_activated and not self.is_paused:
                        self.get_last_measurement()

                        if self.last_measurement_success:
                            # Update setpoint using a method if one is selected
                            if self.method_id:
                                this_controller = db_retrieve_table_daemon(
                                    PID, device_id=self.pid_id)
                                setpoint, ended = calculate_method_setpoint(
                                    self.method_id,
                                    PID,
                                    this_controller,
                                    Method,
                                    MethodData,
                                    self.logger)
                                if ended:
                                    self.method_start_act = 'Ended'
                                if setpoint is not None:
                                    self.setpoint = setpoint
                                else:
                                    self.setpoint = self.default_setpoint

                            write_setpoint_db = threading.Thread(
                                target=write_influxdb_value,
                                args=(self.pid_unique_id,
                                      'setpoint',
                                      self.setpoint,))
                            write_setpoint_db.start()

                            if self.band:
                                band_min = self.setpoint - self.band
                                write_setpoint_db = threading.Thread(
                                    target=write_influxdb_value,
                                    args=(self.pid_unique_id,
                                          'setpoint_band_min',
                                          band_min,))
                                write_setpoint_db.start()

                                band_max = self.setpoint + self.band
                                write_setpoint_db = threading.Thread(
                                    target=write_influxdb_value,
                                    args=(self.pid_unique_id,
                                          'setpoint_band_max',
                                          band_max,))
                                write_setpoint_db.start()

                            # Update PID and get control variable
                            self.control_variable = self.update_pid_output(
                                self.last_measurement)

                            self.write_pid_values()

                    # If PID is active or on hold, activate outputs
                    if ((self.is_activated and not self.is_paused) or
                            (self.is_activated and self.is_held)):
                        self.manipulate_output()
                t.sleep(0.1)

            # Turn off output used in PID when the controller is deactivated
            if self.raise_output_id and self.direction in ['raise', 'both']:
                self.control.relay_off(self.raise_output_id, trigger_conditionals=True)
            if self.lower_output_id and self.direction in ['lower', 'both']:
                self.control.relay_off(self.lower_output_id, trigger_conditionals=True)

            self.running = False
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
                self.logger.exception("Run Error: {err}".format(
                    err=except_msg))

    def initialize_values(self):
        """Set PID parameters"""
        pid = db_retrieve_table_daemon(PID, device_id=self.pid_id)
        self.is_activated = pid.is_activated
        self.is_held = pid.is_held
        self.is_paused = pid.is_paused
        self.method_id = pid.method_id
        self.direction = pid.direction
        self.raise_output_id = pid.raise_relay_id
        self.raise_min_duration = pid.raise_min_duration
        self.raise_max_duration = pid.raise_max_duration
        self.raise_min_off_duration = pid.raise_min_off_duration
        self.lower_output_id = pid.lower_relay_id
        self.lower_min_duration = pid.lower_min_duration
        self.lower_max_duration = pid.lower_max_duration
        self.lower_min_off_duration = pid.lower_min_off_duration
        self.Kp = pid.p
        self.Ki = pid.i
        self.Kd = pid.d
        self.integrator_min = pid.integrator_min
        self.integrator_max = pid.integrator_max
        self.period = pid.period
        self.max_measure_age = pid.max_measure_age
        self.default_setpoint = pid.setpoint
        self.setpoint = pid.setpoint
        self.band = pid.band

        dev_unique_id = pid.measurement.split(',')[0]
        self.measurement = pid.measurement.split(',')[1]

        input_dev = db_retrieve_table_daemon(Input, unique_id=dev_unique_id)
        math = db_retrieve_table_daemon(Math, unique_id=dev_unique_id)
        if input_dev:
            self.dev_unique_id = input_dev.unique_id
            self.input_duration = input_dev.period
        elif math:
            self.dev_unique_id = math.unique_id
            self.input_duration = math.period

        try:
            self.raise_output_type = db_retrieve_table_daemon(
                Output, device_id=self.raise_output_id).relay_type
        except AttributeError:
            self.raise_output_type = None
        try:
            self.lower_output_type = db_retrieve_table_daemon(
                Output, device_id=self.lower_output_id).relay_type
        except AttributeError:
            self.lower_output_type = None

        return "success"

    def update_pid_output(self, current_value):
        """
        Calculate PID output value from reference input and feedback

        :return: Manipulated, or control, variable. This is the PID output.
        :rtype: float

        :param current_value: The input, or process, variable (the actual
            measured condition by the input)
        :type current_value: float
        """
        # Determine if hysteresis is enabled and if the PID should be applied
        setpoint = self.check_hysteresis(current_value)

        if setpoint is None:
            # Prevent PID variables form being manipulated and
            # restrict PID from operating.
            return 0

        self.error = setpoint - current_value

        # Calculate P-value
        self.P_value = self.Kp * self.error

        # Calculate I-value
        self.integrator += self.error

        # First method for managing integrator
        if self.integrator > self.integrator_max:
            self.integrator = self.integrator_max
        elif self.integrator < self.integrator_min:
            self.integrator = self.integrator_min

        # Second method for regulating integrator
        # if self.period is not None:
        #     if self.integrator * self.Ki > self.period:
        #         self.integrator = self.period / self.Ki
        #     elif self.integrator * self.Ki < -self.period:
        #         self.integrator = -self.period / self.Ki

        self.I_value = self.integrator * self.Ki

        # Prevent large initial D-value
        if self.first_start:
            self.derivator = self.error
            self.first_start = False

        # Calculate D-value
        self.D_value = self.Kd * (self.error - self.derivator)
        self.derivator = self.error

        # Produce output form P, I, and D values
        pid_value = self.P_value + self.I_value + self.D_value

        return pid_value

    def write_pid_values(self):
        write_setpoint_db = threading.Thread(
            target=write_influxdb_value,
            args=(self.pid_unique_id,
                  'pid_p_value',
                  self.P_value,))
        write_setpoint_db.start()

        write_setpoint_db = threading.Thread(
            target=write_influxdb_value,
            args=(self.pid_unique_id,
                  'pid_i_value',
                  self.I_value,))
        write_setpoint_db.start()

        write_setpoint_db = threading.Thread(
            target=write_influxdb_value,
            args=(self.pid_unique_id,
                  'pid_d_value',
                  self.D_value,))
        write_setpoint_db.start()

    def check_hysteresis(self, measure):
        """
        Determine if hysteresis is enabled and if the PID should be applied

        :return: float if the setpoint if the PID should be applied, None to
            restrict the PID
        :rtype: float or None

        :param measure: The PID input (or process) variable
        :type measure: float
        """
        if self.band == 0:
            # If band is disabled, return setpoint
            return self.setpoint

        band_min = self.setpoint - self.band
        band_max = self.setpoint + self.band

        if self.direction == 'raise':
            if (measure < band_min or
                    (band_min < measure < band_max and self.allow_raising)):
                self.allow_raising = True
                setpoint = band_max  # New setpoint
                return setpoint  # Apply the PID
            elif measure > band_max:
                self.allow_raising = False
            return None  # Restrict the PID

        elif self.direction == 'lower':
            if (measure > band_max or
                    (band_min < measure < band_max and self.allow_lowering)):
                self.allow_lowering = True
                setpoint = band_min  # New setpoint
                return setpoint  # Apply the PID
            elif measure < band_min:
                self.allow_lowering = False
            return None  # Restrict the PID

        elif self.direction == 'both':
            if measure < band_min:
                setpoint = band_min  # New setpoint
                if not self.allow_raising:
                    # Reset integrator and derivator upon direction switch
                    self.integrator = 0.0
                    self.derivator = 0.0
                    self.allow_raising = True
                    self.allow_lowering = False
            elif measure > band_max:
                setpoint = band_max  # New setpoint
                if not self.allow_lowering:
                    # Reset integrator and derivator upon direction switch
                    self.integrator = 0.0
                    self.derivator = 0.0
                    self.allow_raising = False
                    self.allow_lowering = True
            else:
                return None  # Restrict the PID
            return setpoint  # Apply the PID

    def get_last_measurement(self):
        """
        Retrieve the latest input measurement from InfluxDB

        :rtype: None
        """
        self.last_measurement_success = False
        # Get latest measurement from influxdb
        try:
            self.last_measurement = read_last_influxdb(
                self.dev_unique_id,
                self.measurement,
                int(self.max_measure_age))
            if self.last_measurement:
                self.last_time = self.last_measurement[0]
                self.last_measurement = self.last_measurement[1]

                utc_dt = datetime.datetime.strptime(
                    self.last_time.split(".")[0],
                    '%Y-%m-%dT%H:%M:%S')
                utc_timestamp = calendar.timegm(utc_dt.timetuple())
                local_timestamp = str(datetime.datetime.fromtimestamp(utc_timestamp))
                self.logger.debug("Latest {meas}: {last} @ {ts}".format(
                    meas=self.measurement,
                    last=self.last_measurement,
                    ts=local_timestamp))
                if calendar.timegm(t.gmtime()) - utc_timestamp > self.max_measure_age:
                    self.logger.error(
                        "Last measurement was {last_sec} seconds ago, however"
                        " the maximum measurement age is set to {max_sec}"
                        " seconds.".format(
                            last_sec=calendar.timegm(t.gmtime())-utc_timestamp,
                            max_sec=self.max_measure_age
                        ))
                self.last_measurement_success = True
            else:
                self.logger.warning("No data returned from influxdb")
        except requests.ConnectionError:
            self.logger.error("Failed to read measurement from the "
                              "influxdb database: Could not connect.")
        except Exception as except_msg:
            self.logger.exception(
                "Exception while reading measurement from the influxdb "
                "database: {err}".format(err=except_msg))

    def manipulate_output(self):
        """
        Activate output based on PID control variable and whether
        the manipulation directive is to raise, lower, or both.

        :rtype: None
        """
        # If the last measurement was able to be retrieved and was entered within the past minute
        if self.last_measurement_success:
            #
            # PID control variable is positive, indicating a desire to raise
            # the environmental condition
            #
            if self.direction in ['raise', 'both'] and self.raise_output_id:

                if self.control_variable > 0:
                    # Determine if the output should be PWM or a duration
                    if self.raise_output_type == 'pwm':
                        self.raise_duty_cycle = float("{0:.1f}".format(
                            self.control_var_to_duty_cycle(self.control_variable)))

                        # Ensure the duty cycle doesn't exceed the min/max
                        if (self.raise_max_duration and
                                self.raise_duty_cycle > self.raise_max_duration):
                            self.raise_duty_cycle = self.raise_max_duration
                        elif (self.raise_min_duration and
                                self.raise_duty_cycle < self.raise_min_duration):
                            self.raise_duty_cycle = self.raise_min_duration

                        self.logger.debug(
                            "Setpoint: {sp}, Control Variable: {cv}, Output: PWM output "
                            "{id} to {dc:.1f}%".format(
                                sp=self.setpoint,
                                cv=self.control_variable,
                                id=self.raise_output_id,
                                dc=self.raise_duty_cycle))

                        # Activate pwm with calculated duty cycle
                        self.control.relay_on(self.raise_output_id,
                                              duty_cycle=self.raise_duty_cycle)

                        pid_entry_value = self.control_var_to_duty_cycle(
                            abs(self.control_variable))
                        if self.control_variable < 0:
                            pid_entry_value = -pid_entry_value
                        self.write_pid_output_influxdb(
                            'duty_cycle', pid_entry_value)

                    elif self.raise_output_type in ['command',
                                                    'wired',
                                                    'wireless_433MHz_pi_switch']:
                        # Ensure the output on duration doesn't exceed the set maximum
                        if (self.raise_max_duration and
                                self.control_variable > self.raise_max_duration):
                            self.raise_seconds_on = self.raise_max_duration
                        else:
                            self.raise_seconds_on = float("{0:.2f}".format(
                                self.control_variable))

                        if self.raise_seconds_on > self.raise_min_duration:
                            # Activate raise_output for a duration
                            self.logger.debug(
                                "Setpoint: {sp} Output: {cv} to output "
                                "{id}".format(
                                    sp=self.setpoint,
                                    cv=self.control_variable,
                                    id=self.raise_output_id))
                            self.control.relay_on(
                                self.raise_output_id,
                                duration=self.raise_seconds_on,
                                min_off=self.raise_min_off_duration)

                        self.write_pid_output_influxdb(
                            'pid_output', self.control_variable)

                else:
                    if self.raise_output_type == 'pwm':
                        self.control.relay_on(self.raise_output_id,
                                              duty_cycle=0)

            #
            # PID control variable is negative, indicating a desire to lower
            # the environmental condition
            #
            if self.direction in ['lower', 'both'] and self.lower_output_id:

                if self.control_variable < 0:
                    # Determine if the output should be PWM or a duration
                    if self.lower_output_type == 'pwm':
                        self.lower_duty_cycle = float("{0:.1f}".format(
                            self.control_var_to_duty_cycle(abs(self.control_variable))))

                        # Ensure the duty cycle doesn't exceed the min/max
                        if (self.lower_max_duration and
                                self.lower_duty_cycle > self.lower_max_duration):
                            self.lower_duty_cycle = self.lower_max_duration
                        elif (self.lower_min_duration and
                                self.lower_duty_cycle < self.lower_min_duration):
                            self.lower_duty_cycle = self.lower_min_duration

                        self.logger.debug(
                            "Setpoint: {sp}, Control Variable: {cv}, "
                            "Output: PWM output {id} to {dc:.1f}%".format(
                                sp=self.setpoint,
                                cv=self.control_variable,
                                id=self.lower_output_id,
                                dc=self.lower_duty_cycle))

                        # Turn back negative for proper logging
                        self.lower_duty_cycle = -self.lower_duty_cycle

                        # Activate pwm with calculated duty cycle
                        self.control.relay_on(
                            self.lower_output_id,
                            duty_cycle=self.lower_duty_cycle)

                        pid_entry_value = self.control_var_to_duty_cycle(
                            abs(self.control_variable))
                        pid_entry_value = -pid_entry_value
                        self.write_pid_output_influxdb('duty_cycle', pid_entry_value)

                    elif self.lower_output_type in ['command',
                                                    'wired',
                                                    'wireless_433MHz_pi_switch']:
                        # Ensure the output on duration doesn't exceed the set maximum
                        if (self.lower_max_duration and
                                abs(self.control_variable) > self.lower_max_duration):
                            self.lower_seconds_on = self.lower_max_duration
                        else:
                            self.lower_seconds_on = float("{0:.2f}".format(
                                self.control_variable))

                        if abs(self.lower_seconds_on) > self.lower_min_duration:
                            # Activate lower_output for a duration
                            self.logger.debug("Setpoint: {sp} Output: {cv} to "
                                              "output {id}".format(
                                                sp=self.setpoint,
                                                cv=self.control_variable,
                                                id=self.lower_output_id))
                            self.control.relay_on(
                                self.lower_output_id,
                                duration=self.lower_seconds_on,
                                min_off=self.lower_min_off_duration)

                        self.write_pid_output_influxdb(
                            'pid_output', self.control_variable)

                else:
                    if self.lower_output_type == 'pwm':
                        self.control.relay_on(self.lower_output_id,
                                              duty_cycle=0)

        else:
            if self.direction in ['raise', 'both'] and self.raise_output_id:
                self.control.relay_off(self.raise_output_id)
            if self.direction in ['lower', 'both'] and self.lower_output_id:
                self.control.relay_off(self.lower_output_id)

    def control_var_to_duty_cycle(self, control_variable):
        # Convert control variable to duty cycle
        if control_variable > self.period:
            return 100.0
        else:
            return float((control_variable / self.period) * 100)

    def write_pid_output_influxdb(self, pid_entry_type, pid_entry_value):
        write_pid_out_db = threading.Thread(
            target=write_influxdb_value,
            args=(self.pid_unique_id,
                  pid_entry_type,
                  pid_entry_value,))
        write_pid_out_db.start()

    def pid_mod(self):
        if self.initialize_values():
            return "success"
        else:
            return "error"

    def pid_hold(self):
        self.is_held = True
        self.logger.info("Hold")
        return "success"

    def pid_pause(self):
        self.is_paused = True
        self.logger.info("Pause")
        return "success"

    def pid_resume(self):
        self.is_activated = True
        self.is_held = False
        self.is_paused = False
        self.logger.info("Resume")
        return "success"

    def set_setpoint(self, setpoint):
        """ Initilize the setpoint of PID """
        self.setpoint = setpoint
        self.integrator = 0
        self.derivator = 0

    def set_integrator(self, integrator):
        """ Set the integrator of the controller """
        self.integrator = integrator

    def set_derivator(self, derivator):
        """ Set the derivator of the controller """
        self.derivator = derivator

    def set_kp(self, p):
        """ Set Kp gain of the controller """
        self.Kp = p

    def set_ki(self, i):
        """ Set Ki gain of the controller """
        self.Ki = i

    def set_kd(self, d):
        """ Set Kd gain of the controller """
        self.Kd = d

    def get_setpoint(self):
        return self.setpoint

    def get_error(self):
        return self.error

    def get_integrator(self):
        return self.integrator

    def get_derivator(self):
        return self.derivator

    def is_running(self):
        return self.running

    def stop_controller(self, ended_normally=True, deactivate_pid=False):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
        # Unset method start time
        if self.method_id and ended_normally:
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_pid = db_session.query(PID).filter(
                    PID.id == self.pid_id).first()
                mod_pid.method_start_time = 'Ended'
                mod_pid.method_end_time = None
                db_session.commit()

        if deactivate_pid:
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_pid = db_session.query(PID).filter(
                    PID.id == self.pid_id).first()
                mod_pid.is_activated = False
                db_session.commit()
