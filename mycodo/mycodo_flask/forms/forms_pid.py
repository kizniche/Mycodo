# -*- coding: utf-8 -*-
#
# forms_pid.py - PID Flask Forms
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


class PIDAdd(FlaskForm):
    numberPIDs = IntegerField(
        lazy_gettext(u'Quantity'),
        render_kw={"placeholder": lazy_gettext(u"Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    pidAddSubmit = SubmitField(lazy_gettext(u'Add PIDs'))


class PIDModBase(FlaskForm):
    pid_id = IntegerField('PID ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    measurement = StringField(
        lazy_gettext(u'Measurement'),
        validators=[DataRequired()]
    )
    direction = SelectField(
        lazy_gettext(u'Direction'),
        choices=[
            ('raise', lazy_gettext(u'Raise')),
            ('lower', lazy_gettext(u'Lower')),
            ('both', lazy_gettext(u'Both'))
        ],
        validators=[DataRequired()]
    )
    period = DecimalField(
        lazy_gettext(u'Period (seconds)'),
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    max_measure_age = DecimalField(
        lazy_gettext(u'Max Age (seconds)'),
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    setpoint = DecimalField(
        lazy_gettext(u'Setpoint'),
        validators=[validators.NumberRange(
            min=-1000000,
            max=1000000
        )]
    )
    k_p = DecimalField(
        lazy_gettext(u'Kp Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_i = DecimalField(
        lazy_gettext(u'Ki Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_d = DecimalField(
        lazy_gettext(u'Kd Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    integrator_max = DecimalField(lazy_gettext(u'Integrator Min'))
    integrator_min = DecimalField(lazy_gettext(u'Integrator Max'))
    raise_relay_id = StringField(lazy_gettext(u'Output (Raise)'))
    lower_relay_id = StringField(lazy_gettext(u'Output (Lower)'))
    method_id = IntegerField(
        'Setpoint Tracking Method', widget=widgets.HiddenInput())
    save = SubmitField(lazy_gettext(u'Save'))
    hold = SubmitField(lazy_gettext(u'Hold'))
    pause = SubmitField(lazy_gettext(u'Pause'))
    resume = SubmitField(lazy_gettext(u'Resume'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    activate = SubmitField(lazy_gettext(u'Activate'))
    deactivate = SubmitField(lazy_gettext(u'Deactivate'))
    reorder_up = SubmitField(lazy_gettext(u'Up'))
    reorder_down = SubmitField(lazy_gettext(u'Down'))


class PIDModRelayRaise(FlaskForm):
    raise_min_duration = DecimalField(
        lazy_gettext(u'Min On Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_max_duration = DecimalField(
        lazy_gettext(u'Max On Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_min_off_duration = DecimalField(
        lazy_gettext(u'Min Off Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )


class PIDModRelayLower(FlaskForm):
    lower_min_duration = DecimalField(
        lazy_gettext(u'Min On Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_max_duration = DecimalField(
        lazy_gettext(u'Max On Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_min_off_duration = DecimalField(
        lazy_gettext(u'Min Off Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )


class PIDModPWMRaise(FlaskForm):
    raise_min_duty_cycle = DecimalField(
        lazy_gettext(u'Min Duty Cycle (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )
    raise_max_duty_cycle = DecimalField(
        lazy_gettext(u'Max Duty Cycle (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )


class PIDModPWMLower(FlaskForm):
    lower_min_duty_cycle = DecimalField(
        lazy_gettext(u'Min Duty Cycle (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )
    lower_max_duty_cycle = DecimalField(
        lazy_gettext(u'Max Duty Cycle (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )
