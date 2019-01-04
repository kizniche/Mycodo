# -*- coding: utf-8 -*-
#
# forms_method.py - Method Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput

from mycodo.config import METHODS


class MethodCreate(FlaskForm):
    name = StringField(lazy_gettext('Name'))
    method_type = SelectField(
        choices=METHODS,
        validators=[DataRequired()]
    )
    controller_type = HiddenField('Controller Type')
    Submit = SubmitField(lazy_gettext('Add'))


class MethodAdd(FlaskForm):
    method_id = StringField(
        'Method ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
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
        lazy_gettext('Duration (seconds)'),
        widget=NumberInput(step='any'))
    duration_end = DecimalField(
        lazy_gettext('Duration to End (seconds)'),
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
        render_kw={"placeholder": "HH:MM:SS"}
    )
    output_time = StringField(
        lazy_gettext('Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    output_duration = DecimalField(
        lazy_gettext('Duration/Duty Cycle'),
        widget=NumberInput(step='any'))
    output_id = StringField(lazy_gettext('Output'),)
    output_state = SelectField(
        lazy_gettext('Relay State'),
        choices=[
            ('', ''),
            ('On', lazy_gettext('Turn On')),
            ('Off', lazy_gettext('Turn Off')),
            ('PWM', lazy_gettext('PWM (Duty Cycle)'))
        ]
    )
    save = SubmitField(lazy_gettext('Add to Method'))
    restart = SubmitField(lazy_gettext('Set Repeat Option'))


class MethodMod(FlaskForm):
    method_id = StringField(
        'Method ID', widget=widgets.HiddenInput())
    method_data_id = StringField(
        'Method Data ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
    name = StringField(lazy_gettext('Name'))
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
    output_daily_time = StringField(
        lazy_gettext('Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    output_time = StringField(
        lazy_gettext('Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    duration = DecimalField(
        lazy_gettext('Duration (seconds)'),
        widget=NumberInput(step='any'))
    duration_end = DecimalField(
        lazy_gettext('Duration to End (seconds)'),
        widget=NumberInput(step='any'))
    setpoint_start = DecimalField(
        lazy_gettext('Start Setpoint'),
        widget=NumberInput(step='any'))
    setpoint_end = DecimalField(
        lazy_gettext('End Setpoint'),
        widget=NumberInput(step='any'))
    output_id = StringField(lazy_gettext('Output'))
    output_state = StringField(lazy_gettext('State'))
    output_duration = DecimalField(
        lazy_gettext('Duration/Duty Cycle'),
        widget=NumberInput(step='any'))
    rename = SubmitField(lazy_gettext('Rename'))
    save = SubmitField(lazy_gettext('Save'))
    Delete = SubmitField(lazy_gettext('Delete'))
