# coding=utf-8
"""collection of Method endpoints."""
import logging

import flask_login
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_babel import gettext

from mycodo.config import METHOD_INFO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import DisplayOrder, Method, MethodData
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_method
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general, utils_method
from mycodo.utils.method import create_method_handler
from mycodo.utils.outputs import output_types
from mycodo.utils.system_pi import csv_to_list_of_str, list_to_csv

logger = logging.getLogger('mycodo.mycodo_flask.methods')

blueprint = Blueprint('routes_method',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
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
    method = Method.query.filter(Method.unique_id == method_id).first()

    # User-edited lines of each method
    method_data = MethodData.query.filter(MethodData.method_id == method.unique_id)

    return jsonify(create_method_handler(method, method_data).get_plot(700))


@blueprint.route('/method', methods=('GET', 'POST'))
@flask_login.login_required
def method_list():
    """List all methods on one page with a graph for each."""
    form_create_method = forms_method.MethodCreate()

    method = Method.query.all()
    method_all = MethodData.query.all()

    return render_template('pages/method-list.html',
                           method=method,
                           method_all=method_all,
                           method_info=METHOD_INFO,
                           form_create_method=form_create_method)


@blueprint.route('/method-build/<method_id>', methods=('GET', 'POST'))
@flask_login.login_required
def method_builder(method_id):
    """
    Page to edit the details of each method
    This includes the (time, setpoint) data sets
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_method.method_list'))

    form_create_method = forms_method.MethodCreate()
    form_add_method = forms_method.MethodAdd()
    form_mod_method = forms_method.MethodMod()

    form_fail = None

    # Used in software tests to verify function is executing as admin
    if method_id == '-1':
        return 'admin logged in'

    # Create new method
    elif method_id == '0':
        unmet_dependencies = utils_method.method_create(form_create_method)
        if unmet_dependencies:
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device=form_create_method.method_type.data))

        if not unmet_dependencies:
            new_method = Method.query.order_by(Method.id.desc()).first()
            return redirect('/method-build/{method_id}'.format(
                method_id=new_method.unique_id))
        else:
            return redirect('/method')
    elif not method_id:
        flash("Invalid method ID", "error")
        return redirect('/method')

    # First method column with general information about method
    method = Method.query.filter(Method.unique_id == method_id).first()

    if method.method_type == 'Cascade':
        method_data = MethodData.query.filter(
            MethodData.method_id == method.unique_id)

        cascade_method = Method.query.filter(Method.unique_id != method_id).all()

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addMethod':
                form_fail = utils_method.method_add(form_add_method)
            elif form_name in ['modMethod', 'renameMethod']:
                form_fail = utils_method.method_mod(form_mod_method)
            if (form_name in ['addMethod', 'modMethod', 'renameMethod'] and
                    not form_fail):
                return redirect('/method-build/{method_id}'.format(
                    method_id=method.unique_id))

        if not method_data:
            method_data = []

        return render_template('pages/method-build.html',
                               method=method,
                               method_data=method_data,
                               method_id=method_id,
                               output_types=output_types(),
                               cascade_method=cascade_method,
                               form_create_method=form_create_method,
                               form_add_method=form_add_method,
                               form_mod_method=form_mod_method)

    if method.method_type in ['Date', 'Duration', 'Daily',
                              'DailySine', 'DailyBezier']:

        # Retrieve the order to display method data lines
        display_order = csv_to_list_of_str(method.method_order)

        method_data = MethodData.query.filter(
            MethodData.method_id == method.unique_id)
        setpoint_method_data = MethodData.query.filter(
            MethodData.setpoint_start.isnot(None))
        sine_method_data = MethodData.query.filter(
            MethodData.amplitude.isnot(None))
        bezier_method_data = MethodData.query.filter(
            MethodData.x0.isnot(None))
        if display_order:
            last_setpoint_method = setpoint_method_data.filter(
                MethodData.unique_id == display_order[-1]).first()
            last_sine_method = sine_method_data.filter(
                MethodData.unique_id == display_order[-1]).first()
            last_bezier_method = bezier_method_data.filter(
                MethodData.unique_id == display_order[-1]).first()
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
                    method_id=method.unique_id))

        if not method_data:
            method_data = []

        return render_template('pages/method-build.html',
                               method=method,
                               method_data=method_data,
                               method_id=method_id,
                               last_end_time=last_end_time,
                               last_bezier_method=last_bezier_method,
                               last_sine_method=last_sine_method,
                               last_setpoint_method=last_setpoint_method,
                               last_setpoint=last_setpoint,
                               output_types=output_types(),
                               form_create_method=form_create_method,
                               form_add_method=form_add_method,
                               form_mod_method=form_mod_method)

    return redirect('/method')


@blueprint.route('/method-delete/<method_id>')
@flask_login.login_required
def method_delete(method_id):
    """Delete a method."""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=gettext("Method"))

    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('routes_method.method_list'))

    try:
        MethodData.query.filter(
            MethodData.method_id == method_id).delete()
        MethodData.query.filter(
            MethodData.linked_method_id == method_id).delete()
        Method.query.filter(
            Method.unique_id == method_id).delete()
        display_order = csv_to_list_of_str(DisplayOrder.query.first().method)
        display_order.remove(method_id)
        DisplayOrder.query.first().method = list_to_csv(display_order)
        db.session.commit()
        flash("Success: {action}".format(action=action), "success")
    except Exception as except_msg:
        flash("Error: {action}: {err}".format(action=action,
                                              err=except_msg),
              "error")
    return redirect(url_for('routes_method.method_list'))
