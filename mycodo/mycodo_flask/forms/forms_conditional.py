# -*- coding: utf-8 -*-
#
# forms_misc.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets


#
# Conditionals
#

class Conditional(FlaskForm):
    conditional_id = IntegerField('Conditional ID', widget=widgets.HiddenInput())
    conditional_type = StringField('Conditional Type', widget=widgets.HiddenInput())
    sensor_id = IntegerField('Output ID', widget=widgets.HiddenInput())
    quantity = IntegerField(lazy_gettext(u'Quantity'))
    name = StringField(lazy_gettext(u'Name'))

    # Output conditional options
    if_relay_id = StringField(lazy_gettext(u'If Output'))
    if_relay_state = StringField(lazy_gettext(u'If Output State'))
    if_relay_duration = DecimalField(lazy_gettext(u'If Output Duration'))

    # Input conditional options
    if_sensor_period = DecimalField(lazy_gettext(u'Period'))
    if_sensor_measurement = StringField(lazy_gettext(u'Measurement'))
    if_sensor_edge_select = StringField(lazy_gettext(u'Edge or State'))
    if_sensor_edge_detected = StringField(lazy_gettext(u'Edge Detected'))
    if_sensor_gpio_state = IntegerField(lazy_gettext(u'GPIO State'))
    if_sensor_direction = StringField(lazy_gettext(u'Direction'))
    if_sensor_setpoint = DecimalField(lazy_gettext(u'Setpoint'))

    add_cond = SubmitField(lazy_gettext(u'Add Conditional'))
    save_cond = SubmitField(lazy_gettext(u'Save'))
    delete_cond = SubmitField(lazy_gettext(u'Delete'))
    activate_cond = SubmitField(lazy_gettext(u'Activate'))
    deactivate_cond = SubmitField(lazy_gettext(u'Deactivate'))


class ConditionalActions(FlaskForm):
    conditional_id = IntegerField(
        'Conditional ID', widget=widgets.HiddenInput())
    conditional_action_id = IntegerField(
        'Conditional Action ID', widget=widgets.HiddenInput())
    do_action = StringField(lazy_gettext(u'Action to Perform'))
    do_action_string = StringField(lazy_gettext(u'Action String'))
    do_relay_id = IntegerField(lazy_gettext(u'Output'))
    do_relay_state = StringField(lazy_gettext(u'Output State'))
    do_relay_duration = DecimalField(lazy_gettext(u'Duration'))
    do_camera_id = IntegerField(lazy_gettext(u'Camera'))
    do_camera_duration = DecimalField(lazy_gettext(u'Duration'))
    do_lcd_id = IntegerField(lazy_gettext(u'LCD'))
    do_pid_id = IntegerField(lazy_gettext(u'PID'))
    add_action = SubmitField(lazy_gettext(u'Add Action'))
    save_action = SubmitField(lazy_gettext(u'Save'))
    delete_action = SubmitField(lazy_gettext(u'Delete'))
