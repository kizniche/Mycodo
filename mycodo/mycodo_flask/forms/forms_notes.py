# -*- coding: utf-8 -*-
#
# forms_notes.py - Notes Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DateTimeField
from wtforms import FileField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import widgets

from mycodo.config_translations import TOOLTIPS_SETTINGS


#
# Notes
#

class NoteAdd(FlaskForm):
    name = StringField(
        TOOLTIPS_SETTINGS['name']['title'])
    note_tags = SelectMultipleField('Tags')
    files = FileField(lazy_gettext('Attached Files'))
    enter_custom_date_time = BooleanField(lazy_gettext('Use Custom Date/Time'))
    date_time = DateTimeField('Custom Date/Time', format='%Y-%m-%d %H:%M:%S')
    note = TextAreaField(lazy_gettext('Note'))
    note_add = SubmitField(
        TOOLTIPS_SETTINGS['save']['title'])


class NoteOptions(FlaskForm):
    note_unique_id = StringField(widget=widgets.HiddenInput())
    note_mod = SubmitField(
        TOOLTIPS_SETTINGS['edit']['title'])
    note_del = SubmitField(
        TOOLTIPS_SETTINGS['delete']['title'])


class NoteMod(FlaskForm):
    note_unique_id = StringField(widget=widgets.HiddenInput())
    file_selected = StringField(widget=widgets.HiddenInput())
    name = StringField(
        TOOLTIPS_SETTINGS['name']['title'])
    note_tags = SelectMultipleField(lazy_gettext('Tags'))
    files = FileField(lazy_gettext('Attached Files'))
    enter_custom_date_time = BooleanField(lazy_gettext('Use Custom Date/Time'))
    date_time = DateTimeField('Custom Date/Time', format='%Y-%m-%d %H:%M:%S')
    note = TextAreaField(lazy_gettext('Note'))
    file_del = SubmitField(
        TOOLTIPS_SETTINGS['delete']['title'])
    note_cancel = SubmitField(
        TOOLTIPS_SETTINGS['cancel']['title'])
    rename_name = StringField()
    file_rename = SubmitField(
        TOOLTIPS_SETTINGS['rename']['title'])
    note_del = SubmitField(
        TOOLTIPS_SETTINGS['delete']['title'])
    note_save = SubmitField(
        TOOLTIPS_SETTINGS['save']['title'])


class NotesShow(FlaskForm):
    sort_by_choices = [
        ('id', 'ID'),
        ('name', 'Name'),
        ('date', 'Date/Time'),
        ('tag', 'Tag'),
        ('file', 'File'),
        ('note', 'Note')
    ]
    sort_direction_choices = [
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ]
    filter_names = StringField(lazy_gettext('Filter Names'))
    filter_tags = StringField(lazy_gettext('Filter Tags'))
    filter_files = StringField(lazy_gettext('Filter Files'))
    filter_notes = StringField(lazy_gettext('Filter Notes'))
    sort_by = SelectField(lazy_gettext('Sort By'), choices=sort_by_choices)
    sort_direction = SelectField(lazy_gettext('Sort Direction'), choices=sort_direction_choices)
    notes_show = SubmitField(lazy_gettext('Show Notes'))
    notes_export = SubmitField(lazy_gettext('Export Notes'))
    notes_import_file = FileField('Note ZIP File')
    notes_import_upload = SubmitField(lazy_gettext('Import Notes'))


#
# Tags
#

class TagAdd(FlaskForm):
    tag_name = StringField(lazy_gettext('Tag'))
    tag_add = SubmitField(
        TOOLTIPS_SETTINGS['create']['title'])


class TagOptions(FlaskForm):
    tag_unique_id = StringField(lazy_gettext('Tag'), widget=widgets.HiddenInput())
    rename = StringField()
    tag_rename = SubmitField(
        TOOLTIPS_SETTINGS['rename']['title'])
    tag_del = SubmitField(
        TOOLTIPS_SETTINGS['delete']['title'])
