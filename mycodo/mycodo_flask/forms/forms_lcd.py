# -*- coding: utf-8 -*-
#
# forms_lcd.py - LCD Flask Forms
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
from wtforms.validators import Optional
from wtforms.widgets.html5 import NumberInput

from mycodo.config import LCDS
from mycodo.config_translations import TRANSLATIONS


class LCDAdd(FlaskForm):
    lcd_type = SelectField(
        lazy_gettext('LCD Type'),
        choices=LCDS,
        validators=[DataRequired()]
    )
    add = SubmitField(TRANSLATIONS['add']['title'])


class LCDMod(FlaskForm):
    lcd_id = StringField('LCD ID', widget=widgets.HiddenInput())
    name = StringField(
        TRANSLATIONS['name']['title'],
        validators=[DataRequired()]
    )
    location = StringField(
        "{op} ({unit})".format(op=lazy_gettext('Address'),
                               unit=lazy_gettext('I<sup>2</sup>C'))
    )
    i2c_bus = IntegerField(
        "{op} ({unit})".format(op=lazy_gettext('Bus'),
                               unit=lazy_gettext('I<sup>2</sup>C')),
        validators=[DataRequired()],
        widget=NumberInput()
    )
    pin_reset = IntegerField(
        "{pin}: {reset}".format(pin=TRANSLATIONS['pin']['title'],
                                reset=TRANSLATIONS['reset']['title']),
        validators=[Optional()]
    )
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        validators=[validators.NumberRange(
            min=5,
            max=86400,
            message=lazy_gettext("Duration between calculating LCD output "
                                 "and applying to regulation must be between "
                                 "5 and 86400 seconds.")
        )],
        widget=NumberInput(step='any')
    )
    add_display = SubmitField(lazy_gettext('Add Display Set'))
    save = SubmitField(TRANSLATIONS['save']['title'])
    delete = SubmitField(TRANSLATIONS['delete']['title'])
    activate = SubmitField(TRANSLATIONS['activate']['title'])
    deactivate = SubmitField(TRANSLATIONS['deactivate']['title'])
    reorder_up = SubmitField(TRANSLATIONS['up']['title'])
    reorder_down = SubmitField(TRANSLATIONS['down']['title'])
    reset_flashing = SubmitField(lazy_gettext('Reset LCD'))


class LCDModDisplay(FlaskForm):
    lcd_id = StringField('LCD ID', widget=widgets.HiddenInput())
    lcd_data_id = StringField('LCD Data ID', widget=widgets.HiddenInput())
    line_1_display = StringField("{}: 1".format(TRANSLATIONS['line']['title']))
    line_1_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_1_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_2_display = StringField("{}: 2".format(TRANSLATIONS['line']['title']))
    line_2_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_2_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_3_display = StringField("{}: 3".format(TRANSLATIONS['line']['title']))
    line_3_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_3_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_4_display = StringField("{}: 4".format(TRANSLATIONS['line']['title']))
    line_4_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_4_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_5_display = StringField("{}: 5".format(TRANSLATIONS['line']['title']))
    line_5_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_5_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_6_display = StringField("{}: 6".format(TRANSLATIONS['line']['title']))
    line_6_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_6_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_7_display = StringField("{}: 7".format(TRANSLATIONS['line']['title']))
    line_7_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_7_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_8_display = StringField("{}: 8".format(TRANSLATIONS['line']['title']))
    line_8_max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_8_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )

    save_display = SubmitField(TRANSLATIONS['save']['title'])
    delete_display = SubmitField(TRANSLATIONS['delete']['title'])
