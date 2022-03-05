# -*- coding: utf-8 -*-
#
# forms_dashboard.py - Dashboard Flask Forms
#
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput

from mycodo.config_translations import TRANSLATIONS
from mycodo.mycodo_flask.utils.utils_general import generate_form_widget_list
from mycodo.utils.widgets import parse_widget_information


class DashboardBase(FlaskForm):
    choices_widgets = []
    dict_widgets = parse_widget_information()
    list_widgets_sorted = generate_form_widget_list(dict_widgets)
    choices_widgets.append(('', lazy_gettext('Add Dashboard Widget')))

    for each_widget in list_widgets_sorted:
        choices_widgets.append((each_widget, dict_widgets[each_widget]['widget_name']))

    widget_type = SelectField(
        'Dashboard Widget Type',
        choices=choices_widgets,
        validators=[DataRequired()]
    )

    dashboard_id = StringField('Dashboard ID', widget=widgets.HiddenInput())
    widget_id = StringField('Widget ID', widget=widgets.HiddenInput())

    name = StringField(
        TRANSLATIONS['name']['title'],
        validators=[DataRequired()]
    )
    font_em_name = DecimalField(TRANSLATIONS['font_em_name']['title'])
    refresh_duration = IntegerField(
        TRANSLATIONS['refresh_duration']['title'],
        validators=[validators.NumberRange(
            min=1,
            message=TRANSLATIONS['refresh_duration']['title']
        )],
        widget=NumberInput()
    )
    enable_drag_handle = BooleanField(lazy_gettext('Enable Drag Handle'))
    widget_add = SubmitField(TRANSLATIONS['create']['title'])
    widget_mod = SubmitField(TRANSLATIONS['save']['title'])
    widget_delete = SubmitField(TRANSLATIONS['delete']['title'])


class DashboardConfig(FlaskForm):
    dashboard_id = StringField('Dashboard ID', widget=widgets.HiddenInput())
    name = StringField(
        TRANSLATIONS['name']['title'],
        validators=[DataRequired()]
    )
    lock = SubmitField(TRANSLATIONS['lock']['title'])
    unlock = SubmitField(TRANSLATIONS['unlock']['title'])
    dash_modify = SubmitField(TRANSLATIONS['save']['title'])
    dash_delete = SubmitField(TRANSLATIONS['delete']['title'])
    dash_duplicate = SubmitField(TRANSLATIONS['duplicate']['title'])
