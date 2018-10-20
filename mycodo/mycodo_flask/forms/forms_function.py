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
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput

from mycodo.config import FUNCTION_TYPES


class DataBase(FlaskForm):
    reorder_type = StringField('Reorder Type', widget=widgets.HiddenInput())
    list_visible_elements = SelectMultipleField('New Order')
    reorder = SubmitField(lazy_gettext('Save Order'))


class FunctionAdd(FlaskForm):
    func_type = SelectField(
        choices=FUNCTION_TYPES,
        validators=[DataRequired()]
    )
    func_add = SubmitField(lazy_gettext('Add'))


class Actions(FlaskForm):
    function_type = StringField(
        'Function Type', widget=widgets.HiddenInput())
    function_id = StringField(
        'Function ID', widget=widgets.HiddenInput())
    function_action_id = StringField(
        'Function Action ID', widget=widgets.HiddenInput())
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

    save_action = SubmitField(lazy_gettext('Save'))
    delete_action = SubmitField(lazy_gettext('Delete'))
