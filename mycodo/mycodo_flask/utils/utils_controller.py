# -*- coding: utf-8 -*-
import logging

import os
import sqlalchemy
from flask import url_for
from flask_babel import gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import CustomController
from mycodo.databases.models import DisplayOrder
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_string
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.controllers import parse_controller_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


def controller_mod(form, request_form):
    """Modify a Custom Controller"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['controller']['title'])

    dict_controllers = parse_controller_information()

    try:
        mod_controller = CustomController.query.filter(
            CustomController.unique_id == form.function_id.data).first()

        if mod_controller.is_activated:
            error.append(gettext(
                "Deactivate controller before modifying its settings"))

        mod_controller.name = form.name.data
        mod_controller.log_level_debug = form.log_level_debug.data

        # Generate string to save from custom options
        error, custom_options = custom_options_return_string(
            error, dict_controllers, mod_controller, request_form)

        if not error:
            mod_controller.custom_options = custom_options
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def controller_del(cond_id):
    """Delete a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['controller']['title'])

    cond = CustomController.query.filter(
        CustomController.unique_id == cond_id).first()

    # Deactivate controller if active
    if cond.is_activated:
        controller_deactivate(cond_id)

    try:
        if not error:
            delete_entry_with_id(CustomController, cond_id)

            display_order = csv_to_list_of_str(DisplayOrder.query.first().function)
            display_order.remove(cond_id)
            DisplayOrder.query.first().function = list_to_csv(display_order)

            try:
                file_path = os.path.join(
                    PATH_PYTHON_CODE_USER, 'conditional_{}.py'.format(
                        cond.unique_id))
                os.remove(file_path)
            except:
                pass

            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def controller_activate(controller_id):
    """Activate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['controller']['title'])

    if not error:
        controller_activate_deactivate('activate', 'Custom', controller_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def controller_deactivate(controller_id):
    """Deactivate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['deactivate']['title'],
        controller=TRANSLATIONS['controller']['title'])

    if not error:
        controller_activate_deactivate('deactivate', 'Custom', controller_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))
