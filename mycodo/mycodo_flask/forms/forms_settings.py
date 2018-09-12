# -*- coding: utf-8 -*-
#
# forms_settings.py - Settings Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import FileField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


#
# Settings (Camera)
#

class SettingsCamera(FlaskForm):
    camera_id = StringField('Camera ID', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext('Name'))
    library = StringField(lazy_gettext('Library'))
    device = StringField(lazy_gettext('Device'))
    opencv_device = IntegerField(lazy_gettext('OpenCV Device'))
    hflip = BooleanField(lazy_gettext('Flip image horizontally'))
    vflip = BooleanField(lazy_gettext('Flip image vertically'))
    rotation = IntegerField(lazy_gettext('Rotate Image'))
    height = IntegerField(lazy_gettext('Image Height'))
    width = IntegerField(lazy_gettext('Image Width'))
    brightness = DecimalField(lazy_gettext('Brightness'))
    contrast = DecimalField(lazy_gettext('Contrast'))
    exposure = DecimalField(lazy_gettext('Exposure'))
    gain = DecimalField(lazy_gettext('Gain'))
    hue = DecimalField(lazy_gettext('Hue'))
    saturation = DecimalField(lazy_gettext('Saturation'))
    white_balance = DecimalField(lazy_gettext('White Balance'))
    custom_options = StringField(lazy_gettext('Custom Options'))
    output_id = StringField(lazy_gettext('Output'))
    output_duration = DecimalField(lazy_gettext('Output Duration'))
    cmd_pre_camera = StringField(lazy_gettext('Pre Command'))
    cmd_post_camera = StringField(lazy_gettext('Post Command'))
    camera_add = SubmitField(lazy_gettext('Add Camera'))
    camera_mod = SubmitField(lazy_gettext('Save'))
    camera_del = SubmitField(lazy_gettext('Delete'))


#
# Settings (Email)
#

class SettingsEmail(FlaskForm):
    smtp_host = StringField(
        lazy_gettext('SMTP Host'),
        render_kw={"placeholder": lazy_gettext('SMTP Host')},
        validators=[DataRequired()]
    )
    smtp_port = IntegerField(
        lazy_gettext('SMTP Port'),
        render_kw={"placeholder": lazy_gettext('SMTP Port')},
        validators=[validators.NumberRange(
            min=1,
            max=65535,
            message=lazy_gettext('Port should be between 1 and 65535')
        )]
    )
    smtp_ssl = BooleanField('Enable SSL')
    smtp_user = StringField(
        lazy_gettext('SMTP User'),
        render_kw={"placeholder": lazy_gettext('SMTP User')},
        validators=[DataRequired()]
    )
    smtp_password = PasswordField(
        lazy_gettext('SMTP Password'),
        render_kw={"placeholder": lazy_gettext('Password')}
    )
    smtp_from_email = EmailField(
        lazy_gettext('From Email'),
        render_kw={"placeholder": lazy_gettext('Email')},
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    smtp_hourly_max = IntegerField(
        lazy_gettext('Max emails (per hour)'),
        render_kw={"placeholder": lazy_gettext('Max emails (per hour)')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext('Must have at least one message able to be '
                                 'sent per hour.')
        )]
    )
    send_test = SubmitField(lazy_gettext('Send Test Email'))
    send_test_to_email = EmailField(
        lazy_gettext('Test Email To'),
        render_kw={"placeholder": lazy_gettext('To Email Address')},
        validators=[
            validators.Email(),
            validators.Optional()
        ]
    )
    save = SubmitField('Save')


#
# Settings (General)
#

class SettingsGeneral(FlaskForm):
    landing_page = StringField(lazy_gettext('Landing Page'))
    language = StringField(lazy_gettext('Language'))
    force_https = BooleanField(lazy_gettext('Force HTTPS'))
    hide_success = BooleanField(lazy_gettext('Hide success messages'))
    hide_info = BooleanField(lazy_gettext('Hide info messages'))
    hide_warning = BooleanField(lazy_gettext('Hide warning messages'))
    hide_tooltips = BooleanField(lazy_gettext('Hide Form Tooltips'))
    max_amps = DecimalField(lazy_gettext('Max Amps'))
    output_stats_volts = IntegerField(lazy_gettext('Voltage'))
    output_stats_cost = DecimalField(lazy_gettext('Cost per kWh'))
    output_stats_currency = StringField(lazy_gettext('Currency Unit'))
    output_stats_day_month = StringField(lazy_gettext('Day of Month'))
    output_usage_report_gen = BooleanField(lazy_gettext('Generate Usage/Cost Report'))
    output_usage_report_span = StringField(lazy_gettext('Time Span to Generate'))
    output_usage_report_day = IntegerField(lazy_gettext('Day of Week/Month to Generate'))
    output_usage_report_hour = IntegerField(
        lazy_gettext('Hour of Day to Generate'),
        validators=[validators.NumberRange(
            min=0,
            max=23,
            message=lazy_gettext("Hour Options: 0-23")
        )])
    stats_opt_out = BooleanField(lazy_gettext('Opt-out of statistics'))
    enable_upgrade_check = BooleanField(lazy_gettext('Check for Updates'))
    Submit = SubmitField(lazy_gettext('Save'))


#
# Settings (Input)
#

class Input(FlaskForm):
    import_input_file = FileField(lazy_gettext('Upload'))
    import_input_upload = SubmitField(lazy_gettext('Import Input Module'))

class InputDel(FlaskForm):
    input_id = StringField(widget=widgets.HiddenInput())
    delete_input = SubmitField(lazy_gettext('Delete'))


#
# Settings (Measurement)
#

class MeasurementAdd(FlaskForm):
    name = StringField(lazy_gettext('Measurement Name'))
    units = SelectMultipleField(lazy_gettext('Measurement Units'))
    add_measurement = SubmitField(lazy_gettext('Add Measurement'))


class MeasurementMod(FlaskForm):
    measurement_id = StringField('Measurement ID', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext('Measurement Name'))
    units = SelectMultipleField(lazy_gettext('Measurement Units'))
    save_measurement = SubmitField(lazy_gettext('Save'))
    delete_measurement = SubmitField(lazy_gettext('Delete'))


class UnitAdd(FlaskForm):
    name = StringField(lazy_gettext('Unit Name'),
        validators=[DataRequired()])
    unit = StringField(lazy_gettext('Unit Abbreviation'),
        validators=[DataRequired()])
    add_unit = SubmitField(lazy_gettext('Add Unit'))


class UnitMod(FlaskForm):
    unit_id = StringField('Unit ID', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext('Unit Name'))
    unit = StringField(lazy_gettext('Unit Abbreviation'))
    save_unit = SubmitField(lazy_gettext('Save'))
    delete_unit = SubmitField(lazy_gettext('Delete'))


class ConversionAdd(FlaskForm):
    convert_unit_from = StringField(lazy_gettext('Convert From Unit'),
        validators=[DataRequired()])
    convert_unit_to = StringField(lazy_gettext('Convert To Measurement'),
        validators=[DataRequired()])
    equation = StringField(lazy_gettext('Equation'),
        validators=[DataRequired()])
    add_conversion = SubmitField(lazy_gettext('Add Conversion'))


class ConversionMod(FlaskForm):
    conversion_id = StringField('Conversion ID', widget=widgets.HiddenInput())
    convert_unit_from = StringField(lazy_gettext('Convert From Unit'))
    convert_unit_to = StringField(lazy_gettext('Convert To Unit'))
    equation = StringField(lazy_gettext('Equation'))
    save_conversion = SubmitField(lazy_gettext('Save'))
    delete_conversion = SubmitField(lazy_gettext('Delete'))


#
# Settings (User)
#

class UserRoles(FlaskForm):
    name = StringField(
        lazy_gettext('Role Name'),
        validators=[DataRequired()]
    )
    view_logs = BooleanField(lazy_gettext('View Logs'))
    view_stats = BooleanField(lazy_gettext('View Stats'))
    view_camera = BooleanField(lazy_gettext('View Camera'))
    view_settings = BooleanField(lazy_gettext('View Settings'))
    edit_users = BooleanField(lazy_gettext('Edit Users'))
    edit_controllers = BooleanField(lazy_gettext('Edit Controllers'))
    edit_settings = BooleanField(lazy_gettext('Edit Settings'))
    role_id = StringField('Role ID', widget=widgets.HiddenInput())
    add_role = SubmitField(lazy_gettext('Add Role'))
    save_role = SubmitField(lazy_gettext('Save'))
    delete_role = SubmitField(lazy_gettext('Delete'))


class UserAdd(FlaskForm):
    user_name = StringField(
        lazy_gettext('Username'),
        validators=[DataRequired()]
    )
    email = EmailField(
        lazy_gettext('Email'),
        validators=[
            DataRequired(),
            validators.Email()
        ]
    )
    password_new = PasswordField(
        lazy_gettext('Password'),
        validators=[
            DataRequired(),
            validators.EqualTo('password_repeat',
                               message=lazy_gettext('Passwords must match')),
            validators.Length(
                min=6,
                message=lazy_gettext('Password must be 6 or more characters')
            )
        ]
    )
    password_repeat = PasswordField(
        lazy_gettext('Repeat Password'),
        validators=[DataRequired()]
    )
    addRole = StringField(
        lazy_gettext('Role'),
        validators=[DataRequired()]
    )
    theme = StringField(
        lazy_gettext('Theme'),
        validators=[DataRequired()]
    )
    add_user = SubmitField(lazy_gettext('Add User'))


class UserMod(FlaskForm):
    user_id = StringField('User ID', widget=widgets.HiddenInput())
    email = EmailField(
        lazy_gettext('Email'),
        render_kw={"placeholder": lazy_gettext("Email")},
        validators=[
            DataRequired(),
            validators.Email()])
    password_new = PasswordField(
        lazy_gettext('Password'),
        render_kw={"placeholder": lazy_gettext("New Password")},
        validators=[
            validators.Optional(),
            validators.EqualTo(
                'password_repeat',
                message=lazy_gettext('Passwords must match')
            ),
            validators.Length(
                min=6,
                message=lazy_gettext('Password must be 6 or more characters')
            )
        ]
    )
    password_repeat = PasswordField(
        lazy_gettext('Repeat Password'),
        render_kw={"placeholder": lazy_gettext("Repeat Password")}
    )
    role_id = IntegerField(
        lazy_gettext('Role ID'),
        validators=[DataRequired()]
    )
    theme = StringField(lazy_gettext('Theme'))
    save = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))


#
# Settings (Pi)
#

class SettingsPi(FlaskForm):
    pigpiod_state = StringField('pigpiod state', widget=widgets.HiddenInput())
    enable_i2c = SubmitField(lazy_gettext('Enable I2C'))
    disable_i2c = SubmitField(lazy_gettext('Disable I2C'))
    enable_one_wire = SubmitField(lazy_gettext('Enable 1-Wire'))
    disable_one_wire = SubmitField(lazy_gettext('Disable 1-Wire'))
    enable_serial = SubmitField(lazy_gettext('Enable Serial'))
    disable_serial = SubmitField(lazy_gettext('Disable Serial'))
    enable_spi = SubmitField(lazy_gettext('Enable SPI'))
    disable_spi = SubmitField(lazy_gettext('Disable SPI'))
    enable_ssh = SubmitField(lazy_gettext('Enable SSH'))
    disable_ssh = SubmitField(lazy_gettext('Disable SSH'))
    enable_pi_camera = SubmitField(lazy_gettext('Enable Pi Camera'))
    disable_pi_camera = SubmitField(lazy_gettext('Disable Pi Camera'))
    hostname = StringField(lazy_gettext('Hostname'))
    change_hostname = SubmitField(lazy_gettext('Change Hostname'))
    pigpiod_sample_rate = StringField(lazy_gettext('Configure pigpiod'))
    change_pigpiod_sample_rate = SubmitField(lazy_gettext('Reconfigure'))

    sample_rate_controller_conditional = DecimalField(lazy_gettext('Conditional Sample Rate (seconds)'))
    sample_rate_controller_input = DecimalField(lazy_gettext('Input Sample Rate (seconds)'))
    sample_rate_controller_math = DecimalField(lazy_gettext('Math Sample Rate (seconds)'))
    sample_rate_controller_output = DecimalField(lazy_gettext('Output Sample Rate (seconds)'))
    sample_rate_controller_pid = DecimalField(lazy_gettext('PID Sample Rate (seconds)'))
    save_sample_rates = SubmitField(lazy_gettext('Save Sample Rates'))


#
# Settings (Diagnostic)
#

class SettingsDiagnostic(FlaskForm):
    delete_dashboard_elements = SubmitField(lazy_gettext('Delete All Dashboard Elements'))
    delete_notes_tags = SubmitField(lazy_gettext('Delete All Notes and Note Tags'))
