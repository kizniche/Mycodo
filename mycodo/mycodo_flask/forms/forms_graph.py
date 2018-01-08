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
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired


class GraphAdd(FlaskForm):
    graph_type = StringField('Graph Type', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    math_ids = SelectMultipleField(lazy_gettext('Maths'))
    pid_ids = SelectMultipleField(lazy_gettext('PIDs'))
    relay_ids = SelectMultipleField(lazy_gettext('Outputs'))
    sensor_ids = SelectMultipleField(lazy_gettext('Inputs'))
    width = IntegerField(
        lazy_gettext('Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext('Height (pixels)'),
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xaxis_duration = DecimalField(
        lazy_gettext('X-Axis (minutes)'),
        validators=[validators.NumberRange(
            min=0.1,
            message=lazy_gettext("Number of minutes to display of past "
                                 "measurements.")
        )]
    )
    refresh_duration = DecimalField(
        lazy_gettext('Period (seconds)'),
        validators=[validators.NumberRange(
            min=0.2,
            message=lazy_gettext("Number of seconds to wait between acquiring"
                                 " any new measurements.")
        )]
    )
    enable_auto_refresh = BooleanField(lazy_gettext('Enable Auto Refresh'))
    enable_xaxis_reset = BooleanField(lazy_gettext('Enable X-Axis Reset'))
    enable_title = BooleanField(lazy_gettext('Enable Title'))
    enable_navbar = BooleanField(lazy_gettext('Enable Navbar'))
    enable_export = BooleanField(lazy_gettext('Enable Export'))
    enable_range = BooleanField(lazy_gettext('Enable Range Selector'))
    graph_add = SubmitField(lazy_gettext('Create'))


class GraphMod(FlaskForm):
    graph_id = IntegerField('Graph ID', widget=widgets.HiddenInput())
    graph_type = StringField('Type', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    math_ids = SelectMultipleField(lazy_gettext('Maths'))
    pid_ids = SelectMultipleField(lazy_gettext('PIDs'))
    relay_ids = SelectMultipleField(lazy_gettext('Outputs'))
    sensor_ids = SelectMultipleField(lazy_gettext('Inputs'))
    width = IntegerField(
        lazy_gettext('Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext('Height (pixels)'),
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    xaxis_duration = DecimalField(
        lazy_gettext('X-Axis (minutes)'),
        validators=[validators.NumberRange(
            min=0.1,
            message=lazy_gettext("Number of minutes to display of past "
                                 "measurements.")
        )]
    )
    refresh_duration = DecimalField(
        lazy_gettext('Period (seconds)'),
        validators=[validators.NumberRange(
            min=0.2,
            message=lazy_gettext("Number of seconds to wait between acquiring"
                                 " any new measurements.")
        )]
    )
    enable_auto_refresh = BooleanField(lazy_gettext('Enable Auto Refresh'))
    enable_xaxis_reset = BooleanField(lazy_gettext('Enable X-Axis Reset'))
    enable_title = BooleanField(lazy_gettext('Enable Title'))
    enable_navbar = BooleanField(lazy_gettext('Enable Navbar'))
    enable_export = BooleanField(lazy_gettext('Enable Export'))
    enable_range = BooleanField(lazy_gettext('Enable Range Selector'))
    use_custom_colors = BooleanField(lazy_gettext('Enable Custom Colors'))
    graph_mod = SubmitField(lazy_gettext('Save'))
    graph_del = SubmitField(lazy_gettext('Delete'))
    graph_order_up = SubmitField(lazy_gettext('Up'))
    graph_order_down = SubmitField(lazy_gettext('Down'))


class GaugeAdd(FlaskForm):
    graph_type = StringField('Type', widget=widgets.HiddenInput())
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
    sensor_ids = SelectMultipleField(lazy_gettext('Measurement'))
    width = IntegerField(
        lazy_gettext('Width'),
        validators=[validators.NumberRange(
            min=1,
            max=12
        )]
    )
    height = IntegerField(
        lazy_gettext('Height (pixels)'),
        validators=[validators.NumberRange(
            min=100,
            max=10000
        )]
    )
    y_axis_min = DecimalField(lazy_gettext('Gauge Min'))
    y_axis_max = DecimalField(lazy_gettext('Gauge Max'))
    max_measure_age = DecimalField(lazy_gettext('Max Age (seconds)'))
    refresh_duration = DecimalField(
        lazy_gettext('Refresh (seconds)'),
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext("Number of seconds to wait between acquiring"
                                 " any new measurements.")
        )]
    )
    gauge_add = SubmitField(lazy_gettext('Create'))


class GaugeMod(FlaskForm):
    graph_id = IntegerField('Graph ID', widget=widgets.HiddenInput())
    graph_type = StringField('Type', widget=widgets.HiddenInput())
    name = StringField(lazy_gettext('Name'))
    sensor_ids = SelectMultipleField(lazy_gettext('Measurement'))
    width = IntegerField(lazy_gettext('Width'))
    height = IntegerField(lazy_gettext('Height (pixels)'))
    y_axis_min = DecimalField(lazy_gettext('Gauge Min'))
    y_axis_max = DecimalField(lazy_gettext('Gauge Max'))
    max_measure_age = DecimalField(lazy_gettext('Max Age (seconds)'))
    refresh_duration = DecimalField(lazy_gettext('Refresh (seconds)'))
    gauge_mod = SubmitField(lazy_gettext('Save'))
    gauge_del = SubmitField(lazy_gettext('Delete'))
    gauge_order_up = SubmitField(lazy_gettext('Up'))
    gauge_order_down = SubmitField(lazy_gettext('Down'))
