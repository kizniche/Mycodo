# -*- coding: utf-8 -*-
#
# forms_pid.py - PID Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired


class PIDModBase(FlaskForm):
    pid_id = StringField('PID ID', widget=widgets.HiddenInput())
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
            min=1.0,
            max=86400.0
        )]
    )
    max_measure_age = DecimalField(
        lazy_gettext('Max Age (seconds)'),
        validators=[validators.NumberRange(
            min=1.0,
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
    band = DecimalField(lazy_gettext('Band (+/- Setpoint)'))
    store_lower_as_negative = BooleanField(lazy_gettext('Store Lower as Negative'))
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
    raise_output_id = StringField(lazy_gettext('Output (Raise)'))
    lower_output_id = StringField(lazy_gettext('Output (Lower)'))
    method_id = StringField(
        'Setpoint Tracking Method', widget=widgets.HiddenInput())
    pid_mod = SubmitField(lazy_gettext('Save'))
    pid_hold = SubmitField(lazy_gettext('Hold'))
    pid_pause = SubmitField(lazy_gettext('Pause'))
    pid_resume = SubmitField(lazy_gettext('Resume'))
    pid_delete = SubmitField(lazy_gettext('Delete'))
    pid_activate = SubmitField(lazy_gettext('Activate'))
    pid_deactivate = SubmitField(lazy_gettext('Deactivate'))
    pid_order_up = SubmitField(lazy_gettext('Up'))
    pid_order_down = SubmitField(lazy_gettext('Down'))

    pid_autotune_noiseband = DecimalField(lazy_gettext('Noise Band'))
    pid_autotune = SubmitField(lazy_gettext('Start Autotune'))


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
