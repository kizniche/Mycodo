# -*- coding: utf-8 -*-
import logging
import bcrypt
import functools
import gzip
import os
import re
import requests
import sqlalchemy
import time
import flask_login
from collections import OrderedDict
from datetime import datetime
from cStringIO import StringIO as IO

from flask import after_this_request
from flask import flash
from flask import redirect
from flask import request
from flask import url_for

from sqlalchemy import and_
from mycodo.mycodo_flask.extensions import db
from flask_babel import gettext
from RPi import GPIO

from mycodo.mycodo_client import DaemonControl

from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Graph
from mycodo.databases.models import LCD
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.databases.models import Misc
from mycodo.databases.models import PID
from mycodo.databases.models import Relay
from mycodo.databases.models import Remote
from mycodo.databases.models import Role
from mycodo.databases.models import SMTP
from mycodo.databases.models import Sensor
from mycodo.databases.models import Timer
from mycodo.databases.models import User
from mycodo.utils.utils import test_username
from mycodo.utils.utils import test_password
from mycodo.utils.send_data import send_email
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import list_to_csv

from mycodo.config import CAMERAS
from mycodo.config import DEVICES_DEFAULT_LOCATION
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import MEASUREMENT_UNITS
from mycodo.config import MEASUREMENTS

logger = logging.getLogger(__name__)


#
# Method Development
#

def is_positive_integer(number_string):
    try:
        if int(number_string) < 0:
            flash(gettext(u"Duration must be a positive integer"), "error")
            return False
    except ValueError:
        flash(gettext(u"Duration must be a valid integer"), "error")
        return False
    return True


def validate_method_data(form_data, this_method):
    if form_data.method_select.data == 'setpoint':
        if this_method.method_type == 'Date':
            if (not form_data.time_start.data or
                    not form_data.time_end.data or
                    form_data.setpoint_start.data == ''):
                flash(gettext(u"Required: Start date/time, end date/time, "
                              u"start setpoint"), "error")
                return 1
            try:
                start_time = datetime.strptime(form_data.time_start.data,
                                               '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(form_data.time_end.data,
                                             '%Y-%m-%d %H:%M:%S')
            except ValueError:
                flash(gettext(u"Invalid Date/Time format. Correct format: "
                              u"DD/MM/YYYY HH:MM:SS"), "error")
                return 1
            if end_time <= start_time:
                flash(gettext(u"The end time/date must be after the start "
                              u"time/date."), "error")
                return 1

        elif this_method.method_type == 'Daily':
            if (not form_data.daily_time_start.data or
                    not form_data.daily_time_end.data or
                    form_data.setpoint_start.data == ''):
                flash(gettext(u"Required: Start time, end time, start "
                              u"setpoint"), "error")
                return 1
            try:
                start_time = datetime.strptime(form_data.daily_time_start.data,
                                               '%H:%M:%S')
                end_time = datetime.strptime(form_data.daily_time_end.data,
                                             '%H:%M:%S')
            except ValueError:
                flash(gettext(u"Invalid Date/Time format. Correct format: "
                              u"HH:MM:SS"), "error")
                return 1
            if end_time <= start_time:
                flash(gettext(u"The end time must be after the start time."),
                      "error")
                return 1

        elif this_method.method_type == 'Duration':
            try:
                if form_data.restart.data:
                    return 0
            except:
                pass
            try:
                if form_data.duration_end.data:
                    return 0
            except:
                pass
            if (not form_data.duration.data or
                    not form_data.setpoint_start.data):
                flash(gettext(u"Required: Duration, start setpoint"),
                      "error")
                return 1
            if not is_positive_integer(form_data.duration.data):
                flash(gettext(u"Required: Duration must be positive"),
                      "error")
                return 1

    elif form_data.method_select.data == 'relay':
        if this_method.method_type == 'Date':
            if (not form_data.relay_time.data or
                    not form_data.relay_id.data or
                    not form_data.relay_state.data):
                flash(gettext(u"Required: Date/Time, Relay ID, and Relay "
                              "State"), "error")
                return 1
            try:
                datetime.strptime(form_data.relay_time.data,
                                  '%Y-%m-%d %H:%M:%S')
            except ValueError:
                flash(gettext(u"Invalid Date/Time format. Correct format: "
                              u"DD-MM-YYYY HH:MM:SS"), "error")
                return 1
        elif this_method.method_type == 'Duration':
            if (not form_data.duration.data or
                    not form_data.relay_id.data or
                    not form_data.relay_state.data):
                flash(gettext(u"Required: Relay ID, Relay State, and Relay Duration"),
                      "error")
                return 1
            if not is_positive_integer(form_data.relay_duration.data):
                return 1
        elif this_method.method_type == 'Daily':
            if (not form_data.relay_daily_time.data or
                    not form_data.relay_id.data or
                    not form_data.relay_state.data):
                flash(gettext(u"Required: Time, Relay ID, and Relay State"),
                      "error")
                return 1
            try:
                datetime.strptime(form_data.relay_daily_time.data,
                                  '%H:%M:%S')
            except ValueError:
                flash(gettext(u"Invalid Date/Time format. Correct format: "
                              u"HH:MM:SS"), "error")
                return 1


def method_create(form_create_method):
    """ Create new method table entry (all data stored in method_data table) """
    action = u'{action} {controller}'.format(
        action=gettext(u"Create"),
        controller=gettext(u"Method"))
    error = []

    try:
        # Create method
        new_method = Method()
        new_method.name = form_create_method.name.data
        new_method.method_type = form_create_method.method_type.data
        db.session.add(new_method)
        db.session.commit()

        # Add new method line id to method display order
        method_order = DisplayOrder.query.first()
        display_order = csv_to_list_of_int(method_order.method)
        method_order.method = add_display_order(display_order, new_method.id)
        db.session.commit()

        # For tables that require only one entry to configure,
        # create that single entry now with default values
        if new_method.method_type == 'DailySine':
            new_method_data = MethodData()
            new_method_data.method_id = new_method.id
            new_method_data.amplitude = 1.0
            new_method_data.frequency = 1.0
            new_method_data.shift_angle = 0
            new_method_data.shift_y = 1.0
            db.session.add(new_method_data)
            db.session.commit()
        elif new_method.method_type == 'DailyBezier':
            new_method_data = MethodData()
            new_method_data.method_id = new_method.id
            new_method_data.shift_angle = 0.0
            new_method_data.x0 = 20.0
            new_method_data.y0 = 20.0
            new_method_data.x1 = 10.0
            new_method_data.y1 = 13.5
            new_method_data.x2 = 22.5
            new_method_data.y2 = 30.0
            new_method_data.x3 = 0.0
            new_method_data.y3 = 20.0
            db.session.add(new_method_data)
            db.session.commit()

        # Add new method data line id to method_data display order
        if new_method.method_type in ['DailyBezier', 'DailySine']:
            display_order = csv_to_list_of_int(new_method.method_order)
            method = Method.query.filter(Method.id == new_method.id).first()
            method.method_order = add_display_order(display_order,
                                                    new_method_data.id)
            db.session.commit()

        return 0
    except Exception as except_msg:

        error.append(except_msg)
    flash_success_errors(error, action, url_for('method_routes.method_list'))


def method_add(form_add_method):
    """ Add line to method_data table """
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Method"))
    error = []

    method = Method.query.filter(Method.id == form_add_method.method_id.data).first()
    display_order = csv_to_list_of_int(method.method_order)

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
                flash(gettext(u"Error: Angle Shift is out of range. It must be "
                              u"<= 0 and <= 360."), "error")
                return 1
            if form_add_method.x0.data <= form_add_method.x3.data:
                flash(gettext(u"Error: X0 must be greater than X3."), "error")
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

        if form_add_method.method_select.data == 'setpoint':
            if method.method_type == 'Date':
                start_time = datetime.strptime(form_add_method.time_start.data,
                                               '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(form_add_method.time_end.data,
                                             '%Y-%m-%d %H:%M:%S')
            elif method.method_type == 'Daily':
                start_time = datetime.strptime(form_add_method.daily_time_start.data,
                                               '%H:%M:%S')
                end_time = datetime.strptime(form_add_method.daily_time_end.data,
                                             '%H:%M:%S')

            if method.method_type in ['Date', 'Daily']:
                # Check if the start time comes after the last entry's end time
                display_order = csv_to_list_of_int(method.method_order)
                if display_order:
                    last_method = MethodData.query.filter(MethodData.id == display_order[-1]).first()
                else:
                    last_method = None

                if last_method is not None:
                    if method.method_type == 'Date':
                        last_method_end_time = datetime.strptime(last_method.time_end,
                                                                 '%Y-%m-%d %H:%M:%S')
                    elif method.method_type == 'Daily':
                        last_method_end_time = datetime.strptime(last_method.time_end,
                                                                 '%H:%M:%S')

                    if start_time < last_method_end_time:
                        flash(gettext(u"The new entry start time (%(st)s) "
                                      u"cannot overlap the last entry's end "
                                      u"time (%(et)s). Note: They may be the "
                                      u"same time.",
                                      st=last_method_end_time,
                                      et=start_time),
                              "error")
                        return 1

        elif form_add_method.method_select.data == 'relay':
            if method.method_type == 'Date':
                start_time = datetime.strptime(form_add_method.relay_time.data,
                                               '%Y-%m-%d %H:%M:%S')
            elif method.method_type == 'Daily':
                start_time = datetime.strptime(form_add_method.relay_daily_time.data,
                                               '%H:%M:%S')

        add_method_data = MethodData()
        add_method_data.method_id = form_add_method.method_id.data

        if method.method_type == 'Date':
            if form_add_method.method_select.data == 'setpoint':
                add_method_data.time_start = start_time.strftime('%Y-%m-%d %H:%M:%S')
                add_method_data.time_end = end_time.strftime('%Y-%m-%d %H:%M:%S')
            if form_add_method.method_select.data == 'relay':
                add_method_data.time_start = form_add_method.relay_time.data
        elif method.method_type == 'Daily':
            if form_add_method.method_select.data == 'setpoint':
                add_method_data.time_start = start_time.strftime('%H:%M:%S')
                add_method_data.time_end = end_time.strftime('%H:%M:%S')
            if form_add_method.method_select.data == 'relay':
                add_method_data.time_start = form_add_method.relay_daily_time.data
        elif method.method_type == 'Duration':
            if form_add_method.restart.data:
                add_method_data.duration_sec = 0
                add_method_data.duration_end = form_add_method.duration_end.data
            else:
                add_method_data.duration_sec = form_add_method.duration.data

        if form_add_method.method_select.data == 'setpoint':
            add_method_data.setpoint_start = form_add_method.setpoint_start.data
            add_method_data.setpoint_end = form_add_method.setpoint_end.data
        elif form_add_method.method_select.data == 'relay':
            add_method_data.relay_id = form_add_method.relay_id.data
            add_method_data.relay_state = form_add_method.relay_state.data
            add_method_data.relay_duration = form_add_method.relay_duration.data

        db.session.add(add_method_data)
        db.session.commit()

        # Add line to method data list if not a relay duration
        if form_add_method.method_select.data != 'relay':
            method.method_order = add_display_order(display_order,
                                                    add_method_data.id)
            db.session.commit()

        if form_add_method.method_select.data == 'setpoint':
            if method.method_type == 'Date':
                flash(gettext(u"Added duration to method from %(st)s to "
                              u"%(end)s", st=start_time, end=end_time),
                      "success")
            elif method.method_type == 'Daily':
                flash(gettext(u"Added duration to method from %(st)s to "
                              u"%(end)s",
                              st=start_time.strftime('%H:%M:%S'),
                              end=end_time.strftime('%H:%M:%S')),
                      "success")
            elif method.method_type == 'Duration':
                if form_add_method.restart.data:
                    flash(gettext(u"Added method restart"), "success")
                else:
                    flash(gettext(u"Added duration to method for %(sec)s seconds",
                                  sec=form_add_method.duration.data), "success")
        elif form_add_method.method_select.data == 'relay':
            if method.method_type == 'Date':
                flash(gettext(u"Added relay modulation to method at start "
                              u"time: %(tm)s", tm=start_time), "success")
            elif method.method_type == 'Daily':
                flash(gettext(u"Added relay modulation to method at start "
                              u"time: %(tm)s",
                              tm=start_time.strftime('%H:%M:%S')), "success")
            elif method.method_type == 'Duration':
                flash(gettext(u"Added relay modulation to method at start "
                              u"time: %(tm)s",
                              tm=form_add_method.duration.data), "success")

    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)
    flash_success_errors(error, action, url_for('method_routes.method_list'))


def method_mod(form_mod_method):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Method"))
    error = []

    method = Method.query.filter(
        Method.id == form_mod_method.method_id.data).first()
    method_data = MethodData.query.filter(
        MethodData.id == form_mod_method.method_data_id.data).first()
    display_order = csv_to_list_of_int(method.method_order)

    try:
        if form_mod_method.Delete.data:
            delete_entry_with_id(MethodData,
                                 form_mod_method.method_data_id.data)
            if form_mod_method.method_select.data != 'relay':
                method_order = Method.query.filter(Method.id == method.id).first()
                display_order = csv_to_list_of_int(method_order.method_order)
                display_order.remove(method_data.id)
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

        if form_mod_method.method_select.data == 'setpoint':
            if method.method_type == 'Date':
                start_time = datetime.strptime(form_mod_method.time_start.data, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(form_mod_method.time_end.data, '%Y-%m-%d %H:%M:%S')

                # Ensure the start time comes after the previous entry's end time
                # and the end time comes before the next entry's start time
                # method_id_set is the id given to all method entries, 'method_id', not 'id'
                previous_method = None
                next_method = None
                for index, each_order in enumerate(display_order):
                    if each_order == method_data.id:
                        if len(display_order) > 1 and index > 0:
                            previous_method = MethodData.query.filter(
                                MethodData.id == display_order[index-1]).first()
                        if len(display_order) > index+1:
                            next_method = MethodData.query.filter(
                                MethodData.id == display_order[index+1]).first()

                if previous_method is not None and previous_method.time_end is not None:
                    previous_end_time = datetime.strptime(
                        previous_method.time_end, '%Y-%m-%d %H:%M:%S')
                    if previous_end_time is not None and start_time < previous_end_time:
                        error.append(
                            gettext(u"The entry start time (%(st)s) cannot "
                                    u"overlap the previous entry's end time "
                                    u"(%(et)s)",
                                    st=start_time, et=previous_end_time))

                if next_method is not None and next_method.time_start is not None:
                    next_start_time = datetime.strptime(
                        next_method.time_start, '%Y-%m-%d %H:%M:%S')
                    if next_start_time is not None and end_time > next_start_time:
                        error.append(
                            gettext(u"The entry end time (%(et)s) cannot "
                                    u"overlap the next entry's start time "
                                    u"(%(st)s)",
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

        elif form_mod_method.method_select.data == 'relay':
            if method.method_type == 'Date':
                method_data.time_start = form_mod_method.relay_time.data
            elif method.method_type == 'Duration':
                method_data.duration_sec = form_mod_method.duration.data
                if form_mod_method.duration_sec.data == 0:
                    method_data.duration_end = form_mod_method.duration_end.data
            if form_mod_method.relay_id.data == '':
                method_data.relay_id = None
            else:
                method_data.relay_id = form_mod_method.relay_id.data
            method_data.relay_state = form_mod_method.relay_state.data
            method_data.relay_duration = form_mod_method.relay_duration.data

        elif method.method_type == 'DailySine':
            if form_mod_method.method_select.data == 'relay':
                method_data.time_start = form_mod_method.relay_time.data
                if form_mod_method.relay_id.data == '':
                    method_data.relay_id = None
                else:
                    method_data.relay_id = form_mod_method.relay_id.data
                method_data.relay_state = form_mod_method.relay_state.data
                method_data.relay_duration = form_mod_method.relay_duration.data

        if not error:
            db.session.commit()

    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('method_routes.method_list'))


def method_del(method_id):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Method"))
    error = []

    try:
        delete_entry_with_id(Method,
                             method_id)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('method_routes.method_list'))


#
# Authenticate remote hosts
#

def check_new_credentials(address, user, passw):
    credentials = {
        'user': user,
        'passw': passw
    }
    url = 'https://{}/newremote/'.format(address)
    try:
        r = requests.get(url, params=credentials, verify=False)
        return r.json()
    except Exception as msg:
        return {
            'status': 1,
            'message': "Error connecting to host: {err}".format(err=msg)
        }


def auth_credentials(address, user, password_hash):
    credentials = {
        'user': user,
        'pw_hash': password_hash
    }
    url = 'https://{}/auth/'.format(address)
    try:
        r = requests.get(url, params=credentials, verify=False)
        return int(r.text)
    except Exception as e:
        logger.error(
            "'auth_credentials' raised an exception: {err}".format(err=e))
        return 1


def remote_host_add(form_setup, display_order):
    if not user_has_permission('edit_settings'):
        return redirect(url_for('general_routes.home'))

    if form_setup.validate():
        try:
            pw_check = check_new_credentials(form_setup.host.data,
                                             form_setup.username.data,
                                             form_setup.password.data)
            if pw_check['status']:
                flash(pw_check['message'], "error")
                return 1
            new_remote_host = Remote()
            new_remote_host.host = form_setup.host.data
            new_remote_host.username = form_setup.username.data
            new_remote_host.password_hash = pw_check['message']
            try:
                db.session.add(new_remote_host)
                db.session.commit()
                flash(gettext(u"Remote Host %(host)s with ID %(id)s (%(uuid)s)"
                              u" successfully added",
                              host=form_setup.host.data,
                              id=new_remote_host.id,
                              uuid=new_remote_host.unique_id),
                      "success")

                DisplayOrder.query.first().remote_host = add_display_order(
                    display_order, new_remote_host.id)
                db.session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg),
                      "error")
            except sqlalchemy.exc.IntegrityError as except_msg:
                flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg),
                      "error")
        except Exception as except_msg:
            flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg),
                  "error")
    else:
        flash_form_errors(form_setup)


def remote_host_del(form_setup):
    if not user_has_permission('edit_settings'):
        return redirect(url_for('general_routes.home'))

    try:
        delete_entry_with_id(Remote,
                             form_setup.remote_id.data)
        display_order = csv_to_list_of_int(DisplayOrder.query.first().remote_host)
        display_order.remove(int(form_setup.remote_id.data))
        DisplayOrder.query.first().remote_host = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        flash(gettext(u"Remote Host Error: %(msg)s", msg=except_msg), "error")


#
# Manipulate relay settings while daemon is running
#

def manipulate_relay(action, relay_id):
    """
    Add, delete, and modify relay settings while the daemon is active

    :param relay_id: relay ID in the SQL database
    :type relay_id: str
    :param action: "add", "del", or "mod"
    :type action: str
    """
    control = DaemonControl()
    return_values = control.relay_setup(action, relay_id)
    if return_values and len(return_values) > 1:
        if return_values[0]:
            flash(gettext(u"%(err)s",
                          err=u'{action} Relay: Daemon response: {msg}'.format(
                              action=action,
                              msg=return_values[1])),
                  "error")
        else:
            flash(gettext(u"%(err)s",
                          err=u'{action} Relay: Daemon response: {msg}'.format(
                              action=gettext(action),
                              msg=return_values[1])),
                  "success")
    else:
        flash(gettext(u"%(err)s",
                      err=u'{action} Relay: Could not connect to Daemon'.format(
                          action=action)),
              "error")


#
# Activate/deactivate controller
#

def controller_activate_deactivate(controller_action,
                                   controller_type,
                                   controller_id):
    """
    Activate or deactivate controller

    :param controller_action: Activate or deactivate
    :type controller_action: str
    :param controller_type: The controller type (LCD, PID, Sensor, Timer)
    :type controller_type: str
    :param controller_id: Controller with ID to activate or deactivate
    :type controller_id: str
    """
    if not user_has_permission('edit_controllers'):
        return redirect(url_for('general_routes.home'))

    activated = bool(controller_action == 'activate')

    translated_names = {
        "LCD": gettext(u"LCD"),
        "PID": gettext(u"PID"),
        "Sensor": gettext(u"Sensor"),
        "Timer": gettext(u"Timer")
    }

    mod_controller = None
    if controller_type == 'LCD':
        mod_controller = LCD.query.filter(
            LCD.id == int(controller_id)).first()
    elif controller_type == 'PID':
        mod_controller = PID.query.filter(
            PID.id == int(controller_id)).first()
    elif controller_type == 'Sensor':
        mod_controller = Sensor.query.filter(
            Sensor.id == int(controller_id)).first()
    elif controller_type == 'Timer':
        mod_controller = Timer.query.filter(
            Timer.id == int(controller_id)).first()

    if mod_controller is None:
        return redirect(url_for('general_routes.home'))

    try:
        mod_controller.is_activated = activated
        db.session.commit()

        if activated:
            flash(gettext(u"%(cont)s controller activated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
        else:
            flash(gettext(u"%(cont)s controller deactivated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
    except Exception as except_msg:
        flash(gettext(u"Error: %(err)s",
                      err=u'SQL: {msg}'.format(msg=except_msg)),
              "error")

    try:
        control = DaemonControl()
        if controller_action == 'activate':
            return_values = control.controller_activate(controller_type,
                                                        int(controller_id))
        else:
            return_values = control.controller_deactivate(controller_type,
                                                          int(controller_id))
        if return_values[0]:
            flash("{err}".format(err=return_values[1]), "error")
        else:
            flash("{err}".format(err=return_values[1]), "success")
    except Exception as except_msg:
        flash(gettext(u"Error: %(err)s",
                      err=u'Daemon: {msg}'.format(msg=except_msg)),
              "error")


#
# Choices
#

# return a dictionary of all available measurements
# Used to produce a multi-select form input for creating/modifying custom graphs
def choices_sensors(sensor):
    choices = OrderedDict()
    # populate form multi-select choices for sensors and measurements
    for each_sensor in sensor:
        if each_sensor.device == 'LinuxCommand':
            value = '{id},{meas}'.format(
                id=each_sensor.unique_id,
                meas=each_sensor.cmd_measurement)
            display = u'{dev_id} ({dev_name}) {name} ({unit})'.format(
                dev_id=each_sensor.id,
                dev_name=each_sensor.name,
                name=each_sensor.cmd_measurement,
                unit=each_sensor.cmd_measurement_units)
            choices.update({value: display})
        else:
            for each_measurement in MEASUREMENTS[each_sensor.device]:
                value = '{id},{meas}'.format(
                    id=each_sensor.unique_id,
                    meas=each_measurement)
                display = u'{dev_id} ({dev_name}) {name} ({unit})'.format(
                    dev_id=each_sensor.id,
                    dev_name=each_sensor.name,
                    name=MEASUREMENT_UNITS[each_measurement]['name'],
                    unit=MEASUREMENT_UNITS[each_measurement]['unit'])
                choices.update({value: display})
            # Display custom converted units for ADCs
            if each_sensor.device in ['ADS1x15', 'MCP342x']:
                value = '{id},{meas}'.format(
                    id=each_sensor.unique_id,
                    meas=each_sensor.adc_measure)
                display = u'{id} ({name}) {meas}'.format(
                    id=each_sensor.id,
                    name=each_sensor.name,
                    meas=each_sensor.adc_measure)
                choices.update({value: display})
    return choices


def choices_outputs(output):
    choices = OrderedDict()
    # populate form multi-select choices for output devices
    for each_output in output:
        if each_output.relay_type != 'pwm':
            value = '{id},duration_sec'.format(id=each_output.unique_id)
            display = u'{id} ({name}) Output'.format(
                id=each_output.id, name=each_output.name)
            choices.update({value: display})
        elif each_output.relay_type == 'pwm':
            value = '{id},duty_cycle'.format(id=each_output.unique_id)
            display = u'{id} ({name}) Duty Cycle'.format(
                id=each_output.id, name=each_output.name)
            choices.update({value: display})
    return choices


def choices_pids(pid):
    choices = OrderedDict()
    # populate form multi-select choices for sensors and measurements
    for each_pid in pid:
        value = '{id},setpoint'.format(id=each_pid.unique_id)
        display = u'{id} ({name}) Setpoint'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
        value = '{id},pid_output'.format(id=each_pid.unique_id)
        display = u'{id} ({name}) Output (Duration)'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
        value = '{id},duty_cycle'.format(id=each_pid.unique_id)
        display = u'{id} ({name}) Output (Duty Cycle)'.format(
            id=each_pid.id, name=each_pid.name)
        choices.update({value: display})
    return choices


# Return a dictionary of all available ids and names
# produce a multi-select form input for creating/modifying custom graphs
def choices_id_name(table):
    choices = OrderedDict()
    # populate form multi-select choices for relays
    for each_entry in table:
        value = each_entry.unique_id
        display = u'{id} ({name})'.format(id=each_entry.id,
                                          name=each_entry.name)
        choices.update({value: display})
    return choices


#
# Graph
#

def graph_add(form_add_graph, display_order):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Graph"))
    error = []
    new_graph = Graph()

    if (form_add_graph.graph_type.data == 'graph' and
            (form_add_graph.name.data and
                form_add_graph.width.data and
                form_add_graph.height.data and
                form_add_graph.xaxis_duration.data and
                form_add_graph.refresh_duration.data)):
        new_graph.graph_type = form_add_graph.graph_type.data
        new_graph.name = form_add_graph.name.data
        if form_add_graph.pid_ids.data:
            pid_ids_joined = ";".join(form_add_graph.pid_ids.data)
            new_graph.pid_ids = pid_ids_joined
        if form_add_graph.relay_ids.data:
            relay_ids_joined = ";".join(form_add_graph.relay_ids.data)
            new_graph.relay_ids = relay_ids_joined
        if form_add_graph.sensor_ids.data:
            sensor_ids_joined = ";".join(form_add_graph.sensor_ids.data)
            new_graph.sensor_ids_measurements = sensor_ids_joined
        new_graph.width = form_add_graph.width.data
        new_graph.height = form_add_graph.height.data
        new_graph.x_axis_duration = form_add_graph.xaxis_duration.data
        new_graph.refresh_duration = form_add_graph.refresh_duration.data
        new_graph.enable_navbar = form_add_graph.enable_navbar.data
        new_graph.enable_rangeselect = form_add_graph.enable_range.data
        new_graph.enable_export = form_add_graph.enable_export.data
        try:
            new_graph.save()
            flash(gettext(
                u"Graph with ID %(id)s successfully added",
                id=new_graph.id),
                "success")

            DisplayOrder.query.first().graph = add_display_order(
                display_order, new_graph.id)
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
    elif (form_add_graph.graph_type.data in ['gauge_angular', 'gauge_solid'] and
            form_add_graph.sensor_ids.data):
        if form_add_graph.graph_type.data == 'gauge_solid':
            new_graph.range_colors = '0.2,#33CCFF;0.4,#55BF3B;0.6,#DDDF0D;0.8,#DF5353'
        elif form_add_graph.graph_type.data == 'gauge_angular':
            new_graph.range_colors = '0,25,#33CCFF;25,50,#55BF3B;50,75,#DDDF0D;75,100,#DF5353'
        new_graph.graph_type = form_add_graph.graph_type.data
        new_graph.name = form_add_graph.name.data
        new_graph.width = form_add_graph.width.data
        new_graph.height = form_add_graph.height.data
        new_graph.max_measure_age = form_add_graph.max_measure_age.data
        new_graph.refresh_duration = form_add_graph.refresh_duration.data
        new_graph.y_axis_min = form_add_graph.y_axis_min.data
        new_graph.y_axis_max = form_add_graph.y_axis_max.data
        new_graph.sensor_ids_measurements = form_add_graph.sensor_ids.data[0]
        try:
            new_graph.save()
            flash(gettext(
                u"Graph with ID %(id)s successfully added",
                id=new_graph.id),
                "success")

            DisplayOrder.query.first().graph = add_display_order(
                display_order, new_graph.id)
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
    else:
        flash_form_errors(form_add_graph)
        return

    flash_success_errors(error, action, url_for('page_routes.page_graph'))


def graph_mod(form_mod_graph, request_form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Graph"))
    error = []

    mod_graph = Graph.query.filter(
        Graph.id == form_mod_graph.graph_id.data).first()
    
    def is_rgb_color(color_hex):
            return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))

    if form_mod_graph.graph_type.data == 'graph':
        # Get variable number of color inputs, turn into CSV string
        colors = {}
        short_list = []
        f = request_form
        for key in f.keys():
            if 'color_number' in key:
                for value in f.getlist(key):
                    if not is_rgb_color(value):
                        error.append("Invalid hex color value")
                    colors[key[12:]] = value
        sorted_list = [(k, colors[k]) for k in sorted(colors)]
        for each_color in sorted_list:
            short_list.append(each_color[1])
        sorted_colors_string = ",".join(short_list)
        mod_graph.custom_colors = sorted_colors_string
        
        mod_graph.use_custom_colors = form_mod_graph.use_custom_colors.data
        mod_graph.name = form_mod_graph.name.data

        if form_mod_graph.pid_ids.data:
            pid_ids_joined = ";".join(form_mod_graph.pid_ids.data)
            mod_graph.pid_ids = pid_ids_joined
        else:
            mod_graph.pid_ids = ''

        if form_mod_graph.relay_ids.data:
            relay_ids_joined = ";".join(form_mod_graph.relay_ids.data)
            mod_graph.relay_ids = relay_ids_joined
        else:
            mod_graph.relay_ids = ''

        if form_mod_graph.sensor_ids.data:
            sensor_ids_joined = ";".join(form_mod_graph.sensor_ids.data)
            mod_graph.sensor_ids_measurements = sensor_ids_joined
        else:
            mod_graph.sensor_ids_measurements = ''

        mod_graph.width = form_mod_graph.width.data
        mod_graph.height = form_mod_graph.height.data
        mod_graph.x_axis_duration = form_mod_graph.xaxis_duration.data
        mod_graph.refresh_duration = form_mod_graph.refresh_duration.data
        mod_graph.enable_navbar = form_mod_graph.enable_navbar.data
        mod_graph.enable_export = form_mod_graph.enable_export.data
        mod_graph.enable_rangeselect = form_mod_graph.enable_range.data

    elif form_mod_graph.graph_type.data in ['gauge_angular', 'gauge_solid']:
        colors_hex = {}
        f = request_form
        sorted_colors_string = ""

        if form_mod_graph.graph_type.data == 'gauge_angular':
            # Combine all color form inputs to dictionary
            for key in f.keys():
                if ('color_hex_number' in key or
                        'color_low_number' in key or
                        'color_high_number' in key):
                    if int(key[17:]) not in colors_hex:
                        colors_hex[int(key[17:])] = {}
                if 'color_hex_number' in key:
                    for value in f.getlist(key):
                        if not is_rgb_color(value):
                            error.append("Invalid hex color value")
                        colors_hex[int(key[17:])]['hex'] = value
                elif 'color_low_number' in key:
                    for value in f.getlist(key):
                        colors_hex[int(key[17:])]['low'] = value
                elif 'color_high_number' in key:
                    for value in f.getlist(key):
                        colors_hex[int(key[17:])]['high'] = value

        elif form_mod_graph.graph_type.data == 'gauge_solid':
            # Combine all color form inputs to dictionary
            for key in f.keys():
                if ('color_hex_number' in key or
                        'color_stop_number' in key):
                    if int(key[17:]) not in colors_hex:
                        colors_hex[int(key[17:])] = {}
                if 'color_hex_number' in key:
                    for value in f.getlist(key):
                        if not is_rgb_color(value):
                            error.append("Invalid hex color value")
                        colors_hex[int(key[17:])]['hex'] = value
                elif 'color_stop_number' in key:
                    for value in f.getlist(key):
                        colors_hex[int(key[17:])]['stop'] = value

        # Build string of colors and associated gauge values
        for i, _ in enumerate(colors_hex):
            try:
                if form_mod_graph.graph_type.data == 'gauge_angular':
                    sorted_colors_string += "{},{},{}".format(
                        colors_hex[i]['low'],
                        colors_hex[i]['high'],
                        colors_hex[i]['hex'])
                elif form_mod_graph.graph_type.data == 'gauge_solid':
                    try:
                        if 0 > colors_hex[i]['stop'] > 1:
                            error.append("Color stops must be between 0 and 1")
                        sorted_colors_string += "{},{}".format(
                            colors_hex[i]['stop'],
                            colors_hex[i]['hex'])
                    except Exception:
                        sorted_colors_string += "0,{}".format(
                            colors_hex[i]['hex'])
                if i < len(colors_hex) - 1:
                    sorted_colors_string += ";"
            except Exception as err_msg:
                error.append(err_msg)

        mod_graph.range_colors = sorted_colors_string
        mod_graph.graph_type = form_mod_graph.graph_type.data
        mod_graph.name = form_mod_graph.name.data
        mod_graph.width = form_mod_graph.width.data
        mod_graph.height = form_mod_graph.height.data
        mod_graph.refresh_duration = form_mod_graph.refresh_duration.data
        mod_graph.y_axis_min = form_mod_graph.y_axis_min.data
        mod_graph.y_axis_max = form_mod_graph.y_axis_max.data
        mod_graph.max_measure_age = form_mod_graph.max_measure_age.data
        if form_mod_graph.sensor_ids.data:
            sensor_ids_joined = ";".join(form_mod_graph.sensor_ids.data)
            mod_graph.sensor_ids_measurements = sensor_ids_joined
        else:
            mod_graph.sensor_ids_measurements = ''
    else:
        flash_form_errors(form_mod_graph)

    if not error:
        try:
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_graph'))


def graph_del(form_del_graph):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Graph"))
    error = []

    if form_del_graph.validate():
        try:
            delete_entry_with_id(Graph,
                                 form_del_graph.graph_id.data)
            display_order = csv_to_list_of_int(DisplayOrder.query.first().graph)
            display_order.remove(int(form_del_graph.graph_id.data))
            DisplayOrder.query.first().graph = list_to_csv(display_order)
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_graph'))
    else:
        flash_form_errors(form_del_graph)


def graph_reorder(graph_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"Graph"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     graph_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().graph = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_graph'))


#
# LCD Manipulation
#

def lcd_add(quantity):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"LCD"))
    error = []
    for _ in range(0, quantity):
        try:
            new_lcd = LCD()
            if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
                new_lcd.i2c_bus = 1
            else:
                new_lcd.i2c_bus = 0
            new_lcd.save()
            display_order = csv_to_list_of_int(DisplayOrder.query.first().lcd)
            DisplayOrder.query.first().lcd = add_display_order(
                display_order, new_lcd.id)
            db.session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_mod(form_mod_lcd):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"LCD"))
    error = []

    if form_mod_lcd.validate():
        try:
            mod_lcd = LCD.query.filter(
                LCD.id == form_mod_lcd.lcd_id.data).first()
            if mod_lcd.is_activated:
                flash(gettext(u"Deactivate LCD controller before modifying"
                              u" its settings."), "error")
                return redirect('/lcd')
            mod_lcd = LCD.query.filter(
                LCD.id == form_mod_lcd.lcd_id.data).first()
            mod_lcd.name = form_mod_lcd.name.data
            mod_lcd.location = form_mod_lcd.location.data
            mod_lcd.i2c_bus = form_mod_lcd.i2c_bus.data
            mod_lcd.multiplexer_address = form_mod_lcd.multiplexer_address.data
            mod_lcd.multiplexer_channel = form_mod_lcd.multiplexer_channel.data
            mod_lcd.period = form_mod_lcd.period.data
            mod_lcd.x_characters = int(form_mod_lcd.lcd_type.data.split("x")[0])
            mod_lcd.y_lines = int(form_mod_lcd.lcd_type.data.split("x")[1])
            if form_mod_lcd.line_1_display.data:
                mod_lcd.line_1_sensor_id = form_mod_lcd.line_1_display.data.split(",")[0]
                mod_lcd.line_1_measurement = form_mod_lcd.line_1_display.data.split(",")[1]
            else:
                mod_lcd.line_1_sensor_id = ''
                mod_lcd.line_1_measurement = ''
            if form_mod_lcd.line_2_display.data:
                mod_lcd.line_2_sensor_id = form_mod_lcd.line_2_display.data.split(",")[0]
                mod_lcd.line_2_measurement = form_mod_lcd.line_2_display.data.split(",")[1]
            else:
                mod_lcd.line_2_sensor_id = ''
                mod_lcd.line_2_measurement = ''
            if form_mod_lcd.line_3_display.data:
                mod_lcd.line_3_sensor_id = form_mod_lcd.line_3_display.data.split(",")[0]
                mod_lcd.line_3_measurement = form_mod_lcd.line_3_display.data.split(",")[1]
            else:
                mod_lcd.line_3_sensor_id = ''
                mod_lcd.line_3_measurement = ''
            if form_mod_lcd.line_4_display.data:
                mod_lcd.line_4_sensor_id = form_mod_lcd.line_4_display.data.split(",")[0]
                mod_lcd.line_4_measurement = form_mod_lcd.line_4_display.data.split(",")[1]
            else:
                mod_lcd.line_4_sensor_id = ''
                mod_lcd.line_4_measurement = ''
            db.session.commit()
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))
    else:
        flash_form_errors(form_mod_lcd)


def lcd_del(lcd_id):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"LCD"))
    error = []

    try:
        delete_entry_with_id(LCD,
                             lcd_id)
        display_order = csv_to_list_of_int(DisplayOrder.query.first().lcd)
        display_order.remove(int(lcd_id))
        DisplayOrder.query.first().lcd = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_reorder(lcd_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"LCD"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     lcd_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().lcd = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_activate(lcd_id):
    action = u'{action} {controller}'.format(
        action=gettext(u"Activate"),
        controller=gettext(u"LCD"))
    error = []

    try:
        # All sensors the LCD depends on must be active to activate the LCD
        lcd = LCD.query.filter(
            LCD.id == lcd_id).first()
        if lcd.y_lines == 2:
            lcd_lines = [lcd.line_1_sensor_id,
                         lcd.line_2_sensor_id]
        else:
            lcd_lines = [lcd.line_1_sensor_id,
                         lcd.line_2_sensor_id,
                         lcd.line_3_sensor_id,
                         lcd.line_4_sensor_id]
        # Filter only sensors that will be displayed
        sensor = Sensor.query.filter(
            Sensor.id.in_(lcd_lines)).all()
        # Check if any sensors are not active
        for each_sensor in sensor:
            if not each_sensor.is_activated:
                flash(gettext(
                    u"Cannot activate controller if the associated "
                    u"sensor controller is inactive"), "error")
                return redirect('/lcd')
        controller_activate_deactivate(
            'activate',
            'LCD',
            lcd_id)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_lcd'))


def lcd_deactivate(lcd_id):
    controller_activate_deactivate(
        'deactivate',
        'LCD',
        lcd_id)


def lcd_reset_flashing(lcd_id):
    control = DaemonControl()
    return_value, return_msg = control.flash_lcd(
        lcd_id, 0)
    if return_value:
        flash(gettext(u"%(msg)s", msg=return_msg), "success")
    else:
        flash(gettext(u"%(msg)s", msg=return_msg), "error")


#
# PID manipulation
#

def pid_add(form_add_pid):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"PID"))
    error = []

    if form_add_pid.validate():
        for _ in range(0, form_add_pid.numberPIDs.data):
            try:
                new_pid = PID().save()

                display_order = csv_to_list_of_int(DisplayOrder.query.first().pid)
                DisplayOrder.query.first().pid = add_display_order(
                    display_order, new_pid.id)
                db.session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_pid'))
    else:
        flash_form_errors(form_add_pid)


def pid_mod(form_mod_pid_base,
            form_mod_pid_pwm_raise, form_mod_pid_pwm_lower,
            form_mod_pid_relay_raise, form_mod_pid_relay_lower):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"PID"))
    error = []

    if not form_mod_pid_base.validate():
        flash_form_errors(form_mod_pid_base)

    sensor_unique_id = form_mod_pid_base.measurement.data.split(',')[0]
    sensor = Sensor.query.filter(
        Sensor.unique_id == sensor_unique_id).first()
    if not sensor:
        error.append(gettext(u"A valid sensor is required"))

    mod_pid = PID.query.filter(
        PID.id == form_mod_pid_base.pid_id.data).first()

    # Check if a specific setting can be modified if the PID is active
    if mod_pid.is_activated:
        error = can_set_relay(error,
                              form_mod_pid_base.pid_id.data,
                              form_mod_pid_base.raise_relay_id.data,
                              form_mod_pid_base.lower_relay_id.data)

    mod_pid.name = form_mod_pid_base.name.data
    mod_pid.measurement = form_mod_pid_base.measurement.data
    mod_pid.direction = form_mod_pid_base.direction.data
    mod_pid.period = form_mod_pid_base.period.data
    mod_pid.max_measure_age = form_mod_pid_base.max_measure_age.data
    mod_pid.setpoint = form_mod_pid_base.setpoint.data
    mod_pid.p = form_mod_pid_base.k_p.data
    mod_pid.i = form_mod_pid_base.k_i.data
    mod_pid.d = form_mod_pid_base.k_d.data
    mod_pid.integrator_min = form_mod_pid_base.integrator_max.data
    mod_pid.integrator_max = form_mod_pid_base.integrator_min.data
    if form_mod_pid_base.method_id.data:
        mod_pid.method_id = form_mod_pid_base.method_id.data
    else:
        mod_pid.method_id = None

    if form_mod_pid_base.raise_relay_id.data:
        raise_relay_type = Relay.query.filter(
            Relay.id == int(form_mod_pid_base.raise_relay_id.data)).first().relay_type
        if mod_pid.raise_relay_id == int(form_mod_pid_base.raise_relay_id.data):
            if raise_relay_type == 'pwm':
                if not form_mod_pid_pwm_raise.validate():
                    flash_form_errors(form_mod_pid_pwm_raise)
                else:
                    mod_pid.raise_min_duration = form_mod_pid_pwm_raise.raise_min_duty_cycle.data
                    mod_pid.raise_max_duration = form_mod_pid_pwm_raise.raise_max_duty_cycle.data
            else:
                if not form_mod_pid_relay_raise.validate():
                    flash_form_errors(form_mod_pid_relay_raise)
                else:
                    mod_pid.raise_min_duration = form_mod_pid_relay_raise.raise_min_duration.data
                    mod_pid.raise_max_duration = form_mod_pid_relay_raise.raise_max_duration.data
                    mod_pid.raise_min_off_duration = form_mod_pid_relay_raise.raise_min_off_duration.data
        else:
            if raise_relay_type == 'pwm':
                mod_pid.raise_min_duration = 2
                mod_pid.raise_max_duration = 98
            else:
                mod_pid.raise_min_duration = 0
                mod_pid.raise_max_duration = 0
                mod_pid.raise_min_off_duration = 0
        mod_pid.raise_relay_id = form_mod_pid_base.raise_relay_id.data
    else:
        mod_pid.raise_relay_id = None

    if form_mod_pid_base.lower_relay_id.data:
        lower_relay_type = Relay.query.filter(
            Relay.id == int(form_mod_pid_base.lower_relay_id.data)).first().relay_type
        if mod_pid.lower_relay_id == int(form_mod_pid_base.lower_relay_id.data):
            if lower_relay_type == 'pwm':
                if not form_mod_pid_pwm_lower.validate():
                    flash_form_errors(form_mod_pid_pwm_lower)
                else:
                    mod_pid.lower_min_duration = form_mod_pid_pwm_lower.lower_min_duty_cycle.data
                    mod_pid.lower_max_duration = form_mod_pid_pwm_lower.lower_max_duty_cycle.data
            else:
                if not form_mod_pid_relay_lower.validate():
                    flash_form_errors(form_mod_pid_relay_lower)
                else:
                    mod_pid.lower_min_duration = form_mod_pid_relay_lower.lower_min_duration.data
                    mod_pid.lower_max_duration = form_mod_pid_relay_lower.lower_max_duration.data
                    mod_pid.lower_min_off_duration = form_mod_pid_relay_lower.lower_min_off_duration.data
        else:
            if lower_relay_type == 'pwm':
                mod_pid.lower_min_duration = 2
                mod_pid.lower_max_duration = 98
            else:
                mod_pid.lower_min_duration = 0
                mod_pid.lower_max_duration = 0
                mod_pid.lower_min_off_duration = 0
        mod_pid.lower_relay_id = form_mod_pid_base.lower_relay_id.data
    else:
        mod_pid.lower_relay_id = None

    if (mod_pid.raise_relay_id and mod_pid.lower_relay_id and
                mod_pid.raise_relay_id == mod_pid.lower_relay_id):
        error.append(gettext(u"Raise and lower outputs cannot be the same"))

    try:
        if not error:
            db.session.commit()
            # If the controller is active or paused, refresh variables in thread
            if mod_pid.is_activated:
                control = DaemonControl()
                return_value = control.pid_mod(form_mod_pid_base.pid_id.data)
                flash(gettext(
                    u"PID Controller settings refresh response: %(resp)s",
                    resp=return_value), "success")
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_pid'))


def pid_del(pid_id):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"PID"))
    error = []

    try:
        pid = PID.query.filter(
            PID.id == pid_id).first()
        if pid.is_activated:
            pid_deactivate(pid_id)

        delete_entry_with_id(PID,
                             pid_id)
        display_order = csv_to_list_of_int(DisplayOrder.query.first().pid)
        display_order.remove(int(pid_id))
        DisplayOrder.query.first().pid = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_pid'))


def pid_reorder(pid_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"PID"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     pid_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().pid = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_pid'))


# TODO: Add more settings-checks before allowing controller to be activated
def has_required_pid_values(pid_id):
    pid = PID.query.filter(
        PID.id == pid_id).first()
    error = False
    if not pid.measurement:
        flash(gettext(u"A valid Measurement is required"), "error")
        error = True
    sensor_unique_id = pid.measurement.split(',')[0]
    sensor = Sensor.query.filter(
        Sensor.unique_id == sensor_unique_id).first()
    if not sensor:
        flash(gettext(u"A valid sensor is required"), "error")
        error = True
    if not pid.raise_relay_id and not pid.lower_relay_id:
        flash(gettext(u"A Raise Relay ID and/or a Lower Relay ID is "
                      "required"), "error")
        error = True
    if error:
        return redirect('/pid')


def pid_activate(pid_id):
    if has_required_pid_values(pid_id):
        return redirect(url_for('page_routes.page_pid'))

    action = '{action} {controller}'.format(
        action=gettext(u"Actuate"),
        controller=gettext(u"PID"))
    error = []

    # Check if associated sensor is activated
    pid = PID.query.filter(
        PID.id == pid_id).first()

    error = can_set_relay(
        error, pid_id, pid.raise_relay_id, pid.lower_relay_id)

    sensor_unique_id = pid.measurement.split(',')[0]
    sensor = Sensor.query.filter(
        Sensor.unique_id == sensor_unique_id).first()

    if not sensor.is_activated:
        error.append(gettext(
            u"Cannot activate PID controller if the associated sensor "
            u"controller is inactive"))

    if ((pid.direction == 'both' and not (pid.lower_relay_id and pid.raise_relay_id)) or
                (pid.direction == 'lower' and not pid.lower_relay_id) or
                (pid.direction == 'raise' and not pid.raise_relay_id)):
        error.append(gettext(
            u"Cannot activate PID controller if raise and/or lower relay IDs "
            u"are not selected"))

    if not error:
        # Signal the duration method can run because it's been
        # properly initiated (non-power failure)
        mod_method = Method.query.filter(
            Method.id == pid.method_id).first()
        if mod_method and mod_method.method_type == 'Duration':
            mod_method.start_time = 'Ready'
            db.session.commit()

        time.sleep(1)
        controller_activate_deactivate('activate',
                                       'PID',
                                       pid_id)

    flash_success_errors(error, action, url_for('page_routes.page_pid'))


def pid_deactivate(pid_id):
    pid = PID.query.filter(
        PID.id == pid_id).first()
    pid.is_activated = False
    db.session.commit()
    time.sleep(1)
    controller_activate_deactivate('deactivate',
                                   'PID',
                                   pid_id)


def pid_manipulate(pid_id, action):
    if action not in ['Hold', 'Pause', 'Resume']:
        flash(gettext(u"Invalid PID action: %(act)s", act=action), "error")
        return 1

    try:
        mod_pid = PID.query.filter(
            PID.id == pid_id).first()
        if action == 'Hold':
            mod_pid.is_held = True
            mod_pid.is_paused = False
        elif action == 'Pause':
            mod_pid.is_paused = True
            mod_pid.is_held = False
        elif action == 'Resume':
            mod_pid.is_activated = True
            mod_pid.is_held = False
            mod_pid.is_paused = False
        db.session.commit()

        control = DaemonControl()
        return_value = None
        if action == 'Hold':
            return_value = control.pid_hold(pid_id)
        elif action == 'Pause':
            return_value = control.pid_pause(pid_id)
        elif action == 'Resume':
            return_value = control.pid_resume(pid_id)
        if return_value:
            flash(gettext(u"Daemon response to PID controller %(act)s command: "
                          u"%(rval)s", act=action, rval=return_value), "success")
    except Exception as err:
        flash(gettext(u"PID Error: %(msg)s", msg=err), "error")


def can_set_relay(error, pid_id, raise_relay_id, lower_relay_id):
    """ Don't allow an output to be used with more than one active PID """
    pid_all = (PID.query
               .filter(PID.is_activated == True)
               .filter(PID.id != int(pid_id))
              ).all()
    for each_pid in pid_all:
        if ((raise_relay_id and
                (raise_relay_id == str(each_pid.raise_relay_id) or
                 raise_relay_id == str(each_pid.lower_relay_id))) or
            (lower_relay_id and
                (lower_relay_id == str(each_pid.lower_relay_id) or
                 lower_relay_id == str(each_pid.raise_relay_id)))):
            error.append(gettext(
                u"Cannot set output if it is already "
                u"selected by another active PID controller"))
    return error


#
# Relay manipulation
#


def relay_on_off(form_relay):
    action = u'{action} {controller}'.format(
        action=gettext(u"Actuate"),
        controller=gettext(u"Output"))
    error = []

    try:
        control = DaemonControl()
        relay = Relay.query.filter_by(id=form_relay.relay_id.data).first()
        if relay.relay_type == 'wired' and int(form_relay.relay_pin.data) == 0:
            error.append(gettext(u"Cannot modulate relay with a GPIO of 0"))
        elif form_relay.on_submit.data:
            if relay.relay_type in ['wired',
                                    'wireless_433MHz_pi_switch',
                                    'command']:
                if float(form_relay.sec_on.data) <= 0:
                    error.append(gettext(u"Value must be greater than 0"))
                else:
                    return_value = control.relay_on(form_relay.relay_id.data,
                                                    duration=float(form_relay.sec_on.data))
                    flash(gettext(u"Relay turned on for %(sec)s seconds: %(rvalue)s",
                                  sec=form_relay.sec_on.data,
                                  rvalue=return_value),
                          "success")
            if relay.relay_type == 'pwm':
                if int(form_relay.relay_pin.data) == 0:
                    error.append(gettext(u"Invalid pin"))
                if relay.pwm_hertz <= 0:
                    error.append(gettext(u"PWM Hertz must be a positive value"))
                if float(form_relay.pwm_duty_cycle_on.data) <= 0:
                    error.append(gettext(u"PWM duty cycle must be a positive value"))
                if not error:
                    return_value = control.relay_on(form_relay.relay_id.data,
                                                    duty_cycle=float(form_relay.pwm_duty_cycle_on.data))
                    flash(gettext(u"PWM set to %(dc)s%% at %(hertz)s Hz: %(rvalue)s",
                                  dc=float(form_relay.pwm_duty_cycle_on.data),
                                  hertz=relay.pwm_hertz,
                                  rvalue=return_value),
                          "success")
        elif form_relay.turn_on.data:
            return_value = control.relay_on(form_relay.relay_id.data, 0)
            flash(gettext(u"Output turned on: %(rvalue)s",
                          rvalue=return_value), "success")
        elif form_relay.turn_off.data:
            return_value = control.relay_off(form_relay.relay_id.data)
            flash(gettext(u"Output turned off: %(rvalue)s",
                          rvalue=return_value), "success")
    except ValueError as except_msg:
        error.append('{err}: {msg}'.format(
            err=gettext(u"Invalid value"),
            msg=except_msg))
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_output'))


def conditional_add(cond_type, quantity, sensor_id=None):
    error = []
    if cond_type == 'relay':
        conditional_type = gettext(u"Relay")
    elif cond_type == 'sensor':
        conditional_type = gettext(u"Sensor")
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
        cond_type = gettext(u"Sensor")
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
        cond_type = gettext(u"Sensor")
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
        cond_type = gettext(u"Sensor")
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


#
# Relay
#

def relay_add(form_add_relay):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Relay"))
    error = []

    if is_int(form_add_relay.relay_quantity.data, check_range=[1, 20]):
        for _ in range(0, form_add_relay.relay_quantity.data):
            try:
                new_relay = Relay()
                new_relay.relay_type = form_add_relay.relay_type.data
                if form_add_relay.relay_type.data == 'wired':
                    new_relay.on_at_start = False
                elif form_add_relay.relay_type.data == 'wireless_433MHz_pi_switch':
                    new_relay.protocol = 1
                    new_relay.bit_length = 25
                    new_relay.pulse_length = 189
                    new_relay.on_command = '22559'
                    new_relay.off_command = '22558'
                elif form_add_relay.relay_type.data == 'command':
                    new_relay.on_command = '/home/pi/script_on.sh'
                    new_relay.off_command = '/home/pi/script_off.sh'
                elif form_add_relay.relay_type.data == 'pwm':
                    new_relay.pwm_hertz = 22000
                    new_relay.pwm_library = 'pigpio_any'
                new_relay.save()
                display_order = csv_to_list_of_int(DisplayOrder.query.first().relay)
                DisplayOrder.query.first().relay = add_display_order(
                    display_order, new_relay.id)
                db.session.commit()
                manipulate_relay('Add', new_relay.id)
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
    else:
        error_msg = u"{error}. {accepted_values}: 1-20".format(
            error=gettext(u"Invalid quantity"),
            accepted_values=gettext(u"Acceptable values")
        )
        error.append(error_msg)
    flash_success_errors(error, action, url_for('page_routes.page_output'))


def relay_mod(form_relay):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Relay"))
    error = []

    try:
        mod_relay = Relay.query.filter(
            Relay.id == form_relay.relay_id.data).first()
        mod_relay.name = form_relay.name.data
        if mod_relay.relay_type == 'wired':
            if not is_int(form_relay.gpio.data):
                error.append("BCM Pin must be an integer")
            mod_relay.pin = form_relay.gpio.data
            mod_relay.trigger = bool(int(form_relay.trigger.data))
        elif mod_relay.relay_type == 'wireless_433MHz_pi_switch':
            if not is_int(form_relay.wiringpi_pin.data):
                error.append("WiringPi Pin must be an integer")
            if not is_int(form_relay.protocol.data):
                error.append("Protocol must be an integer")
            if not is_int(form_relay.pulse_length.data):
                error.append("Pulse Length must be an integer")
            if not is_int(form_relay.bit_length.data):
                error.append("Bit Length must be an integer")
            if not is_int(form_relay.on_command.data):
                error.append("On Command must be an integer")
            if not is_int(form_relay.off_command.data):
                error.append("Off Command must be an integer")
            mod_relay.pin = form_relay.wiringpi_pin.data
            mod_relay.protocol = form_relay.protocol.data
            mod_relay.pulse_length = form_relay.pulse_length.data
            mod_relay.bit_length = form_relay.bit_length.data
            mod_relay.on_command = form_relay.on_command.data
            mod_relay.off_command = form_relay.off_command.data
        elif mod_relay.relay_type == 'command':
            mod_relay.on_command = form_relay.on_command.data
            mod_relay.off_command = form_relay.off_command.data
        elif mod_relay.relay_type == 'pwm':
            mod_relay.pin = form_relay.gpio.data
            mod_relay.pwm_hertz = form_relay.pwm_hertz.data
            mod_relay.pwm_library = form_relay.pwm_library.data
        mod_relay.amps = form_relay.amps.data

        if form_relay.on_at_start.data == '-1' or mod_relay.relay_type == 'pwm':
            mod_relay.on_at_start = None
        else:
            mod_relay.on_at_start = bool(int(form_relay.on_at_start.data))

        if not error:
            db.session.commit()
            manipulate_relay('Modify', form_relay.relay_id.data)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_output'))


def relay_del(form_relay):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Relay"))
    error = []

    try:
        delete_entry_with_id(Relay,
                             form_relay.relay_id.data)
        display_order = csv_to_list_of_int(DisplayOrder.query.first().relay)
        display_order.remove(int(form_relay.relay_id.data))
        DisplayOrder.query.first().relay = list_to_csv(display_order)
        db.session.commit()
        manipulate_relay('Delete', form_relay.relay_id.data)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_output'))


def relay_reorder(relay_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"Relay"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     relay_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().relay = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_output'))


#
# Sensor manipulation
#

def sensor_add(form_add_sensor):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Sensor"))
    error = []

    if form_add_sensor.validate():
        for _ in range(0, form_add_sensor.numberSensors.data):
            new_sensor = Sensor()
            new_sensor.device = form_add_sensor.sensor.data
            new_sensor.name = '{name} Sensor'.format(name=form_add_sensor.sensor.data)
            if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
                new_sensor.i2c_bus = 1
                new_sensor.multiplexer_bus = 1
            else:
                new_sensor.i2c_bus = 0
                new_sensor.multiplexer_bus = 0

            # Linux command as sensor
            if form_add_sensor.sensor.data == 'LinuxCommand':
                new_sensor.cmd_command = 'shuf -i 50-70 -n 1'
                new_sensor.cmd_measurement = 'Condition'
                new_sensor.cmd_measurement_units = 'unit'

            # Process monitors
            elif form_add_sensor.sensor.data == 'MYCODO_RAM':
                new_sensor.measurements = 'disk_space'
                new_sensor.location = 'Mycodo_daemon'
            elif form_add_sensor.sensor.data == 'RPi':
                new_sensor.measurements = 'temperature'
                new_sensor.location = 'RPi'
            elif form_add_sensor.sensor.data == 'RPiCPULoad':
                new_sensor.measurements = 'cpu_load_1m,' \
                                          'cpu_load_5m,' \
                                          'cpu_load_15m'
                new_sensor.location = 'RPi'
            elif form_add_sensor.sensor.data == 'RPiFreeSpace':
                new_sensor.measurements = 'disk_space'
                new_sensor.location = '/'
            elif form_add_sensor.sensor.data == 'EDGE':
                new_sensor.measurements = 'edge'

            # Environmental Sensors
            # Temperature
            elif form_add_sensor.sensor.data in ['ATLAS_PT1000_I2C',
                                                 'ATLAS_PT1000_UART',
                                                 'DS18B20',
                                                 'TMP006']:
                new_sensor.measurements = 'temperature'
                if form_add_sensor.sensor.data == 'ATLAS_PT1000_I2C':
                    new_sensor.interface = 'I2C'
                    new_sensor.location = '0x66'
                elif form_add_sensor.sensor.data == 'ATLAS_PT1000_UART':
                    new_sensor.location = 'Tx/Rx'
                    new_sensor.interface = 'UART'
                    new_sensor.baud_rate = 9600
                    if GPIO.RPI_INFO['P1_REVISION'] == 3:
                        new_sensor.device_loc = "/dev/ttyS0"
                    else:
                        new_sensor.device_loc = "/dev/ttyAMA0"
                elif form_add_sensor.sensor.data == 'TMP006':
                    new_sensor.measurements = 'temperature_object,' \
                                              'temperature_die'
                    new_sensor.location = '0x40'

            # Temperature/Humidity
            elif form_add_sensor.sensor.data in ['AM2315', 'DHT11',
                                                 'DHT22', 'HTU21D',
                                                 'SHT1x_7x', 'SHT2x']:
                new_sensor.measurements = 'temperature,humidity,dewpoint'
                if form_add_sensor.sensor.data == 'AM2315':
                    new_sensor.location = '0x5c'
                elif form_add_sensor.sensor.data == 'HTU21D':
                    new_sensor.location = '0x40'
                elif form_add_sensor.sensor.data == 'SHT2x':
                    new_sensor.location = '0x40'

            # Chirp moisture sensor
            elif form_add_sensor.sensor.data == 'CHIRP':
                new_sensor.measurements = 'lux,moisture,temperature'
                new_sensor.location = '0x20'

            # CO2
            elif form_add_sensor.sensor.data == 'MH_Z16_I2C':
                new_sensor.measurements = 'co2'
                new_sensor.location = '0x63'
                new_sensor.interface = 'I2C'
            elif form_add_sensor.sensor.data in ['K30_UART',
                                                 'MH_Z16_UART',
                                                 'MH_Z19_UART']:
                new_sensor.measurements = 'co2'
                new_sensor.location = 'Tx/Rx'
                new_sensor.interface = 'UART'
                new_sensor.baud_rate = 9600
                if GPIO.RPI_INFO['P1_REVISION'] == 3:
                    new_sensor.device_loc = "/dev/ttyS0"
                else:
                    new_sensor.device_loc = "/dev/ttyAMA0"

            # pH
            elif form_add_sensor.sensor.data == 'ATLAS_PH_I2C':
                new_sensor.measurements = 'ph'
                new_sensor.location = '0x63'
                new_sensor.interface = 'I2C'
            elif form_add_sensor.sensor.data == 'ATLAS_PH_UART':
                new_sensor.measurements = 'ph'
                new_sensor.location = 'Tx/Rx'
                new_sensor.interface = 'UART'
                new_sensor.baud_rate = 9600
                if GPIO.RPI_INFO['P1_REVISION'] == 3:
                    new_sensor.device_loc = "/dev/ttyS0"
                else:
                    new_sensor.device_loc = "/dev/ttyAMA0"

            # Pressure
            elif form_add_sensor.sensor.data in ['BME280',
                                                 'BMP180',
                                                 'BMP280']:
                if form_add_sensor.sensor.data == 'BME280':
                    new_sensor.measurements = 'temperature,humidity,' \
                                              'dewpoint,pressure,altitude'
                    new_sensor.location = '0x76'
                elif form_add_sensor.sensor.data in ['BMP180', 'BMP280']:
                    new_sensor.measurements = 'temperature,pressure,altitude'
                    new_sensor.location = '0x77'

            # Light
            elif form_add_sensor.sensor.data in ['BH1750', 'TSL2561', 'TSL2591']:
                new_sensor.measurements = 'lux'
                if form_add_sensor.sensor.data == 'BH1750':
                    new_sensor.location = '0x23'
                    new_sensor.resolution = 0  # 0=Low, 1=High, 2=High2
                    new_sensor.sensitivity = 69
                elif form_add_sensor.sensor.data == 'TSL2561':
                    new_sensor.location = '0x39'
                elif form_add_sensor.sensor.data == 'TSL2591':
                    new_sensor.location = '0x29'

            # Analog to Digital Converters
            elif form_add_sensor.sensor.data in ['ADS1x15', 'MCP342x']:
                new_sensor.measurements = 'voltage'
                if form_add_sensor.sensor.data == 'ADS1x15':
                    new_sensor.location = '0x48'
                    new_sensor.adc_volts_min = -4.096
                    new_sensor.adc_volts_max = 4.096
                elif form_add_sensor.sensor.data == 'MCP342x':
                    new_sensor.location = '0x68'
                    new_sensor.adc_volts_min = -2.048
                    new_sensor.adc_volts_max = 2.048

            try:
                new_sensor.save()

                display_order = csv_to_list_of_int(
                    DisplayOrder.query.first().sensor)
                DisplayOrder.query.first().sensor = add_display_order(
                    display_order, new_sensor.id)
                db.session.commit()

                flash(gettext(
                    u"%(type)s Sensor with ID %(id)s (%(uuid)s) successfully added",
                    type=form_add_sensor.sensor.data,
                    id=new_sensor.id,
                    uuid=new_sensor.unique_id),
                      "success")
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_input'))
    else:
        flash_form_errors(form_add_sensor)


def sensor_mod(form_mod_sensor):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Sensor"))
    error = []

    try:
        mod_sensor = Sensor.query.filter(
            Sensor.id == form_mod_sensor.modSensor_id.data).first()

        if mod_sensor.is_activated:
            error.append(gettext(
                u"Deactivate sensor controller before modifying its "
                u"settings"))
        if (mod_sensor.device == 'AM2315' and
                form_mod_sensor.period.data < 7):
            error.append(gettext(
                u"Choose a Read Period equal to or greater than 7. The "
                u"AM2315 may become unresponsive if the period is "
                u"below 7."))
        if ((form_mod_sensor.period.data < mod_sensor.pre_relay_duration) and
                mod_sensor.pre_relay_duration):
            error.append(gettext(
                u"The Read Period cannot be less than the Pre-Relay "
                u"Duration"))
        if (form_mod_sensor.device_loc.data and
                not os.path.exists(form_mod_sensor.device_loc.data)):
            error.append(gettext(
                u"Invalid device or improper permissions to read device"))

        if not error:
            mod_sensor.name = form_mod_sensor.name.data
            mod_sensor.i2c_bus = form_mod_sensor.i2c_bus.data
            if form_mod_sensor.location.data:
                mod_sensor.location = form_mod_sensor.location.data
            if form_mod_sensor.power_relay_id.data:
                mod_sensor.power_relay_id = form_mod_sensor.power_relay_id.data
            else:
                mod_sensor.power_relay_id = None
            if form_mod_sensor.baud_rate.data:
                mod_sensor.baud_rate = form_mod_sensor.baud_rate.data
            if form_mod_sensor.device_loc.data:
                mod_sensor.device_loc = form_mod_sensor.device_loc.data
            if form_mod_sensor.pre_relay_id.data:
                mod_sensor.pre_relay_id = form_mod_sensor.pre_relay_id.data
            else:
                mod_sensor.pre_relay_id = None
            mod_sensor.pre_relay_duration = form_mod_sensor.pre_relay_duration.data
            mod_sensor.period = form_mod_sensor.period.data
            mod_sensor.resolution = form_mod_sensor.resolution.data
            mod_sensor.sensitivity = form_mod_sensor.sensitivity.data
            mod_sensor.calibrate_sensor_measure = form_mod_sensor.calibrate_sensor_measure.data
            mod_sensor.cmd_command = form_mod_sensor.cmd_command.data
            mod_sensor.cmd_measurement = form_mod_sensor.cmd_measurement.data
            mod_sensor.cmd_measurement_units = form_mod_sensor.cmd_measurement_units.data
            # Multiplexer options
            mod_sensor.multiplexer_address = form_mod_sensor.multiplexer_address.data
            mod_sensor.multiplexer_bus = form_mod_sensor.multiplexer_bus.data
            mod_sensor.multiplexer_channel = form_mod_sensor.multiplexer_channel.data
            # ADC options
            mod_sensor.adc_channel = form_mod_sensor.adc_channel.data
            mod_sensor.adc_gain = form_mod_sensor.adc_gain.data
            mod_sensor.adc_resolution = form_mod_sensor.adc_resolution.data
            mod_sensor.adc_measure = form_mod_sensor.adc_measurement.data.replace(" ", "_")
            mod_sensor.adc_measure_units = form_mod_sensor.adc_measurement_units.data
            mod_sensor.adc_volts_min = form_mod_sensor.adc_volts_min.data
            mod_sensor.adc_volts_max = form_mod_sensor.adc_volts_max.data
            mod_sensor.adc_units_min = form_mod_sensor.adc_units_min.data
            mod_sensor.adc_units_max = form_mod_sensor.adc_units_max.data
            mod_sensor.adc_inverse_unit_scale = form_mod_sensor.adc_inverse_unit_scale.data
            # Switch options
            mod_sensor.switch_edge = form_mod_sensor.switch_edge.data
            mod_sensor.switch_bouncetime = form_mod_sensor.switch_bounce_time.data
            mod_sensor.switch_reset_period = form_mod_sensor.switch_reset_period.data
            # SHT sensor options
            if form_mod_sensor.sht_clock_pin.data:
                mod_sensor.sht_clock_pin = form_mod_sensor.sht_clock_pin.data
            if form_mod_sensor.sht_voltage.data:
                mod_sensor.sht_voltage = form_mod_sensor.sht_voltage.data
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_input'))


def sensor_del(form_mod_sensor):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Sensor"))
    error = []

    try:
        sensor = Sensor.query.filter(
            Sensor.id == form_mod_sensor.modSensor_id.data).first()
        if sensor.is_activated:
            sensor_deactivate_associated_controllers(
                form_mod_sensor.modSensor_id.data)
            controller_activate_deactivate(
                'deactivate',
                'Sensor',
                form_mod_sensor.modSensor_id.data)

        conditionals = Conditional.query.filter(
            Conditional.sensor_id == form_mod_sensor.modSensor_id.data).all()
        for each_cond in conditionals:
            conditional_actions = ConditionalActions.query.filter(
                ConditionalActions.conditional_id == each_cond.id).all()
            for each_cond_action in conditional_actions:
                db.session.delete(each_cond_action)
            db.session.delete(each_cond)
        db.session.commit()

        delete_entry_with_id(Sensor,
                             form_mod_sensor.modSensor_id.data)
        try:
            display_order = csv_to_list_of_int(DisplayOrder.query.first().sensor)
            display_order.remove(int(form_mod_sensor.modSensor_id.data))
            DisplayOrder.query.first().sensor = list_to_csv(display_order)
        except Exception:  # id not in list
            pass
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_input'))


def sensor_reorder(sensor_id, display_order, direction):
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"Sensor"))
    error = []
    try:
        status, reord_list = reorder(display_order,
                                     sensor_id,
                                     direction)
        if status == 'success':
            DisplayOrder.query.first().sensor = ','.join(map(str, reord_list))
            db.session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('page_routes.page_input'))


def sensor_activate(form_mod_sensor):
    sensor = Sensor.query.filter(
        Sensor.id == form_mod_sensor.modSensor_id.data).first()
    if (sensor.device != u'LinuxCommand' and
            not sensor.location and
            sensor.device not in DEVICES_DEFAULT_LOCATION):
        flash("Cannot activate sensor without the GPIO/I2C Address/Port "
              "to communicate with it set.", "error")
        return redirect(url_for('page_routes.page_input'))
    elif (sensor.device == u'LinuxCommand' and
            sensor.cmd_command is ''):
        flash("Cannot activate sensor without a command set.", "error")
        return redirect(url_for('page_routes.page_input'))
    controller_activate_deactivate('activate',
                                   'Sensor',
                                   form_mod_sensor.modSensor_id.data)


def sensor_deactivate(form_mod_sensor):
    sensor_deactivate_associated_controllers(
        form_mod_sensor.modSensor_id.data)
    controller_activate_deactivate('deactivate',
                                   'Sensor',
                                   form_mod_sensor.modSensor_id.data)


# Deactivate any active PID or LCD controllers using this sensor
def sensor_deactivate_associated_controllers(sensor_id):
    sensor_unique_id = Sensor.query.filter(Sensor.id == sensor_id).first().unique_id
    pid = PID.query.filter(PID.is_activated == True).all()
    for each_pid in pid:
        if sensor_unique_id in each_pid.measurement:
            controller_activate_deactivate('deactivate',
                                           'PID',
                                           each_pid.id)

    lcd = LCD.query.filter(LCD.is_activated)
    for each_lcd in lcd:
        if sensor_id in [each_lcd.line_1_sensor_id,
                         each_lcd.line_2_sensor_id,
                         each_lcd.line_3_sensor_id,
                         each_lcd.line_4_sensor_id]:
            controller_activate_deactivate('deactivate',
                                           'LCD',
                                           each_lcd.id)


def check_refresh_conditional(sensor_id, cond_mod):
    sensor = (Sensor.query
              .filter(Sensor.id == sensor_id)
              .filter(Sensor.is_activated == True)
              ).first()
    if sensor:
        control = DaemonControl()
        control.refresh_sensor_conditionals(sensor_id, cond_mod)


#
# Timers
#

def timer_add(form_add_timer, timer_type, display_order):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Timer"))
    error = []

    if form_add_timer.validate():
        new_timer = Timer()
        new_timer.name = form_add_timer.name.data
        new_timer.relay_id = form_add_timer.relay_id.data
        if timer_type == 'time':
            new_timer.timer_type = 'time'
            new_timer.state = form_add_timer.state.data
            new_timer.time_start = form_add_timer.time_start.data
            new_timer.duration_on = form_add_timer.time_on_duration.data
            new_timer.duration_off = 0
        elif timer_type == 'timespan':
            new_timer.timer_type = 'timespan'
            new_timer.state = form_add_timer.state.data
            new_timer.time_start = form_add_timer.time_start_duration.data
            new_timer.time_end = form_add_timer.time_end_duration.data
        elif timer_type == 'duration':
            if (form_add_timer.duration_on.data <= 0 or
                    form_add_timer.duration_off.data <= 0):
                error.append(gettext(u"Durations must be greater than 0"))
            else:
                new_timer.timer_type = 'duration'
                new_timer.duration_on = form_add_timer.duration_on.data
                new_timer.duration_off = form_add_timer.duration_off.data

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
    else:
        flash_form_errors(form_add_timer)


def timer_mod(form_timer):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Timer"))
    error = []

    try:
        mod_timer = Timer.query.filter(
            Timer.id == form_timer.timer_id.data).first()
        if mod_timer.is_activated:
            error.append(gettext(u"Deactivate timer controller before "
                                 u"modifying its settings"))
        else:
            mod_timer.name = form_timer.name.data
            if form_timer.relay_id.data:
                mod_timer.relay_id = form_timer.relay_id.data
            else:
                mod_timer.relay_id = None
            if mod_timer.timer_type == 'time':
                mod_timer.state = form_timer.state.data
                mod_timer.time_start = form_timer.time_start.data
                mod_timer.duration_on = form_timer.time_on_duration.data
            elif mod_timer.timer_type == 'timespan':
                mod_timer.state = form_timer.state.data
                mod_timer.time_start = form_timer.time_start_duration.data
                mod_timer.time_end = form_timer.time_end_duration.data
            elif mod_timer.timer_type == 'duration':
                mod_timer.duration_on = form_timer.duration_on.data
                mod_timer.duration_off = form_timer.duration_off.data
            if not error:
                db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_del(form_timer):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Timer"))
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
    action = u'{action} {controller}'.format(
        action=gettext(u"Reorder"),
        controller=gettext(u"Timer"))
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
    controller_activate_deactivate(
        'activate', 'Timer', form_timer.timer_id.data)


def timer_deactivate(form_timer):
    controller_activate_deactivate(
        'deactivate', 'Timer', form_timer.timer_id.data)


#
# User manipulation
#

def user_roles(form):
    action = None
    if form.add_role.data:
        action = gettext(u"Add")
    elif form.save_role.data:
        action = gettext(u"Modify")
    elif form.delete_role.data:
        action = gettext(u"Delete")

    action = u'{action} {controller}'.format(
        action=action,
        controller=gettext(u"User Role"))
    error = []

    if not error:
        if form.add_role.data:
            new_role = Role()
            new_role.name = form.name.data
            new_role.view_logs = form.view_logs.data
            new_role.view_camera = form.view_camera.data
            new_role.view_stats = form.view_stats.data
            new_role.view_settings = form.view_settings.data
            new_role.edit_users = form.edit_users.data
            new_role.edit_settings = form.edit_settings.data
            new_role.edit_controllers = form.edit_controllers.data
            try:
                new_role.save()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        elif form.save_role.data:
            mod_role = Role.query.filter(Role.id == form.role_id.data).first()
            mod_role.view_logs = form.view_logs.data
            mod_role.view_camera = form.view_camera.data
            mod_role.view_stats = form.view_stats.data
            mod_role.view_settings = form.view_settings.data
            mod_role.edit_users = form.edit_users.data
            mod_role.edit_settings = form.edit_settings.data
            mod_role.edit_controllers = form.edit_controllers.data
            db.session.commit()
        elif form.delete_role.data:
            if User().query.filter(User.role == form.role_id.data).count():
                error.append(
                    "Cannot delete role if it is assigned to a user. "
                    "Change the user to another role and try again.")
            else:
                delete_entry_with_id(Role,
                                     form.role_id.data)
    flash_success_errors(error, action, url_for('settings_routes.settings_users'))


def user_add(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"User"))
    error = []

    if form.validate():
        new_user = User()
        if not test_username(form.user_name.data):
            error.append(gettext(
                u"Invalid user name. Must be between 2 and 64 characters "
                u"and only contain letters and numbers."))

        if User.query.filter_by(email=form.email.data).count():
            error.append(gettext(
                u"Another user already has that email address."))

        if not test_password(form.password_new.data):
            error.append(gettext(
                u"Invalid password. Must be between 6 and 64 characters "
                u"and only contain letters, numbers, and symbols."))

        if form.password_new.data != form.password_repeat.data:
            error.append(gettext(u"Passwords do not match. Please try again."))

        if not error:
            new_user.name = form.user_name.data
            new_user.email = form.email.data
            new_user.set_password(form.password_new.data)
            role = Role.query.filter(
                Role.name == form.addRole.data).first().id
            new_user.role = role
            new_user.theme = 'slate'
            try:
                new_user.save()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('settings_routes.settings_users'))
    else:
        flash_form_errors(form)


def user_mod(form):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"User"))
    error = []

    try:
        mod_user = User.query.filter(
            User.id == form.user_id.data).first()
        mod_user.email = form.email.data
        # Only change the password if it's entered in the form
        logout_user = False
        if form.password_new.data != '':
            if not test_password(form.password_new.data):
                error.append(gettext(u"Invalid password"))
            if form.password_new.data == form.password_repeat.data:
                mod_user.password_hash = bcrypt.hashpw(
                    form.password_new.data.encode('utf-8'),
                    bcrypt.gensalt())
                if flask_login.current_user.id == form.user_id.data:
                    logout_user = True
            else:
                error.append(gettext(u"Passwords do not match. Please try again."))

        if not error:
            role = Role.query.filter(
                Role.name == form.role.data).first().id
            mod_user.role = role
            mod_user.theme = form.theme.data
            db.session.commit()
            if logout_user:
                return 'logout'
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_users'))


def user_del(form):
    user_name = None
    try:
        if form.validate():
            user_name = User.query.filter(User.id == form.user_id.data).first().name
            delete_user(form.user_id.data)
            if form.user_id.data == flask_login.current_user.id:
                return 'logout'
        else:
            flash_form_errors(form)
    except Exception as except_msg:
        flash(gettext(u"Error: %(msg)s",
                      msg=u'{action} {user}: {err}'.format(
                          action=gettext(u"Delete"),
                          user=user_name,
                          err=except_msg)),
              "error")


#
# Settings modifications
#

def settings_general_mod(form):
    """ Modify General settings """
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"General Settings"))
    error = []

    if form.validate():
        if (form.relay_usage_report_span.data == 'monthly' and
                not 0 < form.relay_usage_report_day.data < 29):
            error.append("Day Options: Daily: 1-7 (1=Monday), Monthly: 1-28")
        elif (form.relay_usage_report_span.data == 'weekly' and
                not 0 < form.relay_usage_report_day.data < 8):
            error.append("Day Options: Daily: 1-7 (1=Monday), Monthly: 1-28")

        if not error:
            try:
                mod_misc = Misc.query.first()
                force_https = mod_misc.force_https
                mod_misc.language = form.language.data
                mod_misc.force_https = form.force_https.data
                mod_misc.hide_alert_success = form.hide_success.data
                mod_misc.hide_alert_info = form.hide_info.data
                mod_misc.hide_alert_warning = form.hide_warning.data
                mod_misc.hide_tooltips = form.hide_tooltips.data
                mod_misc.max_amps = form.max_amps.data
                mod_misc.relay_usage_volts = form.relay_stats_volts.data
                mod_misc.relay_usage_cost = form.relay_stats_cost.data
                mod_misc.relay_usage_currency = form.relay_stats_currency.data
                mod_misc.relay_usage_dayofmonth = form.relay_stats_day_month.data
                mod_misc.relay_usage_report_gen = form.relay_usage_report_gen.data
                mod_misc.relay_usage_report_span = form.relay_usage_report_span.data
                mod_misc.relay_usage_report_day = form.relay_usage_report_day.data
                mod_misc.relay_usage_report_hour = form.relay_usage_report_hour.data
                mod_misc.stats_opt_out = form.stats_opt_out.data
                db.session.commit()
                control = DaemonControl()
                control.refresh_daemon_misc_settings()

                if force_https != form.force_https.data:
                    # Force HTTPS option changed.
                    # Reload web server with new settings.
                    wsgi_file = INSTALL_DIRECTORY + '/mycodo_flask.wsgi'
                    with open(wsgi_file, 'a'):
                        os.utime(wsgi_file, None)

            except Exception as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('settings_routes.settings_general'))
    else:
        flash_form_errors(form)


def settings_alert_mod(form_mod_alert):
    """ Modify Alert settings """
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Alert Settings"))
    error = []

    try:
        if form_mod_alert.validate():
            mod_smtp = SMTP.query.one()
            if form_mod_alert.send_test.data:
                send_email(
                    mod_smtp.host, mod_smtp.ssl, mod_smtp.port,
                    mod_smtp.user, mod_smtp.passw, mod_smtp.email_from,
                    form_mod_alert.send_test_to_email.data,
                    u"This is a test email from Mycodo")
                flash(gettext(u"Test email sent to %(recip)s. Check your "
                              u"inbox to see if it was successful.",
                              recip=form_mod_alert.send_test_to_email.data),
                      "success")
                return redirect(url_for('settings_routes.settings_alerts'))
            else:
                mod_smtp.host = form_mod_alert.smtp_host.data
                mod_smtp.port = form_mod_alert.smtp_port.data
                mod_smtp.ssl = form_mod_alert.smtp_ssl.data
                mod_smtp.user = form_mod_alert.smtp_user.data
                if form_mod_alert.smtp_password.data:
                    mod_smtp.passw = form_mod_alert.smtp_password.data
                mod_smtp.email_from = form_mod_alert.smtp_from_email.data
                mod_smtp.hourly_max = form_mod_alert.smtp_hourly_max.data
                db.session.commit()
        else:
            flash_form_errors(form_mod_alert)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_alerts'))


def camera_add(form_camera):
    action = u'{action} {controller}'.format(
        action=gettext(u"Add"),
        controller=gettext(u"Camera"))
    error = []

    if form_camera.validate():
        new_camera = Camera()
        if Camera.query.filter(Camera.name == form_camera.name.data).count():
            flash("You must choose a unique name", "error")
            return redirect(url_for('settings_routes.settings_camera'))
        new_camera.name = form_camera.name.data
        new_camera.camera_type = form_camera.camera_type.data
        new_camera.library = CAMERAS[form_camera.camera_type.data]
        if not error:
            try:
                new_camera.save()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError  as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('settings_routes.settings_camera'))
    else:
        flash_form_errors(form_camera)


def camera_mod(form_camera):
    action = u'{action} {controller}'.format(
        action=gettext(u"Modify"),
        controller=gettext(u"Camera"))
    error = []

    try:
        if (Camera.query
                    .filter(Camera.id != form_camera.camera_id.data)
                    .filter(Camera.name == form_camera.name.data).count()):
            flash("You must choose a unique name", "error")
            return redirect(url_for('settings_routes.settings_camera'))
        if 0 > form_camera.rotation.data > 360:
            flash("Rotation must be between 0 and 360 degrees", "error")
            return redirect(url_for('settings_routes.settings_camera'))

        mod_camera = Camera.query.filter(
            Camera.id == form_camera.camera_id.data).first()
        mod_camera.name = form_camera.name.data
        mod_camera.camera_type = form_camera.camera_type.data
        mod_camera.library = form_camera.library.data
        mod_camera.opencv_device = form_camera.opencv_device.data
        mod_camera.hflip = form_camera.hflip.data
        mod_camera.vflip = form_camera.vflip.data
        mod_camera.rotation = form_camera.rotation.data
        mod_camera.height = form_camera.height.data
        mod_camera.width = form_camera.width.data
        mod_camera.brightness = form_camera.brightness.data
        mod_camera.contrast = form_camera.contrast.data
        mod_camera.exposure = form_camera.exposure.data
        mod_camera.gain = form_camera.gain.data
        mod_camera.hue = form_camera.hue.data
        mod_camera.saturation = form_camera.saturation.data
        mod_camera.white_balance = form_camera.white_balance.data
        if form_camera.relay_id.data:
            mod_camera.relay_id = form_camera.relay_id.data
        else:
            mod_camera.relay_id = None
        mod_camera.cmd_pre_camera = form_camera.cmd_pre_camera.data
        mod_camera.cmd_post_camera = form_camera.cmd_post_camera.data
        db.session.commit()
        control = DaemonControl()
        control.refresh_daemon_camera_settings()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_camera'))


def camera_del(form_camera):
    action = u'{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Camera"))
    error = []

    camera = db_retrieve_table(
        Camera, first=True, device_id=form_camera.camera_id.data)
    if camera.timelapse_started:
        error.append("Cannot delete camera if a time-lapse is currently "
                     "using it. Stop the time-lapse and try again.")

    if not error:
        try:
            delete_entry_with_id(
                Camera, int(form_camera.camera_id.data))
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_camera'))


#
# Miscellaneous
#

def user_has_permission(permission):
    user = User.query.filter(User.name == flask_login.current_user.name).first()
    if ((permission == 'edit_settings' and user.roles.edit_settings) or
        (permission == 'edit_controllers' and user.roles.edit_controllers) or
        (permission == 'edit_users' and user.roles.edit_users) or
        (permission == 'view_settings' and user.roles.view_settings) or
        (permission == 'view_camera' and user.roles.view_camera) or
        (permission == 'view_stats' and user.roles.view_stats) or
        (permission == 'view_logs' and user.roles.view_logs)):
        return True
    flash("You don't have permission to do that", "error")
    return False


def db_retrieve_table(table, first=False, device_id=''):
    """ Return table data from database SQL query """
    if first:
        return_table = table.query.first()
    elif device_id:
        return_table = table.query.filter(
            table.id == device_id).first()
    else:
        return_table = table.query.all()
    return return_table


def delete_user(user_id):
    """ Delete user from SQL database """
    try:
        user = User.query.filter(
            User.id == user_id).first()
        user_name = user.name
        user.delete()
        flash(gettext(u"%(msg)s",
                      msg=u'{action} {user}'.format(
                          action=gettext(u"Delete"),
                          user=user_name)),
              "success")
        return 1
    except sqlalchemy.orm.exc.NoResultFound:
        flash(gettext(u"%(err)s",
                      err=gettext(u"User not found")),
              "error")
        return 0


def delete_entry_with_id(table, entry_id):
    """ Delete SQL database entry with specific id """
    try:
        entries = table.query.filter(
            table.id == entry_id).first()
        db.session.delete(entries)
        db.session.commit()
        flash(gettext(u"%(msg)s",
                      msg=u'{action} {id}'.format(
                          action=gettext(u"Delete"),
                          id=entry_id)),
              "success")
        return 1
    except sqlalchemy.orm.exc.NoResultFound:
        flash(gettext(u"%(err)s",
                      err=gettext(u"Entry with ID %(id)s not found",
                                  id=entry_id)),
              "error")
        flash(gettext(u"%(msg)s",
                      msg=u'{action} {id}: {err}'.format(
                          action=gettext(u"Delete"),
                          id=entry_id,
                          err=gettext(u"Entry with ID %(id)s not found",
                                      id=entry_id))),
              "success")
        return 0


def flash_form_errors(form):
    """ Flashes form errors for easier display """
    for field, errors in form.errors.items():
        for error in errors:
            flash(gettext(u"Error in the %(field)s field - %(err)s",
                          field=getattr(form, field).label.text,
                          err=error),
                  "error")


def flash_success_errors(error, action, redirect_url):
    if error:
        for each_error in error:
            flash(gettext(u"%(msg)s",
                          msg=u'{action}: {err}'.format(
                              action=action,
                              err=each_error)),
                  "error")
        return redirect(redirect_url)
    else:
        flash(gettext(u"%(msg)s",
                      msg=action),
              "success")


def gzipped(f):
    """
    Allows gzipping the response of any view.
    Just add '@gzipped' after the '@app'.
    Used mainly for sending large amounts of data for graphs.
    """
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)

            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func


def add_display_order(display_order, device_id):
    """ Add integer ID to list of string IDs """
    if display_order:
        display_order.append(device_id)
        display_order = [str(i) for i in display_order]
        return ','.join(display_order)
    return str(device_id)


def reorder(display_order, device_id, direction):
    if direction == 'up':
        status, reord_list = reorder_list(
            display_order,
            device_id,
            'up')
    elif direction == 'down':
        status, reord_list = reorder_list(
            display_order,
            device_id,
            'down')
    else:
        status = "Fail"
        reord_list = "unrecognized command"
    return status, reord_list


def reorder_list(modified_list, item, direction):
    """ Reorder entry in a comma-separated list either up or down """
    from_position = modified_list.index(item)
    if direction == "up":
        if from_position == 0:
            return 'error', gettext(u'Cannot move above the first item in the list')
        to_position = from_position - 1
    elif direction == 'down':
        if from_position == len(modified_list) - 1:
            return 'error', gettext(u'Cannot move below the last item in the list')
        to_position = from_position + 1
    else:
        return 'error', []
    modified_list.insert(to_position, modified_list.pop(from_position))
    return 'success', modified_list


def test_sql():
    try:
        num_entries = 1000000
        factor_info = 25000
        PID.query.delete()
        db.session.commit()
        logger.error("Starting SQL uuid generation test: "
                     "{n} entries...".format(n=num_entries))
        before_count = PID.query.count()
        run_times = []
        a = datetime.now()
        for x in range(1, num_entries + 1):
            db.session.add(PID())
            if x % factor_info == 0:
                db.session.commit()
                after_count = PID.query.count()
                b = datetime.now()
                run_times.append(float((b - a).total_seconds()))
                logger.error("Run Time: {time:.2f} sec, "
                             "New entries: {new}, "
                             "Total entries: {tot}".format(
                                time=run_times[-1],
                                new=after_count - before_count,
                                tot=PID.query.count()))
                before_count = PID.query.count()
                a = datetime.now()
        avg_run_time = sum(run_times) / float(len(run_times))
        logger.error("Finished. Total: {tot} entries. "
                     "Averages: {avg:.2f} sec, "
                     "{epm:.2f} entries/min".format(
                        tot=PID.query.count(),
                        avg=avg_run_time,
                        epm=(factor_info / avg_run_time) * 60.0))
    except Exception as msg:
        logger.error("Error creating entries: {err}".format(err=msg))
