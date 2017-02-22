# coding=utf-8
""" collection of Method endpoints """
import logging
import datetime
import time

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask_babel import gettext

# Classes
from mycodo.databases.mycodo_db.models import (
    db,
    Method,
    MethodData,
    Relay
)

# Functions
from mycodo import flaskforms
from mycodo import flaskutils
from mycodo.mycodo_flask.general_routes import (
    inject_mycodo_version,
    logged_in
)
from mycodo.utils.system_pi import (
    csv_to_list_of_int,
    get_sec
)

from mycodo.utils.method import (
    sine_wave_y_out,
    bezier_curve_y_out
)

logger = logging.getLogger('mycodo.mycodo_flask.methods')

blueprint = Blueprint('method_routes',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
def inject_dictionary():
    return inject_mycodo_version()


@blueprint.route('/method-data/<method_id>')
def method_data(method_id):
    """
    Returns options for a particular method
    This includes sets of (time, setpoint) data.
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    # First method column with general information about method
    method = Method.query.filter(Method.id == method_id).first()

    # User-edited lines of each method
    method_data = MethodData.query.filter(MethodData.method_id == method.id)

    # Retrieve the order to display method data lines
    display_order = csv_to_list_of_int(method.method_order)

    last_method_data = None
    if display_order is not None:
        method_data = MethodData.query.filter(MethodData.method_id == method.id)
        last_method_data = method_data.filter(MethodData.id == display_order[-1]).first()

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
            y = sine_wave_y_out(last_method_data.amplitude, last_method_data.frequency,
                                last_method_data.shift_angle, last_method_data.shift_y,
                                angle)
            method_list.append([percent * seconds_in_day * 1000, y])

    elif method.method_type == "Duration":
        first_entry = True
        start_duration = 0
        end_duration = 0
        for each_method in method_data:
            if each_method.setpoint_end is None:
                setpoint_end = each_method.setpoint_start
            else:
                setpoint_end = each_method.setpoint_end
            if first_entry:
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
def method_list():
    """ List all methods on one page with a graph for each """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    form_create_method = flaskforms.CreateMethod()

    method = Method.query.all()
    method_all = MethodData.query.all()

    return render_template('pages/method-list.html',
                           method=method,
                           method_all=method_all,
                           form_create_method=form_create_method)


@blueprint.route('/method-build/<method_id>', methods=('GET', 'POST'))
def method_builder(method_id):
    """
    Page to edit the details of each method
    This includes the (time, setpoint) data sets
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if not flaskutils.authorized(session, 'Guest'):
        flaskutils.deny_guest_user()
        return redirect('/method')

    relay = Relay.query.all()

    form_create_method = flaskforms.CreateMethod()
    form_add_method = flaskforms.AddMethod()
    form_mod_method = flaskforms.ModMethod()

    # Used in software tests to verify function is executing as admin
    if method_id == '-1':
        return 'admin logged in'
    # Create new method
    elif method_id == '0':
        form_fail = flaskutils.method_create(form_create_method)
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

        method_data = MethodData.query.filter(MethodData.method_id == method.id)
        if display_order is not None:
            last_method_data = method_data.filter(MethodData.id == display_order[-1]).first()
        else:
            last_method_data = None

        method_data = None

        last_end_time = ''
        last_setpoint = ''
        if method.method_type in ['Daily', 'Date', 'Duration']:
            method_data = method_data.all()

            # Get last entry end time and setpoint to populate the form
            if last_method_data is None:
                last_end_time = ''
                last_setpoint = ''
            else:
                last_end_time = last_method_data.time_end
                if last_method_data.setpoint_end is not None:
                    last_setpoint = last_method_data.setpoint_end
                else:
                    last_setpoint = last_method_data.setpoint_start

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addMethod':
                form_fail = flaskutils.method_add(form_add_method)
            elif form_name in ['modMethod', 'renameMethod']:
                form_fail = flaskutils.method_mod(form_mod_method)
            if (form_name in ['addMethod', 'modMethod', 'renameMethod'] and
                    not form_fail):
                return redirect('/method-build/{method_id}'.format(
                    method_id=method.id))

        if not method_data:
            method_data = []

        return render_template('pages/method-build.html',
                               method=method,
                               relay=relay,
                               method_data=method_data,
                               method_id=method_id,
                               last_end_time=last_end_time,
                               last_method_data=last_method_data,
                               last_setpoint=last_setpoint,
                               form_create_method=form_create_method,
                               form_add_method=form_add_method,
                               form_mod_method=form_mod_method)

    return redirect('/method')


@blueprint.route('/method-delete/<method_id>')
def method_delete(method_id):
    """Delete a method"""
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Method"))

    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if not flaskutils.authorized(session, 'Guest'):
        flaskutils.deny_guest_user()
        return redirect('/method')

    try:
        Method.query.filter(Method.id == method_id).delete()
        MethodData.query.filter(MethodData.method_id == method_id).delete()
        db.session.commit()
        flash("Success: {action}".format(action=action), "success")
    except Exception as except_msg:
        flash("Error: {action}: {err}".format(action=action,
                                              err=except_msg),
              "error")
    return redirect(url_for('method_routes.method_list'))
