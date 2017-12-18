# -*- coding: utf-8 -*-
#
# forms_func.py - Function Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class FunctionAdd(FlaskForm):
    func_type = StringField(
        'Func Type',
        validators=[DataRequired()])
    func_add = SubmitField(lazy_gettext(u'Add Function'))
