# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import url_for
from flask_babel import gettext

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Output
from mycodo.databases.models import Timer
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# Timers
#

def timer_add(display_order,
              form_add_timer_base,
              form_add_timer):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Timer"))
    error = []

    if not form_add_timer_base.validate():
        error.append("Correct the inputs that are invalid and resubmit")
        flash_form_errors(form_add_timer_base)
    if not form_add_timer.validate():
        error.append("Correct the inputs that are invalid and resubmit")
        flash_form_errors(form_add_timer)

    output = Output.query.filter(
        Output.unique_id == form_add_timer_base.relay_id.data).first()
    if (form_add_timer_base.timer_type.data == 'pwm_method' and
            output.relay_type != 'pwm'):
        error.append("PWM Method Timers require a PWM Output")
    elif (form_add_timer_base.timer_type.data != 'pwm_method' and
            output.relay_type == 'pwm'):
        error.append("Time and Duration Timers require a non-PWM Output")

    new_timer = Timer()
    new_timer.name = form_add_timer_base.name.data
    new_timer.relay_id = form_add_timer_base.relay_id.data
    new_timer.timer_type = form_add_timer_base.timer_type.data
    if form_add_timer_base.timer_type.data == 'time':
        new_timer.state = form_add_timer.state.data
        new_timer.time_start = form_add_timer.time_start.data
        new_timer.duration_on = form_add_timer.time_on_duration.data
        new_timer.duration_off = 0
    elif form_add_timer_base.timer_type.data == 'timespan':
        new_timer.state = form_add_timer.state.data
        new_timer.time_start = form_add_timer.time_start_duration.data
        new_timer.time_end = form_add_timer.time_end_duration.data
    elif form_add_timer_base.timer_type.data == 'duration':
        if (form_add_timer.duration_on.data <= 0 or
                form_add_timer.duration_off.data <= 0):
            error.append(gettext("Durations must be greater than 0"))
        else:
            new_timer.duration_on = form_add_timer.duration_on.data
            new_timer.duration_off = form_add_timer.duration_off.data
    elif form_add_timer_base.timer_type.data == 'pwm_method':
        new_timer.method_id = form_add_timer.method_id.data
        new_timer.method_period = form_add_timer.method_period.data
    else:
        error.append("Not a recognized Timer type")

    if not error:
        try:
            new_timer.save()
            DisplayOrder.query.first().timer = add_display_order(
                display_order, new_timer.id)
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError  as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_mod(form_mod_timer_base, form_mod_timer):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Timer"))
    error = []

    if not form_mod_timer_base.validate():
        error.append("Correct the inputs that are invalid and resubmit")
        flash_form_errors(form_mod_timer_base)
    if not form_mod_timer.validate():
        error.append("Correct the inputs that are invalid and resubmit")
        flash_form_errors(form_mod_timer)

    try:
        mod_timer = Timer.query.filter(
            Timer.id == form_mod_timer_base.timer_id.data).first()
        if mod_timer.is_activated:
            error.append(gettext("Deactivate timer controller before "
                                 "modifying its settings"))
        else:
            mod_timer.name = form_mod_timer_base.name.data
            if form_mod_timer_base.relay_id.data:
                mod_timer.relay_id = form_mod_timer_base.relay_id.data
            else:
                mod_timer.relay_id = None

            if mod_timer.timer_type == 'time':
                mod_timer.state = form_mod_timer.state.data
                mod_timer.time_start = form_mod_timer.time_start.data
                mod_timer.duration_on = form_mod_timer.time_on_duration.data
            elif mod_timer.timer_type == 'timespan':
                mod_timer.state = form_mod_timer.state.data
                mod_timer.time_start = form_mod_timer.time_start_duration.data
                mod_timer.time_end = form_mod_timer.time_end_duration.data
            elif mod_timer.timer_type == 'duration':
                mod_timer.duration_on = form_mod_timer.duration_on.data
                mod_timer.duration_off = form_mod_timer.duration_off.data
            elif mod_timer.timer_type == 'pwm_method':
                if form_mod_timer.method_id.data:
                    mod_timer.method_id = form_mod_timer.method_id.data
                else:
                    mod_timer.method_id = None
                mod_timer.method_period = form_mod_timer.method_period.data
            else:
                error.append("Unknown Timer Type")

        if not error:
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_del(form_timer):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Timer"))
    error = []

    try:
        delete_entry_with_id(Timer,
                             form_timer.timer_id.data)
        display_order = csv_to_list_of_int(DisplayOrder.query.first().timer)
        display_order.remove(int(form_timer.timer_id.data))
        DisplayOrder.query.first().timer = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_reorder(timer_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Timer"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     timer_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().timer = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_activate(form_timer):
    timer = Timer.query.filter(Timer.id == form_timer.timer_id.data).first()
    if timer.timer_type == 'pwm_method':
        # Signal the duration method can run because it's been
        # properly initiated (non-power failure)
        mod_timer = Timer.query.filter(Timer.id == form_timer.timer_id.data).first()
        mod_timer.method_start_time = 'Ready'
        db.session.commit()
    controller_activate_deactivate(
        'activate', 'Timer', form_timer.timer_id.data)


def timer_deactivate(form_timer):
    controller_activate_deactivate(
        'deactivate', 'Timer', form_timer.timer_id.data)
