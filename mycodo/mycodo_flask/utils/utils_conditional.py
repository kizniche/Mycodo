# -*- coding: utf-8 -*-
import logging
import os

import sqlalchemy
from flask import Markup
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import DisplayOrder
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_function import check_actions
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.conditional import save_conditional_code
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


def conditional_mod(form):
    """Modify a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    try:
        error, lines_code, cmd_status, cmd_out = save_conditional_code(
            error,
            form.conditional_statement.data,
            form.function_id.data,
            ConditionalConditions.query.all(),
            Actions.query.all(),
            test=True)

        message = Markup(
            '<pre>\n\n'
            'Full Conditional Statement code:\n\n{code}\n\n'
            'Conditional Statement code analysis:\n\n{report}'
            '</pre>'.format(
                code=lines_code, report=cmd_out.decode("utf-8")))

        cond_mod = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
        cond_mod.name = form.name.data
        cond_mod.conditional_statement = form.conditional_statement.data
        cond_mod.period = form.period.data
        cond_mod.log_level_debug = form.log_level_debug.data
        cond_mod.message_include_code = form.message_include_code.data
        cond_mod.start_offset = form.start_offset.data

        if cmd_status:
            error.append("pylint returned with status: {}".format(cmd_status))

        if message:
            flash("Review your code for issues and test before putting it "
                  "into a production environment.", 'success')
            flash(message, 'success')

        if not error:
            db.session.commit()

            if cond_mod.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(
                    form.function_id.data)
                flash(gettext(
                    "Daemon response: %(resp)s",
                    resp=return_value), "success")

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_del(cond_id):
    """Delete a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    cond = Conditional.query.filter(
        Conditional.unique_id == cond_id).first()

    # Deactivate conditional if active
    if cond.is_activated:
        conditional_deactivate(cond_id)

    try:
        if not error:
            # Delete conditions
            conditions = ConditionalConditions.query.filter(
                ConditionalConditions.conditional_id == cond_id).all()
            for each_condition in conditions:
                delete_entry_with_id(ConditionalConditions,
                                     each_condition.unique_id)

            # Delete Actions
            actions = Actions.query.filter(
                Actions.function_id == cond_id).all()
            for each_action in actions:
                delete_entry_with_id(Actions,
                                     each_action.unique_id)

            delete_entry_with_id(Conditional, cond_id)

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


def conditional_condition_add(form):
    """Add a Conditional Condition"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                  gettext("Condition")))

    cond = Conditional.query.filter(
        Conditional.unique_id == form.function_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before adding a Condition")

    if form.condition_type.data == '':
        error.append("Must select a condition")

    try:
        new_condition = ConditionalConditions()
        new_condition.conditional_id = form.function_id.data
        new_condition.condition_type = form.condition_type.data

        if new_condition.condition_type == 'measurement':
            new_condition.max_age = 360

        if not error:
            new_condition.save()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_condition_mod(form):
    """Modify a Conditional condition"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                  gettext("Condition")))

    try:
        conditional = Conditional.query.filter(
            Conditional.unique_id == form.conditional_id.data).first()

        cond_mod = ConditionalConditions.query.filter(
            ConditionalConditions.unique_id == form.conditional_condition_id.data).first()

        if cond_mod.condition_type in ['measurement',
                                       'measurement_past_average',
                                       'measurement_past_sum',
                                       'measurement_dict']:
            error = check_form_measurements(form, error)
            cond_mod.measurement = form.measurement.data
            cond_mod.max_age = form.max_age.data

        elif cond_mod.condition_type == 'gpio_state':
            cond_mod.gpio_pin = form.gpio_pin.data

        elif cond_mod.condition_type in ['output_state',
                                         'output_duration_on']:
            cond_mod.output_id = form.output_id.data

        elif cond_mod.condition_type == 'controller_status':
            cond_mod.controller_id = form.controller_id.data

        if not error:
            db.session.commit()

            if conditional.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(
                    form.conditional_id.data)
                flash(gettext(
                    "Daemon response: %(resp)s",
                    resp=return_value), "success")

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_condition_del(form):
    """Delete a Conditional Condition"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                  gettext("Condition")))

    cond = Conditional.query.filter(
        Conditional.unique_id == form.conditional_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before deleting a Condition")

    try:
        if not error:
            cond_condition_id = ConditionalConditions.query.filter(
                ConditionalConditions.unique_id == form.conditional_condition_id.data).first().unique_id
            delete_entry_with_id(ConditionalConditions, cond_condition_id)

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_activate(cond_id):
    """Activate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id).all()

    for each_condition in conditions:
        # Check for errors in the Conditional settings
        error = check_cond_conditions(each_condition, error)

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id)
    if not conditions.count():
        flash(
            "Conditional activated without any Conditions. Typical "
            "Conditional Controller use involves the use of Conditions. Only "
            "proceed without Conditions if you know what you're doing.",
            'info')

    actions = Actions.query.filter(
        Actions.function_id == cond_id)
    if not actions.count():
        flash(
            "Conditional activated without any Actions. Typical "
            "Conditional Controller use involves the use of Actions. Only "
            "proceed without Actions if you know what you're doing.",
            'info')

    for each_action in actions.all():
        error = check_actions(each_action, error)

    if not error:
        controller_activate_deactivate('activate', 'Conditional', cond_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_deactivate(cond_id):
    """Deactivate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['deactivate']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    if not error:
        controller_activate_deactivate('deactivate', 'Conditional', cond_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def check_form_measurements(form, error):
    """Checks if the submitted form has any errors"""
    if not form.measurement.data or form.measurement.data == '':
        error.append("{meas} must be set".format(
            meas=form.measurement.label.text))
    if not form.max_age.data or form.max_age.data <= 0:
        error.append("{dir} must be greater than 0".format(
            dir=form.max_age.label.text))
    return error


def check_cond_conditions(cond, error):
    """Checks if the saved variables have any errors"""
    if (cond.condition_type == 'measurement' and
            (not cond.measurement or cond.measurement == '')):
        error.append(
            "Measurement must be set. Condition with ID starting with {id} "
            "is not set.".format(id=cond.unique_id.split('-')[0]))
    if (cond.condition_type == 'output_state' and
            (not cond.output_id or cond.output_id == '')):
        error.append(
            "Output must be set. Condition with ID starting with {id} "
            "is not set.".format(id=cond.unique_id.split('-')[0]))
    if cond.condition_type == 'gpio_state' and not cond.gpio_pin:
        error.append(
            "GPIO Pin must be set. Condition with ID starting with {id} "
            "is not set.".format(id=cond.unique_id.split('-')[0]))
    if not cond.max_age or cond.max_age <= 0:
        error.append("Max Age must be greater than 0")
    return error
