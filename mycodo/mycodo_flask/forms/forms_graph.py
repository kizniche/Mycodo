# -*- coding: utf-8 -*-
#
# forms_graph.py - Graph Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import IntegerField
from wtforms import SelectMultipleField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets

from wtforms.validators import DataRequired


class GraphAdd(FlaskForm):
    graph_type = StringField('Type', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    math_ids = SelectMultipleField(lazy_gettext(u'Maths'))
    pid_ids = SelectMultipleField(lazy_gettext(u'PIDs'))
    relay_ids = SelectMultipleField(lazy_gettext(u'Outputs'))
    sensor_ids = SelectMultipleField(lazy_gettext(u'Inputs'))
    width = IntegerField(
        lazy_gettext(u'Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext(u'Height (pixels)'),
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xaxis_duration = DecimalField(
        lazy_gettext(u'X-Axis (minutes)'),
        validators=[validators.NumberRange(
            min=0.1,
            message=lazy_gettext(u"Number of minutes to display of past "
                                 u"measurements.")
        )]
    )
    refresh_duration = DecimalField(
        lazy_gettext(u'Period (seconds)'),
        validators=[validators.NumberRange(
            min=0.2,
            message=lazy_gettext(u"Number of seconds to wait between acquiring"
                                 u" any new measurements.")
        )]
    )
    enable_auto_refresh = BooleanField(lazy_gettext(u'Enable Auto Refresh'))
    enable_xaxis_reset = BooleanField(lazy_gettext(u'Enable X-Axis Reset'))
    enable_title = BooleanField(lazy_gettext(u'Enable Title'))
    enable_navbar = BooleanField(lazy_gettext(u'Enable Navbar'))
    enable_export = BooleanField(lazy_gettext(u'Enable Export'))
    enable_range = BooleanField(lazy_gettext(u'Enable Range Selector'))
    graph_add = SubmitField(lazy_gettext(u'Create'))


class GraphMod(FlaskForm):
    graph_id = IntegerField('Graph ID', widget=widgets.HiddenInput())
    graph_type = StringField('Type', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    math_ids = SelectMultipleField(lazy_gettext(u'Maths'))
    pid_ids = SelectMultipleField(lazy_gettext(u'PIDs'))
    relay_ids = SelectMultipleField(lazy_gettext(u'Outputs'))
    sensor_ids = SelectMultipleField(lazy_gettext(u'Inputs'))
    width = IntegerField(
        lazy_gettext(u'Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext(u'Height (pixels)'),
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xaxis_duration = DecimalField(
        lazy_gettext(u'X-Axis (minutes)'),
        validators=[validators.NumberRange(
            min=0.1,
            message=lazy_gettext(u"Number of minutes to display of past "
                                 u"measurements.")
        )]
    )
    refresh_duration = DecimalField(
        lazy_gettext(u'Period (seconds)'),
        validators=[validators.NumberRange(
            min=0.2,
            message=lazy_gettext(u"Number of seconds to wait between acquiring"
                                 u" any new measurements.")
        )]
    )
    enable_auto_refresh = BooleanField(lazy_gettext(u'Enable Auto Refresh'))
    enable_xaxis_reset = BooleanField(lazy_gettext(u'Enable X-Axis Reset'))
    enable_title = BooleanField(lazy_gettext(u'Enable Title'))
    enable_navbar = BooleanField(lazy_gettext(u'Enable Navbar'))
    enable_export = BooleanField(lazy_gettext(u'Enable Export'))
    enable_range = BooleanField(lazy_gettext(u'Enable Range Selector'))
    use_custom_colors = BooleanField(lazy_gettext(u'Enable Custom Colors'))
    graph_mod = SubmitField(lazy_gettext(u'Save'))
    graph_del = SubmitField(lazy_gettext(u'Delete'))
    graph_order_up = SubmitField(lazy_gettext(u'Up'))
    graph_order_down = SubmitField(lazy_gettext(u'Down'))


class GaugeAdd(FlaskForm):
    graph_type = StringField('Type', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext(u'Name'),
        validators=[DataRequired()]
    )
    sensor_ids = SelectMultipleField(lazy_gettext(u'Measurement'))
    width = IntegerField(
        lazy_gettext(u'Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext(u'Height (pixels)'),
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    y_axis_min = DecimalField(lazy_gettext(u'Gauge Min'))
    y_axis_max = DecimalField(lazy_gettext(u'Gauge Max'))
    max_measure_age = DecimalField(lazy_gettext(u'Max Age (seconds)'))
    refresh_duration = IntegerField(
        lazy_gettext(u'Refresh (seconds)'),
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u"Number of seconds to wait between acquiring"
                                 u" any new measurements.")
        )]
    )
    gauge_add = SubmitField(lazy_gettext(u'Create'))


class GaugeMod(FlaskForm):
    graph_id = IntegerField('Graph ID', widget=widgets.HiddenInput())
    graph_type = StringField('Type', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext(u'Name'))
    sensor_ids = SelectMultipleField(lazy_gettext(u'Measurement'))
    width = IntegerField(lazy_gettext(u'Width'))
    height = IntegerField(lazy_gettext(u'Height (pixels)'))
    y_axis_min = DecimalField(lazy_gettext(u'Gauge Min'))
    y_axis_max = DecimalField(lazy_gettext(u'Gauge Max'))
    max_measure_age = DecimalField(lazy_gettext(u'Max Age (seconds)'))
    refresh_duration = IntegerField(lazy_gettext(u'Refresh (seconds)'))
    gauge_mod = SubmitField(lazy_gettext(u'Save'))
    gauge_del = SubmitField(lazy_gettext(u'Delete'))
    gauge_order_up = SubmitField(lazy_gettext(u'Up'))
    gauge_order_down = SubmitField(lazy_gettext(u'Down'))
