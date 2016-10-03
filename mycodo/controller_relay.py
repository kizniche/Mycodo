#!/usr/bin/python
# coding=utf-8
#
# controller_log.py - Log controller to periodically query influxdb
#                     and append a log file
#

import datetime
import RPi.GPIO as GPIO
import logging
import subprocess
import threading
import time
import timeit
from influxdb import InfluxDBClient

from config import LOG_PATH
from config import SQL_DATABASE_MYCODO
from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import MAX_AMPS

from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import RelayConditional
from databases.mycodo_db.models import SMTP
from databases.utils import session_scope

from mycodo_client import DaemonControl

from utils.influx import write_influxdb_value
from utils.send_data import send_email
from utils.system_pi import cmd_output

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class RelayController(threading.Thread):
    """
    class for controlling relays

    """

    def __init__(self, logger):
        threading.Thread.__init__(self)

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.logger = logger
        self.control = DaemonControl()

        self.relay_id = {}
        self.relay_name = {}
        self.relay_pin = {}
        self.relay_amps = {}
        self.relay_trigger = {}
        self.relay_start_state = {}
        self.relay_on_until = {}
        self.relay_last_duration = {}
        self.relay_on_duration = {}

        self.logger.debug("[Relay] Initializing Relays")
        try:
            with session_scope(MYCODO_DB_PATH) as new_session:
                smtp = new_session.query(SMTP).first()
                self.smtp_max_count = smtp.hourly_max
                self.smtp_wait_time = time.time() + 3600
                self.smtp_timer = time.time()
                self.email_count = 0
                self.allowed_to_send_notice = True

                relays = new_session.query(Relay).all()
                self.all_relays_initialize(relays)
            # Turn all relays off
            self.all_relays_off()
            # Turn relays on that are set to be on at start
            self.all_relays_on()
            self.logger.info("[Relay] Relays Initialized")

        except Exception as except_msg:
            self.logger.exception("[Relay] Problem initializing "
                                  "relays: {}", except_msg)

        self.running = False


    def run(self):
        try:
            self.running = True
            self.logger.info("[Relay] Relay controller activated in "
                             "{:.1f} ms".format((timeit.default_timer()-self.thread_startup_timer)*1000))
            while (self.running):
                current_time = datetime.datetime.now()
                for relay_id in self.relay_id:
                    if (self.relay_on_until[relay_id] < current_time and
                            self.relay_on_duration[relay_id] and 
                            self.relay_pin[relay_id]):

                        # Use threads to prevent a slow execution of a
                        # process that could slow the loop
                        turn_relay_off = threading.Thread(
                            target=self.relay_on_off,
                            args=(relay_id, 'off',))
                        turn_relay_off.start()

                        if self.relay_last_duration[relay_id] > 0:
                            duration = float(self.relay_last_duration[relay_id])
                            timestamp = datetime.datetime.utcnow()-datetime.timedelta(seconds=duration)
                            write_db = threading.Thread(
                                target=write_influxdb_value,
                                args=(self.logger, INFLUXDB_HOST,
                                      INFLUXDB_PORT, INFLUXDB_USER,
                                      INFLUXDB_PASSWORD, INFLUXDB_DATABASE,
                                      'relay', relay_id, 'duration_sec',
                                      duration,
                                      timestamp,))
                            write_db.start()

                time.sleep(0.01)
        finally:
            self.all_relays_off()
            self.cleanup_gpio()
            self.running = False    
            self.logger.info("[Relay] Relay controller deactivated in "
                             "{:.1f} ms".format((timeit.default_timer()-self.thread_shutdown_timer)*1000))


    def relay_on_off(self, relay_id, state,
                     duration=0.0, trigger_conditionals=True,
                     datetime_now=datetime.datetime.now()):
        """
        Turn a relay on or off
        The GPIO may be either HIGH or LOW to activate a relay. This trigger
        state will be referenced to determine if the GPIO needs to be high or
        low to turn the relay on or off.

        Conditionals will be checked for each action requested of a relay, and
        if true, those conditional actions will be executed. For example:
            'If relay 1 turns on, turn relay 3 off'

        :param relay_id: Unique ID for relay
        :type relay_id: str
        :param state: What state is desired? 'on' or 'off'
        :type state: str
        :param duration: If state is 'on', a duration can be set to turn the relay off after
        :type duration: float
        :param trigger_conditionals: Whether to trigger condionals to act or not
        :type trigger_conditionals: bool
        """
        # Check if relay exists
        if relay_id not in self.relay_id:
            self.logger.warning("[Relay] Cannot turn {} Relay with ID {}. It "
                                "doesn't exist".format(state, relay_id))
            return 1
        if state == 'on':
            if not self.relay_pin[relay_id]:
                self.logger.warning("[Relay] Invalid pin for relay "
                                    "{} ({}).".format(self.relay_id[relay_id],
                                                      self.relay_name[relay_id]))
                return 1

            current_amps = self.current_amp_load()
            if current_amps+self.relay_amps[relay_id] > MAX_AMPS:
                self.logger.warning("[Relay] Cannot turn relay {} "
                                    "({}) On. If this relay turns on, "
                                    "there will be {} amps being drawn, "
                                    "which exceeds the maximum set draw of {}"
                                    " amps.".format(self.relay_id[relay_id],
                                                    self.relay_name[relay_id],
                                                    current_amps,
                                                    MAX_AMPS))
                return 1

            else:
                if duration:
                    time_now = datetime.datetime.now()
                    if self.is_on(relay_id) and self.relay_on_duration[relay_id]:
                        if self.relay_on_until[relay_id] > time_now:
                            remaining_time = (self.relay_on_until[relay_id]-time_now).seconds
                        else:
                            remaining_time = 0
                        time_on = self.relay_last_duration[relay_id] - remaining_time
                        self.logger.debug("[Relay] Relay {} ({}) is already "
                                            "on for a duration of {:.1f} seconds (with "
                                            "{:.1f} seconds remaining). Recording the "
                                            "amount of time the relay has been on ({:.1f} "
                                            "sec) and updating the on duration to {:.1f} "
                                            "seconds.".format(self.relay_id[relay_id],
                                                              self.relay_name[relay_id],
                                                              self.relay_last_duration[relay_id],
                                                              remaining_time,
                                                              time_on,
                                                              duration))
                        if time_on > 0:
                            duration = float(time_on)
                            timestamp = datetime.datetime.utcnow()-datetime.timedelta(seconds=duration)
                            write_db = threading.Thread(
                                target=write_influxdb_value,
                                args=(self.logger, INFLUXDB_HOST,
                                      INFLUXDB_PORT, INFLUXDB_USER,
                                      INFLUXDB_PASSWORD, INFLUXDB_DATABASE,
                                      'relay', relay_id, 'duration_sec',
                                      duration, timestamp,))
                            write_db.start()

                        self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                        self.relay_last_duration[relay_id] = duration
                        return 0
                    elif self.is_on(relay_id) and not self.relay_on_duration:
                        self.relay_on_duration[relay_id] = True
                        self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                        self.relay_last_duration[relay_id] = duration

                        self.logger.debug("[Relay] Relay {} ({}) is currently"
                                          " on without a duration. Turning "
                                          "into a duration  of {:.1f} "
                                          "seconds.".format(self.relay_id[relay_id],
                                                            self.relay_name[relay_id],
                                                            duration))
                        return 0
                    else:
                        self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                        self.relay_on_duration[relay_id] = True
                        self.relay_last_duration[relay_id] = duration
                        self.logger.debug("[Relay] Relay {} ({}) on for {:.1f} "
                                          "seconds.".format(self.relay_id[relay_id],
                                                             self.relay_name[relay_id],
                                                             duration))
                        GPIO.output(self.relay_pin[relay_id], self.relay_trigger[relay_id])

                else:
                    if self.is_on(relay_id):
                        self.logger.warning("[Relay] Relay {} ({}) is already on.".format(
                                self.relay_id[relay_id],
                                self.relay_name[relay_id]))
                        return 1
                    else:
                        GPIO.output(self.relay_pin[relay_id],
                                    self.relay_trigger[relay_id])

        else:
            if self._is_setup(self.relay_pin[relay_id]) and self.relay_pin[relay_id]:  # if pin not 0
                self.relay_on_duration[relay_id] = False
                self.relay_on_until[relay_id] = datetime.datetime.now()
                GPIO.output(self.relay_pin[relay_id], not self.relay_trigger[relay_id])
                self.logger.debug("[Relay] Relay {} ({}) turned off.".format(
                        self.relay_id[relay_id],
                        self.relay_name[relay_id]))

        if trigger_conditionals:
            self.checkConditionals(relay_id, duration)


    def checkConditionals(self, relay_id, on_duration):
        with session_scope(MYCODO_DB_PATH) as new_session:
            conditionals = new_session.query(RelayConditional)
            new_session.expunge_all()
            new_session.close()

        conditionals = conditionals.filter(RelayConditional.if_relay_id == relay_id)
        conditionals = conditionals.filter(RelayConditional.activated == True)

        if self.is_on(relay_id):
            conditionals = conditionals.filter(RelayConditional.if_action == 'on')
            conditionals = conditionals.filter(RelayConditional.if_duration == on_duration)
        else:
            conditionals = conditionals.filter(RelayConditional.if_action == 'off')

        for each_conditional in conditionals.all():
            message = None
            if (each_conditional.do_relay_id or
                    each_conditional.execute_command or
                    each_conditional.email_notify):
                now = time.time()
                timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H-%M-%S')
                message = "{}\n[Relay Conditional {}] {}\n".format(
                    timestamp, each_conditional.id, each_conditional.name)
                message += "If relay {} ({}) turns {}, Then:\n".format(
                    each_conditional.if_relay_id,
                    self.relay_name[each_conditional.if_relay_id],
                    each_conditional.if_action)

            if each_conditional.do_relay_id:
                message += "Turn relay {} ({}) {}".format(
                        each_conditional.do_relay_id,
                        self.relay_name[each_conditional.do_relay_id],
                        each_conditional.do_action)

                if each_conditional.do_duration == 0:
                    self.relay_on_off(each_conditional.do_relay_id,
                                      each_conditional.do_action)
                else:
                    message += " for {} seconds".format(each_conditional.do_duration)
                    self.relay_on_off(each_conditional.do_relay_id,
                                      each_conditional.do_action,
                                      each_conditional.do_duration)
                message += ".\n"

            if each_conditional.execute_command:
                # Execute command as user mycodo
                message += "Execute: '{}'. ".format(
                    each_conditional.execute_command)
                cmd_out, cmd_err, cmd_status = cmd_output(
                    self.cond_execute_command[cond_id])
                message += "Status: {}. ".format(cmd_status)

            if each_conditional.email_notify:
                if (self.email_count >= self.smtp_max_count and
                        time.time() < self.smtp_wait_time):
                     self.allowed_to_send_notice = False
                else:
                    if time.time() > self.smtp_wait_time:
                        self.email_count = 0
                        self.smtp_wait_time = time.time() + 3600
                    self.allowed_to_send_notice = True
                self.email_count += 1

                if self.allowed_to_send_notice:
                    message += "Notify {}.".format(
                        each_conditional.email_notify)

                    with session_scope(MYCODO_DB_PATH) as new_session:
                        smtp = new_session.query(SMTP).first()
                        send_email(self.logger, smtp.host, smtp.ssl, smtp.port,
                              smtp.user, smtp.passw, smtp.email_from,
                              each_conditional.email_notify, message)
                else:
                    self.logger.debug("[Relay Conditional {}] True: "
                                      "{:.0f} seconds left to be "
                                      "allowed to email again.".format(
                                      each_cond.id,
                                      (self.smtp_wait_time-time.time())))

            if each_conditional.flash_lcd:
                start_flashing = threading.Thread(
                    target=self.control.flash_lcd,
                    args=(each_conditional.flash_lcd,
                          1,))
                start_flashing.start()

            if (each_conditional.do_relay_id or
                    each_conditional.execute_command or
                    each_conditional.email_notify):
                self.logger.debug("{}".format(message))


    def all_relays_initialize(self, relays):
        for each_relay in relays:
            self.relay_id[each_relay.id] = each_relay.id
            self.relay_name[each_relay.id] = each_relay.name
            self.relay_pin[each_relay.id] = each_relay.pin
            self.relay_amps[each_relay.id] = each_relay.amps
            self.relay_trigger[each_relay.id] = each_relay.trigger
            self.relay_start_state[each_relay.id] = each_relay.start_state
            self.relay_on_until[each_relay.id] = datetime.datetime.now()
            self.relay_last_duration[each_relay.id] = 0
            self.relay_on_duration[each_relay.id] = False
            self.setup_pin(each_relay.pin)
            self.logger.debug("[Relay] {} ({}) Initialized".format(each_relay.id, each_relay.name))


    def all_relays_off(self):
        """Turn all relays off"""
        for each_relay_id in self.relay_id:
            self.relay_on_off(each_relay_id, 'off', 0, False)


    def all_relays_on(self):
        """Turn all relays on that are set to be on at startup"""
        for each_relay_id in self.relay_id:
            if self.relay_start_state[each_relay_id]:
                self.relay_on_off(each_relay_id, 'on', 0, False)


    def cleanup_gpio(self):
        for each_relay_pin in self.relay_pin:
            GPIO.cleanup(each_relay_pin)


    def add_mod_relay(self, relay_id, do_setup_pin=False):
        """
        Add or modify local dictionary of relay settings form SQL database

        When a relay is added or modified while the relay controller is
        running, these local variables need to also be modified to
        maintain consistency between the SQL database and running controller.

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        :param do_setup_pin: If True, initialize GPIO (when adding new relay)
        :type do_setup_pin: bool
        """
        try:
            with session_scope(MYCODO_DB_PATH) as new_session:
                relay = new_session.query(Relay).filter(
                    Relay.id == relay_id).first()
                self.relay_id[relay_id] = relay.id
                self.relay_name[relay_id] = relay.name
                self.relay_pin[relay_id] = relay.pin
                self.relay_amps[relay_id] = relay.amps
                self.relay_trigger[relay_id] = relay.trigger
                self.relay_start_state[relay_id] = relay.start_state
                self.relay_on_until[relay_id] = datetime.datetime.now()
                self.relay_last_duration[relay_id] = 0
                self.relay_on_duration[relay_id] = False
                message = "[Relay] Relay {} ({}) ".format(
                    self.relay_id[relay_id], self.relay_name[relay_id])
                if do_setup_pin:
                    self.setup_pin(relay.pin)
                    message += "initiliazed"
                else:
                    message += "added"
                self.logger.debug(message)
            return 0, "success"
        except Exception as msg:
            return 1, "Add_Mod_Relay Error: ID {}: {}".format(relay_id, msg)


    def del_relay(self, relay_id):
        """
        Delete local variables

        The controller local variables must match the SQL database settings.
        Therefore, this is called when a relay has been removed from the SQL
        database.

        :return: 0 for success, 1 for fail (with error message)
        :rtype: int, str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        try:
            self.logger.debug("[Relay] Relay {} ({}) Deleted.".format(
                self.relay_id[relay_id], self.relay_name[relay_id]))
            # Ensure relay is off before removing it, to prevent
            # it from being stuck on
            self.relay_on_off(relay_id, 'off')

            self.relay_id.pop(relay_id, None)
            self.relay_name.pop(relay_id, None)
            self.relay_pin.pop(relay_id, None)
            self.relay_amps.pop(relay_id, None)
            self.relay_trigger.pop(relay_id, None)
            self.relay_start_state.pop(relay_id, None)
            self.relay_on_until.pop(relay_id, None)
            self.relay_last_duration.pop(relay_id, None)
            self.relay_on_duration.pop(relay_id, None)
            return 0, "success"
        except Exception as msg:
            return 1, "Del_Relay Error: ID {}: {}".format(relay_id, msg)


    def current_amp_load(self):
        """
        Calculate the current amp draw from all the devices connected to
        all relays currently on.

        :return: total amerage draw
        :rtype: float
        """
        amp_load = 0.0
        for each_relay_id, each_relay_amps in self.relay_amps.iteritems():
            if self.is_on(each_relay_id):
                amp_load += each_relay_amps
        return amp_load


    def setup_pin(self, pin):
        """
        Setup pin for this relay
        :rtype: None
        """
        # Setup GPIO (BCM numbering) and initialize relay pin as output
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(pin, GPIO.OUT)


    def relay_state(self, relay_id):
        """
        :return: Whether the relay is currently "ON"
        :rtype: str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        if self.relay_trigger[relay_id] == GPIO.input(self.relay_pin[relay_id]):
            return 'on'
        else:
            return 'off'


    def is_on(self, relay_id):
        """
        :return: Whether the relay is currently "ON"
        :rtype: bool

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        return self.relay_trigger[relay_id] == GPIO.input(self.relay_pin[relay_id])


    def _is_setup(self, pin):
        """
        This function checks to see if the GPIO pin is setup and ready
        to use. This is for safety and to make sure we don't blow anything.

        # TODO Make it do that.

        :return: Is it safe to manipulate this relay?
        :rtype: bool
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        return True


    def isRunning(self):
        return self.running


    def stopController(self):
        """Signal to stop the controller"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False
