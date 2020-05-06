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
from wtforms import FloatField
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
from mycodo.config_translations import TRANSLATIONS


class DataBase(FlaskForm):
    reorder_type = StringField('Reorder Type', widget=widgets.HiddenInput())
    list_visible_elements = SelectMultipleField('New Order')
    reorder = SubmitField(TRANSLATIONS['save_order']['title'])


class OutputAdd(FlaskForm):
    output_quantity = IntegerField(lazy_gettext('Quantity'))
    output_type = SelectField(
        choices=OUTPUTS,
        validators=[DataRequired()])
    output_add = SubmitField(TRANSLATIONS['add']['title'])


class OutputMod(FlaskForm):
    output_id = StringField('Output ID', widget=widgets.HiddenInput())
    output_pin = HiddenField('Output Pin')
    name = StringField(
        TRANSLATIONS['name']['title'],
        validators=[DataRequired()])
    output_mode = StringField(TRANSLATIONS['output_mode']['title'])
    location = StringField(lazy_gettext('Location'))
    i2c_bus = IntegerField(TRANSLATIONS['i2c_bus']['title'])
    baud_rate = IntegerField(TRANSLATIONS['baud_rate']['title'])
    gpio_location = IntegerField(TRANSLATIONS['gpio_location']['title'], widget=NumberInput())
    protocol = IntegerField(TRANSLATIONS['protocol']['title'], widget=NumberInput())
    pulse_length = IntegerField(TRANSLATIONS['pulse_length']['title'], widget=NumberInput())
    linux_command_user = StringField(TRANSLATIONS['linux_command_user']['title'])
    on_command = StringField(TRANSLATIONS['on_command']['title'])
    off_command = StringField(TRANSLATIONS['off_command']['title'])
    pwm_command = StringField(TRANSLATIONS['pwm_command']['title'])
    force_command = BooleanField(TRANSLATIONS['force_command']['title'])
    pwm_invert_signal = BooleanField(lazy_gettext('Invert Signal'))
    amps = DecimalField(
        TRANSLATIONS['amps']['title'],
        validators=[validators.NumberRange(
            min=0,
            max=50,
            message=lazy_gettext("The current draw of the device connected "
                                 "to this output, in amps.")
        )],
        widget=NumberInput(step='any')
    )
    on_state = SelectField(
        TRANSLATIONS['on_state']['title'],
        choices=[
            ("1", lazy_gettext('High')),
            ("0", lazy_gettext('Low'))
        ],
        validators=[Optional()]
    )
    state_startup = SelectField(TRANSLATIONS['state_startup']['title'])
    startup_value = FloatField(TRANSLATIONS['startup_value']['title'])
    state_shutdown = SelectField(TRANSLATIONS['state_shutdown']['title'])
    shutdown_value = FloatField(TRANSLATIONS['shutdown_value']['title'])
    trigger_functions_at_start = BooleanField(
        TRANSLATIONS['trigger_functions_at_start']['title'])
    pwm_hertz = IntegerField(
        TRANSLATIONS['pwm_hertz']['title'], widget=NumberInput())
    pwm_library = SelectField(
        TRANSLATIONS['pwm_library']['title'],
        choices=[
            ("pigpio_any", lazy_gettext('Any Pin, <= 40 kHz')),
            ("pigpio_hardware", lazy_gettext('Hardware Pin, <= 30 MHz'))
        ],
        validators=[DataRequired()]
    )
    flow_rate = DecimalField(
        TRANSLATIONS['flow_rate']['title'],
        widget=NumberInput(step='any'))
    save = SubmitField(TRANSLATIONS['save']['title'])
    delete = SubmitField(TRANSLATIONS['delete']['title'])
    order_up = SubmitField(TRANSLATIONS['up']['title'])
    order_down = SubmitField(TRANSLATIONS['down']['title'])
    on_submit = SubmitField(lazy_gettext('Turn On'))
