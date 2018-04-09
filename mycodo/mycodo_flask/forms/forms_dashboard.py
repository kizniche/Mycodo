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
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.validators import DataRequired


class DashboardBase(FlaskForm):
    dashboard_id = StringField('Dash Object ID', widget=widgets.HiddenInput())
    dashboard_type = SelectField('Dashboard Element Type',
        choices=[
            ('', lazy_gettext('Add Dashboard Element')),
            ('graph', lazy_gettext('Graph')),
            ('gauge', lazy_gettext('Gauge')),
            ('measurement', lazy_gettext('Measurement')),
            ('output', lazy_gettext('Output')),
            ('pid_control', lazy_gettext('PID Control')),
            ('camera', lazy_gettext('Camera')),
        ],
        validators=[DataRequired()]
    )
    name = StringField(
        lazy_gettext('Name'),
        validators=[DataRequired()]
    )
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
    refresh_duration = DecimalField(
        lazy_gettext('Refresh (seconds)'),
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext("Number of seconds to wait between acquiring"
                                 " any new measurements.")
        )]
    )
    list_visible_elements = SelectMultipleField(lazy_gettext('Visible Elements'))
    reorder = SubmitField(lazy_gettext('Save Order'))
    create = SubmitField(lazy_gettext('Create'))
    modify = SubmitField(lazy_gettext('Save'))
    delete = SubmitField(lazy_gettext('Delete'))
    order_up = SubmitField(lazy_gettext('Up'))
    order_down = SubmitField(lazy_gettext('Down'))


class DashboardGraph(FlaskForm):
    math_ids = SelectMultipleField(lazy_gettext('Maths'))
    pid_ids = SelectMultipleField(lazy_gettext('PIDs'))
    output_ids = SelectMultipleField(lazy_gettext('Outputs'))
    input_ids = SelectMultipleField(lazy_gettext('Inputs'))
    xaxis_duration = DecimalField(
        lazy_gettext('X-Axis (minutes)'),
        validators=[validators.NumberRange(
            min=0.1,
            message=lazy_gettext("Number of minutes to display of past "
                                 "measurements.")
        )]
    )
    enable_auto_refresh = BooleanField(lazy_gettext('Enable Auto Refresh'))
    enable_xaxis_reset = BooleanField(lazy_gettext('Enable X-Axis Reset'))
    enable_title = BooleanField(lazy_gettext('Enable Title'))
    enable_navbar = BooleanField(lazy_gettext('Enable Navbar'))
    enable_export = BooleanField(lazy_gettext('Enable Export'))
    enable_range = BooleanField(lazy_gettext('Enable Range Selector'))
    enable_graph_shift = BooleanField(lazy_gettext('Enable Graph Shift'))
    enable_manual_y_axis = BooleanField(lazy_gettext('Enable Manual Y-Axis Min/Max'))
    enable_align_ticks = BooleanField(lazy_gettext('Enable Y-Axis Align Ticks'))
    enable_start_on_tick = BooleanField(lazy_gettext('Enable Y-Axis Start On Tick'))
    enable_end_on_tick = BooleanField(lazy_gettext('Enable Y-Axis End On Tick'))
    use_custom_colors = BooleanField(lazy_gettext('Enable Custom Colors'))


class DashboardGauge(FlaskForm):
    gauge_type = SelectField(
        lazy_gettext('Gauge Type'),
        choices=[
            ('gauge_angular', lazy_gettext('Angular Gauge')),
            ('gauge_solid', lazy_gettext('Solid Gauge'))
        ],
        validators=[DataRequired()]
    )
    input_ids = StringField(lazy_gettext('Measurement'))
    y_axis_min = DecimalField(lazy_gettext('Gauge Min'))
    y_axis_max = DecimalField(lazy_gettext('Gauge Max'))
    max_measure_age = DecimalField(lazy_gettext('Max Age (seconds)'))
    enable_timestamp = BooleanField(lazy_gettext('Show Timestamp'))


class DashboardMeasurement(FlaskForm):
    measurement_id = StringField(lazy_gettext('Measurement'))
    max_measure_age = DecimalField(lazy_gettext('Max Age (seconds)'))
    font_em_value = DecimalField(lazy_gettext('Value Font (em)'))
    font_em_timestamp = DecimalField(lazy_gettext('Timestamp Font (em)'))
    decimal_places = IntegerField(lazy_gettext('Decimal Places'))


class DashboardOutput(FlaskForm):
    output_id = StringField(lazy_gettext('Output'))
    max_measure_age = DecimalField(lazy_gettext('Max Age (seconds)'))
    font_em_value = DecimalField(lazy_gettext('Value Font (em)'))
    font_em_timestamp = DecimalField(lazy_gettext('Timestamp Font (em)'))
    decimal_places = IntegerField(lazy_gettext('Decimal Places'))
    enable_output_controls = BooleanField(lazy_gettext('Feature Output Controls'))


class DashboardPIDControl(FlaskForm):
    pid_id = StringField(lazy_gettext('PID'))
    max_measure_age = DecimalField(lazy_gettext('Max Age (seconds)'))
    font_em_value = DecimalField(lazy_gettext('Value Font (em)'))
    font_em_timestamp = DecimalField(lazy_gettext('Timestamp Font (em)'))
    camera_max_age = IntegerField(lazy_gettext('Max Age (seconds)'))
    decimal_places = IntegerField(lazy_gettext('Decimal Places'))
    enable_pid_info = BooleanField(lazy_gettext('Show PID Information'))


class DashboardCamera(FlaskForm):
    camera_id = StringField(lazy_gettext('Camera'))
    camera_image_type = StringField(lazy_gettext('Image Display Type'))
    camera_max_age = IntegerField(lazy_gettext('Max Age (seconds)'))
