# coding=utf-8
""" collection of Method endpoints """
import datetime
import logging
import time

import flask_login
from flask import Blueprint
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import gettext

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.databases.models import Output
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_method
from mycodo.mycodo_flask.static_routes import inject_variables
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_method
from mycodo.utils.method import bezier_curve_y_out
from mycodo.utils.method import sine_wave_y_out
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.system_pi import get_sec
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger('mycodo.mycodo_flask.methods')

blueprint = Blueprint('method_routes',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
def inject_dictionary():
    return inject_variables()


@blueprint.route('/method-data/<method_id>')
@flask_login.login_required
def method_data(method_id):
    """
    Returns options for a particular method
    This includes sets of (time, setpoint) data.
    """
    # First method column with general information about method
    method = Method.query.filter(Method.id == method_id).first()

    # User-edited lines of each method
    method_data = MethodData.query.filter(MethodData.method_id == method.id)

    # Retrieve the order to display method data lines
    display_order = csv_to_list_of_int(method.method_order)

    last_method_data = None
    if display_order is not None:
        method_data = MethodData.query.filter(
            MethodData.method_id == method.id)
        last_method_data = method_data.filter(
            MethodData.id == display_order[-1]).first()

    method_list = []
    if method.method_type == "Date":
        for each_method in method_data:
            if each_method.setpoint_end == None:
                setpoint_end = each_method.setpoint_start
            else:
                setpoint_end = each_method.setpoint_end

            start_time = datetime.datetime.strptime(
                each_method.time_start, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.datetime.strptime(
                each_method.time_end, '%Y-%m-%d %H:%M:%S')

            is_dst = time.daylight and time.localtime().tm_isdst > 0
            utc_offset_ms = (time.altzone if is_dst else time.timezone)
            method_list.append(
                [(int(start_time.strftime("%s")) - utc_offset_ms) * 1000,
                 each_method.setpoint_start])
            method_list.append(
                [(int(end_time.strftime("%s")) - utc_offset_ms) * 1000,
                 setpoint_end])
            method_list.append(
                [(int(start_time.strftime("%s")) - utc_offset_ms) * 1000,
                 None])

    elif method.method_type == "Daily":
        method_data = method_data.filter(MethodData.time_start != None)
        method_data = method_data.filter(MethodData.time_end != None)
        method_data = method_data.filter(MethodData.relay_id == None)
        for each_method in method_data:
            if each_method.setpoint_end is None:
                setpoint_end = each_method.setpoint_start
            else:
                setpoint_end = each_method.setpoint_end
            method_list.append(
                [get_sec(each_method.time_start) * 1000,
                 each_method.setpoint_start])
            method_list.append(
                [get_sec(each_method.time_end) * 1000,
                 setpoint_end])
            method_list.append(
                [get_sec(each_method.time_start) * 1000,
                 None])

    elif method.method_type == "DailyBezier":
        points_x = 700
        seconds_in_day = 60 * 60 * 24
        P0 = (last_method_data.x0, last_method_data.y0)
        P1 = (last_method_data.x1, last_method_data.y1)
        P2 = (last_method_data.x2, last_method_data.y2)
        P3 = (last_method_data.x3, last_method_data.y3)
        for n in range(points_x):
            percent = n / float(points_x)
            second_of_day = percent * seconds_in_day
            if second_of_day == 0:
                continue
            y = bezier_curve_y_out(last_method_data.shift_angle,
                                   P0, P1, P2, P3,
                                   second_of_day)
            method_list.append([percent * seconds_in_day * 1000, y])

    elif method.method_type == "DailySine":
        points_x = 700
        seconds_in_day = 60 * 60 * 24
        for n in range(points_x):
            percent = n / float(points_x)
            angle = n / float(points_x) * 360
            y = sine_wave_y_out(last_method_data.amplitude,
                                last_method_data.frequency,
                                last_method_data.shift_angle,
                                last_method_data.shift_y,
                                angle)
            method_list.append([percent * seconds_in_day * 1000, y])

    elif method.method_type == "Duration":
        first_entry = True
        start_duration = 0
        end_duration = 0
        method_data = method_data.filter(MethodData.relay_id == None)
        for each_method in method_data:
            if each_method.setpoint_end is None:
                setpoint_end = each_method.setpoint_start
            else:
                setpoint_end = each_method.setpoint_end

            if each_method.duration_sec == 0:
                pass  # Method line is repeat command, don't add to method_list
            elif first_entry:
                method_list.append([0, each_method.setpoint_start])
                method_list.append([each_method.duration_sec, setpoint_end])
                start_duration += each_method.duration_sec
                first_entry = False
            else:
                end_duration = start_duration + each_method.duration_sec

                method_list.append(
                    [start_duration, each_method.setpoint_start])
                method_list.append(
                    [end_duration, setpoint_end])

                start_duration += each_method.duration_sec

    return jsonify(method_list)


@blueprint.route('/method', methods=('GET', 'POST'))
@flask_login.login_required
def method_list():
    """ List all methods on one page with a graph for each """
    form_create_method = forms_method.MethodCreate()

    method = Method.query.all()
    method_all = MethodData.query.all()

    return render_template('pages/method-list.html',
                           method=method,
                           method_all=method_all,
                           form_create_method=form_create_method)


@blueprint.route('/method-build/<method_id>', methods=('GET', 'POST'))
@flask_login.login_required
def method_builder(method_id):
    """
    Page to edit the details of each method
    This includes the (time, setpoint) data sets
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('method_routes.method_list'))

    output = Output.query.all()

    form_create_method = forms_method.MethodCreate()
    form_add_method = forms_method.MethodAdd()
    form_mod_method = forms_method.MethodMod()

    # Used in software tests to verify function is executing as admin
    if method_id == '-1':
        return 'admin logged in'
    # Create new method
    elif method_id == '0':
        form_fail = utils_method.method_create(form_create_method)
        new_method = Method.query.order_by(Method.id.desc()).first()
        if not form_fail:
            return redirect('/method-build/{method_id}'.format(
                method_id=new_method.id))
        else:
            return redirect('/method')
    elif int(method_id) < 0:
        flash("Invalid method ID", "error")
        return redirect('/method')

    # First method column with general information about method
    method = Method.query.filter(Method.id == int(method_id)).first()

    if method.method_type in ['Date', 'Duration', 'Daily',
                              'DailySine', 'DailyBezier']:

        # Retrieve the order to display method data lines
        display_order = csv_to_list_of_int(method.method_order)

        method_data = MethodData.query.filter(
            MethodData.method_id == method.id)
        setpoint_method_data = MethodData.query.filter(
            MethodData.setpoint_start != None)
        sine_method_data = MethodData.query.filter(
            MethodData.amplitude != None)
        bezier_method_data = MethodData.query.filter(
            MethodData.x0 != None)
        if display_order is not None:
            last_setpoint_method = setpoint_method_data.filter(
                MethodData.id == display_order[-1]).first()
            last_sine_method = sine_method_data.filter(
                MethodData.id == display_order[-1]).first()
            last_bezier_method = bezier_method_data.filter(
                MethodData.id == display_order[-1]).first()
        else:
            last_setpoint_method = None
            last_sine_method = None
            last_bezier_method = None

        last_end_time = ''
        last_setpoint = ''
        if method.method_type in ['Daily', 'Date', 'Duration']:
            method_data = method_data.all()

            # Get last entry end time and setpoint to populate the form
            if last_setpoint_method is None:
                last_end_time = ''
                last_setpoint = ''
            else:
                last_end_time = last_setpoint_method.time_end
                if last_setpoint_method.setpoint_end is not None:
                    last_setpoint = last_setpoint_method.setpoint_end
                else:
                    last_setpoint = last_setpoint_method.setpoint_start

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addMethod':
                form_fail = utils_method.method_add(form_add_method)
            elif form_name in ['modMethod', 'renameMethod']:
                form_fail = utils_method.method_mod(form_mod_method)
            if (form_name in ['addMethod', 'modMethod', 'renameMethod'] and
                    not form_fail):
                return redirect('/method-build/{method_id}'.format(
                    method_id=method.id))

        if not method_data:
            method_data = []

        return render_template('pages/method-build.html',
                               method=method,
                               output=output,
                               method_data=method_data,
                               method_id=method_id,
                               last_end_time=last_end_time,
                               last_bezier_method=last_bezier_method,
                               last_sine_method=last_sine_method,
                               last_setpoint_method=last_setpoint_method,
                               last_setpoint=last_setpoint,
                               form_create_method=form_create_method,
                               form_add_method=form_add_method,
                               form_mod_method=form_mod_method)

    return redirect('/method')


@blueprint.route('/method-delete/<method_id>')
@flask_login.login_required
def method_delete(method_id):
    """Delete a method"""
    action = '{action} {controller}'.format(
        action=gettext(u"Delete"),
        controller=gettext(u"Method"))

    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('method_routes.method_list'))

    try:
        MethodData.query.filter(
            MethodData.method_id == int(method_id)).delete()
        Method.query.filter(
            Method.id == int(method_id)).delete()
        display_order = csv_to_list_of_int(DisplayOrder.query.first().method)
        display_order.remove(int(method_id))
        DisplayOrder.query.first().method = list_to_csv(display_order)
        db.session.commit()
        flash("Success: {action}".format(action=action), "success")
    except Exception as except_msg:
        flash("Error: {action}: {err}".format(action=action,
                                              err=except_msg),
              "error")
    return redirect(url_for('method_routes.method_list'))
