# -*- coding: utf-8 -*-
import json
import logging
import threading

import sqlalchemy
from flask import current_app
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.config import FUNCTION_INFO
from mycodo.config import PID_INFO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases import set_uuid
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Function
from mycodo.databases.models import FunctionChannel
from mycodo.databases.models import PID
from mycodo.databases.models import Trigger
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import custom_channel_options_return_json
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_json
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.conditional import save_conditional_code
from mycodo.utils.functions import parse_function_information
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import str_is_float

logger = logging.getLogger(__name__)

#
# Function manipulation
#

def function_add(form_add_func):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    new_function_id = None
    list_unmet_deps = []
    dep_name = None
    dep_message = ''

    function_name = form_add_func.function_type.data

    dict_controllers = parse_function_information()

    if not current_app.config['TESTING']:
        dep_unmet, _, dep_message = return_dependencies(function_name)
        if dep_unmet:
            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[0])
            messages["error"].append(
                "{dev} has unmet dependencies. They must be installed before the Function can be added.".format(
                    dev=function_name))
            if function_name in dict_controllers:
                dep_name = dict_controllers[function_name]['function_name']
            else:
                messages["error"].append("Function not found: {}".format(function_name))

            return messages, dep_name, list_unmet_deps, dep_message, None

    new_func = None

    try:
        if function_name == 'conditional_conditional':
            new_func = Conditional()
            new_func.position_y = 999
            new_func.conditional_statement = '''
# Example code for learning how to use a Conditional. See the manual for more information.

self.logger.info("This INFO log entry will appear in the Daemon Log")
self.logger.error("This ERROR log entry will appear in the Daemon Log")

if not hasattr(self, "loop_count"):  # Initialize objects saved across executions
    self.loop_count = 1
else:
    self.loop_count += 1

# Replace "asdf1234" with a Condition ID
measurement = self.condition("{asdf1234}") 
self.logger.info("Check this measurement in the Daemon Log. The value is {val}".format(val=measurement))

if measurement is not None:  # If a measurement exists
    self.message += "This message appears in email alerts and notes.\\n"

    if measurement < 23:  # If the measurement is less than 23
        self.message += "Measurement is too Low! Measurement is {meas}\\n".format(meas=measurement)
        self.run_all_actions(message=self.message)  # Run all actions sequentially

    elif measurement > 27:  # Else If the measurement is greater than 27
        self.message += "Measurement is too High! Measurement is {meas}\\n".format(meas=measurement)
        # Replace "qwer5678" with an Action ID
        self.run_action("{qwer5678}", message=self.message)  # Run a single specific Action'''

            new_func.conditional_status = '''
# Example code to provide a return status for other controllers and widgets.
status_dict = {
    'string_status': "This is the demo status of the conditional controller. "
                     "The controller has looped {} times".format(self.loop_count),
    'loop_count': self.loop_count,
    'error': []
}
return status_dict'''

            if not messages["error"]:
                new_func.save()
                new_function_id = new_func.unique_id
                if not current_app.config['TESTING']:
                    save_conditional_code(
                        messages["error"],
                        new_func.conditional_statement,
                        new_func.conditional_status,
                        new_func.unique_id,
                        ConditionalConditions.query.all(),
                        Actions.query.all(),
                        test=False)

        elif function_name == 'pid_pid':
            new_func = PID()
            new_func.position_y = 999
            new_func.save()
            new_function_id = new_func.unique_id

            for each_channel, measure_info in PID_INFO['measure'].items():
                new_measurement = DeviceMeasurements()

                if 'name' in measure_info:
                    new_measurement.name = measure_info['name']
                if 'measurement_type' in measure_info:
                    new_measurement.measurement_type = measure_info['measurement_type']

                new_measurement.device_id = new_func.unique_id
                new_measurement.measurement = measure_info['measurement']
                new_measurement.unit = measure_info['unit']
                new_measurement.channel = each_channel
                if not messages["error"]:
                    new_measurement.save()

        elif function_name in ['trigger_edge',
                               'trigger_output',
                               'trigger_output_pwm',
                               'trigger_timer_daily_time_point',
                               'trigger_timer_daily_time_span',
                               'trigger_timer_duration',
                               'trigger_run_pwm_method',
                               'trigger_sunrise_sunset']:
            new_func = Trigger()
            new_func.name = '{}'.format(FUNCTION_INFO[function_name]['name'])
            new_func.trigger_type = function_name
            new_func.position_y = 999

            if not messages["error"]:
                new_func.save()
                new_function_id = new_func.unique_id

        elif function_name == 'function_actions':
            new_func = Function()
            new_func.position_y = 999
            new_func.function_type = function_name
            if not messages["error"]:
                new_func.save()
                new_function_id = new_func.unique_id

        elif function_name in dict_controllers:
            # Custom Function Controller
            new_func = CustomController()
            new_func.device = function_name
            new_func.position_y = 999

            if 'function_name' in dict_controllers[function_name]:
                new_func.name = dict_controllers[function_name]['function_name']
            else:
                new_func.name = 'Function Name'

            # Generate string to save from custom options
            messages["error"], custom_options = custom_options_return_json(
                messages["error"], dict_controllers, device=function_name, use_defaults=True)
            new_func.custom_options = custom_options

            new_func.unique_id = set_uuid()

            if ('execute_at_creation' in dict_controllers[new_func.device] and
                    not current_app.config['TESTING']):
                messages["error"], new_func = dict_controllers[new_func.device]['execute_at_creation'](
                    messages["error"], new_func, dict_controllers[new_func.device])

            if not messages["error"]:
                new_func.save()
                new_function_id = new_func.unique_id

        elif function_name == '':
            messages["error"].append("Must select a function type")
        else:
            messages["error"].append("Unknown function type: '{}'".format(
                function_name))

        if not messages["error"]:
            if function_name in dict_controllers:
                #
                # Add measurements defined in the Function Module
                #

                if ('measurements_dict' in dict_controllers[function_name] and
                        dict_controllers[function_name]['measurements_dict']):
                    for each_channel in dict_controllers[function_name]['measurements_dict']:
                        measure_info = dict_controllers[function_name]['measurements_dict'][each_channel]
                        new_measurement = DeviceMeasurements()
                        new_measurement.device_id = new_func.unique_id
                        if 'name' in measure_info:
                            new_measurement.name = measure_info['name']
                        else:
                            new_measurement.name = ""
                        if 'measurement' in measure_info:
                            new_measurement.measurement = measure_info['measurement']
                        else:
                            new_measurement.measurement = ""
                        if 'unit' in measure_info:
                            new_measurement.unit = measure_info['unit']
                        else:
                            new_measurement.unit = ""
                        new_measurement.channel = each_channel
                        new_measurement.save()

                #
                # If there are a variable number of measurements
                #

                elif ('measurements_variable_amount' in dict_controllers[function_name] and
                        dict_controllers[function_name]['measurements_variable_amount']):
                    # Add first default measurement with empty unit and measurement
                    new_measurement = DeviceMeasurements()
                    new_measurement.name = ""
                    new_measurement.device_id = new_func.unique_id
                    new_measurement.measurement = ""
                    new_measurement.unit = ""
                    new_measurement.channel = 0
                    new_measurement.save()

                #
                # Add channels defined in the Function Module
                #

                if 'channels_dict' in dict_controllers[function_name]:
                    for each_channel, channel_info in dict_controllers[function_name]['channels_dict'].items():
                        new_channel = FunctionChannel()
                        new_channel.channel = each_channel
                        new_channel.function_id = new_func.unique_id

                        # Generate string to save from custom options
                        messages["error"], custom_options = custom_channel_options_return_json(
                            messages["error"], dict_controllers, None,
                            new_func.unique_id, each_channel,
                            device=new_func.device, use_defaults=True)
                        new_channel.custom_options = custom_options

                        new_channel.save()

            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['add']['title'],
                controller=TRANSLATIONS['function']['title']))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        logger.exception("Add Function")
        messages["error"].append(str(except_msg))

    return messages, dep_name, list_unmet_deps, dep_message, new_function_id


def function_mod(form):
    """Modify a Function"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": [],
        "name": None,
        "return_text": []
    }

    try:
        func_mod = Function.query.filter(
            Function.unique_id == form.function_id.data).first()

        func_mod.name = form.name.data
        messages["name"] = form.name.data
        func_mod.log_level_debug = form.log_level_debug.data

        if not messages["error"]:
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller=TRANSLATIONS['function']['title']))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def function_del(function_id):
    """Delete a Function"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        # Delete Actions
        actions = Actions.query.filter(
            Actions.function_id == function_id).all()
        for each_action in actions:
            delete_entry_with_id(
                Actions, each_action.unique_id, flash_message=False)

        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == function_id).all()
        for each_measurement in device_measurements:
            delete_entry_with_id(
                DeviceMeasurements,
                each_measurement.unique_id,
                flash_message=False)

        delete_entry_with_id(Function, function_id, flash_message=False)

        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['delete']['title'],
            controller=TRANSLATIONS['function']['title']))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def action_add(form):
    """Add an Action"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    action_id = None
    dep_name = ""
    page_refresh = False

    dep_unmet, _, dep_message = return_dependencies(form.action_type.data)
    if dep_unmet:
        list_unmet_deps = []
        for each_dep in dep_unmet:
            list_unmet_deps.append(each_dep[0])
        messages["error"].append(
            "{dev} has unmet dependencies. They must be installed before the Action can be added.".format(
                dev=form.action_type.data))
        dep_name = form.action_type.data

        return messages, dep_name, list_unmet_deps, dep_message, None

    if form.function_type.data == 'conditional':
        func = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'trigger':
        func = Trigger.query.filter(
            Trigger.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'function':
        func = Function.query.filter(
            Function.unique_id == form.function_id.data).first()
    else:
        func = None
        messages["error"].append("Invalid Function type: {}".format(form.function_type.data))

    if form.function_type.data != 'function' and func and func.is_activated:
        messages["error"].append("Deactivate before adding an Action")

    if form.action_type.data == '':
        messages["error"].append("Must select an action")

    try:
        new_action = Actions()
        new_action.function_id = form.function_id.data
        new_action.function_type = form.function_type.data
        new_action.action_type = form.action_type.data

        if form.action_type.data == 'command':
            new_action.do_output_state = 'mycodo'  # user to execute shell command as

        elif form.action_type.data == 'mqtt_publish':
            # Fill in default values
            # TODO: Future improvements to actions will be single-file modules, making this obsolete
            custom_options = {
                "hostname": "localhost",
                "port": 1883,
                "topic": "paho/test/single",
                "keepalive": 60,
                "clientid": "mycodo_mqtt_client",
                "login": False,
                "username": "user",
                "password": ""
            }
            new_action.custom_options = json.dumps(custom_options)

        if not messages["error"]:
            new_action.save()
            action_id = new_action.unique_id
            page_refresh = True
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['add']['title'],
                controller=TRANSLATIONS['actions']['title']))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages, dep_name, dep_unmet, action_id, page_refresh


def action_mod(form, request_form):
    """Modify an Action"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    mod_action = Actions.query.filter(
        Actions.unique_id == form.function_action_id.data).first()

    if not action_mod:
        messages["error"].append("Action not found")

    messages["error"] = check_form_actions(form, messages["error"])

    try:
        if mod_action.action_type == 'pause_actions':
            mod_action.pause_duration = form.pause_duration.data

        elif mod_action.action_type == 'output':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_state = form.do_output_state.data
            mod_action.do_output_duration = form.do_output_duration.data

        elif mod_action.action_type == 'output_pwm':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_pwm = form.do_output_pwm.data

        elif mod_action.action_type == 'output_ramp_pwm':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_pwm = form.do_output_pwm.data
            mod_action.do_output_pwm2 = form.do_output_pwm2.data
            mod_action.do_action_string = form.do_action_string.data
            mod_action.do_output_duration = form.do_output_duration.data

        elif mod_action.action_type == 'output_value':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_amount = form.do_output_amount.data

        elif mod_action.action_type == 'output_volume':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_amount = form.do_output_amount.data

        elif mod_action.action_type in ['activate_controller',
                                        'deactivate_controller',
                                        'activate_pid',
                                        'deactivate_pid',
                                        'resume_pid',
                                        'pause_pid',
                                        'activate_timer',
                                        'deactivate_timer',
                                        'clear_total_volume',
                                        'input_force_measurements']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type in ['setpoint_pid',
                                        'setpoint_pid_raise',
                                        'setpoint_pid_lower']:
            if not str_is_float(form.do_action_string.data):
                messages["error"].append("Setpoint value must be an integer or float value")
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type == 'method_pid':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type in ['email',
                                        'email_multiple']:
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type in ['photo_email',
                                        'video_email']:
            mod_action.do_action_string = form.do_action_string.data
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_camera_duration = form.do_camera_duration.data

        elif mod_action.action_type in ['flash_lcd_on',
                                        'flash_lcd_off',
                                        'lcd_backlight_off',
                                        'lcd_backlight_on']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type == 'lcd_backlight_color':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type in ['photo', 'camera_timelapse_pause', 'camera_timelapse_resume']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type == 'video':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_camera_duration = form.do_camera_duration.data

        elif mod_action.action_type == 'command':
            mod_action.do_action_string = form.do_action_string.data
            mod_action.do_output_state = form.do_output_state.data

        elif mod_action.action_type == 'create_note':
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type in ['system_restart',
                                        'system_shutdown']:
            pass  # No options

        elif mod_action.action_type == 'webhook':
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type == 'mqtt_publish':
            custom_options = {
                "hostname": request_form['hostname'],
                "port": int(request_form['port']),
                "topic": request_form['topic'],
                "keepalive": int(request_form['keepalive']),
                "clientid": request_form['clientid'],
                "username": request_form['username'],
                "password": request_form['password']
            }
            if 'login' in request_form:
                custom_options["login"] = True
            else:
                custom_options["login"] = False
            mod_action.custom_options = json.dumps(custom_options)

        if not messages["error"]:
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller=TRANSLATIONS['actions']['title']))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def action_del(form):
    """Delete an Action"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    conditional = Conditional.query.filter(
        Conditional.unique_id == form.function_id.data).first()

    trigger = Trigger.query.filter(
        Trigger.unique_id == form.function_id.data).first()

    if ((conditional and conditional.is_activated) or
            (trigger and trigger.is_activated)):
        messages["error"].append(
            "Deactivate the Conditional before deleting an Action")

    try:
        if not messages["error"]:
            function_action_id = Actions.query.filter(
                Actions.unique_id == form.function_action_id.data).first().unique_id
            delete_entry_with_id(
                Actions, function_action_id, flash_message=False)
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['delete']['title'],
                controller=TRANSLATIONS['actions']['title']))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def action_execute_all(form):
    """Execute All Conditional Actions"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    function_type = None
    func = None

    if form.function_type.data == 'conditional':
        function_type = TRANSLATIONS['conditional']['title']
        func = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'trigger':
        function_type = TRANSLATIONS['trigger']['title']
        func = Trigger.query.filter(
            Trigger.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'function_actions':
        function_type = TRANSLATIONS['function']['title']
        func = Function.query.filter(
            Function.unique_id == form.function_id.data).first()
    else:
        messages["error"].append("Unknown Function type: '{}'".format(
            form.function_type.data))

    if form.function_type.data != 'function_actions' and func and not func.is_activated:
        messages["error"].append("Activate the Controller before testing all Actions")

    try:
        if not messages["error"]:
            debug = bool(hasattr(form, 'log_level_debug') and form.log_level_debug.data)
            control = DaemonControl()
            trigger_all_actions = threading.Thread(
                target=control.trigger_all_actions,
                args=(form.function_id.data,),
                kwargs={
                    'message': "Triggering all actions of function {}".format(form.function_id.data),
                    'debug': debug
                }
            )
            trigger_all_actions.start()
            messages["success"].append('{action} {controller}'.format(
                action=gettext("Execute All"),
                controller='{} {}'.format(function_type,
                                          TRANSLATIONS['actions']['title'])))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def check_form_actions(form, error):
    """Check if the Actions form inputs are valid"""
    action = Actions.query.filter(
        Actions.unique_id == form.function_action_id.data).first()
    if action.action_type == 'command':
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Command must be set")
    elif action.action_type == 'output':
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Output must be set")
        if not form.do_output_state.data or form.do_output_state.data == '':
            error.append("State must be set")
    elif action.action_type == 'output_pwm':
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Output must be set")
        if form.do_output_pwm.data < 0 or form.do_output_pwm.data > 100 or form.do_output_pwm.data == '':
            error.append("Duty Cycle must be set (0 <= duty cycle <= 100)")
    elif action.action_type == 'output_value':
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Output must be set")
        if not form.do_output_amount.data:
            error.append("Value must be set")
    elif action.action_type == 'output_volume':
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Output must be set")
        if not form.do_output_amount.data:
            error.append("Volume must be set")
    elif action.action_type in ['activate_pid',
                                'deactivate_pid',
                                'resume_pid',
                                'pause_pid']:
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("ID must be set")
    elif action.action_type == 'email':
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Email must be set")
    elif action.action_type in ['photo_email', 'video_email']:
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("Email must be set")
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("Camera must be set")
        if (action.action_type == 'video_email' and
                Camera.query.filter(
                    and_(Camera.unique_id == form.do_unique_id.data,
                         Camera.library != 'picamera')).count()):
            error.append('Only Pi Cameras can record video')
    elif action.action_type == 'flash_lcd_on' and not form.do_unique_id.data:
        error.append("LCD must be set")
    elif action.action_type == 'lcd_backlight_color':
        if not form.do_unique_id.data:
            error.append("LCD must be set")
        try:
            tuple_colors = form.do_action_string.data.split(",")
            if len(tuple_colors) != 3:
                error.append('LCD backlight color must be in the R,G,B format "255,255,255"')

            if not is_int(tuple_colors[0]):
                error.append('Red color does not represent an integer.')
            elif int(tuple_colors[0]) < 0 or int(tuple_colors[0]) > 255:
                error.append('Red color must be >= 0 and <= 255')

            if not is_int(tuple_colors[1]):
                error.append('Blue color does not represent an integer.')
            elif int(tuple_colors[1]) < 0 or int(tuple_colors[1]) > 255:
                error.append('Blue color must be >= 0 and <= 255')

            if not is_int(tuple_colors[2]):
                error.append('Green color does not represent an integer.')
            elif int(tuple_colors[2]) < 0 or int(tuple_colors[2]) > 255:
                error.append('Green color must be >= 0 and <= 255')
        except:
            error.append('Error parsing LCD backlight color. Must be in the R,G,B format '
                         '"255,255,255" without quotes.')
    elif (action.action_type in ['photo', 'video'] and
            (not form.do_unique_id.data or form.do_unique_id.data == '')):
        error.append("Camera must be set")
    elif action.action_type == 'webhook':
        if not form.do_action_string.data or form.do_action_string.data == '':
            error.append("URL must be set")
    return error


def check_actions(action, error):
    """Check if the Actions form inputs are valid"""
    if action.action_type == 'command':
        if not action.do_action_string or action.do_action_string == '':
            error.append("Command must be set")
    elif action.action_type == 'output':
        if not action.do_unique_id or action.do_unique_id == '':
            error.append("Output must be set")
        if not action.do_output_state or action.do_output_state == '':
            error.append("State must be set")
    elif action.action_type in ['activate_pid',
                                'deactivate_pid']:
        if not action.do_unique_id or action.do_unique_id == '':
            error.append("PID must be set")
    elif action.action_type == 'email':
        if not action.do_action_string or action.do_action_string == '':
            error.append("Email must be set")
    elif action.action_type in ['photo_email', 'video_email']:
        if not action.do_action_string or action.do_action_string == '':
            error.append("Email must be set")
        if not action.do_unique_id or action.do_unique_id == '':
            error.append("Camera must be set")
        if (action.action_type == 'video_email' and
                Camera.query.filter(
                    and_(Camera.unique_id == action.do_unique_id,
                         Camera.library != 'picamera')).count()):
            error.append('Only Pi Cameras can record video')
    elif action.action_type == 'flash_lcd_on' and not action.do_unique_id:
        error.append("LCD must be set")
    elif action.action_type == 'lcd_backlight_color':
        if not action.do_unique_id:
            error.append("LCD must be set")
        try:
            tuple_colors = action.do_action_string.split(",")
            if len(tuple_colors) != 3:
                error.append('LCD backlight color must be in the R,G,B format "255,255,255"')

            if not is_int(tuple_colors[0]):
                error.append('Red color does not represent an integer.')
            elif int(tuple_colors[0]) < 0 or int(tuple_colors[0]) > 255:
                error.append('Red color must be >= 0 and <= 255')

            if not is_int(tuple_colors[1]):
                error.append('Blue color does not represent an integer.')
            elif int(tuple_colors[1]) < 0 or int(tuple_colors[1]) > 255:
                error.append('Blue color must be >= 0 and <= 255')

            if not is_int(tuple_colors[2]):
                error.append('Green color does not represent an integer.')
            elif int(tuple_colors[2]) < 0 or int(tuple_colors[2]) > 255:
                error.append('Green color must be >= 0 and <= 255')
        except:
            error.append('Error parsing LCD backlight color. Must be in the R,G,B format '
                         '"255,255,255" without quotes.')
    elif (action.action_type in ['photo', 'video'] and
            (not action.do_unique_id or action.do_unique_id == '')):
        error.append("Camera must be set")
    elif action.action_type == 'webhook':
        if not action.do_action_string or action.do_action_string == '':
            error.append("URL must be set")
    return error
