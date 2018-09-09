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

from mycodo.config import LIST_DEVICES_ADC
from mycodo.config import LIST_DEVICES_I2C
from mycodo.databases.models import Conditional
from mycodo.databases.models import Input
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import SMTP
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measure_influxdb
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
            "mycodo.input_{id}".format(id=input_id.split('-')[0]))

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

        self.input_dev = input_dev
        self.input_name = input_dev.name
        self.unique_id = input_dev.unique_id
        self.i2c_bus = input_dev.i2c_bus
        self.location = input_dev.location
        self.power_output_id = input_dev.power_output_id
        self.measurements = input_dev.measurements
        self.convert_to_unit = input_dev.convert_to_unit
        self.device = input_dev.device
        self.interface = input_dev.interface
        self.device_loc = input_dev.device_loc
        self.baud_rate = input_dev.baud_rate
        self.period = input_dev.period
        self.resolution = input_dev.resolution
        self.sensitivity = input_dev.sensitivity
        self.cmd_command = input_dev.cmd_command
        self.thermocouple_type = input_dev.thermocouple_type
        self.ref_ohm = input_dev.ref_ohm

        # Serial
        self.pin_clock = input_dev.pin_clock
        self.pin_cs = input_dev.pin_cs
        self.pin_mosi = input_dev.pin_mosi
        self.pin_miso = input_dev.pin_miso

        # ADC
        self.adc_measure = input_dev.convert_to_unit.split(',')[0]
        self.adc_volts_min = input_dev.adc_volts_min
        self.adc_volts_max = input_dev.adc_volts_max
        self.adc_units_min = input_dev.adc_units_min
        self.adc_units_max = input_dev.adc_units_max
        self.adc_inverse_unit_scale = input_dev.adc_inverse_unit_scale

        # Edge detection
        self.switch_edge = input_dev.switch_edge
        self.switch_bouncetime = input_dev.switch_bouncetime
        self.switch_reset_period = input_dev.switch_reset_period

        # PWM and RPM options
        self.weighting = input_dev.weighting
        self.rpm_pulses_per_rev = input_dev.rpm_pulses_per_rev
        self.sample_time = input_dev.sample_time

        # Server options
        self.port = input_dev.port
        self.times_check = input_dev.times_check
        self.deadline = input_dev.deadline

        # Output that will activate prior to input read
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
            if each_output.unique_id == self.pre_output_id and self.pre_output_duration:
                self.pre_output_setup = True

        smtp = db_retrieve_table_daemon(SMTP, entry='first')
        self.smtp_max_count = smtp.hourly_max
        self.email_count = 0
        self.allowed_to_send_notice = True

        # Set up input lock
        self.input_lock = None
        self.lock_file = '/var/lock/input_pre_output_{id}'.format(id=self.pre_output_id)

        # Convert string I2C address to base-16 int
        if self.device in LIST_DEVICES_I2C:
            self.i2c_address = int(str(self.location), 16)

        # Set up edge detection of a GPIO pin
        if self.device == 'EDGE':
            if self.switch_edge == 'rising':
                self.switch_edge_gpio = GPIO.RISING
            elif self.switch_edge == 'falling':
                self.switch_edge_gpio = GPIO.FALLING
            else:
                self.switch_edge_gpio = GPIO.BOTH

        # Set up analog-to-digital converter
        if self.device in LIST_DEVICES_ADC:
            if self.device in ['ADS1x15', 'MCP342x']:
                self.adc_lock_file = "/var/lock/mycodo_adc_bus{bus}_0x{i2c:02X}.pid".format(
                    bus=self.i2c_bus, i2c=self.i2c_address)
            elif self.device == 'MCP3008':
                self.adc_lock_file = "/var/lock/mycodo_adc_uart-{clock}-{cs}-{miso}-{mosi}".format(
                    clock=self.pin_clock, cs=self.pin_cs, miso=self.pin_miso, mosi=self.pin_mosi)

            if self.device == 'ADS1x15' and self.location:
                from mycodo.devices.ads1x15 import ADS1x15Read
                self.adc = ADS1x15Read(self.input_dev)
            elif self.device == 'MCP3008':
                from mycodo.devices.mcp3008 import MCP3008Read
                self.adc = MCP3008Read(self.input_dev)
            elif self.device == 'MCP342x' and self.location:
                from mycodo.devices.mcp342x import MCP342xRead
                self.adc = MCP342xRead(self.input_dev)
        else:
            self.adc = None

        self.device_recognized = True

        # Set up inputs or devices
        if self.device in ['EDGE'] + LIST_DEVICES_ADC:
            self.measure_input = None

        else:
            if self.device in self.dict_inputs:
                input_loaded = load_module_from_file(self.dict_inputs[self.device]['file_path'])
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

    def run(self):
        try:
            self.running = True
            self.logger.info("Activated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_startup_timer) * 1000))
            self.ready.set()

            # Set up edge detection
            if self.device == 'EDGE':
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(int(self.location), GPIO.IN)
                GPIO.add_event_detect(int(self.location),
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

                        # Set up lock
                        self.input_lock = locket.lock_file(self.lock_file, timeout=120)
                        try:
                            self.input_lock.acquire()
                            self.pre_output_locked = True
                        except locket.LockError:
                            self.logger.error("Could not acquire input lock. Breaking for future locking.")
                            try:
                                os.remove(self.lock_file)
                            except OSError:
                                self.logger.error("Can't delete lock file: Lock file doesn't exist.")

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

                            # release pre-output lock
                            try:
                                if self.pre_output_locked:
                                    self.input_lock.release()
                                    self.pre_output_locked = False
                            except AttributeError:
                                self.logger.error("Can't release lock: "
                                                  "Lock file not present.")

                        elif not self.pre_output_setup:
                            # Pre-output not enabled, just measure
                            self.update_measure()
                            self.get_new_measurement = False

                        # Add measurement(s) to influxdb
                        if self.measurement_success:
                            add_measure_influxdb(self.unique_id, self.measurement)
                            self.measurement_success = False

                self.trigger_cond = False

                time.sleep(self.sample_rate)

            self.running = False

            if self.device == 'EDGE':
                GPIO.setmode(GPIO.BCM)
                GPIO.cleanup(int(self.location))

            self.logger.info("Deactivated in {:.1f} ms".format(
                (timeit.default_timer() - self.thread_shutdown_timer) * 1000))
        except requests.ConnectionError:
            self.logger.error("Could not connect to influxdb. Check that it "
                              "is running and accepting connections")
        except Exception as except_msg:
            self.logger.exception("Error: {err}".format(
                err=except_msg))

    def read_adc(self):
        """ Read voltage from ADC """
        try:
            lock_acquired = False

            # Set up lock for ADC
            adc_lock = locket.lock_file(self.adc_lock_file, timeout=120)
            try:
                adc_lock.acquire()
                lock_acquired = True
            except:
                self.logger.error("Could not acquire ADC lock. Breaking for future locking.")
                os.remove(self.adc_lock_file)

            if not lock_acquired:
                self.logger.error(
                    "Unable to acquire lock: {lock}".format(
                        lock=self.adc_lock_file))

            # Get measurement from ADC
            measurements = self.adc.next()

            if measurements is not None:
                # Get the voltage difference between min and max volts
                diff_voltage = abs(self.adc_volts_max - self.adc_volts_min)

                # Ensure the voltage stays within the min/max bounds
                if measurements['voltage'] < self.adc_volts_min:
                    measured_voltage = self.adc_volts_min
                elif measurements['voltage'] > self.adc_volts_max:
                    measured_voltage = self.adc_volts_max
                else:
                    measured_voltage = measurements['voltage']

                # Calculate the percentage of the voltage difference
                percent_diff = ((measured_voltage - self.adc_volts_min) /
                                diff_voltage)

                # Get the units difference between min and max units
                diff_units = abs(self.adc_units_max - self.adc_units_min)

                # Calculate the measured units from the percent difference
                if self.adc_inverse_unit_scale:
                    converted_units = (self.adc_units_max -
                                       (diff_units * percent_diff))
                else:
                    converted_units = (self.adc_units_min +
                                       (diff_units * percent_diff))

                # Ensure the units stay within the min/max bounds
                if converted_units < self.adc_units_min:
                    measurements[self.adc_measure] = self.adc_units_min
                elif converted_units > self.adc_units_max:
                    measurements[self.adc_measure] = self.adc_units_max
                else:
                    measurements[self.adc_measure] = converted_units

                if adc_lock and lock_acquired:
                    adc_lock.release()

                return measurements

        except Exception as except_msg:
            self.logger.exception(
                "Error while attempting to read adc: {err}".format(
                    err=except_msg))

        return None

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

        if self.adc:
            measurements = self.read_adc()
        else:
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
        gpio_state = GPIO.input(int(self.location))
        if time.time() > self.edge_reset_timer:
            self.edge_reset_timer = time.time()+self.switch_reset_period

            if (self.switch_edge == 'rising' or
                    (self.switch_edge == 'both' and gpio_state)):
                rising_or_falling = 1  # Rising edge detected
                state_str = 'Rising'
                conditional_edge = 1
            else:
                rising_or_falling = -1  # Falling edge detected
                state_str = 'Falling'
                conditional_edge = 0

            write_db = threading.Thread(
                target=write_influxdb_value,
                args=(self.unique_id, 'edge', rising_or_falling,))
            write_db.start()

            conditionals = db_retrieve_table_daemon(Conditional)
            conditionals = conditionals.filter(
                Conditional.conditional_type == 'conditional_edge')
            conditionals = conditionals.filter(
                Conditional.measurement == self.unique_id)
            conditionals = conditionals.filter(
                Conditional.is_activated == True)

            for each_conditional in conditionals.all():
                if each_conditional.edge_detected in ['both', state_str.lower()]:
                    now = time.time()
                    timestamp = datetime.datetime.fromtimestamp(
                        now).strftime('%Y-%m-%d %H-%M-%S')
                    message = "{ts}\n[Conditional {cid} ({cname})] " \
                              "Input {oid} ({name}) {state} edge detected " \
                              "on pin {pin} (BCM)".format(
                                    ts=timestamp,
                                    cid=each_conditional.id,
                                    cname=each_conditional.name,
                                    oid=self.input_id,
                                    name=self.input_name,
                                    state=state_str,
                                    pin=bcm_pin)

                    self.control.trigger_conditional_actions(
                        each_conditional.unique_id, message=message,
                        edge=conditional_edge)

    def is_running(self):
        return self.running

    def stop_controller(self):
        self.thread_shutdown_timer = timeit.default_timer()
        if self.device not in ['EDGE'] + LIST_DEVICES_ADC:
            self.measure_input.stop_sensor()

        # Ensure pre-output is off
        if self.pre_output_setup:
            output_on = threading.Thread(
                target=self.control.output_off,
                args=(self.pre_output_id,))
            output_on.start()

        self.running = False
