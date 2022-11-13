# -*- coding: utf-8 -*-
import importlib
import json
import logging
import os
from collections import OrderedDict
from datetime import datetime

import flask_login
import sqlalchemy
from flask import flash
from flask import redirect
from flask import request
from flask_babel import gettext
from importlib_metadata import version
from sqlalchemy import and_

from mycodo.config import CAMERA_INFO
from mycodo.config import DEPENDENCIES_GENERAL
from mycodo.config import FUNCTION_INFO
from mycodo.config import METHOD_INFO
from mycodo.config import PATH_CAMERAS
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.config_devices_units import UNITS
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import Dashboard
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Role
from mycodo.databases.models import Trigger
from mycodo.databases.models import User
from mycodo.databases.models import Widget
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.utils.actions import parse_action_information
from mycodo.utils.functions import parse_function_information
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import dpkg_package_exists
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.system_pi import str_is_float
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger(__name__)

#
# Custom options
#

def custom_options_return_string(error, dict_options, mod_dev, request_form):
    # Custom options
    list_options = []

    # TODO: name same name in next major release
    if hasattr(mod_dev, 'device'):
        device = mod_dev.device
    elif hasattr(mod_dev, 'output_type'):
        device = mod_dev.output_type
    else:
        logger.error("Unknown device")
        return

    if 'custom_options' in dict_options[device]:
        for each_option in dict_options[device]['custom_options']:
            if 'id' not in each_option:
                continue

            null_value = True

            for key in request_form.keys():
                if each_option['id'] == key:
                    constraints_pass = True
                    constraints_errors = []
                    value = None

                    if each_option['type'] == 'float':
                        if str_is_float(request_form.get(key)):
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_dev) = each_option['constraints_pass'](
                                    mod_dev, float(request_form.get(key)))
                            if constraints_pass:
                                value = float(request_form.get(key))
                        elif 'required' in each_option and not each_option['required']:
                            value = None
                        else:
                            error.append(
                                "{name} must represent a float/decimal value "
                                "(submitted '{value}')".format(
                                    name=each_option['name'],
                                    value=request_form.get(key)))

                    elif each_option['type'] == 'integer':
                        if is_int(request_form.get(key)):
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_dev) = each_option['constraints_pass'](
                                    mod_dev, int(request_form.get(key)))
                            if constraints_pass:
                                value = int(request_form.get(key))
                        elif 'required' in each_option and not each_option['required']:
                            value = None
                        else:
                            error.append(
                                "{name} must represent an integer value "
                                "(submitted '{value}')".format(
                                    name=each_option['name'],
                                    value=request_form.get(key)))

                    elif each_option['type'] in [
                            'text',
                            'select',
                            'select_custom_choices',
                            'select_measurement',
                            'select_channel',
                            'select_measurement_channel',
                            'select_type_measurement',
                            'select_type_unit',
                            'select_device']:
                        if 'constraints_pass' in each_option:
                            (constraints_pass,
                             constraints_errors,
                             mod_dev) = each_option['constraints_pass'](
                                mod_dev, request_form.get(key))
                        if constraints_pass:
                            value = request_form.get(key)

                    elif each_option['type'] == 'select_multi_measurement':
                        if 'constraints_pass' in each_option:
                            (constraints_pass,
                             constraints_errors,
                             mod_dev) = each_option['constraints_pass'](
                                mod_dev, request_form.get(key))
                        if constraints_pass:
                            value = ",".join(request_form.getlist(key))

                    elif each_option['type'] == 'bool':
                        value = bool(request_form.get(key))

                    for each_error in constraints_errors:
                        error.append(
                            "Error: {name}: {error}".format(
                                name=each_option['name'],
                                error=each_error))

                    if value is not None:
                        null_value = False
                        option = '{id},{value}'.format(
                            id=key,
                            value=value)
                        list_options.append(option)

            if (request_form and
                    each_option['type'] == 'bool' and
                    each_option['id'] not in request_form.keys()):
                option = '{id},{value}'.format(id=each_option['id'], value=False)
                list_options.append(option)

            elif null_value:
                option = '{id},'.format(id=each_option['id'])
                list_options.append(option)

    return error, ';'.join(list_options)


def custom_options_return_json(
        error,
        dict_options,
        request_form=None,
        mod_dev=None,
        device=None,
        use_defaults=False,
        custom_options=None):
    # Custom options
    if custom_options:
        dict_options_return = custom_options
    else:
        dict_options_return = {}

    # TODO: name these the same in next major release
    if mod_dev is None:
        pass
    elif hasattr(mod_dev, 'graph_type'):
        device = mod_dev.graph_type
    elif hasattr(mod_dev, 'device'):
        device = mod_dev.device
    elif hasattr(mod_dev, 'output_type'):
        device = mod_dev.output_type
    elif hasattr(mod_dev, 'action_type'):
        device = mod_dev.action_type
    else:
        logger.error("Unknown device")
        return None, None

    if 'custom_options' in dict_options[device]:
        for each_option in dict_options[device]['custom_options']:
            if 'id' not in each_option:
                continue

            null_value = True

            if request_form:
                for key in request_form.keys():
                    if each_option['id'] == key:
                        constraints_pass = True
                        constraints_errors = []
                        value = None

                        if each_option['type'] == 'float':
                            if str_is_float(request_form.get(key)):
                                if 'constraints_pass' in each_option:
                                    (constraints_pass,
                                     constraints_errors,
                                     mod_dev) = each_option['constraints_pass'](
                                        mod_dev, float(request_form.get(key)))
                                if constraints_pass:
                                    value = float(request_form.get(key))
                            elif 'required' in each_option and not each_option['required']:
                                value = None
                            else:
                                error.append(
                                    "{name} must represent a float/decimal value "
                                    "(submitted '{value}')".format(
                                        name=each_option['name'],
                                        value=request_form.get(key)))

                        elif each_option['type'] == 'integer':
                            if is_int(request_form.get(key)):
                                if 'constraints_pass' in each_option:
                                    (constraints_pass,
                                     constraints_errors,
                                     mod_dev) = each_option['constraints_pass'](
                                        mod_dev, int(request_form.get(key)))
                                if constraints_pass:
                                    value = int(request_form.get(key))
                            elif 'required' in each_option and not each_option['required']:
                                value = None
                            else:
                                error.append(
                                    "{name} must represent an integer value "
                                    "(submitted '{value}')".format(
                                        name=each_option['name'],
                                        value=request_form.get(key)))

                        elif each_option['type'] in [
                                'multiline_text',
                                'text',
                                'select',
                                'select_custom_choices',
                                'select_measurement',
                                'select_measurement_from_this_input',
                                'select_channel',
                                'select_measurement_channel',
                                'select_type_measurement',
                                'select_type_unit',
                                'select_device']:
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_dev) = each_option['constraints_pass'](
                                    mod_dev, request_form.get(key))
                            if constraints_pass:
                                value = request_form.get(key)

                        elif each_option['type'] == 'select_multi_measurement':
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_dev) = each_option['constraints_pass'](
                                    mod_dev, request_form.get(key))
                            if constraints_pass:
                                value = request_form.getlist(key)

                        elif each_option['type'] == 'bool':
                            value = bool(request_form.get(key))

                        for each_error in constraints_errors:
                            error.append(
                                "Error: {name}: {error}".format(
                                    name=each_option['name'],
                                    error=each_error))

                        if value is not None:
                            null_value = False
                            dict_options_return[key] = value

            if (request_form and
                    each_option['type'] == 'bool' and
                    each_option['id'] not in request_form.keys()):
                dict_options_return[each_option['id']] = False

            elif null_value:
                if use_defaults and 'default_value' in each_option:
                    dict_options_return[each_option['id']] = each_option['default_value']
                elif each_option['type'] == "select_multi_measurement":
                    dict_options_return[each_option['id']] = ""
                else:
                    dict_options_return[each_option['id']] = None

    return error, json.dumps(dict_options_return)


def custom_channel_options_return_json(
        error,
        dict_options,
        request_form,
        device_id,
        channel,
        mod_dev=None,
        device=None,
        use_defaults=False):
    # Custom channel_options
    dict_options_return = {}

    # TODO: name same name in next major release
    if mod_dev is None:
        pass
    elif hasattr(mod_dev, 'graph_type'):
        device = mod_dev.graph_type
    elif hasattr(mod_dev, 'device'):
        device = mod_dev.device
    elif hasattr(mod_dev, 'output_type'):
        device = mod_dev.output_type
    else:
        logger.error("Unknown device")
        return None, None

    if 'custom_channel_options' in dict_options[device]:
        for each_option in dict_options[device]['custom_channel_options']:
            if 'id' not in each_option:
                continue

            if each_option['id'] not in dict_options_return:
                dict_options_return[each_option['id']] = OrderedDict()

            null_value = True

            if request_form:
                for key in request_form.keys():
                    key_str = "{}_{}_{}".format(device_id, channel, each_option['id'])
                    if key_str == key:
                        # logger.error("key_str: {}".format(key_str))
                        # logger.error("val: {}".format(request_form.get(key)))
                        constraints_pass = True
                        constraints_errors = []
                        value = None

                        if each_option['type'] == 'float':
                            if str_is_float(request_form.get(key)):
                                if 'constraints_pass' in each_option:
                                    (constraints_pass,
                                     constraints_errors,
                                     mod_dev) = each_option['constraints_pass'](
                                        mod_dev, float(request_form.get(key)))
                                if constraints_pass:
                                    value = float(request_form.get(key))
                            elif 'required' in each_option and not each_option['required']:
                                value = None
                            else:
                                error.append(
                                    "{name} must represent a float/decimal value "
                                    "(submitted '{value}')".format(
                                        name=each_option['name'],
                                        value=request_form.get(key)))

                        elif each_option['type'] == 'integer':
                            if is_int(request_form.get(key)):
                                if 'constraints_pass' in each_option:
                                    (constraints_pass,
                                     constraints_errors,
                                     mod_dev) = each_option['constraints_pass'](
                                        mod_dev, int(request_form.get(key)))
                                if constraints_pass:
                                    value = int(request_form.get(key))
                            elif 'required' in each_option and not each_option['required']:
                                value = None
                            else:
                                error.append(
                                    "{name} must represent an integer value "
                                    "(submitted '{value}')".format(
                                        name=each_option['name'],
                                        value=request_form.get(key)))

                        elif each_option['type'] in ['select', 'select_custom_choices']:
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_dev) = each_option['constraints_pass'](
                                    mod_dev, request_form.get(key))
                            if constraints_pass:
                                value = request_form.get(key)
                                if is_int(request_form.get(key)):
                                    value = int(request_form.get(key))
                                elif str_is_float(request_form.get(key)):
                                    value = float(request_form.get(key))

                        elif each_option['type'] in [
                                'multiline_text',
                                'text',
                                'select_measurement',
                                'select_channel',
                                'select_measurement_channel',
                                'select_type_measurement',
                                'select_type_unit',
                                'select_device']:
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_dev) = each_option['constraints_pass'](
                                    mod_dev, request_form.get(key))
                            if constraints_pass:
                                value = request_form.get(key)

                        elif each_option['type'] == 'select_multi_measurement':
                            if 'constraints_pass' in each_option:
                                (constraints_pass,
                                 constraints_errors,
                                 mod_dev) = each_option['constraints_pass'](
                                    mod_dev, request_form.get(key))
                            if constraints_pass:
                                value = request_form.getlist(key)

                        elif each_option['type'] == 'bool':
                            value = bool(request_form.get(key))

                        for each_error in constraints_errors:
                            error.append(
                                "Error: {name}: {error}".format(
                                    name=each_option['name'],
                                    error=each_error))

                        if value is not None:
                            null_value = False
                            dict_options_return[each_option['id']] = value

            if (request_form and
                    each_option['type'] == 'bool' and
                    "{}_{}_{}".format(device_id, channel, each_option['id']) not in request_form.keys() and
                    not use_defaults):
                dict_options_return[each_option['id']] = False

            elif null_value:
                if use_defaults and 'default_value' in each_option:
                    # If a select type has cast_value set, cast the value as that type
                    if (each_option['type'] in ['select', 'select_custom_choices'] and
                            'cast_value' in each_option and
                            each_option['default_value'] is not None):
                        if each_option['cast_value'] == 'integer':
                            dict_options_return[each_option['id']] = int(each_option['default_value'])
                        elif each_option['cast_value'] == 'float':
                            dict_options_return[each_option['id']] = float(each_option['default_value'])
                        elif each_option['cast_value'] == 'bool':
                            dict_options_return[each_option['id']] = bool(each_option['default_value'])
                    else:
                        dict_options_return[each_option['id']] = each_option['default_value']
                elif each_option['type'] == "select_multi_measurement":
                    dict_options_return[each_option['id']] = ""
                else:
                    dict_options_return[each_option['id']] = None

    return error, json.dumps(dict_options_return)


#
# Activate/deactivate controller
#

def check_for_valid_unit_and_conversion(device_id, error):
    try:
        if DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == device_id).count():
            measurements = DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == device_id)
        else:
            measurements = None
            error.append("Could not find measurements")

        if measurements:
            for each_meas in measurements:
                # Check that unit is set
                if each_meas.unit in ['', None]:
                    error.append("Unit not set for channel {chan}".format(
                        chan=each_meas.channel))

                # If conversion ID set, check if it's valid
                if each_meas.conversion_id:
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == each_meas.conversion_id).count()
                    if not conversion:
                        error.append(
                            "Invalid conversion ID {cid} "
                            "for measurement with ID {meas}".format(
                                cid=each_meas.conversion_id,
                                meas=each_meas.unique_id))
    except Exception as err:
        error.append(err)
        logger.exception("check_for_valid_unit_and_conversion")

    return error


def controller_activate_deactivate(messages,
                                   controller_action,
                                   controller_type,
                                   controller_id,
                                   flash_message=True):
    """
    Activate or deactivate controller

    :param messages: messages to return to the user
    :type messages: dict of list of strings
    :param controller_action: Activate or deactivate
    :type controller_action: str
    :param controller_type: The controller type (Conditional, Input, PID, Trigger, Function)
    :type controller_type: str
    :param controller_id: Controller with ID to activate or deactivate
    :type controller_id: str
    """
    if not user_has_permission('edit_controllers'):
        messages["error"].append(
            "Insufficient permissions to activate/deactivate controller")
        return messages

    activated = bool(controller_action == 'activate')

    mod_controller = None
    if controller_type == 'Conditional':
        mod_controller = Conditional.query.filter(
            Conditional.unique_id == controller_id).first()
    elif controller_type == 'Input':
        mod_controller = Input.query.filter(
            Input.unique_id == controller_id).first()
        if activated:
            messages["error"] = check_for_valid_unit_and_conversion(
                controller_id, messages["error"])
    elif controller_type == 'PID':
        mod_controller = PID.query.filter(
            PID.unique_id == controller_id).first()
        if activated:
            messages["error"] = check_for_valid_unit_and_conversion(
                controller_id, messages["error"])
    elif controller_type == 'Trigger':
        mod_controller = Trigger.query.filter(
            Trigger.unique_id == controller_id).first()
    elif controller_type == 'Function':
        mod_controller = CustomController.query.filter(
            CustomController.unique_id == controller_id).first()

    if mod_controller is None:
        messages["error"].append("{type} Controller {id} doesn't exist".format(
            type=controller_type, id=controller_id))
        return messages

    try:
        if not messages["error"]:
            mod_controller.is_activated = activated
            db.session.commit()
    except Exception as except_msg:
        messages["error"].append(
            '{}: {}'.format(TRANSLATIONS['error']['title'], except_msg))

    try:
        if not messages["error"]:
            control = DaemonControl()
            if controller_action == 'activate':
                return_values = control.controller_activate(controller_id)
            else:
                return_values = control.controller_deactivate(controller_id)
            if flash_message:
                if return_values[0]:
                    messages["error"].append(return_values[1])
                else:
                    messages["success"].append(return_values[1])
    except Exception as except_msg:
        messages["error"].append(
            '{}: {}'.format(TRANSLATIONS['error']['title'], except_msg))

    if flash_message:
        for each_error in messages["error"]:
            flash(each_error, 'error')

    return messages


#
# Choices
#

def choices_controller_ids():
    """populate form multi-select choices from Controller IDs."""
    choices = []
    for each_input in Input.query.all():
        display = '[Input {id:02d}] {name}'.format(
            id=each_input.id,
            name=each_input.name)
        choices.append({'value': each_input.unique_id, 'item': display})
    for each_pid in PID.query.all():
        display = '[PID {id:02d}] {name}'.format(
            id=each_pid.id,
            name=each_pid.name)
        choices.append({'value': each_pid.unique_id, 'item': display})
    for each_cond in Conditional.query.all():
        display = '[Conditional {id:02d}] {name}'.format(
            id=each_cond.id,
            name=each_cond.name)
        choices.append({'value': each_cond.unique_id, 'item': display})
    for each_trigger in Trigger.query.all():
        display = '[Trigger {id:02d}] {name}'.format(
            id=each_trigger.id,
            name=each_trigger.name)
        choices.append({'value': each_trigger.unique_id, 'item': display})
    for each_custom in CustomController.query.all():
        display = '[Function {id:02d}] {name}'.format(
            id=each_custom.id,
            name=each_custom.name)
        choices.append({'value': each_custom.unique_id, 'item': display})
    return choices


def choices_custom_functions():
    """populate form multi-select choices from Function entries."""
    choices = []
    dict_controllers = parse_function_information()
    list_controllers_sorted = generate_form_controller_list(dict_controllers)
    for each_custom in list_controllers_sorted:
        choices.append({
            'value': each_custom,
            'item': dict_controllers[each_custom]['function_name']
        })
    return choices


def choices_inputs(inputs, dict_units, dict_measurements):
    """populate form multi-select choices from Input entries."""
    choices = []
    for each_input in inputs:
        choices = form_input_choices(
            choices, each_input, dict_units, dict_measurements)
    return choices


def choices_input_devices(input_dev):
    """populate form multi-select choices from Output entries."""
    choices = []
    for each_input in input_dev:
        choices = form_input_choices_devices(choices, each_input)
    return choices


def choices_actions(actions, dict_units, dict_measurements):
    """populate form multi-select choices from Action entries."""
    choices = []
    for each_function in actions:
        choices = form_function_choices(
            choices, each_function, dict_units, dict_measurements)
    return choices


def choices_functions(functions, dict_units, dict_measurements):
    """populate form multi-select choices from Function entries."""
    choices = []
    for each_function in functions:
        choices = form_function_choices(
            choices, each_function, dict_units, dict_measurements)
    return choices


def choices_measurements(measurements):
    """populate form multi-select choices from Measurement entries."""
    choices = []
    for each_meas in measurements:
        value = '{meas}'.format(
            meas=each_meas.name_safe)
        display = '{name} ({units})'.format(
            name=each_meas.name,
            units=each_meas.units)
        choices.append({'value': value, 'item': display})
    for each_meas, each_info in MEASUREMENTS.items():
        value = '{meas}'.format(
            meas=each_meas)
        display = '{name} ({units})'.format(
            name=each_info['name'],
            units=",".join(each_info['units']))
        choices.append({'value': value, 'item': display})

    return choices


def choices_measurements_units(measurements, units):
    dict_measurements = add_custom_measurements(measurements)
    dict_units = add_custom_units(units)

    # Sort dictionary by keys
    sorted_keys = sorted(list(dict_measurements), key=lambda s: s.casefold())
    sorted_dict_measurements = []
    for each_key in sorted_keys:
        sorted_dict_measurements.append(
            {'key': each_key, 'measurement': dict_measurements[each_key]})

    choices = []
    for each_meas in sorted_dict_measurements:
        for each_unit in each_meas['measurement']['units']:
            try:
                value = '{meas},{unit}'.format(
                    meas=each_meas['key'], unit=each_unit)
                display = '{meas}: {unit_name}'.format(
                    meas=each_meas['measurement']['name'],
                    unit_name=dict_units[each_unit]['name'])
                if dict_units[each_unit]['unit']:
                    display += ' ({unit})'.format(
                        unit=dict_units[each_unit]['unit'])
                choices.append({'value': value, 'item': display})
            except Exception as e:
                logger.exception(
                    "Error in choices_measurements_units(): {}".format(e))

    return choices


def choices_outputs(output, table_output_channel, dict_outputs, dict_units, dict_measurements):
    """populate form multi-select choices from Output entries."""
    choices = []
    for each_output in output:
        output_channels = table_output_channel.query.filter(
            table_output_channel.output_id == each_output.unique_id).all()
        choices = form_output_choices(
            choices, each_output, output_channels, dict_outputs, dict_units, dict_measurements)
    return choices


def choices_outputs_channels_measurements(
        output, table_output_channel, dict_outputs, dict_units, dict_measurements):
    """populate form multi-select choices from Output entries."""
    choices = []
    for each_output in output:
        output_channels = table_output_channel.query.filter(
            table_output_channel.output_id == each_output.unique_id).all()
        choices = form_output_channel_measurement_choices(
            choices, each_output, output_channels, dict_outputs, dict_units, dict_measurements)
    return choices


def choices_outputs_channels(output, output_channel, dict_outputs):
    """populate form multi-select choices from Output entries."""
    choices = []
    for each_output in output:
        for each_channel in output_channel:
            if each_output.unique_id == each_channel.output_id:
                choices = form_output_channel_choices(
                    choices, each_output, each_channel, dict_outputs)
    return choices


def choices_output_devices(output):
    """populate form multi-select choices from Output entries."""
    choices = []
    for each_output in output:
        choices = form_output_choices_devices(choices, each_output)
    return choices


def choices_outputs_pwm(output, table_output_channel, dict_outputs, dict_units, dict_measurements):
    """populate form multi-select choices from Output entries."""
    choices = []
    for each_output in output:
        if ('output_types' in dict_outputs[each_output.output_type] and
                'pwm' in dict_outputs[each_output.output_type]['output_types']):
            output_channels = table_output_channel.query.filter(
                table_output_channel.output_id == each_output.unique_id).all()
            choices = form_output_choices(
                choices, each_output, output_channels, dict_outputs, dict_units, dict_measurements)
    return choices


def choices_pids(pid, dict_units, dict_measurements):
    """populate form multi-select choices from PID entries."""
    choices = []
    for each_pid in pid:
        choices = form_pid_choices(
            choices, each_pid, dict_units, dict_measurements)
    return choices


def choices_pids_devices(pid):
    """populate form multi-select choices from PID device entries."""
    choices = []
    for each_pid in pid:
        choices = form_pid_choices_devices(choices, each_pid)
    return choices


def choices_methods(method):
    """populate form multi-select choices from Method entries."""
    choices = []
    for each_method in method:
        choices = form_method_choices(choices, each_method)
    return choices


def choices_tags(tags):
    """populate form multi-select choices from Tag entries."""
    choices = []
    for each_tag in tags:
        choices = form_tag_choices(choices, each_tag)
    return choices


def choices_units(units):
    """populate form multi-select choices from Units entries."""
    choices = []
    for each_unit, each_info in UNITS.items():
        if each_info['name']:
            value = '{unit}'.format(
                unit=each_unit)
            unit = ''
            if each_info['unit']:
                unit = ' ({})'.format(each_info['unit'])
            display = '{name}{unit}'.format(
                name=each_info['name'],
                unit=unit)
            choices.append({'value': value, 'item': display})
    for each_unit in units:
        value = '{unit}'.format(
            unit=each_unit.name_safe)
        display = '{name} ({unit})'.format(
            name=each_unit.name,
            unit=each_unit.unit)
        choices.append({'value': value, 'item': display})

    choices.sort(key=lambda item: item.get("item"))

    return choices


def form_input_choices(choices, each_input, dict_units, dict_measurements):
    device_measurements = DeviceMeasurements.query.filter(
        DeviceMeasurements.device_id == each_input.unique_id).all()

    for each_measure in device_measurements:
        conversion = Conversion.query.filter(
            Conversion.unique_id == each_measure.conversion_id).first()
        channel, unit, measurement = return_measurement_info(
            each_measure, conversion)

        if unit:
            value = '{input_id},{meas_id}'.format(
                input_id=each_input.unique_id,
                meas_id=each_measure.unique_id)

            display_unit = find_name_unit(
                dict_units, unit)
            display_measurement = find_name_measurement(
                dict_measurements, measurement)

            if isinstance(channel, int):
                channel_num = ' CH{cnum}'.format(cnum=channel)
            else:
                channel_num = ''

            if each_measure.name:
                channel_name = ' ({name})'.format(name=each_measure.name)
            else:
                channel_name = ''

            if display_measurement and display_unit:
                measurement_unit = ' {meas} ({unit})'.format(
                    meas=display_measurement, unit=display_unit)
            elif display_measurement:
                measurement_unit = ' {meas}'.format(
                    meas=display_measurement)
            else:
                measurement_unit = ' ({unit})'.format(unit=display_unit)

            display = '[Input {id:02d}{chan_num}] {i_name}{chan_name}{meas}'.format(
                id=each_input.id,
                i_name=each_input.name,
                chan_num=channel_num,
                chan_name=channel_name,
                meas=measurement_unit)

            choices.append({'value': value, 'item': display})

    return choices


def form_input_choices_devices(choices, each_input):
    value = '{id},input'.format(id=each_input.unique_id)
    display = '[Input {id:02d}] {name}'.format(
        id=each_input.id,
        name=each_input.name)
    choices.append({'value': value, 'item': display})
    return choices


def form_function_choices(choices, each_function, dict_units, dict_measurements):
    device_measurements = DeviceMeasurements.query.filter(
        DeviceMeasurements.device_id == each_function.unique_id).all()

    for each_measure in device_measurements:
        conversion = Conversion.query.filter(
            Conversion.unique_id == each_measure.conversion_id).first()
        channel, unit, measurement = return_measurement_info(
            each_measure, conversion)

        if unit:
            value = '{function_id},{meas_id}'.format(
                function_id=each_function.unique_id,
                meas_id=each_measure.unique_id)

            display_unit = find_name_unit(
                dict_units, unit)
            display_measurement = find_name_measurement(
                dict_measurements, measurement)

            if each_measure.name:
                channel_info = 'CH{cnum} ({cname})'.format(
                    cnum=channel, cname=each_measure.name)
            else:
                channel_info = 'CH{cnum}'.format(cnum=channel)

            if display_measurement and display_unit:
                measurement_unit = '{meas} ({unit})'.format(
                    meas=display_measurement, unit=display_unit)
            elif display_measurement:
                measurement_unit = '{meas}'.format(
                    meas=display_measurement)
            else:
                measurement_unit = '({unit})'.format(unit=display_unit)

            display = '[Function {id:02d}] {i_name} {chan} {meas}'.format(
                id=each_function.id,
                i_name=each_function.name,
                chan=channel_info,
                meas=measurement_unit)
            choices.append({'value': value, 'item': display})

    return choices


def form_output_choices(choices, each_output, output_channels, dict_outputs, dict_units, dict_measurements):
    return form_output_channel_measurement_choices(
        choices, each_output, output_channels, dict_outputs, dict_units, dict_measurements, include_channel_id_in_value=False)


def form_output_channel_measurement_choices(
        choices, each_output, output_channels, dict_outputs, dict_units, dict_measurements, include_channel_id_in_value=True):
    for each_channel in output_channels:
        measurement_channels = dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]['measurements']
        for measurement_channel in measurement_channels:
            device_measurement = DeviceMeasurements.query.filter(
                and_(DeviceMeasurements.device_id == each_output.unique_id,
                     DeviceMeasurements.channel == measurement_channel)).first()
            if not device_measurement:
                continue

            conversion = Conversion.query.filter(
                Conversion.unique_id == device_measurement.conversion_id).first()
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)

            if unit:
                if include_channel_id_in_value:
                    value = f'{each_output.unique_id},{device_measurement.unique_id},{each_channel.unique_id}'
                else:
                    value = f'{each_output.unique_id},{device_measurement.unique_id}'

                display_unit = find_name_unit(
                    dict_units, unit)
                display_measurement = find_name_measurement(
                    dict_measurements, measurement)

                if device_measurement.name:
                    meas_name = ' ({name})'.format(name=device_measurement.name)
                else:
                    meas_name = ''

                if each_channel.name:
                    channel_name = ' ({name})'.format(name=each_channel.name)
                else:
                    channel_name = ''

                if display_measurement and display_unit:
                    measurement_unit = ' {meas} ({unit})'.format(
                        meas=display_measurement, unit=display_unit)
                elif display_measurement:
                    measurement_unit = ' {meas}'.format(
                        meas=display_measurement)
                else:
                    measurement_unit = ' ({unit})'.format(unit=display_unit)

                display = f'[Output {each_output.id:02d} CH{each_channel.channel} M{device_measurement.channel}] {each_output.name}{channel_name}{meas_name}{measurement_unit}'

                types = []
                if 'types' in dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]:
                    types = dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]['types']

                choices.append(
                    {'value': value,
                     'item': display,
                     'types': types})

    return choices


def form_output_channel_choices(choices, each_output, each_channel, dict_outputs):
    value = '{output_id},{chan_id}'.format(
        output_id=each_output.unique_id,
        chan_id=each_channel.unique_id)

    display = '[Output {id:02d} CH{ch}] {name}'.format(
        id=each_output.id,
        name=each_output.name,
        ch=each_channel.channel)

    if each_channel.name:
        display += ': {}'.format(each_channel.name)
    elif ('name' in dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel] and
            dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]['name']):
        display += ': {}'.format(dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]['name'])

    types = []
    if 'types' in dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]:
        types = dict_outputs[each_output.output_type]['channels_dict'][each_channel.channel]['types']

    choices.append({
        'value': value,
         'item': display,
         'types': types
    })

    return choices


def form_output_choices_devices(choices, each_output):
    value = '{id},output'.format(id=each_output.unique_id)
    display = '[Output {id:02d}] {name}'.format(
        id=each_output.id,
        name=each_output.name)
    choices.append({'value': value, 'item': display})
    return choices


def form_pid_choices(choices, each_pid, dict_units, dict_measurements):
    device_measurements = DeviceMeasurements.query.filter(
        DeviceMeasurements.device_id == each_pid.unique_id).all()

    for each_measure in device_measurements:
        conversion = Conversion.query.filter(
            Conversion.unique_id == each_measure.conversion_id).first()
        channel, unit, measurement = return_measurement_info(
            each_measure, conversion)

        value = '{input_id},{meas_id}'.format(
            input_id=each_pid.unique_id,
            meas_id=each_measure.unique_id)

        if unit:
            display_unit = find_name_unit(
                dict_units, unit)
            display_measurement = find_name_measurement(
                dict_measurements, measurement)
        elif each_measure.measurement_type == 'setpoint':
            display_unit = None
            display_measurement = 'Setpoint'
        else:
            display_unit = None
            display_measurement = None

        if each_measure.name:
            channel_info = 'CH{cnum} ({cname})'.format(
                cnum=channel, cname=each_measure.name)
        else:
            channel_info = 'CH{cnum}'.format(cnum=channel)

        if display_measurement and display_unit:
            measurement_unit = '{meas} ({unit})'.format(
                meas=display_measurement, unit=display_unit)
        elif display_measurement:
            measurement_unit = '{meas}'.format(
                meas=display_measurement)
        else:
            measurement_unit = '({unit})'.format(unit=display_unit)

        display = '[PID {id:02d}] {i_name} {chan} {meas}'.format(
            id=each_pid.id,
            i_name=each_pid.name,
            chan=channel_info,
            meas=measurement_unit)
        choices.append({'value': value, 'item': display})

    return choices


def form_pid_choices_devices(choices, each_pid):
    value = '{id}'.format(id=each_pid.unique_id)
    display = '[PID {id:02d}] {name}'.format(
        id=each_pid.id,
        name=each_pid.name)
    choices.append({'value': value, 'item': display})
    return choices


def form_method_choices(choices, each_method):
    value = '{id}'.format(id=each_method.unique_id)
    display = '[Method {id:02d}] {name}'.format(
        id=each_method.id,
        name=each_method.name)
    choices.append({'value': value, 'item': display})
    return choices


def form_tag_choices(choices, each_tag):
    value = '{id},tag'.format(id=each_tag.unique_id)
    display = '[Tag {id:02d}] {name}'.format(
        id=each_tag.id, name=each_tag.name)
    choices.append({'value': value, 'item': display})
    return choices


def find_name_unit(dict_units, unit):
    if unit in dict_units:
        unit = dict_units[unit]['unit']
    return unit


def find_name_measurement(dict_measurements, measurement):
    if measurement in dict_measurements:
        measurement = dict_measurements[measurement]['name']
    return measurement


def choices_id_name(table):
    """Return a dictionary of all available ids and names of a table."""
    choices = []
    for each_entry in table:
        value = each_entry.unique_id
        display = '[{id:02d}] {name}'.format(
            id=each_entry.id, name=each_entry.name)
        choices.append({'value': value, 'item': display})
    return choices


def user_has_permission(permission, silent=False):
    """
    Determine if the currently-logged-in user has permission to perform a
    specific action.
    """
    user = User.query.filter(User.name == flask_login.current_user.name).first()
    role = Role.query.filter(Role.id == user.role_id).first()
    if ((permission == 'edit_settings' and role.edit_settings) or
            (permission == 'edit_controllers' and role.edit_controllers) or
            (permission == 'edit_users' and role.edit_users) or
            (permission == 'view_settings' and role.view_settings) or
            (permission == 'view_camera' and role.view_camera) or
            (permission == 'view_stats' and role.view_stats) or
            (permission == 'view_logs' and role.view_logs) or
            (permission == 'reset_password' and role.reset_password)):
        return True
    if not silent:
        flash("Insufficient permissions: {}".format(permission), "error")
    return False


def dashboard_widget_get_info(dashboard_id=None):
    """Generate a dictionary of information of all dashboard widgets."""
    dashboards = {}

    if dashboard_id:
        dashboard_table = Dashboard.query.filter(
            Dashboard.unique_id == dashboard_id).all()
        widgets = Widget.query.filter(Widget.dashboard_id == dashboard_id).all()
    else:
        dashboard_table = Dashboard.query.all()
        widgets = Widget.query.all()

    for each_dash in dashboard_table:
        dashboards[each_dash.unique_id] = {
            'name': each_dash.name,
            'widgets': {}
        }

        if not widgets:
            break

        for each_widget in widgets:
            this_widget = dashboards[each_dash.unique_id]['widgets'][each_widget.unique_id]
            this_widget['position_x'] = each_widget.position_x
            this_widget['position_y'] = each_widget.position_y
            this_widget['width'] = each_widget.width
            this_widget['height'] = each_widget.height

        position_x = each_dash.position_x.split(';')
        for each_pos in position_x:
            split_pos = each_pos.split(',')
            widget_id = split_pos[0]
            if widget_id not in dashboards[each_dash.unique_id]['widgets']:
                dashboards[each_dash.unique_id]['widgets'][widget_id] = {}
            dashboards[each_dash.unique_id]['widgets'][widget_id]['position_x'] = int(split_pos[1])

        position_y = each_dash.position_y.split(';')
        for each_pos in position_y:
            split_pos = each_pos.split(',')
            widget_id = split_pos[0]
            if widget_id not in dashboards[each_dash.unique_id]['widgets']:
                dashboards[each_dash.unique_id]['widgets'][widget_id] = {}
            dashboards[each_dash.unique_id]['widgets'][widget_id]['position_y'] = int(split_pos[1])

        width = each_dash.width.split(';')
        for each_size in width:
            split_size = each_size.split(',')
            widget_id = split_size[0]
            if widget_id not in dashboards[each_dash.unique_id]['widgets']:
                dashboards[each_dash.unique_id]['widgets'][widget_id] = {}
            dashboards[each_dash.unique_id]['widgets'][widget_id]['width'] = int(split_size[1])

        height = each_dash.height.split(';')
        for each_size in height:
            split_size = each_size.split(',')
            widget_id = split_size[0]
            if widget_id not in dashboards[each_dash.unique_id]['widgets']:
                dashboards[each_dash.unique_id]['widgets'][widget_id] = {}
            dashboards[each_dash.unique_id]['widgets'][widget_id]['height'] = int(split_size[1])

    return dashboards


def delete_entry_with_id(table, entry_id, flash_message=True):
    """Delete SQL database entry with specific id."""
    try:
        entry = table.query.filter(
            table.unique_id == entry_id).first()
        db.session.delete(entry)
        db.session.commit()
        msg = '{action} {table} with ID: {id}'.format(
            action=TRANSLATIONS['delete']['title'],
            table=table.__tablename__,
            id=entry_id)
        if flash_message:
            flash(gettext("%(msg)s", msg=msg), "success")
        else:
            logger.info(msg)
        return 1
    except sqlalchemy.orm.exc.NoResultFound:
        msg = '{action} {id}: {err}'.format(
            action=TRANSLATIONS['delete']['title'],
            id=entry_id,
            err=gettext("Entry with ID %(id)s not found",
                id=entry_id))
        if flash_message:
            flash(gettext("%(msg)s", msg=msg), "error")
        else:
            logger.error(msg)
        return 0


def flash_form_errors(form):
    """Flashes form errors for easier display."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(gettext("Error in the %(field)s field - %(err)s",
                          field=getattr(form, field).label.text,
                          err=error),
                  "error")


def form_error_messages(form, error):
    """Append form errors."""
    for field, errors in form.errors.items():
        for each_error in errors:
            error.append(
                gettext("Error in the %(field)s field - %(err)s",
                    field=getattr(form, field).label.text,
                    err=each_error))
    return error


def flash_success_errors(error, action, redirect_url):
    if error:
        for each_error in error:
            flash(
                gettext("%(msg)s", msg='{action}: {err}'.format(
                    action=action, err=each_error)),
                "error")
        return redirect(redirect_url)
    else:
        flash(gettext("%(msg)s", msg=action), "success")


def add_display_order(display_order, device_id):
    """Add integer ID to list of string IDs."""
    if display_order:
        display_order.append(device_id)
        return ','.join(display_order)
    return device_id


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
    """Reorder entry in a comma-separated list either up or down."""
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

def get_camera_paths(camera):
    """Retrieve still/timelapse paths for the given camera object."""
    camera_path = os.path.join(PATH_CAMERAS, '{uid}'.format(
        uid=camera.unique_id))

    if camera.path_still:
        still_path = camera.path_still
    else:
        still_path = os.path.join(camera_path, 'still')

    if camera.path_timelapse:
        tl_path = camera.path_timelapse
    else:
        tl_path = os.path.join(camera_path, 'timelapse')
    
    return still_path, tl_path


def bytes2human(n, fmt='%(value).1f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human-readable string based on fmt.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs
    
    Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
    License: MIT

      >>> bytes2human(1.9)
      '1.0 B'
      >>> bytes2human(1024)
      '1.0 K'
      >>> bytes2human(1048576)
      '1.0 M'
      >>> bytes2human(9856, symbols="iec")
      '9.6 Ki'
      >>> bytes2human(9856, symbols="iec_ext")
      '9.6 kibi'
      >>> bytes2human(10000, "%(value).1f %(symbol)s/sec")
      '9.8 K/sec'
      >>> # precision can be adjusted by playing with %f operator
      >>> bytes2human(10000, fmt="%(value).5f %(symbol)s")
      '9.76562 K'
    """
    SYMBOLS = {
        'customary': ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
        'customary_ext': ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                          'zetta', 'iotta'),
        'iec': ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
        'iec_ext': ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                    'zebi', 'yobi'),
    }

    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return fmt % locals()
    return fmt % dict(symbol=symbols[0], value=n)

def get_camera_image_info():
    """Retrieve information about the latest camera images."""
    latest_img_still_ts = {}
    latest_img_still_size = {}
    latest_img_still = {}
    latest_img_tl_ts = {}
    latest_img_tl_size = {}
    latest_img_tl = {}
    time_lapse_imgs = {}

    camera = Camera.query.all()

    for each_camera in camera:
        still_path, tl_path = get_camera_paths(each_camera)

        if each_camera.still_last_file:
            latest_img_still_ts[each_camera.unique_id] = datetime.fromtimestamp(
                each_camera.still_last_ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_img_still[each_camera.unique_id] = each_camera.still_last_file
            file_still_path = os.path.join(still_path, each_camera.still_last_file)
            if os.path.exists(file_still_path):
                latest_img_still_size[each_camera.unique_id] = bytes2human(os.path.getsize(file_still_path))
        else:
            latest_img_still[each_camera.unique_id] = None

        try:
            # Get list of timelapse filename sets for generating a video from images
            time_lapse_imgs[each_camera.unique_id] = []
            for i in os.listdir(tl_path):
                if (os.path.isfile(os.path.join(tl_path, i)) and
                        i[:-10] not in time_lapse_imgs[each_camera.unique_id]):
                    time_lapse_imgs[each_camera.unique_id].append(i[:-10])
            time_lapse_imgs[each_camera.unique_id].sort()
        except Exception:
            pass

        if each_camera.timelapse_last_file:
            latest_img_tl_ts[each_camera.unique_id] = datetime.fromtimestamp(
                each_camera.timelapse_last_ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_img_tl[each_camera.unique_id] = each_camera.timelapse_last_file
            file_tl_path = os.path.join(tl_path, each_camera.timelapse_last_file)
            if os.path.exists(file_tl_path):
                latest_img_tl_size[each_camera.unique_id] = bytes2human(os.path.getsize(file_tl_path))
        else:
            latest_img_tl[each_camera.unique_id] = None

    return (latest_img_still_ts, latest_img_still_size, latest_img_still,
            latest_img_tl_ts, latest_img_tl_size, latest_img_tl, time_lapse_imgs)


def return_dependencies(device_type):
    unmet_deps = []
    met_deps = False
    dep_message = ''

    list_dependencies = [
        parse_function_information(),
        parse_action_information(),
        parse_input_information(),
        parse_output_information(),
        parse_widget_information(),
        CAMERA_INFO,
        FUNCTION_INFO,
        METHOD_INFO,
        DEPENDENCIES_GENERAL
    ]

    for each_section in list_dependencies:
        if device_type in each_section:
            if "dependencies_message" in each_section[device_type]:
                dep_message = each_section[device_type]["dependencies_message"]

            for each_device, each_dict in each_section[device_type].items():
                if not each_dict:
                    met_deps = True
                elif each_device == 'dependencies_module':
                    for (install_type, package, install_id) in each_dict:
                        entry = (
                            package,
                            f'{install_type} {install_id}',
                            install_type,
                            install_id
                        )
                        if install_type == 'pip-pypi':
                            try:
                                module = importlib.util.find_spec(package)

                                # Get version
                                version_mismatch = False
                                if "==" in install_id:
                                    try:
                                        pypi_name = install_id.split("==")[0]
                                        required_version = install_id.split("==")[1]
                                        try:
                                            installed_version = version(pypi_name)
                                        except:
                                            installed_version = "NONE"

                                        logger.info(f"Pypi Package: {pypi_name}, "
                                                    f"Required: v{required_version}, "
                                                    f"Installed: v{installed_version}, "
                                                    f"Same: {required_version == installed_version}")
                                        if required_version != installed_version:
                                            version_mismatch = True
                                    except:
                                        logger.exception(1)

                                if module is None or version_mismatch:
                                    if entry not in unmet_deps:
                                        unmet_deps.append(entry)
                                else:
                                    met_deps = True
                            except ImportError:
                                if entry not in unmet_deps:
                                    unmet_deps.append(entry)
                        elif install_type == 'apt':
                            if (not dpkg_package_exists(package) and
                                    entry not in unmet_deps):
                                unmet_deps.append(entry)
                            else:
                                met_deps = True
                        elif install_type == 'bash-commands':
                            files_not_found = []
                            for each_file in package:
                                if not os.path.isfile(each_file):
                                    files_not_found.append(each_file.split('/')[-1])
                            if files_not_found:
                                if entry not in unmet_deps:
                                    unmet_deps.append((
                                        ", ".join(files_not_found),
                                        install_id,
                                        install_type,
                                        ", ".join(files_not_found)
                                    ))
                                else:
                                    met_deps = True
                        elif install_type == 'internal':
                            if package.startswith('file-exists'):
                                filepath = package.split(' ', 1)[1]
                                if not os.path.isfile(filepath):
                                    if entry not in unmet_deps:
                                        unmet_deps.append(entry)
                                    else:
                                        met_deps = True
                            elif package.startswith('pip-exists'):
                                py_module = package.split(' ', 1)[1]
                                try:
                                    module = importlib.util.find_spec(py_module)
                                    if module is None:
                                        if entry not in unmet_deps:
                                            unmet_deps.append(entry)
                                    else:
                                        met_deps = True
                                except ImportError:
                                    if entry not in unmet_deps:
                                        unmet_deps.append(entry)
                            elif package.startswith('apt'):
                                if (not dpkg_package_exists(package) and
                                        entry not in unmet_deps):
                                    unmet_deps.append(entry)
                                else:
                                    met_deps = True

    return unmet_deps, met_deps, dep_message


def use_unit_generate(device_measurements, input_dev, output, function):
    """Generate dictionary of units to convert to."""
    use_unit = {}

    # Controllers have measurement tables with the same schema
    list_devices_with_measurements = [
        input_dev, function
    ]

    for devices in list_devices_with_measurements:
        for each_device in devices:
            use_unit[each_device.unique_id] = {}

            for each_meas in device_measurements:
                if each_meas.device_id == each_device.unique_id:
                    if each_meas.measurement not in use_unit[each_device.unique_id]:
                        use_unit[each_device.unique_id][each_meas.measurement] = {}
                    if each_meas.unit not in use_unit[each_device.unique_id][each_meas.measurement]:
                        use_unit[each_device.unique_id][each_meas.measurement][each_meas.unit] = OrderedDict()
                    use_unit[each_device.unique_id][each_meas.measurement][each_meas.unit][each_meas.channel] = None

    for each_output in output:
        use_unit[each_output.unique_id] = {}
        if each_output.output_type == 'wired':
            use_unit[each_output.unique_id]['duration_time'] = 'second'

    return use_unit


def get_ip_address():
    return request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown address')


def generate_form_controller_list(dict_controllers):
    # Sort dictionary entries by function_name
    # Results in list of sorted dictionary keys
    list_tuples_sorted = sorted(dict_controllers.items(), key=lambda x: x[1]['function_name'])
    list_controllers_sorted = []
    for each_controller in list_tuples_sorted:
        list_controllers_sorted.append(each_controller[0])
    return list_controllers_sorted


def generate_form_input_list(dict_inputs):
    # Sort dictionary entries by input_manufacturer, then input_name
    # Results in list of sorted dictionary keys
    list_tuples_sorted = sorted(dict_inputs.items(), key=lambda x: (x[1]['input_manufacturer'], x[1]['input_name']))
    list_inputs_sorted = []
    for each_input in list_tuples_sorted:
        list_inputs_sorted.append(each_input[0])
    return list_inputs_sorted


def generate_form_output_list(dict_outputs):
    # Sort dictionary entries by output_name
    # Results in list of sorted dictionary keys
    list_tuples_sorted = sorted(dict_outputs.items(), key=lambda x: (x[1]['output_name']))
    list_outputs_sorted = []
    for each_output in list_tuples_sorted:
        list_outputs_sorted.append(each_output[0])
    return list_outputs_sorted


def generate_form_action_list(dict_actions, application=None):
    # Sort dictionary entries by input_manufacturer, then input_name
    # Results in list of sorted dictionary keys
    def check_application(list1, list2):
        for val in list1:
            if val in list2:
                return True
        return False

    list_tuples_sorted = sorted(dict_actions.items(), key=lambda x: (x[1]['manufacturer'], x[1]['name']))
    list_actions_sorted = []
    for each_action in list_tuples_sorted:
        if (application and 'application' in dict_actions[each_action[0]] and
                not check_application(application, dict_actions[each_action[0]]['application'])):
            continue
        list_actions_sorted.append(each_action[0])
    return list_actions_sorted


def generate_form_widget_list(dict_widgets):
    # Sort dictionary entries by input_manufacturer, then input_name
    # Results in list of sorted dictionary keys
    list_tuples_sorted = sorted(dict_widgets.items(), key=lambda x: (x[1]['widget_name']))
    list_widgets_sorted = []
    for each_widget in list_tuples_sorted:
        list_widgets_sorted.append(each_widget[0])
    return list_widgets_sorted


def custom_command(controller_type, dict_device, unique_id, form):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    if controller_type == "Output":
        controller = Output.query.filter(
            Output.unique_id == unique_id).first()
        device_type = controller.output_type
    elif controller_type == "Function_Custom":
        controller = CustomController.query.filter(
            CustomController.unique_id == unique_id).first()
        device_type = controller.device
    elif controller_type == "Input":
        controller = Input.query.filter(
            Input.unique_id == unique_id).first()
        device_type = controller.device
    else:
        messages["error"].append("Unknown controller: {}".format(controller_type))
        return messages

    if not controller:
        messages["error"].append("Could not find button ID")
        return messages

    if controller_type != "Output" and not controller.is_activated:
        messages["error"].append("Activate controller before executing a Custom Command")
        return messages

    try:
        options = {}
        if 'custom_commands' in dict_device[device_type]:
            for each_option in dict_device[device_type]['custom_commands']:
                if 'id' in each_option and 'type' in each_option:
                    options[each_option['id']] = each_option

        args_dict = {}
        button_id = None
        for key in form.keys():
            if key.startswith('custom_button_'):
                button_id = key[14:]
            else:
                for value in form.getlist(key):
                    if key in options:
                        if options[key]['type'] == 'integer':
                            try:
                                args_dict[key] = int(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent integer: '{}'".format(key, value))
                        elif options[key]['type'] == 'float':
                            try:
                                args_dict[key] = float(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent float: '{}'".format(key, value))
                        elif options[key]['type'] == 'bool':
                            try:
                                args_dict[key] = bool(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent bool: '{}'".format(key, value))
                        elif options[key]['type'] in ['select', 'text']:
                            try:
                                args_dict[key] = str(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent string: '{}'".format(key, value))
                        else:
                            messages["error"].append("Unknown key type. Key: {}, Type: {}".format(key, options[key]['type']))

        if not button_id:
            messages["error"].append("Could not find button ID")
            return messages

        if not messages["error"]:
            control = DaemonControl()
            use_thread = True
            if (button_id in options and
                    'wait_for_return' in options[button_id] and
                    options[button_id]['wait_for_return']):
                use_thread = False
            status = control.module_function(
                controller_type, unique_id, button_id, args_dict, use_thread)
            if status:
                if status[0]:
                    messages["error"].append("Custom Button: {}".format(status[1]))
                else:
                    messages["success"].append("Custom Button: {}".format(status[1]))
            else:
                messages["error"].append("Custom Button didn't receive a return value")

    except Exception as except_msg:
        logger.exception(1)
        messages["error"].append(str(except_msg))

    return messages
