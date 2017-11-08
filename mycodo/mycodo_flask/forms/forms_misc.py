# -*- coding: utf-8 -*-
#
# forms_misc.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from wtforms import DecimalField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import SubmitField
from wtforms import StringField
from wtforms import validators
from wtforms import widgets


#
# Camera Use
#

class Camera(FlaskForm):
    camera_id = IntegerField('Camera ID', widget=widgets.HiddenInput())
    capture_still = SubmitField(lazy_gettext(u'Capture Still'))
    start_timelapse = SubmitField(lazy_gettext(u'Start Timelapse'))
    pause_timelapse = SubmitField(lazy_gettext(u'Pause Timelapse'))
    resume_timelapse = SubmitField(lazy_gettext(u'Resume Timelapse'))
    stop_timelapse = SubmitField(lazy_gettext(u'Stop Timelapse'))
    timelapse_interval = DecimalField(
        lazy_gettext(u'Interval (seconds)'),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext(u'Photo Interval must be a positive value.')
        )]
    )
    timelapse_runtime_sec = DecimalField(
        lazy_gettext(u'Run Time (seconds)'),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext(u'Total Run Time must be a positive value.')
        )]
    )
    start_stream = SubmitField(lazy_gettext(u'Start Stream'))
    stop_stream = SubmitField(lazy_gettext(u'Stop Stream'))


#
# Conditionals
#

class Conditional(FlaskForm):
    conditional_id = IntegerField('Conditional ID', widget=widgets.HiddenInput())
    conditional_type = StringField('Conditional Type', widget=widgets.HiddenInput())
    sensor_id = IntegerField('Output ID', widget=widgets.HiddenInput())
    quantity = IntegerField(lazy_gettext(u'Quantity'))
    name = StringField(lazy_gettext(u'Name'))

    # Relay conditional options
    if_relay_id = StringField(lazy_gettext(u'If Relay ID'))
    if_relay_state = StringField(lazy_gettext(u'If Relay State'))
    if_relay_duration = DecimalField(lazy_gettext(u'If Relay Duration'))

    # Sensor conditional options
    if_sensor_period = DecimalField(lazy_gettext(u'Period'))
    if_sensor_measurement = StringField(lazy_gettext(u'Measurement'))
    if_sensor_edge_select = StringField(lazy_gettext(u'Edge or State'))
    if_sensor_edge_detected = StringField(lazy_gettext(u'Edge Detected'))
    if_sensor_gpio_state = IntegerField(lazy_gettext(u'GPIO State'))
    if_sensor_direction = StringField(lazy_gettext(u'Direction'))
    if_sensor_setpoint = DecimalField(lazy_gettext(u'Setpoint'))

    add_cond = SubmitField(lazy_gettext(u'Add Conditional'))
    save_cond = SubmitField(lazy_gettext(u'Save'))
    delete_cond = SubmitField(lazy_gettext(u'Delete'))
    activate_cond = SubmitField(lazy_gettext(u'Activate'))
    deactivate_cond = SubmitField(lazy_gettext(u'Deactivate'))


class ConditionalActions(FlaskForm):
    conditional_id = IntegerField(
        'Conditional ID', widget=widgets.HiddenInput())
    conditional_action_id = IntegerField(
        'Conditional Action ID', widget=widgets.HiddenInput())
    do_action = StringField(lazy_gettext(u'Action to Perform'))
    do_action_string = StringField(lazy_gettext(u'Action String'))
    do_relay_id = IntegerField(lazy_gettext(u'Relay'))
    do_relay_state = StringField(lazy_gettext(u'Relay State'))
    do_relay_duration = DecimalField(lazy_gettext(u'Duration'))
    do_camera_id = IntegerField(lazy_gettext(u'Camera'))
    do_camera_duration = DecimalField(lazy_gettext(u'Duration'))
    do_lcd_id = IntegerField(lazy_gettext(u'LCD ID'))
    do_pid_id = IntegerField(lazy_gettext(u'PID ID'))
    add_action = SubmitField(lazy_gettext(u'Add Action'))
    save_action = SubmitField(lazy_gettext(u'Save'))
    delete_action = SubmitField(lazy_gettext(u'Delete'))


#
# Daemon Control
#

class DaemonControl(FlaskForm):
    stop = SubmitField(lazy_gettext(u'Stop Daemon'))
    start = SubmitField(lazy_gettext(u'Start Daemon'))
    restart = SubmitField(lazy_gettext(u'Restart Daemon'))


#
# Export Options
#

class ExportOptions(FlaskForm):
    measurement = StringField(lazy_gettext(u'Measurement to Export'))
    date_range = StringField(lazy_gettext(u'Time Range DD/MM/YYYY HH:MM'))
    Export = SubmitField(lazy_gettext(u'Export'))


#
# Log viewer
#

class LogView(FlaskForm):
    lines = IntegerField(
        lazy_gettext(u'Number of Lines'),
        render_kw={'placeholder': lazy_gettext(u'Lines')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u'Number of lines should be greater than 0.')
        )]
    )
    loglogin = SubmitField(lazy_gettext(u'Login Log'))
    loghttp = SubmitField(lazy_gettext(u'HTTP Log'))
    logdaemon = SubmitField(lazy_gettext(u'Daemon Log'))
    logbackup = SubmitField(lazy_gettext(u'Backup Log'))
    logkeepup = SubmitField(lazy_gettext(u'KeepUp Log'))
    logupgrade = SubmitField(lazy_gettext(u'Upgrade Log'))
    logrestore = SubmitField(lazy_gettext(u'Restore Log'))


#
# Upgrade
#

class Upgrade(FlaskForm):
    upgrade = SubmitField(lazy_gettext(u'Upgrade Mycodo'))


#
# Backup/Restore
#

class Backup(FlaskForm):
    backup = SubmitField(lazy_gettext(u'Create Backup'))
    restore = SubmitField(lazy_gettext(u'Restore Backup'))
    delete = SubmitField(lazy_gettext(u'Delete Backup'))
    full_path = HiddenField()
    selected_dir = HiddenField()
