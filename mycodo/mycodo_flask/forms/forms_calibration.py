# -*- coding: utf-8 -*-
#
# forms_calibration.py - Calibration Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput

from mycodo.config import CALIBRATION_DEVICES


class Calibration(FlaskForm):
    selection = SelectField(
        'Device to Calibrate',
        choices=CALIBRATION_DEVICES,
        validators=[DataRequired()]
    )
    submit = SubmitField(lazy_gettext('Select'))


# Atlas Scientific EZO Pump
class CalibrationAtlasEZOPump(FlaskForm):
    hidden_output_id = StringField('Output ID', widget=widgets.HiddenInput())
    hidden_current_stage = StringField('Stage', widget=widgets.HiddenInput())
    selected_output_id = StringField(lazy_gettext('Atlas EZO Pump'))
    start_calibration = SubmitField(lazy_gettext('Begin Calibration'))
    clear_calibration = SubmitField(lazy_gettext('Clear Calibration'))
    ml_to_dispense = DecimalField(
        'Milliliters (ml) To Dispense', widget=NumberInput(step='any'))
    ml_dispensed = DecimalField(
        'Milliliters (ml) Dispensed', widget=NumberInput(step='any'))
    go_to_next_stage = SubmitField(lazy_gettext('Continue to Next Stage'))
    go_to_last_stage = SubmitField(lazy_gettext('Continue to Next Stage'))


# Atlas Scientific EC sensor
class CalibrationAtlasEC(FlaskForm):
    hidden_input_id = StringField('Input ID', widget=widgets.HiddenInput())
    hidden_current_stage = StringField('Stage', widget=widgets.HiddenInput())
    hidden_selected_point_calibration = StringField(
        'EC Points to Calibrate', widget=widgets.HiddenInput())
    hidden_point_low_uS = StringField(
        'Low Solution (μS)', widget=widgets.HiddenInput())
    hidden_point_high_uS = StringField(
        'High Solution (μS)', widget=widgets.HiddenInput())
    selected_input_id = StringField(lazy_gettext('Atlas EC Sensor'))
    point_calibration = StringField(lazy_gettext('EC Points to Calibrate'))
    point_low_uS = IntegerField(lazy_gettext('Low Solution (μS)'))
    point_high_uS = IntegerField(lazy_gettext('High Solution (μS)'))
    start_calibration = SubmitField(lazy_gettext('Begin Calibration'))
    go_to_next_stage = SubmitField(lazy_gettext('Continue to Next Stage'))
    go_to_last_stage = SubmitField(lazy_gettext('Continue to Next Stage'))


# Atlas Scientific pH sensor
class CalibrationAtlasph(FlaskForm):
    hidden_input_id = StringField('Input ID', widget=widgets.HiddenInput())
    hidden_current_stage = StringField('Stage', widget=widgets.HiddenInput())
    hidden_selected_point_calibration = StringField(
        'pH Points to Calibrate', widget=widgets.HiddenInput())
    selected_input_id = StringField(lazy_gettext('Atlas pH Sensor'))
    clear_calibration = SubmitField(lazy_gettext('Clear Calibration'))
    temperature = DecimalField(
        lazy_gettext('Temperature'), widget=NumberInput(step='any'))
    point_calibration = StringField(lazy_gettext('pH Points to Calibrate'))
    start_calibration = SubmitField(lazy_gettext('Begin Calibration'))
    go_to_next_stage = SubmitField(lazy_gettext('Continue to Next Stage'))
    go_to_last_stage = SubmitField(lazy_gettext('Continue to Next Stage'))


# DS18B20 Temperature sensor
class SetupDS18B20(FlaskForm):
    device_id = StringField(lazy_gettext('Device'))
    resolution = IntegerField(
        lazy_gettext('Resolution'), widget=NumberInput())
    set_resolution = SubmitField(lazy_gettext('Set Resolution'))
