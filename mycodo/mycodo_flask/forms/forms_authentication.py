# -*- coding: utf-8 -*-
#
# forms_authentication.py - Authentication Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired

from mycodo.config_translations import TRANSLATIONS


#
# Create Admin
#

class CreateAdmin(FlaskForm):
    username = StringField(
        TRANSLATIONS['user']['title'],
        render_kw={"placeholder": TRANSLATIONS['user']['title']},
        validators=[DataRequired()])
    email = StringField(
        TRANSLATIONS['email']['title'],
        render_kw={"placeholder": TRANSLATIONS['email']['title']},
        validators=[DataRequired()])
    password = PasswordField(
        TRANSLATIONS['password']['title'],
        render_kw={"placeholder": TRANSLATIONS['password']['title']},
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
        TRANSLATIONS['user']['title'],
        render_kw={"placeholder": TRANSLATIONS['user']['title']},
        validators=[DataRequired()]
    )
    password = PasswordField(
        TRANSLATIONS['password']['title'],
        render_kw={"placeholder": TRANSLATIONS['password']['title']},
        validators=[DataRequired()]
    )
    remember = BooleanField(lazy_gettext('remember'))


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
        TRANSLATIONS['user']['title'],
        validators=[DataRequired()]
    )
    password = PasswordField(
        TRANSLATIONS['password']['title'],
        validators=[DataRequired()]
    )
    add = SubmitField(lazy_gettext('Add Host'))
    delete = SubmitField(lazy_gettext('Delete Host'))


class InstallNotice(FlaskForm):
    acknowledge = SubmitField(lazy_gettext('I Understand'))
