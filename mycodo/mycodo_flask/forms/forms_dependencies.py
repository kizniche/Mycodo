# -*- coding: utf-8 -*-
#
# forms_dependencies.py - Dependencies Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired


class Dependencies(FlaskForm):
    device = StringField('Device', widget=widgets.HiddenInput())
    install = SubmitField(lazy_gettext('Install all Dependencies'))
