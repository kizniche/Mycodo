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
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.controllers import parse_controller_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import list_to_csv
from mycodo.utils.system_pi import str_is_float

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

        # Custom options
        list_options = []
        if 'custom_options' in dict_controllers[mod_controller.device]:
            for each_option in dict_controllers[mod_controller.device]['custom_options']:
                null_value = True
                for key in request_form.keys():
                    if each_option['id'] == key:
                        constraints_pass = True
                        constraints_errors = []
                        value = None
                        if each_option['type'] == 'float':
                            if str_is_float(request_form.get(key)):
                                if 'constraints_pass' in each_option:
                                    (constraints_pass,
                                     constraints_errors,
                                     mod_controller) = each_option['constraints_pass'](
                                        mod_controller, float(request_form.get(key)))
                                if constraints_pass:
                                    value = float(request_form.get(key))
                            else:
                                error.append(
                                    "{name} must represent a float/decimal value "
                                    "(submitted '{value}')".format(
                                        name=each_option['name'],
                                        value=request_form.get(key)))

                        elif each_option['type'] == 'integer':
                            if is_int(request_form.get(key)):
                                if 'constraints_pass' in each_option:
                                    (constraints_pass,
                                     constraints_errors,
                                     mod_controller) = each_option['constraints_pass'](
                                        mod_controller, int(request_form.get(key)))
                                if constraints_pass:
                                    value = int(request_form.get(key))
                            else:
                                error.append(
                                    "{name} must represent an integer value "
                                    "(submitted '{value}')".format(
                                        name=each_option['name'],
                                        value=request_form.get(key)))

                        elif each_option['type'] in ['text', 'select']:
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_controller) = each_option['constraints_pass'](
                                    mod_controller, request_form.get(key))
                            if constraints_pass:
                                value = request_form.get(key)

                        elif each_option['type'] == 'bool':
                            value = bool(request_form.get(key))

                        for each_error in constraints_errors:
                            error.append(
                                "Error: {name}: {error}".format(
                                    name=each_option['name'],
                                    error=each_error))

                        if value is not None:
                            null_value = False
                            option = '{id},{value}'.format(
                                id=key,
                                value=value)
                            list_options.append(option)

                if null_value:
                    option = '{id},'.format(id=each_option['id'])
                    list_options.append(option)

        mod_controller.custom_options = ';'.join(list_options)

        if not error:
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
        controller_activate_deactivate('activate', 'CustomController', controller_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def controller_deactivate(controller_id):
    """Deactivate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['deactivate']['title'],
        controller=TRANSLATIONS['controller']['title'])

    if not error:
        controller_activate_deactivate('deactivate', 'CustomController', controller_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))
