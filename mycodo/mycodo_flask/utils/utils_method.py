# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)

#
# Method Development
#

def is_positive_integer(number_string):
    try:
        if int(number_string) < 0:
            flash(gettext("Duration must be a positive integer"), "error")
            return False
    except ValueError:
        flash(gettext("Duration must be a valid integer"), "error")
        return False
    return True


def validate_method_data(form_data, this_method):
    if this_method.method_type == 'Date':
        if (not form_data.time_start.data or
                not form_data.time_end.data or
                form_data.setpoint_start.data == ''):
            flash(f"{gettext('Required')}: {gettext('Start date/time, end date/time, start setpoint')}", "error")
            return 1
        try:
            start_time = datetime.strptime(
                form_data.time_start.data, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(
                form_data.time_end.data, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            flash(f'{gettext("Invalid Date/Time format")}. {gettext("Required")}: {gettext("YYYY/MM/DD HH:MM:SS")}',
                  "error")
            return 1
        if end_time <= start_time:
            flash(gettext("The end time must be after the start time."), "error")
            return 1

    elif this_method.method_type == 'Daily':
        if (not form_data.daily_time_start.data or
                not form_data.daily_time_end.data or
                form_data.setpoint_start.data == ''):
            flash(f"{gettext('Required')}: {gettext('Start time, end time, start setpoint')}", "error")
            return 1
        try:
            start_time = datetime.strptime(
                form_data.daily_time_start.data, '%H:%M:%S')
            end_time = datetime.strptime(
                form_data.daily_time_end.data, '%H:%M:%S')
        except ValueError:
            flash(f'{gettext("Invalid Date/Time format")}. {gettext("Required")}: {gettext("HH:MM:SS")}', "error")
            return 1
        if end_time <= start_time:
            flash(gettext("The end time must be after the start time."), "error")
            return 1

    elif this_method.method_type == 'Duration':
        try:
            if form_data.restart.data:
                return 0
        except Exception:
            pass
        try:
            if form_data.duration_end.data:
                return 0
        except Exception:
            pass
        if not form_data.duration.data:
            flash(f"{gettext('Required')}: {gettext('Duration')}", "error")
            return 1
        elif not is_positive_integer(form_data.duration.data):
            flash(f"{gettext('Required')}: {gettext('Duration must be positive')}", "error")
            return 1
        if form_data.setpoint_start.data is None:
            flash(f"{gettext('Required')}: {gettext('Start Setpoint')}", "error")
            return 1


def method_create(form_create_method):
    """Create new method table entry (all data stored in method_data table)"""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['method']['title'])
    error = []

    dep_unmet, _, _ = return_dependencies(form_create_method.method_type.data)
    if dep_unmet:
        list_unmet_deps = []
        for each_dep in dep_unmet:
            list_unmet_deps.append(each_dep[3])
        error.append(
            "The {dev} device you're trying to add has unmet dependencies: "
            "{dep}".format(dev=form_create_method.method_type.data,
                           dep=', '.join(list_unmet_deps)))

    try:
        # Create method
        new_method = Method()
        new_method.name = form_create_method.name.data
        new_method.method_type = form_create_method.method_type.data

        if not error:
            db.session.add(new_method)
            db.session.commit()

            # Add new method line id to method display order
            method_order = DisplayOrder.query.first()
            display_order = csv_to_list_of_str(method_order.method)
            method_order.method = add_display_order(display_order, new_method.unique_id)
            db.session.commit()

        # Add new method data line id to method_data display order
        if new_method.method_type in ['DailyBezier', 'DailySine']:
            # For tables that require only one entry to configure,
            # create that single entry now with default values
            new_method_data = MethodData()
            new_method_data.method_id = new_method.unique_id

            if new_method.method_type == 'DailySine':
                new_method_data.amplitude = 1.0
                new_method_data.frequency = 1.0
                new_method_data.shift_angle = 0
                new_method_data.shift_y = 1.0
            elif new_method.method_type == 'DailyBezier':
                new_method_data = MethodData()
                new_method_data.method_id = new_method.unique_id
                new_method_data.shift_angle = 0.0
                new_method_data.x0 = 20.0
                new_method_data.y0 = 20.0
                new_method_data.x1 = 10.0
                new_method_data.y1 = 13.5
                new_method_data.x2 = 22.5
                new_method_data.y2 = 30.0
                new_method_data.x3 = 0.0
                new_method_data.y3 = 20.0

            if not error:
                db.session.add(new_method_data)
                db.session.commit()

                display_order = csv_to_list_of_str(new_method.method_order)
                method = Method.query.filter(
                    Method.unique_id == new_method.unique_id).first()
                method.method_order = add_display_order(
                    display_order, new_method_data.unique_id)
                db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_method.method_list'))

    if dep_unmet:
        return 1


def method_add(form_add_method):
    """Add line to method_data table"""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['method']['title'])
    error = []

    start_time = None
    end_time = None

    method = Method.query.filter(
        Method.unique_id == form_add_method.method_id.data).first()
    display_order = csv_to_list_of_str(method.method_order)

    try:
        if validate_method_data(form_add_method, method):
            return 1

        if method.method_type == 'DailySine':
            add_method_data = MethodData.query.filter(
                MethodData.method_id == form_add_method.method_id.data).first()
            add_method_data.amplitude = form_add_method.amplitude.data
            add_method_data.frequency = form_add_method.frequency.data
            add_method_data.shift_angle = form_add_method.shift_angle.data
            add_method_data.shift_y = form_add_method.shiftY.data
            db.session.commit()
            return 0

        elif method.method_type == 'DailyBezier':
            if not 0 <= form_add_method.shift_angle.data <= 360:
                flash(gettext("Error: Angle Shift is out of range. It must be "
                              "<= 0 and <= 360."), "error")
                return 1
            if form_add_method.x0.data <= form_add_method.x3.data:
                flash(gettext("Error: X0 must be greater than X3."), "error")
                return 1
            add_method_data = MethodData.query.filter(
                MethodData.method_id == form_add_method.method_id.data).first()
            add_method_data.shift_angle = form_add_method.shift_angle.data
            add_method_data.x0 = form_add_method.x0.data
            add_method_data.y0 = form_add_method.y0.data
            add_method_data.x1 = form_add_method.x1.data
            add_method_data.y1 = form_add_method.y1.data
            add_method_data.x2 = form_add_method.x2.data
            add_method_data.y2 = form_add_method.y2.data
            add_method_data.x3 = form_add_method.x3.data
            add_method_data.y3 = form_add_method.y3.data
            db.session.commit()
            return 0

        if method.method_type == 'Date':
            start_time = datetime.strptime(
                form_add_method.time_start.data,
                '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(
                form_add_method.time_end.data,
                '%Y-%m-%d %H:%M:%S')
        elif method.method_type == 'Daily':
            start_time = datetime.strptime(
                form_add_method.daily_time_start.data,
                '%H:%M:%S')
            end_time = datetime.strptime(
                form_add_method.daily_time_end.data,
                '%H:%M:%S')

        if method.method_type in ['Date', 'Daily']:
            # Check if the start time comes after the last entry's end time
            display_order = csv_to_list_of_str(method.method_order)
            if display_order:
                last_method = MethodData.query.filter(
                    MethodData.unique_id == display_order[-1]).first()
            else:
                last_method = None

            if last_method is not None:
                if method.method_type == 'Date':
                    last_method_end_time = datetime.strptime(
                        last_method.time_end,
                        '%Y-%m-%d %H:%M:%S')
                elif method.method_type == 'Daily':
                    last_method_end_time = datetime.strptime(
                        last_method.time_end,
                        '%H:%M:%S')
                else:
                    last_method_end_time = None

                if (start_time and last_method_end_time and
                        start_time < last_method_end_time):
                    flash(gettext("The new entry start time (%(st)s) "
                                  "cannot overlap the last entry's end "
                                  "time (%(et)s). Note: They may be the "
                                  "same time.",
                                  st=last_method_end_time,
                                  et=start_time),
                          "error")
                    return 1

        add_method_data = MethodData()
        add_method_data.method_id = form_add_method.method_id.data

        if method.method_type == 'Date':
            add_method_data.time_start = start_time.strftime(
                '%Y-%m-%d %H:%M:%S')
            add_method_data.time_end = end_time.strftime(
                '%Y-%m-%d %H:%M:%S')

        elif method.method_type == 'Daily':
            add_method_data.time_start = start_time.strftime('%H:%M:%S')
            add_method_data.time_end = end_time.strftime('%H:%M:%S')

        elif method.method_type == 'Duration':
            if form_add_method.restart.data:
                add_method_data.duration_sec = 0
                add_method_data.duration_end = form_add_method.duration_end.data
            else:
                add_method_data.duration_sec = form_add_method.duration.data

        elif method.method_type == 'Cascade':
            add_method_data.linked_method_id = form_add_method.linked_method_id.data

        add_method_data.setpoint_start = form_add_method.setpoint_start.data
        add_method_data.setpoint_end = form_add_method.setpoint_end.data


        db.session.add(add_method_data)
        db.session.commit()

        # Add line to method data list
        method.method_order = add_display_order(
            display_order, add_method_data.unique_id)
        db.session.commit()

        if method.method_type == 'Date':
            flash(gettext("Added duration to method from %(st)s to "
                          "%(end)s", st=start_time, end=end_time),
                  "success")
        elif method.method_type == 'Daily':
            flash(gettext("Added duration to method from %(st)s to "
                          "%(end)s",
                          st=start_time.strftime('%H:%M:%S'),
                          end=end_time.strftime('%H:%M:%S')),
                  "success")
        elif method.method_type == 'Duration':
            if form_add_method.restart.data:
                flash(gettext("Added method restart"), "success")
            else:
                flash(gettext("Added duration to method for %(sec)s seconds",
                              sec=form_add_method.duration.data), "success")

    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_method.method_list'))


def method_mod(form_mod_method):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['method']['title'])
    error = []

    method = Method.query.filter(
        Method.unique_id == form_mod_method.method_id.data).first()
    method_data = MethodData.query.filter(
        MethodData.unique_id == form_mod_method.method_data_id.data).first()
    display_order = csv_to_list_of_str(method.method_order)

    try:
        if form_mod_method.delete.data:
            delete_entry_with_id(
                MethodData, form_mod_method.method_data_id.data)
            method_order = Method.query.filter(
                Method.unique_id == method.unique_id).first()
            display_order = csv_to_list_of_str(method_order.method_order)
            display_order.remove(method_data.unique_id)
            method_order.method_order = list_to_csv(display_order)
            db.session.commit()
            return 0

        if form_mod_method.rename.data:
            method.name = form_mod_method.name.data
            db.session.commit()
            return 0

        # Ensure data is valid
        if validate_method_data(form_mod_method, method):
            return 1

        if method.method_type == 'Date':
            start_time = datetime.strptime(form_mod_method.time_start.data, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(form_mod_method.time_end.data, '%Y-%m-%d %H:%M:%S')

            # Ensure the start time comes after the previous entry's end time
            # and the end time comes before the next entry's start time
            # method_id_set is the id given to all method entries, 'method_id', not 'id'
            previous_method = None
            next_method = None
            for index, each_order in enumerate(display_order):
                if each_order == method_data.unique_id:
                    if len(display_order) > 1 and index > 0:
                        previous_method = MethodData.query.filter(
                            MethodData.unique_id == display_order[index-1]).first()
                    if len(display_order) > index+1:
                        next_method = MethodData.query.filter(
                            MethodData.unique_id == display_order[index+1]).first()

            if previous_method is not None and previous_method.time_end is not None:
                previous_end_time = datetime.strptime(
                    previous_method.time_end, '%Y-%m-%d %H:%M:%S')
                if previous_end_time is not None and start_time < previous_end_time:
                    error.append(
                        gettext("The entry start time (%(st)s) cannot "
                                "overlap the previous entry's end time "
                                "(%(et)s)",
                                st=start_time, et=previous_end_time))

            if next_method is not None and next_method.time_start is not None:
                next_start_time = datetime.strptime(
                    next_method.time_start, '%Y-%m-%d %H:%M:%S')
                if next_start_time is not None and end_time > next_start_time:
                    error.append(
                        gettext("The entry end time (%(et)s) cannot "
                                "overlap the next entry's start time "
                                "(%(st)s)",
                                et=end_time, st=next_start_time))

            method_data.time_start = start_time.strftime('%Y-%m-%d %H:%M:%S')
            method_data.time_end = end_time.strftime('%Y-%m-%d %H:%M:%S')

        elif method.method_type == 'Duration':
            if method_data.duration_sec == 0:
                method_data.duration_end = form_mod_method.duration_end.data
            else:
                method_data.duration_sec = form_mod_method.duration.data

        elif method.method_type == 'Daily':
            method_data.time_start = form_mod_method.daily_time_start.data
            method_data.time_end = form_mod_method.daily_time_end.data

        method_data.setpoint_start = form_mod_method.setpoint_start.data
        method_data.setpoint_end = form_mod_method.setpoint_end.data

        if not error:
            db.session.commit()

    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_method.method_list'))


def method_del(method_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['method']['title'])
    error = []

    try:
        delete_entry_with_id(Method,
                             method_id)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_method.method_list'))
