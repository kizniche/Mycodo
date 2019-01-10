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
from wtforms.widgets.html5 import NumberInput

from mycodo.config import MATHS
from mycodo.config_translations import TOOLTIPS_SETTINGS


class MathAdd(FlaskForm):
    math_type = SelectField(
        choices=MATHS,
        validators=[DataRequired()]
    )
    math_add = SubmitField(
        TOOLTIPS_SETTINGS['add']['title'])


class MathMod(FlaskForm):
    math_id = StringField('Math ID', widget=widgets.HiddenInput())
    name = StringField(
        TOOLTIPS_SETTINGS['name']['title'],
        validators=[DataRequired()])
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        validators=[DataRequired()],
        widget=NumberInput(step='any'))
    max_measure_age = IntegerField(
        TOOLTIPS_SETTINGS['max_age']['title'],
        validators=[DataRequired()],
        widget=NumberInput())
    start_offset = DecimalField(
        lazy_gettext('Start Offset (seconds)'),
        widget=NumberInput(step='any'))
    inputs = SelectMultipleField(
        lazy_gettext('Inputs'))
    select_measurement_unit = StringField(
        TOOLTIPS_SETTINGS['select_measurement_unit']['title'])
    measurements_enabled = SelectMultipleField(
        TOOLTIPS_SETTINGS['measurements_enabled']['title'])
    math_mod = SubmitField(
        TOOLTIPS_SETTINGS['save']['title'])
    math_delete = SubmitField(
        TOOLTIPS_SETTINGS['delete']['title'])
    math_activate = SubmitField(
        TOOLTIPS_SETTINGS['activate']['title'])
    math_deactivate = SubmitField(
        TOOLTIPS_SETTINGS['deactivate']['title'])
    math_order_up = SubmitField(
        TOOLTIPS_SETTINGS['up']['title'])
    math_order_down = SubmitField(
        TOOLTIPS_SETTINGS['down']['title'])


class MathModAverageSingle(FlaskForm):
    average_input = StringField(TOOLTIPS_SETTINGS['input']['title'])


class MathModDifference(FlaskForm):
    difference_reverse_order = BooleanField(lazy_gettext('Reverse Equation'))
    difference_absolute = BooleanField(lazy_gettext('Absolute Value'))


class MathModEquation(FlaskForm):
    equation_input = StringField(TOOLTIPS_SETTINGS['input']['title'])
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


class MathModRedundancy(FlaskForm):
    order_of_use = SelectMultipleField(
        lazy_gettext('Order of Use'))


class MathModVerification(FlaskForm):
    max_difference = DecimalField(
        lazy_gettext('Max Difference'),
        validators=[DataRequired()],
        widget=NumberInput(step='any'))


class MathMeasurementMod(FlaskForm):
    math_id = StringField('Math ID', widget=widgets.HiddenInput())
    math_measurement_id = StringField(widget=widgets.HiddenInput())
    name = StringField(
        TOOLTIPS_SETTINGS['name']['title'],
        validators=[DataRequired()]
    )
    select_measurement_unit = StringField(
        TOOLTIPS_SETTINGS['select_measurement_unit']['title'])
    convert_to_measurement_unit = StringField(
        lazy_gettext('Convert to Measurement'))

    math_measurement_mod = SubmitField(
        TOOLTIPS_SETTINGS['save']['title'])


class MathModMisc(FlaskForm):
    unique_id_1 = StringField()
    unique_id_2 = StringField()
