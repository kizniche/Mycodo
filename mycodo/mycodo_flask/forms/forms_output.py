# -*- coding: utf-8 -*-
#
# forms_output.py - Output Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
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


class OutputAdd(FlaskForm):
    relay_quantity = IntegerField(lazy_gettext('Quantity'))
    relay_type = StringField(lazy_gettext('Type'))
    relay_add = SubmitField(lazy_gettext('Add'))


class OutputMod(FlaskForm):
    relay_id = IntegerField('Relay ID', widget=widgets.HiddenInput())
    relay_pin = HiddenField('Relay Pin')
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    gpio = IntegerField(lazy_gettext('BCM Pin'))
    wiringpi_pin = IntegerField(lazy_gettext('WiringPi Pin'))
    protocol = IntegerField(lazy_gettext('Protocol'))
    pulse_length = IntegerField(lazy_gettext('Pulse Length'))
    bit_length = IntegerField(lazy_gettext('Bit length'))
    on_command = StringField(lazy_gettext('On Command'))
    off_command = StringField(lazy_gettext('Off Command'))
    amps = DecimalField(
        lazy_gettext('Current Draw (amps)'),
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message=lazy_gettext("The current draw of the device connected "
                                 "to this relay, in amps.")
        )]
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
    pwm_hertz = IntegerField(lazy_gettext('Frequency (Hertz)'))
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
        validators=[Optional()]
    )
    on_submit = SubmitField(lazy_gettext('Turn On'))
