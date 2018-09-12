# -*- coding: utf-8 -*-
import logging

from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors

logger = logging.getLogger(__name__)


#
# Tag manipulation
#


def tag_add(form):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Tag"))
    error = []

    if not form.tag_name.data:
        error.append("Tag name is empty")
    if ' ' in form.tag_name.data:
        error.append("Tag name cannot contain spaces")

    if NoteTags.query.filter(NoteTags.name == form.tag_name.data).count():
        error.append("Tag already exists")

    if not error:
        new_tag = NoteTags()
        new_tag.name = form.tag_name.data
        new_tag.save()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def tag_del(form):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Tag"))
    error = []

    if not error:
        delete_entry_with_id(NoteTags, form.tag_unique_id.data)

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def note_add(form):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Note"))
    error = []

    new_note = Notes()

    try:
        for each_tag in form.note_tags.data.split(','):
            if not NoteTags.query.filter(NoteTags.name == each_tag).count():
                error.append("Invalid tag: {}".format(each_tag))
    except Exception as msg:
        error.append("Invalid tag format: {}".format(msg))

    if form.enter_custom_date_time.data:
        try:
            # datetime_object = datetime.datetime.strptime(form.date_time.data, '%Y-%m-%d %H:%M:%S')
            new_note.date_time = form.date_time.data
            # error.append("TEST00: {}".format(form.date_time.data))
        except:
            error.append("Error while parsing date/time")

    if not error:
        new_note.name = form.name.data
        new_note.tags = form.note_tags.data
        new_note.files = form.files.data
        new_note.note = form.note.data
        new_note.save()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def note_mod(form):
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Note"))
    error = []

    if not error:
        pass

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def note_del(form):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Note"))
    error = []

    if not form.note_unique_id.data:
        error.append("Unique id is empty")

    if not error:
        delete_entry_with_id(Notes, form.note_unique_id.data)

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def show_notes(form):
    action = '{action} {controller}'.format(
        action=gettext("Search"),
        controller=gettext("Notes"))
    error = []

    notes = Notes.query

    if form.filter_tags.data:
        for each_tag in form.filter_tags.data.split(','):
            count = NoteTags.query.filter(NoteTags.name == each_tag).count()
            if count == 0:
                error.append("Unknown tag: {}".format(each_tag))

        if not error:
            notes = notes.filter(Notes.tags.in_(form.filter_tags.data.split(',')))

    if form.filter_notes.data:
        if '*' in form.filter_notes.data or '_' in form.filter_notes.data:
            looking_for = form.filter_notes.data.replace('_', '__') \
                .replace('*', '%') \
                .replace('?', '_')
        else:
            looking_for = '%{0}%'.format(form.filter_notes.data)
        notes = notes.filter(Notes.note.like(looking_for))

    notes = notes.order_by(Notes.id.desc())

    for each_error in error:
        flash('Error: {}'.format(each_error), 'error')

    if not error:
        return notes
