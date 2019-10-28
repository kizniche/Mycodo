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
#
import calendar
import datetime
import threading
import time
import timeit

import requests

from mycodo.config import OUTPUTS_PWM
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.utils import session_scope
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.method import calculate_method_setpoint
from mycodo.utils.pid_autotune import PIDAutotune
from mycodo.utils.pid_controller import PIDControl
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class PIDController(AbstractController, threading.Thread):
    """
    Class to operate discrete PID controller in Mycodo
    """
    def __init__(self, ready, unique_id):
        threading.Thread.__init__(self)
        super(PIDController, self).__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.sample_rate = None

        self.control = DaemonControl()

        self.device_measurements = None
        self.device_id = None
        self.measurement_id = None
        self.raise_output_type = None
        self.lower_output_type = None
        self.log_level_debug = None
        self.PID_Controller = None
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
        self.setpoint_tracking_type = None
        self.setpoint_tracking_id = None
        self.setpoint_tracking_max_age = None
        self.direction = None
        self.raise_output_id = None
        self.raise_min_duration = None
        self.raise_max_duration = None
        self.raise_min_off_duration = None
        self.lower_output_id = None
        self.lower_min_duration = None
        self.lower_max_duration = None
        self.lower_min_off_duration = None
        self.Kp = 0
        self.Ki = 0
        self.Kd = 0
        self.integrator_min = None
        self.integrator_max = None
        self.period = 0
        self.start_offset = 0
        self.max_measure_age = None
        self.default_setpoint = None
        self.setpoint = 0
        self.store_lower_as_negative = None
        self.first_start = None
        self.timer = None

        # Hysteresis options
        self.band = None
        self.allow_raising = False
        self.allow_lowering = False

        # PID Autotune
        self.autotune = None
        self.autotune_activated = False
        self.autotune_debug = False
        self.autotune_noiseband = 0
        self.autotune_outstep = 0
        self.autotune_timestamp = None

        # Check if a method is set for this PID
        self.method_type = None
        self.method_start_act = None
        self.method_start_time = None
        self.method_end_time = None

    def loop(self):
        if (self.method_start_act == 'Ended' and
                self.method_type == 'Duration'):
            self.stop_controller(
                ended_normally=False, deactivate_pid=True)
            self.logger.warning(
                "Method has ended. "
                "Activate the PID controller to start it again.")
        elif time.time() > self.timer:
            while time.time() > self.timer:
                self.timer = self.timer + self.period
            self.attempt_execute(self.check_pid)

    def run_finally(self):
        # Turn off output used in PID when the controller is deactivated
        if self.raise_output_id and self.direction in ['raise', 'both']:
            self.control.output_off(
                self.raise_output_id,
                trigger_conditionals=True)
        if self.lower_output_id and self.direction in ['lower', 'both']:
            self.control.output_off(
                self.lower_output_id,
                trigger_conditionals=True)

    def initialize_variables(self):
        """Set PID parameters"""
        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_pid

        self.device_measurements = db_retrieve_table_daemon(
            DeviceMeasurements)

        pid = db_retrieve_table_daemon(PID, unique_id=self.unique_id)

        self.device_id = pid.measurement.split(',')[0]
        self.measurement_id = pid.measurement.split(',')[1]

        self.is_activated = pid.is_activated
        self.is_held = pid.is_held
        self.is_paused = pid.is_paused
        self.log_level_debug = pid.log_level_debug
        self.setpoint_tracking_type = pid.setpoint_tracking_type
        self.setpoint_tracking_id = pid.setpoint_tracking_id
        self.setpoint_tracking_max_age = pid.setpoint_tracking_max_age
        self.direction = pid.direction
        self.raise_output_id = pid.raise_output_id
        self.raise_min_duration = pid.raise_min_duration
        self.raise_max_duration = pid.raise_max_duration
        self.raise_min_off_duration = pid.raise_min_off_duration
        self.lower_output_id = pid.lower_output_id
        self.lower_min_duration = pid.lower_min_duration
        self.lower_max_duration = pid.lower_max_duration
        self.lower_min_off_duration = pid.lower_min_off_duration
        self.Kp = pid.p
        self.Ki = pid.i
        self.Kd = pid.d
        self.integrator_min = pid.integrator_min
        self.integrator_max = pid.integrator_max
        self.period = pid.period
        self.start_offset = pid.start_offset
        self.max_measure_age = pid.max_measure_age
        self.default_setpoint = pid.setpoint
        self.setpoint = pid.setpoint
        self.band = pid.band
        self.store_lower_as_negative = pid.store_lower_as_negative
        self.first_start = True
        self.timer = time.time() + self.start_offset

        # Autotune
        self.autotune_activated = pid.autotune_activated
        self.autotune_noiseband = pid.autotune_noiseband
        self.autotune_outstep = pid.autotune_outstep

        self.set_log_level_debug(self.log_level_debug)

        try:
            self.raise_output_type = db_retrieve_table_daemon(
                Output, unique_id=self.raise_output_id).output_type
        except AttributeError:
            self.raise_output_type = None

        try:
            self.lower_output_type = db_retrieve_table_daemon(
                Output, unique_id=self.lower_output_id).output_type
        except AttributeError:
            self.lower_output_type = None

        # Initialize PID Controller
        self.PID_Controller = PIDControl(
            self.period,
            self.Kp, self.Ki, self.Kd,
            integrator_min=self.integrator_min,
            integrator_max=self.integrator_max)

        # If activated, initialize PID Autotune
        if self.autotune_activated:
            self.autotune_timestamp = time.time()
            try:
                self.autotune = PIDAutotune(
                    self.setpoint,
                    out_step=self.autotune_outstep,
                    sampletime=self.period,
                    out_min=0,
                    out_max=self.period,
                    noiseband=self.autotune_noiseband)
            except Exception as msg:
                self.logger.error(msg)
                self.stop_controller(deactivate_pid=True)

        if self.setpoint_tracking_type == 'method' and self.setpoint_tracking_id != '':
            self.setup_method(self.setpoint_tracking_id)

        if self.is_paused:
            self.logger.info("Starting Paused")
        elif self.is_held:
            self.logger.info("Starting Held")

        self.logger.info("PID Settings: {}".format(self.pid_parameters_str()))

        return "success"

    def check_pid(self):
        """ Get measurement and apply to PID controller """
        # If PID is active, retrieve measurement and update
        # the control variable.
        # A PID on hold will sustain the current output and
        # not update the control variable.
        if self.is_activated and (not self.is_paused or not self.is_held):
            self.get_last_measurement()

            if self.last_measurement_success:
                if self.setpoint_tracking_type == 'method' and self.setpoint_tracking_id != '':
                    # Update setpoint using a method
                    this_pid = db_retrieve_table_daemon(
                        PID, unique_id=self.unique_id)
                    setpoint, ended = calculate_method_setpoint(
                        self.setpoint_tracking_id,
                        PID,
                        this_pid,
                        Method,
                        MethodData,
                        self.logger)
                    if ended:
                        self.method_start_act = 'Ended'
                    if setpoint is not None:
                        self.setpoint = setpoint
                    else:
                        self.setpoint = self.default_setpoint

                if self.setpoint_tracking_type == 'input-math' and self.setpoint_tracking_id != '':
                    # Update setpoint using an Input or Math
                    device_id = self.setpoint_tracking_id.split(',')[0]
                    measurement_id = self.setpoint_tracking_id.split(',')[1]

                    measurement = get_measurement(measurement_id)
                    if not measurement:
                        return False, None

                    last_measurement = read_last_influxdb(
                        device_id,
                        measurement.unit,
                        measurement.channel,
                        measure=measurement.measurement,
                        duration_sec=self.setpoint_tracking_max_age)

                    if last_measurement[1] is not None:
                        self.setpoint = last_measurement[1]
                    else:
                        self.logger.debug(
                            "Could not find measurement for Setpoint "
                            "Tracking. Max Age of {} exceeded for measuring "
                            "device ID {} (measurement {})".format(
                                self.setpoint_tracking_max_age,
                                device_id,
                                measurement_id))
                        self.setpoint = None

                # If autotune activated, determine control variable (output) from autotune
                if self.autotune_activated:
                    if not self.autotune.run(self.last_measurement):
                        self.control_variable = self.autotune.output

                        if self.autotune_debug:
                            self.logger.info('')
                            self.logger.info("state: {}".format(self.autotune.state))
                            self.logger.info("output: {}".format(self.autotune.output))
                    else:
                        # Autotune has finished
                        timestamp = time.time() - self.autotune_timestamp
                        self.logger.info('')
                        self.logger.info('time:  {0} min'.format(round(timestamp / 60)))
                        self.logger.info('state: {0}'.format(self.autotune.state))

                        if self.autotune.state == PIDAutotune.STATE_SUCCEEDED:
                            for rule in self.autotune.tuning_rules:
                                params = self.autotune.get_pid_parameters(rule)
                                self.logger.info('')
                                self.logger.info('rule: {0}'.format(rule))
                                self.logger.info('Kp: {0}'.format(params.Kp))
                                self.logger.info('Ki: {0}'.format(params.Ki))
                                self.logger.info('Kd: {0}'.format(params.Kd))

                        self.stop_controller(deactivate_pid=True)
                else:
                    # Calculate new control variable (output) from PID Controller

                    # Original PID method
                    self.control_variable = self.update_pid_output(
                        self.last_measurement)

                    # New PID method (untested)
                    # self.control_variable = self.PID_Controller.calc(
                    #     self.last_measurement, self.setpoint)

                self.write_pid_values()  # Write variables to database

        # Is PID in a state that allows manipulation of outputs
        if (self.is_activated and
                self.setpoint is not None and
                (not self.is_paused or self.is_held)):
            self.manipulate_output()

    def setup_method(self, method_id):
        """ Initialize method variables to start running a method """
        self.setpoint_tracking_id = ''

        method = db_retrieve_table_daemon(Method, unique_id=method_id)
        method_data = db_retrieve_table_daemon(MethodData)
        method_data = method_data.filter(MethodData.method_id == method_id)
        method_data_repeat = method_data.filter(
            MethodData.duration_sec == 0).first()
        pid = db_retrieve_table_daemon(PID, unique_id=self.unique_id)
        self.method_type = method.method_type
        self.method_start_act = pid.method_start_time
        self.method_start_time = None
        self.method_end_time = None

        if self.method_type == 'Duration':
            if self.method_start_act == 'Ended':
                # Method has ended and hasn't been instructed to begin again
                pass
            elif (self.method_start_act == 'Ready' or
                    self.method_start_act is None):
                # Method has been instructed to begin
                now = datetime.datetime.now()
                self.method_start_time = now
                if method_data_repeat and method_data_repeat.duration_end:
                    self.method_end_time = now + datetime.timedelta(
                        seconds=float(method_data_repeat.duration_end))

                with session_scope(MYCODO_DB_PATH) as db_session:
                    mod_pid = db_session.query(PID).filter(
                        PID.unique_id == self.unique_id).first()
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
                                id=method_id,
                                start=self.method_start_time,
                                end=self.method_end_time))
                    else:
                        self.method_start_act = 'Ended'
                else:
                    self.method_start_act = 'Ended'

        self.setpoint_tracking_id = method_id
        self.logger.debug("Method enabled: {id}".format(id=self.setpoint_tracking_id))

    def write_pid_values(self):
        """ Write PID values to the measurement database """
        if self.band:
            setpoint_band_lower = self.setpoint - self.band
            setpoint_band_upper = self.setpoint + self.band
        else:
            setpoint_band_lower = None
            setpoint_band_upper = None

        list_measurements = [
            self.setpoint,
            setpoint_band_lower,
            setpoint_band_upper,
            self.P_value,
            self.I_value,
            self.D_value
        ]

        measurement_dict = {}
        measurements = self.device_measurements.filter(
            DeviceMeasurements.device_id == self.unique_id).all()
        for each_channel, each_measurement in enumerate(measurements):
            if (each_measurement.channel not in measurement_dict and
                    each_measurement.channel < len(list_measurements)):

                # If setpoint, get unit from PID measurement
                if each_measurement.measurement_type == 'setpoint':
                    setpoint_pid = db_retrieve_table_daemon(
                        PID, unique_id=each_measurement.device_id)
                    if setpoint_pid and ',' in setpoint_pid.measurement:
                        pid_measurement = setpoint_pid.measurement.split(',')[1]
                        setpoint_measurement = db_retrieve_table_daemon(
                            DeviceMeasurements, unique_id=pid_measurement)
                        if setpoint_measurement:
                            conversion = db_retrieve_table_daemon(
                                Conversion, unique_id=setpoint_measurement.conversion_id)
                            _, unit, _ = return_measurement_info(
                                setpoint_measurement, conversion)
                            measurement_dict[each_channel] = {
                                'measurement': each_measurement.measurement,
                                'unit': unit,
                                'value': list_measurements[each_channel]
                            }
                else:
                    measurement_dict[each_channel] = {
                        'measurement': each_measurement.measurement,
                        'unit': each_measurement.unit,
                        'value': list_measurements[each_channel]
                    }

        add_measurements_influxdb(self.unique_id, measurement_dict)

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

        self.logger.debug(
            "PID: Input: {inp}, "
            "Output: P: {p}, I: {i}, D: {d}, Out: {o}".format(
            inp=current_value, p=self.P_value, i=self.I_value, d=self.D_value, o=pid_value))

        return pid_value

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
            device_measurement = get_measurement(self.measurement_id)

            if device_measurement:
                conversion = db_retrieve_table_daemon(
                    Conversion, unique_id=device_measurement.conversion_id)
            else:
                conversion = None
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)

            self.last_measurement = read_last_influxdb(
                self.device_id,
                unit,
                channel,
                measure=measurement,
                duration_sec=int(self.max_measure_age))

            if self.last_measurement:
                self.last_time = self.last_measurement[0]
                self.last_measurement = self.last_measurement[1]

                utc_dt = datetime.datetime.strptime(
                    self.last_time.split(".")[0],
                    '%Y-%m-%dT%H:%M:%S')
                utc_timestamp = calendar.timegm(utc_dt.timetuple())
                local_timestamp = str(datetime.datetime.fromtimestamp(utc_timestamp))
                self.logger.debug("Latest (CH{ch}, Unit: {unit}): {last} @ {ts}".format(
                    ch=channel,
                    unit=unit,
                    last=self.last_measurement,
                    ts=local_timestamp))
                if calendar.timegm(time.gmtime()) - utc_timestamp > self.max_measure_age:
                    self.logger.error(
                        "Last measurement was {last_sec} seconds ago, however"
                        " the maximum measurement age is set to {max_sec}"
                        " seconds.".format(
                            last_sec=calendar.timegm(time.gmtime()) - utc_timestamp,
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
                    if self.raise_output_type in OUTPUTS_PWM:
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
                        self.control.output_on(
                            self.raise_output_id,
                            duty_cycle=self.raise_duty_cycle)

                        self.write_pid_output_influxdb(
                            'percent', 'duty_cycle', 7,
                            self.control_var_to_duty_cycle(self.control_variable))

                    elif self.raise_output_type in ['command',
                                                    'python',
                                                    'wired',
                                                    'wireless_rpi_rf']:
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
                            self.control.output_on(
                                self.raise_output_id,
                                amount=self.raise_seconds_on,
                                min_off=self.raise_min_off_duration)

                        self.write_pid_output_influxdb(
                            's', 'duration_time', 6,
                            self.control_variable)

                    elif self.raise_output_type == 'atlas_ezo_pmp':
                        # Activate raise_output for a volume (ml)
                        self.logger.debug(
                            "Setpoint: {sp} Output: {cv} ml to output "
                            "{id}".format(
                                sp=self.setpoint,
                                cv=self.control_variable,
                                id=self.raise_output_id))
                        self.control.output_on(
                            self.raise_output_id,
                            amount=self.control_variable,
                            min_off=self.raise_min_off_duration)

                    self.write_pid_output_influxdb(
                        's', 'duration_time', 6,
                        self.control_variable)

                else:
                    # Turn PWM Off if PWM Output
                    if self.raise_output_type in OUTPUTS_PWM:
                        self.control.output_on(
                            self.raise_output_id,
                            duty_cycle=0)

            #
            # PID control variable is negative, indicating a desire to lower
            # the environmental condition
            #
            if self.direction in ['lower', 'both'] and self.lower_output_id:

                if self.control_variable < 0:
                    # Determine if the output should be PWM or a duration
                    if self.lower_output_type in OUTPUTS_PWM:
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

                        if self.store_lower_as_negative:
                            stored_duty_cycle = -abs(self.lower_duty_cycle)
                            stored_control_variable = -self.control_var_to_duty_cycle(abs(self.control_variable))
                        else:
                            stored_duty_cycle = abs(self.lower_duty_cycle)
                            stored_control_variable = self.control_var_to_duty_cycle(abs(self.control_variable))

                        # Activate pwm with calculated duty cycle
                        self.control.output_on(
                            self.lower_output_id,
                            duty_cycle=stored_duty_cycle)

                        self.write_pid_output_influxdb(
                            'percent', 'duty_cycle', 7,
                            stored_control_variable)

                    elif self.lower_output_type in ['command',
                                                    'python',
                                                    'wired',
                                                    'wireless_rpi_rf']:
                        # Ensure the output on duration doesn't exceed the set maximum
                        if (self.lower_max_duration and
                                abs(self.control_variable) > self.lower_max_duration):
                            self.lower_seconds_on = self.lower_max_duration
                        else:
                            self.lower_seconds_on = float("{0:.2f}".format(
                                abs(self.control_variable)))

                        if self.store_lower_as_negative:
                            stored_amount_on = -abs(self.lower_seconds_on)
                            stored_control_variable = -abs(self.control_variable)
                        else:
                            stored_amount_on = abs(self.lower_seconds_on)
                            stored_control_variable = abs(self.control_variable)

                        if self.lower_seconds_on > self.lower_min_duration:
                            # Activate lower_output for a duration
                            self.logger.debug("Setpoint: {sp} Output: {cv} to "
                                              "output {id}".format(
                                                sp=self.setpoint,
                                                cv=self.control_variable,
                                                id=self.lower_output_id))

                            self.control.output_on(
                                self.lower_output_id,
                                amount=stored_amount_on,
                                min_off=self.lower_min_off_duration)

                        self.write_pid_output_influxdb(
                            's', 'duration_time', 6,
                            stored_control_variable)

                    elif self.lower_output_type == 'atlas_ezo_pmp':
                        if self.store_lower_as_negative:
                            stored_amount_on = -abs(self.lower_seconds_on)
                            stored_control_variable = -abs(self.control_variable)
                        else:
                            stored_amount_on = abs(self.lower_seconds_on)
                            stored_control_variable = abs(self.control_variable)

                        # Activate lower_output for a volume (ml)
                        self.logger.debug("Setpoint: {sp} Output: {cv} to "
                                          "output {id}".format(
                            sp=self.setpoint,
                            cv=self.control_variable,
                            id=self.lower_output_id))

                        self.control.output_on(
                            self.lower_output_id,
                            amount=stored_amount_on,
                            min_off=self.lower_min_off_duration)

                        self.write_pid_output_influxdb(
                            's', 'duration_time', 6,
                            stored_control_variable)

                else:
                    # Turn PWM Off if PWM Output
                    if self.lower_output_type in OUTPUTS_PWM:
                        self.control.output_on(
                            self.lower_output_id,
                            duty_cycle=0)

        else:
            self.logger.debug("Last measurement unsuccessful. Turning outputs off.")
            if self.direction in ['raise', 'both'] and self.raise_output_id:
                self.control.output_off(
                    self.raise_output_id)
            if self.direction in ['lower', 'both'] and self.lower_output_id:
                self.control.output_off(
                    self.lower_output_id)

    def pid_parameters_str(self):
        return "Device ID: {did}, " \
               "Measurement ID: {mid}, " \
               "Direction: {dir}, " \
               "Period: {per}, " \
               "Setpoint: {sp}, " \
               "Band: {band}, " \
               "Kp: {kp}, " \
               "Ki: {ki}, " \
               "Kd: {kd}, " \
               "Integrator Min: {imn}, " \
               "Integrator Max {imx}, " \
               "Output Raise: {opr}, " \
               "Output Raise Min On: {oprmnon}, " \
               "Output Raise Max On: {oprmxon}, " \
               "Output Raise Min Off: {oprmnoff}, " \
               "Output Lower: {opl}, " \
               "Output Lower Min On: {oplmnon}, " \
               "Output Lower Max On: {oplmxon}, " \
               "Output Lower Min Off: {oplmnoff}, " \
               "Setpoint Tracking Type: {sptt}, " \
               "Setpoint Tracking ID: {spt}".format(
            did=self.device_id,
            mid=self.measurement_id,
            dir=self.direction,
            per=self.period,
            sp=self.setpoint,
            band=self.band,
            kp=self.Kp,
            ki=self.Ki,
            kd=self.Kd,
            imn=self.integrator_min,
            imx=self.integrator_max,
            opr=self.raise_output_id,
            oprmnon=self.raise_min_duration,
            oprmxon=self.raise_max_duration,
            oprmnoff=self.raise_min_off_duration,
            opl=self.lower_output_id,
            oplmnon=self.lower_min_duration,
            oplmxon=self.lower_max_duration,
            oplmnoff=self.lower_min_off_duration,
            sptt=self.setpoint_tracking_type,
            spt=self.setpoint_tracking_id)

    def control_var_to_duty_cycle(self, control_variable):
        # Convert control variable to duty cycle
        if control_variable > self.period:
            return 100.0
        else:
            return float((control_variable / self.period) * 100)

    def write_pid_output_influxdb(self, unit, measurement, channel, value):
        write_pid_out_db = threading.Thread(
            target=write_influxdb_value,
            args=(self.unique_id,
                  unit,
                  value,),
            kwargs={'measure': measurement,
                    'channel': channel})
        write_pid_out_db.start()

    def pid_mod(self):
        if self.initialize_variables():
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
        """ Set the setpoint of PID """
        self.setpoint = float(setpoint)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.setpoint = setpoint
            db_session.commit()
        return "Setpoint set to {sp}".format(sp=setpoint)

    def set_method(self, method_id):
        """ Set the method of PID """
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.setpoint_tracking_id = method_id

            if method_id == '':
                self.setpoint_tracking_id = ''
                db_session.commit()
            else:
                mod_pid.method_start_time = 'Ready'
                mod_pid.method_end_time = None
                db_session.commit()
                self.setup_method(method_id)

        return "Method set to {me}".format(me=method_id)

    def set_integrator(self, integrator):
        """ Set the integrator of the controller """
        self.integrator = float(integrator)
        return "Integrator set to {i}".format(i=self.integrator)

    def set_derivator(self, derivator):
        """ Set the derivator of the controller """
        self.derivator = float(derivator)
        return "Derivator set to {d}".format(d=self.derivator)

    def set_kp(self, p):
        """ Set Kp gain of the controller """
        self.Kp = float(p)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.p = p
            db_session.commit()
        return "Kp set to {kp}".format(kp=self.Kp)

    def set_ki(self, i):
        """ Set Ki gain of the controller """
        self.Ki = float(i)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.i = i
            db_session.commit()
        return "Ki set to {ki}".format(ki=self.Ki)

    def set_kd(self, d):
        """ Set Kd gain of the controller """
        self.Kd = float(d)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.d = d
            db_session.commit()
        return "Kd set to {kd}".format(kd=self.Kd)

    def get_setpoint(self):
        return self.setpoint

    def get_error(self):
        return self.error

    def get_integrator(self):
        return self.integrator

    def get_derivator(self):
        return self.derivator

    def get_kp(self):
        return self.Kp

    def get_ki(self):
        return self.Ki

    def get_kd(self):
        return self.Kd

    def stop_controller(self, ended_normally=True, deactivate_pid=False):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False

        # Unset method start time
        if (self.setpoint_tracking_type == 'method' and
                self.setpoint_tracking_id != '' and
                ended_normally):
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_pid = db_session.query(PID).filter(
                    PID.unique_id == self.unique_id).first()
                mod_pid.method_start_time = 'Ended'
                mod_pid.method_end_time = None
                db_session.commit()

        # Deactivate PID and Autotune
        if deactivate_pid:
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_pid = db_session.query(PID).filter(
                    PID.unique_id == self.unique_id).first()
                mod_pid.is_activated = False
                mod_pid.autotune_activated = False
                db_session.commit()
