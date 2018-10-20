# coding=utf-8
#
# controller_trigger.py - Trigger controller that checks measurements
#                         and performs functions in response to events
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

import datetime
import logging
import threading
import time
import timeit

import RPi.GPIO as GPIO

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import SMTP
from mycodo.databases.models import Trigger
from mycodo.databases.utils import session_scope
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.function_actions import trigger_function_actions
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.method import calculate_method_setpoint
from mycodo.utils.sunriseset import calculate_sunrise_sunset_epoch
from mycodo.utils.system_pi import epoch_of_next_time
from mycodo.utils.system_pi import time_between_range

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class TriggerController(threading.Thread):
    """
    Class to operate Trigger controller

    Triggers are conditional statements that can either be True or False
    When a conditional is True, one or more actions associated with that
    conditional are executed.

    The main loop in this class will continually check if the timers for
    Measurement Triggers have elapsed, then check if any of the
    conditionals are True with the check_triggers() function. If any are
    True, trigger_trigger_actions() will be ran to execute all actions
    associated with that particular conditional.

    Edge and Output conditionals are triggered from
    the Input and Output controllers, respectively, and the
    trigger_trigger_actions() function in this class will be ran.
    """
    def __init__(self, ready, function_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger(
            "mycodo.trigger_{id}".format(id=function_id.split('-')[0]))

        self.function_id = function_id
        self.running = False
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.pause_loop = False
        self.verify_pause_loop = True
        self.ready = ready
        self.control = DaemonControl()

        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_conditional

        self.conditional_type = None
        self.is_activated = None
        self.smtp_max_count = None
        self.email_count = None
        self.allowed_to_send_notice = None
        self.smtp_wait_timer = None
        self.timer_period = None
        self.period = None
        self.refractory_period = None
        self.timer_refractory_period = None
        self.smtp_wait_timer = None
        self.timer_period = None
        self.timer_start_time = None
        self.timer_end_time = None
        self.unique_id_1 = None
        self.unique_id_2 = None
        self.trigger_actions_at_period = None
        self.trigger_actions_at_start = None
        self.method_start_time = None
        self.method_end_time = None
        self.method_start_act = None

        self.setup_settings()

    def run(self):
        try:
            self.running = True
            self.logger.info(
                "Activated in {:.1f} ms".format(
                    (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            while self.running:
                # Pause loop to modify conditional statements.
                # Prevents execution of conditional while variables are
                # being modified.
                if self.pause_loop:
                    self.verify_pause_loop = True
                    while self.pause_loop:
                        time.sleep(0.1)

                if (self.is_activated and self.timer_period and
                        self.timer_period < time.time()):
                    check_approved = False

                    # Check if the conditional period has elapsed
                    if self.conditional_type in ['sunrise_sunset', 'run_pwm_method']:
                        while self.timer_period < time.time():
                            self.timer_period += self.period

                        if self.conditional_type == 'run_pwm_method':
                            # Only execute conditional actions when started
                            # Now only set PWM output
                            pwm_duty_cycle, ended = self.get_method_output(
                                self.unique_id_1)
                            if not ended:
                                self.set_output_duty_cycle(
                                    self.unique_id_2,
                                    pwm_duty_cycle)
                                if self.trigger_actions_at_period:
                                    trigger_function_actions(
                                        self.function_id,
                                        duty_cycle=pwm_duty_cycle)
                        else:
                            check_approved = True

                    elif (self.conditional_type in [
                            'timer_daily_time_point',
                            'timer_daily_time_span',
                            'timer_duration']):
                        if self.conditional_type == 'timer_daily_time_point':
                            self.timer_period = epoch_of_next_time(
                                '{hm}:00'.format(hm=self.timer_start_time))
                        elif self.conditional_type in ['timer_duration',
                                                       'timer_daily_time_span']:
                            while self.timer_period < time.time():
                                self.timer_period += self.period
                        check_approved = True

                    if check_approved:
                        self.check_triggers()

                time.sleep(self.sample_rate)

            self.running = False
            self.logger.info(
                "Deactivated in {:.1f} ms".format(
                    (timeit.default_timer() -
                     self.thread_shutdown_timer) * 1000))
        except Exception as except_msg:
            self.logger.exception("Run Error: {err}".format(
                err=except_msg))

    def refresh_settings(self):
        """ Signal to pause the main loop and wait for verification, the refresh settings """
        self.pause_loop = True
        while not self.verify_pause_loop:
            time.sleep(0.1)

        self.logger.info("Refreshing conditional settings")
        self.setup_settings()

        self.pause_loop = False
        self.verify_pause_loop = False
        return "Trigger settings successfully refreshed"

    def setup_settings(self):
        """ Define all settings """
        cond = db_retrieve_table_daemon(
            Trigger, unique_id=self.function_id)

        self.conditional_type = cond.conditional_type
        self.is_activated = cond.is_activated

        self.smtp_max_count = db_retrieve_table_daemon(
            SMTP, entry='first').hourly_max
        self.email_count = 0
        self.allowed_to_send_notice = True

        now = time.time()

        self.smtp_wait_timer = now + 3600
        self.timer_period = None

        # Set up conditional timer (daily time point)
        if self.conditional_type == 'timer_daily_time_point':
            self.timer_start_time = cond.timer_start_time
            self.timer_period = epoch_of_next_time(
                '{hm}:00'.format(hm=cond.timer_start_time))

        # Set up conditional timer (daily time span)
        elif self.conditional_type == 'timer_daily_time_span':
            self.timer_start_time = cond.timer_start_time
            self.timer_end_time = cond.timer_end_time
            self.period = cond.period
            self.timer_period = now

        # Set up conditional timer (duration)
        elif self.conditional_type == 'timer_duration':
            self.period = cond.period
            if cond.timer_start_offset:
                self.timer_period = now + cond.timer_start_offset
            else:
                self.timer_period = now

        # Set up Run PWM Method conditional
        elif self.conditional_type == 'run_pwm_method':
            self.unique_id_1 = cond.unique_id_1
            self.unique_id_2 = cond.unique_id_2
            self.period = cond.period
            self.trigger_actions_at_period = cond.trigger_actions_at_period
            self.trigger_actions_at_start = cond.trigger_actions_at_start
            self.method_start_time = cond.method_start_time
            self.method_end_time = cond.method_end_time
            if self.is_activated:
                self.start_method(cond.unique_id_1)
            if self.trigger_actions_at_start:
                self.timer_period = now + cond.period
                if self.is_activated:
                    pwm_duty_cycle = self.get_method_output(
                        cond.unique_id_1)
                    self.set_output_duty_cycle(cond.unique_id_2,
                                               pwm_duty_cycle)
                    trigger_function_actions(
                        self.function_id, cond.unique_id, duty_cycle=pwm_duty_cycle)
            else:
                self.timer_period = now

        # Set up sunrise/sunset conditional
        elif self.conditional_type == 'sunrise_sunset':
            self.timer_refractory_period = 0
            self.period = 1000
            # Set the next trigger at the specified sunrise/sunset time (+-offsets)
            self.timer_period = calculate_sunrise_sunset_epoch(cond)

    def start_method(self, method_id):
        """ Instruct a method to start running """
        if method_id:
            method = db_retrieve_table_daemon(Method, unique_id=method_id)
            method_data = db_retrieve_table_daemon(MethodData)
            method_data = method_data.filter(MethodData.method_id == method_id)
            method_data_repeat = method_data.filter(MethodData.duration_sec == 0).first()
            self.method_start_act = self.method_start_time
            self.method_start_time = None
            self.method_end_time = None

            if method.method_type == 'Duration':
                if self.method_start_act == 'Ended':
                    with session_scope(MYCODO_DB_PATH) as db_session:
                        mod_conditional = db_session.query(Trigger)
                        mod_conditional = mod_conditional.filter(
                            Trigger.unique_id == self.function_id).first()
                        mod_conditional.is_activated = False
                        db_session.commit()
                    self.stop_controller()
                    self.logger.warning(
                        "Method has ended. "
                        "Activate the Trigger controller to start it again.")
                elif (self.method_start_act == 'Ready' or
                        self.method_start_act is None):
                    # Method has been instructed to begin
                    now = datetime.datetime.now()
                    self.method_start_time = now
                    if method_data_repeat and method_data_repeat.duration_end:
                        self.method_end_time = now + datetime.timedelta(
                            seconds=float(method_data_repeat.duration_end))

                    with session_scope(MYCODO_DB_PATH) as db_session:
                        mod_conditional = db_session.query(Trigger)
                        mod_conditional = mod_conditional.filter(
                            Trigger.unique_id == self.function_id).first()
                        mod_conditional.method_start_time = self.method_start_time
                        mod_conditional.method_end_time = self.method_end_time
                        db_session.commit()

    def get_method_output(self, method_id):
        """ Get output variable from method """
        this_controller = db_retrieve_table_daemon(
            Trigger, unique_id=self.function_id)
        setpoint, ended = calculate_method_setpoint(
            method_id,
            Trigger,
            this_controller,
            Method,
            MethodData,
            self.logger)

        if setpoint is not None:
            if setpoint > 100:
                setpoint = 100
            elif setpoint < 0:
                setpoint = 0

        if ended:
            with session_scope(MYCODO_DB_PATH) as db_session:
                mod_conditional = db_session.query(Trigger)
                mod_conditional = mod_conditional.filter(
                    Trigger.unique_id == self.function_id).first()
                mod_conditional.is_activated = False
                db_session.commit()
            self.is_activated = False
            self.stop_controller()

        return setpoint, ended

    def set_output_duty_cycle(self, output_id, duty_cycle):
        """ Set PWM Output duty cycle """
        self.control.output_on(output_id,
                               duty_cycle=duty_cycle)

    def check_triggers(self):
        """
        Check if any Triggers are activated and
        execute their actions if the Trigger is true.

        For example, if measured temperature is above 30C, notify me@gmail.com

        "if measured temperature is above 30C" is the Trigger to check.
        "notify me@gmail.com" is the Trigger Action to execute if the
        Trigger is True.
        """
        last_measurement = None
        gpio_state = None

        logger_cond = logging.getLogger("mycodo.conditional_{id}".format(
            id=self.function_id))

        cond = db_retrieve_table_daemon(
            Trigger, unique_id=self.function_id, entry='first')

        now = time.time()
        timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
        message = "{ts}\n[Trigger {id} ({name})]".format(
            ts=timestamp,
            name=cond.name,
            id=self.function_id)

        device_id = cond.measurement.split(',')[0]

        if len(cond.measurement.split(',')) > 1:
            device_measurement = cond.measurement.split(',')[1]
        else:
            device_measurement = None

        direction = cond.direction
        setpoint = cond.setpoint
        max_age = cond.max_age

        device = None

        input_dev = db_retrieve_table_daemon(
            Input, unique_id=device_id, entry='first')
        if input_dev:
            device = input_dev

        math = db_retrieve_table_daemon(
            Math, unique_id=device_id, entry='first')
        if math:
            device = math

        output = db_retrieve_table_daemon(
            Output, unique_id=device_id, entry='first')
        if output:
            device = output

        pid = db_retrieve_table_daemon(
            PID, unique_id=device_id, entry='first')
        if pid:
            device = pid

        if not device:
            message += " Error: Controller not Input, Math, Output, or PID"
            logger_cond.error(message)
            return

        # Check Measurement Triggers
        if (cond.conditional_type == 'measurement' and
                direction and device_id and device_measurement):

            # Check if there hasn't been a measurement in the last set number
            # of seconds. If not, trigger conditional
            if direction == 'none_found':
                last_measurement = self.get_last_measurement(
                    device_id, device_measurement, max_age)
                if last_measurement is None:
                    message += " Measurement {meas} for device ID {id} not found in the past" \
                               " {value} seconds.".format(
                                    meas=device_measurement,
                                    id=device_id,
                                    value=max_age)
                else:
                    return

            # Check if last measurement is greater or less than the set value
            else:
                last_measurement = self.get_last_measurement(
                    device_id,
                    device_measurement,
                    max_age)
                if last_measurement is None:
                    logger_cond.debug("Last measurement not found")
                    return
                elif ((direction == 'above' and
                       last_measurement > setpoint) or
                      (direction == 'below' and
                       last_measurement < setpoint)):

                    message += " Measurement {meas}: {value} ".format(
                        meas=device_measurement,
                        value=last_measurement)
                    if direction == 'above':
                        message += ">"
                    elif direction == 'below':
                        message += "<"
                    message += " {sp} (set value).".format(
                        sp=setpoint)
                else:
                    return  # Not triggered

        # If the edge detection variable is set, calling this function will
        # trigger an edge detection event. This will merely produce the correct
        # message based on the edge detection settings.
        elif cond.conditional_type == 'edge':
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(int(input_dev.pin), GPIO.IN)
                gpio_state = GPIO.input(int(input_dev.pin))
            except:
                gpio_state = None
                logger_cond.error("Exception reading the GPIO pin")
            if (input_dev and
                    input_dev.location and
                    gpio_state is not None and
                    gpio_state == cond.if_sensor_gpio_state):
                message += " GPIO State Detected (state = {state}).".format(
                    state=cond.if_sensor_gpio_state)
            else:
                logger_cond.error("GPIO not configured correctly or GPIO state not verified")
                return

        # Calculate the sunrise/sunset times and find the next time this conditional should trigger
        elif cond.conditional_type == 'sunrise_sunset':
            # Since the check time is the trigger time, we will only calculate and set the next trigger time
            self.timer_period = calculate_sunrise_sunset_epoch(cond)

        # Set the refractory period
        if cond.conditional_type == 'measurement':
            self.timer_refractory_period = time.time() + self.refractory_period

        # Check if the current time is between the start and end time
        if cond.conditional_type == 'timer_daily_time_span':
            if not time_between_range(self.timer_start_time, self.timer_end_time):
                return

        # If the code hasn't returned by now, the conditional has been triggered
        # and the actions for that conditional should be executed
        trigger_function_actions(
            self.function_id,
            message=message, last_measurement=last_measurement,
            device_id=device_id, device_measurement=device_measurement,
            edge=gpio_state)
    
    @staticmethod
    def get_last_measurement(unique_id, measurement, duration_sec):
        """
        Retrieve the latest input measurement

        :return: The latest input value or None if no data available
        :rtype: float or None

        :param unique_id: ID of controller
        :type unique_id: str
        :param measurement: Environmental condition of a input (e.g.
            temperature, humidity, pressure, etc.)
        :type measurement: str
        :param duration_sec: number of seconds to check for a measurement
            in the past.
        :type duration_sec: int
        """
        last_measurement = read_last_influxdb(
            unique_id, measurement, duration_sec=duration_sec)

        if last_measurement is not None:
            last_value = last_measurement[1]
            return last_value

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
