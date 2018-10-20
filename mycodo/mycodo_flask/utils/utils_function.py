# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import url_for
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.config import FUNCTION_TYPES
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Function
from mycodo.databases.models import PID
from mycodo.databases.models import Trigger
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv
from mycodo.utils.system_pi import str_is_float

logger = logging.getLogger(__name__)


#
# Function manipulation
#

def function_add(form_add_func):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Function"))
    error = []

    new_func = None

    try:
        if form_add_func.func_type.data.startswith('conditional_'):
            new_func = Conditional().save()
        elif form_add_func.func_type.data.startswith('pid_'):
            new_func = PID().save()
        elif form_add_func.func_type.data.startswith('trigger_'):
            new_func = Trigger().save()
            for id, name, _ in FUNCTION_TYPES:
                if form_add_func.func_type.data == id:
                    new_func.name = name
            new_func.trigger_type = form_add_func.func_type.data
            new_func.save()
        elif form_add_func.func_type.data.startswith('function_'):
            new_func = Function().save()
        else:
            error.append("Unknown function type: '{}'".format(
                form_add_func.func_type.data))

        if not error:
            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().function)
            DisplayOrder.query.first().function = add_display_order(
                display_order, new_func.unique_id)
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def function_mod(form):
    """Modify a Function"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=(gettext("Function")))

    try:
        function_mod = Function.query.filter(
            Function.unique_id == form.function_id.data).first()

        function_mod.name = form.name.data

        if not error:
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def function_del(function_id):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Function"))
    error = []

    try:
        delete_entry_with_id(Function, function_id)

        display_order = csv_to_list_of_str(DisplayOrder.query.first().function)
        display_order.remove(function_id)
        DisplayOrder.query.first().function = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def action_add(form):
    """Add a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller='{} {}'.format(gettext("Conditional"), gettext("Action")))

    if form.function_type.data == 'conditional':
        func = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'trigger':
        func = Trigger.query.filter(
            Trigger.unique_id == form.function_id.data).first()
    else:
        func = None
        error.append("Function type must be either 'conditional' or 'trigger'")

    if func and func.is_activated:
        error.append("Deactivate before adding an Action")

    try:
        new_action = Actions()
        new_action.function_id = form.function_id.data
        new_action.function_type = form.function_type.data
        new_action.action_type = form.action_type.data

        if not error:
            new_action.save()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def action_mod(form):
    """Modify a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller='{} {}'.format(gettext("Conditional"), gettext("Action")))

    error = check_form_actions(form, error)

    try:
        mod_action = Actions.query.filter(
            Actions.unique_id == form.function_action_id.data).first()

        if mod_action.action_type == 'pause_actions':
            mod_action.pause_duration = form.pause_duration.data

        elif mod_action.action_type == 'output':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_state = form.do_output_state.data
            mod_action.do_output_duration = form.do_output_duration.data

        elif mod_action.action_type == 'output_pwm':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_pwm = form.do_output_pwm.data

        elif mod_action.action_type in ['activate_controller',
                                        'deactivate_controller']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type in ['activate_pid',
                                        'deactivate_pid',
                                        'resume_pid',
                                        'pause_pid']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type in ['activate_timer',
                                        'deactivate_timer']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type == 'setpoint_pid':
            if not str_is_float(form.do_action_string.data):
                error.append("Setpoint must be an integer or float value")
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type == 'method_pid':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type == 'email':
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type in ['photo_email',
                                        'video_email']:
            mod_action.do_action_string = form.do_action_string.data
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type in ['flash_lcd_on',
                                        'flash_lcd_off',
                                        'lcd_backlight_off',
                                        'lcd_backlight_on']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type == 'photo':
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type == 'video':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_camera_duration = form.do_camera_duration.data

        elif mod_action.action_type == 'command':
            mod_action.do_action_string = form.do_action_string.data

        if not error:
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def action_del(form):
    """Delete a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller='{} {}'.format(gettext("Conditional"), gettext("Action")))

    cond = Conditional.query.filter(
        Conditional.unique_id == form.conditional_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before deleting an Action")

    try:
        if not error:
            function_action_id = Actions.query.filter(
                Actions.unique_id == form.function_action_id.data).first().unique_id
            delete_entry_with_id(Actions, function_action_id)

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def action_test_all(form):
    """Test All Conditional Actions"""
    error = []

    func_type = None
    func = None

    if form.function_type.data == 'conditional':
        func_type = gettext("Conditional")
        func = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'trigger':
        func_type = gettext("Trigger")
        func = Trigger.query.filter(
            Trigger.unique_id == form.function_id.data).first()
    else:
        error.append("Unknown Function type")

    action = '{action} {controller}'.format(
        action=gettext("Test All"),
        controller='{} {}'.format(func_type, gettext("Action")))

    if func and not func.is_activated:
        error.append("Activate the Conditional before testing all Actions")

    try:
        if not error:
            control = DaemonControl()
            control.test_trigger_actions(
                form.function_id.data,
                message="Test triggering all actions of function {}".format(form.function_id.data))
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def function_reorder(function_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Function"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     function_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().function = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_function'))


def check_form_actions(form, error):
    """Check if the Actions form inputs are valid"""
    action = Actions.query.filter(
        Actions.unique_id == form.function_action_id.data).first()
    if action.action_type == 'command':
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Command must be set")
    elif action.action_type == 'output':
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Output must be set")
        if not form.do_output_state.data or form.do_output_state.data == '':
            error.append("State must be set")
    elif action.action_type == 'output_pwm':
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Output must be set")
        if not form.do_output_pwm.data or form.do_output_pwm.data == '':
            error.append("Duty Cycle must be set")
    elif action.action_type in ['activate_pid',
                                'deactivate_pid',
                                'resume_pid',
                                'pause_pid']:
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("ID must be set")
    elif action.action_type == 'email':
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Email must be set")
    elif action.action_type in ['photo_email', 'video_email']:
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Email must be set")
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Camera must be set")
        if (form.action_type.data == 'video_email' and
                Camera.query.filter(
                    and_(Camera.unique_id == form.do_unique_id.data,
                         Camera.library != 'picamera')).count()):
            error.append('Only Pi Cameras can record video')
    elif action.action_type == 'flash_lcd_on' and not form.do_unique_id.data:
        error.append("LCD must be set")
    elif (action.action_type in ['photo', 'video'] and
            (not form.do_unique_id.data or form.do_unique_id.data == '')):
        error.append("Camera must be set")
    return error


def check_actions(action, error):
    """Check if the Actions form inputs are valid"""
    if action.action_type == 'command':
        if not action.do_action_string or action.do_action_string == '':
            error.append("Command must be set")
    elif action.action_type == 'output':
        if not action.do_unique_id or action.do_unique_id == '':
            error.append("Output must be set")
        if not action.do_output_state or action.do_output_state == '':
            error.append("State must be set")
    elif action.action_type in ['activate_pid',
                                'deactivate_pid']:
        if not action.do_unique_id or action.do_unique_id == '':
            error.append("PID must be set")
    elif action.action_type == 'email':
        if not action.do_action_string or action.do_action_string == '':
            error.append("Email must be set")
    elif action.action_type in ['photo_email', 'video_email']:
        if not action.do_action_string or action.do_action_string == '':
            error.append("Email must be set")
        if not action.do_unique_id or action.do_unique_id == '':
            error.append("Camera must be set")
        if (action.action_type == 'video_email' and
                Camera.query.filter(
                    and_(Camera.unique_id == action.do_unique_id,
                         Camera.library != 'picamera')).count()):
            error.append('Only Pi Cameras can record video')
    elif action.action_type == 'flash_lcd_on' and not action.do_unique_id:
        error.append("LCD must be set")
    elif (action.action_type in ['photo', 'video'] and
            (not action.do_unique_id or action.do_unique_id == '')):
        error.append("Camera must be set")
    return error
