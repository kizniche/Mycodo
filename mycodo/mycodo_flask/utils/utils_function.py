# -*- coding: utf-8 -*-
import logging

import sqlalchemy
from flask import url_for
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.config import FUNCTION_INFO
from mycodo.config import PID_INFO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Function
from mycodo.databases.models import PID
from mycodo.databases.models import Trigger
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.mycodo_flask.utils.utils_misc import save_conditional_code
from mycodo.utils.controllers import parse_controller_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv
from mycodo.utils.system_pi import str_is_float

logger = logging.getLogger(__name__)


#
# Function manipulation
#

def function_add(form_add_func):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['function']['title'])
    error = []

    function_name = form_add_func.function_type.data

    dict_controllers = parse_controller_information()

    dep_unmet, _ = return_dependencies(function_name)
    if dep_unmet:
        list_unmet_deps = []
        for each_dep in dep_unmet:
            list_unmet_deps.append(each_dep[0])
        error.append(
            "The {dev} device you're trying to add has unmet dependencies: "
            "{dep}".format(dev=function_name,
                           dep=', '.join(list_unmet_deps)))

    new_func = None

    try:
        if function_name.startswith('conditional_'):
            new_func = Conditional()
            new_func.conditional_statement = '''
# Example code for learning how to use a Conditional. See the manual for more information.

self.logger.info("This INFO log entry will appear in the Daemon Log")
self.logger.error("This ERROR log entry will appear in the Daemon Log")

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
            new_func.save()
            save_conditional_code(
                error,
                new_func.conditional_statement,
                new_func.unique_id,
                test=False)
        elif function_name.startswith('pid_'):
            new_func = PID().save()

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
                new_measurement.save()

        elif function_name.startswith('trigger_'):
            new_func = Trigger()
            new_func.name = '{}'.format(FUNCTION_INFO[function_name]['name'])
            new_func.trigger_type = function_name
            new_func.save()
        elif function_name.startswith('function_'):
            new_func = Function()
            if function_name == 'function_spacer':
                new_func.name = 'Spacer'
            new_func.function_type = function_name
            new_func.save()

        elif function_name in dict_controllers:
            new_func = CustomController()
            new_func.device = function_name

            if 'controller_name' in dict_controllers[function_name]:
                new_func.name = dict_controllers[function_name]['controller_name']
            else:
                new_func.name = 'Controller Name'

            list_options = []
            if 'custom_options' in dict_controllers[function_name]:
                for each_option in dict_controllers[function_name]['custom_options']:
                    if each_option['default_value'] is False:
                        default_value = ''
                    else:
                        default_value = each_option['default_value']
                    option = '{id},{value}'.format(
                        id=each_option['id'],
                        value=default_value)
                    list_options.append(option)
            new_func.custom_options = ';'.join(list_options)
            new_func.save()

        elif function_name == '':
            error.append("Must select a function type")
        else:
            error.append("Unknown function type: '{}'".format(
                function_name))

        if not error:
            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().function)
            DisplayOrder.query.first().function = add_display_order(
                display_order, new_func.unique_id)
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))

    if dep_unmet:
        return 1


def function_mod(form):
    """Modify a Function"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['function']['title'])

    try:
        func_mod = Function.query.filter(
            Function.unique_id == form.function_id.data).first()

        func_mod.name = form.name.data

        if not error:
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def function_del(function_id):
    """Delete a Function"""
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['function']['title'])
    error = []

    try:
        # Delete Actions
        actions = Actions.query.filter(
            Actions.function_id == function_id).all()
        for each_action in actions:
            delete_entry_with_id(Actions,
                                 each_action.unique_id)

        delete_entry_with_id(Function, function_id)

        display_order = csv_to_list_of_str(DisplayOrder.query.first().function)
        display_order.remove(function_id)
        DisplayOrder.query.first().function = list_to_csv(display_order)
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def action_add(form):
    """Add a function Action"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                  TRANSLATIONS['actions']['title']))

    dep_unmet, _ = return_dependencies(form.action_type.data)
    if dep_unmet:
        list_unmet_deps = []
        for each_dep in dep_unmet:
            list_unmet_deps.append(each_dep[0])
        error.append(
            "The {dev} device you're trying to add has unmet dependencies: "
            "{dep}".format(dev=form.function_type.data,
                           dep=', '.join(list_unmet_deps)))

    if form.function_type.data == 'conditional':
        func = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'trigger':
        func = Trigger.query.filter(
            Trigger.unique_id == form.function_id.data).first()
    elif form.function_type.data == 'function_actions':
        func = Function.query.filter(
            Function.unique_id == form.function_id.data).first()
    else:
        func = None
        error.append("Invalid Function type: {}".format(form.function_type.data))

    if form.function_type.data != 'function_actions' and func and func.is_activated:
        error.append("Deactivate before adding an Action")

    if form.action_type.data == '':
        error.append("Must select an action")

    try:
        new_action = Actions()
        new_action.function_id = form.function_id.data
        new_action.function_type = form.function_type.data
        new_action.action_type = form.action_type.data

        if not error:
            new_action.save()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))

    if dep_unmet:
        return 1


def action_mod(form):
    """Modify a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'], TRANSLATIONS['actions']['title']))

    error = check_form_actions(form, error)

    try:
        mod_action = Actions.query.filter(
            Actions.unique_id == form.function_action_id.data).first()

        if mod_action.action_type == 'pause_actions':
            mod_action.pause_duration = form.pause_duration.data

        elif mod_action.action_type == 'output':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_state = form.do_output_state.data
            mod_action.do_output_duration = form.do_output_duration.data

        elif mod_action.action_type == 'output_pwm':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_output_pwm = form.do_output_pwm.data

        elif mod_action.action_type in ['activate_controller',
                                        'deactivate_controller']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type in ['activate_pid',
                                        'deactivate_pid',
                                        'resume_pid',
                                        'pause_pid']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type in ['activate_timer',
                                        'deactivate_timer']:
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type in ['setpoint_pid',
                                        'setpoint_pid_raise',
                                        'setpoint_pid_lower']:
            if not str_is_float(form.do_action_string.data):
                error.append("Setpoint value must be an integer or float value")
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type == 'method_pid':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_action_string = form.do_action_string.data

        elif mod_action.action_type == 'infrared_send':
            mod_action.remote = form.remote.data
            mod_action.code = form.code.data
            mod_action.send_times = form.send_times.data

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

        elif mod_action.action_type == 'photo':
            mod_action.do_unique_id = form.do_unique_id.data

        elif mod_action.action_type == 'video':
            mod_action.do_unique_id = form.do_unique_id.data
            mod_action.do_camera_duration = form.do_camera_duration.data

        elif mod_action.action_type in ['command',
                                        'create_note']:
            mod_action.do_action_string = form.do_action_string.data

        if not error:
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def action_del(form):
    """Delete a Conditional Action"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'], TRANSLATIONS['actions']['title']))

    conditional = Conditional.query.filter(
        Conditional.unique_id == form.function_id.data).first()

    trigger = Trigger.query.filter(
        Trigger.unique_id == form.function_id.data).first()

    if ((conditional and conditional.is_activated) or
            (trigger and trigger.is_activated)):
        error.append("Deactivate the Conditional before deleting an Action")

    try:
        if not error:
            function_action_id = Actions.query.filter(
                Actions.unique_id == form.function_action_id.data).first().unique_id
            delete_entry_with_id(Actions, function_action_id)

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def action_execute_all(form):
    """Execute All Conditional Actions"""
    error = []

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
        error.append("Unknown Function type: '{}'".format(
            form.function_type.data))

    action = '{action} {controller}'.format(
        action=gettext("Execute All"),
        controller='{} {}'.format(function_type, TRANSLATIONS['actions']['title']))

    if form.function_type.data != 'function_actions' and func and not func.is_activated:
        error.append("Activate the Conditional before testing all Actions")

    try:
        if not error:
            control = DaemonControl()
            control.trigger_all_actions(
                form.function_id.data,
                message="Test triggering all actions of function {}".format(form.function_id.data))
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def function_reorder(function_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['reorder']['title'],
        controller=TRANSLATIONS['function']['title'])
    error = []
    try:
        status, reord_list = reorder(
            display_order, function_id, direction)
        if status == 'success':
            DisplayOrder.query.first().function = ','.join(map(str, reord_list))
            db.session.commit()
        else:
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_function'))


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
    elif action.action_type in ['activate_pid',
                                'deactivate_pid',
                                'resume_pid',
                                'pause_pid']:
        if not form.do_unique_id.data or form.do_unique_id.data == '':
            error.append("ID must be set")
    elif action.action_type == 'infrared_send':
        if not form.remote.data:
            error.append("Remote must be set")
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
    elif (action.action_type in ['photo', 'video'] and
            (not form.do_unique_id.data or form.do_unique_id.data == '')):
        error.append("Camera must be set")
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
    elif action.action_type == 'infrared_send':
        if not action.remote or not action.code:
            error.append("Remote and Code must be set")
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
    elif (action.action_type in ['photo', 'video'] and
            (not action.do_unique_id or action.do_unique_id == '')):
        error.append("Camera must be set")
    return error
