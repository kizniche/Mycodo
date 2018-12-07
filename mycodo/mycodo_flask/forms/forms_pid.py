# -*- coding: utf-8 -*-
#
# forms_pid.py - PID Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput


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
        )],
        widget=NumberInput(step='any')
    )
    start_offset = DecimalField(
        lazy_gettext('Start Offset (seconds)'),
        widget=NumberInput(step='any'))
    max_measure_age = DecimalField(
        lazy_gettext('Max Age (seconds)'),
        validators=[validators.NumberRange(
            min=1.0,
            max=86400.0
        )],
        widget=NumberInput(step='any')
    )
    setpoint = DecimalField(
        lazy_gettext('Setpoint'),
        validators=[validators.NumberRange(
            min=-1000000,
            max=1000000
        )],
        widget=NumberInput(step='any')
    )
    band = DecimalField(
        lazy_gettext('Band (+/- Setpoint)'),
        widget=NumberInput(step='any'))
    store_lower_as_negative = BooleanField(lazy_gettext('Store Lower as Negative'))
    k_p = DecimalField(
        lazy_gettext('Kp Gain'),
        validators=[validators.NumberRange(
            min=0
        )],
        widget=NumberInput(step='any')
    )
    k_i = DecimalField(
        lazy_gettext('Ki Gain'),
        validators=[validators.NumberRange(
            min=0
        )],
        widget=NumberInput(step='any')
    )
    k_d = DecimalField(
        lazy_gettext('Kd Gain'),
        validators=[validators.NumberRange(
            min=0
        )],
        widget=NumberInput(step='any')
    )
    integrator_max = DecimalField(
        lazy_gettext('Integrator Min'),
        widget=NumberInput(step='any'))
    integrator_min = DecimalField(
        lazy_gettext('Integrator Max'),
        widget=NumberInput(step='any'))
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
    order_up = SubmitField(lazy_gettext('Up'))
    order_down = SubmitField(lazy_gettext('Down'))

    pid_autotune_noiseband = DecimalField(
        lazy_gettext('Noise Band'),
        widget=NumberInput(step='any'))
    pid_autotune_outstep = DecimalField(
        lazy_gettext('Outstep'),
        widget=NumberInput(step='any'))
    pid_autotune = SubmitField(lazy_gettext('Start Autotune'))


class PIDModRelayRaise(FlaskForm):
    raise_min_duration = DecimalField(
        lazy_gettext('Min On Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )],
        widget=NumberInput(step='any')
    )
    raise_max_duration = DecimalField(
        lazy_gettext('Max On Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )],
        widget=NumberInput(step='any')
    )
    raise_min_off_duration = DecimalField(
        lazy_gettext('Min Off Duration (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )],
        widget=NumberInput(step='any')
    )


class PIDModRelayLower(FlaskForm):
    lower_min_duration = DecimalField(
        lazy_gettext('Min On Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )],
        widget=NumberInput(step='any')
    )
    lower_max_duration = DecimalField(
        lazy_gettext('Max On Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )],
        widget=NumberInput(step='any')
    )
    lower_min_off_duration = DecimalField(
        lazy_gettext('Min Off Duration (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=86400
        )],
        widget=NumberInput(step='any')
    )


class PIDModPWMRaise(FlaskForm):
    raise_min_duty_cycle = DecimalField(
        lazy_gettext('Min Duty Cycle (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )],
        widget=NumberInput(step='any')
    )
    raise_max_duty_cycle = DecimalField(
        lazy_gettext('Max Duty Cycle (Raise)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )],
        widget=NumberInput(step='any')
    )


class PIDModPWMLower(FlaskForm):
    lower_min_duty_cycle = DecimalField(
        lazy_gettext('Min Duty Cycle (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )],
        widget=NumberInput(step='any')
    )
    lower_max_duty_cycle = DecimalField(
        lazy_gettext('Max Duty Cycle (Lower)'),
        validators=[validators.NumberRange(
            min=0,
            max=100
        )],
        widget=NumberInput(step='any')
    )
