# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import flash
from flask import url_for
from flask_babel import gettext

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
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


def conditional_mod(form):
    """Modify a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Conditional"))

    try:
        cond_mod = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
        cond_mod.name = form.name.data
        cond_mod.conditional_statement = form.conditional_statement.data
        cond_mod.period = form.period.data
        cond_mod.refractory_period = form.refractory_period.data

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
        action=gettext("Delete"),
        controller=gettext("Conditional"))

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

            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().conditional)

            try:
                display_order.remove(cond_id)
                DisplayOrder.query.first().conditional = list_to_csv(
                    display_order)
            except Exception:  # id not in list
                pass

            db.session.commit()

            # Check display order for conditional IDs that don't exist
            # Delete any non-existent IDs from order list
            fixed_display_order = display_order
            fixed = False
            for each_id in display_order:
                if not Conditional.query.filter(
                        Conditional.unique_id == each_id).count():
                    fixed = True
                    fixed_display_order.remove(each_id)
            if fixed:
                DisplayOrder.query.first().conditional = list_to_csv(
                    fixed_display_order)
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
        action=gettext("Add"),
        controller='{} {}'.format(gettext("Conditional"), gettext("Condition")))

    cond = Conditional.query.filter(
        Conditional.unique_id == form.function_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before adding a Condition")

    try:
        new_condition = ConditionalConditions()
        new_condition.conditional_id = form.function_id.data
        new_condition.condition_type = form.condition_type.data

        if new_condition.condition_type == 'measurement':
            new_condition.max_age = 360

        if not error:
            new_condition.save()

            cond_mod = Conditional.query.filter(
                Conditional.unique_id == form.function_id.data).first()
            if not cond_mod.conditional_statement:
                new_statement = '{{{{{id}}}}}'.format(
                    id=new_condition.unique_id.split('-')[0])
            else:
                new_statement = '{orig} and {{{{{id}}}}}'.format(
                    orig=cond_mod.conditional_statement,
                    id=new_condition.unique_id.split('-')[0])

            cond_mod.conditional_statement = new_statement
            db.session.commit()

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
        action=gettext("Mod"),
        controller='{} {}'.format(gettext("Conditional"), gettext("Condition")))

    try:
        conditional = Conditional.query.filter(
            Conditional.unique_id == form.conditional_id.data).first()

        cond_mod = ConditionalConditions.query.filter(
            ConditionalConditions.unique_id == form.conditional_condition_id.data).first()

        if cond_mod.condition_type == 'measurement':
            error = check_form_measurements(form, error)
            cond_mod.measurement = form.measurement.data
            cond_mod.max_age = form.max_age.data

        elif cond_mod.condition_type == 'gpio_state':
            cond_mod.gpio_pin = form.gpio_pin.data

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
        action=gettext("Delete"),
        controller='{} {}'.format(gettext("Conditional"), gettext("Condition")))

    cond = ConditionalConditions.query.filter(
        ConditionalConditions.unique_id == form.conditional_condition_id.data).first()
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
        action=gettext("Activate"),
        controller=gettext("Conditional"))

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id).all()

    for each_condition in conditions:
        # Check for errors in the Conditional settings
        if each_condition.condition_type == 'measurement':
            error = check_cond_measurements(each_condition, error)

    # Check for errors in each Conditional Action
    cond_actions = Actions.query.filter(
        Actions.function_id == cond_id).all()
    for each_action in cond_actions:
        error = check_actions(each_action, error)

    if not error:
        controller_activate_deactivate(
            'activate',
            'Conditional',
            cond_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_deactivate(cond_id):
    """Deactivate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Deactivate"),
        controller=gettext("Conditional"))

    if not error:
        controller_activate_deactivate(
            'deactivate',
            'Conditional',
            cond_id)

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


def check_cond_measurements(form, error):
    """Checks if the saved variables have any errors"""
    if not form.measurement or form.measurement == '':
        error.append("Measurement must be set".format(
            meas=form.measurement))
    if not form.max_age or form.max_age <= 0:
        error.append("Max Age must be greater than 0")
    return error

