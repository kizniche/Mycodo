#!/usr/bin/python
# -*- coding: utf-8 -*-
import bcrypt
import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    VARCHAR
)
from sqlalchemy.ext.declarative import declarative_base
from RPi import GPIO

Base = declarative_base()


# TODO Build a BaseConditional that all the conditionals inherit from

class AlembicVersion(Base):
    __tablename__ = "alembic_version"
    version_num = Column(String(32), primary_key=True, nullable=False)


#
# User Table
#

class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(VARCHAR(64), unique=True, index=True)
    user_password_hash = Column(VARCHAR(255))
    user_email = Column(VARCHAR(64), unique=True, index=True)
    user_restriction = Column(VARCHAR(64))
    user_theme = Column(VARCHAR(64))

    def __repr__(self):
        output = "<User: <name='{name}', email='{email}' is_admin='{isadmin}'>"
        return output.format(name=self.user_name,
                             email=self.user_email,
                             isadmin=bool(self.user_restriction == 'admin'))

    def set_password(self, new_password):
        self.user_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def check_password(password, hashed_password):
        hashes_match = bcrypt.hashpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        return hashes_match


#
# Mycodo settings tables
#

class CameraStill(Base):
    __tablename__ = "camerastill"

    id = Column(Integer, unique=True, primary_key=True)
    relay_id = Column(Text, ForeignKey('relay.id'))  # Relay to turn on while capturing
    hflip = Column(Boolean)  # Horizontal flip image
    vflip = Column(Boolean)  # Vertical flip image
    rotation = Column(Integer)  # Rotation degree (0-360)
    cmd_pre_camera = Column(Text)  # Command to execute before capture
    cmd_post_camera = Column(Text)  # Command to execute after capture


class CameraStream(Base):
    __tablename__ = "camerastream"

    id = Column(Integer, unique=True, primary_key=True)
    relay_id = Column(Text, ForeignKey('relay.id'))  # Relay to turn on while capturing
    hflip = Column(Boolean)  # Horizontal flip image
    vflip = Column(Boolean)  # Vertical flip image
    rotation = Column(Integer)  # Rotation degree (0-360)
    cmd_pre_camera = Column(Text)  # Command to execute before capture
    cmd_post_camera = Column(Text)  # Command to execute after capture


class CameraTimelapse(Base):
    __tablename__ = "cameratimelapse"

    id = Column(Integer, unique=True, primary_key=True)
    relay_id = Column(Text, ForeignKey('relay.id'))  # Relay to turn on while capturing
    hflip = Column(Boolean)  # Horizontal flip image
    vflip = Column(Boolean)  # Vertical flip image
    rotation = Column(Integer)  # Rotation degree (0-360)
    cmd_pre_camera = Column(Text)  # Command to execute before capture
    cmd_post_camera = Column(Text)  # Command to execute after capture


class DisplayOrder(Base):
    __tablename__ = "displayorder"

    id = Column(Integer, unique=True, primary_key=True)
    graph = Column(Text)
    lcd = Column(Text)
    pid = Column(Text)
    relay = Column(Text)
    remote_host = Column(Text)
    sensor = Column(Text)
    timer = Column(Text)


class Graph(Base):
    __tablename__ = "graph"
    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    pid_ids_measurements = Column(Text)  # store IDs and measurements to display
    relay_ids_measurements = Column(Text)  # store IDs and measurements to display
    sensor_ids_measurements = Column(Text)  # store IDs and measurements to display
    width = Column(Integer)  # Width of page (in percent)
    height = Column(Integer)  # Height (in pixels)
    x_axis_duration = Column(Integer)  # X-axis duration (in minutes)
    refresh_duration = Column(Integer)  # How often to add new data and redraw graph
    enable_navbar = Column(Boolean)  # Show navigation bar
    enable_rangeselect = Column(Boolean)  # Show range selection buttons
    enable_export = Column(Boolean)  # Show export menu
    use_colors_custom = Column(Boolean)  # Enable custom colors of graph series
    custom_colors = Column(Text)  # Custom hex color values (csv)


class LCD(Base):
    __tablename__ = "lcd"

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    is_activated = Column(Boolean)
    period = Column(Integer)
    location = Column(Text)
    multiplexer_address = Column(Text)
    multiplexer_channel = Column(Integer)
    x_characters = Column(Integer)
    y_lines = Column(Integer)
    line_1_sensor_id = Column(Text)
    line_1_measurement = Column(Text)
    line_2_sensor_id = Column(Text)
    line_2_measurement = Column(Text)
    line_3_sensor_id = Column(Text)
    line_3_measurement = Column(Text)
    line_4_sensor_id = Column(Text)
    line_4_measurement = Column(Text)


class Method(Base):
    __tablename__ = "method"

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    method_type = Column(Text)
    method_order = Column(Text)


class MethodData(Base):
    __tablename__ = "method_data"
    id = Column(Integer, unique=True, primary_key=True)
    method_id = Column(Text, ForeignKey('method.id'))
    time_start = Column(Text)
    time_end = Column(Text)
    duration_sec = Column(Integer)
    relay_id = Column(Text, ForeignKey('relay.id'))
    relay_state = Column(Text)
    relay_duration = Column(Float)
    setpoint_start = Column(Float)
    setpoint_end = Column(Float)
    amplitude = Column(Float)
    frequency = Column(Float)
    shift_angle = Column(Float)
    shift_y = Column(Float)
    x0 = Column(Float)
    y0 = Column(Float)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    x3 = Column(Float)
    y3 = Column(Float)


class Misc(Base):
    __tablename__ = "misc"

    id = Column(Integer, unique=True, primary_key=True)
    dismiss_notification = Column(Boolean)  # Dismiss login page license notice
    force_https = Column(Boolean)  # Force web interface to use SSL/HTTPS
    hide_alert_info = Column(Boolean)
    hide_alert_success = Column(Boolean)
    hide_alert_warning = Column(Boolean)
    language = Column(Text)  # Force the web interface to use a specific language
    login_message = Column(Text)  # Put a message on the login screen
    relay_stats_cost = Column(Float)  # Energy cost per kWh
    relay_stats_currency = Column(Text)  # Energy cost currency
    relay_stats_dayofmonth = Column(Integer)  # Electricity billing day of month
    relay_stats_volts = Column(Integer)  # Voltage the alternating current operates
    stats_opt_out = Column(Boolean)  # Opt not to send anonymous usage statistics


class PID(Base):
    __tablename__ = "pid"

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    is_activated = Column(Boolean)
    is_preset = Column(Boolean)  # Is config saved as a preset?
    preset_name = Column(Text)  # Name for preset
    period = Column(Integer)
    sensor_id = Column(Text, ForeignKey('sensor.id'))
    measurement = Column(Text)  # What condition is the controller regulating?
    direction = Column(Text)  # Direction of regulation (raise, lower, both)
    setpoint = Column(Float)  # PID setpoint
    method_id = Column(Text, ForeignKey('method.id'))
    p = Column(Float)  # Kp gain
    i = Column(Float)  # Ki gain
    d = Column(Float)  # Kd gain
    integrator_min = Column(Float)
    integrator_max = Column(Float)
    raise_relay_id = Column(Text, ForeignKey('relay.id'))  # Relay to raise the condition
    raise_min_duration = Column(Integer)
    raise_max_duration = Column(Integer)
    lower_relay_id = Column(Text, ForeignKey('relay.id'))  # Relay to lower the condition
    lower_min_duration = Column(Integer)
    lower_max_duration = Column(Integer)


class Relay(Base):
    __tablename__ = "relay"

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    pin = Column(Integer)
    amps = Column(Float)  # The current drawn by the device connected to the relay
    trigger = Column(Boolean)  # GPIO output to turn relay on (True=HIGH, False=LOW)
    on_at_start = Column(Boolean)  # Turn relay on when daemon starts?
    on_until = Column(DateTime)  # Stores time to turn off relay (if on for a duration)
    last_duration = Column(Float)  # Stores the last on duration (seconds)
    on_duration = Column(Boolean)  # Stores if the relay is currently on for a duration

    @staticmethod
    def _is_setup():
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

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    is_activated = Column(Boolean)
    if_relay_id = Column(Text, ForeignKey('relay.id'))  # Watch this relay for action
    if_action = Column(Text)  # What action to watch relay for
    if_duration = Column(Float)
    do_relay_id = Column(Text, ForeignKey('relay.id'))  # Actuate relay if conditional triggered
    do_action = Column(Text)  # what action, such as email, execute command, flash LCD
    do_action_data = Column(Text)  # string, such as email address, command, or duration


class Remote(Base):
    __tablename__ = "remote"

    id = Column(Integer, unique=True, primary_key=True)
    is_activated = Column(Boolean)
    host = Column(Text)
    username = Column(Text)
    password_hash = Column(Text)


class Sensor(Base):
    __tablename__ = "sensor"

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    is_activated = Column(Boolean)
    is_preset = Column(Boolean)  # Is config saved as a preset?
    preset_name = Column(Text)  # Name for preset
    device = Column(Text)  # Device name, such as DHT11, DHT22, DS18B20
    period = Column(Float)  # Duration between readings
    i2c_bus = Column(Integer)  # I2C bus the sensor is connected to
    location = Column(Text)  # GPIO pin or i2c address to communicate with sensor
    power_pin = Column(Integer)  # GPIO pin to turn HIGH/LOW to power sensor
    power_state = Column(Boolean)  # State that powers sensor (True=HIGH, False=LOW)
    measurements = Column(Text)  # Measurements separated by commas
    multiplexer_address = Column(Text)
    multiplexer_bus = Column(Integer)
    multiplexer_channel = Column(Integer)
    switch_edge = Column(Text)
    switch_bouncetime = Column(Integer)
    switch_reset_period = Column(Integer)
    pre_relay_id = Column(Text, ForeignKey('relay.id'))  # Relay to turn on before sensor read
    pre_relay_duration = Column(Float)  # Duration to turn relay on before sensor read
    sht_clock_pin = Column(Integer)
    sht_voltage = Column(Text)

    # Analog to digital converter options
    adc_channel = Column(Integer)
    adc_gain = Column(Integer)
    adc_resolution = Column(Integer)
    adc_measure = Column(Text)
    adc_measure_units = Column(Text)
    adc_volts_min = Column(Float)
    adc_volts_max = Column(Float)
    adc_units_min = Column(Float)
    adc_units_max = Column(Float)

    def is_active(self):
        """
        :return: Whether the sensor is currently activated
        :rtype: bool
        """
        return self.is_activated


class SensorConditional(Base):
    __tablename__ = "sensorconditional"

    id = Column(Integer, unique=True, primary_key=True)
    name = Column(Text)
    is_activated = Column(Integer)
    sensor_id = Column(Text, ForeignKey('sensor.id'))
    period = Column(Integer)
    measurement = Column(Text)  # which measurement to monitor
    edge_select = Column(Text)  # monitor Rising, Falling, or Both switch edges
    gpio_state = Column(Integer)
    edge_detected = Column(Text)
    direction = Column(Text)  # 'above' or 'below' setpoint
    setpoint = Column(Float)
    relay_id = Column(Text)
    relay_state = Column(Text)  # 'on' or 'off'
    relay_on_duration = Column(Float)
    execute_command = Column(Text)
    email_notify = Column(Text)
    flash_lcd = Column(Text)
    camera_record = Column(Text)


class SMTP(Base):
    __tablename__ = "smtp"

    id = Column(Integer, unique=True, primary_key=True)
    host = Column(Text)
    ssl = Column(Boolean)
    port = Column(Integer)
    user = Column(Text)
    passw = Column(Text)
    email_from = Column(Text)
    hourly_max = Column(Integer)


class Timer(Base):
    __tablename__ = "timer"

    id = Column(Integer, unique=True, primary_key=True)
    timer_type = Column(Text)
    name = Column(Text)
    is_activated = Column(Boolean)
    relay_id = Column(Text, ForeignKey('relay.id'))
    state = Column(Text)  # 'on' or 'off'
    time_start = Column(Text)
    time_end = Column(Text)
    duration_on = Column(Float)
    duration_off = Column(Float)
