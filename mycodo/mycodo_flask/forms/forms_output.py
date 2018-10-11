# -*- coding: utf-8 -*-
#
# forms_output.py - Output Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.validators import Optional
from wtforms.widgets.html5 import NumberInput

from mycodo.config import OUTPUTS


class OutputAdd(FlaskForm):
    output_quantity = IntegerField(lazy_gettext('Quantity'))
    output_type = SelectField(
        choices=OUTPUTS,
        validators=[DataRequired()]
    )
    output_add = SubmitField(lazy_gettext('Add'))


class OutputMod(FlaskForm):
    output_id = StringField('Relay ID', widget=widgets.HiddenInput())
    output_pin = HiddenField('Relay Pin')
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    pin = IntegerField(
        lazy_gettext('Pin'), widget = NumberInput())
    protocol = IntegerField(
        lazy_gettext('Protocol'), widget = NumberInput())
    pulse_length = IntegerField(
        lazy_gettext('Pulse Length'), widget = NumberInput())
    on_command = StringField(lazy_gettext('On Command'))
    off_command = StringField(lazy_gettext('Off Command'))
    pwm_command = StringField(lazy_gettext('PWM Command'))
    pwm_invert_signal = BooleanField(lazy_gettext('Invert Signal'))
    amps = DecimalField(
        lazy_gettext('Current Draw (amps)'),
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message=lazy_gettext("The current draw of the device connected "
                                 "to this output, in amps.")
        )],
        widget = NumberInput()
    )
    trigger = SelectField(
        lazy_gettext('On Trigger'),
        choices=[
            ("1", lazy_gettext('High')),
            ("0", lazy_gettext('Low'))
        ],
        validators=[Optional()]
    )
    on_at_start = SelectField(
        lazy_gettext('Start State'),
        choices=[
            ("-1", lazy_gettext('Neither')),
            ("1", lazy_gettext('On')),
            ("0", lazy_gettext('Off'))
        ],
        validators=[DataRequired()]
    )
    pwm_hertz = IntegerField(
        lazy_gettext('Frequency (Hertz)'), widget = NumberInput())
    pwm_library = SelectField(
        lazy_gettext('Library'),
        choices=[
            ("pigpio_any", lazy_gettext('Any Pin, <= 40 kHz')),
            ("pigpio_hardware", lazy_gettext('Hardware Pin, <= 30 MHz'))
        ],
        validators=[DataRequired()]
    )
    save = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))
    order_up = SubmitField(lazy_gettext('Up'))
    order_down = SubmitField(lazy_gettext('Down'))
    pwm_duty_cycle_on = DecimalField(
        '{} (%)'.format(lazy_gettext('Duty Cycle')),
        validators=[Optional()],
        widget = NumberInput()
    )
    on_submit = SubmitField(lazy_gettext('Turn On'))
