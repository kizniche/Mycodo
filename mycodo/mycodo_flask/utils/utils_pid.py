# -*- coding: utf-8 -*-
import logging
import time

from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext

from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import Method
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# PID manipulation
#


def pid_mod(form_mod_pid_base,
            form_mod_pid_pwm_raise, form_mod_pid_pwm_lower,
            form_mod_pid_output_raise, form_mod_pid_output_lower):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("PID"))
    error = []

    if not form_mod_pid_base.validate():
        error.append(gettext("Error in form field(s)"))
        flash_form_errors(form_mod_pid_base)

    mod_pid = PID.query.filter(
        PID.unique_id == form_mod_pid_base.pid_id.data).first()

    # Check if a specific setting can be modified if the PID is active
    if mod_pid.is_activated:
        error = can_set_output(error,
                               form_mod_pid_base.pid_id.data,
                               form_mod_pid_base.raise_output_id.data,
                               form_mod_pid_base.lower_output_id.data)

    mod_pid.name = form_mod_pid_base.name.data
    mod_pid.measurement = form_mod_pid_base.measurement.data
    mod_pid.direction = form_mod_pid_base.direction.data
    mod_pid.period = form_mod_pid_base.period.data
    mod_pid.max_measure_age = form_mod_pid_base.max_measure_age.data
    mod_pid.setpoint = form_mod_pid_base.setpoint.data
    mod_pid.band = abs(form_mod_pid_base.band.data)
    mod_pid.store_lower_as_negative = form_mod_pid_base.store_lower_as_negative.data
    mod_pid.p = form_mod_pid_base.k_p.data
    mod_pid.i = form_mod_pid_base.k_i.data
    mod_pid.d = form_mod_pid_base.k_d.data
    mod_pid.integrator_min = form_mod_pid_base.integrator_max.data
    mod_pid.integrator_max = form_mod_pid_base.integrator_min.data
    mod_pid.method_id = form_mod_pid_base.method_id.data

    if form_mod_pid_base.raise_output_id.data:
        raise_output_type = Output.query.filter(
            Output.unique_id == form_mod_pid_base.raise_output_id.data).first().output_type
        if mod_pid.raise_output_id == form_mod_pid_base.raise_output_id.data:
            if raise_output_type == 'pwm':
                if not form_mod_pid_pwm_raise.validate():
                    error.append(gettext("Error in form field(s)"))
                    flash_form_errors(form_mod_pid_pwm_raise)
                else:
                    mod_pid.raise_min_duration = form_mod_pid_pwm_raise.raise_min_duty_cycle.data
                    mod_pid.raise_max_duration = form_mod_pid_pwm_raise.raise_max_duty_cycle.data
            else:
                if not form_mod_pid_output_raise.validate():
                    error.append(gettext("Error in form field(s)"))
                    flash_form_errors(form_mod_pid_output_raise)
                else:
                    mod_pid.raise_min_duration = form_mod_pid_output_raise.raise_min_duration.data
                    mod_pid.raise_max_duration = form_mod_pid_output_raise.raise_max_duration.data
                    mod_pid.raise_min_off_duration = form_mod_pid_output_raise.raise_min_off_duration.data
        else:
            if raise_output_type == 'pwm':
                mod_pid.raise_min_duration = 2
                mod_pid.raise_max_duration = 98
            else:
                mod_pid.raise_min_duration = 0
                mod_pid.raise_max_duration = 0
                mod_pid.raise_min_off_duration = 0
        mod_pid.raise_output_id = form_mod_pid_base.raise_output_id.data
    else:
        mod_pid.raise_output_id = None

    if form_mod_pid_base.lower_output_id.data:
        lower_output_type = Output.query.filter(
            Output.unique_id == form_mod_pid_base.lower_output_id.data).first().output_type
        if mod_pid.lower_output_id == form_mod_pid_base.lower_output_id.data:
            if lower_output_type == 'pwm':
                if not form_mod_pid_pwm_lower.validate():
                    error.append(gettext("Error in form field(s)"))
                    flash_form_errors(form_mod_pid_pwm_lower)
                else:
                    mod_pid.lower_min_duration = form_mod_pid_pwm_lower.lower_min_duty_cycle.data
                    mod_pid.lower_max_duration = form_mod_pid_pwm_lower.lower_max_duty_cycle.data
            else:
                if not form_mod_pid_output_lower.validate():
                    error.append(gettext("Error in form field(s)"))
                    flash_form_errors(form_mod_pid_output_lower)
                else:
                    mod_pid.lower_min_duration = form_mod_pid_output_lower.lower_min_duration.data
                    mod_pid.lower_max_duration = form_mod_pid_output_lower.lower_max_duration.data
                    mod_pid.lower_min_off_duration = form_mod_pid_output_lower.lower_min_off_duration.data
        else:
            if lower_output_type == 'pwm':
                mod_pid.lower_min_duration = 2
                mod_pid.lower_max_duration = 98
            else:
                mod_pid.lower_min_duration = 0
                mod_pid.lower_max_duration = 0
                mod_pid.lower_min_off_duration = 0
        mod_pid.lower_output_id = form_mod_pid_base.lower_output_id.data
    else:
        mod_pid.lower_output_id = None

    if (mod_pid.raise_output_id and mod_pid.lower_output_id and
            mod_pid.raise_output_id == mod_pid.lower_output_id):
        error.append(gettext("Raise and lower outputs cannot be the same"))

    try:
        if not error:
            db.session.commit()
            # If the controller is active or paused, refresh variables in thread
            if mod_pid.is_activated:
                control = DaemonControl()
                return_value = control.pid_mod(form_mod_pid_base.pid_id.data)
                flash(gettext(
                    "PID Controller settings refresh response: %(resp)s",
                    resp=return_value), "success")
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_function'))


def pid_del(pid_id):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("PID"))
    error = []

    try:
        pid = PID.query.filter(
            PID.unique_id == pid_id).first()
        if pid.is_activated:
            pid_deactivate(pid_id)

        delete_entry_with_id(PID, pid_id)

        display_order = csv_to_list_of_str(DisplayOrder.query.first().pid)
        display_order.remove(pid_id)
        DisplayOrder.query.first().pid = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def pid_reorder(pid_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("PID"))
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
    flash_success_errors(error, action, url_for('routes_page.page_function'))


# TODO: Add more settings-checks before allowing controller to be activated
def has_required_pid_values(pid_id):
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()
    error = False
    device_unique_id = pid.measurement.split(',')[0]
    input = Input.query.filter(
        Input.unique_id == device_unique_id).first()
    math = Math.query.filter(
        Math.unique_id == device_unique_id).first()
    if (not input and not math) or not pid.measurement:
        flash(gettext("A valid Measurement is required"), "error")
        error = True
    if not pid.raise_output_id and not pid.lower_output_id:
        flash(gettext("A Raise Output and/or a Lower Output is "
                      "required"), "error")
        error = True
    if error:
        return redirect('/pid')


def pid_activate(pid_id):
    if has_required_pid_values(pid_id):
        return redirect(url_for('routes_page.page_function'))

    action = '{action} {controller}'.format(
        action=gettext("Actuate"),
        controller=gettext("PID"))
    error = []

    # Check if associated sensor is activated
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()

    error = can_set_output(
        error, pid_id, pid.raise_output_id, pid.lower_output_id)

    device_unique_id = pid.measurement.split(',')[0]
    input = Input.query.filter(
        Input.unique_id == device_unique_id).first()
    math = Math.query.filter(
        Math.unique_id == device_unique_id).first()

    if (input and not input.is_activated) or (math and not math.is_activated):
        error.append(gettext(
            "Cannot activate PID controller if the associated sensor "
            "controller is inactive"))

    if ((pid.direction == 'both' and not (pid.lower_output_id and pid.raise_output_id)) or
                (pid.direction == 'lower' and not pid.lower_output_id) or
                (pid.direction == 'raise' and not pid.raise_output_id)):
        error.append(gettext(
            "Cannot activate PID controller if raise and/or lower output IDs "
            "are not selected"))

    if not error:
        # Signal the duration method can run because it's been
        # properly initiated (non-power failure)
        method = Method.query.filter(
            Method.unique_id == pid.method_id).first()
        if method and method.method_type == 'Duration':
            mod_pid = PID.query.filter(PID.unique_id == pid_id).first()
            mod_pid.method_start_time = 'Ready'
            db.session.commit()

        time.sleep(1)
        controller_activate_deactivate('activate',
                                       'PID',
                                       pid_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def pid_deactivate(pid_id):
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()
    pid.is_activated = False
    pid.is_held = False
    pid.is_paused = False
    db.session.commit()
    time.sleep(1)
    controller_activate_deactivate('deactivate',
                                   'PID',
                                   pid_id)


def pid_manipulate(pid_id, action):
    if action not in ['Hold', 'Pause', 'Resume']:
        flash(gettext("Invalid PID action: %(act)s", act=action), "error")
        return 1

    try:
        mod_pid = PID.query.filter(
            PID.unique_id == pid_id).first()
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
            flash(gettext("Daemon response to PID controller %(act)s command: "
                          "%(rval)s", act=action, rval=return_value), "success")
    except Exception as err:
        flash(gettext("Error: %(err)s",
                      err='PID: {msg}'.format(msg=err)),
              "error")


def can_set_output(error, pid_id, raise_output_id, lower_output_id):
    """ Don't allow an output to be used with more than one active PID """
    pid_all = (PID.query
               .filter(PID.is_activated == True)
               .filter(PID.unique_id != pid_id)
              ).all()
    for each_pid in pid_all:
        if ((raise_output_id and
                (raise_output_id == each_pid.raise_output_id or
                 raise_output_id == each_pid.lower_output_id)) or
            (lower_output_id and
                (lower_output_id == each_pid.lower_output_id or
                 lower_output_id == each_pid.raise_output_id))):
            error.append(gettext(
                "Cannot set output if it is already "
                "selected by another active PID controller"))
    return error
