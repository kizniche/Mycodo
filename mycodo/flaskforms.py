# -*- coding: utf-8 -*-
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired
from wtforms.validators import Optional
from wtforms.fields.html5 import EmailField

from mycodo.config import CALIBRATION_DEVICES
from mycodo.config import SENSORS


#
# Calibration selection (what to calibrate)
#

class Calibration(FlaskForm):
    selection = SelectField(
        'Device to Calibrate',
        choices=CALIBRATION_DEVICES,
        validators=[DataRequired()]
    )
    submit = SubmitField(lazy_gettext(u'Select Device'))


#
# Calibration: Atlas Scientific pH sensor
#

class CalibrationAtlasph(FlaskForm):
    selected_sensor_id = StringField(lazy_gettext(u'Atlas pH Sensor'))
    hidden_sensor_id = StringField('Sensor ID', widget=widgets.HiddenInput())
    clear_calibration = SubmitField(lazy_gettext(u'Clear Calibration'))
    temperature = DecimalField(
        lazy_gettext(u'Temperature'),
        render_kw={"placeholder": 25.00})
    hidden_next_stage = StringField('Stage', widget=widgets.HiddenInput())
    go_from_first_stage = SubmitField(lazy_gettext(u'Begin Calibration'))
    go_to_next_stage = SubmitField(lazy_gettext(u'Continue to Next Stage'))
    go_to_last_stage = SubmitField(lazy_gettext(u'Continue to Next Stage'))


#
# Camera Use
#

class Camera(FlaskForm):
    camera_id = IntegerField('Camera ID', widget=widgets.HiddenInput())
    capture_still = SubmitField(lazy_gettext(u'Capture Still'))
    start_timelapse = SubmitField(lazy_gettext(u'Start Timelapse'))
    pause_timelapse = SubmitField(lazy_gettext(u'Pause Timelapse'))
    resume_timelapse = SubmitField(lazy_gettext(u'Resume Timelapse'))
    stop_timelapse = SubmitField(lazy_gettext(u'Stop Timelapse'))
    timelapse_interval = DecimalField(
        lazy_gettext(u'Photo Interval (sec)'),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext(u'Photo Interval must be a positive value.')
        )]
    )
    timelapse_runtime_sec = DecimalField(
        lazy_gettext(u'Total Run Time (sec)'),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext(u'Total Run Time must be a positive value.')
        )]
    )
    start_stream = SubmitField(lazy_gettext(u'Start Stream'))
    stop_stream = SubmitField(lazy_gettext(u'Stop Stream'))


#
# Conditionals
#

class Conditional(FlaskForm):
    conditional_id = IntegerField('Conditional ID', widget=widgets.HiddenInput())
    conditional_type = StringField('Conditional Type', widget=widgets.HiddenInput())
    sensor_id = IntegerField('Output ID', widget=widgets.HiddenInput())
    quantity = IntegerField(lazy_gettext(u'Quantity'))
    name = StringField(lazy_gettext(u'Name'))

    # Relay conditional options
    if_relay_id = StringField(lazy_gettext(u'If Relay ID'))
    if_relay_state = StringField(lazy_gettext(u'If Relay State'))
    if_relay_duration = DecimalField(lazy_gettext(u'If Relay Duration'))

    # Sensor conditional options
    if_sensor_period = DecimalField(lazy_gettext(u'Period'))
    if_sensor_measurement = StringField(lazy_gettext(u'Measurement'))
    if_sensor_edge_select = StringField(lazy_gettext(u'Edge or State'))
    if_sensor_edge_detected = StringField(lazy_gettext(u'Edge Detected'))
    if_sensor_gpio_state = IntegerField(lazy_gettext(u'GPIO State'))
    if_sensor_direction = StringField(lazy_gettext(u'Direction'))
    if_sensor_setpoint = DecimalField(lazy_gettext(u'Setpoint'))

    add_cond = SubmitField(lazy_gettext(u'Add Conditional'))
    save_cond = SubmitField(lazy_gettext(u'Save'))
    delete_cond = SubmitField(lazy_gettext(u'Delete'))
    activate_cond = SubmitField(lazy_gettext(u'Activate'))
    deactivate_cond = SubmitField(lazy_gettext(u'Deactivate'))


class ConditionalActions(FlaskForm):
    conditional_id = IntegerField(
        'Conditional ID', widget=widgets.HiddenInput())
    conditional_action_id = IntegerField(
        'Conditional Action ID', widget=widgets.HiddenInput())
    do_action = StringField(lazy_gettext(u'Action to Perform'))
    do_action_string = StringField(lazy_gettext(u'Action String'))
    do_relay_id = IntegerField(lazy_gettext(u'Relay'))
    do_relay_state = StringField(lazy_gettext(u'Relay State'))
    do_relay_duration = DecimalField(lazy_gettext(u'Duration'))
    do_camera_id = IntegerField(lazy_gettext(u'Camera'))
    do_camera_duration = DecimalField(lazy_gettext(u'Duration'))
    do_lcd_id = IntegerField(lazy_gettext(u'LCD ID'))
    do_pid_id = IntegerField(lazy_gettext(u'PID ID'))
    add_action = SubmitField(lazy_gettext(u'Add Action'))
    save_action = SubmitField(lazy_gettext(u'Save'))
    delete_action = SubmitField(lazy_gettext(u'Delete'))


#
# Create Admin
#

class CreateAdmin(FlaskForm):
    username = StringField(
        lazy_gettext(u'Username'),
        render_kw={"placeholder": lazy_gettext(u'Username')},
        validators=[DataRequired()])
    email = StringField(
        lazy_gettext(u'Email'),
        render_kw={"placeholder": lazy_gettext(u'Email')},
        validators=[DataRequired()])
    password = PasswordField(
        lazy_gettext(u'Password'),
        render_kw={"placeholder": lazy_gettext(u'Password')},
        validators=[DataRequired()])
    password_repeat = PasswordField(
        lazy_gettext(u'Repeat Password'),
        render_kw={"placeholder": lazy_gettext(u'Repeat Password')},
        validators=[DataRequired()])


#
# Daemon Control
#

class DaemonControl(FlaskForm):
    stop = SubmitField(lazy_gettext(u'Stop Daemon'))
    start = SubmitField(lazy_gettext(u'Start Daemon'))
    restart = SubmitField(lazy_gettext(u'Restart Daemon'))


#
# Email Alerts
#

class EmailAlert(FlaskForm):
    smtp_host = StringField(
        lazy_gettext(u'SMTP Host'),
        render_kw={"placeholder": lazy_gettext(u'SMTP Host')},
        validators=[DataRequired()]
    )
    smtp_port = IntegerField(
        lazy_gettext(u'SMTP Port'),
        render_kw={"placeholder": lazy_gettext(u'SMTP Port')},
        validators=[validators.NumberRange(
            min=1,
            max=65535,
            message=lazy_gettext(u'Port should be between 1 and 65535')
        )]
    )
    smtp_ssl = BooleanField('Enable SSL')
    smtp_user = StringField(
        lazy_gettext(u'SMTP User'),
        render_kw={"placeholder": lazy_gettext(u'SMTP User')},
        validators=[DataRequired()]
    )
    smtp_password = PasswordField(
        lazy_gettext(u'SMTP Password'),
        render_kw={"placeholder": lazy_gettext(u'Password')}
    )
    smtp_from_email = EmailField(
        lazy_gettext(u'From Email'),
        render_kw={"placeholder": lazy_gettext(u'Email')},
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    smtp_hourly_max = IntegerField(
        lazy_gettext(u'Max emails (per hour)'),
        render_kw={"placeholder": lazy_gettext(u'Max emails (per hour)')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u'Must have at least one message able to be '
                                 u'sent per hour.')
        )]
    )
    send_test = SubmitField(lazy_gettext(u'Send Test Email'))
    send_test_to_email = EmailField(
        lazy_gettext(u'Test Email To'),
        render_kw={"placeholder": lazy_gettext(u'To Email Address')},
        validators=[
            validators.Email(),
            validators.Optional()
        ]
    )
    save = SubmitField('Save')


#
# Export Options
#

class ExportOptions(FlaskForm):
    measurement = StringField(lazy_gettext(u'Measurement to Export'))
    date_range = StringField(lazy_gettext(u'Time Range DD/MM/YYYY HH:MM'))
    Export = SubmitField(lazy_gettext(u'Export'))


#
# Graphs
#

class GraphAdd(FlaskForm):
    name = StringField(
        lazy_gettext(u'Graph Name'),
        render_kw={"placeholder": lazy_gettext(u"Graph Name")},
        validators=[DataRequired()]
    )
    pid_ids = SelectMultipleField(lazy_gettext(u'PID IDs (Setpoint)'))
    relay_ids = SelectMultipleField(lazy_gettext(u'Output IDs'))
    sensor_ids = SelectMultipleField(lazy_gettext(u'Output IDs'))
    width = IntegerField(
        lazy_gettext(u'Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext(u'Height (pixels)'),
        render_kw={"placeholder": lazy_gettext(u"Percent Height")},
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xaxis_duration = IntegerField(
        lazy_gettext(u'x-Axis (minutes)'),
        render_kw={"placeholder": lazy_gettext(u"X-Axis Duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u"Number of minutes to display of past "
                                 u"measurements.")
        )]
    )
    refresh_duration = IntegerField(
        lazy_gettext(u'Refresh (seconds)'),
        render_kw={"placeholder": lazy_gettext(u"Refresh duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u"Number of seconds to wait between acquiring"
                                 u" any new measurements.")
        )]
    )
    enable_navbar = BooleanField(lazy_gettext(u'Enable Navbar'))
    enable_export = BooleanField(lazy_gettext(u'Enable Export'))
    enable_range = BooleanField(lazy_gettext(u'Enable Range Selector'))
    Submit = SubmitField(lazy_gettext(u'Create Graph'))


class GraphMod(FlaskForm):
    graph_id = IntegerField('Graph ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Graph Name'),
        render_kw={"placeholder": lazy_gettext(u"Graph Name")},
        validators=[DataRequired()]
    )
    pid_ids = SelectMultipleField(lazy_gettext(u'PID IDs (Setpoint)'))
    relay_ids = SelectMultipleField(lazy_gettext(u'Output IDs'))
    sensor_ids = SelectMultipleField(lazy_gettext(u'Output IDs'))
    width = IntegerField(
        lazy_gettext(u'Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext(u'Height (pixels)'),
        render_kw={"placeholder": lazy_gettext(u"Percent Height")},
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xaxis_duration = IntegerField(
        lazy_gettext(u'x-Axis (minutes)'),
        render_kw={"placeholder": lazy_gettext(u"X-Axis Duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u"Number of minutes to display of past "
                                 u"measurements.")
        )]
    )
    refresh_duration = IntegerField(
        lazy_gettext(u'Refresh (seconds)'),
        render_kw={"placeholder": lazy_gettext(u"Refresh duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u"Number of seconds to wait between acquiring"
                                 u" any new measurements.")
        )]
    )
    enable_navbar = BooleanField(lazy_gettext(u'Enable Navbar'))
    enable_export = BooleanField(lazy_gettext(u'Enable Export'))
    enable_range = BooleanField(lazy_gettext(u'Enable Range Selector'))
    use_custom_colors = BooleanField(lazy_gettext(u'Enable Custom Colors'))
    Submit = SubmitField(lazy_gettext(u'Save Graph'))


class GraphDel(FlaskForm):
    graph_id = IntegerField('Graph ID', widget=widgets.HiddenInput())
    Submit = SubmitField(lazy_gettext(u'Delete Graph'))


class GraphOrder(FlaskForm):
    orderGraph_id = IntegerField('Graph ID', widget=widgets.HiddenInput())
    orderGraphUp = SubmitField(lazy_gettext(u'Up'))
    orderGraphDown = SubmitField(lazy_gettext(u'Down'))


#
# LCDs
#

class LCDAdd(FlaskForm):
    quantity = IntegerField(
        lazy_gettext(u'Quantity'),
        render_kw={"placeholder": lazy_gettext(u"Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    add = SubmitField(lazy_gettext(u'Add LCDs'))


class LCDMod(FlaskForm):
    lcd_id = IntegerField('LCD ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        render_kw={"placeholder": lazy_gettext(u"Name")},
        validators=[DataRequired()]
    )
    location = StringField(
        lazy_gettext(u'I2C Address'),
        render_kw={"placeholder": lazy_gettext(u"I2C Address")},
        validators=[DataRequired()]
    )
    multiplexer_address = StringField(
        lazy_gettext(u'Multiplexer I2C Address'),
        render_kw={"placeholder": lazy_gettext(u"I2C Address")}
    )
    multiplexer_channel = IntegerField(
        lazy_gettext(u'Multiplexer Channel'),
        render_kw={"placeholder": lazy_gettext(u"Channel")},
        validators=[
            validators.NumberRange(
                min=0,
                max=8
            )]
    )
    period = DecimalField(
        lazy_gettext(u'Period'),
        render_kw={"placeholder": lazy_gettext(u"Period")},
        validators=[validators.NumberRange(
            min=5,
            max=86400,
            message=lazy_gettext(u"Duration between calculating LCD output "
                                 u"and applying to regulation must be between "
                                 u"5 and 86400 seconds.")
        )]
    )
    lcd_type = SelectField(
        lazy_gettext(u'LCD Type'),
        choices=[
            ('16x2', '16x2'),
            ('20x4', '20x4')
        ],
        validators=[DataRequired()]
    )
    line_1_display = StringField(
        lazy_gettext(u'Line 1 Display')
    )
    line_2_display = StringField(
        lazy_gettext(u'Line 2 Display')
    )
    line_3_display = StringField(
        lazy_gettext(u'Line 3 Display')
    )
    line_4_display = StringField(
        lazy_gettext(u'Line 4 Display')
    )
    save = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    activate = SubmitField(lazy_gettext(u'Activate'))
    deactivate = SubmitField(lazy_gettext(u'Deactivate'))
    reorder_up = SubmitField(lazy_gettext(u'Up'))
    reorder_down = SubmitField(lazy_gettext(u'Down'))
    reset_flashing = SubmitField(lazy_gettext(u'Reset Flashing'))


#
# Login
#

class Login(FlaskForm):
    username = StringField(
        lazy_gettext(u'Username'),
        render_kw={"placeholder": lazy_gettext(u"Username")},
        validators=[DataRequired()]
    )
    password = PasswordField(
        lazy_gettext(u'Password'),
        render_kw={"placeholder": lazy_gettext(u"Password")},
        validators=[DataRequired()]
    )
    remember = BooleanField(lazy_gettext(u'remember'))


#
# Log viewer
#

class LogView(FlaskForm):
    lines = IntegerField(
        lazy_gettext(u'Number of Lines'),
        render_kw={'placeholder': lazy_gettext(u'Lines')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u'Number of lines should be greater than 0.')
        )]
    )
    loglogin = SubmitField(lazy_gettext(u'Login Log'))
    loghttp = SubmitField(lazy_gettext(u'HTTP Log'))
    logdaemon = SubmitField(lazy_gettext(u'Daemon Log'))
    logbackup = SubmitField(lazy_gettext(u'Backup Log'))
    logkeepup = SubmitField(lazy_gettext(u'KeepUp Log'))
    logupgrade = SubmitField(lazy_gettext(u'Upgrade Log'))
    logrestore = SubmitField(lazy_gettext(u'Restore Log'))


#
# Method (Date)
#

class MethodCreate(FlaskForm):
    name = StringField(lazy_gettext(u'Name'))
    method_type = StringField(lazy_gettext(u'Method Type'))
    controller_type = HiddenField('Controller Type')
    Submit = SubmitField(lazy_gettext(u'Create New Method'))


class MethodAdd(FlaskForm):
    method_id = IntegerField('Method ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
    daily_time_start = StringField(
        lazy_gettext(u'Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    daily_time_end = StringField(
        lazy_gettext(u'End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    time_start = StringField(
        lazy_gettext(u'Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    time_end = StringField(
        lazy_gettext(u'End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    setpoint_start = DecimalField(lazy_gettext(u'Start Setpoint'))
    setpoint_end = DecimalField(lazy_gettext(u'End Setpoint (optional)'))
    duration = IntegerField(lazy_gettext(u'Duration (seconds)'))
    amplitude = DecimalField(lazy_gettext(u'Amplitude'))
    frequency = DecimalField(lazy_gettext(u'Frequency'))
    shift_angle = DecimalField(lazy_gettext(u'Angle Shift (0 to 360)'))
    shiftY = DecimalField(lazy_gettext(u'Y-Axis Shift'))
    x0 = DecimalField('X0')
    y0 = DecimalField('Y0')
    x1 = DecimalField('X1')
    y1 = DecimalField('Y1')
    x2 = DecimalField('X2')
    y2 = DecimalField('Y2')
    x3 = DecimalField('X3')
    y3 = DecimalField('Y3')
    relay_daily_time = StringField(
        lazy_gettext(u'Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relay_time = StringField(
        lazy_gettext(u'Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relay_duration = IntegerField(lazy_gettext(u'Duration On (sec)'))
    relay_id = StringField(lazy_gettext(u'Relay ID'),)
    relay_state = SelectField(
        lazy_gettext(u'Relay State'),
        choices=[
            ('', ''),
            ('On', lazy_gettext(u'Turn On')),
            ('Off', lazy_gettext(u'Turn Off'))
        ]
    )
    save = SubmitField(lazy_gettext(u'Add to Method'))


class MethodMod(FlaskForm):
    method_id = IntegerField('Method ID', widget=widgets.HiddenInput())
    method_data_id = IntegerField('Method Data ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
    name = StringField(lazy_gettext(u'Name'))
    daily_time_start = StringField(
        lazy_gettext(u'Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    daily_time_end = StringField(
        lazy_gettext(u'End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    time_start = StringField(
        lazy_gettext(u'Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    time_end = StringField(
        lazy_gettext(u'End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relay_daily_time = StringField(
        lazy_gettext(u'Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relay_time = StringField(
        lazy_gettext(u'Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    duration = IntegerField(lazy_gettext(u'Duration (seconds)'))
    setpoint_start = DecimalField(lazy_gettext(u'Start Setpoint'))
    setpoint_end = DecimalField(lazy_gettext(u'End Setpoint'))
    relay_id = StringField(lazy_gettext(u'Relay'))
    relay_state = StringField(lazy_gettext(u'Relay State'))
    relay_duration = IntegerField(lazy_gettext(u'Relay Duration'))
    rename = SubmitField(lazy_gettext(u'Rename'))
    save = SubmitField(lazy_gettext(u'Save'))
    Delete = SubmitField(lazy_gettext(u'Delete'))


#
# PIDs
#

class PIDAdd(FlaskForm):
    pid_type = StringField(lazy_gettext(u'Type'))
    numberPIDs = IntegerField(
        lazy_gettext(u'Quantity'),
        render_kw={"placeholder": lazy_gettext(u"Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    pidAddSubmit = SubmitField(lazy_gettext(u'Add PIDs'))


class PIDMod(FlaskForm):
    pid_id = IntegerField('PID ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    sensor_id = StringField(
        lazy_gettext(u'Input ID'),
        validators=[DataRequired()]
    )
    measurement = StringField(
        lazy_gettext(u'Measure Type'),
        validators=[DataRequired()]
    )
    direction = SelectField(
        lazy_gettext(u'Direction'),
        choices=[
            ('raise', lazy_gettext(u'Raise')),
            ('lower', lazy_gettext(u'Lower')),
            ('both', lazy_gettext(u'Both'))
        ],
        validators=[DataRequired()]
    )
    period = DecimalField(
        lazy_gettext(u'Period'),
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    max_measure_age = DecimalField(
        lazy_gettext(u'Max Age (sec)'),
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    setpoint = DecimalField(
        lazy_gettext(u'Setpoint'),
        validators=[validators.NumberRange(
            min=-1000000,
            max=1000000
        )]
    )
    k_p = DecimalField(
        lazy_gettext(u'Kp Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_i = DecimalField(
        lazy_gettext(u'Ki Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_d = DecimalField(
        lazy_gettext(u'Kd Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    integrator_max = DecimalField(lazy_gettext(u'Integrator Min'))
    integrator_min = DecimalField(lazy_gettext(u'Integrator Max'))
    raise_relay_id = StringField(lazy_gettext(u'Output ID (Raise)'))
    raise_min_duration = DecimalField(
        lazy_gettext(u'Raise Min On Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_max_duration = DecimalField(
        lazy_gettext(u'Raise Max On Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_min_off_duration = DecimalField(
        lazy_gettext(u'Raise Min Off Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_relay_id = StringField(lazy_gettext(u'Output ID (Lower)'),)
    lower_min_duration = DecimalField(
        lazy_gettext(u'Lower Min On Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_max_duration = DecimalField(
        lazy_gettext(u'Lower Max On Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_min_off_duration = DecimalField(
        lazy_gettext(u'Lower Min Off Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    method_id = IntegerField(
        'Setpoint Tracking Method', widget=widgets.HiddenInput())
    save = SubmitField(lazy_gettext(u'Save'))
    hold = SubmitField(lazy_gettext(u'Hold'))
    pause = SubmitField(lazy_gettext(u'Pause'))
    resume = SubmitField(lazy_gettext(u'Resume'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    activate = SubmitField(lazy_gettext(u'Activate'))
    deactivate = SubmitField(lazy_gettext(u'Deactivate'))
    reorder_up = SubmitField(lazy_gettext(u'Up'))
    reorder_down = SubmitField(lazy_gettext(u'Down'))


#
# Relays
#

class RelayAdd(FlaskForm):
    relay_quantity = IntegerField(lazy_gettext(u'Quantity'))
    relay_type = StringField(lazy_gettext(u'Type'))
    relay_add = SubmitField(lazy_gettext(u'Add Output Device'))
    relay_cond_quantity = IntegerField(lazy_gettext(u'Quantity'))
    relay_cond_add = SubmitField(lazy_gettext(u'Add Relay Conditional'))


class RelayMod(FlaskForm):
    relay_id = IntegerField('Relay ID', widget=widgets.HiddenInput())
    relay_pin = HiddenField('Relay Pin')
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    gpio = IntegerField(lazy_gettext(u'BCM Pin'))
    wiringpi_pin = IntegerField(lazy_gettext(u'WiringPi Pin'))
    protocol = IntegerField(lazy_gettext(u'Protocol'))
    pulse_length = IntegerField(lazy_gettext(u'Pulse Length'))
    bit_length = IntegerField(lazy_gettext(u'Bit length'))
    on_command = StringField(lazy_gettext(u'On Command'))
    off_command = StringField(lazy_gettext(u'Off Command'))
    amps = DecimalField(
        lazy_gettext(u'Current Draw (amps)'),
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message=lazy_gettext(u"The current draw of the device connected "
                                 u"to this relay, in amps.")
        )]
    )
    trigger = SelectField(
        lazy_gettext(u'On Trigger'),
        choices=[
            ("1", lazy_gettext(u'High')),
            ("0", lazy_gettext(u'Low'))
        ],
        validators=[Optional()]
    )
    on_at_start = SelectField(
        lazy_gettext(u'Start State'),
        choices=[
            ("-1", lazy_gettext(u'Neither')),
            ("1", lazy_gettext(u'On')),
            ("0", lazy_gettext(u'Off'))
        ],
        validators=[DataRequired()]
    )
    pwm_hertz = IntegerField(lazy_gettext(u'Hertz'))
    save = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    order_up = SubmitField(lazy_gettext(u'Up'))
    order_down = SubmitField(lazy_gettext(u'Down'))
    turn_on = SubmitField(lazy_gettext(u'On'))
    turn_off = SubmitField(lazy_gettext(u'Off'))
    sec_on = DecimalField(
        lazy_gettext(u'Seconds to turn on'),
        validators=[Optional()]
    )
    pwm_duty_cycle_on = DecimalField(
        lazy_gettext(u'Duty Cycle'),
        validators=[Optional()]
    )
    on_submit = SubmitField(lazy_gettext(u'Turn On'))


#
# Remote Admin add servers
#

class RemoteSetup(FlaskForm):
    remote_id = IntegerField('Remote Host ID', widget=widgets.HiddenInput())
    host = StringField(
        lazy_gettext(u'Domain or IP Address'),
        render_kw={"placeholder": "youraddress.com or 0.0.0.0"},
        validators=[DataRequired()]
    )
    username = StringField(
        lazy_gettext(u'Username'),
        validators=[DataRequired()]
    )
    password = PasswordField(
        lazy_gettext(u'Password'),
        validators=[DataRequired()]
    )
    add = SubmitField(lazy_gettext(u'Add Host'))
    delete = SubmitField(lazy_gettext(u'Delete Host'))


#
# Sensors
#

class SensorAdd(FlaskForm):
    numberSensors = IntegerField(
        lazy_gettext(u'Quantity'),
        render_kw={"placeholder": lazy_gettext(u"Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    sensor = SelectField(
        lazy_gettext(u'Sensor'),
        choices=SENSORS,
        validators=[DataRequired()]
    )
    sensorAddSubmit = SubmitField(lazy_gettext(u'Add Device'))


class SensorMod(FlaskForm):
    modSensor_id = IntegerField('Input ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    i2c_bus = IntegerField(lazy_gettext(u'I<sup>2</sup>C Bus'))
    location = StringField(lazy_gettext(u'Location'))
    baud_rate = IntegerField(lazy_gettext(u'Baud Rate'))
    device_loc = StringField(lazy_gettext(u'Device'))
    calibrate_sensor_measure = StringField(lazy_gettext(u'Calibration Measurement'))
    resolution = IntegerField(lazy_gettext(u'Resolution'))
    sensitivity = IntegerField(lazy_gettext(u'Sensitivity'))
    power_relay_id = IntegerField(lazy_gettext(u'Power Relay'))
    multiplexer_address = StringField(lazy_gettext(u'Multiplexer (MX)'))
    multiplexer_bus = StringField(lazy_gettext(u'Mx I<sup>2</sup>C Bus'))
    multiplexer_channel = IntegerField(lazy_gettext(u'Mx Channel'))
    adc_channel = IntegerField(lazy_gettext(u'ADC Channel'))
    adc_gain = IntegerField(lazy_gettext(u'ADC Gain'))
    adc_resolution = IntegerField(lazy_gettext(u'ADC Resolution'))
    adc_measurement = StringField(lazy_gettext(u'ADC Measurement Type'))
    adc_measurement_units = StringField(lazy_gettext(u'ADC Measurement Units'))
    adc_volts_min = DecimalField(lazy_gettext(u'Volts Min'))
    adc_volts_max = DecimalField(lazy_gettext(u'Volts Max'))
    adc_units_min = DecimalField(lazy_gettext(u'Units Min'))
    adc_units_max = DecimalField(lazy_gettext(u'Units Max'))
    switch_edge = StringField(lazy_gettext(u'Edge'))
    switch_bounce_time = IntegerField(lazy_gettext(u'Bounce Time (ms)'))
    switch_reset_period = IntegerField(lazy_gettext(u'Reset Period'))
    pre_relay_id = StringField(lazy_gettext(u'Pre Relay'))
    pre_relay_duration = DecimalField(
        lazy_gettext(u'Pre Relay Duration'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    period = DecimalField(
        lazy_gettext(u'Period'),
        validators=[DataRequired(),
                    validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    sht_clock_pin = IntegerField(
        lazy_gettext(u'Clock Pin'),
        validators=[validators.NumberRange(
            min=0,
            max=100,
            message=lazy_gettext(u"If using a SHT sensor, enter the GPIO "
                                 u"connected to the clock pin (using BCM "
                                 u"numbering).")
        )]
    )
    sht_voltage = StringField(lazy_gettext(u'Voltage'))
    modSensorSubmit = SubmitField(lazy_gettext(u'Save'))
    delSensorSubmit = SubmitField(lazy_gettext(u'Delete'))
    activateSensorSubmit = SubmitField(lazy_gettext(u'Activate'))
    deactivateSensorSubmit = SubmitField(lazy_gettext(u'Deactivate'))
    orderSensorUp = SubmitField(lazy_gettext(u'Up'))
    orderSensorDown = SubmitField(lazy_gettext(u'Down'))

    conditional_type = StringField('Conditional Type', widget=widgets.HiddenInput())
    sensorCondAddSubmit = SubmitField(lazy_gettext(u'Add Conditional'))


#
# Settings (Camera)
#

class SettingsCamera(FlaskForm):
    camera_id = IntegerField('Camera ID', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext(u'Name'))
    camera_type = StringField(lazy_gettext(u'Type'))
    library = StringField(lazy_gettext(u'Library'))
    opencv_device = IntegerField(lazy_gettext(u'OpenCV Device'))
    hflip = BooleanField(lazy_gettext(u'Flip image horizontally'))
    vflip = BooleanField(lazy_gettext(u'Flip image vertically'))
    rotation = IntegerField(lazy_gettext(u'Rotate Image'))
    height = IntegerField(lazy_gettext(u'Image Height'))
    width = IntegerField(lazy_gettext(u'Image Width'))
    brightness = DecimalField(lazy_gettext(u'Brightness'))
    contrast = DecimalField(lazy_gettext(u'Contrast'))
    exposure = DecimalField(lazy_gettext(u'Exposure'))
    gain = DecimalField(lazy_gettext(u'Gain'))
    hue = DecimalField(lazy_gettext(u'Hue'))
    saturation = DecimalField(lazy_gettext(u'Saturation'))
    white_balance = DecimalField(lazy_gettext(u'White Balance'))
    relay_id = IntegerField(lazy_gettext(u'Relay ID'))
    cmd_pre_camera = StringField(lazy_gettext(u'Pre Command'))
    cmd_post_camera = StringField(lazy_gettext(u'Post Command'))
    camera_add = SubmitField(lazy_gettext(u'Add Camera'))
    camera_mod = SubmitField(lazy_gettext(u'Save'))
    camera_del = SubmitField(lazy_gettext(u'Delete'))


#
# Settings (General)
#

class SettingsGeneral(FlaskForm):
    language = StringField(lazy_gettext(u'Language'))
    force_https = BooleanField(lazy_gettext(u'Force HTTPS'))
    hide_success = BooleanField(lazy_gettext(u'Hide success messages'))
    hide_info = BooleanField(lazy_gettext(u'Hide info messages'))
    hide_warning = BooleanField(lazy_gettext(u'Hide warning messages'))
    hide_tooltips = BooleanField(lazy_gettext(u'Hide Form Tooltips'))
    relay_stats_volts = IntegerField(lazy_gettext(u'Voltage'))
    relay_stats_cost = DecimalField(lazy_gettext(u'Cost per kWh'))
    relay_stats_currency = StringField(lazy_gettext(u'Currency Unit'))
    relay_stats_day_month = StringField(lazy_gettext(u'Day of Month'))
    relay_usage_report_gen = BooleanField(lazy_gettext(u'Generate Usage/Cost Report'))
    relay_usage_report_span = StringField(lazy_gettext(u'Time Span to Generate'))
    relay_usage_report_day = IntegerField(lazy_gettext(u'Day of Week/Month to Generate'))
    relay_usage_report_hour = IntegerField(
        lazy_gettext(u'Hour of Day to Generate'),
        validators=[validators.NumberRange(
            min=0,
            max=23,
            message=lazy_gettext(u"Hour Options: 0-23")
        )])
    stats_opt_out = BooleanField(lazy_gettext(u'Opt-out of statistics'))
    Submit = SubmitField(lazy_gettext(u'Save'))


#
# Timers
#

class Timer(FlaskForm):
    timer_id = IntegerField('Timer ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    relay_id = StringField(lazy_gettext(u'Relay ID'))
    state = SelectField(
        lazy_gettext(u'State'),
        choices=[
            ('on', lazy_gettext(u'On')),
            ('off', lazy_gettext(u'Off'))
        ],
        validators=[DataRequired()]
    )
    time_start = StringField(lazy_gettext(u'Start Time'))
    time_start_duration = StringField(lazy_gettext(u'Start Time'))
    time_end_duration = StringField(lazy_gettext(u'End Time'))
    time_on_duration = DecimalField(
        lazy_gettext(u'On (sec)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    duration_on = DecimalField(lazy_gettext(u'On (sec)'))
    duration_off = DecimalField(lazy_gettext(u'Off (sec)'))
    create = SubmitField(lazy_gettext(u'Save'))
    modify = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    activate = SubmitField(lazy_gettext(u'Activate'))
    deactivate = SubmitField(lazy_gettext(u'Deactivate'))
    order_up = SubmitField(lazy_gettext(u'Up'))
    order_down = SubmitField(lazy_gettext(u'Down'))


#
# Settings (User)
#

class UserRoles(FlaskForm):
    name = StringField(
        lazy_gettext(u'Role Name'),
        validators=[DataRequired()]
    )
    view_logs = BooleanField(lazy_gettext(u'View Logs'))
    view_stats = BooleanField(lazy_gettext(u'View Stats'))
    view_camera = BooleanField(lazy_gettext(u'View Camera'))
    view_settings = BooleanField(lazy_gettext(u'View Settings'))
    edit_users = BooleanField(lazy_gettext(u'Edit Users'))
    edit_controllers = BooleanField(lazy_gettext(u'Edit Controllers'))
    edit_settings = BooleanField(lazy_gettext(u'Edit Settings'))
    role_id = IntegerField('Role ID', widget=widgets.HiddenInput())
    add_role = SubmitField(lazy_gettext(u'Add Role'))
    save_role = SubmitField(lazy_gettext(u'Save'))
    delete_role = SubmitField(lazy_gettext(u'Delete'))


class UserAdd(FlaskForm):
    user_name = StringField(
        lazy_gettext(u'Username'),
        validators=[DataRequired()]
    )
    email = EmailField(
        lazy_gettext(u'Email'),
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    password_new = PasswordField(
        lazy_gettext(u'Password'),
        validators=[
            DataRequired(),
            validators.EqualTo('password_repeat',
                               message=lazy_gettext(u'Passwords must match')),
            validators.Length(
                min=6,
                message=lazy_gettext(u'Password must be 6 or more characters')
            )
        ]
    )
    password_repeat = PasswordField(
        lazy_gettext(u'Repeat Password'),
        validators=[DataRequired()]
    )
    addRole = StringField(
        lazy_gettext(u'Role'),
        validators=[DataRequired()]
    )
    theme = StringField(
        lazy_gettext(u'Theme'),
        validators=[DataRequired()]
    )
    add_user = SubmitField(lazy_gettext(u'Add User'))


class UserMod(FlaskForm):
    user_id = IntegerField('User ID', widget=widgets.HiddenInput())
    email = EmailField(
        lazy_gettext(u'Email'),
        render_kw={"placeholder": lazy_gettext(u"Email")},
        validators=[
            DataRequired(),
            validators.Email()])
    password_new = PasswordField(
        lazy_gettext(u'Password'),
        render_kw={"placeholder": lazy_gettext(u"New Password")},
        validators=[
            validators.Optional(),
            validators.EqualTo(
                'password_repeat',
                message=lazy_gettext(u'Passwords must match')
            ),
            validators.Length(
                min=6,
                message=lazy_gettext(u'Password must be 6 or more characters')
            )
        ]
    )
    password_repeat = PasswordField(
        lazy_gettext(u'Repeat Password'),
        render_kw={"placeholder": lazy_gettext(u"Repeat Password")}
    )
    role = StringField(
        lazy_gettext(u'Role'),
        validators=[DataRequired()]
    )
    theme = StringField(lazy_gettext(u'Theme'))
    save = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))


class InstallNotice(FlaskForm):
    acknowledge = SubmitField(lazy_gettext(u'I Understand'))


#
# Upgrade
#

class Upgrade(FlaskForm):
    upgrade = SubmitField(lazy_gettext(u'Upgrade Mycodo'))


#
# Backup/Restore
#

class Backup(FlaskForm):
    backup = SubmitField(lazy_gettext(u'Create Backup'))
    restore = SubmitField(lazy_gettext(u'Restore Backup'))
    delete = SubmitField(lazy_gettext(u'Delete Backup'))
    full_path = HiddenField()
    selected_dir = HiddenField()
