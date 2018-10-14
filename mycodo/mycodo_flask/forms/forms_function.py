# -*- coding: utf-8 -*-
#
# forms_func.py - Function Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired

from mycodo.config import CONDITIONALS
from mycodo.config import PIDS


class DataBase(FlaskForm):
    reorder_type = StringField('Reorder Type', widget=widgets.HiddenInput())
    list_visible_elements = SelectMultipleField('New Order')
    reorder = SubmitField(lazy_gettext('Save Order'))


class FunctionAdd(FlaskForm):
    func_type = SelectField(
        choices=PIDS + CONDITIONALS,
        validators=[DataRequired()]
    )
    func_add = SubmitField(lazy_gettext('Add'))
