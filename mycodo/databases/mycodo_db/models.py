#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  update-database.py - Create and update Mycodo SQLite databases
#
#  Copyright (C) 2015  Kyle T. Gabriel
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

from sqlalchemy import Column, TEXT, INT, REAL, DATETIME, BOOLEAN, String
from sqlalchemy.ext.declarative import declarative_base
import RPi.GPIO as GPIO
import datetime


Base = declarative_base()


# TODO Build a BaseConditional that all the conditionals inherit from

class AlembicVersion(Base):
    __tablename__ = "alembic_version"
    version_num = Column(String(32), primary_key=True, nullable=False)


class Method(Base):
    __tablename__ = "method"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    method_id = Column(TEXT)
    method_type = Column(TEXT)
    method_order = Column(INT)
    start_time = Column(TEXT)
    end_time = Column(TEXT)
    duration_sec = Column(INT)
    relay_id = Column(TEXT)
    relay_state = Column(TEXT)
    relay_duration = Column(REAL)
    start_setpoint = Column(REAL)
    end_setpoint = Column(REAL)


class Relay(Base):
    __tablename__ = "relays"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pin = Column(INT)
    amps = Column(REAL)
    trigger = Column(INT)
    start_state = Column(INT)
    on_until = Column(DATETIME)
    last_duration = Column(REAL)
    on_duration = Column(BOOLEAN)

    def _is_setup(self):
        """
        This function checks to see if the GPIO pin is setup and ready to use.  This is for safety
        and to make sure we don't blow anything.

        # TODO Make it do that.

        :return: Is it safe to manipulate this relay?
        :rtype: bool
        """
        return True

    def setup_pin(self):
        """
        Setup pin for this relay

        :rtype: None
        """
        # TODO add some extra checks here.  Maybe verify BCM?
        GPIO.setup(self.pin, GPIO.OUT)

    def turn_off(self):
        """
        Turn this relay off

        :rtype: None
        """
        if self._is_setup():
            self.on_duration = False
            self.on_until = datetime.datetime.now()
            GPIO.output(self.pin, not self.trigger)

    def turn_on(self):
        """
        Turn this relay on

        :rtype: None
        """
        if self._is_setup():
            GPIO.output(self.pin, self.trigger)

    def is_on(self):
        """
        :return: Whether the relay is currently "ON"
        :rtype: bool
        """
        return self.trigger == GPIO.input(self.pin)


class RelayConditional(Base):
    __tablename__ = "relayconditional"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    activated = Column(BOOLEAN)
    if_relay_id = Column(TEXT)
    if_action = Column(TEXT)
    if_duration = Column(REAL)
    do_relay_id = Column(TEXT)
    do_action = Column(TEXT)
    do_duration = Column(REAL)
    execute_command = Column(TEXT)
    email_notify = Column(TEXT)
    flash_lcd = Column(TEXT)


class Sensor(Base):
    __tablename__ = "sensor"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    activated = Column(INT)
    device = Column(TEXT) 
    device_type = Column(TEXT)
    i2c_bus = Column(INT)
    location = Column(TEXT)
    multiplexer_address = Column(TEXT)
    multiplexer_bus = Column(INT)
    multiplexer_channel = Column(INT)
    adc_channel = Column(INT)
    adc_gain = Column(INT)
    adc_resolution = Column(INT)
    adc_measure = Column(TEXT)
    adc_measure_units = Column(TEXT)
    adc_volts_min = Column(REAL)
    adc_volts_max = Column(REAL)
    adc_units_min = Column(REAL)
    adc_units_max = Column(REAL)
    switch_edge = Column(TEXT)
    switch_bouncetime = Column(INT)
    switch_reset_period = Column(INT)
    pre_relay_id = Column(TEXT)
    pre_relay_duration = Column(REAL)
    graph = Column(INT)
    period = Column(INT)
    sht_clock_pin = Column(INT)
    sht_voltage = Column(REAL)

    def is_activated(self):
        """
        :return: Whether the sensor is currently activated
        :rtype: bool
        """
        return self.activated


class SensorPreset(Base):
    __tablename__ = "sensorpreset"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    device = Column(TEXT) 
    device_type = Column(TEXT)
    location = Column(TEXT)
    multiplex = Column(TEXT)
    pre_relay_id = Column(TEXT)
    pre_period = Column(INT)
    graph = Column(INT)
    period = Column(INT)
    sht_clock_pin = Column(INT)
    sht_voltage = Column(REAL)


class SensorConditional(Base):
    __tablename__ = "sensorconditional"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    activated = Column(INT)
    sensor_id = Column(TEXT)
    period = Column(INT)
    measurement_type = Column(TEXT)
    edge_detected = Column(TEXT)
    direction = Column(TEXT) # 'above' or 'below' setpoint
    setpoint = Column(REAL)
    relay_id = Column(TEXT)
    relay_state = Column(TEXT) # 'on' or 'off'
    relay_on_duration = Column(REAL)
    execute_command = Column(TEXT)
    email_notify = Column(TEXT)
    flash_lcd = Column(TEXT)
    camera_record = Column(TEXT)


class PID(Base):
    __tablename__ = "pid"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    activated = Column(INT)
    sensor_id = Column(TEXT)
    measure_type = Column(TEXT)
    direction = Column(TEXT)
    period = Column(INT)
    setpoint = Column(REAL)
    method_id = Column(TEXT)
    p = Column(REAL)
    i = Column(REAL)
    d = Column(REAL)
    raise_relay_id = Column(TEXT)
    raise_min_duration = Column(INT)
    raise_max_duration = Column(INT)
    lower_relay_id = Column(TEXT)
    lower_min_duration = Column(INT)
    lower_max_duration = Column(INT)


class PIDPreset(Base):
    __tablename__ = "pidpreset"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    sensor_id = Column(TEXT)
    measure_type = Column(TEXT)
    direction = Column(TEXT)
    period = Column(INT)
    setpoint = Column(REAL)
    p = Column(REAL)
    i = Column(REAL)
    d = Column(REAL)
    raise_relay_id = Column(TEXT)
    raise_min_duration = Column(INT)
    raise_max_duration = Column(INT)
    lower_relay_id = Column(TEXT)
    lower_min_duration = Column(INT)
    lower_max_duration = Column(INT)


class PIDConditional(Base):
    """
    PID conditionals


    Every PID period, perform math on the PID input (sensor measurement), then
    activate relay_id for a duration of time based on the PID output.

    This is early conception. Future support for PWM, stepper motor, or other output.

    """
    __tablename__ = 'pidconditional'

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    activated = Column(INT)
    pid_id = Column(TEXT)
    relay_id = Column(TEXT)
    relay_math = Column(TEXT)
    relay_on_duration = Column(INT)
    command = Column(TEXT)
    notify = Column(TEXT)


class Graph(Base):
    __tablename__ = "graph"
    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    pid_ids = Column(TEXT)
    relay_ids = Column(TEXT)
    sensor_ids = Column(TEXT)
    width = Column(INT)
    height = Column(INT)
    x_axis_duration = Column(INT)
    refresh_duration = Column(INT)
    enable_navbar = Column(BOOLEAN)
    enable_rangeselect = Column(BOOLEAN)
    enable_export = Column(BOOLEAN)


class DisplayOrder(Base):
    __tablename__ = "displayorder"

    id = Column(TEXT, unique=True, primary_key=True)
    graph = Column(TEXT)
    lcd = Column(TEXT)
    log = Column(TEXT)
    pid = Column(TEXT)
    relay = Column(TEXT)
    remote_host = Column(TEXT)
    sensor = Column(TEXT)
    timer = Column(TEXT)


class LCD(Base):
    __tablename__ = "lcd"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    activated = Column(INT)
    pin = Column(TEXT)
    multiplexer_address = Column(TEXT)
    multiplexer_channel = Column(INT)
    period = Column(INT)
    x_characters = Column(INT)
    y_lines = Column(INT)
    line_1_sensor_id = Column(TEXT)
    line_1_measurement = Column(TEXT)
    line_2_sensor_id = Column(TEXT)
    line_2_measurement = Column(TEXT)
    line_3_sensor_id = Column(TEXT)
    line_3_measurement = Column(TEXT)
    line_4_sensor_id = Column(TEXT)
    line_4_measurement = Column(TEXT)


class Log(Base):
    __tablename__ = "log"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    sensor_id = Column(TEXT)
    measure_type = Column(TEXT)
    activated = Column(INT)
    period = Column(INT)


class Timer(Base):
    __tablename__ = "timer"

    id = Column(TEXT, unique=True, primary_key=True)
    name = Column(TEXT)
    activated = Column(INT)
    relay_id = Column(TEXT)
    state = Column(TEXT) # 'on' or 'off'
    time_on = Column(TEXT)
    duration_on = Column(REAL)
    duration_off = Column(REAL)


class SMTP(Base):
    __tablename__ = "smtp"

    id = Column(TEXT, unique=True, primary_key=True)
    host = Column(TEXT)
    ssl = Column(INT)
    port = Column(INT)
    user = Column(TEXT)
    passw = Column(TEXT)
    email_from = Column(TEXT)
    hourly_max = Column(INT)


class CameraStill(Base):
    __tablename__ = "camerastill"

    id = Column(TEXT, unique=True, primary_key=True)
    relay_id = Column(TEXT)
    timestamp = Column(INT)
    display_last = Column(INT)
    cmd_pre_camera = Column(TEXT)
    cmd_post_camera = Column(TEXT)
    extra_parameters = Column(TEXT)


class CameraStream(Base):
    __tablename__ = "camerastream"

    id = Column(TEXT, unique=True, primary_key=True)
    relay_id = Column(TEXT)
    cmd_pre_camera = Column(TEXT)
    cmd_post_camera = Column(TEXT)
    extra_parameters = Column(TEXT)


class CameraTimelapse(Base):
    __tablename__ = "cameratimelapse"

    id = Column(TEXT, unique=True, primary_key=True)
    relay_id = Column(TEXT)
    path = Column(TEXT)
    prefix = Column(TEXT)
    file_timestamp = Column(INT)
    display_last = Column(INT)
    cmd_pre_camera = Column(TEXT)
    cmd_post_camera = Column(TEXT)
    extra_parameters = Column(TEXT)


class Misc(Base):
    __tablename__ = "misc"

    id = Column(TEXT, unique=True, primary_key=True)
    force_https = Column(BOOLEAN)
    dismiss_notification = Column(INT)
    hide_alert_success = Column(BOOLEAN)
    hide_alert_info = Column(BOOLEAN)
    hide_alert_warning = Column(BOOLEAN)
    stats_opt_out = Column(BOOLEAN)
    login_message = Column(TEXT)
    relay_stats_volts = Column(INT)
    relay_stats_cost = Column(REAL)
    relay_stats_currency = Column(TEXT)
    relay_stats_dayofmonth = Column(INT)

class Remote(Base):
    __tablename__ = "remote"

    id = Column(TEXT, unique=True, primary_key=True)
    activated = Column(INT)
    host = Column(TEXT)
    username = Column(TEXT)
    password_hash = Column(TEXT)
