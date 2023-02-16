# -*- coding: utf-8 -*-
#
# forms_misc.py - Miscellaneous Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms import widgets
from wtforms.widgets import NumberInput

from mycodo.config_translations import TRANSLATIONS


#
# Energy Usage
#

class EnergyUsageAdd(FlaskForm):
    energy_usage_select = SelectField(
        '{}: {}'.format(lazy_gettext('Measurement'), lazy_gettext('Amp')))
    energy_usage_add = SubmitField(TRANSLATIONS['add']['title'])


class EnergyUsageMod(FlaskForm):
    energy_usage_id = StringField('Energy Usage ID', widget=widgets.HiddenInput())
    name = StringField(TRANSLATIONS['name']['title'])
    selection_device_measure_ids = StringField(
        '{}: {}'.format(lazy_gettext('Measurement'), lazy_gettext('Amp')))
    energy_usage_date_range = StringField(lazy_gettext('Time Range MM/DD/YYYY HH:MM'))
    energy_usage_range_calc = SubmitField(TRANSLATIONS['calculate']['title'])
    energy_usage_mod = SubmitField(TRANSLATIONS['save']['title'])
    energy_usage_delete = SubmitField(TRANSLATIONS['delete']['title'])


#
# Daemon Control
#

class DaemonControl(FlaskForm):
    stop = SubmitField(lazy_gettext('Stop Daemon'))
    start = SubmitField(lazy_gettext('Start Daemon'))
    restart = SubmitField(lazy_gettext('Restart Daemon'))


#
# Export/Import Options
#

class ExportMeasurements(FlaskForm):
    measurement = StringField(lazy_gettext('Measurement to Export'))
    date_range = StringField(lazy_gettext('Time Range MM/DD/YYYY HH:MM'))
    export_data_csv = SubmitField(lazy_gettext('Export Data as CSV'))


class ExportSettings(FlaskForm):
    export_settings_zip = SubmitField(lazy_gettext('Export Settings'))


class ImportSettings(FlaskForm):
    settings_import_file = FileField()
    settings_import_upload = SubmitField(lazy_gettext('Import Settings'))


class ExportInfluxdb(FlaskForm):
    export_influxdb_zip = SubmitField(lazy_gettext('Export Influxdb'))


#
# Log viewer
#

class LogView(FlaskForm):
    lines = IntegerField(
        'Number of Lines',
        render_kw={'placeholder': lazy_gettext('Lines')},
        validators=[validators.NumberRange(
            min=1,
            message=lazy_gettext('Number of lines should be greater than 0')
        )],
        widget=NumberInput()
    )
    search = StringField(
        lazy_gettext('Search'),
        render_kw={'placeholder': lazy_gettext('Search')},)
    log = StringField(lazy_gettext('Log'))
    log_view = SubmitField(lazy_gettext('View Log'))


#
# Upgrade
#

class Upgrade(FlaskForm):
    upgrade = SubmitField(lazy_gettext('Upgrade Mycodo'))
    upgrade_next_major_version = SubmitField(lazy_gettext(
        'Upgrade Mycodo to Next Major Version'))


#
# Backup/Restore
#

class Backup(FlaskForm):
    download = SubmitField(lazy_gettext('Download Backup'))
    backup = SubmitField(lazy_gettext('Create Backup'))
    restore = SubmitField(lazy_gettext('Restore Backup'))
    delete = SubmitField(lazy_gettext('Delete Backup'))
    full_path = HiddenField()
    selected_dir = HiddenField()
