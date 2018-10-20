# -*- coding: utf-8 -*-
#
# forms_misc.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput

from mycodo.config import FUNCTION_ACTIONS
from mycodo.config import CONDITIONAL_CONDITIONS


#
# Conditionals
#

class Conditional(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext('Name'))
    conditional_statement = StringField(lazy_gettext('Conditional Statement'))
    period = DecimalField(
        lazy_gettext('Period (seconds)'),
        widget=NumberInput(step='any'))
    refractory_period = DecimalField(
        lazy_gettext('Refractory Period (seconds)'),
        widget=NumberInput(step='any'))
    condition_type = SelectField(
        choices=CONDITIONAL_CONDITIONS,
        validators=[DataRequired()]
    )
    add_condition = SubmitField(lazy_gettext('Add Condition'))
    action_type = SelectField(
        choices=FUNCTION_ACTIONS,
        validators=[DataRequired()]
    )
    add_action = SubmitField(lazy_gettext('Add Action'))
    activate_cond = SubmitField(lazy_gettext('Activate'))
    deactivate_cond = SubmitField(lazy_gettext('Deactivate'))
    test_all_actions = SubmitField(lazy_gettext('Test All Actions'))
    delete_conditional = SubmitField(lazy_gettext('Delete'))
    save_conditional = SubmitField(lazy_gettext('Save'))
    order_up = SubmitField(lazy_gettext('Up'))
    order_down = SubmitField(lazy_gettext('Down'))


class ConditionalConditions(FlaskForm):
    conditional_id = StringField(
        'Conditional ID',widget=widgets.HiddenInput())
    conditional_condition_id = StringField(
        'Conditional Condition ID', widget=widgets.HiddenInput())

    # Measurement
    input_id = StringField('Input ID', widget=widgets.HiddenInput())
    measurement = StringField(lazy_gettext('If Measurement'))
    max_age = IntegerField(
        lazy_gettext('Max Age (seconds)'),
        widget=NumberInput())

    # GPIO State
    gpio_pin = IntegerField(
        lazy_gettext('GPIO Pin (BCM)'),
        widget=NumberInput())

    save_condition = SubmitField(lazy_gettext('Save'))
    delete_condition = SubmitField(lazy_gettext('Delete'))
