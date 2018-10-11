# -*- coding: utf-8 -*-
#
# forms_misc.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput

from mycodo.config import CONDITIONAL_ACTIONS


#
# Conditionals
#

class Conditional(FlaskForm):
    conditional_id = StringField('Conditional ID', widget=widgets.HiddenInput())
    conditional_type = StringField('Conditional Type', widget=widgets.HiddenInput())
    input_id = StringField('Input ID', widget=widgets.HiddenInput())
    quantity = IntegerField(
        lazy_gettext('Quantity'), widget = NumberInput())
    name = StringField(lazy_gettext('Name'))

    # Output conditional options
    unique_id_1 = StringField(lazy_gettext('If ID 1'))
    unique_id_2 = StringField(lazy_gettext('If ID 2'))
    output_state = StringField(lazy_gettext('If State'))
    output_duration = DecimalField(
        lazy_gettext('If Duration (seconds)'), widget = NumberInput())
    output_duty_cycle = DecimalField(
        lazy_gettext('If Duty Cycle (%)'), widget = NumberInput())

    # Input conditional options
    measurement = StringField(lazy_gettext('If Measurement'))
    direction = StringField(lazy_gettext('If State'))
    setpoint = DecimalField(
        lazy_gettext('If Value'), widget = NumberInput())
    period = DecimalField(
        lazy_gettext('Period (seconds)'), widget = NumberInput())
    refractory_period = DecimalField(
        lazy_gettext('Refractory Period (seconds)'), widget = NumberInput())
    max_age = IntegerField(
        lazy_gettext('Max Age (seconds)'), widget = NumberInput())

    # Edge detection
    edge_detected = StringField(lazy_gettext('If Edge Detected'))

    # Sunrise/sunset
    rise_or_set = StringField(
        lazy_gettext('Rise or Set'))
    latitude = DecimalField(
        lazy_gettext('Latitude (decimal)'), widget = NumberInput())
    longitude = DecimalField(
        lazy_gettext('Longitude (decimal)'), widget = NumberInput())
    zenith = DecimalField(
        lazy_gettext('Zenith'), widget = NumberInput())
    date_offset_days = IntegerField(
        lazy_gettext('Date Offset (days)'), widget = NumberInput())
    time_offset_minutes = IntegerField(
        lazy_gettext('Time Offset (minutes)'), widget = NumberInput())

    # Timer
    timer_start_offset = IntegerField(
        lazy_gettext('Start Offset (seconds)'), widget = NumberInput())
    timer_start_time = StringField(lazy_gettext('Start Time (HH:MM)'))
    timer_end_time = StringField(lazy_gettext('End Time (HH:MM)'))

    # Method
    trigger_actions_at_period = BooleanField(lazy_gettext('Trigger Every Period'))
    trigger_actions_at_start = BooleanField(lazy_gettext('Trigger when Activated'))

    add_cond = SubmitField(lazy_gettext('Add Conditional'))
    save_cond = SubmitField(lazy_gettext('Save'))
    delete_cond = SubmitField(lazy_gettext('Delete'))
    activate_cond = SubmitField(lazy_gettext('Activate'))
    deactivate_cond = SubmitField(lazy_gettext('Deactivate'))
    order_up_cond = SubmitField(lazy_gettext('Up'))
    order_down_cond = SubmitField(lazy_gettext('Down'))


class ConditionalActions(FlaskForm):
    conditional_id = StringField(
        'Conditional ID', widget=widgets.HiddenInput())
    conditional_action_id = StringField(
        'Conditional Action ID', widget=widgets.HiddenInput())
    do_action = SelectField(
        choices=CONDITIONAL_ACTIONS,
        validators=[DataRequired()]
    )
    do_action_string = StringField(lazy_gettext('Action String'))
    do_unique_id = StringField(lazy_gettext('Controller ID'))
    do_output_state = StringField(lazy_gettext('Then State'))
    do_output_duration = DecimalField(
        lazy_gettext('Then Duration (seconds)'), widget = NumberInput())
    do_output_pwm = DecimalField(
        lazy_gettext('Then Duty Cycle'), widget = NumberInput())
    do_camera_duration = DecimalField(
        lazy_gettext('Then Duration'), widget = NumberInput())
    add_action = SubmitField(lazy_gettext('Add Action'))
    save_action = SubmitField(lazy_gettext('Save'))
    delete_action = SubmitField(lazy_gettext('Delete'))
