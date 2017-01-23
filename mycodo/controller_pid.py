#!/usr/bin/python
# coding=utf-8
#
# controller_pid.py - PID controller that manages descrete control of a
#                     regulation system of sensors, relays, and devices
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
import logging
import datetime
import threading
import time as t
import timeit

# Classes
from databases.mycodo_db.models import (
    Method,
    PID,
    Relay,
    Sensor
)
from mycodo_client import DaemonControl

# Functions
from databases.utils import session_scope
from utils.database import db_retrieve_table
from utils.influx import (
    read_last_influxdb,
    write_influxdb_setpoint
)
from utils.method import (
    bezier_curve_y_out,
    sine_wave_y_out
)

# Config
from config import (
    SQL_DATABASE_MYCODO
)

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
        self.control = DaemonControl()

        self.initialize_values()

        self.Derivator = 0
        self.Integrator = 0
        self.error = 0.0
        self.P_value = None
        self.I_value = None
        self.D_value = None
        self.raise_seconds_on = 0
        self.last_measurement_success = False
        self.timer = t.time()+self.measure_interval

        # Check if a method is set for this PID
        if self.method_id:
            method = db_retrieve_table(MYCODO_DB_PATH, Method)
            method = method.filter(Method.method_id == self.method_id)
            method = method.filter(Method.method_order == 0).first()
            self.method_type = method.method_type
            self.method_start_time = method.start_time

            if self.method_type == 'Duration':
                if self.method_start_time == 'Ended':
                    # Method has ended and hasn't been instructed to begin again
                    pass
                elif self.method_start_time == 'Ready' or self.method_start_time is None:
                    # Method has been instructed to begin
                    with session_scope(MYCODO_DB_PATH) as db_session:
                        mod_method = db_session.query(Method)
                        mod_method = mod_method.filter(Method.method_id == self.method_id)
                        mod_method = mod_method.filter(Method.method_order == 0).first()
                        mod_method.start_time = datetime.datetime.now()
                        self.method_start_time = mod_method.start_time
                        db_session.commit()
                else:
                    # Method neither instructed to begin or not to
                    # Likely there was a daemon restart ot power failure
                    # Resume method with saved start_time
                    self.method_start_time = datetime.datetime.strptime(
                        self.method_start_time, '%Y-%m-%d %H:%M:%S.%f')
                    self.logger.warning("Resuming method {} started at {}".format(
                        self.method_id, self.method_start_time))

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer()-self.thread_startup_timer)*1000))
            if self.activated == 2:
                self.logger.info("Paused")
            elif self.activated == 3:
                self.logger.info("Held")
            self.ready.set()

            while self.running:
                if t.time() > self.timer:
                    self.timer = self.timer+self.measure_interval
                    # self.activated: 0=inactive, 1=active, 2=pause, 3=hold

                    # If active, retrieve sensor measurement and update PID output
                    if self.activated == 1:
                        self.get_last_measurement()

                        if self.last_measurement_success:
                            # Update setpoint if a method is selected
                            if self.method_id != '':
                                self.calculate_method_setpoint(self.method_id)
                            write_influxdb_setpoint(self.pid_id, self.set_point)
                            # Update PID and get control variable
                            self.control_variable = self.update(self.last_measurement)

                    # If active or on hold, activate relays
                    if self.activated in [1, 3]:
                        self.manipulate_relays()
                t.sleep(0.1)

            if self.raise_relay_id:
                self.control.relay_off(self.raise_relay_id)
            if self.lower_relay_id:
                self.control.relay_off(self.lower_relay_id)

            self.running = False
            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer()-self.thread_shutdown_timer)*1000))
        except Exception as except_msg:
                self.logger.exception("Run Error: {err}".format(
                    err=except_msg))

    def initialize_values(self):
        """Set PID parameters"""
        pid = db_retrieve_table(MYCODO_DB_PATH, PID, device_id=self.pid_id)
        sensor = db_retrieve_table(MYCODO_DB_PATH, Sensor, device_id=pid.sensor_id)
        self.activated = pid.activated  # 0=inactive, 1=active, 2=paused
        self.sensor_id = pid.sensor_id
        self.measure_type = pid.measure_type
        self.method_id = pid.method_id
        self.direction = pid.direction
        self.raise_relay_id = pid.raise_relay_id
        self.raise_min_duration = pid.raise_min_duration
        self.raise_max_duration = pid.raise_max_duration
        self.lower_relay_id = pid.lower_relay_id
        self.lower_min_duration = pid.lower_min_duration
        self.lower_max_duration = pid.lower_max_duration
        self.Kp = pid.p
        self.Ki = pid.i
        self.Kd = pid.d
        self.Integrator_min = pid.integrator_min
        self.Integrator_max = pid.integrator_max
        self.measure_interval = pid.period
        self.default_set_point = pid.setpoint
        self.set_point = pid.setpoint
        self.sensor_duration = sensor.period
        return "success"

    def update(self, current_value):
        """
        Calculate PID output value from reference input and feedback

        :return: Manipulated, or control, variable. This is the PID output.
        :rtype: float

        :param current_value: The input, or process, variable (the actual
            measured condition by the sensor)
        :type current_value: float
        """
        self.error = self.set_point - current_value

        # Calculate P-value
        self.P_value = self.Kp * self.error

        # Calculate I-value
        self.Integrator += self.error

        # First method for managing Integrator
        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min

        # Second method for regulating Integrator
        # if self.measure_interval is not None:
        #     if self.Integrator * self.Ki > self.measure_interval:
        #         self.Integrator = self.measure_interval / self.Ki
        #     elif self.Integrator * self.Ki < -self.measure_interval:
        #         self.Integrator = -self.measure_interval / self.Ki

        self.I_value = self.Integrator * self.Ki

        # Calculate D-value
        self.D_value = self.Kd * (self.error - self.Derivator)
        self.Derivator = self.error

        # Produce output form P, I, and D values
        PID_value = self.P_value + self.I_value + self.D_value

        return PID_value

    def get_last_measurement(self):
        """
        Retrieve the latest sensor measurement from InfluxDB

        :rtype: None
        """
        self.last_measurement_success = False
        # Get latest measurement (from within the past minute) from influxdb
        try:
            if self.sensor_duration < 60:
                duration = 60
            else:
                duration = int(self.sensor_duration*1.5)
            self.last_measurement = read_last_influxdb(
                self.sensor_id,
                self.measure_type,
                duration)
            if self.last_measurement:
                measurement_list = list(self.last_measurement.get_points(
                    measurement=self.measure_type))
                self.last_time = measurement_list[0]['time']
                self.last_measurement = measurement_list[0]['value']
                utc_dt = datetime.datetime.strptime(self.last_time.split(".")[0], '%Y-%m-%dT%H:%M:%S')
                utc_timestamp = calendar.timegm(utc_dt.timetuple())
                local_timestamp = str(datetime.datetime.fromtimestamp(utc_timestamp))
                self.logger.debug("Latest {}: {} @ {}".format(
                    self.measure_type, self.last_measurement,
                    local_timestamp))
                self.last_measurement_success = True
            else:
                self.logger.warning("No data returned from influxdb")
        except Exception as except_msg:
            self.logger.exception("Failed to read measurement from the "
                                  "influxdb database: {err}".format(
                err=except_msg))

    def manipulate_relays(self):
        """
        Activate a relay based on PID output (control variable) and whether
        the manipulation directive is to raise, lower, or both.

        :rtype: None
        """
        # If there was a measurement able to be retrieved from
        # influxdb database that was entered within the past minute
        if self.last_measurement_success:
            #
            # PID control variable positive to raise environmental condition
            #
            if self.direction in ['raise', 'both'] and self.raise_relay_id:
                if self.control_variable > 0:
                    # Ensure the relay on duration doesn't exceed the set maximum
                    if (self.raise_max_duration and
                            self.control_variable > self.raise_max_duration):
                        self.raise_seconds_on = self.raise_max_duration
                    else:
                        self.raise_seconds_on = float("{0:.2f}".format(self.control_variable))

                    # Turn off lower_relay if active, because we're now raising
                    if self.lower_relay_id:
                        relay = db_retrieve_table(
                            MYCODO_DB_PATH,
                            Relay,
                            device_id=self.lower_relay_id)
                        if relay.is_on():
                            self.control.relay_off(self.lower_relay_id)

                    if self.raise_seconds_on > self.raise_min_duration:
                        # Activate raise_relay for a duration
                        self.logger.debug("Setpoint: {sp} Output: {op} to "
                                          "relay {relay}".format(
                                sp=self.set_point,
                                op=self.control_variable,
                                relay=self.raise_relay_id))
                        self.control.relay_on(self.raise_relay_id,
                                              self.raise_seconds_on)
                else:
                    self.control.relay_off(self.raise_relay_id)

            #
            # PID control variable negative to lower environmental condition
            #
            if self.direction in ['lower', 'both'] and self.lower_relay_id:
                if self.control_variable < 0:
                    # Ensure the relay on duration doesn't exceed the set maximum
                    if (self.lower_max_duration and
                            abs(self.control_variable) > self.lower_max_duration):
                        self.lower_seconds_on = self.lower_max_duration
                    else:
                        self.lower_seconds_on = abs(float("{0:.2f}".format(self.control_variable)))

                    # Turn off raise_relay if active, because we're now lowering
                    if self.raise_relay_id:
                        relay = db_retrieve_table(
                            MYCODO_DB_PATH,
                            Relay,
                            device_id=self.raise_relay_id)
                        if relay.is_on():
                            self.control.relay_off(self.raise_relay_id)

                    if self.lower_seconds_on > self.lower_min_duration:
                        # Activate lower_relay for a duration
                        self.logger.debug("Setpoint: {sp} Output: {op} to "
                                          "relay {relay}".format(
                                            sp=self.set_point,
                                            op=self.control_variable,
                                            relay=self.lower_relay_id))
                        self.control.relay_on(self.lower_relay_id,
                                              self.lower_seconds_on)
                else:
                    self.control.relay_off(self.lower_relay_id)

        else:
            if self.direction in ['raise', 'both'] and self.raise_relay_id:
                self.control.relay_off(self.raise_relay_id)
            if self.direction in ['lower', 'both'] and self.lower_relay_id:
                self.control.relay_off(self.lower_relay_id)

    def calculate_method_setpoint(self, method_id):
        method = db_retrieve_table(MYCODO_DB_PATH, Method)

        method_key = method.filter(Method.method_id == method_id)
        method_key = method_key.filter(Method.method_order == 0).first()

        method = method.filter(Method.method_id == method_id)
        method = method.filter(Method.relay_id == None)
        method = method.filter(Method.method_order > 0)
        method = method.order_by(Method.method_order.asc()).all()

        now = datetime.datetime.now()

        # Calculate where the current time/date is within the time/date method
        if method_key.method_type == 'Date':
            for each_method in method:
                start_time = datetime.datetime.strptime(each_method.start_time, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.datetime.strptime(each_method.end_time, '%Y-%m-%d %H:%M:%S')
                if start_time < now < end_time:
                    start_setpoint = each_method.start_setpoint
                    if each_method.end_setpoint:
                        end_setpoint = each_method.end_setpoint
                    else:
                        end_setpoint = each_method.start_setpoint

                    setpoint_diff = abs(end_setpoint-start_setpoint)
                    total_seconds = (end_time-start_time).total_seconds()
                    part_seconds = (now-start_time).total_seconds()
                    percent_total = part_seconds/total_seconds

                    if start_setpoint < end_setpoint:
                        new_setpoint = start_setpoint+(setpoint_diff*percent_total)
                    else:
                        new_setpoint = start_setpoint-(setpoint_diff*percent_total)

                    self.logger.debug("[Method] Start: {} End: {}".format(
                        start_time, end_time))
                    self.logger.debug("[Method] Start: {} End: {}".format(
                        start_setpoint, end_setpoint))
                    self.logger.debug("[Method] Total: {} Part total: {} ({}%)".format(
                        total_seconds, part_seconds, percent_total))
                    self.logger.debug("[Method] New Setpoint: {}".format(
                        new_setpoint))
                    self.set_point = new_setpoint
                    return 0

        # Calculate where the current Hour:Minute:Seconds is within the Daily method
        elif method_key.method_type == 'Daily':
            daily_now = datetime.datetime.now().strftime('%H:%M:%S')
            daily_now = datetime.datetime.strptime(str(daily_now), '%H:%M:%S')
            for each_method in method:
                start_time = datetime.datetime.strptime(each_method.start_time, '%H:%M:%S')
                end_time = datetime.datetime.strptime(each_method.end_time, '%H:%M:%S')
                if start_time < daily_now < end_time:
                    start_setpoint = each_method.start_setpoint
                    if each_method.end_setpoint:
                        end_setpoint = each_method.end_setpoint
                    else:
                        end_setpoint = each_method.start_setpoint

                    setpoint_diff = abs(end_setpoint-start_setpoint)
                    total_seconds = (end_time-start_time).total_seconds()
                    part_seconds = (daily_now-start_time).total_seconds()
                    percent_total = part_seconds/total_seconds

                    if start_setpoint < end_setpoint:
                        new_setpoint = start_setpoint+(setpoint_diff*percent_total)
                    else:
                        new_setpoint = start_setpoint-(setpoint_diff*percent_total)

                    self.logger.debug("[Method] Start: {} End: {}".format(
                        start_time.strftime('%H:%M:%S'), end_time.strftime('%H:%M:%S')))
                    self.logger.debug("[Method] Start: {} End: {}".format(
                        start_setpoint, end_setpoint))
                    self.logger.debug("[Method] Total: {} Part total: {} ({}%)".format(
                        total_seconds, part_seconds, percent_total))
                    self.logger.debug("[Method] New Setpoint: {}".format(
                        new_setpoint))
                    self.set_point = new_setpoint
                    return 0

        # Calculate sine y-axis value from the x-axis (seconds of the day)
        elif method_key.method_type == 'DailySine':
            new_setpoint = sine_wave_y_out(method_key.amplitude,
                                           method_key.frequency,
                                           method_key.shift_angle,
                                           method_key.shift_y)
            self.set_point = new_setpoint
            return 0

        # Calculate Bezier curve y-axis value from the x-axis (seconds of the day)
        elif method_key.method_type == 'DailyBezier':
            new_setpoint = bezier_curve_y_out(method_key.shift_angle,
                                              (method_key.x0, method_key.y0),
                                              (method_key.x1, method_key.y1),
                                              (method_key.x2, method_key.y2),
                                              (method_key.x3, method_key.y3))
            self.set_point = new_setpoint
            return 0

        # Calculate the duration in the method based on self.method_start_time
        elif method_key.method_type == 'Duration' and self.method_start_time != 'Ended':
            seconds_from_start = (now-self.method_start_time).total_seconds()
            total_sec = 0
            previous_total_sec = 0
            for each_method in method:
                total_sec += each_method.duration_sec
                if previous_total_sec <= seconds_from_start < total_sec:
                    row_start_time = float(self.method_start_time.strftime('%s'))+previous_total_sec
                    row_since_start_sec = (now-(self.method_start_time+datetime.timedelta(0, previous_total_sec))).total_seconds()
                    percent_row = row_since_start_sec/each_method.duration_sec

                    start_setpoint = each_method.start_setpoint
                    if each_method.end_setpoint:
                        end_setpoint = each_method.end_setpoint
                    else:
                        end_setpoint = each_method.start_setpoint
                    setpoint_diff = abs(end_setpoint-start_setpoint)
                    if start_setpoint < end_setpoint:
                        new_setpoint = start_setpoint+(setpoint_diff*percent_row)
                    else:
                        new_setpoint = start_setpoint-(setpoint_diff*percent_row)

                    self.logger.debug("[Method] Start: {} Seconds Since: {}".format(
                        self.method_start_time, seconds_from_start))
                    self.logger.debug("[Method] Start time of row: {}".format(
                        datetime.datetime.fromtimestamp(row_start_time)))
                    self.logger.debug("[Method] Sec since start of row: {}".format(
                        row_since_start_sec))
                    self.logger.debug("[Method] Percent of row: {}".format(
                        percent_row))
                    self.logger.debug("[Method] New Setpoint: {}".format(
                        new_setpoint))
                    self.set_point = new_setpoint
                    return 0
                previous_total_sec = total_sec

            # Duration method has ended, reset start_time locally and in DB
            if self.method_start_time:
                with session_scope(MYCODO_DB_PATH) as db_session:
                    mod_method = db_session.query(Method).filter(
                        Method.method_id == self.method_id)
                    mod_method = mod_method.filter(Method.method_order == 0).first()
                    mod_method.start_time = 'Ended'
                    db_session.commit()
                self.method_start_time = 'Ended'

        # Setpoint not needing to be calculated, use default setpoint
        self.set_point = self.default_set_point

    def pid_mod(self):
        if self.initialize_values():
            return "success"
        else:
            return "error"

    def pid_hold(self):
        self.activated = 3
        self.logger.info("Hold")
        return "success"

    def pid_pause(self):
        self.activated = 2
        self.logger.info("Pause")
        return "success"

    def pid_resume(self):
        self.activated = 1
        self.logger.info("Resume")
        return "success"

    def set_setpoint(self, set_point):
        """Initilize the setpoint of PID"""
        self.set_point = set_point
        self.Integrator = 0
        self.Derivator = 0

    def set_integrator(self, Integrator):
        """Set the Integrator of the controller"""
        self.Integrator = Integrator

    def set_derivator(self, Derivator):
        """Set the Derivator of the controller"""
        self.Derivator = Derivator

    def set_kp(self, P):
        """Set Kp gain of the controller"""
        self.Kp = P

    def set_ki(self, I):
        """Set Ki gain of the controller"""
        self.Ki = I

    def set_kd(self, D):
        """Set Kd gain of the controller"""
        self.Kd = D

    def get_setpoint(self):
        return self.set_point

    def get_error(self):
        return self.error

    def get_integrator(self):
        return self.Integrator

    def get_derivator(self):
        return self.Derivator

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
        # Unset method start time
        if self.method_id:
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_method = db_session.query(Method)
                mod_method = mod_method.filter(Method.method_id == self.method_id)
                mod_method = mod_method.filter(Method.method_order == 0).first()
                mod_method.start_time = 'Ended'
                db_session.commit()
