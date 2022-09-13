# -*- coding: utf-8 -*-
#
# forms_method.py - Method Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import HiddenField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput

from mycodo.config import METHODS
from mycodo.config_translations import TRANSLATIONS


class MethodCreate(FlaskForm):
    name = StringField(TRANSLATIONS['name']['title'])
    method_type = SelectField(
        choices=METHODS,
        validators=[DataRequired()]
    )
    controller_type = HiddenField('Controller Type')
    Submit = SubmitField(TRANSLATIONS['add']['title'])


class MethodAdd(FlaskForm):
    method_id = StringField(
        'Method ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    daily_time_start = StringField(
        lazy_gettext('Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    daily_time_end = StringField(
        lazy_gettext('End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    time_start = StringField(
        lazy_gettext('Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    time_end = StringField(
        lazy_gettext('End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    setpoint_start = DecimalField(
        lazy_gettext('Start Setpoint'),
        widget=NumberInput(step='any'))
    setpoint_end = DecimalField(
        lazy_gettext('End Setpoint (optional)'),
        widget=NumberInput(step='any'))
    duration = DecimalField(
        "{} ({})".format(lazy_gettext('Duration'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    duration_end = DecimalField(
        "{} ({})".format(lazy_gettext('Duration to End'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    amplitude = DecimalField(
        lazy_gettext('Amplitude'),
        widget=NumberInput(step='any'))
    frequency = DecimalField(
        lazy_gettext('Frequency'),
        widget=NumberInput(step='any'))
    shift_angle = DecimalField(
        lazy_gettext('Angle Shift (0 to 360)'),
        widget=NumberInput(step='any'))
    shiftY = DecimalField(
        lazy_gettext('Y-Axis Shift'),
        widget=NumberInput(step='any'))
    x0 = DecimalField('X0', widget=NumberInput(step='any'))
    y0 = DecimalField('Y0', widget=NumberInput(step='any'))
    x1 = DecimalField('X1', widget=NumberInput(step='any'))
    y1 = DecimalField('Y1', widget=NumberInput(step='any'))
    x2 = DecimalField('X2', widget=NumberInput(step='any'))
    y2 = DecimalField('Y2', widget=NumberInput(step='any'))
    x3 = DecimalField('X3', widget=NumberInput(step='any'))
    y3 = DecimalField('Y3', widget=NumberInput(step='any'))
    output_daily_time = StringField(
        lazy_gettext('Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"})
    output_time = StringField(
        lazy_gettext('Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"})
    save = SubmitField(lazy_gettext('Add to Method'))
    restart = SubmitField(lazy_gettext('Set Repeat Option'))
    linked_method_id = StringField('Linked Method Id')


class MethodMod(FlaskForm):
    method_id = StringField('Method ID', widget=widgets.HiddenInput())
    method_data_id = StringField('Method Data ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    name = StringField(
        TRANSLATIONS['name']['title'])
    daily_time_start = StringField(
        lazy_gettext('Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"})
    daily_time_end = StringField(
        lazy_gettext('End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"})
    time_start = StringField(
        lazy_gettext('Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"})
    time_end = StringField(
        lazy_gettext('End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"})
    output_daily_time = StringField(
        lazy_gettext('Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"})
    output_time = StringField(
        lazy_gettext('Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"})
    duration = DecimalField(
        "{} ({})".format(lazy_gettext('Duration'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    duration_end = DecimalField(
        "{} ({})".format(lazy_gettext('Duration to End'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    setpoint_start = DecimalField(
        lazy_gettext('Start Setpoint'),
        widget=NumberInput(step='any'))
    setpoint_end = DecimalField(
        lazy_gettext('End Setpoint'),
        widget=NumberInput(step='any'))
    rename = SubmitField(TRANSLATIONS['rename']['title'])
    save = SubmitField(TRANSLATIONS['save']['title'])
    delete = SubmitField(TRANSLATIONS['delete']['title'])
