# coding=utf-8
import logging
import os
import time
import traceback

from mycodo.config import MYCODO_DB_PATH
from mycodo.config import PATH_ACTIONS
from mycodo.config import PATH_ACTIONS_CUSTOM
from mycodo.databases.models import Actions
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Function
from mycodo.databases.models import Input
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.databases.models import SMTP
from mycodo.databases.models import Trigger
from mycodo.databases.utils import session_scope
from mycodo.devices.camera import camera_record
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import get_last_measurement
from mycodo.utils.influx import get_past_measurements
from mycodo.utils.modules import load_module_from_file
from mycodo.utils.system_pi import return_measurement_info

logger = logging.getLogger("mycodo.actions")


def parse_action_information(exclude_custom=False):
    """Parses the variables assigned in each Function Action and return a dictionary of IDs and values."""
    def dict_has_value(dict_inp, action, key, force_type=None):
        if (key in action.ACTION_INFORMATION and
                (action.ACTION_INFORMATION[key] or
                 action.ACTION_INFORMATION[key] == 0)):
            if force_type == 'list':
                if isinstance(action.ACTION_INFORMATION[key], list):
                    dict_inp[action.ACTION_INFORMATION['name_unique']][key] = \
                        action.ACTION_INFORMATION[key]
                else:
                    dict_inp[action.ACTION_INFORMATION['name_unique']][key] = \
                        [action.ACTION_INFORMATION[key]]
            else:
                dict_inp[action.ACTION_INFORMATION['name_unique']][key] = \
                    action.ACTION_INFORMATION[key]
        return dict_inp

    excluded_files = [
        '__init__.py', '__pycache__', 'base_action.py',
        'custom_actions', 'examples', 'scripts', 'tmp_actions'
    ]

    function_paths = [PATH_ACTIONS]

    if not exclude_custom:
        function_paths.append(PATH_ACTIONS_CUSTOM)

    dict_actions = {}

    for each_path in function_paths:

        real_path = os.path.realpath(each_path)

        for each_file in os.listdir(real_path):
            if each_file in excluded_files:
                continue

            full_path = "{}/{}".format(real_path, each_file)
            function_action, status = load_module_from_file(full_path, 'actions')

            if not function_action or not hasattr(function_action, 'ACTION_INFORMATION'):
                continue

            # Populate dictionary of function information
            if function_action.ACTION_INFORMATION['name_unique'] in dict_actions:
                logger.error(
                    "Error: Cannot add controller modules because it does not have a unique name: {name}".format(
                        name=function_action.ACTION_INFORMATION['name_unique']))
            else:
                dict_actions[function_action.ACTION_INFORMATION['name_unique']] = {}

            dict_actions[function_action.ACTION_INFORMATION['name_unique']]['file_path'] = full_path

            dict_actions = dict_has_value(dict_actions, function_action, 'name')
            dict_actions = dict_has_value(dict_actions, function_action, 'manufacturer')
            dict_actions = dict_has_value(dict_actions, function_action, 'application')
            dict_actions = dict_has_value(dict_actions, function_action, 'url_datasheet', force_type='list')
            dict_actions = dict_has_value(dict_actions, function_action, 'url_manufacturer', force_type='list')
            dict_actions = dict_has_value(dict_actions, function_action, 'url_product_purchase', force_type='list')
            dict_actions = dict_has_value(dict_actions, function_action, 'url_additional', force_type='list')
            dict_actions = dict_has_value(dict_actions, function_action, 'application', force_type='list')
            dict_actions = dict_has_value(dict_actions, function_action, 'message')
            dict_actions = dict_has_value(dict_actions, function_action, 'usage')
            dict_actions = dict_has_value(dict_actions, function_action, 'dependencies_module')
            dict_actions = dict_has_value(dict_actions, function_action, 'dependencies_message')
            dict_actions = dict_has_value(dict_actions, function_action, 'custom_options')

    return dict_actions


def check_allowed_to_email():
    smtp_table = db_retrieve_table_daemon(SMTP, entry='first')
    smtp_max_count = smtp_table.hourly_max
    smtp_wait_timer = smtp_table.smtp_wait_timer
    email_count = smtp_table.email_count

    if (email_count >= smtp_max_count and
            time.time() < smtp_wait_timer):
        allowed_to_send_notice = False
    else:
        if time.time() > smtp_wait_timer:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_smtp = new_session.query(SMTP).first()
                mod_smtp.email_count = 0
                mod_smtp.smtp_wait_timer = time.time() + 3600
                new_session.commit()
        allowed_to_send_notice = True

    with session_scope(MYCODO_DB_PATH) as new_session:
        mod_smtp = new_session.query(SMTP).first()
        mod_smtp.email_count += 1
        new_session.commit()

    return smtp_wait_timer, allowed_to_send_notice


def get_condition_value(condition_id):
    """
    Returns condition measurements for Conditional controllers
    :param condition_id: Conditional condition ID
    :return: measurement: multiple types
    """
    if not condition_id:
        logger.error("Must provide a Condition ID")
        return

    sql_condition = db_retrieve_table_daemon(ConditionalConditions).filter(
        ConditionalConditions.unique_id == condition_id).first()

    if not sql_condition:
        logger.error("Condition ID not found")
        return

    # Check Measurement Conditions
    if sql_condition.condition_type == 'measurement_and_ts':
        device_id = sql_condition.measurement.split(',')[0]
        measurement_id = sql_condition.measurement.split(',')[1]

        device_measurement = db_retrieve_table_daemon(
            DeviceMeasurements, unique_id=measurement_id)
        if device_measurement:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        if None in [channel, unit]:
            logger.error(
                "Could not determine channel or unit from measurement ID: "
                "{}".format(measurement_id))
            return {"time": None, "value": None}

        max_age = sql_condition.max_age

        influx_return = get_last_measurement(
            device_id, measurement_id, max_age=max_age)
        if influx_return is not None:
            return_ts = influx_return[0]
            return_measurement = influx_return[1]
        else:
            return_ts = None
            return_measurement = None

        return {"time": return_ts, "value": return_measurement}

    elif sql_condition.condition_type in ['measurement',
                                        'measurement_past_average',
                                        'measurement_past_sum']:
        device_id = sql_condition.measurement.split(',')[0]
        measurement_id = sql_condition.measurement.split(',')[1]

        device_measurement = db_retrieve_table_daemon(
            DeviceMeasurements, unique_id=measurement_id)
        if device_measurement:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        if None in [channel, unit]:
            logger.error(
                "Could not determine channel or unit from measurement ID: "
                "{}".format(measurement_id))
            return

        max_age = sql_condition.max_age

        if sql_condition.condition_type == 'measurement':
            influx_return = get_last_measurement(
                device_id, measurement_id, max_age=max_age)
            if influx_return is not None:
                return_measurement = influx_return[1]
            else:
                return_measurement = None
        elif sql_condition.condition_type == 'measurement_past_average':
            measurement_list = []
            past_measurements = get_past_measurements(
                device_id, measurement_id, max_age=max_age)
            for each_set in past_measurements:
                measurement_list.append(float(each_set[1]))
            return_measurement = sum(measurement_list) / len(measurement_list)
        elif sql_condition.condition_type == 'measurement_past_sum':
            measurement_list = []
            past_measurements = get_past_measurements(
                device_id, measurement_id, max_age=max_age)
            for each_set in past_measurements:
                measurement_list.append(float(each_set[1]))
            return_measurement = sum(measurement_list)
        else:
            return

        return return_measurement

    # Return GPIO state
    elif sql_condition.condition_type == 'gpio_state':
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(int(sql_condition.gpio_pin), GPIO.IN)
            gpio_state = GPIO.input(int(sql_condition.gpio_pin))
        except Exception as e:
            gpio_state = None
            logger.error("Exception reading the GPIO pin: {}".format(e))
        return gpio_state

    # Return output state
    elif sql_condition.condition_type == 'output_state':
        output_id = sql_condition.output_id.split(",")[0]
        channel_id = sql_condition.output_id.split(",")[1]
        channel = db_retrieve_table_daemon(OutputChannel).filter(
            OutputChannel.unique_id == channel_id).first()
        control = DaemonControl()
        return control.output_state(output_id, output_channel=channel.channel)

    # Return the duration the output is currently on for
    elif sql_condition.condition_type == 'output_duration_on':
        output_id = sql_condition.output_id.split(",")[0]
        channel_id = sql_condition.output_id.split(",")[1]
        channel = db_retrieve_table_daemon(OutputChannel).filter(
            OutputChannel.unique_id == channel_id).first()
        control = DaemonControl()
        return control.output_sec_currently_on(output_id, output_channel=channel.channel)

    # Return controller active state
    elif sql_condition.condition_type == 'controller_status':
        control = DaemonControl()
        return control.controller_is_active(sql_condition.controller_id)


def get_condition_value_dict(condition_id):
    """
    Returns dict of multiple condition measurements for Conditional controllers
    :param condition_id: Conditional condition ID
    :return: measurement: dict of float measurements
    """
    if not condition_id:
        logger.error("Must provide a Condition ID")
        return

    sql_condition = db_retrieve_table_daemon(ConditionalConditions).filter(
        ConditionalConditions.unique_id == condition_id).first()

    if not sql_condition:
        logger.error("Condition ID not found")
        return

    # Check Measurement Conditions
    if sql_condition.condition_type == 'measurement_dict':
        device_id = sql_condition.measurement.split(',')[0]
        measurement_id = sql_condition.measurement.split(',')[1]
        max_age = sql_condition.max_age

        device_measurement = db_retrieve_table_daemon(
            DeviceMeasurements, unique_id=measurement_id)
        if device_measurement:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        if None in [channel, unit]:
            logger.error(
                "Could not determine channel or unit from measurement ID: "
                "{}".format(measurement_id))
            return

        past_measurements_dict = get_past_measurements(
            device_id, measurement_id, max_age=max_age)

        return past_measurements_dict


def action_video(cond_action, message):
    this_camera = db_retrieve_table_daemon(
        Camera, unique_id=cond_action.do_unique_id, entry='first')
    message += "  Capturing video with camera {unique_id} ({id}, {name}).".format(
        unique_id=cond_action.do_unique_id,
        id=this_camera.id,
        name=this_camera.name)
    camera_stream = db_retrieve_table_daemon(
        Camera, unique_id=cond_action.do_unique_id)
    path, filename = camera_record(
        'video', camera_stream.unique_id,
        duration_sec=cond_action.do_camera_duration)
    if path and filename:
        attachment_file = os.path.join(path, filename)
        return message, attachment_file
    else:
        message += " A video could not be acquired."
        return message, None


def trigger_action(
        dict_actions,
        action_id,
        value={},
        debug=False):
    """
    Trigger individual action

    :param dict_actions: dict of action information
    :param action_id: unique_id of action
    :param value: an object to be sent to the action. Typically, a dictionary with 'message' as a key.
    :param debug: determine if logging level should be DEBUG

    :return: dict with 'message' as a key
    """
    action = db_retrieve_table_daemon(Actions, unique_id=action_id)
    if not value or 'message' not in value:
        message = ''
    else:
        message = value['message']

    if not action:
        message += 'Error: Action with ID {} not found!'.format(action_id)
        return {'message': message}

    logger_actions = logging.getLogger("mycodo.trigger_action_{id}".format(
        id=action.unique_id.split('-')[0]))

    if debug:
        logger_actions.setLevel(logging.DEBUG)
    else:
        logger_actions.setLevel(logging.INFO)

    # Set up function action to run from standalone action module file
    run_function_action = None
    if action.action_type in dict_actions:
        message += "\n[Action {id}, {name}]:".format(
            id=action.unique_id.split('-')[0],
            name=dict_actions[action.action_type]['name'])
        try:
            action_loaded, status = load_module_from_file(
                dict_actions[action.action_type]['file_path'], 'action')
            if action_loaded:
                run_function_action = action_loaded.ActionModule(action)
                value = run_function_action.run_action(value)

                if value and "message" in value:
                    message = value["message"]
        except:
            message += " Exception executing action: {}".format(traceback.print_exc())

    logger_actions.debug("Message: {}".format(message))

    return value


def run_input_actions(unique_id, message, measurements_dict, debug=False):
    control = DaemonControl()
    actions = db_retrieve_table_daemon(Actions).filter(
        Actions.function_id == unique_id).all()

    for each_action in actions:
        try:
            return_dict = control.trigger_action(
                each_action.unique_id,
                value={"message": message, "measurements_dict": measurements_dict},
                debug=debug)

            # if message is returned, set message
            if return_dict and 'message' in return_dict and return_dict['message']:
                message = return_dict['message']

            # if measurements_dict is returned, use that to store measurements
            if return_dict and 'measurements_dict' in return_dict and return_dict['measurements_dict']:
                measurements_dict = return_dict['measurements_dict']
        except:
            logger.exception(f"Running Input Action {each_action.unique_id}")

    return message, measurements_dict


def trigger_controller_actions(dict_actions, controller_id, message='', debug=False):
    """
    Execute the Actions belonging to a particular controller

    :param dict_actions: dict of function action information
    :param controller_id: unique ID of function to execute all actions of
    :param message: The message generated from the conditional check
    :param debug: determine if logging level should be DEBUG
    :return:
    """
    logger_actions = logging.getLogger("mycodo.trigger_controller_actions_{id}".format(
        id=controller_id.split('-')[0]))

    if debug:
        logger_actions.setLevel(logging.DEBUG)
    else:
        logger_actions.setLevel(logging.INFO)

    actions = db_retrieve_table_daemon(Actions)
    actions = actions.filter(
        Actions.function_id == controller_id).all()
    
    dict_return = {'message': message}

    for each_action in actions:
        dict_return = trigger_action(
            dict_actions,
            each_action.unique_id,
            value=dict_return,
            debug=debug)

    if dict_return and 'message' in dict_return:
        message = dict_return['message']

    logger_actions.debug("Message: {}".format(message))

    return message


def which_controller(unique_id):
    """Determine which type of controller the unique_id is for."""
    controller_type = None
    controller_object = None
    controller_entry = None

    if db_retrieve_table_daemon(Conditional, unique_id=unique_id):
        controller_type = 'Conditional'
        controller_object = Conditional
        controller_entry = db_retrieve_table_daemon(
            Conditional, unique_id=unique_id)
    elif db_retrieve_table_daemon(CustomController, unique_id=unique_id):
        controller_type = 'Function'
        controller_object = CustomController
        controller_entry = db_retrieve_table_daemon(
            CustomController, unique_id=unique_id)
    elif db_retrieve_table_daemon(Function, unique_id=unique_id):
        controller_type = 'Function'
        controller_object = Function
        controller_entry = db_retrieve_table_daemon(
            Function, unique_id=unique_id)
    elif db_retrieve_table_daemon(Input, unique_id=unique_id):
        controller_type = 'Input'
        controller_object = Input
        controller_entry = db_retrieve_table_daemon(
            Input, unique_id=unique_id)
    elif db_retrieve_table_daemon(PID, unique_id=unique_id):
        controller_type = 'PID'
        controller_object = PID
        controller_entry = db_retrieve_table_daemon(
            PID, unique_id=unique_id)
    elif db_retrieve_table_daemon(Trigger, unique_id=unique_id):
        controller_type = 'Trigger'
        controller_object = Trigger
        controller_entry = db_retrieve_table_daemon(
            Trigger, unique_id=unique_id)

    return controller_type, controller_object, controller_entry
