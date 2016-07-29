#!/usr/bin/python
# coding=utf-8
#
# controller_pid.py - PID controller that manages descrete control of a
#                     regulation system of sensors, relays, and devices
#
# PID controller code was used from the source below, with modifications.
#
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
# <http://code.activestate.com/recipes/577231-discrete-pid-controller/>

import calendar
import threading
import time as t
import timeit
from datetime import datetime, time

from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import SQL_DATABASE_MYCODO
from databases.mycodo_db.models import PID
from databases.mycodo_db.models import PIDSetpoints
from databases.mycodo_db.models import Relay
from databases.utils import session_scope
from mycodo_client import DaemonControl
from daemonutils import read_last_influxdb, write_influxdb

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class PIDController(threading.Thread):
    """
    Class to operate discrete PID controller

    """

    def __init__(self, ready, logger, pid_id):
        threading.Thread.__init__(self)

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.logger = logger
        self.pid_id = pid_id
        self.control = DaemonControl()

        with session_scope(MYCODO_DB_PATH) as new_session:
            pid = new_session.query(PID).filter(PID.id == self.pid_id).first()
            self.sensor_id = pid.sensor_id
            self.measure_type = pid.measure_type
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
            self.measure_interval = pid.period
            self.default_set_point = pid.setpoint
            self.set_point = pid.setpoint

        with session_scope(MYCODO_DB_PATH) as new_session:
            self.pidsetpoints = new_session.query(PIDSetpoints)
            self.pidsetpoints = self.pidsetpoints.filter(PIDSetpoints.pid_id == self.pid_id)
            self.pidsetpoints = self.pidsetpoints.order_by(PIDSetpoints.start_time.asc())
            new_session.expunge_all()
            new_session.close()

        self.Derivator = 0
        self.Integrator = 0
        self.Integrator_max = 500
        self.Integrator_min = -500
        self.error = 0.0
        self.P_value = None
        self.I_value = None
        self.D_value = None
        self.raise_seconds_on = 0
        self.timer = t.time() + self.measure_interval


    def run(self):
        try:
            self.running = True
            self.logger.info("[PID {}] Activated in {}ms".format(
                self.pid_id,
                (timeit.default_timer()-self.thread_startup_timer)*1000))
            self.ready.set()

            while (self.running):
                if t.time() > self.timer:
                    self.timer = t.time() + self.measure_interval
                    self.get_last_measurement()
                    self.manipulate_relays()
                t.sleep(0.1)

            if self.raise_relay_id:
                self.control.relay_off(self.raise_relay_id)
            if self.lower_relay_id:
                self.control.relay_off(self.lower_relay_id)

            self.running = False
            self.logger.info("[PID {}] Deactivated in {}ms".format(
                self.pid_id,
                (timeit.default_timer()-self.thread_shutdown_timer)*1000))
        except Exception as except_msg:
                self.logger.exception("[PID {}] Error: {}".format(self.pid_id,
                                                                except_msg))


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
        # Old method for managing Integrator
        # if self.Integrator > self.Integrator_max:
        #     self.Integrator = self.Integrator_max
        # elif self.Integrator < self.Integrator_min:
        #     self.Integrator = self.Integrator_min
        # New method for regulating Integrator
        if self.measure_interval is not None:  
            if self.Integrator * self.Ki > self.measure_interval:
                self.Integrator = self.measure_interval / self.Ki
            elif self.Integrator * self.Ki < -self.measure_interval:
                self.Integrator = -self.measure_interval / self.Ki
        self.I_value = self.Integrator * self.Ki

        # Calculate D-value
        self.D_value = self.Kd * (self.error - self.Derivator)
        self.Derivator = self.error

        # Produce output form P, I, and D values
        PID = self.P_value + self.I_value + self.D_value
        return PID


    def get_last_measurement(self):
        """
        Retrieve the latest sensor measurement from InfluxDB

        :rtype: None
        """
        self.last_measurement_success = False
        # Get latest measurement (from within the past minute) from influxdb
        try:
            self.last_measurement = read_last_influxdb(
                INFLUXDB_HOST,
                INFLUXDB_PORT,
                INFLUXDB_USER,
                INFLUXDB_PASSWORD,
                INFLUXDB_DATABASE,
                self.sensor_id,
                self.measure_type)
            if self.last_measurement:
                measurement_list = list(self.last_measurement.get_points(
                    measurement=self.measure_type))
                self.last_time = measurement_list[0]['time']
                self.last_measurement = measurement_list[0]['value']
                utc_dt = datetime.strptime(self.last_time.split(".")[0], '%Y-%m-%dT%H:%M:%S')
                utc_timestamp = calendar.timegm(utc_dt.timetuple())
                local_timestamp = str(datetime.fromtimestamp(utc_timestamp))
                self.logger.debug("[PID {}] Latest {}: {} @ {}".format(
                    self.pid_id, self.measure_type,
                    self.last_measurement, local_timestamp))
                self.last_measurement_success = True
            else:
                self.logger.warning("[PID {}] No data returned "
                                    "from influxdb".format(self.pid_id))
        except Exception as except_msg:
            self.logger.exception("[PID {}] Failed to read "
                                "measurement from the influxdb "
                                "database: {}".format(self.pid_id,
                                                      except_msg))


    def manipulate_relays(self):
        """
        Activate a relay based on PID output (control variable) and whether
        the manipulation directive is to raise, lower, or both.

        :rtype: None
        """
        # If there was a measurement able to be retrieved from
        # influxdb database that was entered within the past minute
        if self.last_measurement_success:

            # Update setpoint if dynamic setpoints are enabled for this PID
            # and the current time is within one of the set time spans
            use_default_setpoint = True
            for each_setpt in self.pidsetpoints:
                if self.now_in_range(each_setpt.start_time,
                                     each_setpt.end_time):
                    use_default_setpoint = False
                    self.calculate_new_setpoint(each_setpt.start_time,
                                                each_setpt.end_time,
                                                each_setpt.start_setpoint,
                                                each_setpt.end_setpoint)
                    self.logger.debug("[PID {}] New setpoint: {}".format(self.pid_id, self.set_point))
            if use_default_setpoint:
                self.set_point = self.default_set_point

            self.addSetpointInfluxdb(self.pid_id, self.set_point)

            # Update PID and get control variable
            self.control_variable = self.update(self.last_measurement)

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
                        with session_scope(MYCODO_DB_PATH) as new_session:
                            relay = new_session.query(Relay).filter(
                                Relay.id == self.lower_relay_id).first()
                            if relay.is_on():
                                self.control.relay_off(self.lower_relay_id)

                    if self.raise_seconds_on > self.raise_min_duration:
                        # Activate raise_relay for a duration
                        self.logger.debug("[PID {}] Setpoint: {} "
                            "Output: {} to relay {}".format(
                                self.pid_id,
                                self.set_point,
                                self.control_variable,
                                self.raise_relay_id))
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
                        with session_scope(MYCODO_DB_PATH) as new_session:
                            relay = new_session.query(Relay).filter(
                                Relay.id == self.raise_relay_id).first()
                            if relay.is_on():
                                self.control.relay_off(self.raise_relay_id)

                    if self.lower_seconds_on > self.lower_min_duration:
                        # Activate lower_relay for a duration
                        self.logger.debug("[PID {}] Setpoint: {} "
                            "Output: {} to relay {}".format(
                                self.pid_id,
                                self.set_point,
                                self.control_variable,
                                self.lower_relay_id))
                        self.control.relay_on(self.lower_relay_id,
                                         self.lower_seconds_on)
                else:
                    self.control.relay_off(self.lower_relay_id)

        else:
            if self.direction in ['raise', 'both'] and self.raise_relay_id:
                self.control.relay_off(self.raise_relay_id)
            if self.direction in ['lower', 'both'] and self.lower_relay_id:
                self.control.relay_off(self.lower_relay_id)


    def now_in_range(self, start_time, end_time):
        """
        Check if the current time is between start_time and end_time

        :return: 1 is within range, 0 if not within range
        :rtype: int
        """
        start_hour = int(start_time.split(":")[0])
        start_min = int(start_time.split(":")[1])
        end_hour = int(end_time.split(":")[0])
        end_min = int(end_time.split(":")[1])
        now_time = datetime.now().time()
        now_time = now_time.replace(second=0, microsecond=0)
        if ((start_hour < end_hour) or
                (start_hour == end_hour and start_min < end_min)):
            if now_time >= time(start_hour,start_min) and now_time <= time(end_hour,end_min):
                return 1  # Yes now within range
        else:
            if now_time >= time(start_hour,start_min) or now_time <= time(end_hour,end_min):
                return 1  # Yes now within range
        return 0 # No now not within range


    def calculate_new_setpoint(self, start_time, end_time, start_setpoint, end_setpoint):
        """
        Calculate a dynamic setpoint that changes over time

        The current time must fall between the start_time and end_time.
        If there is only a start_setpoint, that is the only setpoint that can
        be returned.

        Based on where the current time falls between the start_time
        and the end_time, a setpoint between the start_setpoint and
        end_setpoint will be calculated.

        For example, if the time range is 12:00 to 1:00, and the setPoint
        range is 0 to 60, and the current time is 12:30, the calculated
        setpoint will be 30.

        :return: 0 if only a start setpoint is set, 1 if both start and end
            setpoints are set and the value between has been calculated.
        :rtype: int

        :param start_time: The start hour and minute of the time range
        :type start_time: str
        :param end_time: The end hour and minute of the time range
        :type end_time: str
        :param start_setpoint: The start setpoint
        :type start_setpoint: float
        :param end_setpoint: The end setpoint
        :type end_setpoint: float or None
        """
        # Only a start_setpoint set for this time period
        if end_setpoint is None:
            self.set_point = start_setpoint
            return 0

        # Split hour and minute into separate integers
        start_hour = int(start_time.split(":")[0])
        start_min = int(start_time.split(":")[1])
        end_hour = int(end_time.split(":")[0])
        end_min = int(end_time.split(":")[1])

        # Set the date and time format
        date_format = "%d %H:%M"  # Add day in case end time is the next day

        # Convert string of 'day hour:minute' to actual date and time
        start_time_formatted  = datetime.strptime("1 "+start_time, date_format)
        end_day_modifier = "1 "  # End time is the same day
        if (start_hour > end_hour or
                (start_hour == end_hour and start_min > end_min)):
            end_day_modifier = "2 "  # End time is the next day
        end_time_formatted  = datetime.strptime(end_day_modifier+end_time, date_format)

        # Total number of minute between start time and end time
        diff = end_time_formatted-start_time_formatted
        diff_min = diff.seconds/60

        # Find the difference between setpoints
        diff_setpoints = abs(end_setpoint-start_setpoint) 

        # Total number of minute between start time and now
        now = datetime.now()
        if now.hour > start_hour:
            hours = now.hour-start_hour
        elif now.hour < start_hour:
            hours = now.hour+(24-start_hour)
        elif now.hour == start_hour:
            hours = 0
        minutes = now.minute-start_min  # May be negative
        total_minutes = (hours*60)+minutes

        # Based on the number of minutes between the start and end time and the
        # minutes passed since the start time, calculate the new setpoint
        mod_setpoint = total_minutes/float(diff_min/diff_setpoints)

        if end_setpoint < start_setpoint:
            # Setpoint decreases over duration
            new_setpoint = float("{0:.2f}".format(start_setpoint-mod_setpoint))
        else:
            # Setpoint increases over duration
            new_setpoint = float("{0:.2f}".format(start_setpoint+mod_setpoint))

        self.set_point = new_setpoint
        return 1


    def addSetpointInfluxdb(self, pid_id, setpoint):
        """
        Add a setpoint entry to InfluxDB

        :rtype: None
        """
        write_db = threading.Thread(
            target=write_influxdb,
            args=(self.logger, INFLUXDB_HOST,
                  INFLUXDB_PORT, INFLUXDB_USER,
                  INFLUXDB_PASSWORD, INFLUXDB_DATABASE,
                  'pid', pid_id, 'setpoint', setpoint,))
        write_db.start()


    def setPoint(self, set_point):
        """Initilize the setpoint of PID"""
        self.set_point = set_point
        self.Integrator = 0
        self.Derivator = 0


    def setIntegrator(self, Integrator):
        """Set the Integrator of the controller"""
        self.Integrator = Integrator


    def setDerivator(self, Derivator):
        """Set the Derivator of the controller"""
        self.Derivator = Derivator


    def setKp(self, P):
        """Set Kp gain of the controller"""
        self.Kp = P


    def setKi(self, I):
        """Set Ki gain of the controller"""
        self.Ki = I


    def setKd(self, D):
        """Set Kd gain of the controller"""
        self.Kd = D


    def getPoint(self):
        return self.set_point


    def getError(self):
        return self.error


    def getIntegrator(self):
        return self.Integrator


    def getDerivator(self):
        return self.Derivator


    def isRunning(self):
        return self.running


    def stopController(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
