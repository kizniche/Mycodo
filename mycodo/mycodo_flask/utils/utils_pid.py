# -*- coding: utf-8 -*-
import logging
import time

from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import DeviceMeasurements
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
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# PID manipulation
#


def pid_mod(form_mod_pid_base,
            form_mod_pid_pwm_raise, form_mod_pid_pwm_lower,
            form_mod_pid_output_raise, form_mod_pid_output_lower):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['pid']['title'])
    error = []

    dict_outputs = parse_output_information()

    if not form_mod_pid_base.validate():
        error.append(TRANSLATIONS['error']['title'])
        flash_form_errors(form_mod_pid_base)

    mod_pid = PID.query.filter(
        PID.unique_id == form_mod_pid_base.function_id.data).first()

    mod_pid.name = form_mod_pid_base.name.data
    mod_pid.measurement = form_mod_pid_base.measurement.data
    mod_pid.direction = form_mod_pid_base.direction.data
    mod_pid.period = form_mod_pid_base.period.data
    mod_pid.log_level_debug = form_mod_pid_base.log_level_debug.data
    mod_pid.start_offset = form_mod_pid_base.start_offset.data
    mod_pid.max_measure_age = form_mod_pid_base.max_measure_age.data
    mod_pid.setpoint = form_mod_pid_base.setpoint.data
    mod_pid.band = abs(form_mod_pid_base.band.data)
    mod_pid.store_lower_as_negative = form_mod_pid_base.store_lower_as_negative.data
    mod_pid.p = form_mod_pid_base.k_p.data
    mod_pid.i = form_mod_pid_base.k_i.data
    mod_pid.d = form_mod_pid_base.k_d.data
    mod_pid.integrator_min = form_mod_pid_base.integrator_max.data
    mod_pid.integrator_max = form_mod_pid_base.integrator_min.data
    mod_pid.setpoint_tracking_type = form_mod_pid_base.setpoint_tracking_type.data
    if form_mod_pid_base.setpoint_tracking_type.data == 'method':
        mod_pid.setpoint_tracking_id = form_mod_pid_base.setpoint_tracking_method_id.data
    elif form_mod_pid_base.setpoint_tracking_type.data == 'input-math':
        mod_pid.setpoint_tracking_id = form_mod_pid_base.setpoint_tracking_input_math_id.data
        if form_mod_pid_base.setpoint_tracking_max_age.data:
            mod_pid.setpoint_tracking_max_age = form_mod_pid_base.setpoint_tracking_max_age.data
        else:
            mod_pid.setpoint_tracking_max_age = 120
    else:
        mod_pid.setpoint_tracking_id = ''

    # Change measurement information
    if ',' in form_mod_pid_base.measurement.data:
        measurement_id = form_mod_pid_base.measurement.data.split(',')[1]
        selected_measurement = get_measurement(measurement_id)

        measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == form_mod_pid_base.function_id.data).all()
        for each_measurement in measurements:
            # Only set channels 0, 1, 2
            if each_measurement.channel in [0, 1, 2]:
                each_measurement.measurement = selected_measurement.measurement
                each_measurement.unit = selected_measurement.unit

    if form_mod_pid_base.raise_output_id.data:
        raise_output_type = Output.query.filter(
            Output.unique_id == form_mod_pid_base.raise_output_id.data).first().output_type

        if ('output_types' in dict_outputs[raise_output_type] and
                'pwm' in dict_outputs[raise_output_type]['output_types']):
            mod_pid.raise_always_min_pwm = form_mod_pid_pwm_raise.raise_always_min_pwm.data

        if mod_pid.raise_output_id == form_mod_pid_base.raise_output_id.data:
            if ('output_types' in dict_outputs[raise_output_type] and
                    'pwm' in dict_outputs[raise_output_type]['output_types']):
                if not form_mod_pid_pwm_raise.validate():
                    error.append(TRANSLATIONS['error']['title'])
                    flash_form_errors(form_mod_pid_pwm_raise)
                else:
                    mod_pid.raise_min_duration = form_mod_pid_pwm_raise.raise_min_duty_cycle.data
                    mod_pid.raise_max_duration = form_mod_pid_pwm_raise.raise_max_duty_cycle.data
            else:
                if not form_mod_pid_output_raise.validate():
                    error.append(TRANSLATIONS['error']['title'])
                    flash_form_errors(form_mod_pid_output_raise)
                else:
                    mod_pid.raise_min_duration = form_mod_pid_output_raise.raise_min_duration.data
                    mod_pid.raise_max_duration = form_mod_pid_output_raise.raise_max_duration.data
                    mod_pid.raise_min_off_duration = form_mod_pid_output_raise.raise_min_off_duration.data
        else:
            if ('output_types' in dict_outputs[raise_output_type] and
                    'pwm' in dict_outputs[raise_output_type]['output_types']):
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

        if ('output_types' in dict_outputs[lower_output_type] and
                'pwm' in dict_outputs[lower_output_type]['output_types']):
            mod_pid.lower_always_min_pwm = form_mod_pid_pwm_lower.lower_always_min_pwm.data

        if mod_pid.lower_output_id == form_mod_pid_base.lower_output_id.data:
            if ('output_types' in dict_outputs[lower_output_type] and
                    'pwm' in dict_outputs[lower_output_type]['output_types']):
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
            if ('output_types' in dict_outputs[lower_output_type] and
                    'pwm' in dict_outputs[lower_output_type]['output_types']):
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
                return_value = control.pid_mod(form_mod_pid_base.function_id.data)
                flash("PID Controller settings refresh response: "
                      "{resp}".format(resp=return_value), "success")
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_function'))


def pid_del(pid_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['pid']['title'])
    error = []

    try:
        pid = PID.query.filter(
            PID.unique_id == pid_id).first()
        if pid.is_activated:
            pid_deactivate(pid_id)

        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == pid_id).all()

        for each_measurement in device_measurements:
            delete_entry_with_id(DeviceMeasurements, each_measurement.unique_id)

        delete_entry_with_id(PID, pid_id)
        try:
            display_order = csv_to_list_of_str(DisplayOrder.query.first().math)
            display_order.remove(pid_id)
            DisplayOrder.query.first().function = list_to_csv(display_order)
        except Exception:  # id not in list
            pass
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def pid_autotune(form_mod_pid_base):
    action = '{action} {controller}'.format(
        action=gettext("Start Autotune"),
        controller=TRANSLATIONS['pid']['title'])
    error = []
    try:
        # Activate autotune flag in PID config
        mod_pid = PID.query.filter(
            PID.unique_id == form_mod_pid_base.function_id.data).first()
        mod_pid.autotune_activated = True
        mod_pid.autotune_noiseband = form_mod_pid_base.pid_autotune_noiseband.data
        mod_pid.autotune_outstep = form_mod_pid_base.pid_autotune_outstep.data
        db.session.commit()

        # Activate PID
        pid_activate(form_mod_pid_base.function_id.data)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_function'))


# TODO: Add more settings-checks before allowing controller to be activated
def has_required_pid_values(pid_id):
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()
    error = False

    if not pid.measurement:
        flash(gettext("A valid Measurement is required"), "error")
        error = True
    else:
        device_unique_id = pid.measurement.split(',')[0]
        input_dev = Input.query.filter(
            Input.unique_id == device_unique_id).first()
        math = Math.query.filter(
            Math.unique_id == device_unique_id).first()
        if not input_dev and not math:
            flash(gettext("A valid Measurement is required"), "error")
            error = True

    if not pid.raise_output_id and not pid.lower_output_id:
        flash(gettext("A Raise Output and/or a Lower Output is ""required"),
              "error")
        error = True
    if error:
        return redirect('/pid')


def pid_activate(pid_id):
    if has_required_pid_values(pid_id):
        return redirect(url_for('routes_page.page_function'))

    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['pid']['title'])
    error = []

    # Check if associated sensor is activated
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()

    device_unique_id = pid.measurement.split(',')[0]
    input_dev = Input.query.filter(
        Input.unique_id == device_unique_id).first()
    math = Math.query.filter(
        Math.unique_id == device_unique_id).first()

    if (input_dev and not input_dev.is_activated) or (math and not math.is_activated):
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
            Method.unique_id == pid.setpoint_tracking_id).first()
        if pid.setpoint_tracking_type == 'method' and method and method.method_type == 'Duration':
            mod_pid = PID.query.filter(PID.unique_id == pid_id).first()
            mod_pid.method_start_time = 'Ready'
            db.session.commit()
        time.sleep(1)
        controller_activate_deactivate('activate', 'PID', pid_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def pid_deactivate(pid_id):
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()
    pid.is_activated = False
    pid.is_held = False
    pid.is_paused = False
    db.session.commit()
    time.sleep(1)
    controller_activate_deactivate('deactivate', 'PID', pid_id)


def pid_manipulate(pid_id, action):
    if action not in ['Hold', 'Pause', 'Resume']:
        flash('{}: {}'.format(TRANSLATIONS['invalid']['title'], action), "error")
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
            flash(
                '{}: {}: {}: {}'.format(
                    TRANSLATIONS['controller']['title'],
                    TRANSLATIONS['pid']['title'],
                    action,
                    return_value),
                "success")
    except Exception as err:
        flash(
            "{}: {}: {}".format(
                TRANSLATIONS['Error']['title'],
                TRANSLATIONS['PID']['title'], err),
            "error")
