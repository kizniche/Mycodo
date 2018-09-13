# -*- coding: utf-8 -*-
import glob
import logging
import time
from datetime import datetime

import os
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import INSTALL_DIRECTORY
from mycodo.databases import set_uuid
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.system_pi import assure_path_exists

logger = logging.getLogger(__name__)


#
# Tags
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


def tag_rename(form):
    action = '{action} {controller}'.format(
        action=gettext("Rename"),
        controller=gettext("Tag"))
    error = []

    mod_tag = NoteTags.query.filter(NoteTags.unique_id == form.tag_unique_id.data).first()

    if not form.rename.data:
        error.append("Tag name is empty")
    if ' ' in form.rename.data:
        error.append("Tag name cannot contain spaces")

    if NoteTags.query.filter(NoteTags.name == form.rename.data).count():
        error.append("Tag already exists")

    if not error:
        mod_tag.name = form.rename.data
        db.session.commit()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def tag_del(form):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Tag"))
    error = []

    if Notes.query.filter(Notes.tags.ilike("%{0}%".format(form.tag_unique_id.data))).first():
        error.append("Cannot delete tag because it's currently assicuated with at least one note")

    if not error:
        delete_entry_with_id(NoteTags, form.tag_unique_id.data)

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


#
# Notes
#

def note_add(form):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Note"))
    error = []
    list_tags = []

    new_note = Notes()

    if not form.name.data:
        error.append("Name cannot be left blank")
    if not form.note_tags.data:
        error.append("At least one tag must be selected")
    if not form.note.data:
        error.append("Note cannot be left blank")

    try:
        for each_tag in form.note_tags.data:
            check_tag = NoteTags.query.filter(NoteTags.unique_id == each_tag).first()
            if not check_tag:
                error.append("Invalid tag: {}".format(each_tag))
            else:
                list_tags.append(check_tag.unique_id)
        new_note.tags = ",".join(list_tags)
    except Exception as msg:
        error.append("Invalid tag format: {}".format(msg))

    if form.enter_custom_date_time.data:
        try:
            new_note.date_time = datetime_time_to_utc(form.date_time.data)
        except Exception as msg:
            error.append("Error while parsing date/time: {}".format(msg))

    if form.files.data:
        new_note.unique_id = set_uuid()
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        note_file_directory = os.path.join(install_dir, 'note_attachments')
        assure_path_exists(note_file_directory)
        filename_list = []
        for each_file in form.files.raw_data:
            file_name = "{pre}_{name}".format(pre=new_note.unique_id, name=each_file.filename)
            file_save_path = os.path.join(note_file_directory, file_name)
            each_file.save(file_save_path)
            filename_list.append(file_name)
        new_note.files = ",".join(filename_list)

    if not error:
        new_note.name = form.name.data
        new_note.note = form.note.data
        new_note.save()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def note_mod(form):
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Note"))
    error = []
    list_tags = []

    mod_note = Notes.query.filter(Notes.unique_id == form.note_unique_id.data).first()

    if not form.name.data:
        error.append("Name cannot be left blank")
    if not form.note_tags.data:
        error.append("At least one tag must be selected")
    if not form.note.data:
        error.append("Note cannot be left blank")

    try:
        for each_tag in form.note_tags.data:
            check_tag = NoteTags.query.filter(NoteTags.unique_id == each_tag).first()
            if not check_tag:
                error.append("Invalid tag: {}".format(each_tag))
            else:
                list_tags.append(check_tag.unique_id)
    except Exception as msg:
        error.append("Invalid tag format: {}".format(msg))

    try:
        mod_note.date_time = datetime_time_to_utc(form.date_time.data)
    except:
        error.append("Error while parsing date/time")

    if form.files.data:
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        note_file_directory = os.path.join(install_dir, 'note_attachments')
        assure_path_exists(note_file_directory)
        if mod_note.files:
            filename_list = mod_note.files.split(",")
        else:
            filename_list = []
        for each_file in form.files.raw_data:
            file_name = "{pre}_{name}".format(pre=mod_note.unique_id, name=each_file.filename)
            file_save_path = os.path.join(note_file_directory, file_name)
            each_file.save(file_save_path)
            filename_list.append(file_name)
        mod_note.files = ",".join(filename_list)

    if not error:
        mod_note.name = form.name.data
        mod_note.tags = ",".join(list_tags)
        mod_note.note = form.note.data
        db.session.commit()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def file_del(form):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("File"))
    error = []

    if not form.note_unique_id.data:
        error.append("Unique id is empty")

    mod_note = Notes.query.filter(Notes.unique_id == form.note_unique_id.data).first()
    files_list = mod_note.files.split(",")

    if form.file_selected.data in files_list:
        try:
            files_list.remove(form.file_selected.data)
        except:
            error.append("Could not remove file from filesystem")

    if mod_note.files:
        try:
            install_dir = os.path.abspath(INSTALL_DIRECTORY)
            note_file_directory = os.path.join(install_dir, 'note_attachments')
            full_file_path = os.path.join(note_file_directory, form.file_selected.data)
            os.remove(full_file_path)
        except:
            error.append("Could not remove file from filesystem")

    if not error:
        mod_note.files = ",".join(files_list)
        db.session.commit()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def note_del(form):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Note"))
    error = []

    if not form.note_unique_id.data:
        error.append("Unique id is empty")

    note = Notes.query.filter(Notes.unique_id == form.note_unique_id.data).first()

    if note.files:
        install_dir = os.path.abspath(INSTALL_DIRECTORY)
        note_file_directory = os.path.join(install_dir, 'note_attachments')
        delete_string = "{dir}/{id}*".format(dir=note_file_directory, id=form.note_unique_id.data)
        for filename in glob.glob(delete_string):
            os.remove(filename)

    if not error:
        delete_entry_with_id(Notes, form.note_unique_id.data)

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def show_notes(form):
    error = []

    notes = Notes.query

    if form.filter_names.data:
        if '*' in form.filter_names.data or '_' in form.filter_names.data:
            looking_for = form.filter_names.data.replace('_', '__') \
                .replace('*', '%') \
                .replace('?', '_')
        else:
            looking_for = '%{0}%'.format(form.filter_names.data)
        notes = notes.filter(Notes.note.like(looking_for))

    if form.filter_tags.data:
        unique_ids_of_tags = []
        for each_tag in form.filter_tags.data.split(','):
            tag = NoteTags.query.filter(NoteTags.name == each_tag).first()
            if tag:
                unique_ids_of_tags.append(tag.unique_id)

        for each_tag_unique_id in unique_ids_of_tags:
            notes = notes.filter(Notes.tags.like('%{0}%'.format(each_tag_unique_id)))

    if form.filter_files.data:
        notes = notes.filter(Notes.tags.in_(form.filter_files.data.split(',')))

    if form.filter_notes.data:
        if '*' in form.filter_notes.data or '_' in form.filter_notes.data:
            looking_for = form.filter_notes.data.replace('_', '__') \
                .replace('*', '%') \
                .replace('?', '_')
        else:
            looking_for = '%{0}%'.format(form.filter_notes.data)
        notes = notes.filter(Notes.note.like(looking_for))

    if form.sort_direction.data == 'desc':
        if form.sort_by.data == 'id':
            notes = notes.order_by(Notes.id.desc())
        elif form.sort_by.data == 'name':
            notes = notes.order_by(Notes.name.desc())
        elif form.sort_by.data == 'date':
            notes = notes.order_by(Notes.date_time.desc())
        elif form.sort_by.data == 'tag':
            notes = notes.order_by(Notes.tags.desc())
        elif form.sort_by.data == 'file':
            notes = notes.order_by(Notes.files.desc())
        elif form.sort_by.data == 'note':
            notes = notes.order_by(Notes.note.desc())
    elif form.sort_direction.data == 'asc':
        if form.sort_by.data == 'id':
            notes = notes.order_by(Notes.id.asc())
        elif form.sort_by.data == 'name':
            notes = notes.order_by(Notes.name.asc())
        elif form.sort_by.data == 'date':
            notes = notes.order_by(Notes.date_time.asc())
        elif form.sort_by.data == 'tag':
            notes = notes.order_by(Notes.tags.asc())
        elif form.sort_by.data == 'file':
            notes = notes.order_by(Notes.files.asc())
        elif form.sort_by.data == 'note':
            notes = notes.order_by(Notes.note.asc())

    for each_error in error:
        flash('Error: {}'.format(each_error), 'error')

    if not error:
        return notes


def datetime_time_to_utc(datetime_time):
    timestamp = str(time.mktime(datetime_time.timetuple()))[:-2]
    return datetime.utcfromtimestamp(int(timestamp))
