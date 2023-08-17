# -*- coding: utf-8 -*-
#
# forms_authentication.py - Authentication Flask Forms
#
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired

from mycodo.config_translations import TRANSLATIONS


#
# Language
#

class LanguageSelect(FlaskForm):
    language = StringField(lazy_gettext('Language'))


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
    mycodo_username = StringField(
        TRANSLATIONS['user']['title'],
        render_kw={"placeholder": TRANSLATIONS['user']['title']},
        validators=[DataRequired()]
    )
    mycodo_password = PasswordField(
        TRANSLATIONS['password']['title'],
        render_kw={"placeholder": TRANSLATIONS['password']['title']},
        validators=[DataRequired()]
    )
    remember = BooleanField()


#
# Forgot Password
#

class ForgotPassword(FlaskForm):
    reset_method = SelectField(
        lazy_gettext('Reset Method'),
        choices=[
            ('file', lazy_gettext('Save Reset Code to File')),
            ('email', lazy_gettext('Email Reset Code'))],
        validators=[DataRequired()]
    )
    username = StringField(
        TRANSLATIONS['user']['title'],
        render_kw={"placeholder": TRANSLATIONS['user']['title']})
    submit = SubmitField(lazy_gettext('Submit'))


class ResetPassword(FlaskForm):
    password_reset_code = StringField(
        "Password Reset Code",
        render_kw={"placeholder": "Reset Code"})
    password = PasswordField(
        TRANSLATIONS['password']['title'],
        render_kw={"placeholder": TRANSLATIONS['password']['title']})
    password_repeat = PasswordField(
        lazy_gettext('Repeat Password'),
        render_kw={"placeholder": lazy_gettext('Repeat Password')})
    submit = SubmitField(lazy_gettext('Change Password'))


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
