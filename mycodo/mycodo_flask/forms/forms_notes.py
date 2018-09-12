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


#
# Notes
#

class NoteAdd(FlaskForm):
    name = StringField(lazy_gettext('Name'))
    note_tags = SelectMultipleField('Tags')
    files = FileField(lazy_gettext('Attached Files'))
    enter_custom_date_time = BooleanField(lazy_gettext('Use Custom Date/Time'))
    date_time = DateTimeField('Custom Date/Time', format='%Y-%m-%d %H:%M:%S')
    note = TextAreaField(lazy_gettext('Note'))
    note_add = SubmitField(lazy_gettext('Save'))


class NoteOptions(FlaskForm):
    note_unique_id = StringField(widget=widgets.HiddenInput())
    note_mod = SubmitField(lazy_gettext('Edit'))
    note_del = SubmitField(lazy_gettext('Delete'))


class NoteMod(FlaskForm):
    note_unique_id = StringField(widget=widgets.HiddenInput())
    name = StringField(lazy_gettext('Name'))
    note_tags = SelectMultipleField(lazy_gettext('Tags'))
    files = FileField(lazy_gettext('Attached Files'))
    enter_custom_date_time = BooleanField(lazy_gettext('Use Custom Date/Time'))
    date_time = DateTimeField('Custom Date/Time', format='%Y-%m-%d %H:%M:%S')
    note = TextAreaField(lazy_gettext('Note'))
    note_cancel = SubmitField(lazy_gettext('Cancel'))
    note_del = SubmitField(lazy_gettext('Delete'))
    note_save = SubmitField(lazy_gettext('Save'))


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


#
# Tags
#

class TagAdd(FlaskForm):
    tag_name = StringField(lazy_gettext('Tag'))
    tag_add = SubmitField(lazy_gettext('Create'))


class TagOptions(FlaskForm):
    tag_unique_id = StringField(lazy_gettext('Tag'), widget=widgets.HiddenInput())
    tag_del = SubmitField(lazy_gettext('Delete'))
