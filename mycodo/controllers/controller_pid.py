# coding=utf-8
#
# controller_pid.py - PID controller that manages discrete control of a
#                     regulation system of inputs, outputs, and devices
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

from mycodo.config import MYCODO_DB_PATH
from mycodo.controllers.base_controller import AbstractController
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Misc
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.databases.utils import session_scope
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_influxdb_single
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.method import load_method_handler, parse_db_time
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.pid_controller_default import PIDControl
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info


class PIDController(AbstractController, threading.Thread):
    """
    Class to operate discrete PID controller in Mycodo
    """
    def __init__(self, ready, unique_id):
        threading.Thread.__init__(self)
        super().__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.sample_rate = None
        self.dict_outputs = None

        self.control = DaemonControl()

        self.PID_Controller = None
        self.setpoint = None

        self.device_measurements = None
        self.device_id = None
        self.measurement_id = None
        self.log_level_debug = None
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
        self.raise_output_id = None
        self.raise_output_channel_id = None
        self.raise_output_channel = None
        self.raise_output_type = None
        self.raise_min_duration = None
        self.raise_max_duration = None
        self.raise_min_off_duration = None
        self.raise_always_min_pwm = None
        self.lower_output_id = None
        self.lower_output_channel_id = None
        self.lower_output_channel = None
        self.lower_output_type = None
        self.lower_min_duration = None
        self.lower_max_duration = None
        self.lower_min_off_duration = None
        self.lower_always_min_pwm = None
        self.period = 0
        self.start_offset = 0
        self.max_measure_age = None
        self.send_lower_as_negative = None
        self.store_lower_as_negative = None
        self.timer = 0

        # Check if a method is set for this PID
        self.method_type = None
        self.method_start_time = None
        self.method_end_time = None

    def loop(self):
        if time.time() > self.timer:
            while time.time() > self.timer:
                self.timer = self.timer + self.period
            self.attempt_execute(self.check_pid)

    def run_finally(self):
        # Turn off output used in PID when the controller is deactivated
        if self.raise_output_id and self.PID_Controller.direction in ['raise', 'both']:
            self.control.output_off(
                self.raise_output_id, output_channel=self.raise_output_channel, trigger_conditionals=True)
        if self.lower_output_id and self.PID_Controller.direction in ['lower', 'both']:
            self.control.output_off(
                self.lower_output_id, output_channel=self.lower_output_channel, trigger_conditionals=True)

    def initialize_variables(self):
        """Set PID parameters."""
        self.dict_outputs = parse_output_information()

        self.sample_rate = db_retrieve_table_daemon(Misc, entry='first').sample_rate_controller_pid

        self.device_measurements = db_retrieve_table_daemon(DeviceMeasurements)

        pid = db_retrieve_table_daemon(PID, unique_id=self.unique_id)

        self.log_level_debug = pid.log_level_debug
        self.set_log_level_debug(self.log_level_debug)

        self.device_id = pid.measurement.split(',')[0]
        self.measurement_id = pid.measurement.split(',')[1]
        self.is_activated = pid.is_activated
        self.is_held = pid.is_held
        self.is_paused = pid.is_paused
        self.setpoint_tracking_type = pid.setpoint_tracking_type
        self.setpoint_tracking_id = pid.setpoint_tracking_id
        self.setpoint_tracking_max_age = pid.setpoint_tracking_max_age
        if pid.raise_output_id and "," in pid.raise_output_id:
            self.raise_output_id = pid.raise_output_id.split(",")[0]
            self.raise_output_channel_id = pid.raise_output_id.split(",")[1]
            output_channel = db_retrieve_table_daemon(
                OutputChannel, unique_id=self.raise_output_channel_id)
            self.raise_output_channel = output_channel.channel
        self.raise_output_type = pid.raise_output_type
        self.raise_min_duration = pid.raise_min_duration
        self.raise_max_duration = pid.raise_max_duration
        self.raise_min_off_duration = pid.raise_min_off_duration
        self.raise_always_min_pwm = pid.raise_always_min_pwm
        if pid.lower_output_id and "," in pid.lower_output_id:
            self.lower_output_id = pid.lower_output_id.split(",")[0]
            self.lower_output_channel_id = pid.lower_output_id.split(",")[1]
            output_channel = db_retrieve_table_daemon(
                OutputChannel, unique_id=self.lower_output_channel_id)
            self.lower_output_channel = output_channel.channel
        self.lower_output_type = pid.lower_output_type
        self.lower_min_duration = pid.lower_min_duration
        self.lower_max_duration = pid.lower_max_duration
        self.lower_min_off_duration = pid.lower_min_off_duration
        self.lower_always_min_pwm = pid.lower_always_min_pwm
        self.period = pid.period
        self.start_offset = pid.start_offset
        self.max_measure_age = pid.max_measure_age
        self.send_lower_as_negative = pid.send_lower_as_negative
        self.store_lower_as_negative = pid.store_lower_as_negative
        self.timer = time.time() + self.start_offset
        self.setpoint = pid.setpoint

        # Initialize PID Controller
        if self.PID_Controller is None:
            self.PID_Controller = PIDControl(
                self.logger, pid.setpoint, pid.p, pid.i, pid.d, pid.direction,
                pid.band, pid.integrator_min, pid.integrator_max)
        else:
            # Set PID options
            self.PID_Controller.setpoint = pid.setpoint
            self.PID_Controller.Kp = pid.p
            self.PID_Controller.Ki = pid.i
            self.PID_Controller.Kd = pid.d
            self.PID_Controller.direction = pid.direction
            self.PID_Controller.band = pid.band
            self.PID_Controller.integrator_min = pid.integrator_min
            self.PID_Controller.integrator_max = pid.integrator_max
            self.PID_Controller.first_start = True

        if self.setpoint_tracking_type == 'method' and self.setpoint_tracking_id != '':
            self.setup_method(self.setpoint_tracking_id)

        if self.is_paused:
            self.logger.info("Starting Paused")
        elif self.is_held:
            self.logger.info("Starting Held")

        self.logger.info(f"PID Settings: {self.pid_parameters_str()}")

        self.ready.set()
        self.running = True

        return "success"

    def check_pid(self):
        """Get measurement and apply to PID controller."""
        # If PID is active, retrieve measurement and update
        # the control variable.
        # A PID on hold will sustain the current output and
        # not update the control variable.
        if self.is_activated and (not self.is_paused or not self.is_held):
            self.get_last_measurement_pid()

            if self.last_measurement_success:
                if self.setpoint_tracking_type == 'method' and self.setpoint_tracking_id != '':
                    # Update setpoint using a method
                    this_pid = db_retrieve_table_daemon(PID, unique_id=self.unique_id)

                    now = datetime.datetime.now()

                    method = load_method_handler(self.setpoint_tracking_id, self.logger)
                    new_setpoint, ended = method.calculate_setpoint(now, this_pid.method_start_time)
                    self.logger.debug(f"Method {self.setpoint_tracking_id} {method} {now} {this_pid.method_start_time}")

                    if ended:
                        # point in time is out of method range
                        with session_scope(MYCODO_DB_PATH) as db_session:
                            # Overwrite this_controller with committable connection
                            this_pid = db_session.query(PID).filter(
                                PID.unique_id == self.unique_id).first()

                            self.logger.debug("Ended")
                            # Duration method has ended, reset method_start_time locally and in DB
                            this_pid.method_start_time = None
                            this_pid.method_end_time = None
                            this_pid.is_activated = False
                            db_session.commit()

                            self.is_activated = False
                            self.stop_controller()

                            db_session.commit()

                    if new_setpoint is not None:
                        self.logger.debug(f"New setpoint = {new_setpoint} {ended}")
                        self.PID_Controller.setpoint = new_setpoint
                    else:
                        self.logger.debug(f"New setpoint = default {self.setpoint} {ended}")
                        self.PID_Controller.setpoint = self.setpoint

                if self.setpoint_tracking_type == 'input-math' and self.setpoint_tracking_id != '':
                    # Update setpoint using an Input
                    device_id = self.setpoint_tracking_id.split(',')[0]
                    measurement_id = self.setpoint_tracking_id.split(',')[1]

                    measurement = get_measurement(measurement_id)
                    if not measurement:
                        return False, None

                    conversion = db_retrieve_table_daemon(
                        Conversion, unique_id=measurement.conversion_id)
                    channel, unit, measurement = return_measurement_info(
                        measurement, conversion)

                    last_measurement = read_influxdb_single(
                        device_id,
                        unit,
                        channel,
                        measure=measurement,
                        duration_sec=self.setpoint_tracking_max_age,
                        value='LAST')

                    if last_measurement[1] is not None:
                        self.PID_Controller.setpoint = last_measurement[1]
                    else:
                        self.logger.debug(
                            "Could not find measurement for Setpoint "
                            f"Tracking. Max Age of {self.setpoint_tracking_max_age} exceeded for measuring "
                            f"device ID {device_id} (measurement {measurement_id})")
                        self.PID_Controller.setpoint = None

                # Calculate new control variable (output) from PID Controller
                self.PID_Controller.update_pid_output(self.last_measurement)

                self.write_pid_values()  # Write variables to database

        # Is PID in a state that allows manipulation of outputs
        if (self.is_activated and
                self.PID_Controller.setpoint is not None and
                (not self.is_paused or self.is_held)):
            self.manipulate_output()

    def setup_method(self, method_id):
        """Initialize method variables to start running a method."""
        self.setpoint_tracking_id = ''

        method = load_method_handler(method_id, self.logger)

        this_controller = db_retrieve_table_daemon(PID, unique_id=self.unique_id)
        self.method_type = method.method_type

        if parse_db_time(this_controller.method_start_time) is None:
            self.method_start_time = datetime.datetime.now()
            self.method_end_time = method.determine_end_time(self.method_start_time)

            self.logger.info(f"Starting method {self.method_start_time} {self.method_end_time}")

            with session_scope(MYCODO_DB_PATH) as db_session:
                this_controller = db_session.query(PID)
                this_controller = this_controller.filter(PID.unique_id == self.unique_id).first()
                this_controller.method_start_time = self.method_start_time
                this_controller.method_end_time = self.method_end_time
                db_session.commit()
        else:
            # already running, potentially the daemon has been restarted
            self.method_start_time = this_controller.method_start_time
            self.method_end_time = this_controller.method_end_time

        self.setpoint_tracking_id = method_id
        self.logger.debug(f"Method enabled: {self.setpoint_tracking_id}")

    def stop_method(self):
        self.method_start_time = None
        self.method_end_time = None
        with session_scope(MYCODO_DB_PATH) as db_session:
            this_controller = db_session.query(PID)
            this_controller = this_controller.filter(PID.unique_id == self.unique_id).first()
            this_controller.is_activated = False
            this_controller.method_start_time = None
            this_controller.method_end_time = None
            db_session.commit()
        self.stop_controller()
        self.is_activated = False
        self.logger.warning(
            "Method has ended. "
            "Activate the Trigger controller to start it again.")

    def write_pid_values(self):
        """Write PID values to the measurement database"""
        if self.PID_Controller.band:
            setpoint_band_lower = self.PID_Controller.setpoint - self.PID_Controller.band
            setpoint_band_upper = self.PID_Controller.setpoint + self.PID_Controller.band
        else:
            setpoint_band_lower = None
            setpoint_band_upper = None

        list_measurements = [
            self.PID_Controller.setpoint,
            setpoint_band_lower,
            setpoint_band_upper,
            self.PID_Controller.P_value,
            self.PID_Controller.I_value,
            self.PID_Controller.D_value
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
                        setpoint_measurement = db_retrieve_table_daemon(DeviceMeasurements, unique_id=pid_measurement)
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

    def get_last_measurement_pid(self):
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

            last_measurement = read_influxdb_single(
                self.device_id,
                unit,
                channel,
                measure=measurement,
                duration_sec=int(self.max_measure_age),
                value='LAST')

            if last_measurement:
                self.last_time = last_measurement[0] / 1000
                self.last_measurement = last_measurement[1]

                local_timestamp = str(datetime.datetime.fromtimestamp(self.last_time))
                self.logger.debug(f"Latest (CH{channel}, Unit: {unit}): {self.last_measurement} @ {local_timestamp}")
                self.last_measurement_success = True
            else:
                self.logger.warning("No data from the specified time period returned from influxdb")
        except requests.ConnectionError:
            self.logger.error("Failed to read measurement from the influxdb database: Could not connect.")
        except Exception:
            self.logger.exception(
                "Exception while reading measurement from the influxdb database")

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
            if self.PID_Controller.direction in ['raise', 'both'] and self.raise_output_id:

                if self.PID_Controller.control_variable > 0:

                    if self.raise_output_type == 'pwm':
                        raise_duty_cycle = self.control_var_to_duty_cycle(
                            self.PID_Controller.control_variable)

                        # Ensure the duty cycle doesn't exceed the min/max
                        if (self.raise_max_duration and
                                raise_duty_cycle > self.raise_max_duration):
                            raise_duty_cycle = self.raise_max_duration
                        elif (self.raise_min_duration and
                                raise_duty_cycle < self.raise_min_duration):
                            raise_duty_cycle = self.raise_min_duration

                        self.logger.debug(
                            f"Setpoint: {self.PID_Controller.setpoint}, "
                            f"Control Variable: {self.PID_Controller.control_variable}, "
                            f"Output: PWM output {self.raise_output_id} "
                            f"CH{self.raise_output_channel} to {raise_duty_cycle:.1f}%")

                        # Activate pwm with calculated duty cycle
                        self.control.output_on(
                            self.raise_output_id,
                            output_type='pwm',
                            amount=raise_duty_cycle,
                            output_channel=self.raise_output_channel)

                        self.write_pid_output_influxdb(
                            'percent', 'duty_cycle', 7,
                            self.control_var_to_duty_cycle(self.PID_Controller.control_variable))

                    elif self.raise_output_type == 'on_off':
                        raise_seconds_on = self.PID_Controller.control_variable

                        # Ensure the output on duration doesn't exceed the set maximum
                        if (self.raise_max_duration and
                                raise_seconds_on > self.raise_max_duration):
                            raise_seconds_on = self.raise_max_duration

                        if raise_seconds_on >= self.raise_min_duration:
                            # Activate raise_output for a duration
                            self.logger.debug(
                                f"Setpoint: {self.PID_Controller.setpoint} "
                                f"Output: {self.PID_Controller.control_variable} sec to "
                                f"output {self.raise_output_id} CH{self.raise_output_channel}")

                            self.control.output_on(
                                self.raise_output_id,
                                output_type='sec',
                                amount=raise_seconds_on,
                                min_off=self.raise_min_off_duration,
                                output_channel=self.raise_output_channel)

                        self.write_pid_output_influxdb(
                            's', 'duration_time', 6, self.PID_Controller.control_variable)

                    elif self.raise_output_type == 'value':
                        raise_value = self.PID_Controller.control_variable

                        # Ensure the duty cycle doesn't exceed the min/max
                        if (self.raise_max_duration and
                                raise_value > self.raise_max_duration):
                            raise_value = self.raise_max_duration

                        if raise_value >= self.raise_min_duration:
                            # Activate raise_output for a value
                            self.logger.debug(
                                f"Setpoint: {self.PID_Controller.setpoint} "
                                f"Output: {self.PID_Controller.control_variable} to "
                                f"output {self.raise_output_id} CH{self.raise_output_channel}")

                            self.control.output_on(
                                self.raise_output_id,
                                output_type='value',
                                amount=raise_value,
                                min_off=self.raise_min_off_duration,
                                output_channel=self.raise_output_channel)

                        self.write_pid_output_influxdb(
                            'none', 'unitless', 9, raise_value)

                    elif self.raise_output_type == 'volume':
                        raise_volume = self.PID_Controller.control_variable

                        # Ensure the duty cycle doesn't exceed the min/max
                        if (self.raise_max_duration and
                                raise_volume > self.raise_max_duration):
                            raise_volume = self.raise_max_duration

                        if raise_volume >= self.raise_min_duration:
                            # Activate raise_output for a volume (ml)
                            self.logger.debug(
                                f"Setpoint: {self.PID_Controller.setpoint} "
                                f"Output: {self.PID_Controller.control_variable} ml to "
                                f"output {self.raise_output_id} CH{self.raise_output_channel}")

                            self.control.output_on(
                                self.raise_output_id,
                                output_type='vol',
                                amount=raise_volume,
                                min_off=self.raise_min_off_duration,
                                output_channel=self.raise_output_channel)

                        self.write_pid_output_influxdb(
                            'ml', 'volume', 8, self.PID_Controller.control_variable)

                elif self.raise_output_type == 'pwm' and not self.raise_always_min_pwm:
                    # Turn PWM Off if PWM Output and not instructed to always be at least min
                    self.control.output_on(
                        self.raise_output_id,
                        output_type='pwm',
                        amount=0,
                        output_channel=self.raise_output_channel)

            #
            # PID control variable is negative, indicating a desire to lower
            # the environmental condition
            #
            if self.PID_Controller.direction in ['lower', 'both'] and self.lower_output_id:

                if self.PID_Controller.control_variable < 0:

                    if self.lower_output_type == 'pwm':
                        lower_duty_cycle = self.control_var_to_duty_cycle(
                            abs(self.PID_Controller.control_variable))

                        # Ensure the duty cycle doesn't exceed the min/max
                        if (self.lower_max_duration and
                                lower_duty_cycle > self.lower_max_duration):
                            lower_duty_cycle = self.lower_max_duration
                        elif (self.lower_min_duration and
                                lower_duty_cycle < self.lower_min_duration):
                            lower_duty_cycle = self.lower_min_duration

                        self.logger.debug(
                            f"Setpoint: {self.PID_Controller.setpoint}, "
                            f"Control Variable: {self.PID_Controller.control_variable}, "
                            f"Output: PWM output {self.lower_output_id} "
                            f"CH{self.lower_output_channel} to {lower_duty_cycle:.1f}%")

                        if self.store_lower_as_negative:
                            store_duty_cycle = -self.control_var_to_duty_cycle(
                                abs(self.PID_Controller.control_variable))
                        else:
                            store_duty_cycle = self.control_var_to_duty_cycle(
                                abs(self.PID_Controller.control_variable))

                        if self.send_lower_as_negative:
                            send_duty_cycle = -abs(lower_duty_cycle)
                        else:
                            send_duty_cycle = abs(lower_duty_cycle)

                        # Activate pwm with calculated duty cycle
                        self.control.output_on(
                            self.lower_output_id,
                            output_type='pwm',
                            amount=send_duty_cycle,
                            output_channel=self.lower_output_channel)

                        self.write_pid_output_influxdb(
                            'percent', 'duty_cycle', 7, store_duty_cycle)

                    elif self.lower_output_type == 'on_off':
                        lower_seconds_on = abs(self.PID_Controller.control_variable)

                        # Ensure the output on duration doesn't exceed the set maximum
                        if (self.lower_max_duration and
                                lower_seconds_on > self.lower_max_duration):
                            lower_seconds_on = self.lower_max_duration

                        if self.store_lower_as_negative:
                            store_amount_on = -abs(self.PID_Controller.control_variable)
                        else:
                            store_amount_on = abs(self.PID_Controller.control_variable)

                        if self.send_lower_as_negative:
                            send_amount_on = -lower_seconds_on
                        else:
                            send_amount_on = lower_seconds_on

                        if lower_seconds_on >= self.lower_min_duration:
                            # Activate lower_output for a duration
                            self.logger.debug(
                                f"Setpoint: {self.PID_Controller.setpoint} "
                                f"Output: {self.PID_Controller.control_variable} sec to "
                                f"output {self.lower_output_id} CH{self.lower_output_channel}")

                            self.control.output_on(
                                self.lower_output_id,
                                output_type='sec',
                                amount=send_amount_on,
                                min_off=self.lower_min_off_duration,
                                output_channel=self.lower_output_channel)

                        self.write_pid_output_influxdb(
                            's', 'duration_time', 6, store_amount_on)

                    elif self.lower_output_type == 'value':
                        lower_value = abs(self.PID_Controller.control_variable)

                        # Ensure the output value doesn't exceed the set maximum
                        if (self.lower_max_duration and
                                lower_value > self.lower_max_duration):
                            lower_value = self.lower_max_duration

                        if self.store_lower_as_negative:
                            store_value = -abs(self.PID_Controller.control_variable)
                        else:
                            store_value = abs(self.PID_Controller.control_variable)

                        if self.send_lower_as_negative:
                            send_value = -lower_value
                        else:
                            send_value = lower_value

                        if lower_value >= self.lower_min_duration:
                            # Activate lower_output for a value
                            self.logger.debug(
                                f"Setpoint: {self.PID_Controller.setpoint} "
                                f"Output: {self.PID_Controller.control_variable} to "
                                f"output {self.lower_output_id} CH{self.lower_output_channel}")

                            self.control.output_on(
                                self.lower_output_id,
                                output_type='value',
                                amount=send_value,
                                min_off=self.lower_min_off_duration,
                                output_channel=self.lower_output_channel)

                        self.write_pid_output_influxdb(
                            'none', 'unitless', 9, store_value)

                    elif self.lower_output_type == 'volume':
                        lower_volume = abs(self.PID_Controller.control_variable)

                        # Ensure the output volume doesn't exceed the set maximum
                        if (self.lower_max_duration and
                                lower_volume > self.lower_max_duration):
                            lower_volume = self.lower_max_duration

                        if self.store_lower_as_negative:
                            store_volume = -abs(self.PID_Controller.control_variable)
                        else:
                            store_volume = abs(self.PID_Controller.control_variable)

                        if self.send_lower_as_negative:
                            send_volume = -lower_volume
                        else:
                            send_volume = lower_volume

                        if lower_volume >= self.lower_min_duration:
                            # Activate lower_output for a volume (ml)
                            self.logger.debug(
                                f"Setpoint: {self.PID_Controller.setpoint} "
                                f"Output: {self.PID_Controller.control_variable} ml to "
                                f"output {self.lower_output_id} CH{self.lower_output_channel}")

                            self.control.output_on(
                                self.lower_output_id,
                                output_type='vol',
                                amount=send_volume,
                                min_off=self.lower_min_off_duration,
                                output_channel=self.lower_output_channel)

                        self.write_pid_output_influxdb(
                            'ml', 'volume', 8, store_volume)

                elif self.lower_output_type == 'pwm' and not self.lower_always_min_pwm:
                    # Turn PWM Off if PWM Output and not instructed to always be at least min
                    self.control.output_on(
                        self.lower_output_id,
                        output_type='pwm',
                        amount=0,
                        output_channel=self.lower_output_channel)

        else:
            self.logger.debug("Last measurement unsuccessful. Turning outputs off.")
            if self.PID_Controller.direction in ['raise', 'both'] and self.raise_output_id:
                self.control.output_off(
                    self.raise_output_id, output_channel=self.raise_output_channel)
            if self.PID_Controller.direction in ['lower', 'both'] and self.lower_output_id:
                self.control.output_off(
                    self.lower_output_id, output_channel=self.lower_output_channel)

    def pid_parameters_str(self):
        return f"Device ID: {self.device_id}, " \
               f"Measurement ID: {self.measurement_id}, " \
               f"Direction: {self.PID_Controller.direction}, " \
               f"Period: {self.period}, " \
               f"Setpoint: {self.PID_Controller.setpoint}, " \
               f"Band: {self.PID_Controller.band}, " \
               f"Kp: {self.PID_Controller.Kp}, " \
               f"Ki: {self.PID_Controller.Ki}, " \
               f"Kd: {self.PID_Controller.Kd}, " \
               f"Integrator Min: {self.PID_Controller.integrator_min}, " \
               f"Integrator Max {self.PID_Controller.integrator_max}, " \
               f"Output Raise: {self.raise_output_id}, " \
               f"Output Raise Channel: {self.raise_output_channel}, " \
               f"Output Raise Type: {self.raise_output_type}, " \
               f"Output Raise Min On: {self.raise_min_duration}, " \
               f"Output Raise Max On: {self.raise_max_duration}, " \
               f"Output Raise Min Off: {self.raise_min_off_duration}, " \
               f"Output Raise Always Min: {self.raise_always_min_pwm}, " \
               f"Output Lower: {self.lower_output_id}, " \
               f"Output Lower Channel: {self.lower_output_channel}, " \
               f"Output Lower Type: {self.lower_output_type}, " \
               f"Output Lower Min On: {self.lower_min_duration}, " \
               f"Output Lower Max On: {self.lower_max_duration}, " \
               f"Output Lower Min Off: {self.lower_min_off_duration}, " \
               f"Output Lower Always Min: {self.lower_always_min_pwm}, " \
               f"Setpoint Tracking Type: {self.setpoint_tracking_type}, " \
               f"Setpoint Tracking ID: {self.setpoint_tracking_id}"

    def control_var_to_duty_cycle(self, control_variable):
        # Convert control variable to duty cycle
        if control_variable > self.period:
            return 100.0
        else:
            return float((control_variable / self.period) * 100)

    @staticmethod
    def return_output_channel(output_channel_id):
        output_channel = db_retrieve_table_daemon(
            OutputChannel, unique_id=output_channel_id)
        if output_channel and output_channel.channel is not None:
            return output_channel.channel

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
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.is_held = True
            db_session.commit()
        self.logger.info("PID Held")
        return "success"

    def pid_pause(self):
        self.is_paused = True
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.is_paused = True
            db_session.commit()
        self.logger.info("PID Paused")
        return "success"

    def pid_resume(self):
        self.is_activated = True
        self.is_held = False
        self.is_paused = False
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.unique_id == self.unique_id).first()
            mod_pid.is_activated = True
            mod_pid.is_held = False
            mod_pid.is_paused = False
            db_session.commit()
        self.logger.info("PID Resumed")
        return "success"

    def set_setpoint(self, setpoint):
        """Set the setpoint of PID."""
        self.PID_Controller.setpoint = float(setpoint)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(PID.unique_id == self.unique_id).first()
            mod_pid.setpoint = setpoint
            db_session.commit()
        return f"Setpoint set to {setpoint}"

    def set_method(self, method_id):
        """Set the method of PID."""
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(PID.unique_id == self.unique_id).first()
            mod_pid.setpoint_tracking_id = method_id

            if method_id == '':
                self.setpoint_tracking_id = ''
                db_session.commit()
            else:
                mod_pid.method_start_time = None
                mod_pid.method_end_time = None
                db_session.commit()
                self.setup_method(method_id)

        return f"Method set to {method_id}"

    def set_integrator(self, integrator):
        """Set the integrator of the controller."""
        self.PID_Controller.integrator = float(integrator)
        return f"Integrator set to {self.PID_Controller.integrator}"

    def set_derivator(self, derivator):
        """Set the derivator of the controller."""
        self.PID_Controller.derivator = float(derivator)
        return f"Derivator set to {self.PID_Controller.derivator}"

    def set_kp(self, p):
        """Set Kp gain of the controller."""
        self.PID_Controller.Kp = float(p)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(PID.unique_id == self.unique_id).first()
            mod_pid.p = p
            db_session.commit()
        return f"Kp set to {self.PID_Controller.Kp}"

    def set_ki(self, i):
        """Set Ki gain of the controller."""
        self.PID_Controller.Ki = float(i)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(PID.unique_id == self.unique_id).first()
            mod_pid.i = i
            db_session.commit()
        return f"Ki set to {self.PID_Controller.Ki}"

    def set_kd(self, d):
        """Set Kd gain of the controller."""
        self.PID_Controller.Kd = float(d)
        with session_scope(MYCODO_DB_PATH) as db_session:
            mod_pid = db_session.query(PID).filter(PID.unique_id == self.unique_id).first()
            mod_pid.d = d
            db_session.commit()
        return f"Kd set to {self.PID_Controller.Kd}"

    def get_setpoint(self):
        return self.PID_Controller.setpoint

    def get_setpoint_band(self):
        return self.PID_Controller.setpoint_band

    def get_error(self):
        return self.PID_Controller.error

    def get_integrator(self):
        return self.PID_Controller.integrator

    def get_derivator(self):
        return self.PID_Controller.derivator

    def get_kp(self):
        return self.PID_Controller.Kp

    def get_ki(self):
        return self.PID_Controller.Ki

    def get_kd(self):
        return self.PID_Controller.Kd

    def function_status(self):
        total = self.PID_Controller.P_value + self.PID_Controller.I_value + self.PID_Controller.D_value
        return_dict = {
            'string_status': "This info is being returned from the PID Controller."
                             f"\nCurrent time: {datetime.datetime.now()}"
                             f"\nControl Variable: {total:.4f} = "
                             f"{self.PID_Controller.P_value:.4f} (P), "
                             f"{self.PID_Controller.I_value:.4f} (I), "
                             f"{self.PID_Controller.D_value:.4f} (D)",
            'error': []
        }
        return return_dict

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
                mod_pid.method_start_time = None
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
