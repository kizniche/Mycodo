# -*- coding: utf-8 -*-
import csv
import glob
import logging
import socket
import time
import uuid
import zipfile
from datetime import datetime

import io
import os
import shutil
from flask import flash
from flask import url_for
from flask_babel import gettext
from werkzeug.utils import secure_filename

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import PATH_NOTE_ATTACHMENTS
from mycodo.config_translations import TRANSLATIONS
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
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['tag']['title'])
    error = []

    disallowed_tag_names = ['device_id', 'unit', 'channel']

    if not form.tag_name.data:
        error.append("Tag name is empty")
    if ' ' in form.tag_name.data:
        error.append("Tag name cannot contain spaces")
    elif form.tag_name.data in disallowed_tag_names:
        error.append("Tag name cannot be from this list: {}".format(disallowed_tag_names))

    if NoteTags.query.filter(NoteTags.name == form.tag_name.data).count():
        error.append("Tag already exists")

    if not error:
        new_tag = NoteTags()
        new_tag.name = form.tag_name.data
        new_tag.save()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def tag_rename(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['rename']['title'],
        controller=TRANSLATIONS['tag']['title'])
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
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['tag']['title'])
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
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['note']['title'])
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
            check_tag = NoteTags.query.filter(
                NoteTags.unique_id == each_tag).first()
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
        assure_path_exists(PATH_NOTE_ATTACHMENTS)
        filename_list = []
        for each_file in form.files.raw_data:
            file_name = "{pre}_{name}".format(
                pre=new_note.unique_id, name=each_file.filename)
            file_save_path = os.path.join(PATH_NOTE_ATTACHMENTS, file_name)
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
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['note']['title'])
    error = []
    list_tags = []

    mod_note = Notes.query.filter(
        Notes.unique_id == form.note_unique_id.data).first()

    if not form.name.data:
        error.append("Name cannot be left blank")
    if not form.note_tags.data:
        error.append("At least one tag must be selected")
    if not form.note.data:
        error.append("Note cannot be left blank")

    try:
        for each_tag in form.note_tags.data:
            check_tag = NoteTags.query.filter(
                NoteTags.unique_id == each_tag).first()
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
        assure_path_exists(PATH_NOTE_ATTACHMENTS)
        if mod_note.files:
            filename_list = mod_note.files.split(",")
        else:
            filename_list = []
        for each_file in form.files.raw_data:
            file_name = "{pre}_{name}".format(
                pre=mod_note.unique_id, name=each_file.filename)
            file_save_path = os.path.join(PATH_NOTE_ATTACHMENTS, file_name)
            each_file.save(file_save_path)
            filename_list.append(file_name)
        mod_note.files = ",".join(filename_list)

    if not error:
        mod_note.name = form.name.data
        mod_note.tags = ",".join(list_tags)
        mod_note.note = form.note.data
        db.session.commit()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def file_rename(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['rename']['title'],
        controller=gettext("File"))
    error = []

    if not form.note_unique_id.data:
        error.append("Unique id is empty")
    if not form.note_unique_id.data:
        error.append("New file name cannot be blank")

    mod_note = Notes.query.filter(
        Notes.unique_id == form.note_unique_id.data).first()
    files_list = mod_note.files.split(",")

    new_file_name = "{id}_{name}".format(
        id=form.note_unique_id.data,
        name=form.rename_name.data)

    if form.file_selected.data in files_list:
        # Replace old name with new name
        files_list[files_list.index(form.file_selected.data)] = new_file_name
    else:
        error.append("File not foun din note")

    if mod_note.files:
        try:
            full_file_path = os.path.join(
                PATH_NOTE_ATTACHMENTS, form.file_selected.data)
            new_file_path = os.path.join(PATH_NOTE_ATTACHMENTS, new_file_name)
            os.rename(full_file_path, new_file_path)
        except:
            error.append("Could not remove file from filesystem")

    if not error:
        mod_note.files = ",".join(files_list)
        db.session.commit()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def file_del(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=gettext("File"))
    error = []

    if not form.note_unique_id.data:
        error.append("Unique id is empty")

    mod_note = Notes.query.filter(
        Notes.unique_id == form.note_unique_id.data).first()
    files_list = mod_note.files.split(",")

    if form.file_selected.data in files_list:
        try:
            files_list.remove(form.file_selected.data)
        except:
            error.append("Could not remove file from note")

    if mod_note.files:
        try:
            full_file_path = os.path.join(PATH_NOTE_ATTACHMENTS, form.file_selected.data)
            os.remove(full_file_path)
        except:
            error.append("Could not remove file from filesystem")

    if not error:
        mod_note.files = ",".join(files_list)
        db.session.commit()

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def note_del(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['note']['title'])
    error = []

    if not form.note_unique_id.data:
        error.append("Unique id is empty")

    note = Notes.query.filter(
        Notes.unique_id == form.note_unique_id.data).first()

    if note.files:
        delete_string = "{dir}/{id}*".format(
            dir=PATH_NOTE_ATTACHMENTS, id=form.note_unique_id.data)
        for filename in glob.glob(delete_string):
            os.remove(filename)

    if not error:
        delete_entry_with_id(Notes, form.note_unique_id.data)

    flash_success_errors(error, action, url_for('routes_page.page_notes'))


def notes_filter(error, form):
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

    return error, notes


def show_notes(form):
    error = []
    error, notes = notes_filter(error, form)

    for each_error in error:
        flash('Error: {}'.format(each_error), 'error')

    if not error:
        return notes


def export_notes(form):
    """
    Convert note table entries to CSV file, then zip CSV file and note attachments
    :param form: wtforms form object
    :return:
    """
    error = []
    attach_files = []

    error, notes = notes_filter(error, form)

    if notes.count() == 0:
        error.append("Cannot Export Notes: No notes were found with the current search filters.")

    date_time_now = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    file_name = '{time}_{host}_notes_exported.csv'.format(time=date_time_now, host=socket.gethostname())
    full_path_csv = os.path.join('/var/tmp/', file_name)

    with open(full_path_csv, mode='w') as csv_file:
        cw = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        cw.writerow(['ID', 'UUID', 'Time', 'Name', 'Note', 'Tags', 'Files'])
        for each_note in notes:
            tags = {}
            list_tag_id_names = []
            for each_tag_id in each_note.tags.split(','):
                tag_name = NoteTags.query.filter(
                    NoteTags.unique_id == each_tag_id).first().name
                tags[each_tag_id] = tag_name
                list_tag_id_names.append('{},{}'.format(each_tag_id, tag_name))

            cw.writerow([each_note.id,
                         each_note.unique_id,
                         each_note.date_time.strftime("%Y-%m-%d %H:%M:%S"),
                         each_note.name,
                         each_note.note,
                         ';'.join(list_tag_id_names),
                         each_note.files])
            attach_files.append(each_note.files.split(','))

    # Zip csv file and attachments
    data = io.BytesIO()
    with zipfile.ZipFile(data, mode='w') as z:
        z.write(full_path_csv, file_name)
        for each_file_set in attach_files:
            for each_file in each_file_set:
                path_attachment = os.path.join(PATH_NOTE_ATTACHMENTS, each_file)
                z.write(path_attachment, os.path.join('/attachments', each_file))
    data.seek(0)

    os.remove(full_path_csv)

    if not error:
        return notes, data
    else:
        for each_error in error:
            flash('{}'.format(each_error), 'error')
        return notes, None


def import_notes(form):
    """
    Receive a zip file containing a CSV file and note attachments
    """
    action = '{action} {controller}'.format(
        action=gettext("Import"),
        controller=TRANSLATIONS['note']['title'])
    error = []

    upload_folder = os.path.join(INSTALL_DIRECTORY, 'upload')
    tmp_folder = os.path.join(upload_folder, 'mycodo_notes_tmp')
    full_path = None

    try:
        if not form.notes_import_file.data:
            error.append('No file present')
        elif form.notes_import_file.data.filename == '':
            error.append('No file name')

        if not error:
            # Save file to upload directory
            filename = secure_filename(
                form.notes_import_file.data.filename)
            full_path = os.path.join(tmp_folder, filename)
            assure_path_exists(upload_folder)
            assure_path_exists(tmp_folder)
            form.notes_import_file.data.save(
                os.path.join(tmp_folder, filename))

            # Unzip file
            try:
                zip_ref = zipfile.ZipFile(full_path, 'r')
                zip_ref.extractall(tmp_folder)
                zip_ref.close()
            except Exception as err:
                logger.exception(1)
                error.append("Exception while extracting zip file: "
                             "{err}".format(err=err))

        if not error:
            found_csv = False
            for each_file in os.listdir(tmp_folder):
                if each_file.endswith('_notes_exported.csv') and not found_csv:
                    found_csv = True
                    count_notes = 0
                    count_notes_skipped = 0
                    count_attach = 0
                    logger.error(each_file)

                    file_csv = os.path.join(tmp_folder, each_file)
                    path_attachments = os.path.join(tmp_folder, 'attachments')

                    with open(file_csv, 'r' ) as theFile:
                        reader = csv.DictReader(theFile)
                        for line in reader:
                            if not Notes.query.filter(Notes.unique_id == line['UUID']).count():
                                count_notes += 1

                                new_note = Notes()
                                new_note.unique_id = line['UUID']
                                new_note.date_time = datetime.strptime(line['Time'], '%Y-%m-%d %H:%M:%S')
                                new_note.name = line['Name']
                                new_note.note = line['Note']

                                tag_ids = []
                                tags = {}
                                for each_tag in line['Tags'].split(';'):
                                    tags[each_tag.split(',')[0]] = each_tag.split(',')[1]
                                    tag_ids.append(each_tag.split(',')[0])

                                for each_tag_id, each_tag_name in tags.items():
                                    if (not NoteTags.query.filter(NoteTags.unique_id == each_tag_id).count() and
                                            not NoteTags.query.filter(NoteTags.name == each_tag_name).count()):
                                        new_tag = NoteTags()
                                        new_tag.unique_id = each_tag_id
                                        new_tag.name = each_tag_name
                                        new_tag.save()

                                    elif (not NoteTags.query.filter(NoteTags.unique_id == each_tag_id).count() and
                                            NoteTags.query.filter(NoteTags.name == each_tag_name).count()):
                                        new_tag = NoteTags()
                                        new_tag.unique_id = each_tag_id
                                        new_tag.name = each_tag_name + str(uuid.uuid4())[:8]
                                        new_tag.save()

                                new_note.tags = ','.join(tag_ids)
                                new_note.files = line['Files']
                                new_note.save()

                                for each_file in line['Files'].split(','):
                                    count_attach += 1
                                    os.rename(os.path.join(path_attachments, each_file),
                                              os.path.join(PATH_NOTE_ATTACHMENTS, each_file))
                            else:
                                count_notes_skipped += 1

                    if (count_notes + count_attach) == 0:
                        error.append("0 imported, {notes} skipped".format(
                            notes=count_notes_skipped))
                    else:
                        flash("Imported {notes} notes and {attach} "
                              "attachments".format(notes=count_notes,
                                                   attach=count_attach),
                              "success")

            if not found_csv:
                error.append("Cannot import notes: Could not find CSV file in ZIP archive.")

    except Exception as err:
        error.append("Exception: {}".format(err))
    finally:
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)  # Delete tmp directory

    flash_success_errors(error, action, url_for('routes_page.page_export'))


def datetime_time_to_utc(datetime_time):
    timestamp = str(time.mktime(datetime_time.timetuple()))[:-2]
    return datetime.utcfromtimestamp(int(timestamp))
