# -*- coding: utf-8 -*-
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    SubmitField,
    StringField,
    validators,
    widgets
)
from wtforms.validators import DataRequired
from wtforms.validators import Optional
from wtforms.fields.html5 import EmailField


#
# Method (Date)
#

class CreateMethod(FlaskForm):
    name = StringField(
        'Name',
        render_kw={"placeholder": "Name"}
    )
    method_type = StringField(
        'Method Type',
        render_kw={"placeholder": ""}
    )
    controller_type = HiddenField('Controller Type')
    Submit = SubmitField(lazy_gettext('Create New Method'))


class AddMethod(FlaskForm):
    method_id = IntegerField(
        lazy_gettext('Method ID'),
        widget=widgets.HiddenInput()
    )
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
    startDailyTime = StringField(
        lazy_gettext('Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    endDailyTime = StringField(
        lazy_gettext('End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    startTime = StringField(
        lazy_gettext('Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    endTime = StringField(
        lazy_gettext('End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    startSetpoint = DecimalField(lazy_gettext('Start Setpoint'))
    endSetpoint = DecimalField(lazy_gettext('End Setpoint (optional)'))
    DurationSec = IntegerField(lazy_gettext('Duration (seconds)'))
    amplitude = DecimalField(lazy_gettext('Amplitude'))
    frequency = DecimalField(lazy_gettext('Frequency'))
    shiftAngle = DecimalField(lazy_gettext('Angle Shift (0 to 360)'))
    shiftY = DecimalField(lazy_gettext('Y-Axis Shift'))
    x0 = DecimalField('X0')
    y0 = DecimalField('Y0')
    x1 = DecimalField('X1')
    y1 = DecimalField('Y1')
    x2 = DecimalField('X2')
    y2 = DecimalField('Y2')
    x3 = DecimalField('X3')
    y3 = DecimalField('Y3')
    relayDailyTime = StringField(
        lazy_gettext('Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relayTime = StringField(
        lazy_gettext('Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relayDurationSec = IntegerField(
        lazy_gettext('Duration On (sec)'),
        render_kw={"placeholder": ""}
    )
    relayID = StringField(
        lazy_gettext('Relay ID'),
        render_kw={"placeholder": ""}
    )
    relayState = SelectField(
        lazy_gettext('Relay State'),
        choices=[
            ('', ''),
            ('On', 'Turn On'),
            ('Off', 'Turn Off')
        ]
    )
    save = SubmitField(lazy_gettext('Add to Method'))


class ModMethod(FlaskForm):
    method_id = HiddenField('Method ID')
    method_data_id = HiddenField('Method Data ID')
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
    name = StringField(lazy_gettext('Name'))
    startDailyTime = StringField(
        lazy_gettext('Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    endDailyTime = StringField(
        lazy_gettext('End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    startTime = StringField(
        lazy_gettext('Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    endTime = StringField(
        lazy_gettext('End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relayDailyTime = StringField(
        lazy_gettext('Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relayTime = StringField(
        lazy_gettext('Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    DurationSec = IntegerField(lazy_gettext('Duration (seconds)'))
    startSetpoint = DecimalField(lazy_gettext('Start Setpoint'))
    endSetpoint = DecimalField(lazy_gettext('End Setpoint'))
    relayID = StringField(lazy_gettext('Relay'))
    relayState = StringField(lazy_gettext('Relay State'))
    relayDurationSec = IntegerField(lazy_gettext('Relay On Duration (sec)'))
    rename = SubmitField(lazy_gettext('Rename'))
    save = SubmitField(lazy_gettext('Save'))
    Delete = SubmitField(lazy_gettext('Delete'))


#
# Remote Admin add servers
#

class RemoteSetup(FlaskForm):
    remote_id = HiddenField('Remote Host ID')
    host = StringField(
        lazy_gettext('Domain or IP Address'),
        render_kw={"placeholder": "youraddress.com or 0.0.0.0"},
        validators=[DataRequired()]
    )
    username = StringField(
        lazy_gettext('Username'),
        render_kw={"placeholder": "Username"},
        validators=[DataRequired()]
    )
    password = PasswordField(
        lazy_gettext('Password'),
        render_kw={"placeholder": "Password"},
        validators=[DataRequired()]
    )
    add = SubmitField(lazy_gettext('Add Host'))
    delete = SubmitField(lazy_gettext('Delete Host'))


#
# Tools/Log View
#

class LogView(FlaskForm):
    lines = IntegerField(
        lazy_gettext('Number of Lines'),
        render_kw={'placeholder': lazy_gettext('Lines')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext('Number of lines should be greater than 0.')
        )]
    )
    loglogin = SubmitField(lazy_gettext('Login Log'))
    loghttp = SubmitField(lazy_gettext('HTTP Log'))
    logdaemon = SubmitField(lazy_gettext('Daemon Log'))
    logupgrade = SubmitField(lazy_gettext('Upgrade Log'))
    logrestore = SubmitField(lazy_gettext('Restore Log'))


#
# Daemon Control
#

class DaemonControl(FlaskForm):
    stop = SubmitField(lazy_gettext('Stop Daemon'))
    start = SubmitField(lazy_gettext('Start Daemon'))
    restart = SubmitField(lazy_gettext('Restart Daemon'))


#
# Camera Use
#

class Camera(FlaskForm):
    camera_id = HiddenField('Camera ID')
    capture_still = SubmitField(lazy_gettext('Capture Still'))
    start_timelapse = SubmitField(lazy_gettext('Start Timelapse'))
    pause_timelapse = SubmitField(lazy_gettext('Pause Timelapse'))
    resume_timelapse = SubmitField(lazy_gettext('Resume Timelapse'))
    stop_timelapse = SubmitField(lazy_gettext('Stop Timelapse'))
    timelapse_interval = DecimalField(
        lazy_gettext('Photo Interval (sec)'),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext('Photo Interval must be a positive value.')
        )]
    )
    timelapse_runtime_sec = DecimalField(
        lazy_gettext('Total Run Time (sec)'),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext('Total Run Time must be a positive value.')
        )]
    )
    start_stream = SubmitField(lazy_gettext('Start Stream'))
    stop_stream = SubmitField(lazy_gettext('Stop Stream'))


#
# Alerts
#

class EmailAlert(FlaskForm):
    smtpHost = StringField(
        lazy_gettext('SMTP Host'),
        render_kw={"placeholder": lazy_gettext('SMTP Host')},
        validators=[DataRequired()]
    )
    smtpPort = IntegerField(
        lazy_gettext('SMTP Port'),
        render_kw={"placeholder": lazy_gettext('SMTP Port')},
        validators=[validators.NumberRange(
            min=1,
            max=65535,
            message=lazy_gettext('Port should be between 1 and 65535')
        )]
    )
    sslEnable = BooleanField('Enable SSL')
    smtpUser = StringField(
        lazy_gettext('SMTP User'),
        render_kw={"placeholder": lazy_gettext('SMTP User')},
        validators=[DataRequired()]
    )
    smtpPassword = PasswordField(
        lazy_gettext('SMTP Password'),
        render_kw={"placeholder": lazy_gettext('Password')}
    )
    smtpFromEmail = EmailField(
        lazy_gettext('From Email'),
        render_kw={"placeholder": lazy_gettext('Email')},
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    smtpMaxPerHour = IntegerField(
        lazy_gettext('Max emails (per hour)'),
        render_kw={"placeholder": lazy_gettext('Max emails (per hour)')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext('Must have at least one message able to be '
                                 'sent per hour.')
        )]
    )
    sendTestEmail = SubmitField('Send Test Email')
    testEmailTo = EmailField(
        lazy_gettext('Test Email To'),
        render_kw={"placeholder": lazy_gettext('To Email Address')},
        validators=[
            validators.Email(),
            validators.Optional()
        ]
    )
    smtpSubmit = SubmitField('Save')


#
# General Settings
#

class SettingsGeneral(FlaskForm):
    language = StringField(lazy_gettext('Language'))
    forceHTTPS = BooleanField(lazy_gettext('Force HTTPS'))
    hideAlertSuccess = BooleanField(lazy_gettext('Hide success messages'))
    hideAlertInfo = BooleanField(lazy_gettext('Hide info messages'))
    relayStatsVolts = IntegerField(lazy_gettext('Voltage'))
    relayStatsCost = DecimalField(lazy_gettext('Cost per kWh'))
    relayStatsCurrency = StringField(lazy_gettext('Currency Unit'))
    relayStatsDayOfMonth = StringField(lazy_gettext('Billing Day of Month (1-30)'))
    hideAlertWarning = BooleanField(lazy_gettext('Hide warning messages'))
    stats_opt_out = BooleanField(lazy_gettext('Opt-out of sending statistics'))
    Submit = SubmitField(lazy_gettext('Save'))


#
# User Settings
#

class AddUser(FlaskForm):
    addUsername = StringField(
        lazy_gettext('Username'),
        render_kw={"placeholder": lazy_gettext("Username")},
        validators=[DataRequired()]
    )
    addEmail = EmailField(
        lazy_gettext('Email'),
        render_kw={"placeholder": lazy_gettext("Email")},
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    addPassword = PasswordField(
        lazy_gettext('Password'),
        render_kw={"placeholder": lazy_gettext("Password")},
        validators=[
            DataRequired(),
            validators.EqualTo('addPassword_repeat',
                               message=lazy_gettext('Passwords must match')),
            validators.Length(
                min=6,
                message=lazy_gettext('Password must be 6 or more characters')
            )
        ]
    )
    addPassword_repeat = PasswordField(
        lazy_gettext('Repeat Password'),
        render_kw={"placeholder": lazy_gettext("Repeat Password")},
        validators=[DataRequired()]
    )
    addGroup = StringField(
        lazy_gettext('Group'),
        validators=[DataRequired()]
    )
    addSubmit = SubmitField(lazy_gettext('Submit'))


class ModUser(FlaskForm):
    modUsername = HiddenField('Username')
    modEmail = EmailField(
        lazy_gettext('Email'),
        render_kw={"placeholder": lazy_gettext("Email")},
        validators=[
            DataRequired(),
            validators.Email()])
    modPassword = PasswordField(
        lazy_gettext('Password'),
        render_kw={"placeholder": lazy_gettext("New Password")},
        validators=[
            validators.Optional(),
            validators.EqualTo(
                'modPassword_repeat',
                message=lazy_gettext('Passwords must match')
            ),
            validators.Length(
                min=6,
                message=lazy_gettext('Password must be 6 or more characters')
            )
        ]
    )
    modPassword_repeat = PasswordField(
        lazy_gettext('Repeat Password'),
        render_kw={"placeholder": lazy_gettext("Repeat Password")}
    )
    modGroup = StringField(
        lazy_gettext('Group'),
        validators=[DataRequired()]
    )
    modTheme = StringField(lazy_gettext('Theme'))
    modSubmit = SubmitField(lazy_gettext('Submit'))


class DelUser(FlaskForm):
    delUsername = HiddenField('Username')
    delUserSubmit = SubmitField(lazy_gettext('Delete'))


#
# Camera Options
#

class SettingsCamera(FlaskForm):
    camera_id = HiddenField(lazy_gettext('Camera ID'))
    name = StringField(lazy_gettext('Name'))
    camera_type = StringField(lazy_gettext('Type'))
    library = StringField(lazy_gettext('Library'))
    opencv_device = IntegerField(lazy_gettext('OpenCV Device'))
    hflip = BooleanField(lazy_gettext('Flip image horizontally'))
    vflip = BooleanField(lazy_gettext('Flip image vertically'))
    rotation = IntegerField(lazy_gettext('Rotate image (degrees)'))
    height = IntegerField(lazy_gettext('Image Height'))
    width = IntegerField(lazy_gettext('Image width'))
    brightness = DecimalField(lazy_gettext('Brightness'))
    contrast = DecimalField(lazy_gettext('Contrast'))
    exposure = DecimalField(lazy_gettext('Exposure'))
    gain = DecimalField(lazy_gettext('Gain'))
    hue = DecimalField(lazy_gettext('Hue'))
    saturation = DecimalField(lazy_gettext('Saturation'))
    white_balance = DecimalField(lazy_gettext('White Balance'))
    relay_id = IntegerField(lazy_gettext('Relay ID'))
    cmd_pre_camera = StringField(lazy_gettext('Pre Command'))
    cmd_post_camera = StringField(lazy_gettext('Post Command'))
    camera_add = SubmitField(lazy_gettext('Add Camera'))
    camera_mod = SubmitField(lazy_gettext('Save'))
    camera_del = SubmitField(lazy_gettext('Delete'))


#
# Export Options
#

class ExportOptions(FlaskForm):
    measurement = StringField(lazy_gettext('Measurement to Export'))
    date_range = StringField(lazy_gettext('Time Range DD/MM/YYYY HH:MM'))
    Export = SubmitField(lazy_gettext('Export'))


#
# Graphs
#

class AddGraph(FlaskForm):
    name = StringField(
        lazy_gettext('Graph Name'),
        render_kw={"placeholder": lazy_gettext("Graph Name")},
        validators=[DataRequired()]
    )
    pidIDs = SelectMultipleField(
        lazy_gettext('PID IDs (Setpoint)'),
        coerce=int
    )
    relayIDs = SelectMultipleField(
        lazy_gettext('Relay IDs'),
        coerce=int
    )
    sensorIDs = SelectMultipleField(
        lazy_gettext('Sensor IDs')
    )
    width = IntegerField(
        lazy_gettext('Width (%)'),
        render_kw={"placeholder": lazy_gettext("Percent Width")},
        validators=[validators.NumberRange(
            min=10,
            max=100
        )]
    )
    height = IntegerField(
        lazy_gettext('Height (pixels)'),
        render_kw={"placeholder": lazy_gettext("Percent Height")},
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xAxisDuration = IntegerField(
        lazy_gettext('x-Axis (minutes)'),
        render_kw={"placeholder": lazy_gettext("X-Axis Duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext("Number of minutes to display of past "
                                 "measurements.")
        )]
    )
    refreshDuration = IntegerField(
        lazy_gettext('Refresh (seconds)'),
        render_kw={"placeholder": lazy_gettext("Refresh duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext("Number of seconds to wait between acquiring"
                                 " any new measurements.")
        )]
    )
    enableNavbar = BooleanField(lazy_gettext('Enable Navbar'))
    enableExport = BooleanField(lazy_gettext('Enable Export'))
    enableRangeSelect = BooleanField(lazy_gettext('Enable Range Selector'))
    Submit = SubmitField(lazy_gettext('Create Graph'))


class ModGraph(FlaskForm):
    graph_id = IntegerField(
        lazy_gettext('Graph ID'),
        widget=widgets.HiddenInput()
    )
    name = StringField(
        lazy_gettext('Graph Name'),
        render_kw={"placeholder": lazy_gettext("Graph Name")},
        validators=[DataRequired()]
    )
    pidIDs = SelectMultipleField(
        lazy_gettext('PID IDs (Setpoint)'),
        coerce=int
    )
    relayIDs = SelectMultipleField(
        lazy_gettext('Relay IDs'),
        coerce=int
    )
    sensorIDs = SelectMultipleField(
        lazy_gettext('Sensor IDs')
    )
    width = IntegerField(
        lazy_gettext('Width (%)'),
        render_kw={"placeholder": lazy_gettext("Percent Width")},
        validators=[validators.NumberRange(
            min=10,
            max=100
        )]
    )
    height = IntegerField(
        lazy_gettext('Height (pixels)'),
        render_kw={"placeholder": lazy_gettext("Percent Height")},
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xAxisDuration = IntegerField(
        lazy_gettext('x-Axis (min)'),
        render_kw={"placeholder": lazy_gettext("X-Axis Duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext("Number of minutes to display of past "
                                 "measurements.")
        )]
    )
    refreshDuration = IntegerField(
        lazy_gettext('Refresh (seconds)'),
        render_kw={"placeholder": lazy_gettext("Refresh duration")},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext("Number of seconds to wait between acquiring"
                                 " any new measurements.")
        )]
    )
    enableNavbar = BooleanField(lazy_gettext('Enable Navbar'))
    enableExport = BooleanField(lazy_gettext('Enable Export'))
    enableRangeSelect = BooleanField(lazy_gettext('Enable Range Selector'))
    use_custom_colors = BooleanField(lazy_gettext('Enable Custom Colors'))
    Submit = SubmitField(lazy_gettext('Save Graph'))


class DelGraph(FlaskForm):
    graph_id = HiddenField('Graph ID')
    Submit = SubmitField(lazy_gettext('Delete Graph'))


class OrderGraph(FlaskForm):
    orderGraph_id = HiddenField('Graph')
    orderGraphUp = SubmitField(lazy_gettext('Up'))
    orderGraphDown = SubmitField(lazy_gettext('Down'))


#
# LCDs
#

class AddLCD(FlaskForm):
    numberLCDs = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    lcdAddSubmit = SubmitField(lazy_gettext('Add LCDs'))


class ModLCD(FlaskForm):
    lcd_id = IntegerField(
        lazy_gettext('LCD ID'),
        widget=widgets.HiddenInput()
    )
    name = StringField(
        lazy_gettext('Name'),
        render_kw={"placeholder": lazy_gettext("Name")},
        validators=[DataRequired()]
    )
    location = StringField(
        lazy_gettext('I2C Address'),
        render_kw={"placeholder": lazy_gettext("I2C Address")},
        validators=[DataRequired()]
    )
    multiplexer_address = StringField(
        lazy_gettext('Multiplexer I2C Address'),
        render_kw={"placeholder": lazy_gettext("I2C Address")}
    )
    multiplexer_channel = IntegerField(
        lazy_gettext('Multiplexer Channel'),
        render_kw={"placeholder": lazy_gettext("Channel")},
        validators=[
            validators.NumberRange(
                min=0,
                max=8
            )]
    )
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        render_kw={"placeholder": lazy_gettext("Period")},
        validators=[validators.NumberRange(
            min=5,
            max=86400,
            message=lazy_gettext("Duration between calculating LCD output "
                                 "and applying to regulation must be between "
                                 "5 and 86400 seconds.")
        )]
    )
    lcd_type = SelectField(
        lazy_gettext('LCD Type'),
        choices=[
            ('16x2', '16x2'),
            ('20x4', '20x4')
        ],
        validators=[DataRequired()]
    )
    line_1_display = StringField(
        lazy_gettext('Line 1 Sensor ID')
    )
    line_2_display = StringField(
        lazy_gettext('Line 2 Sensor ID')
    )
    line_3_display = StringField(
        lazy_gettext('Line 3 Sensor ID')
    )
    line_4_display = StringField(
        lazy_gettext('Line 4 Sensor ID')
    )
    save = SubmitField(lazy_gettext('Save'))


class DelLCD(FlaskForm):
    lcd_id = HiddenField('LCD ID')
    delete = SubmitField(lazy_gettext('Delete'))


class ActivateLCD(FlaskForm):
    lcd_id = HiddenField('LCD ID')
    activate = SubmitField(lazy_gettext('Activate'))


class DeactivateLCD(FlaskForm):
    lcd_id = HiddenField('LCD ID')
    deactivate = SubmitField(lazy_gettext('Deactivate'))


class OrderLCD(FlaskForm):
    lcd_id = HiddenField('LCD ID')
    reorder_up = SubmitField(lazy_gettext('Up'))
    reorder_down = SubmitField(lazy_gettext('Down'))


class ResetFlashingLCD(FlaskForm):
    lcd_id = HiddenField('LCD ID')
    Submit = SubmitField(lazy_gettext('Reset Flashing'))


#
# Create Admin
#

class CreateAdmin(FlaskForm):
    username = StringField(
        lazy_gettext('Username'),
        render_kw={"placeholder": lazy_gettext("Username")},
        validators=[DataRequired()]
    )
    email = StringField(
        lazy_gettext('Email'),
        render_kw={"placeholder": lazy_gettext("Email")},
        validators=[DataRequired()]
    )
    password = PasswordField(
        lazy_gettext('Password'),
        render_kw={"placeholder": lazy_gettext("Password")},
        validators=[DataRequired()]
    )
    password_repeat = PasswordField(
        lazy_gettext('Repeat Password'),
        render_kw={"placeholder": lazy_gettext("Repeat Password")},
        validators=[DataRequired()]
    )


#
# Login
#

class Login(FlaskForm):
    username = StringField(
        lazy_gettext('Username'),
        render_kw={"placeholder": lazy_gettext("Username")},
        validators=[DataRequired()]
    )
    password = PasswordField(
        lazy_gettext('Password'),
        render_kw={"placeholder": lazy_gettext("Password")},
        validators=[DataRequired()]
    )
    remember = BooleanField(lazy_gettext('remember'))


class InstallNotice(FlaskForm):
    acknowledge = SubmitField(lazy_gettext('I Understand'))


#
# PIDs
#

class AddPID(FlaskForm):
    numberPIDs = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    pidAddSubmit = SubmitField(lazy_gettext('Add PIDs'))


class ModPID(FlaskForm):
    pid_id = IntegerField(
        lazy_gettext('PID ID'),
        widget=widgets.HiddenInput()
    )
    name = StringField(
        lazy_gettext('Name'),
        render_kw={"placeholder": lazy_gettext("Name")},
        validators=[DataRequired()]
    )
    sensor_id = StringField(
        lazy_gettext('Sensor ID'),
        render_kw={"placeholder": lazy_gettext("Sensor ID")},
        validators=[DataRequired()]
    )
    measurement = StringField(
        lazy_gettext('Measure Type'),
        validators=[DataRequired()]
    )
    direction = SelectField(
        lazy_gettext('Direction'),
        choices=[
            ('raise', 'Raise'),
            ('lower', 'Lower'),
            ('both', 'Both')
        ],
        validators=[DataRequired()]
    )
    period = DecimalField(
        lazy_gettext('Period (sec)'),
        render_kw={"placeholder": lazy_gettext("Period")},
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    max_measure_age = DecimalField(
        lazy_gettext('Max Age (sec)'),
        render_kw={"placeholder": lazy_gettext("Max Age")},
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    setpoint = DecimalField(
        lazy_gettext('Setpoint'),
        render_kw={"placeholder": "Setpoint"},
        validators=[validators.NumberRange(
            min=-1000000,
            max=1000000
        )]
    )
    k_p = DecimalField(
        lazy_gettext('Kp Gain'),
        render_kw={"placeholder": lazy_gettext("Kp Gain")},
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_i = DecimalField(
        lazy_gettext('Ki Gain'),
        render_kw={"placeholder": lazy_gettext("Ki Gain")},
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_d = DecimalField(
        lazy_gettext('Kd Gain'),
        render_kw={"placeholder": lazy_gettext("Kd Gain")},
        validators=[validators.NumberRange(
            min=0
        )]
    )
    integrator_max = DecimalField(lazy_gettext('Integrator Min'))
    integrator_min = DecimalField(lazy_gettext('Integrator Max'))
    raise_relay_id = StringField(
        lazy_gettext('Raise Relay ID'),
        render_kw={"placeholder": lazy_gettext("Raise Relay ID")},
    )
    raise_min_duration = DecimalField(
        lazy_gettext('Raise Min On Duration'),
        render_kw={"placeholder": lazy_gettext("Raise Min On Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_max_duration = DecimalField(
        lazy_gettext('Raise Max On Duration'),
        render_kw={"placeholder": lazy_gettext("Raise Max On Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_min_off_duration = DecimalField(
        lazy_gettext('Raise Min Off Duration'),
        render_kw={"placeholder": lazy_gettext("Raise Min Off Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_relay_id = StringField(
        lazy_gettext('Lower Relay ID'),
        render_kw={"placeholder": lazy_gettext("Lower Relay ID")},
    )
    lower_min_duration = DecimalField(
        lazy_gettext('Lower Min On Duration'),
        render_kw={"placeholder": lazy_gettext("Lower Min On Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_max_duration = DecimalField(
        lazy_gettext('Lower Max On Duration'),
        render_kw={"placeholder": lazy_gettext("Lower Max On Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_min_off_duration = DecimalField(
        lazy_gettext('Lower Min Off Duration'),
        render_kw={"placeholder": lazy_gettext("Lower Min Off Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    method_id = HiddenField('Setpoint Tracking Method')
    save = SubmitField(lazy_gettext('Save Settings'))
    hold = SubmitField(lazy_gettext('Hold'))
    pause = SubmitField(lazy_gettext('Pause'))
    resume = SubmitField(lazy_gettext('Resume'))
    delete = SubmitField(lazy_gettext('Delete PID'))
    activate = SubmitField(lazy_gettext('Activate PID'))
    deactivate = SubmitField(lazy_gettext('Deactivate PID'))
    reorder_up = SubmitField(lazy_gettext('Order Up'))
    reorder_down = SubmitField(lazy_gettext('Order Down'))


#
# Relays
#

class AddRelay(FlaskForm):
    relay_quantity = IntegerField(lazy_gettext('Quantity'))
    relay_add = SubmitField(lazy_gettext('Add Relay'))
    relay_cond_quantity = IntegerField(lazy_gettext('Quantity'))
    relay_cond_add = SubmitField(lazy_gettext('Add Conditionals'))


class ModRelay(FlaskForm):
    relay_id = IntegerField(
        lazy_gettext('Relay ID'),
        widget=widgets.HiddenInput()
    )
    relay_pin = HiddenField('Relay Pin')
    name = StringField(
        lazy_gettext('Name'),
        render_kw={"placeholder": lazy_gettext("Name")},
        validators=[DataRequired()]
    )
    gpio = IntegerField(
        lazy_gettext('GPIO Pin (BCM)'),
        render_kw={"placeholder": lazy_gettext("GPIO")},
        validators=[validators.NumberRange(
            min=0,
            max=27,
            message=lazy_gettext("GPIO pin, using BCM numbering, between 1 and 27 "
                                 "(0 to disable)")
        )]
    )
    amps = DecimalField(
        lazy_gettext('Current Draw (amps)'),
        render_kw={"placeholder": lazy_gettext("Amps")},
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message=lazy_gettext("The current draw of the device connected "
                                 "to this relay, in amps.")
        )]
    )
    trigger = SelectField(
        lazy_gettext('On Trigger'),
        choices=[
            ("1", 'High'),
            ("0", 'Low')
        ],
        validators=[DataRequired()]
    )
    on_at_start = SelectField(
        lazy_gettext('Start State'),
        choices=[
            ("1", 'On'),
            ("0", 'Off')
        ],
        validators=[DataRequired()]
    )
    save = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))
    order_up = SubmitField(lazy_gettext('Up'))
    order_down = SubmitField(lazy_gettext('Down'))
    turn_on = SubmitField(lazy_gettext('On'))
    turn_off = SubmitField(lazy_gettext('Off'))
    sec_on = DecimalField(
        lazy_gettext('Seconds to turn on'),
        validators=[Optional()]
    )
    sec_on_submit = SubmitField(lazy_gettext('Turn On'))


class ModRelayConditional(FlaskForm):
    relay_id = IntegerField(
        lazy_gettext('Relay Conditional ID'),
        widget=widgets.HiddenInput()
    )
    name = StringField(
        lazy_gettext('Name'),
        render_kw={"placeholder": lazy_gettext("Name")}
    )
    if_relay_id = StringField(
        lazy_gettext('If Relay ID')
    )
    if_relay_action = StringField(
        lazy_gettext('If Action')
    )
    if_relay_duration = DecimalField(
        lazy_gettext('If Relay Duration'),
        render_kw={"placeholder": lazy_gettext("Duration")}
    )
    do_action = StringField(
        lazy_gettext('Action')
    )

    do_relay_id = StringField(
        lazy_gettext('Do Relay ID')
    )
    do_relay_action = StringField(
        lazy_gettext('Do Action')
    )
    do_relay_action_command = StringField(
        lazy_gettext('Do Action Command(s)')
    )
    do_relay_duration = DecimalField(
        lazy_gettext('Do Relay Duration'),
        render_kw={"placeholder": lazy_gettext("Duration")}
    )
    do_execute = StringField(
        lazy_gettext('Execute Command'),
        render_kw={"placeholder": lazy_gettext("Command")}
    )
    do_notify = StringField(
        lazy_gettext('Notify by Email'),
        render_kw={"placeholder": lazy_gettext("Email")}
    )
    do_flash_lcd = StringField(
        lazy_gettext('Flash LCD'),
        render_kw={"placeholder": lazy_gettext("LCD")}
    )
    activate = SubmitField(lazy_gettext('Activate'))
    deactivate = SubmitField(lazy_gettext('Deactivate'))
    add_action = SubmitField(lazy_gettext('Add Action'))
    save = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))


#
# Master Conditional Form
#

class Conditional(FlaskForm):
    conditional_id = IntegerField(
        lazy_gettext('Conditional ID'),
        widget=widgets.HiddenInput()
    )
    quantity = IntegerField(lazy_gettext('Quantity'))
    name = StringField(lazy_gettext('Name'))
    conditional_type = StringField(
        lazy_gettext('Conditional Type'),
        widget=widgets.HiddenInput()
    )
    sensor_id = IntegerField(
        lazy_gettext('Sensor ID'),
        widget=widgets.HiddenInput()
    )

    # Relay conditional options
    if_relay_id = StringField(lazy_gettext('If Relay ID'))
    if_relay_state = StringField(lazy_gettext('If Relay State'))
    if_relay_duration = DecimalField(lazy_gettext('If Relay Duration'))

    # Sensor conditional options
    if_sensor_period = DecimalField(lazy_gettext('Period (sec)'))
    if_sensor_measurement = StringField(lazy_gettext('Measurement'))
    if_sensor_edge_select = StringField(lazy_gettext('Edge or State'))
    if_sensor_edge_detected = StringField(lazy_gettext('Edge Detected'))
    if_sensor_gpio_state = IntegerField(lazy_gettext('GPIO State'))
    if_sensor_direction = StringField(lazy_gettext('Direction'))
    if_sensor_setpoint = DecimalField(lazy_gettext('Setpoint'))

    add_cond = SubmitField(lazy_gettext('Add Conditional'))
    save_cond = SubmitField(lazy_gettext('Save'))
    delete_cond = SubmitField(lazy_gettext('Delete'))
    activate_cond = SubmitField(lazy_gettext('Activate'))
    deactivate_cond = SubmitField(lazy_gettext('Deactivate'))


class ConditionalActions(FlaskForm):
    conditional_id = IntegerField(
        lazy_gettext('Conditional ID'),
        widget=widgets.HiddenInput()
    )
    do_action = StringField(lazy_gettext('Action to Perform'))
    do_action_string = StringField(lazy_gettext('Action String'))
    do_relay_id = IntegerField(lazy_gettext('Relay'))
    do_relay_state = StringField(lazy_gettext('Relay State'))
    do_relay_duration = DecimalField(lazy_gettext('Duration (sec)'))
    do_camera_id = IntegerField(lazy_gettext('Camera'))
    do_camera_duration = DecimalField(lazy_gettext('Duration (sec)'))
    do_lcd_id = IntegerField(lazy_gettext('LCD ID'))
    add_action = SubmitField(lazy_gettext('Add Action'))
    save_action = SubmitField(lazy_gettext('Save'))
    delete_action = SubmitField(lazy_gettext('Delete'))


#
# Sensors
#

class AddSensor(FlaskForm):
    numberSensors = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    sensor = SelectField(
        lazy_gettext('Sensor'),
        choices=[
            ('RPi', 'Raspberry Pi CPU Temperature'),
            ('RPiCPULoad', 'Raspberry Pi CPU Load'),
            ('RPiFreeSpace', 'Raspberry Pi Free Disk Space'),
            ('ADS1x15', 'Analog-to-Digital Converter: ADS1x15'),
            ('MCP342x', 'Analog-to-Digital Converter: MCP342x'),
            ('EDGE', 'Edge Detection: Simple Switch'),
            ('K30', 'CO2: K30'),
            ('TSL2561', 'Luminance: TSL2561'),
            ('CHIRP', 'Moisture: Chirp'),
            ('BME280', 'Pressure: BME 280'),
            ('BMP', 'Pressure: BMP 180/085'),
            ('DS18B20', 'Temperature: DS18B20'),
            ('TMP006', 'Temperature (Contactless): TMP 006/007'),
            ('ATLAS_PT1000', 'Temperature: Atlas Scientific, PT-1000'),
            ('AM2315', 'Temperature/Humidity: AM2315'),
            ('DHT11', 'Temperature/Humidity: DHT11'),
            ('DHT22', 'Temperature/Humidity: DHT22'),
            ('HTU21D', 'Temperature/Humidity: HTU21D'),
            ('SHT1x_7x', 'Temperature/Humidity: SHT 10/11/15/71/75'),
            ('SHT2x', 'Temperature/Humidity: SHT 21/25')
        ],
        validators=[DataRequired()]
    )
    sensorAddSubmit = SubmitField(lazy_gettext('Add Device'))


class ModSensor(FlaskForm):
    modSensor_id = IntegerField(
        lazy_gettext('Sensor ID'),
        widget=widgets.HiddenInput()
    )
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    modBus = IntegerField(lazy_gettext('I<sup>2</sup>C Bus'))
    location = StringField(lazy_gettext('Location'))
    modPowerPin = IntegerField(lazy_gettext('Power Pin'))
    modPowerState = IntegerField(lazy_gettext('Power On State'))
    multiplexer_address = StringField(lazy_gettext('Multiplexer (MX)'))
    modMultiplexBus = StringField(lazy_gettext('Mx I<sup>2</sup>C Bus'))
    multiplexer_channel = IntegerField(lazy_gettext('Mx Channel'))
    modADCChannel = IntegerField(lazy_gettext('ADC Channel'))
    modADCGain = IntegerField(lazy_gettext('ADC Gain'))
    modADCResolution = IntegerField(lazy_gettext('ADC Resolution'))
    modADCMeasure = StringField(lazy_gettext('ADC Measurement Type'))
    modADCMeasureUnits = StringField(lazy_gettext('ADC Measurement Units'))
    modADCVoltsMin = DecimalField(lazy_gettext('Volts Min'))
    modADCVoltsMax = DecimalField(lazy_gettext('Volts Max'))
    modADCUnitsMin = DecimalField(lazy_gettext('Units Min'))
    modADCUnitsMax = DecimalField(lazy_gettext('Units Max'))
    modSwitchEdge = StringField(lazy_gettext('Edge'))
    modSwitchBounceTime = IntegerField(lazy_gettext('Bounce Time (milliseconds)'))
    modSwitchResetPeriod = IntegerField(lazy_gettext('Reset Period (seconds)'))
    modPreRelayID = StringField(lazy_gettext('Pre Relay'))
    modPreRelayDuration = DecimalField(
        lazy_gettext('Pre Relay Duration (sec)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    period = DecimalField(
        lazy_gettext('Read Period (seconds)'),
        validators=[DataRequired(),
                    validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    modSHTClockPin = IntegerField(
        lazy_gettext('Clock Pin'),
        validators=[validators.NumberRange(
            min=0,
            max=100,
            message=lazy_gettext("If using a SHT sensor, enter the GPIO "
                                 "connected to the clock pin (using BCM "
                                 "numbering).")
        )]
    )
    modSHTVoltage = StringField(lazy_gettext('Voltage'))
    modSensorSubmit = SubmitField(lazy_gettext('Save'))
    delSensorSubmit = SubmitField(lazy_gettext('Delete'))
    activateSensorSubmit = SubmitField(lazy_gettext('Activate'))
    deactivateSensorSubmit = SubmitField(lazy_gettext('Deactivate'))
    orderSensorUp = SubmitField(lazy_gettext('Up'))
    orderSensorDown = SubmitField(lazy_gettext('Down'))
    sensorCondAddSubmit = SubmitField(lazy_gettext('Add Conditional'))


#
# Sensor Conditionals
#

class ModSensorConditional(FlaskForm):
    modCondSensor_id = IntegerField(
        lazy_gettext('Conditional ID'),
        widget=widgets.HiddenInput()
    )
    modSensor_id = IntegerField(
        lazy_gettext('Sensor ID'),
        widget=widgets.HiddenInput()
    )
    modCondName = StringField(lazy_gettext('Name'))
    Period = DecimalField(
        lazy_gettext('Period (sec)'),
        validators=[validators.NumberRange(
            min=0.0
        )]
    )
    MeasureType = StringField(lazy_gettext('Measurement Type'))
    EdgeSelect = StringField(lazy_gettext('Edge or State'))
    EdgeDetected = StringField(lazy_gettext('Edge Detected'))
    GPIOState = IntegerField(lazy_gettext('GPIO State'))
    Direction = StringField(lazy_gettext('Direction'))
    Setpoint = DecimalField(lazy_gettext('Setpoint'))
    modCondRelayID = StringField(lazy_gettext('Relay ID'))
    RelayState = StringField(lazy_gettext('Relay State'))
    RelayDuration = DecimalField(lazy_gettext('Relay Duration'))
    DoExecute = StringField(lazy_gettext('Execute Command'))
    DoNotify = StringField(lazy_gettext('Notify by Email'))
    DoFlashLCD = StringField(lazy_gettext('Flash LCD'))
    DoRecord = StringField(lazy_gettext('Record with Camera'))
    modSubmit = SubmitField(lazy_gettext('Save'))
    delSubmit = SubmitField(lazy_gettext('Delete'))
    activateSubmit = SubmitField(lazy_gettext('Activate'))
    deactivateSubmit = SubmitField(lazy_gettext('Deactivate'))


#
# Upgrade
#

class Upgrade(FlaskForm):
    upgrade = SubmitField(lazy_gettext('Upgrade Mycodo'))


#
# Backup/Restore
#

class Backup(FlaskForm):
    backup = SubmitField(lazy_gettext('Create Backup'))
    restore = SubmitField(lazy_gettext('Restore Backup'))
    restore_dir = HiddenField('Restore Backup')


#
# Timers
#

class Timer(FlaskForm):
    timer_id = IntegerField(
        lazy_gettext('Timer ID'),
        widget=widgets.HiddenInput()
    )
    name = StringField(
        lazy_gettext('Name'),
        render_kw={"placeholder": lazy_gettext("Name")},
        validators=[DataRequired()]
    )
    relayID = StringField(
        lazy_gettext('Relay ID'),
        render_kw={"placeholder": lazy_gettext("Relay ID")}
    )
    state = SelectField(
        lazy_gettext('State'),
        choices=[
            ('on', 'On'),
            ('off', 'Off')
        ],
        validators=[DataRequired()]
    )
    timeStart = StringField(lazy_gettext('Time of day'))
    timeEnd = StringField(lazy_gettext('Time of day'))
    timeOnDurationOn = DecimalField(
        lazy_gettext('On (sec)'),
        render_kw={"placeholder": lazy_gettext("On (sec)")},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    durationOn = DecimalField(
        lazy_gettext('On (sec)'),
        render_kw={"placeholder": lazy_gettext("On seconds")}
    )
    durationOff = DecimalField(
        lazy_gettext('Off (sec)'),
        render_kw={"placeholder": lazy_gettext("Off seconds")}
    )
    timerCreate = SubmitField(lazy_gettext('Create Timer'))
    timerMod = SubmitField(lazy_gettext('Save'))
    timerDel = SubmitField(lazy_gettext('Delete'))
    activate = SubmitField(lazy_gettext('Activate'))
    deactivate = SubmitField(lazy_gettext('Deactivate'))
    orderTimerUp = SubmitField(lazy_gettext('Up'))
    orderTimerDown = SubmitField(lazy_gettext('Down'))


class ActivateTimer(FlaskForm):
    activateTimer_id = HiddenField('Timer')
    activateTimerSubmit = SubmitField(lazy_gettext('Activate'))


class DeactivateTimer(FlaskForm):
    deactivateTimer_id = HiddenField('Timer')
    deactivateTimerSubmit = SubmitField(lazy_gettext('Deactivate'))
