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
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired

from mycodo.config import MATHS


class MathAdd(FlaskForm):
    math_type = SelectField(
        choices=MATHS,
        validators=[DataRequired()]
    )
    math_add = SubmitField(lazy_gettext('Add Math'))


class MathMod(FlaskForm):
    math_id = IntegerField('Math ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()])
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        validators=[DataRequired()])
    max_measure_age = IntegerField(
        lazy_gettext('Max Age (seconds)'),
        validators=[DataRequired()])
    inputs = SelectMultipleField(
        lazy_gettext('Inputs'))
    measure = StringField(
        lazy_gettext('Measurement'),
        validators=[DataRequired()])
    measure_units = StringField(
        lazy_gettext('Units'),
        validators=[DataRequired()])
    math_mod = SubmitField(lazy_gettext('Save'))
    math_delete = SubmitField(lazy_gettext('Delete'))
    math_activate = SubmitField(lazy_gettext('Activate'))
    math_deactivate = SubmitField(lazy_gettext('Deactivate'))
    math_order_up = SubmitField(lazy_gettext('Up'))
    math_order_down = SubmitField(lazy_gettext('Down'))


class MathModDifference(FlaskForm):
    difference_reverse_order = BooleanField(lazy_gettext('Reverse Equation'))
    difference_absolute = BooleanField(lazy_gettext('Absolute Value'))


class MathModEquation(FlaskForm):
    equation_input = StringField(lazy_gettext('Input'))
    equation = StringField(lazy_gettext('Equation'))


class MathModHumidity(FlaskForm):
    dry_bulb_temperature = StringField(
        lazy_gettext('Dry Bulb Temperature'),
        validators=[DataRequired()])
    wet_bulb_temperature = StringField(
        lazy_gettext('Wet Bulb Temperature'),
        validators=[DataRequired()])
    pressure = StringField(
        '{press} ({opt})'.format(press=lazy_gettext('Pressure'),
                                 opt=lazy_gettext('optional')))


class MathModVerification(FlaskForm):
    max_difference = DecimalField(
        lazy_gettext('Max Difference'),
        validators=[DataRequired()])
