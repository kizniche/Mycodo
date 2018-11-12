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
from wtforms.widgets.html5 import NumberInput


class LCDAdd(FlaskForm):
    quantity = IntegerField(
        lazy_gettext('Quantity'),
        validators=[validators.NumberRange(
            min=1,
            max=20
        )],
        widget=NumberInput()
    )
    add = SubmitField(lazy_gettext('Add'))


class LCDMod(FlaskForm):
    lcd_id = StringField('LCD ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    location = StringField(
        "{op} ({unit})".format(op=lazy_gettext('Address'),
                               unit=lazy_gettext('I<sup>2</sup>C')),
        validators=[DataRequired()]
    )
    i2c_bus = IntegerField(
        "{op} ({unit})".format(op=lazy_gettext('Bus'),
                               unit=lazy_gettext('I<sup>2</sup>C')),
        validators=[DataRequired()],
        widget=NumberInput()
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
    lcd_type = SelectField(
        lazy_gettext('LCD Type'),
        choices=[
            ('16x2', '16x2'),
            ('20x4', '20x4')
        ],
        validators=[DataRequired()]
    )
    add_display = SubmitField(lazy_gettext('Add Display Set'))
    save = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))
    activate = SubmitField(lazy_gettext('Activate'))
    deactivate = SubmitField(lazy_gettext('Deactivate'))
    reorder_up = SubmitField(lazy_gettext('Up'))
    reorder_down = SubmitField(lazy_gettext('Down'))
    reset_flashing = SubmitField(lazy_gettext('Reset LCD'))


class LCDModDisplay(FlaskForm):
    lcd_id = StringField('LCD ID', widget=widgets.HiddenInput())
    lcd_data_id = StringField('LCD Data ID', widget=widgets.HiddenInput())
    line_1_display = StringField(lazy_gettext('Line 1'))
    line_1_max_age = IntegerField(
        lazy_gettext('Max Age (seconds)'),
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_1_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_2_display = StringField(lazy_gettext('Line 2'))
    line_2_max_age = IntegerField(
        lazy_gettext('Max Age (seconds)'),
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_2_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_3_display = StringField(lazy_gettext('Line 3'))
    line_3_max_age = IntegerField(
        lazy_gettext('Max Age (seconds)'),
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_3_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    line_4_display = StringField(lazy_gettext('Line 4'))
    line_4_max_age = IntegerField(
        lazy_gettext('Max Age (seconds)'),
        validators=[validators.NumberRange(min=1, max=999999999)],
        widget=NumberInput()
    )
    line_4_decimal_places = IntegerField(
        lazy_gettext('Decimal Places'),
        validators=[validators.NumberRange(min=0)],
        widget=NumberInput()
    )
    save_display = SubmitField(lazy_gettext('Save'))
    delete_display = SubmitField(lazy_gettext('Delete'))
