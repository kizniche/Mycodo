# coding=utf-8
""" collection of Page endpoints """
import logging
import os
import re
import subprocess

import flask_login
from flask import current_app
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.blueprints import Blueprint
from sqlalchemy import and_

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import MATH_INFO
from mycodo.config import PATH_1WIRE
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import InputChannel
from mycodo.databases.models import Math
from mycodo.databases.models import Measurement
from mycodo.databases.models import Method
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_input
from mycodo.mycodo_flask.forms import forms_math
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_input
from mycodo.mycodo_flask.utils import utils_math
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.outputs import output_types
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import check_missing_ids
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import dpkg_package_exists
from mycodo.utils.system_pi import list_to_csv
from mycodo.utils.system_pi import parse_custom_option_values
from mycodo.utils.system_pi import parse_custom_option_values_input_channels_json

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
    """ Submit form for Data page """
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    page_refresh = False
    input_id = None
    dep_unmet = ''
    dep_name = ''
    dep_list = []
    dep_message = ''

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
        elif form_mod_input.input_mod.data:
            messages, page_refresh = utils_input.input_mod(
                form_mod_input, request.form)
            input_id = form_mod_input.input_id.data
        elif form_mod_input.input_delete.data:
            messages = utils_input.input_del(
                form_mod_input.input_id.data)
            input_id = form_mod_input.input_id.data
        elif form_mod_input.input_activate.data:
            messages = utils_input.input_activate(form_mod_input)
            input_id = form_mod_input.input_id.data
        elif form_mod_input.input_deactivate.data:
            messages = utils_input.input_deactivate(form_mod_input)
            input_id = form_mod_input.input_id.data
        elif form_mod_input.input_acquire_measurements.data:
            messages = utils_input.force_acquire_measurements(
                form_mod_input.input_id.data)

        # Custom action
        else:
            custom_button = False
            for key in request.form.keys():
                if key.startswith('custom_button_'):
                    custom_button = True
                    break
            if custom_button:
                messages = utils_general.custom_action(
                    "Input",
                    parse_input_information(),
                    form_mod_input.input_id.data,
                    request.form)
            else:
                messages["error"].append("Unknown function directive")

    return jsonify(data={
        'input_id': input_id,
        'dep_name': dep_name,
        'dep_list': dep_list,
        'dep_unmet': dep_unmet,
        'dep_message': dep_message,
        'messages': messages,
        "page_refresh": page_refresh
    })


@blueprint.route('/save_input_layout', methods=['POST'])
def save_input_layout():
    """Save positions of inputs"""
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
    """ Display Data page options """
    input_type = request.args.get('input_type', None)
    input_id = request.args.get('input_id', None)
    each_input = None
    if input_type in ['entry', 'options']:
        each_input = Input.query.filter(Input.unique_id == input_id).first()

    function = CustomController.query.all()
    input_dev = Input.query.all()
    input_channel = InputChannel.query.all()
    math = Math.query.all()
    method = Method.query.all()
    measurement = Measurement.query.all()
    output = Output.query.all()
    output_channel = OutputChannel.query.all()
    pid = PID.query.all()
    user = User.query.all()
    unit = Unit.query.all()

    display_order_input = csv_to_list_of_str(DisplayOrder.query.first().inputs)
    display_order_math = csv_to_list_of_str(DisplayOrder.query.first().math)

    form_add_input = forms_input.InputAdd()
    form_mod_input = forms_input.InputMod()

    form_base = forms_math.DataBase()
    form_mod_math = forms_math.MathMod()
    form_mod_math_measurement = forms_math.MathMeasurementMod()
    form_mod_average_single = forms_math.MathModAverageSingle()
    form_mod_sum_single = forms_math.MathModSumSingle()
    form_mod_redundancy = forms_math.MathModRedundancy()
    form_mod_difference = forms_math.MathModDifference()
    form_mod_equation = forms_math.MathModEquation()
    form_mod_humidity = forms_math.MathModHumidity()
    form_mod_verification = forms_math.MathModVerification()
    form_mod_misc = forms_math.MathModMisc()

    dict_inputs = parse_input_information()

    if request.method == 'POST':  # TODO: Remove entire POST section and remove Math controllers
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_input.page_input'))

        # Reorder Math controllers
        if form_base.reorder.data:
            mod_order = DisplayOrder.query.first()
            mod_order.math = list_to_csv(form_base.list_visible_elements.data)
            mod_order.function = check_missing_ids(mod_order.function, [math])
            db.session.commit()
            flash("Reorder Complete", "success")

        # Mod Math Measurement
        elif form_mod_math_measurement.math_measurement_mod.data:
            utils_math.math_measurement_mod(form_mod_math_measurement)

        # Mod other Math settings
        elif form_mod_math.math_mod.data:
            math_type = Math.query.filter(
                Math.unique_id == form_mod_math.math_id.data).first().math_type
            if math_type == 'humidity':
                utils_math.math_mod(form_mod_math, form_mod_humidity)
            elif math_type == 'average_single':
                utils_math.math_mod(form_mod_math, form_mod_average_single)
            elif math_type == 'sum_single':
                utils_math.math_mod(form_mod_math, form_mod_sum_single)
            elif math_type == 'redundancy':
                utils_math.math_mod(form_mod_math, form_mod_redundancy)
            elif math_type == 'difference':
                utils_math.math_mod(form_mod_math, form_mod_difference)
            elif math_type == 'equation':
                utils_math.math_mod(form_mod_math, form_mod_equation)
            elif math_type == 'verification':
                utils_math.math_mod(form_mod_math, form_mod_verification)
            elif math_type == 'vapor_pressure_deficit':
                utils_math.math_mod(form_mod_math, form_mod_misc)
            else:
                utils_math.math_mod(form_mod_math)
        elif form_mod_math.math_delete.data:
            utils_math.math_del(form_mod_math)
        elif form_mod_math.math_order_up.data:
            utils_math.math_reorder(form_mod_math.math_id.data,
                                    display_order_math, 'up')
        elif form_mod_math.math_order_down.data:
            utils_math.math_reorder(form_mod_math.math_id.data,
                                    display_order_math, 'down')
        elif form_mod_math.math_activate.data:
            utils_math.math_activate(form_mod_math)
        elif form_mod_math.math_deactivate.data:
            utils_math.math_deactivate(form_mod_math)

        return redirect(url_for('routes_input.page_input'))

    custom_options_values_inputs = parse_custom_option_values(
        input_dev, dict_controller=dict_inputs)
    custom_options_values_input_channels = parse_custom_option_values_input_channels_json(
        input_channel, dict_controller=dict_inputs, key_name='custom_channel_options')

    custom_actions = {}
    for each_input_dev in input_dev:
        if each_input_dev.device in dict_inputs and 'custom_actions' in dict_inputs[each_input_dev.device]:
            custom_actions[each_input_dev.device] = True

    # Generate dict that incorporate user-added measurements/units
    dict_outputs = parse_output_information()
    dict_units = add_custom_units(unit)
    dict_measurements = add_custom_measurements(measurement)

    # Create list of choices to be used in dropdown menus
    choices_function = utils_general.choices_functions(
        function, dict_units, dict_measurements)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_math = utils_general.choices_maths(
        math, dict_units, dict_measurements)
    choices_method = utils_general.choices_methods(method)
    choices_output = utils_general.choices_outputs(
        output, dict_units, dict_measurements)
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

    # Create dict of Math names
    names_math = {}
    all_elements = math
    for each_element in all_elements:
        names_math[each_element.unique_id] = '[{id:02d}] ({uid}) {name}'.format(
            id=each_element.id,
            uid=each_element.unique_id.split('-')[0],
            name=each_element.name)

    # Create list of file names from the math_options directory
    # Used in generating the correct options for each math controller
    math_templates = []
    math_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/data_options/math_options')
    for (_, _, file_names) in os.walk(math_path):
        math_templates.extend(file_names)
        break

    # Create list of file names from the input_options directory
    # Used in generating the correct options for each input controller
    input_templates = []
    input_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/data_options/input_options')
    for (_, _, file_names) in os.walk(input_path):
        input_templates.extend(file_names)
        break

    # If DS18B20 inputs added, compile a list of detected inputs
    devices_1wire_w1thermsensor = []
    if os.path.isdir(PATH_1WIRE):
        for each_name in os.listdir(PATH_1WIRE):
            if 'bus' not in each_name and '-' in each_name:
                devices_1wire_w1thermsensor.append(
                    {'name': each_name, 'value': each_name.split('-')[1]}
                )

    # Add 1-wire devices from ow-shell (if installed)
    devices_1wire_ow_shell = []
    if current_app.config['TESTING']:
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
                from mycodo.devices.atlas_scientific_ftdi import get_ftdi_device_list
                ftdi_devices = get_ftdi_device_list()
                break

    if not input_type:
        return render_template('pages/input.html',
                               and_=and_,
                               choices_function=choices_function,
                               choices_input=choices_input,
                               choices_math=choices_math,
                               choices_output=choices_output,
                               choices_measurement=choices_measurement,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               choices_pid_devices=choices_pid_devices,
                               choices_unit=choices_unit,
                               custom_actions=custom_actions,
                               custom_options_values_inputs=custom_options_values_inputs,
                               custom_options_values_input_channels=custom_options_values_input_channels,
                               dict_inputs=dict_inputs,
                               dict_measurements=dict_measurements,
                               dict_units=dict_units,
                               display_order_input=display_order_input,
                               display_order_math=display_order_math,
                               form_base=form_base,
                               form_add_input=form_add_input,
                               form_mod_input=form_mod_input,
                               form_mod_average_single=form_mod_average_single,
                               form_mod_sum_single=form_mod_sum_single,
                               form_mod_redundancy=form_mod_redundancy,
                               form_mod_difference=form_mod_difference,
                               form_mod_equation=form_mod_equation,
                               form_mod_humidity=form_mod_humidity,
                               form_mod_math=form_mod_math,
                               form_mod_math_measurement=form_mod_math_measurement,
                               form_mod_verification=form_mod_verification,
                               form_mod_misc=form_mod_misc,
                               ftdi_devices=ftdi_devices,
                               input_channel=input_channel,
                               input_templates=input_templates,
                               math_info=MATH_INFO,
                               math_templates=math_templates,
                               names_input=names_input,
                               names_math=names_math,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_math=Math,
                               user=user,
                               devices_1wire_ow_shell=devices_1wire_ow_shell,
                               devices_1wire_w1thermsensor=devices_1wire_w1thermsensor)
    elif input_type == 'entry':
        return render_template('pages/data_options/input_entry.html',
                               and_=and_,
                               choices_function=choices_function,
                               choices_input=choices_input,
                               choices_math=choices_math,
                               choices_output=choices_output,
                               choices_measurement=choices_measurement,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               choices_pid_devices=choices_pid_devices,
                               choices_unit=choices_unit,
                               custom_actions=custom_actions,
                               custom_options_values_inputs=custom_options_values_inputs,
                               custom_options_values_input_channels=custom_options_values_input_channels,
                               dict_inputs=dict_inputs,
                               dict_measurements=dict_measurements,
                               dict_units=dict_units,
                               display_order_input=display_order_input,
                               display_order_math=display_order_math,
                               each_input=each_input,
                               form_add_input=form_add_input,
                               form_mod_input=form_mod_input,
                               form_mod_average_single=form_mod_average_single,
                               form_mod_sum_single=form_mod_sum_single,
                               form_mod_redundancy=form_mod_redundancy,
                               form_mod_difference=form_mod_difference,
                               form_mod_equation=form_mod_equation,
                               form_mod_humidity=form_mod_humidity,
                               form_mod_math=form_mod_math,
                               form_mod_math_measurement=form_mod_math_measurement,
                               form_mod_verification=form_mod_verification,
                               form_mod_misc=form_mod_misc,
                               ftdi_devices=ftdi_devices,
                               input_channel=input_channel,
                               input_templates=input_templates,
                               math_info=MATH_INFO,
                               math_templates=math_templates,
                               names_input=names_input,
                               names_math=names_math,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_math=Math,
                               user=user,
                               devices_1wire_ow_shell=devices_1wire_ow_shell,
                               devices_1wire_w1thermsensor=devices_1wire_w1thermsensor)
    elif input_type == 'options':
        return render_template('pages/data_options/input_options.html',
                               and_=and_,
                               choices_function=choices_function,
                               choices_input=choices_input,
                               choices_math=choices_math,
                               choices_output=choices_output,
                               choices_measurement=choices_measurement,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               choices_pid_devices=choices_pid_devices,
                               choices_unit=choices_unit,
                               custom_actions=custom_actions,
                               custom_options_values_inputs=custom_options_values_inputs,
                               custom_options_values_input_channels=custom_options_values_input_channels,
                               dict_inputs=dict_inputs,
                               dict_measurements=dict_measurements,
                               dict_units=dict_units,
                               display_order_input=display_order_input,
                               display_order_math=display_order_math,
                               each_input=each_input,
                               form_add_input=form_add_input,
                               form_mod_input=form_mod_input,
                               form_mod_average_single=form_mod_average_single,
                               form_mod_sum_single=form_mod_sum_single,
                               form_mod_redundancy=form_mod_redundancy,
                               form_mod_difference=form_mod_difference,
                               form_mod_equation=form_mod_equation,
                               form_mod_humidity=form_mod_humidity,
                               form_mod_math=form_mod_math,
                               form_mod_math_measurement=form_mod_math_measurement,
                               form_mod_verification=form_mod_verification,
                               form_mod_misc=form_mod_misc,
                               ftdi_devices=ftdi_devices,
                               input_channel=input_channel,
                               input_templates=input_templates,
                               math_info=MATH_INFO,
                               math_templates=math_templates,
                               names_input=names_input,
                               names_math=names_math,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_math=Math,
                               user=user,
                               devices_1wire_ow_shell=devices_1wire_ow_shell,
                               devices_1wire_w1thermsensor=devices_1wire_w1thermsensor)
