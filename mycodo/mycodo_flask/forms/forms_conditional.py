# -*- coding: utf-8 -*-
#
# forms_conditional.py - Miscellaneous Flask Forms
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
from wtforms.widgets import NumberInput

from mycodo.config import CONDITIONAL_CONDITIONS
from mycodo.config_translations import TRANSLATIONS


#
# Conditionals
#

class Conditional(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    conditional_import = StringField(lazy_gettext('Import Python Code'))
    conditional_initialize = StringField(lazy_gettext('Initialize Python Code'))
    conditional_statement = StringField(lazy_gettext('Run Python Code'))
    conditional_status = StringField(lazy_gettext('Status Python Code'))
    period = DecimalField(
        "{} ({})".format(lazy_gettext('Period'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])
    message_include_code = BooleanField(
        TRANSLATIONS['message_include_code']['title'])
    refractory_period = DecimalField(
        "{} ({})".format(lazy_gettext('Refractory Period'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    start_offset = DecimalField(
        "{} ({})".format(lazy_gettext('Start Offset'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    pyro_timeout = DecimalField(
        "{} ({})".format(lazy_gettext('Timeout'), lazy_gettext('Seconds')),
        widget=NumberInput(step='any'))
    condition_type = SelectField(
        choices=[('', TRANSLATIONS['select_one']['title'])] + CONDITIONAL_CONDITIONS)
    add_condition = SubmitField(lazy_gettext('Add'))


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
        "{}: {} ({})".format(lazy_gettext('Pin'), lazy_gettext('GPIO'), lazy_gettext('BCM')),
        widget=NumberInput())

    output_id = StringField(TRANSLATIONS['output']['title'])
    controller_id = StringField(TRANSLATIONS['controller']['title'])

    save_condition = SubmitField(TRANSLATIONS['save']['title'])
    delete_condition = SubmitField(TRANSLATIONS['delete']['title'])
