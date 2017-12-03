# -*- coding: utf-8 -*-
import logging
import sqlalchemy

from flask import flash
from flask import url_for

from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Math
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import list_to_csv

from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder

logger = logging.getLogger(__name__)


#
# Math manipulation
#

def math_add(form_add_math):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Math"))
    error = []

    if form_add_math.validate():
        new_math = Math()
        new_math.name = 'Math {name}'.format(name=form_add_math.math_type.data)
        new_math.math_type = form_add_math.math_type.data

        try:
            new_math.save()

            display_order = csv_to_list_of_int(
                DisplayOrder.query.first().math)
            DisplayOrder.query.first().math = add_display_order(
                display_order, new_math.id)
            db.session.commit()

            flash(gettext(
                u"%(type)s Math with ID %(id)s (%(uuid)s) successfully added",
                type=form_add_math.math_type.data,
                id=new_math.id,
                uuid=new_math.unique_id),
                  "success")
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_input'))
    else:
        flash_form_errors(form_add_math)


def math_mod(form_mod_math):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Math"))
    error = []

    try:
        mod_math = Math.query.filter(
            Math.id == form_mod_math.math_id.data).first()

        if mod_math.is_activated:
            error.append(gettext(
                u"Deactivate Math controller before modifying its "
                u"settings"))

        if not error:
            mod_math.name = form_mod_math.name.data
            mod_math.period = form_mod_math.period.data

            if form_mod_math.inputs.data:
                inputs_joined = ";".join(form_mod_math.inputs.data)
                mod_math.inputs = inputs_joined
            else:
                mod_math.inputs = ''

            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_input'))


def math_del(form_mod_math):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Math"))
    error = []

    try:
        math = Math.query.filter(
            Math.id == form_mod_math.math_id.data).first()
        if math.is_activated:
            controller_activate_deactivate(
                'deactivate',
                'Math',
                form_mod_math.math_id.data)

        delete_entry_with_id(Math, form_mod_math.math_id.data)
        try:
            display_order = csv_to_list_of_int(DisplayOrder.query.first().math)
            display_order.remove(int(form_mod_math.math_id.data))
            DisplayOrder.query.first().math = list_to_csv(display_order)
        except Exception:  # id not in list
            pass
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_input'))


def math_reorder(math_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"Math"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     math_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().math = ','.join(map(str, reord_list))
            db.session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_input'))


def math_activate(form_mod_math):
    controller_activate_deactivate('activate',
                                   'Math',
                                   form_mod_math.math_id.data)


def math_deactivate(form_mod_math):
    controller_activate_deactivate('deactivate',
                                   'Math',
                                   form_mod_math.math_id.data)
