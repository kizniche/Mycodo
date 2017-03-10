# -*- coding: utf-8 -*-
import bcrypt
import datetime
import logging
import uuid
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from RPi import GPIO

from mycodo.config import ALEMBIC_VERSION

logger = logging.getLogger(__name__)

db = SQLAlchemy()

# TODO Build a BaseConditional that all the conditionals inherit from


class CRUDMixin(object):
    """
    Basic Create, Read, Update and Delete methods
    Models that inherit from this class automatically get these CRUD methods
    """

    def save(self, session=db.session):
        """ creates the model in the database """

        try:
            session.add(self)
            session.commit()
            return self
        except Exception as error:
            session.rollback()
            logging.error(
                "Unable to save {model} due to error: {err}".format(
                    model=self, err=error))
            raise error

    def delete(self, session=db.session):
        """ deletes the record from the database """
        try:
            session.delete(self)
            session.commit()
        except Exception as error:
            logger.error(
                "Failed to delete '{record}' due to error: '{err}'".format(
                    record=self, err=error))


def set_uuid():
    return str(uuid.uuid4())


class AlembicVersion(CRUDMixin, db.Model):
    __tablename__ = "alembic_version"
    version_num = db.Column(db.String(32),
                            primary_key=True, nullable=False,
                            default=ALEMBIC_VERSION)


#
# User Table
#

class User(UserMixin, CRUDMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(64), unique=True, index=True)
    password_hash = db.Column(db.VARCHAR(255))
    email = db.Column(db.VARCHAR(64), unique=True, index=True)
    role = db.Column(db.Integer, db.ForeignKey('roles.id'), default=None)
    theme = db.Column(db.VARCHAR(64))

    roles = db.relationship("Role", back_populates="user")

    def __repr__(self):
        output = "<User: <name='{name}', email='{email}' is_admin='{isadmin}'>"
        return output.format(name=self.name,
                             email=self.email,
                             isadmin=bool(self.role == 1))

    def set_password(self, new_password):
        self.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def check_password(password, hashed_password):
        hashes_match = bcrypt.hashpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        return hashes_match


class Role(CRUDMixin, db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    edit_settings = db.Column(db.Boolean, nullable=False, default=False)
    edit_controllers = db.Column(db.Boolean, nullable=False, default=False)
    edit_users = db.Column(db.Boolean, nullable=False, default=False)
    view_settings = db.Column(db.Boolean, nullable=False, default=False)
    view_camera = db.Column(db.Boolean, nullable=False, default=False)
    view_stats = db.Column(db.Boolean, nullable=False, default=False)
    view_logs = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="roles")


#
# Mycodo settings tables
#

class Camera(CRUDMixin, db.Model):
    __tablename__ = "camera"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, unique=True, nullable=False)
    camera_type = db.Column(db.Text, nullable=False)
    library = db.Column(db.Text, nullable=False)
    opencv_device = db.Column(db.Integer, default=0)
    hflip = db.Column(db.Boolean, default=False)  # Horizontal flip image
    vflip = db.Column(db.Boolean, default=False)  # Vertical flip image
    rotation = db.Column(db.Integer, default=0)  # Rotation degree (0-360)
    height = db.Column(db.Integer, default=640)
    width = db.Column(db.Integer, default=480)
    brightness = db.Column(db.Float, default=0.75)
    contrast = db.Column(db.Float, default=0.2)
    exposure = db.Column(db.Float, default=0.0)
    gain = db.Column(db.Float, default=0.0)
    hue = db.Column(db.Float, default=0.0)
    saturation = db.Column(db.Float, default=0.3)
    white_balance = db.Column(db.Float, default=0.0)
    relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Turn relay on during capture
    cmd_pre_camera = db.Column(db.Text, default='')  # Command to execute before capture
    cmd_post_camera = db.Column(db.Text, default='')  # Command to execute after capture
    stream_started = db.Column(db.Boolean, default=False)
    timelapse_started = db.Column(db.Boolean, default=False)
    timelapse_paused = db.Column(db.Boolean, default=False)
    timelapse_start_time = db.Column(db.Float, default=None)
    timelapse_end_time = db.Column(db.Float, default=None)
    timelapse_interval = db.Column(db.Float, default=None)
    timelapse_next_capture = db.Column(db.Float, default=None)
    timelapse_capture_number = db.Column(db.Integer, default=None)


class Conditional(CRUDMixin, db.Model):
    __tablename__ = "conditional"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Conditional Name')
    conditional_type = db.Column(db.Text, default=None)
    is_activated = db.Column(db.Boolean, default=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), default=None)  # Which sensor does this belong?

    # Relay options
    if_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Watch this relay for action
    if_relay_state = db.Column(db.Text, default='')  # What action to watch relay for
    if_relay_duration = db.Column(db.Float, default=0.0)

    # Sensor options
    if_sensor_period = db.Column(db.Float, default=60.0)
    if_sensor_measurement = db.Column(db.Text, default='')  # which measurement to monitor
    if_sensor_edge_select = db.Column(db.Text, default='edge')  # monitor Rising, Falling, or Both switch edges
    if_sensor_edge_detected = db.Column(db.Text, default='rising')
    if_sensor_gpio_state = db.Column(db.Boolean, default=True)
    if_sensor_direction = db.Column(db.Text, default='')  # 'above' or 'below' setpoint
    if_sensor_setpoint = db.Column(db.Float, default=0.0)


class ConditionalActions(CRUDMixin, db.Model):
    __tablename__ = "conditional_data"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    conditional_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)

    # Actions
    do_action = db.Column(db.Text, default='')  # what action, such as 'email', 'execute command', 'flash LCD'
    do_action_string = db.Column(db.Text, default='')  # string, such as the email address or command
    do_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)
    do_relay_state = db.Column(db.Text, default='')  # 'on' or 'off'
    do_relay_duration = db.Column(db.Float, default=0.0)

    do_camera_id = db.Column(db.Integer, db.ForeignKey('lcd.id'), default=None)
    do_camera_duration = db.Column(db.Float, default=0.0)
    do_lcd_id = db.Column(db.Integer, db.ForeignKey('lcd.id'), default=None)
    do_pid_id = db.Column(db.Integer, db.ForeignKey('pid.id'), default=None)


class DisplayOrder(CRUDMixin, db.Model):
    __tablename__ = "displayorder"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    graph = db.Column(db.Text, default='')
    lcd = db.Column(db.Text, default='')
    method = db.Column(db.Text, default='')
    pid = db.Column(db.Text, default='')
    relay = db.Column(db.Text, default='')
    remote_host = db.Column(db.Text, default='')
    sensor = db.Column(db.Text, default='')
    timer = db.Column(db.Text, default='')


class Graph(CRUDMixin, db.Model):
    __tablename__ = "graph"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Graph')
    pid_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    relay_ids = db.Column(db.Text, default='')  # store IDs and measurements to display
    sensor_ids_measurements = db.Column(db.Text, default='')  # store IDs and measurements to display
    width = db.Column(db.Integer, default=100)  # Width of page (in percent)
    height = db.Column(db.Integer, default=400)  # Height (in pixels)
    x_axis_duration = db.Column(db.Integer, default=1440)  # X-axis duration (in minutes)
    refresh_duration = db.Column(db.Integer, default=120)  # How often to add new data and redraw graph
    enable_navbar = db.Column(db.Boolean, default=False)  # Show navigation bar
    enable_rangeselect = db.Column(db.Boolean, default=False)  # Show range selection buttons
    enable_export = db.Column(db.Boolean, default=False)  # Show export menu
    use_custom_colors = db.Column(db.Boolean, default=False)  # Enable custom colors of graph series
    custom_colors = db.Column(db.Text, default='')  # Custom hex color values (csv)


class LCD(CRUDMixin, db.Model):
    __tablename__ = "lcd"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='LCD')
    is_activated = db.Column(db.Boolean, default=False)
    period = db.Column(db.Float, default=30)
    location = db.Column(db.Text, default='27')
    multiplexer_address = db.Column(db.Text, default='')
    multiplexer_channel = db.Column(db.Integer, default=0)
    x_characters = db.Column(db.Integer, default=16)
    y_lines = db.Column(db.Integer, default=2)
    line_1_sensor_id = db.Column(db.Text, default='')
    line_1_measurement = db.Column(db.Text, default='')
    line_2_sensor_id = db.Column(db.Text, default='')
    line_2_measurement = db.Column(db.Text, default='')
    line_3_sensor_id = db.Column(db.Text, default='')
    line_3_measurement = db.Column(db.Text, default='')
    line_4_sensor_id = db.Column(db.Text, default='')
    line_4_measurement = db.Column(db.Text, default='')


class Method(CRUDMixin, db.Model):
    __tablename__ = "method"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Method')
    method_order = db.Column(db.Text, default='')
    method_type = db.Column(db.Text, default='')
    start_time = db.Column(db.DateTime, default=None)

    method_data = db.relationship("MethodData", back_populates="method")


class MethodData(CRUDMixin, db.Model):
    __tablename__ = "method_data"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    method_id = db.Column(db.Integer, db.ForeignKey('method.id'), default=None)
    time_start = db.Column(db.Text, default=None)
    time_end = db.Column(db.Text, default=None)
    duration_sec = db.Column(db.Float, default=None)
    relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)
    relay_state = db.Column(db.Text, default=None)
    relay_duration = db.Column(db.Float, default=None)
    setpoint_start = db.Column(db.Float, default=None)
    setpoint_end = db.Column(db.Float, default=None)
    amplitude = db.Column(db.Float, default=None)
    frequency = db.Column(db.Float, default=None)
    shift_y = db.Column(db.Float, default=None)
    shift_angle = db.Column(db.Float, default=None)
    x0 = db.Column(db.Float, default=None)
    y0 = db.Column(db.Float, default=None)
    x1 = db.Column(db.Float, default=None)
    y1 = db.Column(db.Float, default=None)
    x2 = db.Column(db.Float, default=None)
    y2 = db.Column(db.Float, default=None)
    x3 = db.Column(db.Float, default=None)
    y3 = db.Column(db.Float, default=None)

    method = db.relationship("Method", back_populates="method_data")


class Misc(CRUDMixin, db.Model):
    __tablename__ = "misc"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    dismiss_notification = db.Column(db.Boolean, default=False)  # Dismiss login page license notice
    force_https = db.Column(db.Boolean, default=True)  # Force web interface to use SSL/HTTPS
    hide_alert_info = db.Column(db.Boolean, default=False)
    hide_alert_success = db.Column(db.Boolean, default=False)
    hide_alert_warning = db.Column(db.Boolean, default=False)
    language = db.Column(db.Text, default=None)  # Force the web interface to use a specific language
    login_message = db.Column(db.Text, default='')  # Put a message on the login screen
    relay_usage_cost = db.Column(db.Float, default=0.05)  # Energy cost per kWh
    relay_usage_currency = db.Column(db.Text, default='$')  # Energy cost currency
    relay_usage_dayofmonth = db.Column(db.Integer, default=15)  # Electricity billing day of month
    relay_usage_volts = db.Column(db.Integer, default=120)  # Voltage the alternating current operates
    relay_usage_report_gen = db.Column(db.Boolean, default=False)
    relay_usage_report_span = db.Column(db.Text, default='monthly')
    relay_usage_report_day = db.Column(db.Integer, default=1)
    relay_usage_report_hour = db.Column(db.Integer, default=0)
    stats_opt_out = db.Column(db.Boolean, default=False)  # Opt not to send anonymous usage statistics


class PID(CRUDMixin, db.Model):
    __tablename__ = "pid"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default='PID')
    is_activated = db.Column(db.Boolean, default=False)
    is_held = db.Column(db.Boolean, default=False)
    is_paused = db.Column(db.Boolean, default=False)
    is_preset = db.Column(db.Boolean, default=False)  # Is config saved as a preset?
    preset_name = db.Column(db.Text, default='')  # Name for preset
    period = db.Column(db.Float, default=30.0)
    max_measure_age = db.Column(db.Float, default=120.0)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), default=None)
    measurement = db.Column(db.Text, default='')  # What condition is the controller regulating?
    direction = db.Column(db.Text, default='Raise')  # Direction of regulation (raise, lower, both)
    setpoint = db.Column(db.Float, default=30.0)  # PID setpoint
    method_id = db.Column(db.Integer, db.ForeignKey('method.id'), default=None)
    p = db.Column(db.Float, default=1.0)  # Kp gain
    i = db.Column(db.Float, default=0.0)  # Ki gain
    d = db.Column(db.Float, default=0.0)  # Kd gain
    integrator_min = db.Column(db.Float, default=-100.0)
    integrator_max = db.Column(db.Float, default=100.0)
    raise_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Relay to raise the condition
    raise_min_duration = db.Column(db.Float, default=0.0)
    raise_max_duration = db.Column(db.Float, default=0.0)
    raise_min_off_duration = db.Column(db.Float, default=0.0)
    lower_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Relay to lower the condition
    lower_min_duration = db.Column(db.Float, default=0.0)
    lower_max_duration = db.Column(db.Float, default=0.0)
    lower_min_off_duration = db.Column(db.Float, default=0.0)


class Relay(CRUDMixin, db.Model):
    __tablename__ = "relay"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default='Relay')
    pin = db.Column(db.Integer, default=0)
    amps = db.Column(db.Float, default=0.0)  # The current drawn by the device connected to the relay
    trigger = db.Column(db.Boolean, default=True)  # GPIO output to turn relay on (True=HIGH, False=LOW)
    on_at_start = db.Column(db.Boolean, default=False)  # Turn relay on when daemon starts?
    on_until = db.Column(db.DateTime, default=None)  # Stores time to turn off relay (if on for a duration)
    last_duration = db.Column(db.Float, default=None)  # Stores the last on duration (seconds)
    on_duration = db.Column(db.Boolean, default=None)  # Stores if the relay is currently on for a duration

    def _is_setup(self):
        """
        This function checks to see if the GPIO pin is setup and ready to use.  This is for safety
        and to make sure we don't blow anything.

        # TODO Make it do that.

        :return: Is it safe to manipulate this relay?
        :rtype: bool
        """
        if self.pin:
            self.setup_pin()
            return True

    def setup_pin(self):
        """
        Setup pin for this relay

        :rtype: None
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
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
        if self._is_setup():
            return self.trigger == GPIO.input(self.pin)


class Remote(CRUDMixin, db.Model):
    __tablename__ = "remote"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    is_activated = db.Column(db.Boolean, default=False)
    host = db.Column(db.Text, default='')
    username = db.Column(db.Text, default='')
    password_hash = db.Column(db.Text, default='')


class Sensor(CRUDMixin, db.Model):
    __tablename__ = "sensor"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    name = db.Column(db.Text, default='Sensor')
    is_activated = db.Column(db.Boolean, default=False)
    is_preset = db.Column(db.Boolean, default=False)  # Is config saved as a preset?
    preset_name = db.Column(db.Text, default=None)  # Name for preset
    device = db.Column(db.Text, default='')  # Device name, such as DHT11, DHT22, DS18B20
    device_type = db.Column(db.Text, default='')
    period = db.Column(db.Float, default=15.0)  # Duration between readings
    i2c_bus = db.Column(db.Integer, default='')  # I2C bus the sensor is connected to
    location = db.Column(db.Text, default='')  # GPIO pin or i2c address to communicate with sensor
    power_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Relay to power sensor
    measurements = db.Column(db.Text, default='')  # Measurements separated by commas
    multiplexer_address = db.Column(db.Text, default=None)
    multiplexer_bus = db.Column(db.Integer, default=1)
    multiplexer_channel = db.Column(db.Integer, default=0)
    switch_edge = db.Column(db.Text, default='rising')
    switch_bouncetime = db.Column(db.Integer, default=50)
    switch_reset_period = db.Column(db.Integer, default=10)
    pre_relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)  # Relay to turn on before sensor read
    pre_relay_duration = db.Column(db.Float, default=0.0)  # Duration to turn relay on before sensor read
    sht_clock_pin = db.Column(db.Integer, default=None)
    sht_voltage = db.Column(db.Text, default='3.5')

    # Analog to digital converter options
    adc_channel = db.Column(db.Integer, default=0)
    adc_gain = db.Column(db.Integer, default=1)
    adc_resolution = db.Column(db.Integer, default=18)
    adc_measure = db.Column(db.Text, default='Condition')
    adc_measure_units = db.Column(db.Text, default='unit')
    adc_volts_min = db.Column(db.Float, default=None)
    adc_volts_max = db.Column(db.Float, default=None)
    adc_units_min = db.Column(db.Float, default=0)
    adc_units_max = db.Column(db.Float, default=10)

    def is_active(self):
        """
        :return: Whether the sensor is currently activated
        :rtype: bool
        """
        return self.is_activated


class SMTP(CRUDMixin, db.Model):
    __tablename__ = "smtp"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    host = db.Column(db.Text, default='smtp.gmail.com')
    ssl = db.Column(db.Boolean, default=1)
    port = db.Column(db.Integer, default=465)
    user = db.Column(db.Text, default='email@gmail.com')
    passw = db.Column(db.Text, default='password')
    email_from = db.Column(db.Text, default='email@gmail.com')
    hourly_max = db.Column(db.Integer, default=2)


class Timer(CRUDMixin, db.Model):
    __tablename__ = "timer"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.Text, default='Timer')
    is_activated = db.Column(db.Boolean, default=False)
    timer_type = db.Column(db.Text, default=None)
    relay_id = db.Column(db.Integer, db.ForeignKey('relay.id'), default=None)
    state = db.Column(db.Text, default=None)  # 'on' or 'off'
    time_start = db.Column(db.Text, default=None)
    time_end = db.Column(db.Text, default=None)
    duration_on = db.Column(db.Float, default=None)
    duration_off = db.Column(db.Float, default=None)
