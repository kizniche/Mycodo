# -*- coding: utf-8 -*-
#
# forms_function.py - Function Flask Forms
#
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets

from mycodo.config_translations import TRANSLATIONS


class FunctionAdd(FlaskForm):
    function_type = SelectField()
    function_add = SubmitField(TRANSLATIONS['add']['title'])


class FunctionMod(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])

    execute_all_actions = SubmitField(lazy_gettext('Execute All Actions'))
    function_activate = SubmitField(TRANSLATIONS['activate']['title'])
    function_deactivate = SubmitField(TRANSLATIONS['deactivate']['title'])
    function_mod = SubmitField(TRANSLATIONS['save']['title'])
    function_delete = SubmitField(TRANSLATIONS['delete']['title'])
