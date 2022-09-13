# -*- coding: utf-8 -*-
#
# forms_trigger.py - Function Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import widgets
from wtforms.widgets import NumberInput

from mycodo.config_translations import TRANSLATIONS


class Trigger(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])

    # Edge detection
    measurement = StringField(TRANSLATIONS['measurement']['title'])
    edge_detected = StringField(lazy_gettext('If Edge Detected'))

    # Sunrise/sunset
    rise_or_set = StringField(lazy_gettext('Rise or Set'))
    latitude = DecimalField(
        lazy_gettext('Latitude (decimal)'), widget=NumberInput(step='any'))
    longitude = DecimalField(
        lazy_gettext('Longitude (decimal)'), widget=NumberInput(step='any'))
    zenith = DecimalField(
        lazy_gettext('Zenith'), widget=NumberInput(step='any'))
    date_offset_days = IntegerField(
        lazy_gettext('Date Offset (days)'), widget=NumberInput())
    time_offset_minutes = IntegerField(
        lazy_gettext('Time Offset (minutes)'), widget=NumberInput())

    # Receive infrared from remote
    program = StringField(lazy_gettext('Program'))
    word = StringField(lazy_gettext('Word'))

    # Timer
    period = DecimalField(
        "{} ({})".format(lazy_gettext('Period'), lazy_gettext('Seconds')), widget=NumberInput(step='any'))
    timer_start_offset = IntegerField(
        "{} ({})".format(lazy_gettext('Start Offset'), lazy_gettext('Seconds')), widget=NumberInput())
    timer_start_time = StringField(lazy_gettext('Start Time (HH:MM)'))
    timer_end_time = StringField(lazy_gettext('End Time (HH:MM)'))

    # Method
    trigger_actions_at_period = BooleanField(lazy_gettext('Trigger Every Period'))
    trigger_actions_at_start = BooleanField(lazy_gettext('Trigger when Activated'))

    # Output
    unique_id_1 = StringField(lazy_gettext('If ID 1'))
    unique_id_2 = StringField(lazy_gettext('If ID 2'))
    output_state = StringField(lazy_gettext('If State'))
    output_duration = DecimalField(
        "{} ({})".format(lazy_gettext('If Duration'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    output_duty_cycle = DecimalField(
        lazy_gettext('If Duty Cycle (%%)'), widget=NumberInput(step='any'))
