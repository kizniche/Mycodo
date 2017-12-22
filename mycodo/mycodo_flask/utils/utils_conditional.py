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

logger = logging.getLogger(__name__)


def conditional_mod(form, mod_type):
    error = []
    conditional_type = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first().conditional_type
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Conditional"))

    if mod_type == 'delete':
        if not error:
            delete_entry_with_id(Conditional,
                                 form.conditional_id.data)
            conditional_actions = ConditionalActions.query.filter(
                ConditionalActions.conditional_id == form.conditional_id.data).all()
            for each_cond_action in conditional_actions:
                db.session.delete(each_cond_action)
            db.session.commit()
            check_refresh_conditional(form.sensor_id.data,  'del')

    elif mod_type == 'modify':
        try:
            cond_mod = Conditional.query.filter(
                Conditional.id == form.conditional_id.data).first()
            cond_mod.name = form.name.data

            if conditional_type in ['relay', 'conditional_output']:
                if form.if_relay_id.data:
                    cond_mod.if_relay_id = form.if_relay_id.data
                else:
                    cond_mod.if_relay_id = None
                    cond_mod.if_relay_state = form.if_relay_state.data
                cond_mod.if_relay_duration = form.if_relay_duration.data

            else:
                if form.measurement.data:
                    cond_mod.measurement = form.measurement.data
                else:
                    error.append("Must select a measurement")
                cond_mod.if_sensor_period = form.if_sensor_period.data
                cond_mod.if_sensor_measurement = form.if_sensor_measurement.data
                # cond_mod.if_sensor_edge_select = form.if_sensor_edge_select.data
                # cond_mod.if_sensor_edge_detected = form.if_sensor_edge_detected.data
                # cond_mod.if_sensor_gpio_state = form.if_sensor_gpio_state.data
                cond_mod.if_sensor_direction = form.if_sensor_direction.data
                cond_mod.if_sensor_setpoint = form.if_sensor_setpoint.data

            if not error:
                db.session.commit()
                check_refresh_conditional(form.sensor_id.data, 'mod')

        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_action_add(form):
    error = []
    conditional_type = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first().conditional_type
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Conditional"))

    try:
        new_action = ConditionalActions()
        new_action.conditional_id = form.conditional_id.data
        new_action.do_action = form.do_action.data
        new_action.save()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_action_mod(form, mod_type):
    error = []
    cond = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first()
    action = '{action} {controller}'.format(
        action=gettext("Mod"),
        controller=gettext("Conditional"))

    if mod_type == 'delete':
        delete_entry_with_id(ConditionalActions,
                             form.conditional_action_id.data)
    elif mod_type == 'modify':
        try:
            mod_action = ConditionalActions.query.filter(
                ConditionalActions.id == form.conditional_action_id.data).first()
            mod_action.do_action = form.do_action.data
            if form.do_action.data == 'relay':
                if form.do_relay_id.data:
                    mod_action.do_relay_id = form.do_relay_id.data
                else:
                    mod_action.do_relay_id = None
                mod_action.do_relay_state = form.do_relay_state.data
                mod_action.do_relay_duration = form.do_relay_duration.data
            elif form.do_action.data == 'deactivate_pid':
                if form.do_pid_id.data:
                    mod_action.do_pid_id = form.do_pid_id.data
                else:
                    mod_action.do_pid_id = None
            elif form.do_action.data == 'email':
                mod_action.do_action_string = form.do_action_string.data
            elif form.do_action.data in ['photo_email', 'video_email']:
                mod_action.do_action_string = form.do_action_string.data
                mod_action.do_camera_id = form.do_camera_id.data
                if (form.do_action.data == 'video_email' and
                        Camera.query.filter(
                            and_(Camera.id == form.do_camera_id.data,
                                 Camera.library != 'picamera')).count()):
                    error.append('Only Pi Cameras can record video')
            elif form.do_action.data == 'flash_lcd':
                if form.do_lcd_id.data:
                    mod_action.do_lcd_id = form.do_lcd_id.data
                else:
                    mod_action.do_lcd_id = None
            elif form.do_action.data == 'photo':
                if form.do_camera_id.data:
                    mod_action.do_camera_id = form.do_camera_id.data
                else:
                    mod_action.do_camera_id = None
            elif form.do_action.data == 'video':
                if form.do_camera_id.data:
                    if (Camera.query.filter(
                            and_(Camera.id == form.do_camera_id.data,
                                 Camera.library != 'picamera')).count()):
                        error.append('Only Pi Cameras can record video')
                    mod_action.do_camera_id = form.do_camera_id.data
                else:
                    mod_action.do_camera_id = None
                mod_action.do_camera_duration = form.do_camera_duration.data
            elif form.do_action.data == 'command':
                mod_action.do_action_string = form.do_action_string.data
            if not error:
                db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

        check_refresh_conditional(cond.sensor_id, 'mod')

    flash_success_errors(error, action, url_for('page_routes.page_function'))


def conditional_reorder(cond_id, display_order, direction):
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


def conditional_activate(form):
    dev_id = form.conditional_id.data.input_id.data
    controller_activate_deactivate('activate', 'Conditional', dev_id)


def conditional_deactivate(form):
    dev_id = form.conditional_id.data.input_id.data
    controller_activate_deactivate('deactivate', 'Conditional', dev_id)


def check_refresh_conditional(cont_id, cond_mod):
    error = []
    action = '{action} {controller}'.format(
        action=gettext("Refresh"),
        controller=gettext("Conditional"))

    control = DaemonControl()
    control.refresh_conditional(cont_id, cond_mod)

    flash_success_errors(error, action, url_for('page_routes.page_function'))
