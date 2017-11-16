# -*- coding: utf-8 -*-
#
# forms_authentication.py - Authentication Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired


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
# Remote Admin add servers
#

class RemoteSetup(FlaskForm):
    remote_id = IntegerField('Remote Host ID', widget=widgets.HiddenInput())
    host = StringField(
        lazy_gettext(u'Domain or IP Address'),
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


class InstallNotice(FlaskForm):
    acknowledge = SubmitField(lazy_gettext(u'I Understand'))
