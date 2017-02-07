#!/usr/bin/python
# -*- coding: utf-8 -*-
#
import logging
import bcrypt
import functools
import gzip
import os
import random
import re
import requests
import sqlalchemy
import string
import time
from collections import OrderedDict
from datetime import datetime
from cStringIO import StringIO as IO
from flask import (
    after_this_request,
    current_app,
    flash,
    redirect,
    request,
    session,
    url_for
)
from flask_babel import gettext
from RPi import GPIO

# Classes
from databases.mycodo_db.models import (
    CameraStill,
    DisplayOrder,
    Graph,
    LCD,
    Method,
    Misc,
    PID,
    Relay,
    RelayConditional,
    Remote,
    SMTP,
    Sensor,
    SensorConditional,
    Timer
)
from mycodo_client import DaemonControl

# Functions
from databases.users_db.models import Users
from databases.utils import session_scope
from scripts.utils import (
    test_username,
    test_password
)
from utils.send_data import send_email

# Config
from config import INSTALL_DIRECTORY

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
    if form_data.method_select.data == 'setpoint':
        if this_method.method_type == 'Date':
            if (not form_data.startTime.data or
                    not form_data.endTime.data or
                    form_data.startSetpoint.data == ''):
                flash(gettext("Required: Start date/time, end date/time, "
                              "start setpoint"), "error")
                return 1
            try:
                start_time = datetime.strptime(form_data.startTime.data,
                                               '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(form_data.endTime.data,
                                             '%Y-%m-%d %H:%M:%S')
            except ValueError:
                flash(gettext("Invalid Date/Time format. Correct format: "
                              "DD/MM/YYYY HH:MM:SS"), "error")
                return 1
            if end_time <= start_time:
                flash(gettext("The end time/date must be after the start "
                              "time/date."), "error")
                return 1

        elif this_method.method_type == 'Daily':
            if (not form_data.startDailyTime.data or
                    not form_data.endDailyTime.data or
                    form_data.startSetpoint.data == ''):
                flash(gettext("Required: Start time, end time, start "
                              "setpoint"), "error")
                return 1
            try:
                start_time = datetime.strptime(form_data.startDailyTime.data,
                                               '%H:%M:%S')
                end_time = datetime.strptime(form_data.endDailyTime.data,
                                             '%H:%M:%S')
            except ValueError:
                flash(gettext("Invalid Date/Time format. Correct format: "
                              "HH:MM:SS"), "error")
                return 1
            if end_time <= start_time:
                flash(gettext("The end time must be after the start time."),
                      "error")
                return 1

        elif this_method.method_type == 'Duration':
            if (not form_data.DurationSec.data or
                    form_data.startSetpoint.data == ''):
                flash(gettext("Required: Duration, start setpoint"),
                      "error")
                return 1
            if not is_positive_integer(form_data.DurationSec.data):
                return 1

    elif form_data.method_select.data == 'relay':
        if this_method.method_type == 'Date':
            if (not form_data.relayTime.data or
                    not form_data.relayID.data or
                    not form_data.relayState.data):
                flash(gettext("Required: Date/Time, Relay ID, and Relay "
                              "State"), "error")
                return 1
            try:
                datetime.strptime(form_data.relayTime.data,
                                  '%Y-%m-%d %H:%M:%S')
            except ValueError:
                flash(gettext("Invalid Date/Time format. Correct format: "
                              "DD-MM-YYYY HH:MM:SS"), "error")
                return 1
        elif this_method.method_type == 'Duration':
            if (not form_data.DurationSec.data or
                    not form_data.relayID.data or
                    not form_data.relayState.data):
                flash(gettext("Required: Duration, Relay ID, and Relay State"),
                      "error")
                return 1
            if not is_positive_integer(form_data.DurationSec.data):
                return 1
        elif this_method.method_type == 'Daily':
            if (not form_data.relayDailyTime.data or
                    not form_data.relayID.data or
                    not form_data.relayState.data):
                flash(gettext("Required: Time, Relay ID, and Relay State"),
                      "error")
                return 1
            try:
                datetime.strptime(form_data.relayDailyTime.data,
                                  '%H:%M:%S')
            except ValueError:
                flash(gettext("Invalid Date/Time format. Correct format: "
                              "HH:MM:SS"), "error")
                return 1


def method_create(form_create_method, method_id):
    action = '{action} {controller}'.format(
        action=gettext("Create"),
        controller=gettext("Method"))
    error = []

    try:
        new_method = Method()
        random_id = ''.join([random.choice(
            string.ascii_letters + string.digits) for _ in xrange(8)])
        new_method.id = random_id
        new_method.method_id = method_id
        if not form_create_method.name.data:
            new_method.name = "New Method"
        else:
            new_method.name = form_create_method.name.data
        new_method.method_type = form_create_method.method_type.data
        if form_create_method.method_type.data == 'DailySine':
            new_method.amplitude = 1.0
            new_method.frequency = 1.0
            new_method.shift_angle = 0.0
            new_method.shift_y = 1.0
        if form_create_method.method_type.data == 'DailyBezier':
            new_method.shift_angle = 0.0
            new_method.x0 = 20.0
            new_method.y0 = 20.0
            new_method.x1 = 10.0
            new_method.y1 = 13.5
            new_method.x2 = 22.5
            new_method.y2 = 30.0
            new_method.x3 = 0.0
            new_method.y3 = 20.0
        new_method.method_order = 0
        new_method.controller_type = form_create_method.controller_type.data
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            db_session.add(new_method)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('method_routes.method_list'))


def method_add(form_add_method, method):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Method"))
    error = []

    try:
        # Validate input time data
        this_method = method.filter(Method.method_id == form_add_method.method_id.data)
        this_method = this_method.filter(Method.method_order == 0).first()
        if validate_method_data(form_add_method, this_method):
            return 1

        if this_method.method_type == 'DailySine':
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_method = db_session.query(Method).filter(
                    Method.method_id == form_add_method.method_id.data).first()
                mod_method.amplitude = form_add_method.amplitude.data
                mod_method.frequency = form_add_method.frequency.data
                mod_method.shift_angle = form_add_method.shiftAngle.data
                mod_method.shift_y = form_add_method.shiftY.data
                db_session.commit()
            return 0

        if this_method.method_type == 'DailyBezier':
            if not 0 <= form_add_method.shiftAngle.data <= 360:
                flash(gettext("Error: Angle Shift is out of range. It must be "
                              "<= 0 and <= 360."), "error")
                return 1
            if form_add_method.x0.data <= form_add_method.x3.data:
                flash(gettext("Error: X0 must be greater than X3."), "error")
                return 1
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_method = db_session.query(Method).filter(
                    Method.method_id == form_add_method.method_id.data).first()
                mod_method.shift_angle = form_add_method.shiftAngle.data
                mod_method.x0 = form_add_method.x0.data
                mod_method.y0 = form_add_method.y0.data
                mod_method.x1 = form_add_method.x1.data
                mod_method.y1 = form_add_method.y1.data
                mod_method.x2 = form_add_method.x2.data
                mod_method.y2 = form_add_method.y2.data
                mod_method.x3 = form_add_method.x3.data
                mod_method.y3 = form_add_method.y3.data
                db_session.commit()
            return 0

        if form_add_method.method_select.data == 'setpoint':
            if this_method.method_type == 'Date':
                start_time = datetime.strptime(form_add_method.startTime.data,
                                               '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(form_add_method.endTime.data,
                                             '%Y-%m-%d %H:%M:%S')
            elif this_method.method_type == 'Daily':
                start_time = datetime.strptime(form_add_method.startDailyTime.data,
                                               '%H:%M:%S')
                end_time = datetime.strptime(form_add_method.endDailyTime.data,
                                             '%H:%M:%S')

            if this_method.method_type in ['Date', 'Daily']:
                # Check if the start time comes after the last entry's end time
                last_method = method.filter(Method.method_id == this_method.method_id)
                last_method = last_method.filter(Method.method_order > 0)
                last_method = last_method.filter(Method.relay_id == None)
                last_method = last_method.order_by(Method.method_order.desc()).first()
                if last_method is not None:
                    if this_method.method_type == 'Date':
                        last_method_end_time = datetime.strptime(last_method.end_time,
                                                                 '%Y-%m-%d %H:%M:%S')
                    elif this_method.method_type == 'Daily':
                        last_method_end_time = datetime.strptime(last_method.end_time,
                                                                 '%H:%M:%S')

                    if start_time < last_method_end_time:
                        flash(gettext("The new entry start time (%(st)s) "
                                      "cannot overlap the last entry's end "
                                      "time (%(et)s). Note: They may be the "
                                      "same time.",
                                      st=last_method_end_time,
                                      et=start_time),
                              "error")
                        return 1

        elif form_add_method.method_select.data == 'relay':
            if this_method.method_type == 'Date':
                start_time = datetime.strptime(form_add_method.relayTime.data,
                                               '%Y-%m-%d %H:%M:%S')
            elif this_method.method_type == 'Daily':
                start_time = datetime.strptime(form_add_method.relayDailyTime.data,
                                               '%H:%M:%S')

        new_method = Method()
        random_id = ''.join([random.choice(
            string.ascii_letters + string.digits) for _ in xrange(8)])
        new_method.id = random_id
        new_method.method_id = form_add_method.method_id.data

        # Get last number in ordered list, increment for new entry
        method_last = method.order_by(Method.method_order.desc()).first()
        new_method.method_order = method_last.method_order+1

        if this_method.method_type == 'Date':
            if form_add_method.method_select.data == 'setpoint':
                new_method.start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                new_method.end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
            if form_add_method.method_select.data == 'relay':
                new_method.start_time = form_add_method.relayTime.data
        elif this_method.method_type == 'Daily':
            if form_add_method.method_select.data == 'setpoint':
                new_method.start_time = start_time.strftime('%H:%M:%S')
                new_method.end_time = end_time.strftime('%H:%M:%S')
            if form_add_method.method_select.data == 'relay':
                new_method.start_time = form_add_method.relayDailyTime.data
        elif this_method.method_type == 'Duration':
            new_method.duration_sec = form_add_method.DurationSec.data

        if form_add_method.method_select.data == 'setpoint':
            new_method.start_setpoint = form_add_method.startSetpoint.data
            new_method.end_setpoint = form_add_method.endSetpoint.data
        elif form_add_method.method_select.data == 'relay':
            new_method.relay_id = form_add_method.relayID.data
            new_method.relay_state = form_add_method.relayState.data
            new_method.relay_duration = form_add_method.relayDurationSec.data

        new_method.repeat = ''
        new_method.repeat_duration = ''
        new_method.repeat_units = ''
        new_method.total_runs = ''

        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            db_session.add(new_method)

        if form_add_method.method_select.data == 'setpoint':
            if this_method.method_type == 'Date':
                flash(gettext("Added duration to method from %(st)s to "
                              "%(end)s", st=start_time, end=end_time),
                      "success")
            elif this_method.method_type == 'Daily':
                flash(gettext("Added duration to method from %(st)s to "
                              "%(end)s",
                              st=start_time.strftime('%H:%M:%S'),
                              end=end_time.strftime('%H:%M:%S')),
                      "success")
            elif this_method.method_type == 'Duration':
                flash(gettext("Added duration to method for %(sec)s seconds",
                              sec=form_add_method.DurationSec.data), "success")
        elif form_add_method.method_select.data == 'relay':
            if this_method.method_type == 'Date':
                flash(gettext("Added relay modulation to method at start "
                              "time: %(tm)s", tm=start_time), "success")
            elif this_method.method_type == 'Daily':
                flash(gettext("Added relay modulation to method at start "
                              "time: %(tm)s",
                              tm=start_time.strftime('%H:%M:%S')), "success")
            elif this_method.method_type == 'Duration':
                flash(gettext("Added relay modulation to method at start "
                              "time: %(tm)s",
                              tm=form_add_method.DurationSec.data), "success")

    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('method_routes.method_list'))


def method_mod(form_mod_method, method):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Method"))
    error = []

    try:
        if form_mod_method.Delete.data:
            delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                                 Method,
                                 form_mod_method.method_id.data)
            return 0

        if form_mod_method.name.data:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_method = db_session.query(Method).filter(
                    Method.method_id == form_mod_method.method_id.data)
                mod_method = mod_method.filter(Method.method_order == 0).first()
                mod_method.name = form_mod_method.name.data
                db_session.commit()
                return 0

        # Ensure data data is valid
        this_method = method.filter(Method.id == form_mod_method.method_id.data).first()
        method_set = method.filter(Method.method_id == this_method.method_id)
        method_set = method_set.filter(Method.method_order == 0).first()
        if validate_method_data(form_mod_method, method_set):
            return 1

        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            mod_method = db_session.query(Method).filter(
                Method.id == form_mod_method.method_id.data).first()

            if form_mod_method.method_select.data == 'setpoint':
                if method_set.method_type == 'Date':
                    start_time = datetime.strptime(form_mod_method.startTime.data, '%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(form_mod_method.endTime.data, '%Y-%m-%d %H:%M:%S')

                    # Ensure the start time comes after the previous entry's end time
                    # and the end time comes before the next entry's start time
                    # method_id_set is the id given to all method entries, 'method_id', not 'id'

                    previous_method = method.order_by(Method.method_order.desc()).filter(
                        Method.method_order < this_method.method_order).first()
                    next_method = method.order_by(Method.method_order.asc()).filter(
                        Method.method_order > this_method.method_order).first()

                    if previous_method is not None and previous_method.end_time is not None:
                        previous_end_time = datetime.strptime(
                            previous_method.end_time, '%Y-%m-%d %H:%M:%S')
                        if previous_end_time is not None and start_time < previous_end_time:
                            error.append(
                                gettext("The entry start time (%(st)s) cannot "
                                        "overlap the previous entry's end time "
                                        "(%(et)s)",
                                        st=start_time, et=previous_end_time))

                    if next_method is not None and next_method.start_time is not None:
                        next_start_time = datetime.strptime(
                            next_method.start_time, '%Y-%m-%d %H:%M:%S')
                        if next_start_time is not None and end_time > next_start_time:
                            error.append(
                                gettext("The entry end time (%(et)s) cannot "
                                        "overlap the next entry's start time "
                                        "(%(st)s)",
                                        et=end_time, st=next_start_time))

                    mod_method.start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                    mod_method.end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

                elif method_set.method_type == 'Duration':
                    mod_method.duration_sec = form_mod_method.DurationSec.data

                elif method_set.method_type == 'Daily':
                    mod_method.start_time = form_mod_method.startDailyTime.data
                    mod_method.end_time = form_mod_method.endDailyTime.data

                mod_method.start_setpoint = form_mod_method.startSetpoint.data
                mod_method.end_setpoint = form_mod_method.endSetpoint.data

            elif form_mod_method.method_select.data == 'relay':
                if method_set.method_type == 'Date':
                    mod_method.start_time = form_mod_method.relayTime.data
                elif method_set.method_type == 'Duration':
                    mod_method.duration_sec = form_mod_method.DurationSec.data
                mod_method.relay_id = form_mod_method.relayID.data
                mod_method.relay_state = form_mod_method.relayState.data
                mod_method.relay_duration = form_mod_method.relayDurationSec.data

            elif method_set.method_type == 'DailySine':
                if form_mod_method.method_select.data == 'relay':
                    mod_method.start_time = form_mod_method.relayTime.data
                    mod_method.relay_id = form_mod_method.relayID.data
                    mod_method.relay_state = form_mod_method.relayState.data
                    mod_method.relay_duration = form_mod_method.relayDurationSec.data

            if not error:
                db_session.commit()

    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('method_routes.method_list'))


def method_del(method_id):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Method"))
    error = []

    try:
        delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                             Method,
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
    if deny_guest_user():
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
            random_id = ''.join([random.choice(
                    string.ascii_letters + string.digits) for _ in xrange(8)])
            new_remote_host.id = random_id
            new_remote_host.activated = 0
            new_remote_host.host = form_setup.host.data
            new_remote_host.username = form_setup.username.data
            new_remote_host.password_hash = pw_check['message']
            try:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    db_session.add(new_remote_host)
                flash(gettext("Remote Host %(host)s with ID %(id)s "
                              "successfully added",
                              host=form_setup.host.data, id=random_id),
                      "success")
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_remote = db_session.query(DisplayOrder).first()
                    display_order.append(random_id)
                    order_remote.remote_host = ','.join(display_order)
                    db_session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                flash(gettext("Remote Host Error: %(msg)s", msg=except_msg),
                      "error")
            except sqlalchemy.exc.IntegrityError as except_msg:
                flash(gettext("Remote Host Error: %(msg)s", msg=except_msg),
                      "error")
        except Exception as except_msg:
            flash(gettext("Remote Host Error: %(msg)s", msg=except_msg),
                  "error")
    else:
        flash_form_errors(form_setup)


def remote_host_del(form_setup, display_order):
    if deny_guest_user():
        return redirect(url_for('general_routes.home'))

    try:
        delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                             Remote,
                             form_setup.remote_id.data)
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            order_remote = db_session.query(DisplayOrder).first()
            display_order.remove(form_setup.remote_id.data)
            order_remote.remote_host = ','.join(display_order)
            db_session.commit()
    except Exception as except_msg:
        flash(gettext("Remote Host Error: %(msg)s", msg=except_msg), "error")


#
# Manipulate relay settings while daemon is running
#

def manipulate_relay(action, relay_id, setup_pin=False):
    """
    Add, delete, and modify relay settings while the daemon is active

    :param relay_id: relay ID in the SQL database
    :type relay_id: str
    :param action: add, del, or mod
    :type action: str
    :param setup_pin: Initialize new pin (if changed)
    :type setup_pin: bool
    """
    control = DaemonControl()
    return_values = control.relay_setup(action, relay_id, setup_pin)
    if return_values[0]:
        flash(gettext("Error: %(err)s",
                      err='{action} Relay: Daemon response: {msg}'.format(
                          action=action,
                          msg=return_values[1])),
              "error")
    else:
        flash(gettext("Success: %(err)s",
                      err='{action} Relay: Daemon response: {msg}'.format(
                          action=action,
                          msg=return_values[1])),
              "success")


#
# Activate/deactivate controller
#

def activate_deactivate_controller(controller_action,
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
    if deny_guest_user():
        return redirect(url_for('general_routes.home'))

    if controller_action == 'activate':
        activated = True
    else:
        activated = False

    translated_names = {
        "LCD": gettext("LCD"),
        "PID": gettext("PID"),
        "Sensor": gettext("Sensor"),
        "Timer": gettext("Timer")
    }

    try:
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            if controller_type == 'LCD':
                mod_controller = db_session.query(LCD).filter(
                    LCD.id == controller_id).first()
            elif controller_type == 'PID':
                mod_controller = db_session.query(PID).filter(
                    PID.id == controller_id).first()
            elif controller_type == 'Sensor':
                mod_controller = db_session.query(Sensor).filter(
                    Sensor.id == controller_id).first()
            elif controller_type == 'Timer':
                mod_controller = db_session.query(Timer).filter(
                    Timer.id == controller_id).first()
            mod_controller.activated = activated
            db_session.commit()
        if activated:
            flash(gettext("%(cont)s controller activated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
        else:
            flash(gettext("%(cont)s controller deactivated in SQL database",
                          cont=translated_names[controller_type]),
                  "success")
    except Exception as except_msg:
        flash(gettext("Error: %(err)s",
                      err='SQL: {msg}'.format(msg=except_msg)),
              "error")

    try:
        control = DaemonControl()
        if controller_action == 'activate':
            return_values = control.activate_controller(controller_type,
                                                        controller_id)
        else:
            return_values = control.deactivate_controller(controller_type,
                                                          controller_id)
        if return_values[0]:
            flash("{err}".format(err=return_values[1]), "error")
        else:
            flash("{err}".format(err=return_values[1]), "success")
    except Exception as except_msg:
        flash(gettext("Error: %(err)s",
                      err='Daemon: {msg}'.format(msg=except_msg)),
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
        if each_sensor.device in ['RPiCPULoad']:
            value = '{},cpu_load_1m'.format(each_sensor.id)
            display = '{} ({}) CPU Load (1m)'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
            value = '{},cpu_load_5m'.format(each_sensor.id)
            display = '{} ({}) CPU Load (5m)'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
            value = '{},cpu_load_15m'.format(each_sensor.id)
            display = '{} ({}) CPU Load (15m)'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device == 'CHIRP':
            value = '{},moisture'.format(each_sensor.id)
            display = '{} ({}) Moisture'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device in ['AM2315', 'ATLAS_PT1000', 'BME280', 'BMP',
                                  'CHIRP', 'DHT11', 'DHT22', 'DS18B20',
                                  'HTU21D', 'RPi', 'SHT1x_7x', 'SHT2x']:
            value = '{},temperature'.format(each_sensor.id)
            display = '{} ({}) Temperature'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device == 'TMP006':
            value = '{},temperature_object'.format(each_sensor.id)
            display = '{} ({}) Temperature (Object)'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
            value = '{},temperature_die'.format(each_sensor.id)
            display = '{} ({}) Temperature (Die)'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device in ['AM2315', 'BME280', 'DHT11', 'DHT22', 'HTU21D',
                                  'SHT1x_7x', 'SHT2x']:
            value = '{},humidity'.format(each_sensor.id)
            display = '{} ({}) Humidity'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
            value = '{},dewpoint'.format(each_sensor.id)
            display = '{} ({}) Dew Point'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device == 'K30':
            value = '{},co2'.format(each_sensor.id)
            display = '{} ({}) CO2'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device in ['BME280', 'BMP']:
            value = '{},pressure'.format(each_sensor.id)
            display = '{} ({}) Pressure'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
            value = '{},altitude'.format(each_sensor.id)
            display = '{} ({}) Altitude'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device == 'EDGE':
            value = '{},edge'.format(each_sensor.id)
            display = '{} ({}) Edge'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
        if each_sensor.device in ['ADS1x15', 'MCP342x']:
            value = '{},voltage'.format(each_sensor.id)
            display = '{} ({}) Volts'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
            value = '{},{}'.format(each_sensor.id, each_sensor.adc_measure)
            display = '{} ({}) {}'.format(
                each_sensor.id, each_sensor.name, each_sensor.adc_measure)
            choices.update({value: display})
        if each_sensor.device in ['CHIRP', 'TSL2561']:
            value = '{},lux'.format(each_sensor.id)
            display = '{} ({}) Lux'.format(
                each_sensor.id, each_sensor.name)
            choices.update({value: display})
    return choices


# Return a dictionary of all available ids and names
# produce a multi-select form input for creating/modifying custom graphs
def choices_id_name(table):
    choices = OrderedDict()
    # populate form multi-select choices for relays
    for each_entry in table:
        value = each_entry.id
        display = '{id} ({name})'.format(id=each_entry.id,
                                         name=each_entry.name)
        choices.update({value:display})
    return choices


#
# Graph
#

def graph_add(form_add_graph, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Graph"))
    error = []

    if (form_add_graph.name.data and form_add_graph.width.data and
            form_add_graph.height.data and form_add_graph.xAxisDuration.data and
            form_add_graph.refreshDuration.data):
        new_graph = Graph()
        random_id = ''.join([random.choice(
                string.ascii_letters + string.digits) for _ in xrange(8)])
        new_graph.id = random_id
        new_graph.colors = ''
        new_graph.colors_custom = False
        new_graph.name = form_add_graph.name.data
        pid_ids_joined = ",".join(form_add_graph.pidIDs.data)
        new_graph.pid_ids = pid_ids_joined
        relay_ids_joined = ",".join(form_add_graph.relayIDs.data)
        new_graph.relay_ids = relay_ids_joined
        sensor_ids_joined = ";".join(form_add_graph.sensorIDs.data)
        new_graph.sensor_ids = sensor_ids_joined
        new_graph.width = form_add_graph.width.data
        new_graph.height = form_add_graph.height.data
        new_graph.x_axis_duration = form_add_graph.xAxisDuration.data
        new_graph.refresh_duration = form_add_graph.refreshDuration.data
        new_graph.enable_navbar = form_add_graph.enableNavbar.data
        new_graph.enable_rangeselect = form_add_graph.enableRangeSelect.data
        new_graph.enable_export = form_add_graph.enableExport.data
        try:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                db_session.add(new_graph)
            flash(gettext(
                "Graph with ID %(id)s successfully created", id=random_id),
                "success")
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                order_graph = db_session.query(DisplayOrder).first()
                display_order.append(random_id)
                order_graph.graph = ','.join(display_order)
                db_session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_graph'))
    else:
        flash_form_errors(form_add_graph)


def graph_mod(form_mod_graph, request_form):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Graph"))
    error = []

    if form_mod_graph.validate():
        def is_rgb_color(color_hex):
            return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))

        # Get variable number of color inputs, turn into CSV string
        colors = {}
        f = request_form
        for key in f.keys():
            if 'color_number' in key:
                for value in f.getlist(key):
                    if not is_rgb_color(value):
                        flash(gettext("Invalid hex color value"), "error")
                        return redirect(url_for('page_routes.page_graph'))
                    colors[key[12:]] = value

        sorted_list = [(k, colors[k]) for k in sorted(colors)]

        short_list = []
        for each_color in sorted_list:
            short_list.append(each_color[1])
        sorted_colors_string = ",".join(short_list)

        try:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_graph = db_session.query(Graph).filter(
                    Graph.id == form_mod_graph.graph_id.data).first()
                mod_graph.colors = sorted_colors_string
                mod_graph.colors_custom = form_mod_graph.colors_custom.data
                mod_graph.name = form_mod_graph.name.data
                pid_ids_joined = ",".join(form_mod_graph.pidIDs.data)
                mod_graph.pid_ids = pid_ids_joined
                relay_ids_joined = ",".join(form_mod_graph.relayIDs.data)
                mod_graph.relay_ids = relay_ids_joined
                sensor_ids_joined = ";".join(form_mod_graph.sensorIDs.data)
                mod_graph.sensor_ids = sensor_ids_joined
                mod_graph.width = form_mod_graph.width.data
                mod_graph.height = form_mod_graph.height.data
                mod_graph.x_axis_duration = form_mod_graph.xAxisDuration.data
                mod_graph.refresh_duration = form_mod_graph.refreshDuration.data
                mod_graph.enable_navbar = form_mod_graph.enableNavbar.data
                mod_graph.enable_export = form_mod_graph.enableExport.data
                mod_graph.enable_rangeselect = form_mod_graph.enableRangeSelect.data
                db_session.commit()
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_graph'))
    else:
        flash_form_errors(form_mod_graph)


def graph_del(form_del_graph, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Graph"))
    error = []

    if form_del_graph.validate():
        try:
            delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                                 Graph,
                                 form_del_graph.graph_id.data)
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                order_graph = db_session.query(DisplayOrder).first()
                display_order.remove(form_del_graph.graph_id.data)
                order_graph.graph = ','.join(display_order)
                db_session.commit()
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_graph'))
    else:
        flash_form_errors(form_del_graph)


def graph_reorder(form_order_graph, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Graph"))
    error = []

    if form_order_graph.validate():
        try:
            if form_order_graph.orderGraphUp.data:
                status, reord_list = reorder_list(
                    display_order,
                    form_order_graph.orderGraph_id.data,
                    'up')
            elif form_order_graph.orderGraphDown.data:
                status, reord_list = reorder_list(
                    display_order,
                    form_order_graph.orderGraph_id.data,
                    'down')
            if status == 'success':
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_graph = db_session.query(DisplayOrder).first()
                    order_graph.graph = ','.join(reord_list)
                    db_session.commit()
            else:
                error.append(reord_list)
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_graph'))
    else:
        flash_form_errors(form_order_graph)


#
# LCD Manipulation
#

def lcd_add(form_add_lcd, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("LCD"))
    error = []

    if form_add_lcd.validate():
        for _ in range(0, form_add_lcd.numberLCDs.data):
            new_lcd = LCD()
            random_lcd_id = ''.join([random.choice(
                    string.ascii_letters + string.digits) for _ in xrange(8)])
            new_lcd.id = random_lcd_id
            new_lcd.name = 'LCD {}'.format(random_lcd_id)
            new_lcd.pin = "27"
            new_lcd.multiplexer_address = ''
            new_lcd.multiplexer_channel = 0
            new_lcd.period = 30
            new_lcd.activated = 0
            new_lcd.x_characters = 16
            new_lcd.y_lines = 2
            new_lcd.line_1_sensor_id = ''
            new_lcd.line_1_measurement = ''
            new_lcd.line_2_sensor_id = ''
            new_lcd.line_2_measurement = ''
            new_lcd.line_3_sensor_id = ''
            new_lcd.line_3_measurement = ''
            new_lcd.line_4_sensor_id = ''
            new_lcd.line_4_measurement = ''
            try:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    db_session.add(new_lcd)
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_lcd = db_session.query(DisplayOrder).first()
                    display_order.append(random_lcd_id)
                    order_lcd.lcd = ','.join(display_order)
                    db_session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
            flash_success_errors(error, action, url_for('page_routes.page_lcd'))
    else:
        flash_form_errors(form_add_lcd)


def lcd_mod(form_mod_lcd):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("LCD"))
    error = []

    if form_mod_lcd.validate():
        try:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_lcd = db_session.query(LCD).filter(
                    LCD.id == form_mod_lcd.modLCD_id.data).first()
                if mod_lcd.activated:
                    flash(gettext("Deactivate LCD controller before modifying"
                                  " its settings."), "error")
                    return redirect('/lcd')
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_lcd = db_session.query(LCD).filter(
                    LCD.id == form_mod_lcd.modLCD_id.data).first()
                mod_lcd.name = form_mod_lcd.modName.data
                mod_lcd.pin = form_mod_lcd.modPin.data
                mod_lcd.multiplexer_address = form_mod_lcd.modMultiplexAddress.data
                mod_lcd.multiplexer_channel = form_mod_lcd.modMultiplexChannel.data
                mod_lcd.period = form_mod_lcd.modPeriod.data
                mod_lcd.x_characters = form_mod_lcd.modLCDType.data.split("x")[0]
                mod_lcd.y_lines = form_mod_lcd.modLCDType.data.split("x")[1]
                if form_mod_lcd.modLine1SensorIDMeasurement.data:
                    mod_lcd.line_1_sensor_id = form_mod_lcd.modLine1SensorIDMeasurement.data.split(",")[0]
                    mod_lcd.line_1_measurement = form_mod_lcd.modLine1SensorIDMeasurement.data.split(",")[1]
                else:
                    mod_lcd.line_1_sensor_id = ''
                    mod_lcd.line_1_measurement = ''
                if form_mod_lcd.modLine2SensorIDMeasurement.data:
                    mod_lcd.line_2_sensor_id = form_mod_lcd.modLine2SensorIDMeasurement.data.split(",")[0]
                    mod_lcd.line_2_measurement = form_mod_lcd.modLine2SensorIDMeasurement.data.split(",")[1]
                else:
                    mod_lcd.line_2_sensor_id = ''
                    mod_lcd.line_2_measurement = ''
                if form_mod_lcd.modLine3SensorIDMeasurement.data:
                    mod_lcd.line_3_sensor_id = form_mod_lcd.modLine3SensorIDMeasurement.data.split(",")[0]
                    mod_lcd.line_3_measurement = form_mod_lcd.modLine3SensorIDMeasurement.data.split(",")[1]
                else:
                    mod_lcd.line_3_sensor_id = ''
                    mod_lcd.line_3_measurement = ''
                if form_mod_lcd.modLine4SensorIDMeasurement.data:
                    mod_lcd.line_4_sensor_id = form_mod_lcd.modLine4SensorIDMeasurement.data.split(",")[0]
                    mod_lcd.line_4_measurement = form_mod_lcd.modLine4SensorIDMeasurement.data.split(",")[1]
                else:
                    mod_lcd.line_4_sensor_id = ''
                    mod_lcd.line_4_measurement = ''
                db_session.commit()
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))
    else:
        flash_form_errors(form_mod_lcd)


def lcd_del(form_del_lcd, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("LCD"))
    error = []

    if form_del_lcd.validate():
        try:
            delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                                 LCD,
                                 form_del_lcd.delLCD_id.data)
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                order_lcd = db_session.query(DisplayOrder).first()
                display_order.remove(form_del_lcd.delLCD_id.data)
                order_lcd.lcd = ','.join(display_order)
                db_session.commit()
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))
    else:
        flash_form_errors(form_del_lcd)


def lcd_reorder(form_order_lcd, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("LCD"))
    error = []

    if form_order_lcd.validate():
        try:
            if form_order_lcd.orderLCDUp.data:
                status, reord_list = reorder_list(
                    display_order,
                    form_order_lcd.orderLCD_id.data,
                    'up')
            elif form_order_lcd.orderLCDDown.data:
                status, reord_list = reorder_list(
                    display_order,
                    form_order_lcd.orderLCD_id.data,
                    'down')
            if status == 'success':
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_lcd = db_session.query(DisplayOrder).first()
                    order_lcd.lcd = ','.join(reord_list)
                    db_session.commit()
            else:
                error.append(reord_list)
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))
    else:
        flash_form_errors(form_order_lcd)


def lcd_activate(form_activate_lcd):
    action = '{action} {controller}'.format(
        action=gettext("Activate"),
        controller=gettext("LCD"))
    error = []

    if form_activate_lcd.validate():
        try:
            # All sensors the LCD depends on must be active to activate the LCD
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                lcd = db_session.query(LCD).filter(
                    LCD.id == form_activate_lcd.activateLCD_id.data).first()
                if lcd.y_lines == 2:
                    lcd_lines = [lcd.line_1_sensor_id,
                                 lcd.line_2_sensor_id]
                else:
                    lcd_lines = [lcd.line_1_sensor_id,
                                 lcd.line_2_sensor_id,
                                 lcd.line_3_sensor_id,
                                 lcd.line_4_sensor_id]
                # Filter only sensors that will be displayed
                sensor = db_session.query(Sensor).filter(
                    Sensor.id.in_(lcd_lines)).all()
                # Check if any sensors are not active
                for each_sensor in sensor:
                    if not each_sensor.is_activated():
                        flash(gettext(
                            "Cannot activate controller if the associated "
                            "sensor controller is inactive"), "error")
                        return redirect('/lcd')
            activate_deactivate_controller(
                'activate', 'LCD', form_activate_lcd.activateLCD_id.data)
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_lcd'))
    else:
        flash_form_errors(form_activate_lcd)


def lcd_deactivate(form_deactivate_lcd):
    if form_deactivate_lcd.validate():
        activate_deactivate_controller(
            'deactivate', 'LCD', form_deactivate_lcd.deactivateLCD_id.data)
    else:
        flash_form_errors(form_deactivate_lcd)


def lcd_reset_flashing(form_reset_flashing_lcd):
    if form_reset_flashing_lcd.validate():
        control = DaemonControl()
        return_value, return_msg = control.flash_lcd(
            form_reset_flashing_lcd.flashLCD_id.data, 0)
        if not return_value:
            flash(gettext("Error: %(msg)s", msg=return_msg), "error")
    else:
        flash_form_errors(form_reset_flashing_lcd)


#
# PID manipulation
#

def pid_add(form_add_pid, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("PID"))
    error = []

    if form_add_pid.validate():
        for _ in range(0, form_add_pid.numberPIDs.data):
            new_pid = PID()
            random_pid_id = ''.join([random.choice(
                    string.ascii_letters + string.digits) for _ in xrange(8)])
            new_pid.id = random_pid_id
            new_pid.name = 'PID {}'.format(random_pid_id)
            new_pid.activated = 0
            new_pid.sensor_id = ''
            new_pid.measure_type = ''
            new_pid.direction = 'raise'
            new_pid.period = 60
            new_pid.setpoint = 0.0
            new_pid.method_id = ''
            new_pid.p = 1.0
            new_pid.i = 0.0
            new_pid.d = 0.0
            new_pid.integrator_min = -100.0
            new_pid.integrator_max = 100.0
            new_pid.raise_relay_id = ''
            new_pid.raise_min_duration = 0
            new_pid.raise_max_duration = 0
            new_pid.lower_relay_id = ''
            new_pid.lower_min_duration = 0
            new_pid.lower_max_duration = 0
            try:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    db_session.add(new_pid)
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_pid = db_session.query(DisplayOrder).first()
                    display_order.append(random_pid_id)
                    order_pid.pid = ','.join(display_order)
                    db_session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_pid'))
    else:
        flash_form_errors(form_add_pid)


def pid_mod(form_mod_pid):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("PID"))
    error = []

    if form_mod_pid.validate():
        try:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                sensor = db_session.query(Sensor).filter(
                    Sensor.id == form_mod_pid.modSensorID.data).first()
                if not sensor:
                    error.append(gettext("A valid sensor ID is required"))
                elif (
                      (sensor.device_type == 'tsensor' and
                       form_mod_pid.modMeasureType.data not in ['temperature']) or

                      (sensor.device_type == 'tmpsensor' and
                       form_mod_pid.modMeasureType.data not in ['temperature_object',
                                                                'temperature_die']) or

                      (sensor.device_type == 'htsensor' and
                       form_mod_pid.modMeasureType.data not in ['temperature',
                                                                'humidity',
                                                                'dewpoint']) or

                      (sensor.device_type == 'co2sensor' and
                       form_mod_pid.modMeasureType.data not in ['co2']) or

                      (sensor.device_type == 'luxsensor' and
                       form_mod_pid.modMeasureType.data not in ['lux']) or

                      (sensor.device_type == 'moistsensor' and
                       form_mod_pid.modMeasureType.data not in ['temperature',
                                                                'lux',
                                                                'moisture']) or

                      (sensor.device_type == 'presssensor' and
                       form_mod_pid.modMeasureType.data not in ['temperature',
                                                                'pressure',
                                                                'altitude'])
                ):
                    error.append(gettext(
                        "Select a Measure Type that is compatible with the "
                        "chosen sensor"))
                if not error:
                    mod_pid = db_session.query(PID).filter(
                        PID.id == form_mod_pid.modPID_id.data).first()
                    mod_pid.name = form_mod_pid.modName.data
                    mod_pid.sensor_id = form_mod_pid.modSensorID.data
                    mod_pid.measure_type = form_mod_pid.modMeasureType.data
                    mod_pid.direction = form_mod_pid.modDirection.data
                    mod_pid.period = form_mod_pid.modPeriod.data
                    mod_pid.setpoint = form_mod_pid.modSetpoint.data
                    mod_pid.p = form_mod_pid.modKp.data
                    mod_pid.i = form_mod_pid.modKi.data
                    mod_pid.d = form_mod_pid.modKd.data
                    mod_pid.integrator_min = form_mod_pid.modIntegratorMin.data
                    mod_pid.integrator_max = form_mod_pid.modIntegratorMax.data
                    mod_pid.raise_relay_id = form_mod_pid.modRaiseRelayID.data
                    mod_pid.raise_min_duration = form_mod_pid.modRaiseMinDuration.data
                    mod_pid.raise_max_duration = form_mod_pid.modRaiseMaxDuration.data
                    mod_pid.lower_relay_id = form_mod_pid.modLowerRelayID.data
                    mod_pid.lower_min_duration = form_mod_pid.modLowerMinDuration.data
                    mod_pid.lower_max_duration = form_mod_pid.modLowerMaxDuration.data
                    mod_pid.method_id = form_mod_pid.mod_method_id.data
                    db_session.commit()
                    # If the controller is active or paused, refresh variables in thread
                    if mod_pid.activated:
                        control = DaemonControl()
                        return_value = control.pid_mod(form_mod_pid.modPID_id.data)
                        flash(gettext(
                            "PID Controller settings refresh response: %(resp)s",
                            resp=return_value), "success")
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_pid'))
    else:
        flash_form_errors(form_mod_pid)


def pid_del(pid_id, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("PID"))
    error = []

    try:
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            pid = db_session.query(PID).filter(
                PID.id == pid_id).first()
            if pid.activated:
                pid_deactivate(pid_id)

        delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                             PID,
                             pid_id)
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            order_pid = db_session.query(DisplayOrder).first()
            display_order.remove(pid_id)
            order_pid.pid = ','.join(display_order)
            db_session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_pid'))


def pid_reorder(pid_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("PID"))
    error = []

    try:
        if direction == 'up':
            status, reord_list = reorder_list(display_order, pid_id, 'up')
        elif direction == 'down':
            status, reord_list = reorder_list(display_order, pid_id, 'down')
        if status == 'success':
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                order_pid = db_session.query(DisplayOrder).first()
                order_pid.pid = ','.join(reord_list)
                db_session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_pid'))


def has_required_pid_values(pid_id):
    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        pid = db_session.query(PID).filter(
            PID.id == pid_id).first()
        error = False
        # TODO: Add more settings-checks before allowing controller to be activated
        if not pid.sensor_id:
            flash(gettext("A valid sensor  is required"), "error")
            error = True
        if not pid.measure_type:
            flash(gettext("A valid Measure Type is required"), "error")
            error = True
        if not pid.raise_relay_id and not pid.lower_relay_id:
            flash(gettext("A Raise Relay ID and/or a Lower Relay ID is "
                          "required"), "error")
            error = True
        if error:
            return redirect('/pid')


def pid_activate(pid_id):
    if has_required_pid_values(pid_id):
        return redirect(url_for('page_routes.page_pid'))

    action = '{action} {controller}'.format(
        action=gettext("Actuate"),
        controller=gettext("PID"))
    error = []

    # Check if associated sensor is activated
    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        pid = db_session.query(PID).filter(
            PID.id == pid_id).first()
        sensor = db_session.query(Sensor).filter(
            Sensor.id == pid.sensor_id).first()

        if not sensor.is_activated():
            error.append(gettext(
                "Cannot activate PID controller if the associated sensor "
                "controller is inactive"))
        else:
            # Signal the duration method can run because it's been
            # properly initiated (non-power failure)
            mod_method = db_session.query(Method).filter(
                Method.method_id == pid.method_id)
            mod_method = mod_method.filter(Method.method_order == 0).first()
            if mod_method and mod_method.method_type == 'Duration':
                mod_method.start_time = 'Ready'
                db_session.commit()

            time.sleep(1)
            activate_deactivate_controller('activate',
                                           'PID',
                                           pid_id)

    flash_success_errors(error, action, url_for('page_routes.page_pid'))


def pid_deactivate(pid_id):
    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        pid = db_session.query(PID).filter(
            PID.id == pid_id).first()
        pid.activated = 0
        db_session.commit()
    time.sleep(1)
    activate_deactivate_controller('deactivate',
                                   'PID',
                                   pid_id)


def pid_manipulate(pid_id, action):
    if action not in ['Hold', 'Pause', 'Resume']:
        flash(gettext("Invalid PID action: %(act)s", act=action), "error")
        return 1

    try:
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            mod_pid = db_session.query(PID).filter(
                PID.id == pid_id).first()
            if action == 'Hold':
                mod_pid.activated = 3
            elif action == 'Pause':
                mod_pid.activated = 2
            elif action == 'Resume':
                mod_pid.activated = 1
            db_session.commit()

        control = DaemonControl()
        if action == 'Hold':
            return_value = control.pid_hold(pid_id)
        elif action == 'Pause':
            return_value = control.pid_pause(pid_id)
        elif action == 'Resume':
            return_value = control.pid_resume(pid_id)
        flash(gettext("Daemon response to PID controller %(act)s command: "
                      "%(rval)s", act=action, rval=return_value), "success")
    except Exception as err:
        flash(gettext("PID Error: %(msg)s", msg=err), "error")


#
# Relay manipulation
#

def relay_on_off(form_relay):
    action = '{action} {controller}'.format(
        action=gettext("Actuate"),
        controller=gettext("Relay"))
    error = []

    try:
        control = DaemonControl()
        if int(form_relay.relay_pin.data) <= 0:
            error.append(gettext("Cannot modulate relay with a GPIO of 0"))
        elif form_relay.sec_on_submit.data:
            if float(form_relay.sec_on.data) <= 0:
                error.append(gettext("Value must be greater than 0"))
            else:
                return_value = control.relay_on(form_relay.relay_id.data,
                                                float(form_relay.sec_on.data))
                flash(gettext("Relay turned on for %(sec)s seconds: %(rvalue)s",
                              sec=form_relay.sec_on.data,
                              rvalue=return_value),
                      "success")
        elif form_relay.turn_on.data:
            return_value = control.relay_on(form_relay.relay_id.data, 0)
            flash(gettext("Relay turned on: %(rvalue)s",
                          rvalue=return_value), "success")
        elif form_relay.turn_off.data:
            return_value = control.relay_off(form_relay.relay_id.data)
            flash(gettext("Relay turned off: %(rvalue)s",
                          rvalue=return_value), "success")
    except ValueError as except_msg:
        error.append('{err}: {msg}'.format(
            err=gettext("Invalid value"),
            msg=except_msg))
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_relay'))


def relay_add(form_add_relay, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Relay"))
    error = []

    if form_add_relay.validate():
        for _ in range(0, form_add_relay.numberRelays.data):
            new_relay = Relay()
            random_relay_id = ''.join([random.choice(
                    string.ascii_letters + string.digits) for _ in xrange(8)])
            new_relay.id = random_relay_id
            new_relay.name = 'Relay'
            new_relay.pin = 0
            new_relay.amps = 0
            new_relay.trigger = 1
            new_relay.start_state = 0
            try:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    db_session.add(new_relay)
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_relay = db_session.query(DisplayOrder).first()
                    display_order.append(random_relay_id)
                    order_relay.relay = ','.join(display_order)
                    db_session.commit()
                manipulate_relay(gettext('Add'), random_relay_id)
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_relay'))
    else:
        flash_form_errors(form_add_relay)


def relay_mod(form_relay):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Relay"))
    error = []

    if form_relay.validate():
        try:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_relay = db_session.query(Relay).filter(
                    Relay.id == form_relay.relay_id.data).first()
                mod_relay.name = form_relay.name.data
                setup_pin = False
                if mod_relay.pin is not form_relay.gpio.data:
                    setup_pin = True
                mod_relay.pin = form_relay.gpio.data
                mod_relay.amps = form_relay.amps.data
                mod_relay.trigger = form_relay.trigger.data
                mod_relay.start_state = form_relay.start_state.data
                db_session.commit()
                manipulate_relay(gettext('Modify'),
                                 form_relay.relay_id.data,
                                 setup_pin)
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_relay'))
    else:
        flash_form_errors(form_relay)


def relay_del(form_relay, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Relay"))
    error = []

    if form_relay.validate():
        try:
            delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                                 Relay,
                                 form_relay.relay_id.data)
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                order_relay = db_session.query(DisplayOrder).first()
                display_order.remove(form_relay.relay_id.data)
                order_relay.relay = ','.join(display_order)
                db_session.commit()
            manipulate_relay(gettext('Delete'), form_relay.relay_id.data)
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_relay'))
    else:
        flash_form_errors(form_relay)


def relay_reorder(form_relay, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Relay"))
    error = []

    if form_relay.validate():
        try:
            if form_relay.order_up.data:
                status, reord_list = reorder_list(
                    display_order,
                    form_relay.relay_id.data,
                    'up')
            elif form_relay.order_down.data:
                status, reord_list = reorder_list(
                    display_order,
                    form_relay.relay_id.data,
                    'down')
            if status == 'success':
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_relay = db_session.query(DisplayOrder).first()
                    order_relay.relay = ','.join(reord_list)
                    db_session.commit()
            else:
                error.append(reord_list)
        except Exception as except_msg:
            error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_relay'))
    else:
        flash_form_errors(form_relay)


#
# Relay conditional manipulation
#

def relay_conditional_add(form_add_relay_cond):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Relay Conditional"))
    error = []

    if form_add_relay_cond.validate():
        for _ in range(0, form_add_relay_cond.numberRelayConditionals.data):
            new_relay_cond = RelayConditional()
            random_id = ''.join([random.choice(
                    string.ascii_letters + string.digits) for _ in xrange(8)])
            new_relay_cond.id = random_id
            new_relay_cond.name = 'Relay Conditional'
            new_relay_cond.activated = False
            new_relay_cond.if_relay_id = ''
            new_relay_cond.if_action = ''
            new_relay_cond.if_duration = 0
            new_relay_cond.do_relay_id = ''
            new_relay_cond.do_action = ''
            new_relay_cond.do_duration = 0
            new_relay_cond.execute_command = ''
            new_relay_cond.email_notify = ''
            new_relay_cond.flash_lcd = ''
            try:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    db_session.add(new_relay_cond)
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_sensor'))
    else:
        flash_form_errors(form_add_relay_cond)


def relay_conditional_mod(form_relay_cond):
    action = None
    error = []

    try:
        if form_relay_cond.activate.data:
            action = '{action} {controller}'.format(
                action=gettext("Activate"),
                controller=gettext("Relay Conditional"))
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                relay_cond = db_session.query(RelayConditional)
                relay_cond = relay_cond.filter(
                    RelayConditional.id == form_relay_cond.relay_id.data).first()
                relay_cond.activated = True
                db_session.commit()
        elif form_relay_cond.deactivate.data:
            action = '{action} {controller}'.format(
                action=gettext("Deactivate"),
                controller=gettext("Relay Conditional"))
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                relay_cond = db_session.query(RelayConditional).filter(
                    RelayConditional.id == form_relay_cond.relay_id.data).first()
                relay_cond.activated = 0
                db_session.commit()
        elif form_relay_cond.delete.data:
            action = '{action} {controller}'.format(
                action=gettext("Delete"),
                controller=gettext("Relay Conditional"))
            delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                                 RelayConditional,
                                 form_relay_cond.relay_id.data)
        elif (form_relay_cond.save.data and
                form_relay_cond.validate()):
            action = '{action} {controller}'.format(
                action=gettext("Modify"),
                controller=gettext("Relay Conditional"))
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_relay = db_session.query(RelayConditional).filter(
                    RelayConditional.id == form_relay_cond.relay_id.data).first()
                mod_relay.name = form_relay_cond.name.data
                mod_relay.if_relay_id = form_relay_cond.if_relay_id.data
                mod_relay.if_action = form_relay_cond.if_relay_action.data
                mod_relay.if_duration = form_relay_cond.if_relay_duration.data
                mod_relay.do_relay_id = form_relay_cond.do_relay_id.data
                mod_relay.do_action = form_relay_cond.do_relay_action.data
                mod_relay.do_duration = form_relay_cond.do_relay_duration.data
                mod_relay.execute_command = form_relay_cond.do_execute.data
                mod_relay.email_notify = form_relay_cond.do_notify.data
                mod_relay.flash_lcd = form_relay_cond.do_flash_lcd.data
                db_session.commit()
        else:
            flash_form_errors(form_relay_cond)
            return redirect(url_for('page_routes.page_relay'))
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_sensor'))


#
# Sensor manipulation
#

def sensor_add(form_add_sensor, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Sensor"))
    error = []

    if form_add_sensor.validate():
        for _ in range(0, form_add_sensor.numberSensors.data):
            new_sensor = Sensor()
            random_sensor_id = ''.join([random.choice(
                    string.ascii_letters + string.digits) for _ in xrange(8)])
            new_sensor.id = random_sensor_id
            new_sensor.device = form_add_sensor.sensor.data
            new_sensor.name = '{} ({})'.format(form_add_sensor.sensor.data,
                                               random_sensor_id)
            if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
                new_sensor.i2c_bus = 1
                new_sensor.multiplexer_bus = 1
            else:
                new_sensor.i2c_bus = 0
                new_sensor.multiplexer_bus = 0
            new_sensor.location = ''
            new_sensor.multiplexer_address = ''
            new_sensor.multiplexer_channel = 0
            new_sensor.adc_channel = 0
            new_sensor.adc_gain = 1
            new_sensor.adc_resolution = 18
            new_sensor.adc_measure = 'Condition'
            new_sensor.adc_measure_units = 'Unit'
            new_sensor.adc_units_min = 0.0
            new_sensor.adc_units_max = 10.0
            new_sensor.switch_edge = 'rising'
            new_sensor.switch_bouncetime = 50
            new_sensor.switch_reset_period = 10
            new_sensor.pre_relay_duration = 0
            new_sensor.activated = 0
            new_sensor.graph = 0
            new_sensor.period = 15
            new_sensor.sht_clock_pin = 0
            new_sensor.sht_voltage = 3.5

            # Process monitors
            if form_add_sensor.sensor.data == 'RPiCPULoad':
                new_sensor.device_type = 'cpu_load'
                new_sensor.location = 'RPi'
            elif form_add_sensor.sensor.data == 'EDGE':
                new_sensor.device_type = 'edgedetect'

            # Environmental Sensors
            # Temperature
            elif form_add_sensor.sensor.data in ['ATLAS_PT1000', 'DS18B20',
                                                 'RPi', 'TMP006']:
                new_sensor.device_type = 'tsensor'
                if form_add_sensor.sensor.data == 'ATLAS_PT1000':
                    new_sensor.location = '0x66'
                elif form_add_sensor.sensor.data == 'RPi':
                    new_sensor.location = 'RPi'
                elif form_add_sensor.sensor.data == 'TMP006':
                    new_sensor.location = '0x40'
            
            # Temperature/Humidity
            elif form_add_sensor.sensor.data in ['AM2315', 'DHT11', 'DHT22',
                                                 'HTU21D', 'SHT1x_7x',
                                                 'SHT2x']:
                new_sensor.device_type = 'htsensor'
                if form_add_sensor.sensor.data == 'AM2315':
                    new_sensor.location = '0x5c'
                elif form_add_sensor.sensor.data == 'HTU21D':
                    new_sensor.location = '0x40'
                elif form_add_sensor.sensor.data == 'SHT2x':
                    new_sensor.location = '0x40'

            # Chirp moisture sensor
            elif form_add_sensor.sensor.data == 'CHIRP':
                new_sensor.device_type = 'moistsensor'
                new_sensor.location = '0x20'

            # CO2
            elif form_add_sensor.sensor.data == 'K30':
                new_sensor.device_type = 'co2sensor'
                new_sensor.location = 'Tx/Rx'
            
            # Pressure
            elif form_add_sensor.sensor.data in ['BME280', 'BMP']:
                new_sensor.device_type = 'presssensor'
                if form_add_sensor.sensor.data == 'BME280':
                    new_sensor.location = '0x76'
                elif form_add_sensor.sensor.data == 'BMP':
                    new_sensor.location = '0x77'

            # Light
            elif form_add_sensor.sensor.data == 'TSL2561':
                new_sensor.device_type = 'luxsensor'
                new_sensor.location = '0x39'

            # Analog to Digital Converters
            elif form_add_sensor.sensor.data in ['ADS1x15', 'MCP342x']:
                new_sensor.device_type = 'analogsensor'
                if form_add_sensor.sensor.data == 'ADS1x15':
                    new_sensor.location = '0x48'
                    new_sensor.adc_volts_min = -4.096
                    new_sensor.adc_volts_max = 4.096
                elif form_add_sensor.sensor.data == 'MCP342x':
                    new_sensor.location = '0x68'
                    new_sensor.adc_volts_min = -2.048
                    new_sensor.adc_volts_max = 2.048

            try:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    db_session.add(new_sensor)
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_sensor = db_session.query(DisplayOrder).first()
                    display_order.append(random_sensor_id)
                    order_sensor.sensor = ','.join(display_order)
                    db_session.commit()
                flash(gettext(
                    "%(type)s Sensor with ID %(id)s successfully added",
                    type=form_add_sensor.sensor.data, id=random_sensor_id),
                    "success")
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
        flash_success_errors(error, action, url_for('page_routes.page_sensor'))
    else:
        flash_form_errors(form_add_sensor)


def sensor_mod(form_mod_sensor):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Sensor"))
    error = []

    try:
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            mod_sensor = db_session.query(Sensor).filter(
                Sensor.id == form_mod_sensor.modSensor_id.data).first()

            if not form_mod_sensor.modLocation.data:
                error.append(gettext(
                    "Invalid device GPIO/I2C address/location"))
            if mod_sensor.activated:
                error.append(gettext(
                    "Deactivate sensor controller before modifying its "
                    "settings"))
            if (mod_sensor.device == 'AM2315' and
                    form_mod_sensor.modPeriod.data < 7):
                error.append(gettext(
                    "Choose a Read Period equal to or greater than 7. The "
                    "AM2315 may become unresponsive if the period is "
                    "below 7."))
            if form_mod_sensor.modPeriod.data < mod_sensor.pre_relay_duration:
                error.append(gettext(
                    "The Read Period cannot be less than the Pre-Relay "
                    "Duration"))

            if not error:
                mod_sensor.name = form_mod_sensor.modName.data
                mod_sensor.i2c_bus = form_mod_sensor.modBus.data
                mod_sensor.location = form_mod_sensor.modLocation.data
                mod_sensor.multiplexer_address = form_mod_sensor.modMultiplexAddress.data
                mod_sensor.multiplexer_bus = form_mod_sensor.modMultiplexBus.data
                mod_sensor.multiplexer_channel = form_mod_sensor.modMultiplexChannel.data
                mod_sensor.adc_channel = form_mod_sensor.modADCChannel.data
                mod_sensor.adc_gain = form_mod_sensor.modADCGain.data
                mod_sensor.adc_resolution = form_mod_sensor.modADCResolution.data
                mod_sensor.adc_measure = form_mod_sensor.modADCMeasure.data.replace(" ", "_")
                mod_sensor.adc_measure_units = form_mod_sensor.modADCMeasureUnits.data
                mod_sensor.adc_volts_min = form_mod_sensor.modADCVoltsMin.data
                mod_sensor.adc_volts_max = form_mod_sensor.modADCVoltsMax.data
                mod_sensor.adc_units_min = form_mod_sensor.modADCUnitsMin.data
                mod_sensor.adc_units_max = form_mod_sensor.modADCUnitsMax.data
                mod_sensor.switch_edge = form_mod_sensor.modSwitchEdge.data
                mod_sensor.switch_bouncetime = form_mod_sensor.modSwitchBounceTime.data
                mod_sensor.switch_reset_period = form_mod_sensor.modSwitchResetPeriod.data
                mod_sensor.pre_relay_id = form_mod_sensor.modPreRelayID.data
                mod_sensor.pre_relay_duration = form_mod_sensor.modPreRelayDuration.data
                mod_sensor.period = form_mod_sensor.modPeriod.data
                mod_sensor.sht_clock_pin = form_mod_sensor.modSHTClockPin.data
                mod_sensor.sht_voltage = float(form_mod_sensor.modSHTVoltage.data)
                db_session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_sensor'))


def sensor_del(form_mod_sensor, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Sensor"))
    error = []

    try:
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            sensor = db_session.query(Sensor).filter(
                Sensor.id == form_mod_sensor.modSensor_id.data).first()
            if sensor.activated:
                sensor_deactivate_associated_controllers(
                    form_mod_sensor.modSensor_id.data)
                activate_deactivate_controller(
                    'deactivate', 'Sensor',
                    form_mod_sensor.modSensor_id.data)

            sensor_cond = db_session.query(SensorConditional).all()
            for each_sensor_cond in sensor_cond:
                if each_sensor_cond.sensor_id == form_mod_sensor.modSensor_id.data:
                    delete_entry_with_id(
                        current_app.config['MYCODO_DB_PATH'],
                        SensorConditional,
                        each_sensor_cond.id)

        delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                             Sensor,
                             form_mod_sensor.modSensor_id.data)
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            order_sensor = db_session.query(DisplayOrder).first()
            display_order.remove(form_mod_sensor.modSensor_id.data)
            order_sensor.sensor = ','.join(display_order)
            db_session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_sensor'))


def sensor_reorder(form_mod_sensor, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Sensor"))
    error = []

    try:
        status = None
        if form_mod_sensor.orderSensorUp.data:
            status, reord_list = reorder_list(
                display_order, form_mod_sensor.modSensor_id.data, 'up')
        elif form_mod_sensor.orderSensorDown.data:
            status, reord_list = reorder_list(
                display_order, form_mod_sensor.modSensor_id.data, 'down')
        if status == 'success':
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                order_sensor = db_session.query(DisplayOrder).first()
                order_sensor.sensor = ','.join(reord_list)
                db_session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_sensor'))


def sensor_activate(form_mod_sensor):
    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        sensor = db_session.query(Sensor).filter(
            Sensor.id == form_mod_sensor.modSensor_id.data).first()
        if not sensor.location:
            flash("Cannot activate sensor without the GPIO/I2C Address/Port "
                  "to communicate with it set.", "error")
            return redirect('/sensor')
    activate_deactivate_controller('activate',
                                   'Sensor',
                                   form_mod_sensor.modSensor_id.data)


def sensor_deactivate(form_mod_sensor):
    sensor_deactivate_associated_controllers(
        form_mod_sensor.modSensor_id.data)
    activate_deactivate_controller('deactivate',
                                   'Sensor',
                                   form_mod_sensor.modSensor_id.data)


# Deactivate any active PID or LCD controllers using this sensor
def sensor_deactivate_associated_controllers(sensor_id):
    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        pid = db_session.query(PID).filter(sqlalchemy.and_(
                PID.sensor_id == sensor_id,
                PID.activated == 1)).all()
        if pid:
            for each_pid in pid:
                activate_deactivate_controller('deactivate',
                                               'PID',
                                               each_pid.id)
        lcd = db_session.query(LCD).filter(LCD.activated)
        for each_lcd in lcd:
            if sensor_id in [each_lcd.line_1_sensor_id,
                             each_lcd.line_2_sensor_id,
                             each_lcd.line_3_sensor_id,
                             each_lcd.line_4_sensor_id]:
                activate_deactivate_controller('deactivate',
                                               'LCD',
                                               each_lcd.id)


#
# Sensor conditional manipulation
#

def sensor_conditional_add(form_mod_sensor):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Sensor Conditional"))
    error = []

    new_sensor_cond = SensorConditional()
    random_id = ''.join([random.choice(
            string.ascii_letters + string.digits) for _ in xrange(8)])
    new_sensor_cond.id = random_id
    new_sensor_cond.name = 'Sensor Conditional'
    new_sensor_cond.activated = 0
    new_sensor_cond.sensor_id = form_mod_sensor.modSensor_id.data
    new_sensor_cond.period = 60
    new_sensor_cond.measurement_type = ''
    new_sensor_cond.edge_select = 'edge'
    new_sensor_cond.edge_detected = 'rising'
    new_sensor_cond.gpio_state = 1
    new_sensor_cond.direction = ''
    new_sensor_cond.setpoint = 0.0
    new_sensor_cond.relay_id = ''
    new_sensor_cond.relay_state = ''
    new_sensor_cond.relay_on_duration = 0.0
    new_sensor_cond.execute_command = ''
    new_sensor_cond.email_notify = ''
    new_sensor_cond.flash_lcd = ''
    new_sensor_cond.camera_record = ''
    try:
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            db_session.add(new_sensor_cond)
        check_refresh_conditional(form_mod_sensor.modSensor_id.data,
                                  'add',
                                  random_id)
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_sensor'))


def sensor_conditional_mod(form_mod_sensor_cond):
    action = None
    error = []

    if form_mod_sensor_cond.delSubmit.data:
        action = '{action} {controller}'.format(
            action=gettext("Delete"),
            controller=gettext("Sensor Conditional"))
        try:
            delete_entry_with_id(
                current_app.config['MYCODO_DB_PATH'],
                SensorConditional,
                form_mod_sensor_cond.modCondSensor_id.data)
            check_refresh_conditional(
                form_mod_sensor_cond.modSensor_id.data,
                'del',
                form_mod_sensor_cond.modCondSensor_id.data)
        except Exception as except_msg:
            error.append(except_msg)
    elif (form_mod_sensor_cond.modSubmit.data and
            form_mod_sensor_cond.validate()):
        action = '{action} {controller}'.format(
            action=gettext("Modify"),
            controller=gettext("Sensor Conditional"))
        try:
            if (form_mod_sensor_cond.DoRecord.data == 'photoemail' or form_mod_sensor_cond.DoRecord.data == 'videoemail') and not form_mod_sensor_cond.DoNotify.data:
                error.append(gettext("A notification email address is "
                                     "required if the record and email "
                                     "option is selected"))
            else:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    mod_sensor = db_session.query(SensorConditional).filter(
                        SensorConditional.id == form_mod_sensor_cond.modCondSensor_id.data).first()
                    mod_sensor.name = form_mod_sensor_cond.modCondName.data
                    mod_sensor.period = form_mod_sensor_cond.Period.data
                    mod_sensor.measurement_type = form_mod_sensor_cond.MeasureType.data
                    mod_sensor.edge_select = form_mod_sensor_cond.EdgeSelect.data
                    mod_sensor.edge_detected = form_mod_sensor_cond.EdgeDetected.data
                    mod_sensor.gpio_state = form_mod_sensor_cond.GPIOState.data
                    mod_sensor.direction = form_mod_sensor_cond.Direction.data
                    mod_sensor.setpoint = form_mod_sensor_cond.Setpoint.data
                    mod_sensor.relay_id = form_mod_sensor_cond.modCondRelayID.data
                    mod_sensor.relay_state = form_mod_sensor_cond.RelayState.data
                    mod_sensor.relay_on_duration = form_mod_sensor_cond.RelayDuration.data
                    mod_sensor.execute_command = form_mod_sensor_cond.DoExecute.data
                    mod_sensor.email_notify = form_mod_sensor_cond.DoNotify.data
                    mod_sensor.flash_lcd = form_mod_sensor_cond.DoFlashLCD.data
                    mod_sensor.camera_record = form_mod_sensor_cond.DoRecord.data
                    db_session.commit()
                    check_refresh_conditional(
                        form_mod_sensor_cond.modSensor_id.data,
                        'mod',
                        form_mod_sensor_cond.modCondSensor_id.data)
        except Exception as except_msg:
            error.append(except_msg)
    elif form_mod_sensor_cond.activateSubmit.data:
        action = '{action} {controller}'.format(
            action=gettext("Activate"),
            controller=gettext("Sensor Conditional"))
        try:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_sensor = db_session.query(SensorConditional).filter(
                    SensorConditional.id == form_mod_sensor_cond.modCondSensor_id.data).first()
                sensor = db_session.query(Sensor).filter(
                    Sensor.id == mod_sensor.sensor_id).first()

                device_specific_configured = False
                cond_configured = False
                
                # Ensure device-specific settings configured properly
                if sensor.device == 'EDGE' and mod_sensor.edge_detected:
                    device_specific_configured = True
                elif (sensor.device != 'EDGE' and
                        mod_sensor.period and
                        mod_sensor.measurement_type and
                        mod_sensor.direction):
                    device_specific_configured = True

                # Ensure universal conditional settings configured properly
                if ((mod_sensor.relay_id and mod_sensor.relay_state) or
                        mod_sensor.execute_command or
                        mod_sensor.email_notify or
                        mod_sensor.flash_lcd or
                        mod_sensor.camera_record):
                    cond_configured = True

                if device_specific_configured and cond_configured:
                    mod_sensor.activated = 1
                    db_session.commit()
                    check_refresh_conditional(
                        form_mod_sensor_cond.modSensor_id.data,
                        'mod',
                        form_mod_sensor_cond.modCondSensor_id.data)
                else:
                    error.append(gettext(
                        "Cannot activate sensor conditional %(cond)s because "
                        "of an incomplete configuration",
                        cond=form_mod_sensor_cond.modCondSensor_id.data))
        except Exception as except_msg:
            error.append(except_msg)
    elif form_mod_sensor_cond.deactivateSubmit.data:
        action = '{action} {controller}'.format(
            action=gettext("Deactivate"),
            controller=gettext("Sensor Conditional"))
        try:
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_sensor = db_session.query(SensorConditional).filter(
                    SensorConditional.id == form_mod_sensor_cond.modCondSensor_id.data).first()
                mod_sensor.activated = 0
                db_session.commit()
                check_refresh_conditional(
                    form_mod_sensor_cond.modSensor_id.data,
                    'mod',
                    form_mod_sensor_cond.modCondSensor_id.data)
        except Exception as except_msg:
            error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_sensor'))


def check_refresh_conditional(sensor_id, cond_mod, cond_id):
    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        sensor = db_session.query(Sensor).filter(sqlalchemy.and_(
                Sensor.id == sensor_id,
                Sensor.activated == 1)).first()
        if sensor:
            control = DaemonControl()
            control.refresh_sensor_conditionals(sensor_id, cond_mod, cond_id)


#
# Timers
#

def timer_add(form_add_timer, timer_type, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Timer"))
    error = []

    if form_add_timer.validate():
        new_timer = Timer()
        random_timer_id = ''.join([random.choice(
                string.ascii_letters + string.digits) for _ in xrange(8)])
        new_timer.id = random_timer_id
        new_timer.name = form_add_timer.name.data
        new_timer.activated = 0
        new_timer.relay_id = form_add_timer.relayID.data
        if timer_type == 'time':
            new_timer.timer_type = 'time'
            new_timer.state = form_add_timer.state.data
            new_timer.time_start = form_add_timer.timeStart.data
            new_timer.duration_on = form_add_timer.timeOnDurationOn.data
            new_timer.duration_off = 0
        elif timer_type == 'timespan':
            new_timer.timer_type = 'timespan'
            new_timer.state = form_add_timer.state.data
            new_timer.time_start = form_add_timer.timeStart.data
            new_timer.time_end = form_add_timer.timeEnd.data
        elif timer_type == 'duration':
            if (form_add_timer.durationOn.data <= 0 or
                    form_add_timer.durationOff.data <= 0):
                error.append(gettext("Durations must be greater than 0"),
                             "error")
            else:
                new_timer.timer_type = 'duration'
                new_timer.duration_on = form_add_timer.durationOn.data
                new_timer.duration_off = form_add_timer.durationOff.data

        if not error:
            try:
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    db_session.add(new_timer)
                with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                    order_timer = db_session.query(DisplayOrder).first()
                    display_order.append(random_timer_id)
                    order_timer.timer = ','.join(display_order)
                    db_session.commit()
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError  as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('page_routes.page_timer'))
    else:
        flash_form_errors(form_add_timer)


def timer_mod(form_timer):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Timer"))
    error = []

    try:
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            mod_timer = db_session.query(Timer).filter(
                Timer.id == form_timer.timer_id.data).first()
            if mod_timer.activated:
                error.append(gettext("Deactivate timer controller before "
                                     "modifying its settings"))
                return redirect(url_for('page_routes.page_timer'))
            else:
                mod_timer.name = form_timer.name.data
                mod_timer.relay_id = form_timer.relayID.data
                if mod_timer.timer_type == 'time':
                    mod_timer.state = form_timer.state.data
                    mod_timer.time_start = form_timer.timeStart.data
                    mod_timer.duration_on = form_timer.timeOnDurationOn.data
                elif mod_timer.timer_type == 'timespan':
                    mod_timer.state = form_timer.state.data
                    mod_timer.time_start = form_timer.timeStart.data
                    mod_timer.time_end = form_timer.timeEnd.data
                elif mod_timer.timer_type == 'duration':
                    mod_timer.duration_on = form_timer.durationOn.data
                    mod_timer.duration_off = form_timer.durationOff.data
                db_session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_del(form_timer, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Timer"))
    error = []

    try:
        delete_entry_with_id(current_app.config['MYCODO_DB_PATH'],
                             Timer,
                             form_timer.timer_id.data)
        with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
            order_sensor = db_session.query(DisplayOrder).first()
            display_order.remove(form_timer.timer_id.data)
            order_sensor.timer = ','.join(display_order)
            db_session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_reorder(form_timer, display_order):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Timer"))
    error = []

    try:
        status = ''
        reord_list = ''
        if form_timer.orderTimerUp.data:
            status, reord_list = reorder_list(display_order,
                                              form_timer.timer_id.data,
                                              'up')
        elif form_timer.orderTimerDown.data:
            status, reord_list = reorder_list(display_order,
                                              form_timer.timer_id.data,
                                              'down')
        if status == 'success':
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                order_timer = db_session.query(DisplayOrder).first()
                order_timer.timer = ','.join(reord_list)
                db_session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('page_routes.page_timer'))


def timer_activate(form_timer):
    activate_deactivate_controller(
        'activate', 'Timer', form_timer.timer_id.data)


def timer_deactivate(form_timer):
    activate_deactivate_controller(
        'deactivate', 'Timer', form_timer.timer_id.data)


#
# User manipulation
#

def user_add(form_add_user):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("User"))
    error = []

    if form_add_user.validate():
        new_user = Users()
        if not test_username(form_add_user.addUsername.data):
            error.append(gettext(
                "Invalid user name. Must be between 2 and 64 characters "
                "and only contain letters and numbers."))

        if not test_password(form_add_user.addPassword.data):
            error.append(gettext(
                "Invalid password. Must be between 6 and 64 characters "
                "and only contain letters, numbers, and symbols."))

        if form_add_user.addPassword.data != form_add_user.addPassword_repeat.data:
            error.append(gettext("Passwords do not match. Please try again."))

        if not error:
            new_user.user_name = form_add_user.addUsername.data
            new_user.user_email = form_add_user.addEmail.data
            new_user.set_password(form_add_user.addPassword.data)
            new_user.user_restriction = form_add_user.addGroup.data
            new_user.user_theme = 'slate'
            try:
                with session_scope(current_app.config['USER_DB_PATH']) as db_session:
                    db_session.add(new_user)

            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)

        flash_success_errors(error, action, url_for('settings_routes.settings_users'))
    else:
        flash_form_errors(form_add_user)


def user_mod(form_mod_user):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("User"))
    error = []

    try:
        with session_scope(current_app.config['USER_DB_PATH']) as db_session:
            mod_user = db_session.query(Users).filter(
                Users.user_name == form_mod_user.modUsername.data).first()
            mod_user.user_email = form_mod_user.modEmail.data
            # Only change the password if it's entered in the form
            logout_user = False
            if form_mod_user.modPassword.data != '':
                if not test_password(form_mod_user.modPassword.data):
                    error.append(gettext("Invalid password"))
                if form_mod_user.modPassword.data == form_mod_user.modPassword_repeat.data:
                    mod_user.user_password_hash = bcrypt.hashpw(
                        form_mod_user.modPassword.data.encode('utf-8'),
                        bcrypt.gensalt())
                    if session['user_name'] == form_mod_user.modUsername.data:
                        logout_user = True
                else:
                    error.append(gettext("Passwords do not match. Please try again."))

            if not error:
                mod_user.user_restriction = form_mod_user.modGroup.data
                mod_user.user_theme = form_mod_user.modTheme.data
                if session['user_name'] == form_mod_user.modUsername.data:
                    session['user_theme'] = form_mod_user.modTheme.data
                db_session.commit()
                if logout_user:
                    return 'logout'
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_users'))


def user_del(form_del_user):
    try:
        if form_del_user.validate():
            delete_user(current_app.config['USER_DB_PATH'],
                        Users,
                        form_del_user.delUsername.data)
            if form_del_user.delUsername.data == session['user_name']:
                return 'logout'
        else:
            flash_form_errors(form_del_user)
    except Exception as except_msg:
        flash(gettext("Error: %(msg)s",
                      msg='{action} {user}: {err}'.format(
                          action=gettext("Delete"),
                          user=form_del_user.delUsername.data,
                          err=except_msg)),
              "error")


#
# Settings modifications
#

def settings_general_mod(form_mod_general):
    """ Modify General settings """
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("General Settings"))
    error = []

    try:
        if form_mod_general.validate():
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_misc = db_session.query(Misc).one()
                force_https = mod_misc.force_https
                mod_misc.language = form_mod_general.language.data
                mod_misc.force_https = form_mod_general.forceHTTPS.data
                mod_misc.hide_alert_success = form_mod_general.hideAlertSuccess.data
                mod_misc.hide_alert_info = form_mod_general.hideAlertInfo.data
                mod_misc.relay_stats_volts = form_mod_general.relayStatsVolts.data
                mod_misc.relay_stats_cost = form_mod_general.relayStatsCost.data
                mod_misc.relay_stats_currency = form_mod_general.relayStatsCurrency.data
                mod_misc.relay_stats_dayofmonth = form_mod_general.relayStatsDayOfMonth.data
                mod_misc.hide_alert_warning = form_mod_general.hideAlertWarning.data
                mod_misc.stats_opt_out = form_mod_general.stats_opt_out.data
                db_session.commit()

                if force_https != form_mod_general.forceHTTPS.data:
                    # Force HTTPS option changed.
                    # Reload web server with new settings.
                    wsgi_file = INSTALL_DIRECTORY+'/mycodo_flask.wsgi'
                    with open(wsgi_file, 'a'):
                        os.utime(wsgi_file, None)
        else:
            flash_form_errors(form_mod_general)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_general'))


def settings_camera_mod(form_mod_camera):
    """ Modify Camera settings """
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Camera Settings"))
    error = []

    try:
        if form_mod_camera.validate():
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_camera = db_session.query(CameraStill).one()
                mod_camera.hflip = form_mod_camera.hflip.data
                mod_camera.vflip = form_mod_camera.vflip.data
                mod_camera.rotation = form_mod_camera.rotation.data
                db_session.commit()
        else:
            flash_form_errors(form_mod_camera)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_camera'))


def settings_alert_mod(form_mod_alert):
    """ Modify Alert settings """
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Alert Settings"))
    error = []

    try:
        if form_mod_alert.validate():
            with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
                mod_smtp = db_session.query(SMTP).one()
                if form_mod_alert.sendTestEmail.data:
                    send_email(
                        mod_smtp.host, mod_smtp.ssl, mod_smtp.port,
                        mod_smtp.user, mod_smtp.passw, mod_smtp.email_from,
                        form_mod_alert.testEmailTo.data,
                        "This is a test email from Mycodo")
                    flash(gettext("Test email sent to %(recip)s. Check your "
                                  "inbox to see if it was successful.",
                                  recip=form_mod_alert.testEmailTo.data),
                          "success")
                    return redirect(url_for('settings_routes.settings_alerts'))
                else:
                    mod_smtp.host = form_mod_alert.smtpHost.data
                    mod_smtp.port = form_mod_alert.smtpPort.data
                    mod_smtp.ssl = form_mod_alert.sslEnable.data
                    mod_smtp.user = form_mod_alert.smtpUser.data
                    if form_mod_alert.smtpPassword.data:
                        mod_smtp.passw = form_mod_alert.smtpPassword.data
                    mod_smtp.email_from = form_mod_alert.smtpFromEmail.data
                    mod_smtp.hourly_max = form_mod_alert.smtpMaxPerHour.data
                    db_session.commit()
        else:
            flash_form_errors(form_mod_alert)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('settings_routes.settings_alerts'))


#
# Miscellaneous
#


def db_retrieve_table(database, table, first=False, device_id=''):
    """ Return table data from database SQL query """
    with session_scope(database) as new_session:
        if first:
            return_table = new_session.query(table).first()
        elif device_id:
            return_table = new_session.query(table).filter(
                table.id == device_id).first()
        else:
            return_table = new_session.query(table).all()
        new_session.expunge_all()
        new_session.close()
    return return_table


def delete_user(db_path, users, username):
    """ Delete user from SQL database """
    try:
        with session_scope(db_path) as db_session:
            user = db_session.query(users).filter(
                users.user_name == username).first()
            db_session.delete(user)
            flash(gettext("Success: %(msg)s",
                          msg='{action} {user}'.format(
                              action=gettext("Delete"),
                              user=username)),
                  "success")
            return 1
    except sqlalchemy.orm.exc.NoResultFound:
        flash(gettext("Error: %(err)s",
                      err=gettext("User not found")),
              "error")
        return 0


def delete_entry_with_id(db_path, table, entry_id):
    """ Delete SQL database entry with specific id """
    try:
        with session_scope(db_path) as db_session:
            entries = db_session.query(table).filter(
                table.id == entry_id).first()
            db_session.delete(entries)
            flash(gettext("Success: %(msg)s",
                          msg='{action} {id}'.format(
                              action=gettext("Delete"),
                              id=entry_id)),
                  "success")
            return 1
    except sqlalchemy.orm.exc.NoResultFound:
        flash(gettext("Error: %(err)s",
                      err=gettext("Entry with ID %(id)s not found",
                                  id=entry_id)),
              "error")
        flash(gettext("Error: %(msg)s",
                      msg='{action} {id}: {err}'.format(
                          action=gettext("Delete"),
                          id=entry_id,
                          err=gettext("Entry with ID %(id)s not found",
                                      id=entry_id))),
              "success")
        return 0


def deny_guest_user():
    if session['user_group'] == 'guest':
        flash(gettext("Guests are not permitted to do that"), "error")
        return True


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
            flash(gettext("Error: %(msg)s",
                          msg='{action}: {err}'.format(
                              action=action,
                              err=each_error)),
                  "error")
        return redirect(redirect_url)
    else:
        flash(gettext("Success: %(msg)s",
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


def reorder_list(modified_list, item, direction):
    """ Reorder entry in a comma-separated list either up or down """
    from_position = modified_list.index(item)
    if direction == "up":
        if from_position == 0:
            return 'error', gettext('Cannot move above the first item in the list')
        to_position = from_position - 1
    elif direction == 'down':
        if from_position == len(modified_list) - 1:
            return 'error', gettext('Cannot move below the last item in the list')
        to_position = from_position + 1
    else:
        return 'error', []
    modified_list.insert(to_position, modified_list.pop(from_position))
    return 'success', modified_list
