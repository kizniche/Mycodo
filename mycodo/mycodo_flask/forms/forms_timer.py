# -*- coding: utf-8 -*-
#
# forms_timer.py - Timer Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired


class TimerBase(FlaskForm):
    timer_id = StringField('Timer ID', widget=widgets.HiddenInput())
    timer_type = SelectField(
        lazy_gettext('Timer Type'),
        choices=[
            ('', lazy_gettext('Select a Timer Type')),
            ('time', lazy_gettext('Daily Time Point')),
            ('timespan', lazy_gettext('Daily Time Span')),
            ('duration', lazy_gettext('Duration')),
            ('pwm_method', lazy_gettext('PWM Method (Duty Cycle)'))
        ],
        validators=[DataRequired()]
    )
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    output_id = StringField(lazy_gettext('Output'))
    create = SubmitField(lazy_gettext('Add'))
    modify = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))
    activate = SubmitField(lazy_gettext('Activate'))
    deactivate = SubmitField(lazy_gettext('Deactivate'))
    order_up = SubmitField(lazy_gettext('Up'))
    order_down = SubmitField(lazy_gettext('Down'))


class TimerTimePoint(FlaskForm):
    state = SelectField(
        lazy_gettext('State'),
        choices=[
            ('on', lazy_gettext('On')),
            ('off', lazy_gettext('Off'))
        ],
        validators=[DataRequired()]
    )
    time_start = StringField(lazy_gettext('Start Time'))
    time_on_duration = DecimalField(
        lazy_gettext('On (seconds)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )


class TimerTimeSpan(FlaskForm):
    state = SelectField(
        lazy_gettext('State'),
        choices=[
            ('on', lazy_gettext('On')),
            ('off', lazy_gettext('Off'))
        ],
        validators=[DataRequired()]
    )
    time_start_duration = StringField(lazy_gettext('Start Time'))
    time_end_duration = StringField(lazy_gettext('End Time'))


class TimerDuration(FlaskForm):
    duration_on = DecimalField(lazy_gettext('On (seconds)'))
    duration_off = DecimalField(lazy_gettext('Off (seconds)'))


class TimerPWMMethod(FlaskForm):
    method_id = StringField(lazy_gettext('Method'))
    method_period = StringField(lazy_gettext('Period (seconds)'))
