# -*- coding: utf-8 -*-
#
# forms_notes.py - Notes Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import FileField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import widgets


#
# Notes
#

class NoteAdd(FlaskForm):
    name = StringField(lazy_gettext('Name'))
    tags = StringField('Tags')
    note = TextAreaField(lazy_gettext('Note'))
    files = FileField(lazy_gettext('Attached Files'))
    enter_custom_date_time = BooleanField(lazy_gettext('Use Custom Date/Time'))
    date_time = StringField('Custom Date/Time')
    note_add = SubmitField(lazy_gettext('Save Note'))


class NoteOptions(FlaskForm):
    note_unique_id = StringField(widget=widgets.HiddenInput())
    note_mod = SubmitField(lazy_gettext('Edit'))
    note_del = SubmitField(lazy_gettext('Delete'))


class NoteMod(FlaskForm):
    name = StringField(lazy_gettext('Name'))
    tags = StringField(lazy_gettext('Tags'))
    files = FileField(lazy_gettext('Attached Files'))
    note = StringField(lazy_gettext('Note'))
    note_save = SubmitField(lazy_gettext('Save'))


#
# Tags
#

class TagAdd(FlaskForm):
    tag_name = StringField(lazy_gettext('Name'))
    tag_add = SubmitField(lazy_gettext('Save'))


class TagOptions(FlaskForm):
    tag_unique_id = StringField(lazy_gettext('Tag'), widget=widgets.HiddenInput())
    tag_del = SubmitField(lazy_gettext('Delete'))
