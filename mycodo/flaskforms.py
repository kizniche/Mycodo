# -*- coding: utf-8 -*-
#

from flask_wtf import Form
from wtforms import BooleanField, DecimalField, HiddenField, IntegerField, PasswordField, SelectField, SelectMultipleField, SubmitField, TextField, validators
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField


#
# Method (Date)
#

class CreateMethod(Form):
    name = TextField(
        u'Name',
        render_kw={"placeholder": "Name"}
    )
    method_type = TextField(
        u'Method Type',
        render_kw={"placeholder": ""}
    )
    controller_type = HiddenField(u'Controller Type')
    Submit = SubmitField(u'Create New Method')


class AddMethod(Form):
    method_id = HiddenField(u'Method ID')
    method_type = HiddenField(u'Method Type')
    method_select = HiddenField(u'Method Select')
    startTime = TextField(
        u'Start (DD-MM-YYYY HH:MM:SS)',
        render_kw={"placeholder": "DD-MM-YYYY HH:MM:SS"}
    )
    endTime = TextField(
        u'End (DD-MM-YYYY HH:MM:SS)',
        render_kw={"placeholder": "DD-MM-YYYY HH:MM:SS"}
    )
    startSetpoint = DecimalField(
        u'Start Setpoint',
        render_kw={"placeholder": "0.0"}
    )
    endSetpoint = DecimalField(
        u'End Setpoint (optional)',
        render_kw={"placeholder": "0.0"}
    )
    DurationSec = IntegerField(
        u'Duration (seconds)',
        render_kw={"placeholder": ""}
    )
    relayTime = TextField(
        u'Time (DD-MM-YYYY HH:MM:SS)',
        render_kw={"placeholder": "DD-MM-YYYY HH:MM:SS"}
    )
    relayDurationSec = IntegerField(
        u'Duration On (seconds)',
        render_kw={"placeholder": ""}
    )
    relayID = TextField(
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
    startTime = TextField(
        u'Start (DD-MM-YYYY HH:MM:SS)',
        render_kw={"placeholder": "DD-MM-YYYY HH:MM:SS"}
    )
    endTime = TextField(
        u'End (DD-MM-YYYY HH:MM:SS)',
        render_kw={"placeholder": "DD-MM-YYYY HH:MM:SS"}
    )
    relayTime = TextField(
        u'Time (DD-MM-YYYY HH:MM:SS)',
        render_kw={"placeholder": "DD-MM-YYYY HH:MM:SS"}
    )
    DurationSec = IntegerField(
        u'Duration (seconds)',
        render_kw={"placeholder": ""}
    )
    startSetpoint = DecimalField(
        u'Start Setpoint',
        render_kw={"placeholder": "0.0"}
    )
    endSetpoint = DecimalField(
        u'End Setpoint (optional)',
        render_kw={"placeholder": "0.0"}
    )
    relayID = TextField(u'Relay',)
    relayState = TextField(u'Relay State')
    relayDurationSec = IntegerField(u'Relay On Duration (sec)')
    Submit = SubmitField(u'Save')
    Delete = SubmitField(u'Delete')


#
# Remote Admin add servers
#

class RemoteSetup(Form):
    remote_id = HiddenField(u'Remote Host ID')
    host = TextField(
        u'Domain or IP Address',
        render_kw={"placeholder": "youraddress.com or 0.0.0.0"},
        validators=[DataRequired()]
    )
    username = TextField(
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
    logupdate = SubmitField(u'Update Log')
    logrestore = SubmitField(u'Restore Log')


#
# Daemon Control
#

class DaemonControl(Form):
    stop = SubmitField(u'Stop Daemon')
    start = SubmitField(u'Start Daemon')
    restart = SubmitField(u'Restart Daemon')



#
# Camera
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
    smtpHost = TextField(
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
    smtpUser = TextField(
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
# Settings - General
#

class SettingsGeneral(Form):
    hideAlertSuccess = BooleanField(u'Hide success messages')
    hideAlertInfo = BooleanField(u'Hide info messages')
    hideAlertWarning = BooleanField(u'Hide warning messages')
    stats_opt_out = BooleanField(u'Opt-out of sending statistics')
    Submit = SubmitField(u'Save')



#
# Graphs
#

class AddGraph(Form):
    name = TextField(
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
    name = TextField(
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
    modName = TextField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    modPin = TextField(
        u'I2C Address',
        render_kw={"placeholder": "I2C Address"},
        validators=[DataRequired()]
    )
    modMultiplexAddress = TextField(
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
    modLine1SensorIDMeasurement = TextField(
        u'Line 1 Sensor ID'
    )
    modLine2SensorIDMeasurement = TextField(
        u'Line 2 Sensor ID'
    )
    modLine3SensorIDMeasurement = TextField(
        u'Line 3 Sensor ID'
    )
    modLine4SensorIDMeasurement = TextField(
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
# Login
#

class Login(Form):
    username = TextField(
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
    name = TextField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    sensorMeasurement = TextField(u'Sensor and Measurement')
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
    modName = TextField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    modSensorID = TextField(
        u'Sensor ID',
        render_kw={"placeholder": "Sensor ID"},
        validators=[DataRequired()]
    )
    modMeasureType = TextField(
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
    modRaiseRelayID = TextField(
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
    modLowerRelayID = TextField(
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
    modPIDSubmit = SubmitField(u'Save')


class ModPIDMethod(Form):
    pid_id = HiddenField(u'PID ID')
    method_id = HiddenField(u'Selected Method')
    Submit = SubmitField(u'Use Method')


class AddPIDsetpoint(Form):
    PID_id = HiddenField(u'PID ID')
    startTime = TextField(u'Start Time')
    endTime = TextField(u'End Time')
    startSetpoint = DecimalField(u'Start Setpoint')
    endSetpoint = DecimalField(
        u'End Setpoint (optional)',
        validators=[
            validators.Optional()
        ])
    Submit = SubmitField(u'Add New Setpoint(s)')

class ModPIDsetpoint(Form):
    PIDSetpoint_id = HiddenField(u'PID Setpoint ID')
    PID_id = HiddenField(u'PID ID')
    startTime = TextField(u'Start Time')
    endTime = TextField(u'End Time')
    startSetpoint = DecimalField(u'Start Setpoint')
    endSetpoint = DecimalField(
        u'End Setpoint (optional)',
        validators=[
            validators.Optional()
        ])
    Delete = SubmitField(u'Delete')
    Save = SubmitField(u'Save')

class DelPID(Form):
    delPID_id = HiddenField(u'PID')
    delPIDSubmit = SubmitField(u'Delete')

class ActivatePID(Form):
    activatePID_id = HiddenField(u'PID')
    activatePIDSubmit = SubmitField(u'Activate')

class DeactivatePID(Form):
    deactivatePID_id = HiddenField(u'PID')
    deactivatePIDSubmit = SubmitField(u'Deactivate')

class OrderPID(Form):
    orderPID_id = HiddenField(u'PID')
    orderPIDUp = SubmitField(u'Up')
    orderPIDDown = SubmitField(u'Down')



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
    modName = TextField(
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
    modCondName = TextField(
        u'Name',
        render_kw={"placeholder": "Name"}
    )
    IfRelayID = TextField(
        u'If Relay ID'
    )
    IfRelayAction = TextField(
        u'If Action'
    )
    IfRelayDuration = DecimalField(
        u'If Relay Duration',
        render_kw={"placeholder": "Duration"}
    )
    DoRelayID = TextField(
        u'Do Relay ID'
    )
    DoRelayAction = TextField(
        u'Do Action'
    )
    DoRelayDuration = DecimalField(
        u'Do Relay Duration',
        render_kw={"placeholder": "Duration"}
    )
    DoExecute = TextField(
        u'Execute Command',
        render_kw={"placeholder": "Command"}
    )
    DoNotify = TextField(
        u'Botify by Email',
        render_kw={"placeholder": "Email"}
    )
    DoFlashLCD = TextField(
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
            ('ADS1x15', 'Analog to Digital Converter: ADS1x15'),
            ('MCP342x', 'Analog to Digital Converter: MCP342x'),
            ('K30', 'CO2: K30'),
            ('EDGE', 'Edge Detection: Simple Switch'),
            ('TSL2561', 'Luminance: TSL2561'),
            ('BMP', 'Pressure/Temperature: BMP 180/085'),
            ('DS18B20', 'Temperature: DS18B20'),
            ('TMP006', 'Temperature (Contactless): TMP 006/007'),
            ('DHT11', 'Temperature/Humidity: DHT11'),
            ('DHT22', 'Temperature/Humidity: DHT22'),
            ('AM2315', 'Temperature/Humidity: AM2315'),
            ('SHT1x_7x', 'Temperature/Humidity: SHT 10/11/15/71/75'),
            ('SHT2x', 'Temperature/Humidity: SHT 21/25')
        ],
        validators=[DataRequired()]
    )
    sensorAddSubmit = SubmitField(u'Add Device')

class ModSensor(Form):
    modSensor_id = HiddenField(u'Sensor')
    modName = TextField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    modLocation = TextField(
        u'Location',
        render_kw={"placeholder": "Location"}
    )
    modMultiplexAddress = TextField(
        u'Multiplexer I2C Address',
        render_kw={"placeholder": "I2C Address"}
    )
    modMultiplexChannel = IntegerField(
        u'Multiplexer Channel',
        render_kw={"placeholder": "Channel"}
    )
    modADCChannel = IntegerField(
        u'ADC Channel',
        render_kw={"placeholder": "Channel"}
    )
    modADCGain = IntegerField(
        u'ADC Gain',
        render_kw={"placeholder": "Gain"}
    )
    modADCResolution = IntegerField(
        u'ADC Resolution',
        render_kw={"placeholder": "Resolution"}
    )
    modADCMeasure = TextField(
        u'ADC Measurement Type',
        render_kw={"placeholder": "Measurement"}
    )
    modADCMeasureUnits = TextField(
        u'ADC Measurement Units',
        render_kw={"placeholder": "Units"}
    )
    modADCVoltsMin = DecimalField(
        u'Volts Min',
        render_kw={"placeholder": "Volts Min"}
    )
    modADCVoltsMax = DecimalField(
        u'Volts Max',
        render_kw={"placeholder": "Volts Max"}
    )
    modADCUnitsMin = DecimalField(
        u'Units Min',
        render_kw={"placeholder": "Units Min"}
    )
    modADCUnitsMax = DecimalField(
        u'Units Max',
        render_kw={"placeholder": "Units Max"}
    )
    modSwitchEdge = TextField(
        u'Switch Edge Detected',
        render_kw={"placeholder": "Edge Detected"}
    )
    modSwitchBounceTime = IntegerField(
        u'Bounce Time (ms)',
        render_kw={"placeholder": "Bounce Time"}
    )
    modSwitchResetPeriod = IntegerField(
        u'Reset Period (sec)',
        render_kw={"placeholder": "Reset Period"}
    )
    modPreRelayID = TextField(
        u'Pre Relay',
        render_kw={"placeholder": "Pre Relay"}
    )
    modPreRelayDuration = DecimalField(
        u'Pre Relay Duration (sec)',
        render_kw={"placeholder": "Pre Relay Duration"},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    modPeriod = IntegerField(
        u'Read Period (sec)',
        render_kw={"placeholder": "Period"},
        validators=[
                DataRequired(),
                validators.NumberRange(
            min=5,
            max=86400
        )]
    )
    modSHTClockPin = IntegerField(
        u'Clock Pin',
        render_kw={"placeholder": "SHT Clock Pin"},
        validators=[validators.NumberRange(
            min=0,
            max=100,
            message="If using a SHT sensor, enter the clock pin."
        )]
    )
    modSHTVoltage = TextField(
        u'Voltage',
        render_kw={"placeholder": "Voltage"}
    )
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
    modCondName = TextField(
        u'Name',
        render_kw={"placeholder": "Name"}
    )
    Period = IntegerField(
        u'Period (sec)',
        render_kw={"placeholder": "Period"},
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    MeasureType = TextField(
        u'Measurement Type'
    )
    EdgeDetected = TextField(
        u'Edge Detected'
    )
    Direction = TextField(
        u'Direction'
    )
    Setpoint = DecimalField(
        u'Setpoint',
        render_kw={"placeholder": "Setpoint"}
    )
    modCondRelayID = TextField(
        u'Relay ID'
    )
    RelayState = TextField(
        u'Relay State'
    )
    RelayDuration = DecimalField(
        u'Relay Duration',
        render_kw={"placeholder": "Duration"}
    )
    DoExecute = TextField(
        u'Execute Command',
        render_kw={"placeholder": "Command"}
    )
    DoNotify = TextField(
        u'Notify by Email',
        render_kw={"placeholder": "Email"}
    )
    DoFlashLCD = TextField(
        u'Flash LCD',
        render_kw={"placeholder": "LCD"}
    )
    DoRecord = TextField(
        u'Record with Camera',
        render_kw={"placeholder": "Record"}
    )
    modSubmit = SubmitField(u'Save')
    delSubmit = SubmitField(u'Delete')
    activateSubmit = SubmitField(u'Activate')
    deactivateSubmit = SubmitField(u'Deactivate')



#
# Update
#

class Update(Form):
    update = SubmitField(u'Update Mycodo')



#
# Backup/Restore
#

class Backup(Form):
    backup = SubmitField(u'Create Backup')
    restore = SubmitField(u'Restore Backup')
    restore_dir = HiddenField(u'Restore Backup')



#
# Users
#

class AddUser(Form):
    addUsername = TextField(
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
    modTheme = SelectField(
        u'Group',
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark')
        ],
        validators=[DataRequired()]
    )
    modSubmit = SubmitField(u'Submit')


class DelUser(Form):
    delUsername = HiddenField(u'Username')
    delUserSubmit = SubmitField(u'Delete')


#
# Timers
#

class Timer(Form):
    timer_id = HiddenField(u'Timer ID')
    name = TextField(
        u'Name',
        render_kw={"placeholder": "Name"},
        validators=[DataRequired()]
    )
    relayID = TextField(
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
    timeOn = TextField(
        u'Time of day',
        render_kw={"placeholder": "Time"}
    )
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
