# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import url_for
from flask_babel import gettext

from mycodo.databases.models import Conditional
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import PID
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.system_pi import csv_to_list_of_int

logger = logging.getLogger(__name__)


#
# Function manipulation
#

def func_add(form_add_func):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Function"))
    error = []

    if form_add_func.validate():
        try:
            if form_add_func.func_type.data == 'pid':
                new_func = PID().save()
                if not error:
                    display_order = csv_to_list_of_int(
                        DisplayOrder.query.first().pid)
                    DisplayOrder.query.first().pid = add_display_order(
                        display_order, new_func.id)
                    db.session.commit()
            elif form_add_func.func_type.data in ['conditional_measurement',
                                                  'conditional_output',
                                                  'conditional_edge']:
                new_func = Conditional()
                new_func.conditional_type = form_add_func.func_type.data
                new_func.save()
                if not error:
                    display_order = csv_to_list_of_int(
                        DisplayOrder.query.first().conditional)
                    DisplayOrder.query.first().conditional = add_display_order(
                        display_order, new_func.id)
                    db.session.commit()

        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_function'))
    else:
        flash_form_errors(form_add_func)
