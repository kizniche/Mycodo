# -*- coding: utf-8 -*-
#
# forms_function.py - Function Flask Forms
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
from wtforms.widgets.html5 import NumberInput

from mycodo.config import FUNCTION_ACTIONS
from mycodo.config_translations import TRANSLATIONS


class DataBase(FlaskForm):
    reorder_type = StringField('Reorder Type', widget=widgets.HiddenInput())
    list_visible_elements = SelectMultipleField('New Order')
    reorder = SubmitField(TRANSLATIONS['save_order']['title'])


class FunctionAdd(FlaskForm):
    function_type = SelectField()
    func_add = SubmitField(TRANSLATIONS['add']['title'])


class FunctionMod(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])
    action_type = SelectField(
        choices=[('', TRANSLATIONS['select_one']['title'])] + FUNCTION_ACTIONS)
    add_action = SubmitField(lazy_gettext('Add Action'))
    order_up = SubmitField(TRANSLATIONS['up']['title'])
    order_down = SubmitField(TRANSLATIONS['down']['title'])
    execute_all_actions = SubmitField(lazy_gettext('Execute All Actions'))
    save_function = SubmitField(TRANSLATIONS['save']['title'])
    delete_function = SubmitField(TRANSLATIONS['delete']['title'])


class Actions(FlaskForm):
    function_type = StringField(
        'Function Type', widget=widgets.HiddenInput())
    function_id = StringField(
        'Function ID', widget=widgets.HiddenInput())
    function_action_id = StringField(
        'Function Action ID', widget=widgets.HiddenInput())
    pause_duration = DecimalField(
        lazy_gettext('Duration (seconds)'),
        widget=NumberInput(step='any'))
    do_action_string = StringField(lazy_gettext('Action String'))
    do_unique_id = StringField(lazy_gettext('Controller ID'))
    do_output_state = StringField(lazy_gettext('Then State'))
    do_output_duration = DecimalField(
        lazy_gettext('Duration (seconds)'),
        widget=NumberInput(step='any'))
    do_output_pwm = DecimalField(
        lazy_gettext('Duty Cycle (%)'),
        widget=NumberInput(step='any'))
    do_output_pwm2 = DecimalField(
        lazy_gettext('Duty Cycle (%)'),
        widget=NumberInput(step='any'))
    do_camera_duration = DecimalField(
        lazy_gettext('Duration (seconds)'),
        widget=NumberInput(step='any'))

    # Infrared
    remote = StringField(lazy_gettext('Remote'))
    code = StringField(lazy_gettext('Code'))
    send_times = IntegerField(lazy_gettext('Times to Send'))

    save_action = SubmitField(TRANSLATIONS['save']['title'])
    delete_action = SubmitField(TRANSLATIONS['delete']['title'])
