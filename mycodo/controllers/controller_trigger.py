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
import threading
import time

import RPi.GPIO as GPIO

from mycodo.controllers.base_controller import AbstractController
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
from mycodo.utils.method import calculate_method_setpoint
from mycodo.utils.sunriseset import calculate_sunrise_sunset_epoch
from mycodo.utils.system_pi import epoch_of_next_time
from mycodo.utils.system_pi import time_between_range

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class TriggerController(AbstractController, threading.Thread):
    """
    Class to operate Trigger controller

    Triggers are events that are used to signal when a set of actions
    should be executed.

    The main loop in this class will continually check if any timer
    Triggers have elapsed. If any have, trigger_all_actions()
    will be ran to execute all actions associated with that particular
    trigger.

    Edge and Output conditionals are triggered from
    the Input and Output controllers, respectively, and the
    trigger_all_actions() function in this class will be ran.
    """
    def __init__(self, ready, unique_id):
        threading.Thread.__init__(self)
        super(TriggerController, self).__init__(ready, unique_id=unique_id, name=__name__)

        self.unique_id = unique_id
        self.sample_rate = None

        self.control = DaemonControl()
        
        self.pause_loop = False
        self.verify_pause_loop = True
        self.trigger = None
        self.trigger_type = None
        self.trigger_name = None
        self.is_activated = None
        self.log_level_debug = None
        self.smtp_max_count = None
        self.email_count = None
        self.allowed_to_send_notice = None
        self.smtp_wait_timer = None
        self.timer_period = None
        self.period = None
        self.smtp_wait_timer = None
        self.timer_start_time = None
        self.timer_end_time = None
        self.unique_id_1 = None
        self.unique_id_2 = None
        self.trigger_actions_at_period = None
        self.trigger_actions_at_start = None
        self.method_start_time = None
        self.method_end_time = None
        self.method_start_act = None

        # Infrared remote input
        self.lirc = None
        self.program = None
        self.word = None

    def loop(self):
        # Pause loop to modify trigger.
        # Prevents execution of trigger while variables are
        # being modified.
        if self.pause_loop:
            self.verify_pause_loop = True
            while self.pause_loop:
                time.sleep(0.1)

        if self.trigger_type == 'trigger_infrared_remote_input':
            self.infrared_remote_input()

        elif (self.is_activated and self.timer_period and
                self.timer_period < time.time()):
            check_approved = False

            # Check if the trigger period has elapsed
            if self.trigger_type in ['trigger_sunrise_sunset',
                                     'trigger_run_pwm_method']:
                while self.running and self.timer_period < time.time():
                    self.timer_period = calculate_sunrise_sunset_epoch(self.trigger)

                if self.trigger_type == 'trigger_run_pwm_method':
                    # Only execute trigger actions when started
                    # Now only set PWM output
                    pwm_duty_cycle, ended = self.get_method_output(
                        self.unique_id_1)
                    if not ended:
                        self.set_output_duty_cycle(
                            self.unique_id_2,
                            pwm_duty_cycle)
                        if self.trigger_actions_at_period:
                            trigger_function_actions(
                                self.unique_id,
                                debug=self.log_level_debug)
                else:
                    check_approved = True

            elif (self.trigger_type in [
                    'trigger_timer_daily_time_point',
                    'trigger_timer_daily_time_span',
                    'trigger_timer_duration']):
                if self.trigger_type == 'trigger_timer_daily_time_point':
                    self.timer_period = epoch_of_next_time(
                        '{hm}:00'.format(hm=self.timer_start_time))
                elif self.trigger_type in ['trigger_timer_duration',
                                           'trigger_timer_daily_time_span']:
                    while self.running and self.timer_period < time.time():
                        self.timer_period += self.period
                check_approved = True

            if check_approved:
                self.attempt_execute(self.check_triggers)

    def run_finally(self):
        pass

    def refresh_settings(self):
        """ Signal to pause the main loop and wait for verification, the refresh settings """
        self.pause_loop = True
        while not self.verify_pause_loop:
            time.sleep(0.1)

        self.logger.info("Refreshing trigger settings")
        self.initialize_variables()

        self.pause_loop = False
        self.verify_pause_loop = False
        return "Trigger settings successfully refreshed"

    def initialize_variables(self):
        """ Define all settings """
        self.email_count = 0
        self.allowed_to_send_notice = True

        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_conditional

        self.smtp_max_count = db_retrieve_table_daemon(
            SMTP, entry='first').hourly_max

        self.trigger = db_retrieve_table_daemon(
            Trigger, unique_id=self.unique_id)
        self.trigger_type = self.trigger.trigger_type
        self.trigger_name = self.trigger.name
        self.is_activated = self.trigger.is_activated
        self.log_level_debug = self.trigger.log_level_debug

        self.set_log_level_debug(self.log_level_debug)

        now = time.time()
        self.smtp_wait_timer = now + 3600
        self.timer_period = None

        # Set up trigger timer (daily time point)
        if self.trigger_type == 'trigger_timer_daily_time_point':
            self.timer_start_time = self.trigger.timer_start_time
            self.timer_period = epoch_of_next_time(
                '{hm}:00'.format(hm=self.trigger.timer_start_time))

        # Set up trigger timer (daily time span)
        elif self.trigger_type == 'trigger_timer_daily_time_span':
            self.timer_start_time = self.trigger.timer_start_time
            self.timer_end_time = self.trigger.timer_end_time
            self.period = self.trigger.period
            self.timer_period = now

        # Set up trigger timer (duration)
        elif self.trigger_type == 'trigger_timer_duration':
            self.period = self.trigger.period
            if self.trigger.timer_start_offset:
                self.timer_period = now + self.trigger.timer_start_offset
            else:
                self.timer_period = now

        # Set up trigger Run PWM Method
        elif self.trigger_type == 'trigger_run_pwm_method':
            self.unique_id_1 = self.trigger.unique_id_1
            self.unique_id_2 = self.trigger.unique_id_2
            self.period = self.trigger.period
            self.trigger_actions_at_period = self.trigger.trigger_actions_at_period
            self.trigger_actions_at_start = self.trigger.trigger_actions_at_start
            self.method_start_time = self.trigger.method_start_time
            self.method_end_time = self.trigger.method_end_time
            if self.is_activated:
                self.start_method(self.trigger.unique_id_1)
            if self.trigger_actions_at_start:
                self.timer_period = now + self.trigger.period
                if self.is_activated:
                    pwm_duty_cycle = self.get_method_output(
                        self.trigger.unique_id_1)
                    self.set_output_duty_cycle(
                        self.trigger.unique_id_2, pwm_duty_cycle)
                    trigger_function_actions(self.unique_id,
                                             debug=self.log_level_debug)
            else:
                self.timer_period = now

        elif self.trigger_type == 'trigger_infrared_remote_input':
            import lirc
            self.lirc = lirc
            self.program = self.trigger.program
            self.word = self.trigger.word
            lirc.init(self.program,
                      config_filename='/home/pi/.lircrc',
                      blocking=False)

            # Set up trigger sunrise/sunset
        elif self.trigger_type == 'trigger_sunrise_sunset':
            self.period = 60
            # Set the next trigger at the specified sunrise/sunset time (+-offsets)
            self.timer_period = calculate_sunrise_sunset_epoch(self.trigger)

    def start_method(self, method_id):
        """ Instruct a method to start running """
        if method_id:
            method = db_retrieve_table_daemon(Method, unique_id=method_id)
            method_data = db_retrieve_table_daemon(MethodData)
            method_data = method_data.filter(MethodData.method_id == method_id)
            method_data_repeat = method_data.filter(
                MethodData.duration_sec == 0).first()
            self.method_start_act = self.method_start_time
            self.method_start_time = None
            self.method_end_time = None

            if method.method_type == 'Duration':
                if self.method_start_act == 'Ended':
                    with session_scope(MYCODO_DB_PATH) as db_session:
                        mod_conditional = db_session.query(Trigger)
                        mod_conditional = mod_conditional.filter(
                            Trigger.unique_id == self.unique_id).first()
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
                            Trigger.unique_id == self.unique_id).first()
                        mod_conditional.method_start_time = self.method_start_time
                        mod_conditional.method_end_time = self.method_end_time
                        db_session.commit()

    def get_method_output(self, method_id):
        """ Get output variable from method """
        this_controller = db_retrieve_table_daemon(
            Trigger, unique_id=self.unique_id)
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
                    Trigger.unique_id == self.unique_id).first()
                mod_conditional.is_activated = False
                db_session.commit()
            self.is_activated = False
            self.stop_controller()

        return setpoint, ended

    def set_output_duty_cycle(self, output_id, duty_cycle):
        """ Set PWM Output duty cycle """
        self.control.output_on(output_id, duty_cycle=duty_cycle)

    def check_triggers(self):
        """
        Check if any Triggers are activated and
        execute their actions if so.

        For example, if measured temperature is above 30C, notify me@gmail.com

        "if measured temperature is above 30C" is the Trigger to check.
        "notify me@gmail.com" is the Trigger Action to execute if the
        Trigger is True.
        """
        now = time.time()
        timestamp = datetime.datetime.fromtimestamp(now).strftime(
            '%Y-%m-%d %H:%M:%S')
        message = "{ts}\n[Trigger {id} ({name})]".format(
            ts=timestamp,
            name=self.trigger_name,
            id=self.unique_id)

        trigger = db_retrieve_table_daemon(
            Trigger, unique_id=self.unique_id, entry='first')

        device_id = trigger.measurement.split(',')[0]

        # if len(trigger.measurement.split(',')) > 1:
        #     device_measurement = trigger.measurement.split(',')[1]
        # else:
        #     device_measurement = None

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
            self.logger.error(message)
            return

        # If the edge detection variable is set, calling this function will
        # trigger an edge detection event. This will merely produce the correct
        # message based on the edge detection settings.
        elif trigger.trigger_type == 'trigger_edge':
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(int(input_dev.pin), GPIO.IN)
                gpio_state = GPIO.input(int(input_dev.pin))
            except:
                gpio_state = None
                self.logger.error("Exception reading the GPIO pin")
            if (gpio_state is not None and
                    gpio_state == trigger.if_sensor_gpio_state):
                message += " GPIO State Detected (state = {state}).".format(
                    state=trigger.if_sensor_gpio_state)
            else:
                self.logger.error("GPIO not configured correctly or GPIO state not verified")
                return

        # Calculate the sunrise/sunset times and find the next time this trigger should trigger
        elif trigger.trigger_type == 'trigger_sunrise_sunset':
            # Since the check time is the trigger time, we will only calculate and set the next trigger time
            self.timer_period = calculate_sunrise_sunset_epoch(trigger)

        # Check if the current time is between the start and end time
        elif trigger.trigger_type == 'trigger_timer_daily_time_span':
            if not time_between_range(self.timer_start_time,
                                      self.timer_end_time):
                return

        # If the code hasn't returned by now, action should be executed
        trigger_function_actions(
            self.unique_id,
            message=message,
            debug=self.log_level_debug)

    def infrared_remote_input(self):
        """
        Wait for an infrared input signal
        Because only one thread will capture the button press, the thread that
        catches it will send a broadcast of the codes to all trigger threads.
        """
        code = self.lirc.nextcode()
        if code:
            self.control.send_infrared_code_broadcast(code)

    def receive_infrared_code_broadcast(self, code):
        if self.word in code:
            timestamp = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y-%m-%d %H:%M:%S')
            message = "{ts}\n[Trigger {id} ({name})]".format(
                ts=timestamp,
                name=self.trigger_name,
                id=self.unique_id)
            message += "\nInfrared Remote Input detected " \
                       "'{word}' on program '{prog}'".format(
                        word=self.word, prog=self.program)
            trigger_function_actions(self.unique_id,
                                     message=message,
                                     debug=self.log_level_debug)
