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
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired
from wtforms.validators import Optional


class OutputAdd(FlaskForm):
    relay_quantity = IntegerField(lazy_gettext(u'Quantity'))
    relay_type = StringField(lazy_gettext(u'Type'))
    relay_add = SubmitField(lazy_gettext(u'Add Output Device'))
    relay_cond_quantity = IntegerField(lazy_gettext(u'Quantity'))
    relay_cond_add = SubmitField(lazy_gettext(u'Add Relay Conditional'))


class OutputMod(FlaskForm):
    relay_id = IntegerField('Relay ID', widget=widgets.HiddenInput())
    relay_pin = HiddenField('Relay Pin')
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    gpio = IntegerField(lazy_gettext(u'BCM Pin'))
    wiringpi_pin = IntegerField(lazy_gettext(u'WiringPi Pin'))
    protocol = IntegerField(lazy_gettext(u'Protocol'))
    pulse_length = IntegerField(lazy_gettext(u'Pulse Length'))
    bit_length = IntegerField(lazy_gettext(u'Bit length'))
    on_command = StringField(lazy_gettext(u'On Command'))
    off_command = StringField(lazy_gettext(u'Off Command'))
    amps = DecimalField(
        lazy_gettext(u'Current Draw (amps)'),
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message=lazy_gettext(u"The current draw of the device connected "
                                 u"to this relay, in amps.")
        )]
    )
    trigger = SelectField(
        lazy_gettext(u'On Trigger'),
        choices=[
            ("1", lazy_gettext(u'High')),
            ("0", lazy_gettext(u'Low'))
        ],
        validators=[Optional()]
    )
    on_at_start = SelectField(
        lazy_gettext(u'Start State'),
        choices=[
            ("-1", lazy_gettext(u'Neither')),
            ("1", lazy_gettext(u'On')),
            ("0", lazy_gettext(u'Off'))
        ],
        validators=[DataRequired()]
    )
    pwm_hertz = IntegerField(lazy_gettext(u'Frequency (Hertz)'))
    pwm_library = SelectField(
        lazy_gettext(u'Library'),
        choices=[
            ("pigpio_any", lazy_gettext(u'Any Pin, <= 40 kHz')),
            ("pigpio_hardware", lazy_gettext(u'Hardware Pin, <= 30 MHz'))
        ],
        validators=[DataRequired()]
    )
    save = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    order_up = SubmitField(lazy_gettext(u'Up'))
    order_down = SubmitField(lazy_gettext(u'Down'))
    pwm_duty_cycle_on = DecimalField(
        '{} (%)'.format(lazy_gettext(u'Duty Cycle')),
        validators=[Optional()]
    )
    on_submit = SubmitField(lazy_gettext(u'Turn On'))
