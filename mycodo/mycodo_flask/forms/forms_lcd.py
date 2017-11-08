# -*- coding: utf-8 -*-
#
# forms_lcd.py - LCD Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired


class LCDAdd(FlaskForm):
    quantity = IntegerField(
        lazy_gettext(u'Quantity'),
        render_kw={"placeholder": lazy_gettext(u"Quantity")},
        validators=[validators.NumberRange(
            min=1,
            max=20
        )]
    )
    add = SubmitField(lazy_gettext(u'Add LCDs'))


class LCDMod(FlaskForm):
    lcd_id = IntegerField('LCD ID', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    location = StringField(
        lazy_gettext(u'I2C Address'),
        validators=[DataRequired()]
    )
    i2c_bus = IntegerField(
        lazy_gettext(u'I2C Bus'),
        validators=[DataRequired()]
    )
    multiplexer_address = StringField(
        lazy_gettext(u'Multiplexer I2C Address')
    )
    multiplexer_channel = IntegerField(
        lazy_gettext(u'Multiplexer Channel'),
        validators=[
            validators.NumberRange(
                min=0,
                max=8
            )]
    )
    period = DecimalField(
        lazy_gettext(u'Period (seconds)'),
        render_kw={"placeholder": lazy_gettext(u"Period")},
        validators=[validators.NumberRange(
            min=5,
            max=86400,
            message=lazy_gettext(u"Duration between calculating LCD output "
                                 u"and applying to regulation must be between "
                                 u"5 and 86400 seconds.")
        )]
    )
    lcd_type = SelectField(
        lazy_gettext(u'LCD Type'),
        choices=[
            ('16x2', '16x2'),
            ('20x4', '20x4')
        ],
        validators=[DataRequired()]
    )
    line_1_display = StringField(
        lazy_gettext(u'Line 1 Display')
    )
    line_2_display = StringField(
        lazy_gettext(u'Line 2 Display')
    )
    line_3_display = StringField(
        lazy_gettext(u'Line 3 Display')
    )
    line_4_display = StringField(
        lazy_gettext(u'Line 4 Display')
    )
    save = SubmitField(lazy_gettext(u'Save'))
    delete = SubmitField(lazy_gettext(u'Delete'))
    activate = SubmitField(lazy_gettext(u'Activate'))
    deactivate = SubmitField(lazy_gettext(u'Deactivate'))
    reorder_up = SubmitField(lazy_gettext(u'Up'))
    reorder_down = SubmitField(lazy_gettext(u'Down'))
    reset_flashing = SubmitField(lazy_gettext(u'Reset Flashing'))
