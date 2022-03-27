# -*- coding: utf-8 -*-
import logging
import time

from flask import flash
from flask_babel import gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import form_error_messages
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import get_measurement

logger = logging.getLogger(__name__)

#
# PID manipulation
#

def pid_mod(form_mod_pid_base,
            form_mod_pid_pwm_raise,
            form_mod_pid_pwm_lower,
            form_mod_pid_output_raise,
            form_mod_pid_output_lower,
            form_mod_pid_value_raise,
            form_mod_pid_value_lower,
            form_mod_pid_volume_raise,
            form_mod_pid_volume_lower):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": [],
        "name": None
    }
    page_refresh = False

    dict_outputs = parse_output_information()

    if not form_mod_pid_base.validate():
        messages["error"] = form_error_messages(
            form_mod_pid_base, messages["error"])

    mod_pid = PID.query.filter(
        PID.unique_id == form_mod_pid_base.function_id.data).first()

    mod_pid.name = form_mod_pid_base.name.data
    messages["name"] = form_mod_pid_base.name.data
    mod_pid.measurement = form_mod_pid_base.measurement.data
    mod_pid.direction = form_mod_pid_base.direction.data
    mod_pid.period = form_mod_pid_base.period.data
    mod_pid.log_level_debug = form_mod_pid_base.log_level_debug.data
    mod_pid.start_offset = form_mod_pid_base.start_offset.data
    mod_pid.max_measure_age = form_mod_pid_base.max_measure_age.data
    mod_pid.setpoint = form_mod_pid_base.setpoint.data
    mod_pid.band = abs(form_mod_pid_base.band.data)
    mod_pid.send_lower_as_negative = form_mod_pid_base.send_lower_as_negative.data
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

        #
        # Handle Raise Output Settings
        #
        if form_mod_pid_base.raise_output_id.data:
            output_id = form_mod_pid_base.raise_output_id.data.split(",")[0]
            channel_id = form_mod_pid_base.raise_output_id.data.split(",")[1]
            raise_output_type = Output.query.filter(
                Output.unique_id == output_id).first().output_type

            def default_raise_output_settings(mod):
                if mod.raise_output_type == 'on_off':
                    mod.raise_min_duration = 0
                    mod.raise_max_duration = 0
                    mod.raise_min_off_duration = 0
                elif mod.raise_output_type == 'pwm':
                    mod.raise_min_duration = 2
                    mod.raise_max_duration = 98
                elif mod.raise_output_type == 'value':
                    mod.raise_min_duration = 0
                    mod.raise_max_duration = 0
                elif mod.raise_output_type == 'volume':
                    mod.raise_min_duration = 0
                    mod.raise_max_duration = 0
                return mod

            raise_output_id_changed = False
            if mod_pid.raise_output_id != form_mod_pid_base.raise_output_id.data:
                mod_pid.raise_output_id = form_mod_pid_base.raise_output_id.data
                raise_output_id_changed = True
                page_refresh = True

            # Output ID changed
            if ('output_types' in dict_outputs[raise_output_type] and
                    mod_pid.raise_output_id and
                    raise_output_id_changed):

                if len(dict_outputs[raise_output_type]['output_types']) == 1:
                    mod_pid.raise_output_type = dict_outputs[raise_output_type]['output_types'][0]
                else:
                    mod_pid.raise_output_type = None

                mod_pid = default_raise_output_settings(mod_pid)

            # Output ID unchanged
            elif ('output_types' in dict_outputs[raise_output_type] and
                  mod_pid.raise_output_id and
                  not raise_output_id_changed):

                if (not mod_pid.raise_output_type or
                        mod_pid.raise_output_type != form_mod_pid_base.raise_output_type.data):
                    if len(dict_outputs[raise_output_type]['output_types']) > 1:
                        mod_pid.raise_output_type = form_mod_pid_base.raise_output_type.data
                    mod_pid = default_raise_output_settings(mod_pid)
                elif mod_pid.raise_output_type == 'on_off':
                    if not form_mod_pid_output_raise.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_output_raise, messages["error"])
                    else:
                        mod_pid.raise_min_duration = form_mod_pid_output_raise.raise_min_duration.data
                        mod_pid.raise_max_duration = form_mod_pid_output_raise.raise_max_duration.data
                        mod_pid.raise_min_off_duration = form_mod_pid_output_raise.raise_min_off_duration.data
                elif mod_pid.raise_output_type == 'pwm':
                    if not form_mod_pid_pwm_raise.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_pwm_raise, messages["error"])
                    else:
                        mod_pid.raise_min_duration = form_mod_pid_pwm_raise.raise_min_duty_cycle.data
                        mod_pid.raise_max_duration = form_mod_pid_pwm_raise.raise_max_duty_cycle.data
                        mod_pid.raise_always_min_pwm = form_mod_pid_pwm_raise.raise_always_min_pwm.data
                elif mod_pid.raise_output_type == 'value':
                    if not form_mod_pid_value_raise.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_value_raise, messages["error"])
                    else:
                        mod_pid.raise_min_duration = form_mod_pid_value_raise.raise_min_amount.data
                        mod_pid.raise_max_duration = form_mod_pid_value_raise.raise_max_amount.data
                elif mod_pid.raise_output_type == 'volume':
                    if not form_mod_pid_volume_raise.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_volume_raise, messages["error"])
                    else:
                        mod_pid.raise_min_duration = form_mod_pid_volume_raise.raise_min_amount.data
                        mod_pid.raise_max_duration = form_mod_pid_volume_raise.raise_max_amount.data
        else:
            if mod_pid.raise_output_id is not None:
                page_refresh = True
            mod_pid.raise_output_id = None

        #
        # Handle Lower Output Settings
        #
        if form_mod_pid_base.lower_output_id.data:
            output_id = form_mod_pid_base.lower_output_id.data.split(",")[0]
            channel_id = form_mod_pid_base.lower_output_id.data.split(",")[1]
            lower_output_type = Output.query.filter(
                Output.unique_id == output_id).first().output_type

            def default_lower_output_settings(mod):
                if mod.lower_output_type == 'on_off':
                    mod.lower_min_duration = 0
                    mod.lower_max_duration = 0
                    mod.lower_min_off_duration = 0
                elif mod.lower_output_type == 'pwm':
                    mod.lower_min_duration = 2
                    mod.lower_max_duration = 98
                elif mod.lower_output_type == 'value':
                    mod.lower_min_duration = 0
                    mod.lower_max_duration = 0
                elif mod.lower_output_type == 'volume':
                    mod.lower_min_duration = 0
                    mod.lower_max_duration = 0
                return mod

            lower_output_id_changed = False
            if mod_pid.lower_output_id != form_mod_pid_base.lower_output_id.data:
                mod_pid.lower_output_id = form_mod_pid_base.lower_output_id.data
                lower_output_id_changed = True
                page_refresh = True

            # Output ID changed
            if ('output_types' in dict_outputs[lower_output_type] and
                    mod_pid.lower_output_id and
                    lower_output_id_changed):

                if len(dict_outputs[lower_output_type]['output_types']) == 1:
                    mod_pid.lower_output_type = dict_outputs[lower_output_type]['output_types'][0]
                else:
                    mod_pid.lower_output_type = None

                mod_pid = default_lower_output_settings(mod_pid)

            # Output ID unchanged
            elif ('output_types' in dict_outputs[lower_output_type] and
                    mod_pid.lower_output_id and
                    not lower_output_id_changed):

                if (not mod_pid.lower_output_type or
                        mod_pid.lower_output_type != form_mod_pid_base.lower_output_type.data):
                    if len(dict_outputs[lower_output_type]['output_types']) > 1:
                        mod_pid.lower_output_type = form_mod_pid_base.lower_output_type.data
                    mod_pid = default_lower_output_settings(mod_pid)
                elif mod_pid.lower_output_type == 'on_off':
                    if not form_mod_pid_output_lower.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_output_lower, messages["error"])
                    else:
                        mod_pid.lower_min_duration = form_mod_pid_output_lower.lower_min_duration.data
                        mod_pid.lower_max_duration = form_mod_pid_output_lower.lower_max_duration.data
                        mod_pid.lower_min_off_duration = form_mod_pid_output_lower.lower_min_off_duration.data
                elif mod_pid.lower_output_type == 'pwm':
                    if not form_mod_pid_pwm_lower.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_pwm_lower, messages["error"])
                    else:
                        mod_pid.lower_min_duration = form_mod_pid_pwm_lower.lower_min_duty_cycle.data
                        mod_pid.lower_max_duration = form_mod_pid_pwm_lower.lower_max_duty_cycle.data
                        mod_pid.lower_always_min_pwm = form_mod_pid_pwm_lower.lower_always_min_pwm.data
                elif mod_pid.lower_output_type == 'value':
                    if not form_mod_pid_value_lower.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_value_lower, messages["error"])
                    else:
                        mod_pid.lower_min_duration = form_mod_pid_value_lower.lower_min_amount.data
                        mod_pid.lower_max_duration = form_mod_pid_value_lower.lower_max_amount.data
                elif mod_pid.lower_output_type == 'volume':
                    if not form_mod_pid_volume_lower.validate():
                        messages["error"] = form_error_messages(
                            form_mod_pid_volume_lower, messages["error"])
                    else:
                        mod_pid.lower_min_duration = form_mod_pid_volume_lower.lower_min_amount.data
                        mod_pid.lower_max_duration = form_mod_pid_volume_lower.lower_max_amount.data
        else:
            if mod_pid.lower_output_id is not None:
                page_refresh = True
            mod_pid.lower_output_id = None

    if (mod_pid.raise_output_id and mod_pid.lower_output_id and
            mod_pid.raise_output_id == mod_pid.lower_output_id):
        messages["error"].append(gettext("Raise and lower outputs cannot be the same"))

    try:
        if not messages["error"]:
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller=TRANSLATIONS['pid']['title']))

            # If the controller is active or paused, refresh variables in thread
            if mod_pid.is_activated:
                control = DaemonControl()
                return_value = control.pid_mod(form_mod_pid_base.function_id.data)
                flash("PID Controller settings refresh response: "
                      "{resp}".format(resp=return_value), "success")
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages, page_refresh


def pid_del(pid_id):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        pid = PID.query.filter(
            PID.unique_id == pid_id).first()
        if pid.is_activated:
            pid_deactivate(pid_id)

        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == pid_id).all()

        for each_measurement in device_measurements:
            delete_entry_with_id(
                DeviceMeasurements,
                each_measurement.unique_id,
                flash_message=False)

        delete_entry_with_id(
            PID, pid_id, flash_message=False)

        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['delete']['title'],
            controller=TRANSLATIONS['pid']['title']))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def has_required_pid_values(pid_id, messages):
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()

    if not pid.measurement:
        messages["error"].append("A valid Measurement is required")
    else:
        device_unique_id = pid.measurement.split(',')[0]
        input_dev = Input.query.filter(
            Input.unique_id == device_unique_id).first()
        function = CustomController.query.filter(
            CustomController.unique_id == device_unique_id).first()
        if not input_dev and not function:
            messages["error"].append("A valid controller/measurement is required")

    if not pid.raise_output_id and not pid.lower_output_id:
        messages["error"].append("A Raise Output and/or a Lower Output is required")

    return messages


def pid_activate(pid_id):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    messages = has_required_pid_values(pid_id, messages)

    # Check if associated sensor is activated
    pid = PID.query.filter(
        PID.unique_id == pid_id).first()

    device_unique_id = pid.measurement.split(',')[0]
    input_dev = Input.query.filter(
        Input.unique_id == device_unique_id).first()

    if input_dev and not input_dev.is_activated:
        messages["error"].append(gettext(
            "Cannot activate PID controller if the associated Input "
            "controller is inactive"))

    if ((pid.direction == 'both' and not (pid.lower_output_id and pid.raise_output_id)) or
            (pid.direction == 'lower' and not pid.lower_output_id) or
            (pid.direction == 'raise' and not pid.raise_output_id)):
        messages["error"].append(gettext(
            "Cannot activate PID controller if raise and/or lower output IDs "
            "are not selected"))

    time.sleep(1)
    messages = controller_activate_deactivate(
        messages, 'activate', 'PID', pid_id, flash_message=False)

    if not messages["error"]:
        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['activate']['title'],
            controller=TRANSLATIONS['pid']['title']))

    return messages


def pid_deactivate(pid_id):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    pid = PID.query.filter(
        PID.unique_id == pid_id).first()
    if not pid:
        messages["error"].append("PID Controller not found")

    if not pid.is_activated:
        messages["error"].append("PID Controller not active")

    if not messages["error"]:
        pid.is_activated = False
        pid.is_held = False
        pid.is_paused = False
        pid.method_start_time = None
        pid.method_end_time = None
        db.session.commit()

        time.sleep(1)
        messages = controller_activate_deactivate(
            messages, 'deactivate', 'PID', pid_id, flash_message=False)

    if not messages["error"]:
        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['deactivate']['title'],
            controller=TRANSLATIONS['pid']['title']))

    return messages


def pid_manipulate(pid_id, action):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    if action not in ['Hold', 'Pause', 'Resume']:
        messages["error"].append(
            '{}: {}'.format(TRANSLATIONS['invalid']['title'], action))
        return messages

    try:
        control = DaemonControl()
        return_value = None
        if action == 'Hold':
            return_value = control.pid_hold(pid_id)
        elif action == 'Pause':
            return_value = control.pid_pause(pid_id)
        elif action == 'Resume':
            return_value = control.pid_resume(pid_id)
        if return_value:
            messages["success"].append(
                '{}: {}: {}: {}'.format(
                    TRANSLATIONS['controller']['title'],
                    TRANSLATIONS['pid']['title'],
                    action,
                    return_value))
    except Exception as err:
        messages["error"].append(
            "{}: {}: {}".format(
                TRANSLATIONS['Error']['title'],
                TRANSLATIONS['PID']['title'], err))

    return messages
