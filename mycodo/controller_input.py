# coding=utf-8
#
# controller_input.py - Input controller that manages reading inputs and
#                       creating database entries
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
import logging
import threading
import time
import timeit

import RPi.GPIO as GPIO
import locket
import os
import requests

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import SMTP
from mycodo.databases.models import Trigger
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import parse_measurement
from mycodo.utils.influx import write_influxdb_value
from mycodo.utils.inputs import load_module_from_file
from mycodo.utils.inputs import parse_input_information


class Measurement:
    """
    Class for holding all measurement values in a dictionary.
    The dictionary is formatted in the following way:

    {'measurement type':measurement value}

    Measurement type: The environmental or physical condition
    being measured, such as 'temperature', or 'pressure'.

    Measurement value: The actual measurement of the condition.
    """

    def __init__(self, raw_data):
        self.rawData = raw_data

    @property
    def values(self):
        return self.rawData


class InputController(threading.Thread):
    """
    Class for controlling the input

    """
    def __init__(self, ready, input_id):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger(
            "{}_{}".format(__name__, input_id.split('-')[0]))

        self.stop_iteration_counter = 0
        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.ready = ready
        self.lock = {}
        self.measurement = None
        self.measurement_success = False
        self.control = DaemonControl()
        self.pause_loop = False
        self.verify_pause_loop = True

        self.dict_inputs = parse_input_information()

        self.sample_rate = db_retrieve_table_daemon(
            Misc, entry='first').sample_rate_controller_input

        self.input_id = input_id
        input_dev = db_retrieve_table_daemon(
            Input, unique_id=self.input_id)

        if input_dev.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        self.device_measurements = db_retrieve_table_daemon(
            DeviceMeasurements).filter(
                DeviceMeasurements.device_id == self.input_id)

        self.conversions = db_retrieve_table_daemon(Conversion)

        self.input_dev = input_dev
        self.input_name = input_dev.name
        self.unique_id = input_dev.unique_id
        self.gpio_location = input_dev.gpio_location
        self.device = input_dev.device
        self.interface = input_dev.interface
        self.period = input_dev.period

        # Edge detection
        self.switch_edge = input_dev.switch_edge
        self.switch_bouncetime = input_dev.switch_bouncetime
        self.switch_reset_period = input_dev.switch_reset_period

        # Pre-Output: Activates prior to input measurement
        self.pre_output_id = input_dev.pre_output_id
        self.pre_output_duration = input_dev.pre_output_duration
        self.pre_output_during_measure = input_dev.pre_output_during_measure
        self.pre_output_setup = False
        self.next_measurement = time.time()
        self.get_new_measurement = False
        self.trigger_cond = False
        self.measurement_acquired = False
        self.pre_output_activated = False
        self.pre_output_locked = False
        self.pre_output_timer = time.time()

        # Check if Pre-Output ID actually exists
        output = db_retrieve_table_daemon(Output, entry='all')
        for each_output in output:
            if (each_output.unique_id == self.pre_output_id and
                    self.pre_output_duration):
                self.pre_output_setup = True

        smtp = db_retrieve_table_daemon(SMTP, entry='first')
        self.smtp_max_count = smtp.hourly_max
        self.email_count = 0
        self.allowed_to_send_notice = True

        # Set up input lock
        self.input_lock = None
        self.lock_file = '/var/lock/input_pre_output_{id}'.format(
            id=self.pre_output_id)

        # Convert string I2C address to base-16 int
        if self.interface == 'I2C':
            self.i2c_address = int(str(self.input_dev.i2c_location), 16)

        # Set up edge detection of a GPIO pin
        if self.device == 'EDGE':
            if self.switch_edge == 'rising':
                self.switch_edge_gpio = GPIO.RISING
            elif self.switch_edge == 'falling':
                self.switch_edge_gpio = GPIO.FALLING
            else:
                self.switch_edge_gpio = GPIO.BOTH

        self.device_recognized = True

        if self.device in self.dict_inputs:
            input_loaded = load_module_from_file(
                self.dict_inputs[self.device]['file_path'])

            if self.device == 'EDGE':
                # Edge detection handled internally, no module to load
                self.measure_input = None
            else:
                self.measure_input = input_loaded.InputModule(self.input_dev)

        else:
            self.device_recognized = False
            self.logger.debug("Device '{device}' not recognized".format(
                device=self.device))
            raise Exception("'{device}' is not a valid device type.".format(
                device=self.device))

        self.edge_reset_timer = time.time()
        self.input_timer = time.time()
        self.running = False
        self.lastUpdate = None

    def __str__(self):
        return str(self.__class__)

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            # Set up edge detection
            if self.device == 'EDGE':
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(int(self.gpio_location), GPIO.IN)
                GPIO.add_event_detect(int(self.gpio_location),
                                      self.switch_edge_gpio,
                                      callback=self.edge_detected,
                                      bouncetime=self.switch_bouncetime)

            while self.running:
                # Pause loop to modify conditional statements.
                # Prevents execution of conditional while variables are
                # being modified.
                if self.pause_loop:
                    self.verify_pause_loop = True
                    while self.pause_loop:
                        time.sleep(0.1)

                if self.device not in ['EDGE']:
                    now = time.time()
                    # Signal that a measurement needs to be obtained
                    if now > self.next_measurement and not self.get_new_measurement:
                        self.get_new_measurement = True
                        self.trigger_cond = True
                        while self.next_measurement < now:
                            self.next_measurement += self.period

                    # if signaled and a pre output is set up correctly, turn the
                    # output on or on for the set duration
                    if (self.get_new_measurement and
                            self.pre_output_setup and
                            not self.pre_output_activated):

                        self.lock_setup()

                        self.pre_output_timer = time.time() + self.pre_output_duration
                        self.pre_output_activated = True

                        # Only run the pre-output before measurement
                        # Turn on for a duration, measure after it turns off
                        if not self.pre_output_during_measure:
                            output_on = threading.Thread(
                                target=self.control.output_on,
                                args=(self.pre_output_id,
                                      self.pre_output_duration,))
                            output_on.start()

                        # Run the pre-output during the measurement
                        # Just turn on, then off after the measurement
                        else:
                            output_on = threading.Thread(
                                target=self.control.output_on,
                                args=(self.pre_output_id,))
                            output_on.start()

                    # If using a pre output, wait for it to complete before
                    # querying the input for a measurement
                    if self.get_new_measurement:

                        if (self.pre_output_setup and
                                self.pre_output_activated and
                                now > self.pre_output_timer):

                            if self.pre_output_during_measure:
                                # Measure then turn off pre-output
                                self.update_measure()
                                output_off = threading.Thread(
                                    target=self.control.output_off,
                                    args=(self.pre_output_id,))
                                output_off.start()
                            else:
                                # Pre-output has turned off, now measure
                                self.update_measure()

                            self.pre_output_activated = False
                            self.get_new_measurement = False

                            self.lock_release()

                        elif not self.pre_output_setup:
                            # Pre-output not enabled, just measure
                            self.update_measure()
                            self.get_new_measurement = False

                        # Add measurement(s) to influxdb
                        if self.measurement_success:
                            use_same_timestamp = True
                            if ('measurements_use_same_timestamp' in self.dict_inputs[self.device] and
                                    not self.dict_inputs[self.device]['measurements_use_same_timestamp']):
                                use_same_timestamp = False
                            add_measurements_influxdb(
                                self.unique_id,
                                self.create_measurements_dict(),
                                use_same_timestamp=use_same_timestamp)
                            self.measurement_success = False

                self.trigger_cond = False

                time.sleep(self.sample_rate)

            self.running = False

            if self.device == 'EDGE':
                GPIO.setmode(GPIO.BCM)
                GPIO.cleanup(int(self.gpio_location))

            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except requests.ConnectionError:
            self.logger.error("Could not connect to influxdb. Check that it "
                              "is running and accepting connections")
        except Exception as except_msg:
            self.logger.exception("Error: {err}".format(
                err=except_msg))

    def lock_setup(self):
        # Set up lock
        self.input_lock = locket.lock_file(self.lock_file, timeout=30)
        try:
            self.input_lock.acquire()
            self.pre_output_locked = True
        except locket.LockError:
            self.logger.error("Could not acquire input lock. Breaking for future locking.")
            try:
                os.remove(self.lock_file)
            except OSError:
                self.logger.error("Can't delete lock file: Lock file doesn't exist.")

    def lock_release(self):
        # release pre-output lock
        try:
            if self.pre_output_locked:
                self.input_lock.release()
                self.pre_output_locked = False
        except AttributeError:
            self.logger.error("Can't release lock: "
                              "Lock file not present.")

    def update_measure(self):
        """
        Retrieve measurement from input

        :return: None if success, 0 if fail
        :rtype: int or None
        """
        measurements = None

        if not self.device_recognized:
            self.logger.debug("Device not recognized: {device}".format(
                device=self.device))
            self.measurement_success = False
            return 1

        try:
            # Get measurement from input
            measurements = self.measure_input.next()
            # Reset StopIteration counter on successful read
            if self.stop_iteration_counter:
                self.stop_iteration_counter = 0
        except StopIteration:
            self.stop_iteration_counter += 1
            # Notify after 3 consecutive errors. Prevents filling log
            # with many one-off errors over long periods of time
            if self.stop_iteration_counter > 2:
                self.stop_iteration_counter = 0
                self.logger.error(
                    "StopIteration raised. Possibly could not read "
                    "input. Ensure it's connected properly and "
                    "detected.")
        except Exception as except_msg:
            self.logger.exception(
                "Error while attempting to read input: {err}".format(
                    err=except_msg))

        if self.device_recognized and measurements is not None:
            self.measurement = Measurement(measurements)
            self.measurement_success = True
        else:
            self.measurement_success = False

        self.lastUpdate = time.time()

    def edge_detected(self, bcm_pin):
        """
        Callback function from GPIO.add_event_detect() for when an edge is detected

        Write rising (1) or falling (-1) edge to influxdb database
        Trigger any conditionals that match the rising/falling/both edge

        :param bcm_pin: BMC pin of rising/falling edge (required parameter)
        :return: None
        """
        gpio_state = GPIO.input(int(self.gpio_location))
        if time.time() > self.edge_reset_timer:
            self.edge_reset_timer = time.time()+self.switch_reset_period

            if (self.switch_edge == 'rising' or
                    (self.switch_edge == 'both' and gpio_state)):
                rising_or_falling = 1  # Rising edge detected
                state_str = 'Rising'
            else:
                rising_or_falling = -1  # Falling edge detected
                state_str = 'Falling'

            write_db = threading.Thread(
                target=write_influxdb_value,
                args=(self.unique_id, 'edge', rising_or_falling,))
            write_db.start()

            trigger = db_retrieve_table_daemon(Trigger)
            trigger = trigger.filter(
                Trigger.trigger_type == 'trigger_edge')
            trigger = trigger.filter(
                Trigger.measurement == self.unique_id)
            trigger = trigger.filter(
                Trigger.is_activated == True)

            for each_trigger in trigger.all():
                if each_trigger.edge_detected in ['both', state_str.lower()]:
                    now = time.time()
                    timestamp = datetime.datetime.fromtimestamp(
                        now).strftime('%Y-%m-%d %H-%M-%S')
                    message = "{ts}\n[Trigger {cid} ({cname})] " \
                              "Input {oid} ({name}) {state} edge detected " \
                              "on pin {pin} (BCM)".format(
                                    ts=timestamp,
                                    cid=each_trigger.id,
                                    cname=each_trigger.name,
                                    oid=self.input_id,
                                    name=self.input_name,
                                    state=state_str,
                                    pin=bcm_pin)
                    self.logger.debug("Edge: {}".format(message))

                    self.control.trigger_all_actions(
                        each_trigger.unique_id, message=message)

    def create_measurements_dict(self):
        measurements_record = {}
        for each_channel, each_measurement in self.measurement.values.items():
            measurement = self.device_measurements.filter(
                DeviceMeasurements.channel == each_channel).first()

            if 'value' in each_measurement:
                conversion = self.conversions.filter(
                    Conversion.unique_id == measurement.conversion_id).first()

                measurements_record = parse_measurement(
                    conversion,
                    measurement,
                    measurements_record,
                    each_channel,
                    each_measurement)
        self.logger.debug(
            "Adding measurements to InfluxDB with ID {}: {}".format(
                self.input_id, measurements_record))
        return measurements_record

    def force_measurements(self):
        # Signal that a measurement needs to be obtained
        self.next_measurement = time.time()
        return "Input instructed to begin acquiring measurements"

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()

        # Execute stop_sensor() if not EDGE or ADC
        if self.device != 'EDGE':
            self.measure_input.stop_sensor()

        # Ensure pre-output is off
        if self.pre_output_setup:
            output_on = threading.Thread(
                target=self.control.output_off,
                args=(self.pre_output_id,))
            output_on.start()

        self.running = False
