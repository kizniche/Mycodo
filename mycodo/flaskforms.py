# -*- coding: utf-8 -*-
#

from flask_babel import lazy_gettext
from flask_wtf import Form
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
    validators
)
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField


#
# Method (Date)
#

class CreateMethod(Form):
    name = StringField(
        u'Name',
        render_kw={"placeholder": "Name"}
    )
    method_type = StringField(
        u'Method Type',
        render_kw={"placeholder": ""}
    )
    controller_type = HiddenField(u'Controller Type')
    Submit = SubmitField(lazy_gettext(u'Create New Method'))


class AddMethod(Form):
    method_id = HiddenField(u'Method ID')
    method_type = HiddenField(u'Method Type')
    method_select = HiddenField(u'Method Select')
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
    x0 = DecimalField(u'X0')
    y0 = DecimalField(u'Y0')
    x1 = DecimalField(u'X1')
    y1 = DecimalField(u'Y1')
    x2 = DecimalField(u'X2')
    y2 = DecimalField(u'Y2')
    x3 = DecimalField(u'X3')
    y3 = DecimalField(u'Y3')
    relayDailyTime = StringField(
        lazy_gettext('Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relayTime = StringField(
        lazy_gettext('Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relayDurationSec = IntegerField(
        lazy_gettext('Duration On (seconds)'),
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
    Submit = SubmitField(lazy_gettext('Add to Method'))


class ModMethod(Form):
    method_id = HiddenField(u'Method ID')
    method_type = HiddenField(u'Method Type')
    method_select = HiddenField(u'Method Select')
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
    endSetpoint = DecimalField(lazy_gettext('End Setpoint (optional)'))
    relayID = StringField(lazy_gettext('Relay'))
    relayState = StringField(lazy_gettext('Relay State'))
    relayDurationSec = IntegerField(lazy_gettext('Relay On Duration (sec)'))
    Submit = SubmitField(lazy_gettext('Save'))
    Delete = SubmitField(lazy_gettext('Delete'))


#
# Remote Admin add servers
#

class RemoteSetup(Form):
    remote_id = HiddenField(u'Remote Host ID')
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

class LogView(Form):
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

class DaemonControl(Form):
    stop = SubmitField(lazy_gettext('Stop Daemon'))
    start = SubmitField(lazy_gettext('Start Daemon'))
    restart = SubmitField(lazy_gettext('Restart Daemon'))


#
# Camera Use
#

class Camera(Form):
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

class EmailAlert(Form):
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
    sslEnable = BooleanField(u'Enable SSL')
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
    sendTestEmail = SubmitField(u'Send Test Email')
    testEmailTo = EmailField(
        lazy_gettext('Test Email To'),
        render_kw={"placeholder": lazy_gettext('Email address to send test '
                                               'email')},
        validators=[
            validators.Email(),
            validators.Optional()
        ]
    )
    smtpSubmit = SubmitField(u'Save')


#
# General Settings
#

class SettingsGeneral(Form):
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

class AddUser(Form):
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


class ModUser(Form):
    modUsername = HiddenField(u'Username')
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


class DelUser(Form):
    delUsername = HiddenField(u'Username')
    delUserSubmit = SubmitField(lazy_gettext('Delete'))


#
# Camera Options
#

class SettingsCamera(Form):
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

class ExportOptions(Form):
    measurement = StringField(lazy_gettext('Measurement to Export'))
    date_range = StringField(lazy_gettext('Time Range DD/MM/YYYY HH:MM'))
    Export = SubmitField(lazy_gettext('Export'))


#
# Graphs
#

class AddGraph(Form):
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


class ModGraph(Form):
    graph_id = HiddenField(u'Graph ID')
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


class DelGraph(Form):
    graph_id = HiddenField(u'Graph ID')
    Submit = SubmitField(lazy_gettext('Delete Graph'))


class OrderGraph(Form):
    orderGraph_id = HiddenField(u'Graph')
    orderGraphUp = SubmitField(lazy_gettext('Up'))
    orderGraphDown = SubmitField(lazy_gettext('Down'))


#
# LCDs
#

class AddLCD(Form):
    numberLCDs = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    lcdAddSubmit = SubmitField(lazy_gettext('Add LCDs'))


class ModLCD(Form):
    modLCD_id = HiddenField(u'Relay')
    modName = StringField(
        lazy_gettext('Name'),
        render_kw={"placeholder": lazy_gettext("Name")},
        validators=[DataRequired()]
    )
    modLocation = StringField(
        lazy_gettext('I2C Address'),
        render_kw={"placeholder": lazy_gettext("I2C Address")},
        validators=[DataRequired()]
    )
    modMultiplexAddress = StringField(
        lazy_gettext('Multiplexer I2C Address'),
        render_kw={"placeholder": lazy_gettext("I2C Address")}
    )
    modMultiplexChannel = IntegerField(
        lazy_gettext('Multiplexer Channel'),
        render_kw={"placeholder": lazy_gettext("Channel")},
        validators=[
            validators.NumberRange(
                min=0,
                max=8
            )]
    )
    modPeriod = DecimalField(
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
    modLCDType = SelectField(
        lazy_gettext('LCD Type'),
        choices=[
            ('16x2', '16x2'),
            ('20x4', '20x4')
        ],
        validators=[DataRequired()]
    )
    modLine1SensorIDMeasurement = StringField(
        lazy_gettext('Line 1 Sensor ID')
    )
    modLine2SensorIDMeasurement = StringField(
        lazy_gettext('Line 2 Sensor ID')
    )
    modLine3SensorIDMeasurement = StringField(
        lazy_gettext('Line 3 Sensor ID')
    )
    modLine4SensorIDMeasurement = StringField(
        lazy_gettext('Line 4 Sensor ID')
    )
    modLCDSubmit = SubmitField(lazy_gettext('Save'))


class DelLCD(Form):
    delLCD_id = HiddenField(u'LCD')
    delLCDSubmit = SubmitField(lazy_gettext('Delete'))


class ActivateLCD(Form):
    activateLCD_id = HiddenField(u'LCD')
    activateLCDSubmit = SubmitField(lazy_gettext('Activate'))


class DeactivateLCD(Form):
    deactivateLCD_id = HiddenField(u'LCD')
    deactivateLCDSubmit = SubmitField(lazy_gettext('Deactivate'))


class OrderLCD(Form):
    orderLCD_id = HiddenField(u'LCD')
    orderLCDUp = SubmitField(lazy_gettext('Up'))
    orderLCDDown = SubmitField(lazy_gettext('Down'))


class ResetFlashingLCD(Form):
    flashLCD_id = HiddenField(u'LCD')
    Submit = SubmitField(lazy_gettext('Reset Flashing'))


#
# Create Admin
#

class CreateAdmin(Form):
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

class Login(Form):
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


class InstallNotice(Form):
    acknowledge = SubmitField(lazy_gettext('I Understand'))


#
# PIDs
#

class AddPID(Form):
    numberPIDs = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    pidAddSubmit = SubmitField(lazy_gettext('Add PIDs'))


class ModPID(Form):
    modPID_id = HiddenField(u'Relay')
    modName = StringField(
        lazy_gettext('Name'),
        render_kw={"placeholder": lazy_gettext("Name")},
        validators=[DataRequired()]
    )
    modSensorID = StringField(
        lazy_gettext('Sensor ID'),
        render_kw={"placeholder": lazy_gettext("Sensor ID")},
        validators=[DataRequired()]
    )
    modMeasurement = StringField(
        lazy_gettext('Measure Type'),
        validators=[DataRequired()]
    )
    modDirection = SelectField(
        lazy_gettext('Direction'),
        choices=[
            ('raise', 'Raise'),
            ('lower', 'Lower'),
            ('both', 'Both')
        ],
        validators=[DataRequired()]
    )
    modPeriod = DecimalField(
        lazy_gettext('Period (seconds)'),
        render_kw={"placeholder": lazy_gettext("Period")},
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0,
            message=lazy_gettext("Duration between calculating PID output "
                                 "and applying to regulation must be between "
                                 "5 and 86400 seconds.")
        )]
    )
    modSetpoint = DecimalField(
        lazy_gettext('Setpoint'),
        render_kw={"placeholder": "Setpoint"},
        validators=[validators.NumberRange(
            min=-1000000,
            max=1000000,
            message=lazy_gettext("Setpoint range must be between -1,000,000 "
                                 "and 1,000,000.")
        )]
    )
    modKp = DecimalField(
        lazy_gettext('Kp'),
        render_kw={"placeholder": lazy_gettext("P")},
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext("Kp must be a positive value.")
        )]
    )
    modKi = DecimalField(
        lazy_gettext('Ki'),
        render_kw={"placeholder": lazy_gettext("I")},
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext("Ki must be a positive value.")
        )]
    )
    modKd = DecimalField(
        lazy_gettext('Kd'),
        render_kw={"placeholder": lazy_gettext("D")},
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext("Kd must be a positive value.")
        )]
    )
    modIntegratorMin = DecimalField(lazy_gettext('Integrator Min'))
    modIntegratorMax = DecimalField(lazy_gettext('Integrator Max'))
    modRaiseRelayID = StringField(
        lazy_gettext('Raise Relay ID'),
        render_kw={"placeholder": lazy_gettext("Raise Relay ID")},
    )
    modRaiseMinDuration = IntegerField(
        lazy_gettext('Raise Min Duration'),
        render_kw={"placeholder": lazy_gettext("Raise Min Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message=lazy_gettext("Raise minimum duration must be a "
                                 "non-negative value. (0 to disable)")
        )]
    )
    modRaiseMaxDuration = IntegerField(
        lazy_gettext('Raise Max Duration'),
        render_kw={"placeholder": lazy_gettext("Raise Max Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message=lazy_gettext("Raise maximum duration must be a "
                                 "non-negative value. (0 to disable)")
        )]
    )
    modLowerRelayID = StringField(
        lazy_gettext('Lower Relay ID'),
        render_kw={"placeholder": lazy_gettext("Lower Relay ID")},
    )
    modLowerMinDuration = IntegerField(
        lazy_gettext('Lower Min Duration'),
        render_kw={"placeholder": lazy_gettext("Lower Min Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message=lazy_gettext("Lower minimum duration must be a "
                                 "non-negative value. (0 to disable)")
        )]
    )
    modLowerMaxDuration = IntegerField(
        lazy_gettext('Lower Max Duration'),
        render_kw={"placeholder": lazy_gettext("Lower Max Duration")},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message=lazy_gettext("Lower maximum duration must be a "
                                 "non-negative value. (0 to disable)")
        )]
    )
    mod_method_id = HiddenField(u'Setpoint Tracking Method')
    mod_pid_save = SubmitField(lazy_gettext('Save Settings'))
    mod_pid_hold = SubmitField(lazy_gettext('Hold'))
    mod_pid_pause = SubmitField(lazy_gettext('Pause'))
    mod_pid_resume = SubmitField(lazy_gettext('Resume'))
    mod_pid_del = SubmitField(lazy_gettext('Delete PID'))
    mod_pid_activate = SubmitField(lazy_gettext('Activate PID'))
    mod_pid_deactivate = SubmitField(lazy_gettext('Deactivate PID'))
    mod_pid_order_up = SubmitField(lazy_gettext('Order Up'))
    mod_pid_order_down = SubmitField(lazy_gettext('Order Down'))


#
# Relays
#

class AddRelay(Form):
    numberRelays = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    relayAddSubmit = SubmitField(lazy_gettext('Add Relays'))


class ModRelay(Form):
    relay_id = HiddenField(u'Relay')
    relay_pin = HiddenField(u'Relay Pin')
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
    sec_on = DecimalField(lazy_gettext('Seconds to turn on'))
    sec_on_submit = SubmitField(lazy_gettext('Turn On'))


#
# Relay Conditionals
#

class AddRelayConditional(Form):
    numberRelayConditionals = IntegerField(
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    relayCondAddSubmit = SubmitField(lazy_gettext('Add Conditionals'))


class ModRelayConditional(Form):
    relay_id = HiddenField(u'Conditional ID')
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
    do_relay_id = StringField(
        lazy_gettext('Do Relay ID')
    )
    do_relay_action = StringField(
        lazy_gettext('Do Action')
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
    save = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))


#
# Sensors
#

class AddSensor(Form):
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


class ModSensor(Form):
    modSensor_id = HiddenField(u'Sensor')
    modName = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    modBus = IntegerField(lazy_gettext('I<sup>2</sup>C Bus'))
    modLocation = StringField(lazy_gettext('Location'))
    modPowerPin = IntegerField(lazy_gettext('Power Pin'))
    modPowerState = IntegerField(lazy_gettext('Power On State'))
    modMultiplexAddress = StringField(lazy_gettext('Multiplexer (MX)'))
    modMultiplexBus = StringField(lazy_gettext('Mx I<sup>2</sup>C Bus'))
    modMultiplexChannel = IntegerField(lazy_gettext('Mx Channel'))
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
    modPeriod = DecimalField(
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

class ModSensorConditional(Form):
    modCondSensor_id = HiddenField(u'Conditional ID')
    modSensor_id = HiddenField(lazy_gettext('Sensor ID'))
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

class Upgrade(Form):
    upgrade = SubmitField(lazy_gettext('Upgrade Mycodo'))


#
# Backup/Restore
#

class Backup(Form):
    backup = SubmitField(lazy_gettext('Create Backup'))
    restore = SubmitField(lazy_gettext('Restore Backup'))
    restore_dir = HiddenField(u'Restore Backup')


#
# Timers
#

class Timer(Form):
    timer_id = HiddenField(u'Timer ID')
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


class ActivateTimer(Form):
    activateTimer_id = HiddenField(u'Timer')
    activateTimerSubmit = SubmitField(lazy_gettext('Activate'))


class DeactivateTimer(Form):
    deactivateTimer_id = HiddenField(u'Timer')
    deactivateTimerSubmit = SubmitField(lazy_gettext('Deactivate'))
