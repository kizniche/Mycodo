# -*- coding: utf-8 -*-
#
# forms_function.py - Function Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.widgets.html5 import NumberInput

from mycodo.config import FUNCTION_ACTIONS
from mycodo.config_translations import TOOLTIPS_SETTINGS


class DataBase(FlaskForm):
    reorder_type = StringField('Reorder Type', widget=widgets.HiddenInput())
    list_visible_elements = SelectMultipleField('New Order')
    reorder = SubmitField(
        TOOLTIPS_SETTINGS['save_order']['title'])


class FunctionAdd(FlaskForm):
    func_type = SelectField('Function Type')
    func_add = SubmitField(
        TOOLTIPS_SETTINGS['add']['title'])


class FunctionMod(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(
        TOOLTIPS_SETTINGS['name']['title'])
    action_type = SelectField(
        choices=[('', TOOLTIPS_SETTINGS['select_one']['title'])] + FUNCTION_ACTIONS)
    add_action = SubmitField(lazy_gettext('Add Action'))
    order_up = SubmitField(
        TOOLTIPS_SETTINGS['up']['title'])
    order_down = SubmitField(
        TOOLTIPS_SETTINGS['down']['title'])
    execute_all_actions = SubmitField(lazy_gettext('Execute All Actions'))
    save_function = SubmitField(
        TOOLTIPS_SETTINGS['save']['title'])
    delete_function = SubmitField(
        TOOLTIPS_SETTINGS['delete']['title'])


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
        lazy_gettext('Then Duration (seconds)'),
        widget=NumberInput(step='any'))
    do_output_pwm = DecimalField(
        lazy_gettext('Then Duty Cycle'),
        widget=NumberInput(step='any'))
    do_camera_duration = DecimalField(
        lazy_gettext('Then Duration'),
        widget=NumberInput(step='any'))

    save_action = SubmitField(
        TOOLTIPS_SETTINGS['save']['title'])
    delete_action = SubmitField(
        TOOLTIPS_SETTINGS['delete']['title'])
