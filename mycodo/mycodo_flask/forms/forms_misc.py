# -*- coding: utf-8 -*-
#
# forms_misc.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField
from wtforms import FileField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import SubmitField
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
            message=lazy_gettext(u'Photo Interval must be a positive value')
        )]
    )
    timelapse_runtime_sec = DecimalField(
        lazy_gettext(u'Run Time (seconds)'),
        validators=[validators.NumberRange(
            min=0,
            message=lazy_gettext(u'Total Run Time must be a positive value')
        )]
    )
    start_stream = SubmitField(lazy_gettext(u'Start Stream'))
    stop_stream = SubmitField(lazy_gettext(u'Stop Stream'))


#
# Daemon Control
#

class DaemonControl(FlaskForm):
    stop = SubmitField(lazy_gettext(u'Stop Daemon'))
    start = SubmitField(lazy_gettext(u'Start Daemon'))
    restart = SubmitField(lazy_gettext(u'Restart Daemon'))


#
# Export/Import Options
#

class ExportMeasurements(FlaskForm):
    measurement = StringField(lazy_gettext(u'Measurement to Export'))
    date_range = StringField(lazy_gettext(u'Time Range DD/MM/YYYY HH:MM'))
    export_data_csv = SubmitField(lazy_gettext(u'Export Data as CSV'))

class ExportSettings(FlaskForm):
    export_settings_zip = SubmitField(lazy_gettext(u'Export Settings'))

class ExportInfluxdb(FlaskForm):
    export_influxdb_zip = SubmitField(lazy_gettext(u'Export Influxdb'))

class ImportSettings(FlaskForm):
    settings_import_file = FileField('Upload')
    settings_import_upload = SubmitField(lazy_gettext(u'Import Settings'))


#
# Log viewer
#

class LogView(FlaskForm):
    lines = IntegerField(
        lazy_gettext(u'Number of Lines'),
        render_kw={'placeholder': lazy_gettext(u'Lines')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext(u'Number of lines should be greater than 0')
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
