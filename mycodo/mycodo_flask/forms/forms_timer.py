# -*- coding: utf-8 -*-
#
# forms_timer.py - Timer Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired


class TimerBase(FlaskForm):
    timer_id = IntegerField('Timer ID', widget=widgets.HiddenInput())
    timer_type = SelectField(
        lazy_gettext(u'Timer Type'),
        choices=[
            ('', lazy_gettext(u'Select a Timer Type')),
            ('time', lazy_gettext(u'Daily Time Point')),
            ('timespan', lazy_gettext(u'Daily Time Span')),
            ('duration', lazy_gettext(u'Duration')),
            ('pwm_method', lazy_gettext(u'PWM Method (Duty Cycle)'))
        ],
        validators=[DataRequired()]
    )
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    relay_id = StringField(lazy_gettext(u'Output'))
    create = SubmitField(lazy_gettext(u'Save'))
    modify = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    activate = SubmitField(lazy_gettext(u'Activate'))
    deactivate = SubmitField(lazy_gettext(u'Deactivate'))
    order_up = SubmitField(lazy_gettext(u'Up'))
    order_down = SubmitField(lazy_gettext(u'Down'))


class TimerTimePoint(FlaskForm):
    state = SelectField(
        lazy_gettext(u'State'),
        choices=[
            ('on', lazy_gettext(u'On')),
            ('off', lazy_gettext(u'Off'))
        ],
        validators=[DataRequired()]
    )
    time_start = StringField(lazy_gettext(u'Start Time'))
    time_on_duration = DecimalField(
        lazy_gettext(u'On (seconds)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )


class TimerTimeSpan(FlaskForm):
    state = SelectField(
        lazy_gettext(u'State'),
        choices=[
            ('on', lazy_gettext(u'On')),
            ('off', lazy_gettext(u'Off'))
        ],
        validators=[DataRequired()]
    )
    time_start_duration = StringField(lazy_gettext(u'Start Time'))
    time_end_duration = StringField(lazy_gettext(u'End Time'))


class TimerDuration(FlaskForm):
    duration_on = DecimalField(lazy_gettext(u'On (seconds)'))
    duration_off = DecimalField(lazy_gettext(u'Off (seconds)'))


class TimerPWMMethod(FlaskForm):
    method_id = StringField(lazy_gettext(u'Method'))
    method_period = StringField(lazy_gettext(u'Period (seconds)'))
