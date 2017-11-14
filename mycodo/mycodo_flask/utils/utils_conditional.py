# -*- coding: utf-8 -*-
import logging
import sqlalchemy

from flask import url_for

from sqlalchemy import and_
from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext

from mycodo.mycodo_client import DaemonControl

from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import Input
from mycodo.utils.system_pi import is_int

from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors

logger = logging.getLogger(__name__)


def conditional_add(cond_type, quantity, sensor_id=None):
    error = []
    if cond_type == 'relay':
        conditional_type = gettext(u"Relay")
    elif cond_type == 'sensor':
        conditional_type = gettext(u"Input")
    else:
        error.append("Unrecognized conditional type: {cond_type}".format(
            cond_type=cond_type))
        conditional_type = None
    action = u'{action} {controller} ({type})'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Conditional"),
        type=conditional_type)

    if not error:
        if is_int(quantity, check_range=[1, 20]):
            for _ in range(0, quantity):
                new_conditional = Conditional()
                try:
                    new_conditional.conditional_type = cond_type
                    if sensor_id:
                        new_conditional.sensor_id = sensor_id
                    new_conditional.save()
                except sqlalchemy.exc.OperationalError as except_msg:
                    error.append(except_msg)
                except sqlalchemy.exc.IntegrityError as except_msg:
                    error.append(except_msg)

                if cond_type == 'sensor':
                    check_refresh_conditional(
                        sensor_id,
                        'add')
    flash_success_errors(error, action, url_for('page_routes.page_output'))


def conditional_mod(form, mod_type):
    error = []
    conditional_type = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first().conditional_type
    if conditional_type == 'relay':
        cond_type = gettext(u"Relay")
    elif conditional_type == 'sensor':
        cond_type = gettext(u"Input")
    else:
        error.append("Unrecognized conditional type: {cond_type}".format(
            cond_type=form.conditional_type.data))
        cond_type = None
    action = u'{action} {controller} ({cond_type})'.format(
        action=gettext(u"Mod"),
        controller=gettext(u"Conditional"),
        cond_type=cond_type)

    if not error:
        if mod_type == 'delete':
            delete_entry_with_id(Conditional,
                                 form.conditional_id.data)
            conditional_actions = ConditionalActions.query.filter(
                ConditionalActions.conditional_id == form.conditional_id.data).all()
            for each_cond_action in conditional_actions:
                db.session.delete(each_cond_action)
            db.session.commit()

            if conditional_type == 'sensor':
                check_refresh_conditional(
                    form.sensor_id.data,
                    'del')

        elif mod_type == 'modify':
            try:
                mod_action = Conditional.query.filter(
                    Conditional.id == form.conditional_id.data).first()
                mod_action.name = form.name.data
                if conditional_type == 'relay':
                    if form.if_relay_id.data:
                        mod_action.if_relay_id = form.if_relay_id.data
                    else:
                        mod_action.if_relay_id = None
                    mod_action.if_relay_state = form.if_relay_state.data
                    mod_action.if_relay_duration = form.if_relay_duration.data
                elif conditional_type == 'sensor':
                    mod_action.if_sensor_period = form.if_sensor_period.data
                    mod_action.if_sensor_measurement = form.if_sensor_measurement.data
                    mod_action.if_sensor_edge_select = form.if_sensor_edge_select.data
                    mod_action.if_sensor_edge_detected = form.if_sensor_edge_detected.data
                    mod_action.if_sensor_gpio_state = form.if_sensor_gpio_state.data
                    mod_action.if_sensor_direction = form.if_sensor_direction.data
                    mod_action.if_sensor_setpoint = form.if_sensor_setpoint.data
                db.session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)

            if conditional_type == 'sensor':
                check_refresh_conditional(
                    form.sensor_id.data,
                    'mod')
    flash_success_errors(error, action, url_for('page_routes.page_output'))


def conditional_action_add(form):
    error = []
    conditional_type = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first().conditional_type
    if conditional_type == 'relay':
        cond_type = gettext(u"Relay")
    elif conditional_type == 'sensor':
        cond_type = gettext(u"Input")
    else:
        error.append("Unrecognized conditional type: {cond_type}".format(
            cond_type=form.conditional_type.data))
        cond_type = None
    action = u'{action} {controller} ({cond_type})'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Conditional"),
        cond_type=cond_type)

    try:
        new_action = ConditionalActions()
        new_action.conditional_id = form.conditional_id.data
        new_action.do_action = form.do_action.data
        new_action.save()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_output'))


def conditional_action_mod(form, mod_type):
    error = []
    cond = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first()
    if cond.conditional_type == 'relay':
        cond_type = gettext(u"Relay")
    elif cond.conditional_type == 'sensor':
        cond_type = gettext(u"Input")
    else:
        error.append("Unrecognized conditional type: {cond_type}".format(
            cond_type=form.conditional_type.data))
        cond_type = None
    action = u'{action} {controller} ({cond_type})'.format(
        action=gettext(u"Mod"),
        controller=gettext(u"Conditional"),
        cond_type=cond_type)

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
                                 Camera.library == 'opencv')).count()):
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
                                 Camera.library == 'opencv')).count()):
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

        if cond.conditional_type == 'sensor':
            check_refresh_conditional(
                cond.sensor_id,
                'mod')
    flash_success_errors(error, action, url_for('page_routes.page_output'))


def conditional_activate(form):
    conditional = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first()
    conditional.is_activated = True
    db.session.commit()
    if conditional.conditional_type == 'sensor':
        check_refresh_conditional(
            form.sensor_id.data,
            'mod')


def conditional_deactivate(form):
    conditional = Conditional.query.filter(
        Conditional.id == form.conditional_id.data).first()
    conditional.is_activated = False
    db.session.commit()
    if conditional.conditional_type == 'sensor':
        check_refresh_conditional(
            form.sensor_id.data,
            'mod')


def check_refresh_conditional(sensor_id, cond_mod):
    sensor = (Input.query
              .filter(Input.id == sensor_id)
              .filter(Input.is_activated == True)
              ).first()
    if sensor:
        control = DaemonControl()
        control.refresh_sensor_conditionals(sensor_id, cond_mod)
