# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import url_for
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import DisplayOrder
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.utils.system_pi import csv_to_list_of_int
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
            Conditional.id == form.conditional_id.data).first()
        cond_mod.name = form.name.data

        if cond_mod.conditional_type == 'conditional_edge':
            error = check_form_edge(form, error)

            cond_mod.if_sensor_edge_select = form.if_sensor_edge_select.data
            cond_mod.if_sensor_edge_detected = form.if_sensor_edge_detected.data
            cond_mod.if_sensor_gpio_state = form.if_sensor_gpio_state.data
            cond_mod.if_sensor_period = form.if_sensor_period.data

        elif cond_mod.conditional_type == 'conditional_measurement':
            error = check_form_measurements(form, error)

            cond_mod.if_sensor_measurement = form.if_sensor_measurement.data
            cond_mod.if_sensor_direction = form.if_sensor_direction.data
            cond_mod.if_sensor_setpoint = form.if_sensor_setpoint.data
            cond_mod.if_sensor_period = form.if_sensor_period.data
            cond_mod.if_sensor_max_age = form.if_sensor_max_age.data

        elif cond_mod.conditional_type == 'conditional_output':
            error = check_form_output(form, error)

            cond_mod.if_relay_id = form.if_relay_id.data
            cond_mod.if_relay_state = form.if_relay_state.data
            cond_mod.if_relay_duration = form.if_relay_duration.data

        if not error:
            db.session.commit()
            check_refresh_conditional(form.conditional_id.data)

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_del(cond_id):
    """Delete a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Conditional"))

    # Deactivate conditional
    conditional_deactivate(cond_id)

    # Refresh conditional controller
    check_refresh_conditional(cond_id)

    try:
        if not error:
            # Delete conditional
            cond = Conditional.query.filter(
                Conditional.id == cond_id).first()
            conditional_actions = ConditionalActions.query.filter(
                ConditionalActions.conditional_id == cond.id).all()
            for each_cond_action in conditional_actions:
                delete_entry_with_id(ConditionalActions, each_cond_action.id)
            delete_entry_with_id(Conditional, cond.id)

            try:
                display_order = csv_to_list_of_int(DisplayOrder.query.first().conditional)
                display_order.remove(int(cond.id))
                DisplayOrder.query.first().conditional = list_to_csv(display_order)
            except Exception:  # id not in list
                pass

            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_action_add(form):
    """Add a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Conditional"))

    cond = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before adding an Action")

    try:
        new_action = ConditionalActions()
        new_action.conditional_id = form.conditional_id.data
        new_action.do_action = form.do_action.data

        if not error:
            new_action.save()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_action_mod(form):
    """Modify a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Conditional"))

    error = check_form_actions(form, error)

    try:
        mod_action = ConditionalActions.query.filter(
            ConditionalActions.id == form.conditional_action_id.data).first()

        if mod_action.do_action == 'output':
            mod_action.do_relay_id = form.do_relay_id.data
            mod_action.do_relay_state = form.do_relay_state.data
            mod_action.do_relay_duration = form.do_relay_duration.data

        elif mod_action.do_action in ['activate_pid',
                                      'deactivate_pid']:
            mod_action.do_pid_id = form.do_pid_id.data

        elif mod_action.do_action == 'email':
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.do_action in ['photo_email',
                                      'video_email']:
            mod_action.do_action_string = form.do_action_string.data
            mod_action.do_camera_id = form.do_camera_id.data

        elif mod_action.do_action == 'flash_lcd':
            mod_action.do_lcd_id = form.do_lcd_id.data

        elif mod_action.do_action == 'photo':
            mod_action.do_camera_id = form.do_camera_id.data

        elif mod_action.do_action == 'video':
            mod_action.do_camera_id = form.do_camera_id.data
            mod_action.do_camera_duration = form.do_camera_duration.data

        elif mod_action.do_action == 'command':
            mod_action.do_action_string = form.do_action_string.data

        if not error:
            db.session.commit()
            check_refresh_conditional(form.conditional_id.data)

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_action_del(form):
    """Delete a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Conditional"))

    cond = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before deleting an Action")

    try:
        if not error:
            cond_action_id = ConditionalActions.query.filter(
                ConditionalActions.id == form.conditional_action_id.data).first().id
            delete_entry_with_id(ConditionalActions, cond_action_id)

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_reorder(cond_id, display_order, direction):
    """Reorder a Conditional"""
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Conditional"))
    error = []

    try:
        status, reord_list = reorder(display_order, cond_id, direction)
        if status == 'success':
            DisplayOrder.query.first().conditional = ','.join(map(str, reord_list))
            db.session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_activate(cond_id):
    """Activate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Activate"),
        controller=gettext("Conditional"))

    mod_cond = Conditional.query.filter(
        Conditional.id == cond_id).first()
    conditional_type = mod_cond.conditional_type
    mod_cond.is_activated = True

    # Check for errors in the Conditional settings
    if conditional_type == 'conditional_edge':
        error = check_cond_edge(mod_cond, error)
    elif conditional_type == 'conditional_measurement':
        error = check_cond_measurements(mod_cond, error)
    elif conditional_type == 'conditional_output':
        error = check_cond_output(mod_cond, error)

    # Check for errors in each Conditional Action
    cond_actions = ConditionalActions.query.filter(
        ConditionalActions.conditional_id == cond_id).all()
    for each_action in cond_actions:
        error = check_cond_actions(each_action, error)

    if not error:
        db.session.commit()
        check_refresh_conditional(cond_id)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_deactivate(cond_id):
    """Deactivate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Deactivate"),
        controller=gettext("Conditional"))

    mod_cond = Conditional.query.filter(
        Conditional.id == cond_id).first()
    mod_cond.is_activated = False

    if not error:
        db.session.commit()
        check_refresh_conditional(cond_id)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def check_refresh_conditional(cond_id):
    """Check if the Conditional is active, and if so, refresh the settings"""
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Refresh"),
        controller=gettext("Conditional"))

    cond = Conditional.query.filter(
        Conditional.id == cond_id).first()

    if cond.conditional_type == 'conditional_measurement':
        control = DaemonControl()
        control.refresh_conditionals()

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def check_form_actions(form, error):
    """Check if the Conditional Actions form inputs are valid"""
    cond_action = ConditionalActions.query.filter(
        ConditionalActions.id == form.conditional_action_id.data).first()

    if cond_action.do_action == 'command':
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Command must be set")

    elif cond_action.do_action == 'output':
        if not form.do_relay_id.data or form.do_relay_id.data == '':
            error.append("Output must be set")
        if not form.do_relay_state.data or form.do_relay_state.data == '':
            error.append("State must be set")

    elif cond_action.do_action in ['activate_pid',
                                   'deactivate_pid']:
        if not form.do_pid_id.data or form.do_pid_id.data == '':
            error.append("PID must be set")

    elif cond_action.do_action == 'email':
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Email must be set")

    elif cond_action.do_action in ['photo_email', 'video_email']:
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Email must be set")
        if not form.do_camera_id.data or form.do_camera_id.data == '':
            error.append("Camera must be set")
        if (form.do_action.data == 'video_email' and
                Camera.query.filter(
                    and_(Camera.id == form.do_camera_id.data,
                         Camera.library != 'picamera')).count()):
            error.append('Only Pi Cameras can record video')

    elif cond_action.do_action == 'flash_lcd':
        if not form.do_lcd_id.data:
            error.append("LCD must be set")

    elif cond_action.do_action == 'photo':
        if not form.do_camera_id.data or form.do_camera_id.data == '':
            error.append("Camera must be set")

    elif cond_action.do_action == 'video':
        if not form.do_camera_id.data or form.do_camera_id.data == '':
            error.append("Camera must be set")

    return error


def check_cond_actions(cond_action, error):
    """Check if the Conditional Actions form inputs are valid"""
    if cond_action.do_action == 'command':
        if not cond_action.do_action_string or cond_action.do_action_string == '':
            error.append("Command must be set")

    elif cond_action.do_action == 'output':
        if not cond_action.do_relay_id or cond_action.do_relay_id == '':
            error.append("Output must be set")
        if not cond_action.do_relay_state or cond_action.do_relay_state == '':
            error.append("State must be set")

    elif cond_action.do_action in ['activate_pid',
                                 'deactivate_pid']:
        if not cond_action.do_pid_id or cond_action.do_pid_id == '':
            error.append("PID must be set")

    elif cond_action.do_action == 'email':
        if not cond_action.do_action_string or cond_action.do_action_string == '':
            error.append("Email must be set")

    elif cond_action.do_action in ['photo_email', 'video_email']:
        if not cond_action.do_action_string or cond_action.do_action_string == '':
            error.append("Email must be set")
        if not cond_action.do_camera_id or cond_action.do_camera_id == '':
            error.append("Camera must be set")
        if (cond_action.do_action == 'video_email' and
                Camera.query.filter(
                    and_(Camera.id == cond_action.do_camera_id,
                         Camera.library != 'picamera')).count()):
            error.append('Only Pi Cameras can record video')

    elif cond_action.do_action == 'flash_lcd':
        if not cond_action.do_lcd_id:
            error.append("LCD must be set")

    elif cond_action.do_action == 'photo':
        if not cond_action.do_camera_id or cond_action.do_camera_id == '':
            error.append("Camera must be set")

    elif cond_action.do_action == 'video':
        if not cond_action.do_camera_id or cond_action.do_camera_id == '':
            error.append("Camera must be set")

    return error


def check_form_edge(form, error):
    """Checks if the submitted form has any errors"""
    if (form.if_sensor_edge_select.data == 'edge' and
            not form.if_sensor_edge_detected.data):
        error.append("If the {edge} radio button is selected,"
                     " {edge} must be set".format(
            edge=form.if_sensor_edge_detected.label.text))

    if (form.if_sensor_edge_select.data == 'state' and
            not form.if_sensor_gpio_state.data):
        error.append("If the {gpio} radio button is selected,"
                     " {gpio} must be set".format(
            gpio=form.if_sensor_gpio_state.label.text))

    if (form.if_sensor_edge_select.data == 'state' and
            form.if_sensor_period.data <= 0):
        error.append("If the {state} radio button is selected,"
                     " {per} must be greater than 1".format(
            state=form.if_sensor_gpio_state.label.text,
            per=form.if_sensor_period.label.text))

    if form.if_sensor_edge_select.data not in ['state', 'edge']:
        error.append("A radio button selection must be made")

    return error


def check_cond_edge(cond, error):
    """Checks if the saved variables have any errors"""
    if (cond.if_sensor_edge_select == 'edge' and
            not cond.if_sensor_edge_detected):
        error.append("If the Edge Detected radio button is selected,"
                     " Edge Detected must be set")

    if (cond.if_sensor_edge_select == 'state' and
            not cond.if_sensor_gpio_state):
        error.append("If the GPIO State radio button is selected,"
                     " a GPIO State must be set")

    if (cond.if_sensor_edge_select == 'state' and
            cond.if_sensor_period <= 0):
        error.append("If the GPIO State radio button is selected,"
                     " Period must be greater than 1")

    if cond.if_sensor_edge_select not in ['state', 'edge']:
        error.append("A radio button selection must be made")

    return error


def check_form_measurements(form, error):
    """Checks if the submitted form has any errors"""
    if not form.if_sensor_measurement.data or form.if_sensor_measurement.data == '':
        error.append("{meas} must be set".format(
            meas=form.if_sensor_measurement.label.text))

    if not form.if_sensor_direction.data or form.if_sensor_direction.data == '':
        error.append("{dir} must be set".format(
            dir=form.if_sensor_direction.label.text))

    if not form.if_sensor_period.data or form.if_sensor_period.data <= 0:
        error.append("{dir} must be greater than 0".format(
            dir=form.if_sensor_period.label.text))

    if not form.if_sensor_max_age.data or form.if_sensor_max_age.data <= 0:
        error.append("{dir} must be greater than 0".format(
            dir=form.if_sensor_max_age.label.text))

    return error


def check_cond_measurements(cond, error):
    """Checks if the saved variables have any errors"""
    if not cond.if_sensor_measurement or cond.if_sensor_measurement == '':
        error.append("Measurement must be set".format(
            meas=cond.if_sensor_measurement))

    if not cond.if_sensor_direction or cond.if_sensor_direction == '':
        error.append("State must be set".format(
            dir=cond.if_sensor_direction))

    if not cond.if_sensor_period or cond.if_sensor_period <= 0:
        error.append("Period must be greater than 0")

    if not cond.if_sensor_max_age or cond.if_sensor_max_age <= 0:
        error.append("Max Age must be greater than 0")

    return error


def check_form_output(form, error):
    """Checks if the submitted form has any errors"""
    if not form.if_relay_id.data:
        error.append("{id} must be set".format(
            id=form.if_relay_id.label.text))

    if not form.if_relay_state.data:
        error.append("{id} must be set".format(
            id=form.if_relay_state.label.text))

    return error


def check_cond_output(cond, error):
    """Checks if the saved variables have any errors"""
    if not cond.if_relay_id or cond.if_relay_id == '':
        error.append("An Output must be set")

    if not cond.if_relay_state or cond.if_relay_state == '':
        error.append("A State must be set")

    return error
