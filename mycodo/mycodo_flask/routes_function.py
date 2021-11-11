# coding=utf-8
""" collection of Function endpoints """
import datetime
import json
import logging

import flask_login
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.blueprints import Blueprint
from sqlalchemy import and_

from mycodo.config import CONDITIONAL_CONDITIONS
from mycodo.config import FUNCTIONS
from mycodo.config import FUNCTION_ACTION_INFO
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Function
from mycodo.databases.models import FunctionChannel
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import Math
from mycodo.databases.models import Measurement
from mycodo.databases.models import Method
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.databases.models import Trigger
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_conditional
from mycodo.mycodo_flask.forms import forms_custom_controller
from mycodo.mycodo_flask.forms import forms_function
from mycodo.mycodo_flask.forms import forms_pid
from mycodo.mycodo_flask.forms import forms_trigger
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_conditional
from mycodo.mycodo_flask.utils import utils_controller
from mycodo.mycodo_flask.utils import utils_function
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_pid
from mycodo.mycodo_flask.utils import utils_trigger
from mycodo.mycodo_flask.utils.utils_misc import determine_controller_type
from mycodo.utils.functions import parse_function_information
from mycodo.utils.outputs import output_types
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.sunriseset import Sun
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import parse_custom_option_values
from mycodo.utils.system_pi import parse_custom_option_values_function_channels_json

logger = logging.getLogger('mycodo.mycodo_flask.routes_function')

blueprint = Blueprint('routes_function',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.route('/function_submit', methods=['POST'])
@flask_login.login_required
def page_function_submit():
    """ Submit form for Data page """
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    page_refresh = False
    action_id = None
    condition_id = None
    function_id = None
    dep_unmet = ''
    dep_name = ''
    dep_list = []
    dep_message = ''

    if not utils_general.user_has_permission('edit_controllers'):
        messages["error"].append("Your permissions do not allow this action")

    form_actions = forms_function.Actions()
    form_add_function = forms_function.FunctionAdd()
    form_conditional = forms_conditional.Conditional()
    form_conditional_conditions = forms_conditional.ConditionalConditions()
    form_function = forms_custom_controller.CustomController()
    form_function_base = forms_function.FunctionMod()
    form_mod_pid_base = forms_pid.PIDModBase()
    form_mod_pid_output_raise = forms_pid.PIDModRelayRaise()
    form_mod_pid_output_lower = forms_pid.PIDModRelayLower()
    form_mod_pid_pwm_raise = forms_pid.PIDModPWMRaise()
    form_mod_pid_pwm_lower = forms_pid.PIDModPWMLower()
    form_mod_pid_value_raise = forms_pid.PIDModValueRaise()
    form_mod_pid_value_lower = forms_pid.PIDModValueLower()
    form_mod_pid_volume_raise = forms_pid.PIDModVolumeRaise()
    form_mod_pid_volume_lower = forms_pid.PIDModVolumeLower()
    form_trigger = forms_trigger.Trigger()

    if not messages["error"]:
        if form_add_function.function_add.data:
            (messages,
             dep_name,
             dep_list,
             dep_message,
             function_id) = utils_function.function_add(
                form_add_function)
            if dep_list:
                dep_unmet = form_add_function.function_type.data
        else:
            function_id = form_function_base.function_id.data
            controller_type = determine_controller_type(function_id)
            if form_function_base.function_mod.data:
                if controller_type == "Conditional":
                    messages = utils_conditional.conditional_mod(
                        form_conditional)
                elif controller_type == "PID":
                    messages, page_refresh = utils_pid.pid_mod(
                        form_mod_pid_base,
                        form_mod_pid_pwm_raise,
                        form_mod_pid_pwm_lower,
                        form_mod_pid_output_raise,
                        form_mod_pid_output_lower,
                        form_mod_pid_value_raise,
                        form_mod_pid_value_lower,
                        form_mod_pid_volume_raise,
                        form_mod_pid_volume_lower)
                elif controller_type == "Trigger":
                    messages = utils_trigger.trigger_mod(form_trigger)
                elif controller_type == "Function":
                    messages = utils_function.function_mod(form_function_base)
                elif controller_type == "Function_Custom":
                    messages, page_refresh = utils_controller.controller_mod(
                        form_function, request.form)
            elif form_function_base.function_delete.data:
                if controller_type == "Conditional":
                    messages = utils_conditional.conditional_del(function_id)
                elif controller_type == "PID":
                    messages = utils_pid.pid_del(function_id)
                elif controller_type == "Trigger":
                    messages = utils_trigger.trigger_del(function_id)
                elif controller_type == "Function":
                    messages = utils_function.function_del(function_id)
                elif controller_type == "Function_Custom":
                    messages = utils_controller.controller_del(function_id)
            elif form_function_base.function_activate.data:
                if controller_type == "Conditional":
                    messages = utils_conditional.conditional_activate(
                        function_id)
                elif controller_type == "PID":
                    messages = utils_pid.pid_activate(function_id)
                elif controller_type == "Trigger":
                    messages = utils_trigger.trigger_activate(function_id)
                elif controller_type == "Function_Custom":
                    messages = utils_controller.controller_activate(
                        function_id)
            elif form_function_base.function_deactivate.data:
                if controller_type == "Conditional":
                    messages = utils_conditional.conditional_deactivate(
                        function_id)
                elif controller_type == "PID":
                    messages = utils_pid.pid_deactivate(function_id)
                elif controller_type == "Trigger":
                    messages = utils_trigger.trigger_deactivate(function_id)
                elif controller_type == "Function_Custom":
                    messages = utils_controller.controller_deactivate(
                        function_id)
            elif form_function_base.execute_all_actions.data:
                if controller_type == "Conditional":
                    messages = utils_function.action_execute_all(
                        form_conditional)
                elif controller_type == "Trigger":
                    messages = utils_function.action_execute_all(
                        form_conditional)
                elif controller_type == "Function":
                    messages = utils_function.action_execute_all(
                        form_conditional)

            # PID
            elif form_mod_pid_base.pid_hold.data:
                messages = utils_pid.pid_manipulate(
                    form_mod_pid_base.function_id.data, 'Hold')
            elif form_mod_pid_base.pid_pause.data:
                messages = utils_pid.pid_manipulate(
                    form_mod_pid_base.function_id.data, 'Pause')
            elif form_mod_pid_base.pid_resume.data:
                messages = utils_pid.pid_manipulate(
                    form_mod_pid_base.function_id.data, 'Resume')

            # Actions
            elif form_function_base.add_action.data:
                (messages,
                 dep_name,
                 dep_list,
                 action_id,
                 page_refresh) = utils_function.action_add(form_function_base)
                if dep_list:
                    dep_unmet = form_function_base.action_type.data
            elif form_actions.save_action.data:
                messages = utils_function.action_mod(
                    form_actions, request.form)
            elif form_actions.delete_action.data:
                messages = utils_function.action_del(form_actions)
                page_refresh = True
                action_id = form_actions.function_action_id.data

            # Conditions
            elif form_conditional.add_condition.data:
                (messages,
                 condition_id) = utils_conditional.conditional_condition_add(
                    form_conditional)
                page_refresh = True
                function_id = form_actions.function_id.data
            elif form_conditional_conditions.save_condition.data:
                messages = utils_conditional.conditional_condition_mod(
                    form_conditional_conditions)
            elif form_conditional_conditions.delete_condition.data:
                messages = utils_conditional.conditional_condition_del(
                    form_conditional_conditions)
                page_refresh = True
                condition_id = form_conditional_conditions.conditional_condition_id.data

            # Custom action
            else:
                custom_button = False
                for key in request.form.keys():
                    if key.startswith('custom_button_'):
                        custom_button = True
                        break
                if custom_button:
                    messages = utils_general.custom_action(
                        "Function_Custom",
                        parse_function_information(),
                        form_function.function_id.data,
                        request.form)
                else:
                    messages["error"].append("Unknown function directive")

    return jsonify(data={
        'action_id': action_id,
        'condition_id': condition_id,
        'function_id': function_id,
        'dep_name': dep_name,
        'dep_list': dep_list,
        'dep_unmet': dep_unmet,
        'dep_message': dep_message,
        'messages': messages,
        "page_refresh": page_refresh
    })


@blueprint.route('/save_function_layout', methods=['POST'])
def save_function_layout():
    """Save positions of functions"""
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))
    data = request.get_json()
    keys = ('id', 'y')
    for each_function in data:
        if all(k in each_function for k in keys):
            controller_type = determine_controller_type(each_function['id'])

            if controller_type == "Conditional":
                mod_device = Conditional.query.filter(
                    Conditional.unique_id == each_function['id']).first()
            elif controller_type == "PID":
                mod_device = PID.query.filter(
                    PID.unique_id == each_function['id']).first()
            elif controller_type == "Trigger":
                mod_device = Trigger.query.filter(
                    Trigger.unique_id == each_function['id']).first()
            elif controller_type == "Function":
                mod_device = Function.query.filter(
                    Function.unique_id == each_function['id']).first()
            elif controller_type == "Function_Custom":
                mod_device = CustomController.query.filter(
                    CustomController.unique_id == each_function['id']).first()
            else:
                logger.info("Could not find controller with ID {}".format(
                    each_function['id']))
                return "error"
            if mod_device:
                mod_device.position_y = each_function['y']
    db.session.commit()
    return "success"


@blueprint.route('/function', methods=('GET', 'POST'))
@flask_login.login_required
def page_function():
    """ Display Function page options """
    function_type = request.args.get('function_type', None)
    function_id = request.args.get('function_id', None)
    action_id = request.args.get('action_id', None)
    condition_id = request.args.get('condition_id', None)
    each_function = None
    each_action = None
    each_condition = None
    function_page_entry = None
    function_page_options = None

    if function_type in ['entry', 'options', 'conditions', 'actions'] and function_id != '0':
        controller_type = determine_controller_type(function_id)
        if controller_type == "Conditional":
            each_function = Conditional.query.filter(
                Conditional.unique_id == function_id).first()
            function_page_entry = 'pages/function_options/conditional_entry.html'
            function_page_options = 'pages/function_options/conditional_options.html'
        elif controller_type == "PID":
            each_function = PID.query.filter(
                PID.unique_id == function_id).first()
            function_page_entry = 'pages/function_options/pid_entry.html'
            function_page_options = 'pages/function_options/pid_options.html'
        elif controller_type == "Trigger":
            each_function = Trigger.query.filter(
                Trigger.unique_id == function_id).first()
            function_page_entry = 'pages/function_options/trigger_entry.html'
            function_page_options = 'pages/function_options/trigger_options.html'
        elif controller_type == "Function":
            each_function = Function.query.filter(
                Function.unique_id == function_id).first()
            function_page_entry = 'pages/function_options/function_entry.html'
            function_page_options = 'pages/function_options/function_options.html'
        elif controller_type == "Function_Custom":
            each_function = CustomController.query.filter(
                CustomController.unique_id == function_id).first()
            function_page_entry = 'pages/function_options/custom_function_entry.html'
            function_page_options = 'pages/function_options/custom_function_options.html'

        if function_type == 'actions':
            if action_id:
                each_action = Actions.query.filter(
                    Actions.unique_id == action_id).first()

        if function_type == 'conditions':
            if condition_id:
                each_condition = ConditionalConditions.query.filter(
                    ConditionalConditions.unique_id == condition_id).first()

    camera = Camera.query.all()
    conditional = Conditional.query.all()
    conditional_conditions = ConditionalConditions.query.all()
    function = CustomController.query.all()
    function_channel = FunctionChannel.query.all()
    function_dev = Function.query.all()
    actions = Actions.query.all()
    input_dev = Input.query.all()
    lcd = LCD.query.all()
    math = Math.query.all()
    measurement = Measurement.query.all()
    method = Method.query.all()
    tags = NoteTags.query.all()
    output = Output.query.all()
    output_channel = OutputChannel.query.all()
    pid = PID.query.all()
    trigger = Trigger.query.all()
    unit = Unit.query.all()
    user = User.query.all()

    display_order_function = csv_to_list_of_str(
        DisplayOrder.query.first().function)

    form_add_function = forms_function.FunctionAdd()
    form_mod_pid_base = forms_pid.PIDModBase()
    form_mod_pid_output_raise = forms_pid.PIDModRelayRaise()
    form_mod_pid_output_lower = forms_pid.PIDModRelayLower()
    form_mod_pid_pwm_raise = forms_pid.PIDModPWMRaise()
    form_mod_pid_pwm_lower = forms_pid.PIDModPWMLower()
    form_mod_pid_value_raise = forms_pid.PIDModValueRaise()
    form_mod_pid_value_lower = forms_pid.PIDModValueLower()
    form_mod_pid_volume_raise = forms_pid.PIDModVolumeRaise()
    form_mod_pid_volume_lower = forms_pid.PIDModVolumeLower()
    form_function_base = forms_function.FunctionMod()
    form_trigger = forms_trigger.Trigger()
    form_conditional = forms_conditional.Conditional()
    form_conditional_conditions = forms_conditional.ConditionalConditions()
    form_function = forms_custom_controller.CustomController()
    form_actions = forms_function.Actions()

    dict_controllers = parse_function_information()

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    dict_outputs = parse_output_information()

    custom_options_values_controllers = parse_custom_option_values(
        function, dict_controller=dict_controllers)
    custom_options_values_function_channels = parse_custom_option_values_function_channels_json(
        function_channel, dict_controller=function, key_name='custom_channel_options')

    # TODO: Update actions to use single-file modules and be consistent with other custom_options
    custom_options_values_actions = {}
    for each_action_dev in actions:
        try:
            custom_options_values_actions[each_action_dev.unique_id] = json.loads(each_action_dev.custom_options)
        except:
            custom_options_values_actions[each_action_dev.unique_id] = {}

    # Create lists of built-in and custom functions
    choices_functions = []
    for choice_function in FUNCTIONS:
        choices_functions.append({'value': choice_function[0], 'item': choice_function[1]})
    choices_custom_functions = utils_general.choices_custom_functions()
    # Combine function lists
    choices_functions_add = choices_functions + choices_custom_functions
    # Sort combined list
    choices_functions_add = sorted(choices_functions_add, key=lambda i: i['item'])

    custom_actions = {}
    for choice_function in function:
        if 'custom_actions' in dict_controllers[choice_function.device]:
            custom_actions[choice_function.device] = True

    choices_function = utils_general.choices_functions(
        function, dict_units, dict_measurements)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_input_devices = utils_general.choices_input_devices(input_dev)
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
    choices_measurements_units = utils_general.choices_measurements_units(
        measurement, unit)

    choices_controller_ids = utils_general.choices_controller_ids()

    actions_dict = {
        'conditional': {},
        'trigger': {}
    }
    for each_action_dev in actions:
        if (each_action_dev.function_type == 'conditional' and
                each_action_dev.unique_id not in actions_dict['conditional']):
            actions_dict['conditional'][each_action_dev.function_id] = True
        if (each_action_dev.function_type == 'trigger' and
                each_action_dev.unique_id not in actions_dict['trigger']):
            actions_dict['trigger'][each_action_dev.function_id] = True

    conditions_dict = {}
    for each_cond in conditional_conditions:
        if each_cond.unique_id not in conditions_dict:
            conditions_dict[each_cond.conditional_id] = True

    controllers = []
    controllers_all = [('Input', input_dev),
                       ('Conditional', conditional),
                       ('Function', function),
                       ('LCD', lcd),
                       ('Math', math),
                       ('PID', pid),
                       ('Trigger', trigger)]
    for each_controller in controllers_all:
        for each_cont in each_controller[1]:
            controllers.append((each_controller[0],
                                each_cont.unique_id,
                                each_cont.id,
                                each_cont.name))

    # Create dict of Function names
    names_function = {}
    all_elements = [conditional, pid, trigger, function_dev, function]
    for each_element in all_elements:
        for each_func_name in each_element:
            names_function[each_func_name.unique_id] = '[{id}] {name}'.format(
                id=each_func_name.unique_id.split('-')[0], name=each_func_name.name)

    # Calculate sunrise/sunset times if conditional controller is set up properly
    sunrise_set_calc = {}
    for each_trigger in trigger:
        if each_trigger.trigger_type == 'trigger_sunrise_sunset':
            sunrise_set_calc[each_trigger.unique_id] = {}
            try:
                sun = Sun(latitude=each_trigger.latitude,
                          longitude=each_trigger.longitude,
                          zenith=each_trigger.zenith)
                sunrise = sun.get_sunrise_time()['time_local']
                sunset = sun.get_sunset_time()['time_local']

                # Adjust for date offset
                new_date = datetime.datetime.now() + datetime.timedelta(
                    days=each_trigger.date_offset_days)

                sun = Sun(latitude=each_trigger.latitude,
                          longitude=each_trigger.longitude,
                          zenith=each_trigger.zenith,
                          day=new_date.day,
                          month=new_date.month,
                          year=new_date.year,
                          offset_minutes=each_trigger.time_offset_minutes)
                offset_rise = sun.get_sunrise_time()['time_local']
                offset_set = sun.get_sunset_time()['time_local']

                sunrise_set_calc[each_trigger.unique_id]['sunrise'] = (
                    sunrise.strftime("%Y-%m-%d %H:%M"))
                sunrise_set_calc[each_trigger.unique_id]['sunset'] = (
                    sunset.strftime("%Y-%m-%d %H:%M"))
                sunrise_set_calc[each_trigger.unique_id]['offset_sunrise'] = (
                    offset_rise.strftime("%Y-%m-%d %H:%M"))
                sunrise_set_calc[each_trigger.unique_id]['offset_sunset'] = (
                    offset_set.strftime("%Y-%m-%d %H:%M"))
            except:
                logger.exception(1)
                sunrise_set_calc[each_trigger.unique_id]['sunrise'] = None
                sunrise_set_calc[each_trigger.unique_id]['sunrise'] = None
                sunrise_set_calc[each_trigger.unique_id]['offset_sunrise'] = None
                sunrise_set_calc[each_trigger.unique_id]['offset_sunset'] = None

    if not function_type:
        return render_template('pages/function.html',
                               and_=and_,
                               actions=actions,
                               actions_dict=actions_dict,
                               camera=camera,
                               choices_controller_ids=choices_controller_ids,
                               choices_custom_functions=choices_custom_functions,
                               choices_function=choices_function,
                               choices_functions=choices_functions,
                               choices_functions_add=choices_functions_add,
                               choices_input=choices_input,
                               choices_input_devices=choices_input_devices,
                               choices_math=choices_math,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output=choices_output,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               conditional_conditions_list=CONDITIONAL_CONDITIONS,
                               conditional=conditional,
                               conditional_conditions=conditional_conditions,
                               conditions_dict=conditions_dict,
                               controllers=controllers,
                               function=function,
                               function_channel=function_channel,
                               custom_actions=custom_actions,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_controllers=custom_options_values_controllers,
                               custom_options_values_function_channels=custom_options_values_function_channels,
                               dict_controllers=dict_controllers,
                               dict_measurements=dict_measurements,
                               dict_outputs=dict_outputs,
                               dict_units=dict_units,
                               display_order_function=display_order_function,
                               form_conditional=form_conditional,
                               form_conditional_conditions=form_conditional_conditions,
                               form_function=form_function,
                               form_actions=form_actions,
                               form_add_function=form_add_function,
                               form_function_base=form_function_base,
                               form_mod_pid_base=form_mod_pid_base,
                               form_mod_pid_pwm_raise=form_mod_pid_pwm_raise,
                               form_mod_pid_pwm_lower=form_mod_pid_pwm_lower,
                               form_mod_pid_output_raise=form_mod_pid_output_raise,
                               form_mod_pid_output_lower=form_mod_pid_output_lower,
                               form_mod_pid_value_raise=form_mod_pid_value_raise,
                               form_mod_pid_value_lower=form_mod_pid_value_lower,
                               form_mod_pid_volume_raise=form_mod_pid_volume_raise,
                               form_mod_pid_volume_lower=form_mod_pid_volume_lower,
                               form_trigger=form_trigger,
                               function_action_info=FUNCTION_ACTION_INFO,
                               function_dev=function_dev,
                               function_types=FUNCTIONS,
                               input=input_dev,
                               lcd=lcd,
                               math=math,
                               method=method,
                               names_function=names_function,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               sunrise_set_calc=sunrise_set_calc,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_output=Output,
                               tags=tags,
                               trigger=trigger,
                               units=MEASUREMENTS,
                               user=user)
    elif function_type == 'entry':
        return render_template(function_page_entry,
                               and_=and_,
                               actions=actions,
                               actions_dict=actions_dict,
                               camera=camera,
                               choices_controller_ids=choices_controller_ids,
                               choices_custom_functions=choices_custom_functions,
                               choices_function=choices_function,
                               choices_functions=choices_functions,
                               choices_functions_add=choices_functions_add,
                               choices_input=choices_input,
                               choices_input_devices=choices_input_devices,
                               choices_math=choices_math,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output=choices_output,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               conditional_conditions_list=CONDITIONAL_CONDITIONS,
                               conditional=conditional,
                               conditional_conditions=conditional_conditions,
                               conditions_dict=conditions_dict,
                               controllers=controllers,
                               function=function,
                               function_channel=function_channel,
                               custom_actions=custom_actions,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_controllers=custom_options_values_controllers,
                               custom_options_values_function_channels=custom_options_values_function_channels,
                               dict_controllers=dict_controllers,
                               dict_measurements=dict_measurements,
                               dict_outputs=dict_outputs,
                               dict_units=dict_units,
                               display_order_function=display_order_function,
                               each_function=each_function,
                               form_conditional=form_conditional,
                               form_conditional_conditions=form_conditional_conditions,
                               form_function=form_function,
                               form_actions=form_actions,
                               form_add_function=form_add_function,
                               form_function_base=form_function_base,
                               form_mod_pid_base=form_mod_pid_base,
                               form_mod_pid_pwm_raise=form_mod_pid_pwm_raise,
                               form_mod_pid_pwm_lower=form_mod_pid_pwm_lower,
                               form_mod_pid_output_raise=form_mod_pid_output_raise,
                               form_mod_pid_output_lower=form_mod_pid_output_lower,
                               form_mod_pid_value_raise=form_mod_pid_value_raise,
                               form_mod_pid_value_lower=form_mod_pid_value_lower,
                               form_mod_pid_volume_raise=form_mod_pid_volume_raise,
                               form_mod_pid_volume_lower=form_mod_pid_volume_lower,
                               form_trigger=form_trigger,
                               function_action_info=FUNCTION_ACTION_INFO,
                               function_dev=function_dev,
                               function_types=FUNCTIONS,
                               input=input_dev,
                               lcd=lcd,
                               math=math,
                               method=method,
                               names_function=names_function,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               sunrise_set_calc=sunrise_set_calc,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_output=Output,
                               tags=tags,
                               trigger=trigger,
                               units=MEASUREMENTS,
                               user=user)
    elif function_type == 'options':
        return render_template(function_page_options,
                               and_=and_,
                               actions=actions,
                               actions_dict=actions_dict,
                               camera=camera,
                               choices_controller_ids=choices_controller_ids,
                               choices_custom_functions=choices_custom_functions,
                               choices_function=choices_function,
                               choices_functions=choices_functions,
                               choices_functions_add=choices_functions_add,
                               choices_input=choices_input,
                               choices_input_devices=choices_input_devices,
                               choices_math=choices_math,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output=choices_output,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               conditional_conditions_list=CONDITIONAL_CONDITIONS,
                               conditional=conditional,
                               conditional_conditions=conditional_conditions,
                               conditions_dict=conditions_dict,
                               controllers=controllers,
                               each_function=each_function,
                               function=function,
                               function_channel=function_channel,
                               custom_actions=custom_actions,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_controllers=custom_options_values_controllers,
                               custom_options_values_function_channels=custom_options_values_function_channels,
                               dict_controllers=dict_controllers,
                               dict_measurements=dict_measurements,
                               dict_outputs=dict_outputs,
                               dict_units=dict_units,
                               display_order_function=display_order_function,
                               form_conditional=form_conditional,
                               form_conditional_conditions=form_conditional_conditions,
                               form_function=form_function,
                               form_actions=form_actions,
                               form_add_function=form_add_function,
                               form_function_base=form_function_base,
                               form_mod_pid_base=form_mod_pid_base,
                               form_mod_pid_pwm_raise=form_mod_pid_pwm_raise,
                               form_mod_pid_pwm_lower=form_mod_pid_pwm_lower,
                               form_mod_pid_output_raise=form_mod_pid_output_raise,
                               form_mod_pid_output_lower=form_mod_pid_output_lower,
                               form_mod_pid_value_raise=form_mod_pid_value_raise,
                               form_mod_pid_value_lower=form_mod_pid_value_lower,
                               form_mod_pid_volume_raise=form_mod_pid_volume_raise,
                               form_mod_pid_volume_lower=form_mod_pid_volume_lower,
                               form_trigger=form_trigger,
                               function_action_info=FUNCTION_ACTION_INFO,
                               function_dev=function_dev,
                               function_types=FUNCTIONS,
                               input=input_dev,
                               lcd=lcd,
                               math=math,
                               method=method,
                               names_function=names_function,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               sunrise_set_calc=sunrise_set_calc,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_output=Output,
                               tags=tags,
                               trigger=trigger,
                               units=MEASUREMENTS,
                               user=user)
    elif function_type == 'actions':
        return render_template('pages/function_options/actions.html',
                               and_=and_,
                               actions=actions,
                               actions_dict=actions_dict,
                               camera=camera,
                               choices_controller_ids=choices_controller_ids,
                               choices_custom_functions=choices_custom_functions,
                               choices_function=choices_function,
                               choices_functions=choices_functions,
                               choices_functions_add=choices_functions_add,
                               choices_input=choices_input,
                               choices_input_devices=choices_input_devices,
                               choices_math=choices_math,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output=choices_output,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               conditional_conditions_list=CONDITIONAL_CONDITIONS,
                               conditional=conditional,
                               conditional_conditions=conditional_conditions,
                               conditions_dict=conditions_dict,
                               controllers=controllers,
                               each_action=each_action,
                               each_function=each_function,
                               function=function,
                               function_channel=function_channel,
                               custom_actions=custom_actions,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_controllers=custom_options_values_controllers,
                               custom_options_values_function_channels=custom_options_values_function_channels,
                               dict_controllers=dict_controllers,
                               dict_measurements=dict_measurements,
                               dict_outputs=dict_outputs,
                               dict_units=dict_units,
                               display_order_function=display_order_function,
                               form_conditional=form_conditional,
                               form_conditional_conditions=form_conditional_conditions,
                               form_function=form_function,
                               form_actions=form_actions,
                               form_add_function=form_add_function,
                               form_function_base=form_function_base,
                               form_mod_pid_base=form_mod_pid_base,
                               form_mod_pid_pwm_raise=form_mod_pid_pwm_raise,
                               form_mod_pid_pwm_lower=form_mod_pid_pwm_lower,
                               form_mod_pid_output_raise=form_mod_pid_output_raise,
                               form_mod_pid_output_lower=form_mod_pid_output_lower,
                               form_mod_pid_value_raise=form_mod_pid_value_raise,
                               form_mod_pid_value_lower=form_mod_pid_value_lower,
                               form_mod_pid_volume_raise=form_mod_pid_volume_raise,
                               form_mod_pid_volume_lower=form_mod_pid_volume_lower,
                               form_trigger=form_trigger,
                               function_action_info=FUNCTION_ACTION_INFO,
                               function_dev=function_dev,
                               function_types=FUNCTIONS,
                               input=input_dev,
                               lcd=lcd,
                               math=math,
                               method=method,
                               names_function=names_function,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               sunrise_set_calc=sunrise_set_calc,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_output=Output,
                               tags=tags,
                               trigger=trigger,
                               units=MEASUREMENTS,
                               user=user)
    elif function_type == 'conditions':
        return render_template('pages/function_options/conditional_condition.html',
                               and_=and_,
                               actions=actions,
                               actions_dict=actions_dict,
                               camera=camera,
                               choices_controller_ids=choices_controller_ids,
                               choices_custom_functions=choices_custom_functions,
                               choices_function=choices_function,
                               choices_functions=choices_functions,
                               choices_functions_add=choices_functions_add,
                               choices_input=choices_input,
                               choices_input_devices=choices_input_devices,
                               choices_math=choices_math,
                               choices_measurements_units=choices_measurements_units,
                               choices_method=choices_method,
                               choices_output=choices_output,
                               choices_output_channels=choices_output_channels,
                               choices_output_channels_measurements=choices_output_channels_measurements,
                               choices_pid=choices_pid,
                               conditional_conditions_list=CONDITIONAL_CONDITIONS,
                               conditional=conditional,
                               conditional_conditions=conditional_conditions,
                               conditions_dict=conditions_dict,
                               controllers=controllers,
                               each_action=each_action,
                               each_condition=each_condition,
                               each_function=each_function,
                               function=function,
                               function_channel=function_channel,
                               custom_actions=custom_actions,
                               custom_options_values_actions=custom_options_values_actions,
                               custom_options_values_controllers=custom_options_values_controllers,
                               custom_options_values_function_channels=custom_options_values_function_channels,
                               dict_controllers=dict_controllers,
                               dict_measurements=dict_measurements,
                               dict_outputs=dict_outputs,
                               dict_units=dict_units,
                               display_order_function=display_order_function,
                               form_conditional=form_conditional,
                               form_conditional_conditions=form_conditional_conditions,
                               form_function=form_function,
                               form_actions=form_actions,
                               form_add_function=form_add_function,
                               form_function_base=form_function_base,
                               form_mod_pid_base=form_mod_pid_base,
                               form_mod_pid_pwm_raise=form_mod_pid_pwm_raise,
                               form_mod_pid_pwm_lower=form_mod_pid_pwm_lower,
                               form_mod_pid_output_raise=form_mod_pid_output_raise,
                               form_mod_pid_output_lower=form_mod_pid_output_lower,
                               form_mod_pid_value_raise=form_mod_pid_value_raise,
                               form_mod_pid_value_lower=form_mod_pid_value_lower,
                               form_mod_pid_volume_raise=form_mod_pid_volume_raise,
                               form_mod_pid_volume_lower=form_mod_pid_volume_lower,
                               form_trigger=form_trigger,
                               function_action_info=FUNCTION_ACTION_INFO,
                               function_dev=function_dev,
                               function_types=FUNCTIONS,
                               input=input_dev,
                               lcd=lcd,
                               math=math,
                               method=method,
                               names_function=names_function,
                               output=output,
                               output_types=output_types(),
                               pid=pid,
                               sunrise_set_calc=sunrise_set_calc,
                               table_conversion=Conversion,
                               table_device_measurements=DeviceMeasurements,
                               table_input=Input,
                               table_output=Output,
                               tags=tags,
                               trigger=trigger,
                               units=MEASUREMENTS,
                               user=user)
    else:
        return "Could not determine template"


@blueprint.route('/function_status/<unique_id>', methods=('GET', 'POST'))
@flask_login.login_required
def function_status(unique_id):
    try:
        control = DaemonControl()
        return jsonify(control.function_status(unique_id))
    except Exception as err:
        logger.error("Function Status Error: {}".format(err))
        return jsonify({'error': err})
