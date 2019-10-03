# -*- coding: utf-8 -*-
#
# forms_custom_controller.py - Miscellaneous Flask Forms
#

from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets

from mycodo.config_translations import TRANSLATIONS


#
# Conditionals
#

class CustomController(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])
    activate_controller = SubmitField(TRANSLATIONS['activate']['title'])
    deactivate_controller = SubmitField(TRANSLATIONS['deactivate']['title'])
    delete_controller = SubmitField(TRANSLATIONS['delete']['title'])
    save_controller = SubmitField(TRANSLATIONS['save']['title'])
    order_up = SubmitField(TRANSLATIONS['up']['title'])
    order_down = SubmitField(TRANSLATIONS['down']['title'])
