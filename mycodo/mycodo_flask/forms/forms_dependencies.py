# -*- coding: utf-8 -*-
#
# forms_dependencies.py - Dependencies Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets


class Dependencies(FlaskForm):
    device = StringField('Device', widget=widgets.HiddenInput())
    install = SubmitField(lazy_gettext('Install All Dependencies'))
