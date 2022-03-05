# -*- coding: utf-8 -*-
#
# forms_function.py - Function Flask Forms
#
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.widgets import NumberInput

from mycodo.config_translations import TRANSLATIONS
from mycodo.mycodo_flask.utils.utils_general import generate_form_action_list
from mycodo.utils.function_actions import parse_function_action_information


class FunctionAdd(FlaskForm):
    function_type = SelectField()
    function_add = SubmitField(TRANSLATIONS['add']['title'])


class FunctionMod(FlaskForm):
    choices_actions = []
    dict_actions = parse_function_action_information()
    list_actions_sorted = generate_form_action_list(dict_actions)
    for each_action in list_actions_sorted:
        choices_actions.append((each_action, dict_actions[each_action]['name']))
    action_type = SelectField(
        choices=[('', TRANSLATIONS['select_one']['title'])] + choices_actions)

    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])

    add_action = SubmitField(lazy_gettext('Add Action'))
    execute_all_actions = SubmitField(lazy_gettext('Execute All Actions'))
    function_activate = SubmitField(TRANSLATIONS['activate']['title'])
    function_deactivate = SubmitField(TRANSLATIONS['deactivate']['title'])
    function_mod = SubmitField(TRANSLATIONS['save']['title'])
    function_delete = SubmitField(TRANSLATIONS['delete']['title'])


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
    do_output_state = StringField(lazy_gettext('State'))
    do_output_amount = DecimalField(
        lazy_gettext('Amount'),
        widget=NumberInput(step='any'))
    do_output_duration = DecimalField(
        lazy_gettext('Duration (seconds)'),
        widget=NumberInput(step='any'))
    do_output_pwm = DecimalField(
        lazy_gettext('Duty Cycle'),
        widget=NumberInput(step='any'))
    do_output_pwm2 = DecimalField(
        lazy_gettext('Duty Cycle'),
        widget=NumberInput(step='any'))
    do_camera_duration = DecimalField(
        lazy_gettext('Duration (seconds)'),
        widget=NumberInput(step='any'))

    save_action = SubmitField(TRANSLATIONS['save']['title'])
    delete_action = SubmitField(TRANSLATIONS['delete']['title'])
