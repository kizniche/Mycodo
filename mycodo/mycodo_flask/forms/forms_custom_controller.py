# -*- coding: utf-8 -*-
#
# forms_custom_controller.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import widgets
from wtforms.widgets import NumberInput

from mycodo.config_translations import TRANSLATIONS


#
# Custom Controllers
#

class CustomController(FlaskForm):
    function_id = StringField('Function ID', widget=widgets.HiddenInput())
    function_type = StringField('Function Type', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    num_channels = IntegerField(lazy_gettext('Number of Measurements'), widget=NumberInput())
    measurements_enabled = SelectMultipleField(TRANSLATIONS['measurements_enabled']['title'])
    log_level_debug = BooleanField(
        TRANSLATIONS['log_level_debug']['title'])
