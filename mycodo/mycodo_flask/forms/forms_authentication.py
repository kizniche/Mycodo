# -*- coding: utf-8 -*-
#
# forms_authentication.py - Authentication Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired


#
# Create Admin
#

class CreateAdmin(FlaskForm):
    username = StringField(
        lazy_gettext('Username'),
        render_kw={"placeholder": lazy_gettext('Username')},
        validators=[DataRequired()])
    email = StringField(
        lazy_gettext('Email'),
        render_kw={"placeholder": lazy_gettext('Email')},
        validators=[DataRequired()])
    password = PasswordField(
        lazy_gettext('Password'),
        render_kw={"placeholder": lazy_gettext('Password')},
        validators=[DataRequired()])
    password_repeat = PasswordField(
        lazy_gettext('Repeat Password'),
        render_kw={"placeholder": lazy_gettext('Repeat Password')},
        validators=[DataRequired()])


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


#
# Log viewer
#

class LogView(FlaskForm):
    lines = IntegerField(
        lazy_gettext('Number of Lines'),
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext('Number of lines should be greater than 0')
        )]
    )
    loglogin = SubmitField(lazy_gettext('Login Log'))
    loghttp = SubmitField(lazy_gettext('HTTP Log'))
    logdaemon = SubmitField(lazy_gettext('Daemon Log'))
    logbackup = SubmitField(lazy_gettext('Backup Log'))
    logkeepup = SubmitField(lazy_gettext('KeepUp Log'))
    logupgrade = SubmitField(lazy_gettext('Upgrade Log'))
    logrestore = SubmitField(lazy_gettext('Restore Log'))


#
# Remote Admin add servers
#

class RemoteSetup(FlaskForm):
    remote_id = StringField('Remote Host ID', widget=widgets.HiddenInput())
    host = StringField(
        lazy_gettext('Domain or IP Address'),
        validators=[DataRequired()]
    )
    username = StringField(
        lazy_gettext('Username'),
        validators=[DataRequired()]
    )
    password = PasswordField(
        lazy_gettext('Password'),
        validators=[DataRequired()]
    )
    add = SubmitField(lazy_gettext('Add Host'))
    delete = SubmitField(lazy_gettext('Delete Host'))


class InstallNotice(FlaskForm):
    acknowledge = SubmitField(lazy_gettext('I Understand'))
