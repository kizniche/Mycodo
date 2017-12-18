# -*- coding: utf-8 -*-
#
# forms_method.py - Method Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets


class MethodCreate(FlaskForm):
    name = StringField(lazy_gettext(u'Name'))
    method_type = StringField(lazy_gettext(u'Method Type'))
    controller_type = HiddenField('Controller Type')
    Submit = SubmitField(lazy_gettext(u'Create New Method'))


class MethodAdd(FlaskForm):
    method_id = IntegerField('Method ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
    daily_time_start = StringField(
        lazy_gettext(u'Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    daily_time_end = StringField(
        lazy_gettext(u'End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    time_start = StringField(
        lazy_gettext(u'Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    time_end = StringField(
        lazy_gettext(u'End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    setpoint_start = DecimalField(lazy_gettext(u'Start Setpoint'))
    setpoint_end = DecimalField(lazy_gettext(u'End Setpoint (optional)'))
    duration = DecimalField(lazy_gettext(u'Duration (seconds)'))
    duration_end = DecimalField(lazy_gettext(u'End After (seconds)'))
    amplitude = DecimalField(lazy_gettext(u'Amplitude'))
    frequency = DecimalField(lazy_gettext(u'Frequency'))
    shift_angle = DecimalField(lazy_gettext(u'Angle Shift (0 to 360)'))
    shiftY = DecimalField(lazy_gettext(u'Y-Axis Shift'))
    x0 = DecimalField('X0')
    y0 = DecimalField('Y0')
    x1 = DecimalField('X1')
    y1 = DecimalField('Y1')
    x2 = DecimalField('X2')
    y2 = DecimalField('Y2')
    x3 = DecimalField('X3')
    y3 = DecimalField('Y3')
    relay_daily_time = StringField(
        lazy_gettext(u'Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relay_time = StringField(
        lazy_gettext(u'Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relay_duration = IntegerField(lazy_gettext(u'Duration On (seconds)'))
    relay_id = StringField(lazy_gettext(u'Output'),)
    relay_state = SelectField(
        lazy_gettext(u'Relay State'),
        choices=[
            ('', ''),
            ('On', lazy_gettext(u'Turn On')),
            ('Off', lazy_gettext(u'Turn Off'))
        ]
    )
    save = SubmitField(lazy_gettext(u'Add to Method'))
    restart = SubmitField(lazy_gettext(u'Restart at Beginning'))


class MethodMod(FlaskForm):
    method_id = IntegerField('Method ID', widget=widgets.HiddenInput())
    method_data_id = IntegerField('Method Data ID', widget=widgets.HiddenInput())
    method_type = HiddenField('Method Type')
    method_select = HiddenField('Method Select')
    name = StringField(lazy_gettext(u'Name'))
    daily_time_start = StringField(
        lazy_gettext(u'Start HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    daily_time_end = StringField(
        lazy_gettext(u'End HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    time_start = StringField(
        lazy_gettext(u'Start YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    time_end = StringField(
        lazy_gettext(u'End YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    relay_daily_time = StringField(
        lazy_gettext(u'Time HH:MM:SS'),
        render_kw={"placeholder": "HH:MM:SS"}
    )
    relay_time = StringField(
        lazy_gettext(u'Time YYYY-MM-DD HH:MM:SS'),
        render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"}
    )
    duration = DecimalField(lazy_gettext(u'Duration (seconds)'))
    duration_end = DecimalField(lazy_gettext(u'End After (seconds)'))
    setpoint_start = DecimalField(lazy_gettext(u'Start Setpoint'))
    setpoint_end = DecimalField(lazy_gettext(u'End Setpoint'))
    relay_id = StringField(lazy_gettext(u'Relay'))
    relay_state = StringField(lazy_gettext(u'Relay State'))
    relay_duration = IntegerField(lazy_gettext(u'Relay Duration'))
    rename = SubmitField(lazy_gettext(u'Rename'))
    save = SubmitField(lazy_gettext(u'Save'))
    Delete = SubmitField(lazy_gettext(u'Delete'))
