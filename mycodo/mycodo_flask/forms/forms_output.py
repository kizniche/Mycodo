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
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.validators import Optional
from wtforms.widgets.html5 import NumberInput

from mycodo.config import OUTPUTS
from mycodo.config_translations import TOOLTIPS_SETTINGS


class DataBase(FlaskForm):
    reorder_type = StringField('Reorder Type', widget=widgets.HiddenInput())
    list_visible_elements = SelectMultipleField('New Order')
    reorder = SubmitField(lazy_gettext('Save Order'))


class OutputAdd(FlaskForm):
    output_quantity = IntegerField(lazy_gettext('Quantity'))
    output_type = SelectField(
        choices=OUTPUTS,
        validators=[DataRequired()]
    )
    output_add = SubmitField(lazy_gettext('Add'))


class OutputMod(FlaskForm):
    output_id = StringField('Output ID', widget=widgets.HiddenInput())
    output_pin = HiddenField('Output Pin')
    name = StringField(
        TOOLTIPS_SETTINGS['name']['title'],
        validators=[DataRequired()]
    )
    location = StringField(lazy_gettext('Location'))
    i2c_bus = IntegerField(
        TOOLTIPS_SETTINGS['i2c_bus']['title'])
    baud_rate = IntegerField(
        TOOLTIPS_SETTINGS['baud_rate']['title'])
    gpio_location = IntegerField(
        TOOLTIPS_SETTINGS['gpio_location']['title'], widget=NumberInput())
    protocol = IntegerField(
        TOOLTIPS_SETTINGS['protocol']['title'], widget=NumberInput())
    pulse_length = IntegerField(
        TOOLTIPS_SETTINGS['pulse_length']['title'], widget=NumberInput())
    on_command = StringField(
        TOOLTIPS_SETTINGS['on_command']['title'])
    off_command = StringField(
        TOOLTIPS_SETTINGS['off_command']['title'])
    pwm_command = StringField(
        TOOLTIPS_SETTINGS['pwm_command']['title'])
    pwm_invert_signal = BooleanField(lazy_gettext('Invert Signal'))
    amps = DecimalField(
        TOOLTIPS_SETTINGS['amps']['title'],
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message=lazy_gettext("The current draw of the device connected "
                                 "to this output, in amps.")
        )],
        widget=NumberInput(step='any')
    )
    trigger = SelectField(
        TOOLTIPS_SETTINGS['trigger']['title'],
        choices=[
            ("1", lazy_gettext('High')),
            ("0", lazy_gettext('Low'))
        ],
        validators=[Optional()]
    )
    on_at_start = SelectField(
        TOOLTIPS_SETTINGS['on_at_start']['title'],
        choices=[
            ("-1", lazy_gettext('Neither')),
            ("1", lazy_gettext('On')),
            ("0", lazy_gettext('Off'))
        ],
        validators=[DataRequired()]
    )
    trigger_functions_at_start = BooleanField(
        TOOLTIPS_SETTINGS['trigger_functions_at_start']['title'])
    pwm_hertz = IntegerField(
        TOOLTIPS_SETTINGS['pwm_hertz']['title'], widget=NumberInput())
    pwm_library = SelectField(
        TOOLTIPS_SETTINGS['pwm_library']['title'],
        choices=[
            ("pigpio_any", lazy_gettext('Any Pin, <= 40 kHz')),
            ("pigpio_hardware", lazy_gettext('Hardware Pin, <= 30 MHz'))
        ],
        validators=[DataRequired()]
    )
    flow_rate = DecimalField(
        TOOLTIPS_SETTINGS['trigger_functions_at_start']['title'],
        widget=NumberInput(step='any')
    )
    save = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))
    order_up = SubmitField(lazy_gettext('Up'))
    order_down = SubmitField(lazy_gettext('Down'))
    on_submit = SubmitField(lazy_gettext('Turn On'))
