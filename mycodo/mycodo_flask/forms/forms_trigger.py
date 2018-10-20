# -*- coding: utf-8 -*-
#
# forms_trigger.py - Function Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput

from mycodo.config import FUNCTION_ACTIONS


class DataBase(FlaskForm):
    reorder_type = StringField('Reorder Type', widget=widgets.HiddenInput())
    list_visible_elements = SelectMultipleField('New Order')
    reorder = SubmitField(lazy_gettext('Save Order'))


class Trigger(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext('Name'))

    # Edge detection
    measurement = StringField(lazy_gettext('Measurement'))
    edge_detected = StringField(lazy_gettext('If Edge Detected'))

    # Sunrise/sunset
    rise_or_set = StringField(
        lazy_gettext('Rise or Set'))
    latitude = DecimalField(
        lazy_gettext('Latitude (decimal)'),
        widget=NumberInput(step='any'))
    longitude = DecimalField(
        lazy_gettext('Longitude (decimal)'),
        widget=NumberInput(step='any'))
    zenith = DecimalField(
        lazy_gettext('Zenith'),
        widget=NumberInput(step='any'))
    date_offset_days = IntegerField(
        lazy_gettext('Date Offset (days)'),
        widget=NumberInput())
    time_offset_minutes = IntegerField(
        lazy_gettext('Time Offset (minutes)'),
        widget=NumberInput())

    # Timer
    period = StringField(lazy_gettext('Period (seconds)'))
    timer_start_offset = IntegerField(
        lazy_gettext('Start Offset (seconds)'), widget=NumberInput())
    timer_start_time = StringField(lazy_gettext('Start Time (HH:MM)'))
    timer_end_time = StringField(lazy_gettext('End Time (HH:MM)'))

    # Method
    trigger_actions_at_period = BooleanField(lazy_gettext('Trigger Every Period'))
    trigger_actions_at_start = BooleanField(lazy_gettext('Trigger when Activated'))

    # Output conditional options
    unique_id_1 = StringField(lazy_gettext('If ID 1'))
    unique_id_2 = StringField(lazy_gettext('If ID 2'))
    output_state = StringField(lazy_gettext('If State'))
    output_duration = DecimalField(
        lazy_gettext('If Duration (seconds)'),
        widget=NumberInput(step='any'))
    output_duty_cycle = DecimalField(
        lazy_gettext('If Duty Cycle (%)'),
        widget=NumberInput(step='any'))

    action_type = SelectField(
        choices=FUNCTION_ACTIONS,
        validators=[DataRequired()]
    )
    add_action = SubmitField(lazy_gettext('Add Action'))

    activate_trigger = SubmitField(lazy_gettext('Activate'))
    deactivate_trigger = SubmitField(lazy_gettext('Deactivate'))
    test_all_actions = SubmitField(lazy_gettext('Test All Actions'))
    delete_trigger = SubmitField(lazy_gettext('Delete'))
    save_trigger = SubmitField(lazy_gettext('Save'))
    order_up_trigger = SubmitField(lazy_gettext('Up'))
    order_down_trigger = SubmitField(lazy_gettext('Down'))

class Actions(FlaskForm):
    function_id = StringField(
        'Conditional ID', widget=widgets.HiddenInput())
    function_action_id = StringField(
        'Conditional Action ID', widget=widgets.HiddenInput())
    do_action_string = StringField(lazy_gettext('Action String'))
    do_unique_id = StringField(lazy_gettext('Controller ID'))
    do_output_state = StringField(lazy_gettext('Then State'))
    do_output_duration = DecimalField(
        lazy_gettext('Then Duration (seconds)'),
        widget=NumberInput(step='any'))
    do_output_pwm = DecimalField(
        lazy_gettext('Then Duty Cycle'),
        widget=NumberInput(step='any'))
    do_camera_duration = DecimalField(
        lazy_gettext('Then Duration'),
        widget=NumberInput(step='any'))

    save_action = SubmitField(lazy_gettext('Save'))
    delete_action = SubmitField(lazy_gettext('Delete'))
