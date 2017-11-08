# -*- coding: utf-8 -*-
#
# forms_settings.py - Settings Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField


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
    relay_id = IntegerField(lazy_gettext(u'Output'))
    cmd_pre_camera = StringField(lazy_gettext(u'Pre Command'))
    cmd_post_camera = StringField(lazy_gettext(u'Post Command'))
    camera_add = SubmitField(lazy_gettext(u'Add Camera'))
    camera_mod = SubmitField(lazy_gettext(u'Save'))
    camera_del = SubmitField(lazy_gettext(u'Delete'))


#
# Settings (Email)
#

class SettingsEmail(FlaskForm):
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
# Settings (General)
#

class SettingsGeneral(FlaskForm):
    language = StringField(lazy_gettext(u'Language'))
    force_https = BooleanField(lazy_gettext(u'Force HTTPS'))
    hide_success = BooleanField(lazy_gettext(u'Hide success messages'))
    hide_info = BooleanField(lazy_gettext(u'Hide info messages'))
    hide_warning = BooleanField(lazy_gettext(u'Hide warning messages'))
    hide_tooltips = BooleanField(lazy_gettext(u'Hide Form Tooltips'))
    max_amps = DecimalField(lazy_gettext(u'Max Amps'))
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
