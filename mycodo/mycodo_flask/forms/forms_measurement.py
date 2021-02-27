# -*- coding: utf-8 -*-
#
# forms_measurement.py - Measurement Flask Forms
#
import logging

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.widgets.html5 import NumberInput

from mycodo.config_translations import TRANSLATIONS

logger = logging.getLogger("mycodo.forms_measurement")


class MeasurementMod(FlaskForm):
    device_id = StringField('Input ID', widget=widgets.HiddenInput())
    measurement_id = StringField(widget=widgets.HiddenInput())
    device_type = StringField(widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    select_measurement_unit = StringField(TRANSLATIONS['select_measurement_unit']['title'])

    scale_from_min = DecimalField(
        TRANSLATIONS['scale_from_min']['title'],
        widget=NumberInput(step='any'))
    scale_from_max = DecimalField(
        TRANSLATIONS['scale_from_max']['title'],
        widget=NumberInput(step='any'))
    scale_to_min = DecimalField(
        TRANSLATIONS['scale_to_min']['title'],
        widget=NumberInput(step='any'))
    scale_to_max = DecimalField(
        TRANSLATIONS['scale_to_max']['title'],
        widget=NumberInput(step='any'))
    invert_scale = BooleanField(
        TRANSLATIONS['invert_scale']['title'])

    rescaled_measurement_unit = StringField(lazy_gettext('Rescaled Measurement'))
    convert_to_measurement_unit = StringField(TRANSLATIONS['convert_to_measurement_unit']['title'])

    measurement_mod = SubmitField(TRANSLATIONS['save']['title'])
