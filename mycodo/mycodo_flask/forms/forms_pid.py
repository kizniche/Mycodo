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
        lazy_gettext('Quantity'),
        render_kw={"placeholder": lazy_gettext("Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    pidAddSubmit = SubmitField(lazy_gettext('Add PIDs'))


class PIDModBase(FlaskForm):
    pid_id = IntegerField('PID ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    measurement = StringField(
        lazy_gettext('Measurement'),
        validators=[DataRequired()]
    )
    direction = SelectField(
        lazy_gettext('Direction'),
        choices=[
            ('raise', lazy_gettext('Raise')),
            ('lower', lazy_gettext('Lower')),
            ('both', lazy_gettext('Both'))
        ],
        validators=[DataRequired()]
    )
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    max_measure_age = DecimalField(
        lazy_gettext('Max Age (seconds)'),
        validators=[validators.NumberRange(
            min=5.0,
            max=86400.0
        )]
    )
    setpoint = DecimalField(
        lazy_gettext('Setpoint'),
        validators=[validators.NumberRange(
            min=-1000000,
            max=1000000
        )]
    )
    k_p = DecimalField(
        lazy_gettext('Kp Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_i = DecimalField(
        lazy_gettext('Ki Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    k_d = DecimalField(
        lazy_gettext('Kd Gain'),
        validators=[validators.NumberRange(
            min=0
        )]
    )
    integrator_max = DecimalField(lazy_gettext('Integrator Min'))
    integrator_min = DecimalField(lazy_gettext('Integrator Max'))
    raise_relay_id = StringField(lazy_gettext('Output (Raise)'))
    lower_relay_id = StringField(lazy_gettext('Output (Lower)'))
    method_id = IntegerField(
        'Setpoint Tracking Method', widget=widgets.HiddenInput())
    save = SubmitField(lazy_gettext('Save'))
    hold = SubmitField(lazy_gettext('Hold'))
    pause = SubmitField(lazy_gettext('Pause'))
    resume = SubmitField(lazy_gettext('Resume'))
    delete = SubmitField(lazy_gettext('Delete'))
    activate = SubmitField(lazy_gettext('Activate'))
    deactivate = SubmitField(lazy_gettext('Deactivate'))
    reorder_up = SubmitField(lazy_gettext('Up'))
    reorder_down = SubmitField(lazy_gettext('Down'))


class PIDModRelayRaise(FlaskForm):
    raise_min_duration = DecimalField(
        lazy_gettext('Min On Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_max_duration = DecimalField(
        lazy_gettext('Max On Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    raise_min_off_duration = DecimalField(
        lazy_gettext('Min Off Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )


class PIDModRelayLower(FlaskForm):
    lower_min_duration = DecimalField(
        lazy_gettext('Min On Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_max_duration = DecimalField(
        lazy_gettext('Max On Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )
    lower_min_off_duration = DecimalField(
        lazy_gettext('Min Off Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )]
    )


class PIDModPWMRaise(FlaskForm):
    raise_min_duty_cycle = DecimalField(
        lazy_gettext('Min Duty Cycle (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )
    raise_max_duty_cycle = DecimalField(
        lazy_gettext('Max Duty Cycle (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )


class PIDModPWMLower(FlaskForm):
    lower_min_duty_cycle = DecimalField(
        lazy_gettext('Min Duty Cycle (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )
    lower_max_duty_cycle = DecimalField(
        lazy_gettext('Max Duty Cycle (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )]
    )
