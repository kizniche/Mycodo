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
from wtforms.widgets.html5 import NumberInput

from mycodo.config import CONDITIONAL_CONDITIONS
from mycodo.config import FUNCTION_ACTIONS
from mycodo.config_translations import TRANSLATIONS


#
# Conditionals
#

class Conditional(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    conditional_statement = StringField(lazy_gettext('Conditional Statement'))
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        widget=NumberInput(step='any'))
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])
    refractory_period = DecimalField(
        lazy_gettext('Refractory Period (seconds)'),
        widget=NumberInput(step='any'))
    start_offset = DecimalField(
        lazy_gettext('Start Offset (seconds)'),
        widget=NumberInput(step='any'))
    condition_type = SelectField(
        choices=[('', TRANSLATIONS['select_one']['title'])] + CONDITIONAL_CONDITIONS)
    add_condition = SubmitField(lazy_gettext('Add Condition'))
    action_type = SelectField(
        choices=[('', TRANSLATIONS['select_one']['title'])] + FUNCTION_ACTIONS)
    add_action = SubmitField(lazy_gettext('Add Action'))
    activate_cond = SubmitField(TRANSLATIONS['activate']['title'])
    deactivate_cond = SubmitField(TRANSLATIONS['deactivate']['title'])
    test_all_actions = SubmitField(lazy_gettext('Test All Actions'))
    delete_conditional = SubmitField(TRANSLATIONS['delete']['title'])
    save_conditional = SubmitField(TRANSLATIONS['save']['title'])
    order_up = SubmitField(TRANSLATIONS['up']['title'])
    order_down = SubmitField(TRANSLATIONS['down']['title'])


class ConditionalConditions(FlaskForm):
    conditional_id = StringField(
        'Conditional ID',widget=widgets.HiddenInput())
    conditional_condition_id = StringField(
        'Conditional Condition ID', widget=widgets.HiddenInput())

    # Measurement
    input_id = StringField('Input ID', widget=widgets.HiddenInput())
    measurement = StringField(TRANSLATIONS['measurement']['title'])
    max_age = IntegerField(
        TRANSLATIONS['max_age']['title'],
        widget=NumberInput())

    # GPIO State
    gpio_pin = IntegerField(
        lazy_gettext('GPIO Pin (BCM)'),
        widget=NumberInput())

    output_id = StringField(TRANSLATIONS['output']['title'])

    save_condition = SubmitField(TRANSLATIONS['save']['title'])
    delete_condition = SubmitField(TRANSLATIONS['delete']['title'])
