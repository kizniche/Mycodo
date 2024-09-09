# -*- coding: utf-8 -*-
import logging
import os

import sqlalchemy
from flask import current_app
from flask_babel import gettext
from markupsafe import Markup

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.utils.conditional import save_conditional_code

logger = logging.getLogger(__name__)


def conditional_mod(form):
    """Modify a Conditional."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": [],
        "page_refresh": True,
        "return_text": [],
        "name": None
    }

    cmd_status = None
    pylint_message = ""

    try:
        if not current_app.config['TESTING']:
            messages["error"], lines_code, cmd_status, cmd_out = save_conditional_code(
                messages["error"],
                form.conditional_import.data,
                form.conditional_initialize.data,
                form.conditional_statement.data,
                form.conditional_status.data,
                form.function_id.data,
                ConditionalConditions.query.all(),
                Actions.query.all(),
                timeout=form.pyro_timeout.data,
                test=form.use_pylint.data)

            code_str = f"<pre>\n\nFull Conditional code:\n\n{lines_code}"
            if form.use_pylint.data:
                code_str += f'\npylint code analysis:\n\n{cmd_out.decode("utf-8")}'
            code_str += "</pre>"
            pylint_message = Markup(code_str)

        cond_mod = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
        cond_mod.name = form.name.data
        messages["name"] = form.name.data
        cond_mod.conditional_import = form.conditional_import.data
        cond_mod.conditional_initialize = form.conditional_initialize.data
        cond_mod.conditional_statement = form.conditional_statement.data
        cond_mod.conditional_status = form.conditional_status.data
        cond_mod.period = form.period.data
        cond_mod.log_level_debug = form.log_level_debug.data
        cond_mod.use_pylint = form.use_pylint.data
        cond_mod.message_include_code = form.message_include_code.data
        cond_mod.start_offset = form.start_offset.data
        cond_mod.pyro_timeout = form.pyro_timeout.data

        if cmd_status:
            messages["warning"].append("pylint returned with status: {}. Note that warnings are not errors. This only indicates that the pylint analysis did not return a perfect score of 10.".format(cmd_status))

        if pylint_message:
            messages["info"].append("Review your code for issues and test before putting it "
                  "into a production environment.")
            messages["return_text"].append(pylint_message)

        if not messages["error"]:
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller=TRANSLATIONS['conditional']['title']))

            if cond_mod.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(
                    form.function_id.data)
                messages["success"].append(gettext(
                    "Daemon response: %(resp)s",
                    resp=return_value))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_del(cond_id):
    """Delete a Conditional."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    cond = Conditional.query.filter(
        Conditional.unique_id == cond_id).first()

    # Deactivate conditional if active
    if cond.is_activated:
        conditional_deactivate(cond_id)

    try:
        if not messages["error"]:
            # Delete conditions
            conditions = ConditionalConditions.query.filter(
                ConditionalConditions.conditional_id == cond_id).all()
            for each_condition in conditions:
                delete_entry_with_id(
                    ConditionalConditions,
                    each_condition.unique_id,
                    flash_message=False)

            # Delete Actions
            actions = Actions.query.filter(
                Actions.function_id == cond_id).all()
            for each_action in actions:
                delete_entry_with_id(
                    Actions,
                    each_action.unique_id,
                    flash_message=False)

            delete_entry_with_id(
                Conditional, cond_id, flash_message=False)

            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['delete']['title'],
                controller=TRANSLATIONS['conditional']['title']))

            try:
                file_path = os.path.join(
                    PATH_PYTHON_CODE_USER, 'conditional_{}.py'.format(
                        cond.unique_id))
                os.remove(file_path)
            except:
                pass

            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_condition_add(form):
    """Add a Conditional Condition."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    condition_id = None

    cond = Conditional.query.filter(
        Conditional.unique_id == form.function_id.data).first()
    if cond.is_activated:
        messages["error"].append("Deactivate the Conditional before adding a Condition")

    if form.condition_type.data == '':
        messages["error"].append("Must select a condition")

    try:
        new_condition = ConditionalConditions()
        new_condition.conditional_id = form.function_id.data
        new_condition.condition_type = form.condition_type.data

        if new_condition.condition_type == 'measurement':
            new_condition.max_age = 360

        if not messages["error"]:
            new_condition.save()
            condition_id = new_condition.unique_id
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['add']['title'],
                controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                          gettext("Condition"))))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages, condition_id


def conditional_condition_mod(form):
    """Modify a Conditional condition."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        cond_mod = ConditionalConditions.query.filter(
            ConditionalConditions.unique_id == form.conditional_condition_id.data).first()

        conditional = Conditional.query.filter(
            Conditional.unique_id == cond_mod.conditional_id).first()

        if cond_mod.condition_type in ['measurement',
                                       'measurement_and_ts',
                                       'measurement_past_average',
                                       'measurement_past_sum',
                                       'measurement_dict']:
            messages["error"] = check_form_measurements(form, messages["error"])
            cond_mod.measurement = form.measurement.data
            cond_mod.max_age = form.max_age.data

        elif cond_mod.condition_type == 'gpio_state':
            cond_mod.gpio_pin = form.gpio_pin.data

        elif cond_mod.condition_type in ['output_state',
                                         'output_duration_on']:
            cond_mod.output_id = form.output_id.data

        elif cond_mod.condition_type == 'controller_status':
            cond_mod.controller_id = form.controller_id.data

        if not messages["error"]:
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                          gettext("Condition"))))

            if conditional.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(
                    form.conditional_id.data)
                messages["success"].append(gettext(
                    "Daemon response: %(resp)s",
                    resp=return_value))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_condition_del(form):
    """Delete a Conditional Condition."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    condition = ConditionalConditions.query.filter(
        ConditionalConditions.unique_id == form.conditional_condition_id.data).first()
    if not condition:
        messages["error"].append("Condition not found")

    conditional = Conditional.query.filter(
        Conditional.unique_id == condition.conditional_id).first()
    if conditional.is_activated:
        messages["error"].append("Deactivate the Conditional before deleting a Condition")

    try:
        if not messages["error"]:
            delete_entry_with_id(
                ConditionalConditions, condition.unique_id, flash_message=False)
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['delete']['title'],
                controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                          gettext("Condition"))))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_activate(cond_id):
    """Activate a Conditional."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id).all()

    for each_condition in conditions:
        # Check for errors in the Conditional settings
        messages["success"] = check_cond_conditions(
            each_condition, messages["success"])

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id)
    if not conditions.count():
        messages["info"].append(
            "Conditional activated without any Conditions. Typical "
            "Conditional Function use involves the use of Conditions. Only "
            "proceed without Conditions if you know what you're doing.")

    actions = Actions.query.filter(Actions.function_id == cond_id)
    if not actions.count():
        messages["info"].append(
            "Conditional activated without any Actions. Typical "
            "Conditional Function use involves the use of Actions. Only "
            "proceed without Actions if you know what you're doing.")

    messages = controller_activate_deactivate(
        messages, 'activate', 'Conditional', cond_id, flash_message=False)

    if not messages["success"]:
        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['activate']['title'],
            controller=TRANSLATIONS['conditional']['title']))

    return messages


def conditional_deactivate(cond_id):
    """Deactivate a Conditional."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    messages = controller_activate_deactivate(
        messages, 'deactivate', 'Conditional', cond_id, flash_message=False)

    if not messages["error"]:
        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['deactivate']['title'],
            controller=TRANSLATIONS['conditional']['title']))

    return messages


def check_form_measurements(form, error):
    """Checks if the submitted form has any errors."""
    if not form.measurement.data or form.measurement.data == '':
        error.append("{meas} must be set".format(
            meas=form.measurement.label.text))
    if not form.max_age.data or form.max_age.data <= 0:
        error.append("{dir} must be greater than 0".format(
            dir=form.max_age.label.text))
    return error


def check_cond_conditions(cond, error):
    """Checks if the saved variables have any errors."""
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
