# -*- coding: utf-8 -*-
#
# forms_math.py - Math Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired

from config import MATHS


class MathAdd(FlaskForm):
    math_type = SelectField(
        choices=MATHS,
        validators=[DataRequired()]
    )
    add = SubmitField(lazy_gettext(u'Add Math Controller'))


class MathMod(FlaskForm):
    math_id = IntegerField('Math ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    period = DecimalField(lazy_gettext(u'Period (seconds)'))
    inputs = SelectMultipleField(lazy_gettext(u'Input'))
    max_measure_age = IntegerField(lazy_gettext(u'Max Age (seconds)'))
    measure = StringField(lazy_gettext(u'Measurement'))
    measure_units = StringField(lazy_gettext(u'Units'))
    mod = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    activate = SubmitField(lazy_gettext(u'Activate'))
    deactivate = SubmitField(lazy_gettext(u'Deactivate'))
    order_up = SubmitField(lazy_gettext(u'Up'))
    order_down = SubmitField(lazy_gettext(u'Down'))
