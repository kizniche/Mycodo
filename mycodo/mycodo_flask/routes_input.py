# coding=utf-8
"""collection of Page endpoints."""
import json
import logging
import os
import re
import subprocess

import flask_login
from flask import (current_app, jsonify, redirect, render_template, request,
                   url_for)
from flask.blueprints import Blueprint
from sqlalchemy import and_

from mycodo.config import INSTALL_DIRECTORY, PATH_1WIRE
from mycodo.databases.models import (PID, Actions, Camera, Conditional,
                                     Conversion, CustomController,
                                     DeviceMeasurements, DisplayOrder, Input,
                                     InputChannel, Measurement, Method, Misc,
                                     Output, OutputChannel, Trigger, Unit,
                                     User)
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_action, forms_input
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_action, utils_general, utils_input
from mycodo.mycodo_flask.utils.utils_general import generate_form_action_list
from mycodo.utils.actions import parse_action_information
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.outputs import output_types, parse_output_information
from mycodo.utils.system_pi import (
    add_custom_measurements, add_custom_units, csv_to_list_of_str,
    dpkg_package_exists, parse_custom_option_values,
    parse_custom_option_values_input_channels_json)

logger = logging.getLogger('mycodo.mycodo_flask.routes_input')

blueprint = Blueprint('routes_input',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.route('/input_submit', methods=['POST'])
@flask_login.login_required
def page_input_submit():
    """Submit form for Data page"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    page_refresh = False
    action_id = None
    input_id = None
    duplicated_input_id = ''
    dep_unmet = ''
    dep_name = ''
    dep_list = []
    dep_message = ''

    form_actions = forms_action.Actions()
    form_add_input = forms_input.InputAdd()
    form_mod_input = forms_input.InputMod()

    if not utils_general.user_has_permission('edit_controllers'):
        messages["error"].append("Your permissions do not allow this action")

    if not messages["error"]:
        if form_add_input.input_add.data:
            (messages,
             dep_name,
             dep_list,
             dep_message,
             input_id) = utils_input.input_add(form_add_input)
            if dep_list:
                dep_unmet = form_add_input.input_type.data.split(',')[0]
        elif form_mod_input.input_duplicate.data:
            messages, input_id = utils_input.input_duplicate(
                form_mod_input)
            duplicated_input_id = form_mod_input.input_id.data
        else:
            input_id = form_mod_input.input_id.data
            if form_mod_input.input_mod.data:
                messages, page_refresh = utils_input.input_mod(
                    form_mod_input, request.form)
            elif form_mod_input.input_delete.data:
                messages = utils_input.input_del(
                    form_mod_input.input_id.data)
            elif form_mod_input.input_activate.data:
                messages = utils_input.input_activate(form_mod_input)
            elif form_mod_input.input_deactivate.data:
                messages = utils_input.input_deactivate(form_mod_input)
            elif form_mod_input.input_acquire_measurements.data:
                messages = utils_input.force_acquire_measurements(
                    form_mod_input.input_id.data)

            # Actions
            elif form_actions.add_action.data:
                (messages,
                 dep_name,
                 dep_list,
                 action_id,
                 page_refresh) = utils_action.action_add(form_actions)
                if dep_list:
                    dep_unmet = form_actions.action_type.data
                input_id = form_actions.device_id.data
            elif form_actions.save_action.data:
                messages = utils_action.action_mod(
                    form_actions, request.form)
                input_id = form_actions.device_id.data
            elif form_actions.delete_action.data:
                messages = utils_action.action_del(form_actions)
                page_refresh = True
                input_id = form_actions.device_id.data
                action_id = form_actions.action_id.data

            # Custom action
            else:
                custom_button = False
                for key in request.form.keys():
                    if key.startswith('custom_button_'):
                        custom_button = True
                        break
                if custom_button:
                    messages = utils_general.custom_command(
                        "Input",
                        parse_input_information(),
                        form_mod_input.input_id.data,
                        request.form)
                else:
                    messages["error"].append("Unknown function directive")

    return jsonify(data={
        'action_id': action_id,
        'input_id': input_id,
        'duplicated_input_id': duplicated_input_id,
        'dep_name': dep_name,
        'dep_list': dep_list,
        'dep_unmet': dep_unmet,
        'dep_message': dep_message,
        'messages': messages,
        "page_refresh": page_refresh
    })


@blueprint.route('/save_input_layout', methods=['POST'])
def save_input_layout():
    """Save positions of inputs."""
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))
    data = request.get_json()
    keys = ('id', 'y')
    for each_input in data:
        if all(k in each_input for k in keys):
            input_mod = Input.query.filter(
                Input.unique_id == each_input['id']).first()
            if input_mod:
                input_mod.position_y = each_input['y']
    db.session.commit()
    return "success"


@blueprint.route('/input', methods=('GET', 'POST'))
@flask_login.login_required
def page_input():
    """Display Data page options."""
    input_type = request.args.get('input_type', None)
    input_id = request.args.get('input_id', None)
    action_id = request.args.get('action_id', None)

    each_input = None
    each_action = None

    if input_type in ['entry', 'options', 'actions']:
        each_input = Input.query.filter(Input.unique_id == input_id).first()

        if input_type == 'actions' and action_id:
            each_action = Actions.query.filter(
                Actions.unique_id == action_id).first()

    action = Actions.query.all()
    function = CustomController.query.all()
    input_dev = Input.query.all()
    input_channel = InputChannel.query.all()
    method = Method.query.all()
    measurement = Measurement.query.all()
    misc = Misc.query.first()
    output = Output.query.all()
    output_channel = OutputChannel.query.all()
    pid = PID.query.all()
    user = User.query.all()
    unit = Unit.query.all()

    display_order_input = csv_to_list_of_str(DisplayOrder.query.first().inputs)

    form_add_input = forms_input.InputAdd()
    form_mod_input = forms_input.InputMod()
    form_actions = forms_action.Actions()

    dict_inputs = parse_input_information()
    dict_actions = parse_action_information()

    custom_options_values_inputs = parse_custom_option_values(
        input_dev, dict_controller=dict_inputs)
    custom_options_values_input_channels = parse_custom_option_values_input_channels_json(
        input_channel, dict_controller=dict_inputs, key_name='custom_channel_options')

    custom_options_values_actions = {}
    for each_action_dev in action:
        try:
            custom_options_values_actions[each_action_dev.unique_id] = json.loads(each_action_dev.custom_options)
        except:
            custom_options_values_actions[each_action_dev.unique_id] = {}

    custom_commands = {}
    for each_input_dev in input_dev:
        if each_input_dev.device in dict_inputs and 'custom_commands' in dict_inputs[each_input_dev.device]:
            custom_commands[each_input_dev.device] = True

    # Generate dict that incorporate user-added measurements/units
    dict_outputs = parse_output_information()
    dict_units = add_custom_units(unit)
    dict_measurements = add_custom_measurements(measurement)

    # Generate Action dropdown for use with Inputs
    choices_actions = []
    list_actions_sorted = generate_form_action_list(dict_actions, application=["inputs"])
    for name in list_actions_sorted:
        choices_actions.append((name, dict_actions[name]['name']))

    # Create list of choices to be used in dropdown menus
    choices_function = utils_general.choices_functions(
        function, dict_units, dict_measurements)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_method = utils_general.choices_methods(method)
    choices_output = utils_general.choices_outputs(
        output, OutputChannel, dict_outputs, dict_units, dict_measurements)
    choices_output_channels = utils_general.choices_outputs_channels(
        output, output_channel, dict_outputs)
    choices_output_channels_measurements = utils_general.choices_outputs_channels_measurements(
        output, OutputChannel, dict_outputs, dict_units, dict_measurements)
    choices_pid = utils_general.choices_pids(
        pid, dict_units, dict_measurements)
    choices_pid_devices = utils_general.choices_pids_devices(pid)
    choices_unit = utils_general.choices_units(unit)
    choices_measurement = utils_general.choices_measurements(measurement)
    choices_measurements_units = utils_general.choices_measurements_units(measurement, unit)

    # Create dict of Input names
    names_input = {}
    all_elements = input_dev
    for each_element in all_elements:
        names_input[each_element.unique_id] = '[{id:02d}] ({uid}) {name}'.format(
            id=each_element.id,
            uid=each_element.unique_id.split('-')[0],
            name=each_element.name)

    # Create list of file names from the input_options directory
    # Used in generating the correct options for each input controller
    input_templates = []
    input_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/data_options/input_options')
    for (_, _, file_names) in os.walk(input_path):
        input_templates.extend(file_names)
        break

    # Compile a list of 1-wire devices
    devices_1wire = []
    if os.path.isdir(PATH_1WIRE):
        for each_name in os.listdir(PATH_1WIRE):
            if 'bus' not in each_name and '-' in each_name:
                devices_1wire.append(
                    {'name': each_name, 'value': each_name.split('-')[1]}
                )

    # Compile a list of 1-wire devices (using ow-shell)
    devices_1wire_ow_shell = []
    if not Input.query.filter(Input.device == "DS18B20_OWS").count():
        pass
    elif current_app.config['TESTING']:
        logger.debug("Testing: Skipping testing for 'ow-shell'")
    elif not dpkg_package_exists('ow-shell'):
        logger.debug("Package 'ow-shell' not found")
    else:
        logger.debug("Package 'ow-shell' found")
        try:
            test_cmd = subprocess.check_output(['owdir']).splitlines()
            for each_ow in test_cmd:
                str_ow = re.sub("\ |\/|\'", "", each_ow.decode("utf-8"))  # Strip / and '
                if '.' in str_ow and len(str_ow) == 15:
                    devices_1wire_ow_shell.append(str_ow)
        except Exception:
            logger.error("Error finding 1-wire devices with 'owdir'")

    # Find FTDI devices
    ftdi_devices = []
    if not current_app.config['TESTING']:
        for each_input_dev in input_dev:
            if each_input_dev.interface == "FTDI":
                from mycodo.devices.atlas_scientific_ftdi import \
                    get_ftdi_device_list
                ftdi_devices = get_ftdi_device_list()
                break

    if not input_type:
        return render_template('pages/input.html',
                               and_=and_,
                               action=action,
                               choices_actions=choices_actions,
                               choices_function=choices_function,
                               choices_input=choices_input,
                               choices_output=choices_output,
                               choices_measurement=choices_measurement,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               choices_pid_devices=choices_pid_devices,
                               choices_unit=choices_unit,
                               custom_commands=custom_commands,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_inputs=custom_options_values_inputs,
                               custom_options_values_input_channels=custom_options_values_input_channels,
                               dict_actions=dict_actions,
                               dict_inputs=dict_inputs,
                               dict_measurements=dict_measurements,
                               dict_units=dict_units,
                               display_order_input=display_order_input,
                               form_actions=form_actions,
                               form_add_input=form_add_input,
                               form_mod_input=form_mod_input,
                               ftdi_devices=ftdi_devices,
                               input_channel=input_channel,
                               input_templates=input_templates,
                               misc=misc,
                               names_input=names_input,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_camera=Camera,
                               table_conditional=Conditional,
                               table_function=CustomController,
                               table_input=Input,
                               table_output=Output,
                               table_pid=PID,
                               table_trigger=Trigger,
                               user=user,
                               devices_1wire_ow_shell=devices_1wire_ow_shell,
                               devices_1wire=devices_1wire)
    elif input_type == 'entry':
        return render_template('pages/data_options/input_entry.html',
                               and_=and_,
                               action=action,
                               choices_actions=choices_actions,
                               choices_function=choices_function,
                               choices_input=choices_input,
                               choices_output=choices_output,
                               choices_measurement=choices_measurement,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               choices_pid_devices=choices_pid_devices,
                               choices_unit=choices_unit,
                               custom_commands=custom_commands,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_inputs=custom_options_values_inputs,
                               custom_options_values_input_channels=custom_options_values_input_channels,
                               dict_actions=dict_actions,
                               dict_inputs=dict_inputs,
                               dict_measurements=dict_measurements,
                               dict_units=dict_units,
                               display_order_input=display_order_input,
                               each_input=each_input,
                               form_actions=form_actions,
                               form_add_input=form_add_input,
                               form_mod_input=form_mod_input,
                               ftdi_devices=ftdi_devices,
                               input_channel=input_channel,
                               input_templates=input_templates,
                               misc=misc,
                               names_input=names_input,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_camera=Camera,
                               table_conditional=Conditional,
                               table_function=CustomController,
                               table_input=Input,
                               table_output=Output,
                               table_pid=PID,
                               table_trigger=Trigger,
                               user=user,
                               devices_1wire_ow_shell=devices_1wire_ow_shell,
                               devices_1wire=devices_1wire)
    elif input_type == 'options':
        return render_template('pages/data_options/input_options.html',
                               and_=and_,
                               action=action,
                               choices_actions=choices_actions,
                               choices_function=choices_function,
                               choices_input=choices_input,
                               choices_output=choices_output,
                               choices_measurement=choices_measurement,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               choices_pid_devices=choices_pid_devices,
                               choices_unit=choices_unit,
                               custom_commands=custom_commands,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_inputs=custom_options_values_inputs,
                               custom_options_values_input_channels=custom_options_values_input_channels,
                               dict_actions=dict_actions,
                               dict_inputs=dict_inputs,
                               dict_measurements=dict_measurements,
                               dict_units=dict_units,
                               display_order_input=display_order_input,
                               each_input=each_input,
                               form_actions=form_actions,
                               form_add_input=form_add_input,
                               form_mod_input=form_mod_input,
                               ftdi_devices=ftdi_devices,
                               input_channel=input_channel,
                               input_templates=input_templates,
                               misc=misc,
                               names_input=names_input,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_camera=Camera,
                               table_conditional=Conditional,
                               table_function=CustomController,
                               table_input=Input,
                               table_output=Output,
                               table_pid=PID,
                               table_trigger=Trigger,
                               user=user,
                               devices_1wire_ow_shell=devices_1wire_ow_shell,
                               devices_1wire=devices_1wire)
    elif input_type == 'actions':
        return render_template('pages/actions.html',
                               and_=and_,
                               action=action,
                               choices_actions=choices_actions,
                               choices_function=choices_function,
                               choices_input=choices_input,
                               choices_output=choices_output,
                               choices_measurement=choices_measurement,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               choices_pid_devices=choices_pid_devices,
                               choices_unit=choices_unit,
                               custom_commands=custom_commands,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_inputs=custom_options_values_inputs,
                               custom_options_values_input_channels=custom_options_values_input_channels,
                               dict_actions=dict_actions,
                               dict_inputs=dict_inputs,
                               dict_measurements=dict_measurements,
                               dict_units=dict_units,
                               display_order_input=display_order_input,
                               each_action=each_action,
                               each_input=each_input,
                               form_actions=form_actions,
                               form_add_input=form_add_input,
                               form_mod_input=form_mod_input,
                               ftdi_devices=ftdi_devices,
                               input_channel=input_channel,
                               input_templates=input_templates,
                               misc=misc,
                               names_input=names_input,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_camera=Camera,
                               table_conditional=Conditional,
                               table_function=CustomController,
                               table_input=Input,
                               table_output=Output,
                               table_pid=PID,
                               table_trigger=Trigger,
                               user=user,
                               devices_1wire_ow_shell=devices_1wire_ow_shell,
                               devices_1wire=devices_1wire)
