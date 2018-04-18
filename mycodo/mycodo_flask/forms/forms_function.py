# -*- coding: utf-8 -*-
#
# forms_func.py - Function Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms import SubmitField
from wtforms.validators import DataRequired

from mycodo.config import CONDITIONALS
from mycodo.config import PIDS


class FunctionAdd(FlaskForm):
    func_type = SelectField(
        choices=PIDS + CONDITIONALS,
        validators=[DataRequired()]
    )
    func_add = SubmitField(lazy_gettext('Add'))
