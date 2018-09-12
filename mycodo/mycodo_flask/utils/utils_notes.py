# -*- coding: utf-8 -*-
import logging

import os
import sqlalchemy
from RPi import GPIO
from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext

from mycodo.config_devices_units import MEASUREMENTS
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Notes
from mycodo.databases.models import NoteTags
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

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

    if not error:
        new_note = Notes()
        new_note.name = form.name.data
        new_note.tags = form.tags.data
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
