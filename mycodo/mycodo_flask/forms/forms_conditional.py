# -*- coding: utf-8 -*-
#
# forms_misc.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets


#
# Conditionals
#

class Conditional(FlaskForm):
    conditional_id = StringField('Conditional ID', widget=widgets.HiddenInput())
    conditional_type = StringField('Conditional Type', widget=widgets.HiddenInput())
    input_id = StringField('Input ID', widget=widgets.HiddenInput())
    quantity = IntegerField(lazy_gettext('Quantity'))
    name = StringField(lazy_gettext('Name'))

    # Output conditional options
    unique_id_1 = StringField(lazy_gettext('If Output'))
    output_state = StringField(lazy_gettext('If State'))
    output_duration = DecimalField(lazy_gettext('If Duration (seconds)'))
    output_duty_cycle = DecimalField(lazy_gettext('If Duty Cycle (%)'))

    # Input conditional options
    measurement = StringField(lazy_gettext('If Measurement'))
    direction = StringField(lazy_gettext('If State'))
    setpoint = DecimalField(lazy_gettext('If Value'))
    period = DecimalField(lazy_gettext('Period (seconds)'))
    refractory_period = DecimalField(lazy_gettext('Refractory Period (seconds)'))
    max_age = IntegerField(lazy_gettext('Max Age (seconds)'))

    # Edge detection
    edge_detected = StringField(lazy_gettext('If Edge Detected'))

    # Sunrise/sunset
    rise_or_set = StringField(lazy_gettext('Rise or Set'))
    latitude = DecimalField(lazy_gettext('Latitude (decimal)'))
    longitude = DecimalField(lazy_gettext('Longitude (decimal)'))
    zenith = DecimalField(lazy_gettext('Zenith'))
    date_offset_days = IntegerField(lazy_gettext('Date Offset (days)'))
    time_offset_minutes = IntegerField(lazy_gettext('Time Offset (minutes)'))

    # Timer
    timer_duration = IntegerField(lazy_gettext('Duration (seconds)'))
    timer_start_offset = IntegerField(lazy_gettext('Start Offset (seconds)'))
    timer_start_time = StringField(lazy_gettext('Start Time (HH:MM)'))

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
    do_action = StringField(lazy_gettext('Action to Perform'))
    do_action_string = StringField(lazy_gettext('Action String'))
    do_unique_id = StringField(lazy_gettext('Controller ID'))
    do_output_state = StringField(lazy_gettext('Then State'))
    do_output_duration = DecimalField(lazy_gettext('Then Duration (seconds)'))
    do_output_pwm = DecimalField(lazy_gettext('Then Duty Cycle'))
    do_camera_duration = DecimalField(lazy_gettext('Then Duration'))
    add_action = SubmitField(lazy_gettext('Add Action'))
    save_action = SubmitField(lazy_gettext('Save'))
    delete_action = SubmitField(lazy_gettext('Delete'))
