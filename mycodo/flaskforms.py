# -*- coding: utf-8 -*-
#

from flask_wtf import Form
from wtforms import BooleanField, DecimalField, HiddenField, IntegerField, PasswordField, SelectField, SelectMultipleField, SubmitField, StringField, validators
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
    Submit = SubmitField(u'Create New Method')


class AddMethod(Form):
    method_id = HiddenField(u'Method ID')
    method_type = HiddenField(u'Method Type')
    method_select = HiddenField(u'Method Select')
    startDailyTime = StringField(
        u'Start HH:MM:SS',
        render_kw={"placeholder": "HH:MM:SS"}
    )
    endDailyTime = StringField(
        u'End HH:MM:SS',
        render_kw={"placeholder": "HH:MM:SS"}
    )
    startTime = StringField(
        u'Start YYYY-MM-DD HH:MM:SS',
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    endTime = StringField(
        u'End YYYY-MM-DD HH:MM:SS',
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    startSetpoint = DecimalField(u'Start Setpoint')
    endSetpoint = DecimalField(u'End Setpoint (optional)')
    DurationSec = IntegerField(u'Duration (seconds)')
    amplitude = DecimalField(u'Amplitude')
    frequency = DecimalField(u'Frequency')
    shiftAngle = DecimalField(u'Angle Shift (0 to 360)')
    shiftY = DecimalField(u'Y-Axis Shift')
    x0 = DecimalField(u'X0')
    y0 = DecimalField(u'Y0')
    x1 = DecimalField(u'X1')
    y1 = DecimalField(u'Y1')
    x2 = DecimalField(u'X2')
    y2 = DecimalField(u'Y2')
    x3 = DecimalField(u'X3')
    y3 = DecimalField(u'Y3')
    relayDailyTime = StringField(
        u'Time HH:MM:SS',
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relayTime = StringField(
        u'Time YYYY-MM-DD HH:MM:SS',
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relayDurationSec = IntegerField(
        u'Duration On (seconds)',
        render_kw={"placeholder": ""}
    )
    relayID = StringField(
        u'Relay ID',
        render_kw={"placeholder": ""}
    )
    relayState = SelectField(
        u'Relay State',
        choices=[
            ('', ''),
            ('On', 'Turn On'),
            ('Off', 'Turn Off')
        ]
    )
    Submit = SubmitField(u'Add to Method')


class ModMethod(Form):
    method_id = HiddenField(u'Method ID')
    method_type = HiddenField(u'Method Type')
    method_select = HiddenField(u'Method Select')
    name = StringField(u'Name')
    startDailyTime = StringField(
        u'Start HH:MM:SS',
        render_kw={"placeholder": "HH:MM:SS"}
    )
    endDailyTime = StringField(
        u'End HH:MM:SS',
        render_kw={"placeholder": "HH:MM:SS"}
    )
    startTime = StringField(
        u'Start YYYY-MM-DD HH:MM:SS',
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    endTime = StringField(
        u'End YYYY-MM-DD HH:MM:SS',
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relayDailyTime = StringField(
        u'Time HH:MM:SS',
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relayTime = StringField(
        u'Time YYYY-MM-DD HH:MM:SS',
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    DurationSec = IntegerField(u'Duration (seconds)')
    startSetpoint = DecimalField(u'Start Setpoint')
    endSetpoint = DecimalField(u'End Setpoint (optional)')
    relayID = StringField(u'Relay',)
    relayState = StringField(u'Relay State')
    relayDurationSec = IntegerField(u'Relay On Duration (sec)')
    Submit = SubmitField(u'Save')
    Delete = SubmitField(u'Delete')


#
# Remote Admin add servers
#

class RemoteSetup(Form):
    remote_id = HiddenField(u'Remote Host ID')
    host = StringField(
        u'Domain or IP Address',
        render_kw={"placeholder": "youraddress.com or 0.0.0.0"},
        validators=[DataRequired()]
    )
    username = StringField(
        u'Username',
        render_kw={"placeholder": "Username"},
        validators=[DataRequired()]
    )
    password = PasswordField(
        u'Password',
         render_kw={"placeholder": "Password"},
         validators=[DataRequired()]
    )
    add = SubmitField(u'Add Host')
    delete = SubmitField(u'Delete Host')


#
# Tools/Log View
#

class LogView(Form):
    lines = IntegerField(
        u'Number of Lines',
        render_kw={"placeholder": "Lines"},
        validators=[validators.NumberRange(
            min=1,
            message="Number of lines should be greater than 0."
        )]
    )
    loglogin = SubmitField(u'Login Log')
    loghttp = SubmitField(u'HTTP Log')
    logdaemon = SubmitField(u'Daemon Log')
    logupgrade = SubmitField(u'Upgrade Log')
    logrestore = SubmitField(u'Restore Log')


#
# Daemon Control
#

class DaemonControl(Form):
    stop = SubmitField(u'Stop Daemon')
    start = SubmitField(u'Start Daemon')
    restart = SubmitField(u'Restart Daemon')


#
# Camera Use
#

class Camera(Form):
    Still = SubmitField(u'Capture Still')
    StartTimelapse = SubmitField(u'Start Timelapse')
    StopTimelapse = SubmitField(u'Stop Timelapse')
    TimelapseInterval = DecimalField(
        u'Photo Interval (sec)',
        render_kw={"placeholder": ""},
        validators=[validators.NumberRange(
            min=0,
            message="Photo Interval must be a positive value."
        )]
    )
    TimelapseRunTime = DecimalField(
        u'Total Run Time (sec)',
        render_kw={"placeholder": ""},
        validators=[validators.NumberRange(
            min=0,
            message="Total Run Time must be a positive value."
        )]
    )
    StartStream = SubmitField(u'Start Stream')
    StopStream = SubmitField(u'Stop Stream')


#
# Alerts
#

class EmailAlert(Form):
    smtpHost = StringField(
        u'SMTP Host',
        render_kw={"placeholder": "SMTP Host"},
        validators=[DataRequired()]
    )
    smtpPort = IntegerField(
        u'SMTP Port',
        render_kw={"placeholder": "SMTP Port"},
        validators=[validators.NumberRange(
            min=1,
            max=65535,
            message="Port should be between 1 and 65535"
        )]
    )
    sslEnable = BooleanField(u'Enable SSL')
    smtpUser = StringField(
        u'SMTP User',
        render_kw={"placeholder": "SMTP User"},
        validators=[DataRequired()]
    )
    smtpPassword = PasswordField(
        u'SMTP Password',
        render_kw={"placeholder": "Password"}
    )
    smtpFromEmail = EmailField(
        u'From Email',
        render_kw={"placeholder": "Email"},
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    smtpMaxPerHour = IntegerField(
        u'Max emails (per hour)',
        render_kw={"placeholder": "Max emails per hour"},
        validators=[validators.NumberRange(
            min=1,
            message="Must have at least one message able to be sent per hour."
        )]
    )
    sendTestEmail = SubmitField(u'Send Test Email')
    testEmailTo = EmailField(
        u'Test Email To',
        render_kw={"placeholder": "Email address to send test email"},
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
    forceHTTPS = BooleanField(u'Force HTTPS')
    hideAlertSuccess = BooleanField(u'Hide success messages')
    hideAlertInfo = BooleanField(u'Hide info messages')
    relayStatsVolts = IntegerField(u'Voltage')
    relayStatsCost = DecimalField(u'Cost per kWh')
    relayStatsCurrency = StringField(u'Currency Unit')
    relayStatsDayOfMonth = StringField(u'Billing Day of Month (1-30)')
    hideAlertWarning = BooleanField(u'Hide warning messages')
    stats_opt_out = BooleanField(u'Opt-out of sending statistics')
    Submit = SubmitField(u'Save')


#
# User Settings
#

class AddUser(Form):
    addUsername = StringField(
        u'Username',
        render_kw={"placeholder": "Username"},
        validators=[DataRequired()]
    )
    addEmail = EmailField(
        u'Email',
        render_kw={"placeholder": "Email"},
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    addPassword = PasswordField(
        u'Password',
        render_kw={"placeholder": "Password"},
        validators=[
            DataRequired(),
            validators.EqualTo('addPassword_repeat', message='Passwords must match'),
            validators.Length(
                min=6,
                message='Password must be 6 or more characters'
            )
        ]
    )
    addPassword_repeat = PasswordField(
        u'Repeat Password',
        render_kw={"placeholder": "Repeat Password"},
        validators=[DataRequired()]
    )
    addGroup = SelectField(
        u'Group',
        choices=[
            ('admin', 'Admin'),
            ('guest', 'Guest')
        ],
        validators=[DataRequired()]
    )
    addSubmit = SubmitField(u'Submit')


class ModUser(Form):
    modUsername = HiddenField(u'Username')
    modEmail = EmailField(u'Email',
            render_kw={"placeholder": "Email"},
            validators=[
                DataRequired(),
                validators.Email()])
    modPassword = PasswordField(
        u'Password',
        render_kw={"placeholder": "New Password"},
        validators=[
            validators.Optional(),
            validators.EqualTo(
                'modPassword_repeat',
                message='Passwords must match'
            ),
            validators.Length(
                min=6,
                message='Password must be 6 or more characters'
            )
        ]
    )
    modPassword_repeat = PasswordField(
        u'Repeat Password',
        render_kw={"placeholder": "Repeat Password"}
    )
    modGroup = SelectField(
        u'Group',
        choices=[
            ('admin', 'Admin'),
            ('guest', 'Guest')
        ],
        validators=[DataRequired()]
    )
    modTheme = StringField(u'Theme')
    modSubmit = SubmitField(u'Submit')


class DelUser(Form):
    delUsername = HiddenField(u'Username')
    delUserSubmit = SubmitField(u'Delete')


#
# Camera Settings
#

class SettingsCamera(Form):
    hflip = BooleanField(u'Flip Horizontally')
    vflip = BooleanField(u'Flip Vertically')
    rotation = IntegerField(u'Rotate Image')
    Submit = SubmitField(u'Save')


#
# Graphs
#

class AddGraph(Form):
    name = StringField(
        u'Graph Name',
        render_kw={"placeholder": "Graph Name"},
        validators=[DataRequired()]
    )
    pidIDs = SelectMultipleField(
        u'PID IDs (Setpoint)'
    )
    relayIDs = SelectMultipleField(
        u'Relay IDs'
    )
    sensorIDs = SelectMultipleField(
        u'Sensor IDs'
    )
    width = IntegerField(
        u'Width (%)',
        render_kw={"placeholder": "Percent Width"},
        validators=[
                validators.NumberRange(
            min=10,
            max=100
        )]
    )
    height = IntegerField(
        u'Height (pixels)',
        render_kw={"placeholder": "Percent Height"},
        validators=[
                validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xAxisDuration = IntegerField(
        u'x-Axis (min)',
        render_kw={"placeholder": "X-Axis Duration"},
        validators=[validators.NumberRange(
            min=1,
            message="Number of minutes to display of past measurements."
        )]
    )
    refreshDuration = IntegerField(
        u'Refresh (sec)',
        render_kw={"placeholder": "Refresh duration"},
        validators=[validators.NumberRange(
            min=1,
            message="Number of seconds to wait between acquiring any new measurements."
        )]
    )
    enableNavbar = BooleanField(u'Enable Navbar')
    enableExport = BooleanField(u'Enable Export')
    enableRangeSelect = BooleanField(u'Enable Range Selector')
    Submit = SubmitField(u'Create Graph')


class ModGraph(Form):
    graph_id = HiddenField(u'Graph ID')
    name = StringField(
        u'Graph Name',
        render_kw={"placeholder": "Graph Name"},
        validators=[DataRequired()]
    )
    pidIDs = SelectMultipleField(
        u'PID IDs (Setpoint)'
    )
    relayIDs = SelectMultipleField(
        u'Relay IDs'
    )
    sensorIDs = SelectMultipleField(
        u'Sensor IDs'
    )
    width = IntegerField(
        u'Width (%)',
        render_kw={"placeholder": "Percent Width"},
        validators=[
                validators.NumberRange(
            min=10,
            max=100
        )]
    )
    height = IntegerField(
        u'Height (pixels)',
        render_kw={"placeholder": "Percent Height"},
        validators=[
                validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xAxisDuration = IntegerField(
        u'x-Axis (min)',
        render_kw={"placeholder": "X-Axis Duration"},
        validators=[validators.NumberRange(
            min=1,
            message="Number of minutes to display of past measurements."
        )]
    )
    refreshDuration = IntegerField(
        u'Refresh (sec)',
        render_kw={"placeholder": "Refresh duration"},
        validators=[validators.NumberRange(
            min=1,
            message="Number of seconds to wait between acquiring any new measurements."
        )]
    )
    enableNavbar = BooleanField(u'Enable Navbar')
    enableExport = BooleanField(u'Enable Export')
    enableRangeSelect = BooleanField(u'Enable Range Selector')
    Submit = SubmitField(u'Save Graph')


class DelGraph(Form):
    graph_id = HiddenField(u'Graph ID')
    Submit = SubmitField(u'Delete Graph')

class OrderGraph(Form):
    orderGraph_id = HiddenField(u'Graph')
    orderGraphUp = SubmitField(u'Up')
    orderGraphDown = SubmitField(u'Down')


#
# LCDs
#

class AddLCD(Form):
    numberLCDs = IntegerField(
        u'Quantity',
        render_kw={"placeholder": "Quantity"},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    lcdAddSubmit = SubmitField(u'Add LCDs')

class ModLCD(Form):
    modLCD_id = HiddenField(u'Relay')
    modName = StringField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    modPin = StringField(
        u'I2C Address',
        render_kw={"placeholder": "I2C Address"},
        validators=[DataRequired()]
    )
    modMultiplexAddress = StringField(
        u'Multiplexer I2C Address',
        render_kw={"placeholder": "I2C Address"}
    )
    modMultiplexChannel = IntegerField(
        u'Multiplexer Channel',
        render_kw={"placeholder": "Channel"},
        validators=[
                validators.NumberRange(
            min=0,
            max=8
        )]
    )
    modPeriod = IntegerField(
        u'Period (sec)',
        render_kw={"placeholder": "Period"},
        validators=[validators.NumberRange(
            min=5,
            max=86400,
            message="Duration between calculating LCD output and applying to regulation must be between 5 and 86400 seconds."
        )]
    )
    modLCDType = SelectField(
        u'LCD Type',
        choices=[
            ('16x2', '16x2'),
            ('20x4', '20x4')
        ],
        validators=[DataRequired()]
    )
    modLine1SensorIDMeasurement = StringField(
        u'Line 1 Sensor ID'
    )
    modLine2SensorIDMeasurement = StringField(
        u'Line 2 Sensor ID'
    )
    modLine3SensorIDMeasurement = StringField(
        u'Line 3 Sensor ID'
    )
    modLine4SensorIDMeasurement = StringField(
        u'Line 4 Sensor ID'
    )
    modLCDSubmit = SubmitField(u'Save')

class DelLCD(Form):
    delLCD_id = HiddenField(u'LCD')
    delLCDSubmit = SubmitField(u'Delete')

class ActivateLCD(Form):
    activateLCD_id = HiddenField(u'LCD')
    activateLCDSubmit = SubmitField(u'Activate')

class DeactivateLCD(Form):
    deactivateLCD_id = HiddenField(u'LCD')
    deactivateLCDSubmit = SubmitField(u'Deactivate')

class OrderLCD(Form):
    orderLCD_id = HiddenField(u'LCD')
    orderLCDUp = SubmitField(u'Up')
    orderLCDDown = SubmitField(u'Down')

class ResetFlashingLCD(Form):
    flashLCD_id = HiddenField(u'LCD')
    Submit = SubmitField(u'Reset Flashing')



#
# Create Admin
#

class CreateAdmin(Form):
    username = StringField(
        u'Username',
        render_kw={"placeholder": "Username"},
        validators=[DataRequired()]
    )
    email = StringField(
        u'Email',
        render_kw={"placeholder": "Email"},
        validators=[DataRequired()]
    )
    password = PasswordField(
        u'Password',
         render_kw={"placeholder": "Password"},
         validators=[DataRequired()]
    )


#
# Login
#

class Login(Form):
    username = StringField(
        u'Username',
        render_kw={"placeholder": "Username"},
        validators=[DataRequired()]
    )
    password = PasswordField(
        u'Password',
         render_kw={"placeholder": "Password"},
         validators=[DataRequired()]
    )
    remember = BooleanField(u'remember')

class InstallNotice(Form):
    acknowledge = SubmitField(u'I Understand')


#
# Logs
#

class Log(Form):
    log_id = HiddenField(u'Log ID')
    name = StringField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    sensorMeasurement = StringField(u'Sensor and Measurement')
    period = IntegerField(u'Period (sec)')
    logCreate = SubmitField(u'Create Log Controller')
    logMod = SubmitField(u'Save')
    logDel = SubmitField(u'Delete')
    activate = SubmitField(u'Activate')
    deactivate = SubmitField(u'Deactivate')
    orderLogUp = SubmitField(u'Up')
    orderLogDown = SubmitField(u'Down')

class ActivateLog(Form):
    activateLog_id = HiddenField(u'Log')
    activateLogSubmit = SubmitField(u'Activate')

class DeactivateLog(Form):
    deactivateLog_id = HiddenField(u'Log')
    deactivateLogSubmit = SubmitField(u'Deactivate')


#
# PIDs
#

class AddPID(Form):
    numberPIDs = IntegerField(
        u'Quantity',
        render_kw={"placeholder": "Quantity"},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    pidAddSubmit = SubmitField(u'Add PIDs')

class ModPID(Form):
    modPID_id = HiddenField(u'Relay')
    modName = StringField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    modSensorID = StringField(
        u'Sensor ID',
        render_kw={"placeholder": "Sensor ID"},
        validators=[DataRequired()]
    )
    modMeasureType = StringField(
        u'Measure Type',
        validators=[DataRequired()]
    )
    modDirection = SelectField(
        u'Direction',
        choices=[
            ('raise', 'Raise'),
            ('lower', 'Lower'),
            ('both', 'Both')
        ],
        validators=[DataRequired()]
    )
    modPeriod = IntegerField(
        u'Period (sec)',
        render_kw={"placeholder": "Period"},
        validators=[validators.NumberRange(
            min=5,
            max=86400,
            message="Duration between calculating PID output and applying to regulation must be between 5 and 86400 seconds."
        )]
    )
    modSetpoint = DecimalField(
        u'Setpoint',
        render_kw={"placeholder": "Setpoint"},
        validators=[validators.NumberRange(
            min=-1000000,
            max=1000000,
            message="Setpoint range must be between -1,000,000 and 1,000,000."
        )]
    )
    modKp = DecimalField(
        u'Kp',
        render_kw={"placeholder": "P"},
        validators=[validators.NumberRange(
            min=0,
            message="Kp must be a positive value."
        )]
    )
    modKi = DecimalField(
        u'Ki',
        render_kw={"placeholder": "I"},
        validators=[validators.NumberRange(
            min=0,
            message="Ki must be a positive value."
        )]
    )
    modKd = DecimalField(
        u'Kd',
        render_kw={"placeholder": "D"},
        validators=[validators.NumberRange(
            min=0,
            message="Kd must be a positive value."
        )]
    )
    modIntegratorMin = DecimalField(u'Integrator Min')
    modIntegratorMax = DecimalField(u'Integrator Max')
    modRaiseRelayID = StringField(
        u'Raise Relay ID',
        render_kw={"placeholder": "Raise Relay ID"},
    )
    modRaiseMinDuration = IntegerField(
        u'Raise Min Duration',
        render_kw={"placeholder": "Raise Min Duration"},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message="Raise minimum duration must be a non-negative value. (0 to disable)"
        )]
    )
    modRaiseMaxDuration = IntegerField(
        u'Raise Max Duration',
        render_kw={"placeholder": "Raise Max Duration"},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message="Raise maximum duration must be a non-negative value. (0 to disable)"
        )]
    )
    modLowerRelayID = StringField(
        u'Lower Relay ID',
        render_kw={"placeholder": "Lower Relay ID"},
    )
    modLowerMinDuration = IntegerField(
        u'Lower Min Duration',
        render_kw={"placeholder": "Lower Min Duration"},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message="Lower minimum duration must be a non-negative value. (0 to disable)"
        )]
    )
    modLowerMaxDuration = IntegerField(
        u'Lower Max Duration',
        render_kw={"placeholder": "Lower Max Duration"},
        validators=[validators.NumberRange(
            min=0,
            max=86400,
            message="Lower maximum duration must be a non-negative value. (0 to disable)"
        )]
    )
    mod_method_id = HiddenField(u'Setpoint Tracking Method')
    mod_pid_save = SubmitField(u'Save Settings')
    mod_pid_hold = SubmitField(u'Hold')
    mod_pid_pause = SubmitField(u'Pause')
    mod_pid_resume = SubmitField(u'Resume')
    mod_pid_del = SubmitField(u'Delete PID')
    mod_pid_activate = SubmitField(u'Activate PID')
    mod_pid_deactivate = SubmitField(u'Deactivate PID')
    mod_pid_order_up = SubmitField(u'Order Up')
    mod_pid_order_down = SubmitField(u'Order Down')


#
# Relays
#

class AddRelay(Form):
    numberRelays = IntegerField(
        u'Quantity',
        render_kw={"placeholder": "Quantity"},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    relayAddSubmit = SubmitField(u'Add Relays')

class ModRelay(Form):
    modRelay_id = HiddenField(u'Relay')
    modName = StringField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    modGpio = IntegerField(
        u'GPIO',
        render_kw={"placeholder": "GPIO"},
        validators=[validators.NumberRange(
            min=0,
            max=27,
            message="GPIO (BCM numbering) is between 1 and 27 (0 to disable)"
        )]
    )
    modAmps = DecimalField(
        u'Current Draw',
        render_kw={"placeholder": "Amps"},
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message="The current draw of the device connected to this relay, in amps."
        )]
    )
    modTrigger = SelectField(
        u'On Trigger',
        choices=[
            ("1", 'High'),
            ("0", 'Low')
        ],
        validators=[DataRequired()]
    )
    modStartState = SelectField(
        u'Start State',
        choices=[
            ("1", 'On'),
            ("0", 'Off')
        ],
        validators=[DataRequired()]
    )
    modRelaySubmit = SubmitField(u'Save')

class DelRelay(Form):
    delRelay_id = HiddenField(u'Relay')
    delRelaySubmit = SubmitField(u'Delete')

class OrderRelay(Form):
    orderRelay_id = HiddenField(u'Relay')
    orderRelayUp = SubmitField(u'Up')
    orderRelayDown = SubmitField(u'Down')

class RelayOnOff(Form):
    Relay_id = HiddenField(u'Relay ID')
    Relay_pin = HiddenField(u'Relay Pin')
    On = SubmitField(u'On')
    Off = SubmitField(u'Off')



#
# Relay Conditionals
#

class AddRelayConditional(Form):
    numberRelayConditionals = IntegerField(
        u'Quantity',
        render_kw={"placeholder": "Quantity"},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    relayCondAddSubmit = SubmitField(u'Add Conditionals')

class ModRelayConditional(Form):
    Relay_id = HiddenField(u'Conditional ID')
    modCondName = StringField(
        u'Name',
        render_kw={"placeholder": "Name"}
    )
    IfRelayID = StringField(
        u'If Relay ID'
    )
    IfRelayAction = StringField(
        u'If Action'
    )
    IfRelayDuration = DecimalField(
        u'If Relay Duration',
        render_kw={"placeholder": "Duration"}
    )
    DoRelayID = StringField(
        u'Do Relay ID'
    )
    DoRelayAction = StringField(
        u'Do Action'
    )
    DoRelayDuration = DecimalField(
        u'Do Relay Duration',
        render_kw={"placeholder": "Duration"}
    )
    DoExecute = StringField(
        u'Execute Command',
        render_kw={"placeholder": "Command"}
    )
    DoNotify = StringField(
        u'Botify by Email',
        render_kw={"placeholder": "Email"}
    )
    DoFlashLCD = StringField(
        u'Flash LCD',
        render_kw={"placeholder": "LCD"}
    )
    activate = SubmitField(u'Activate')
    deactivate = SubmitField(u'Deactivate')
    modCondRelaySubmit = SubmitField(u'Save')
    delCondRelaySubmit = SubmitField(u'Delete')



#
# Sensors
#

class AddSensor(Form):
    numberSensors = IntegerField(
        u'Quantity',
        render_kw={"placeholder": "Quantity"},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    sensor = SelectField(
        u'Sensor',
        choices=[
            ('RPi', 'Raspberry Pi CPU Temperature'),
            ('RPiCPULoad', 'Raspberry Pi CPU Load'),
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
    sensorAddSubmit = SubmitField(u'Add Device')

class ModSensor(Form):
    modSensor_id = HiddenField(u'Sensor')
    modName = StringField(
        u'Name',
        validators=[DataRequired()]
    )
    modBus = IntegerField(u'I<sup>2</sup>C Bus')
    modLocation = StringField(u'Location')
    modMultiplexAddress = StringField(u'Multiplexer (MX)')
    modMultiplexBus = StringField(u'Mx I<sup>2</sup>C Bus')
    modMultiplexChannel = IntegerField(u'Mx Channel')
    modADCChannel = IntegerField(u'ADC Channel')
    modADCGain = IntegerField(u'ADC Gain')
    modADCResolution = IntegerField(u'ADC Resolution')
    modADCMeasure = StringField(u'ADC Measurement Type')
    modADCMeasureUnits = StringField(u'ADC Measurement Units')
    modADCVoltsMin = DecimalField(u'Volts Min')
    modADCVoltsMax = DecimalField(u'Volts Max')
    modADCUnitsMin = DecimalField(u'Units Min')
    modADCUnitsMax = DecimalField(u'Units Max')
    modSwitchEdge = StringField(u'Switch Edge Detected')
    modSwitchBounceTime = IntegerField(u'Bounce Time (ms)')
    modSwitchResetPeriod = IntegerField(u'Reset Period (sec)')
    modPreRelayID = StringField(u'Pre Relay')
    modPreRelayDuration = DecimalField(
        u'Pre Relay Duration (sec)',
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    modPeriod = IntegerField(
        u'Read Period (sec)',
        validators=[
                DataRequired(),
                validators.NumberRange(
            min=5,
            max=86400
        )]
    )
    modSHTClockPin = IntegerField(
        u'Clock Pin',
        validators=[validators.NumberRange(
            min=0,
            max=100,
            message="If using a SHT sensor, enter the GPIO connected to the clock pin (using BCM numbering)."
        )]
    )
    modSHTVoltage = StringField(u'SHT Input Voltage')
    modSensorSubmit = SubmitField(u'Save')
    delSensorSubmit = SubmitField(u'Delete')
    activateSensorSubmit = SubmitField(u'Activate')
    deactivateSensorSubmit = SubmitField(u'Deactivate')
    orderSensorUp = SubmitField(u'Up')
    orderSensorDown = SubmitField(u'Down')
    sensorCondAddSubmit = SubmitField(u'Add Conditional')



#
# Sensor Conditionals
#

class ModSensorConditional(Form):
    modCondSensor_id = HiddenField(u'Conditional ID')
    modSensor_id = HiddenField(u'Sensor ID')
    modCondName = StringField(u'Name')
    Period = IntegerField(
        u'Period (sec)',
        validators=[validators.NumberRange(
            min=0
        )]
    )
    MeasureType = StringField(u'Measurement Type')
    EdgeSelect = StringField(u'Edge or State')
    EdgeDetected = StringField(u'Edge Detected')
    GPIOState = IntegerField(u'GPIO State')
    Direction = StringField( u'Direction')
    Setpoint = DecimalField(u'Setpoint')
    modCondRelayID = StringField(u'Relay ID')
    RelayState = StringField(u'Relay State')
    RelayDuration = DecimalField(u'Relay Duration')
    DoExecute = StringField(u'Execute Command')
    DoNotify = StringField(u'Notify by Email')
    DoFlashLCD = StringField(u'Flash LCD')
    DoRecord = StringField(u'Record with Camera')
    modSubmit = SubmitField(u'Save')
    delSubmit = SubmitField(u'Delete')
    activateSubmit = SubmitField(u'Activate')
    deactivateSubmit = SubmitField(u'Deactivate')



#
# Upgrade
#

class Upgrade(Form):
    upgrade = SubmitField(u'Upgrade Mycodo')



#
# Backup/Restore
#

class Backup(Form):
    backup = SubmitField(u'Create Backup')
    restore = SubmitField(u'Restore Backup')
    restore_dir = HiddenField(u'Restore Backup')



#
# Timers
#

class Timer(Form):
    timer_id = HiddenField(u'Timer ID')
    name = StringField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    relayID = StringField(
        u'Relay ID',
        render_kw={"placeholder": "Relay ID"}
    )
    state = SelectField(
        u'State',
        choices=[
            ('on', 'On'),
            ('off', 'Off')
        ],
        validators=[DataRequired()]
    )
    timeStart = StringField(u'Time of day')
    timeEnd = StringField(u'Time of day')
    timeOnDurationOn = DecimalField(
        u'On (sec)',
        render_kw={"placeholder": "On sec."},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    durationOn = DecimalField(
        u'On (sec)',
        render_kw={"placeholder": "On sec."}
    )
    durationOff = DecimalField(
        u'Off (sec)',
        render_kw={"placeholder": "Off secself."}
    )
    timerCreate = SubmitField(u'Create Timer')
    timerMod = SubmitField(u'Save')
    timerDel = SubmitField(u'Delete')
    activate = SubmitField(u'Activate')
    deactivate = SubmitField(u'Deactivate')
    orderTimerUp = SubmitField(u'Up')
    orderTimerDown = SubmitField(u'Down')

class ActivateTimer(Form):
    activateTimer_id = HiddenField(u'Timer')
    activateTimerSubmit = SubmitField(u'Activate')

class DeactivateTimer(Form):
    deactivateTimer_id = HiddenField(u'Timer')
    deactivateTimerSubmit = SubmitField(u'Deactivate')
