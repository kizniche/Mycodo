# -*- coding: utf-8 -*-
import json
import logging
import os

import sqlalchemy
from flask_babel import gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import FunctionChannel
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils import utils_measurement
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import custom_channel_options_return_json
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_json
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.utils.functions import parse_function_information
from mycodo.utils.system_pi import parse_custom_option_values

logger = logging.getLogger(__name__)


def controller_mod(form_mod, request_form):
    """Modify a Custom Function."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": [],
        "name": None
    }
    page_refresh = False

    dict_controllers = parse_function_information()

    try:
        channels = FunctionChannel.query.filter(
            FunctionChannel.function_id == form_mod.function_id.data).all()
        mod_controller = CustomController.query.filter(
            CustomController.unique_id == form_mod.function_id.data).first()

        if mod_controller.is_activated:
            messages["error"].append(gettext(
                "Deactivate controller before modifying its settings"))

        mod_controller.name = form_mod.name.data
        messages["name"] = form_mod.name.data
        mod_controller.log_level_debug = form_mod.log_level_debug.data

        # Enable/disable Channels
        measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == form_mod.function_id.data).all()
        if form_mod.measurements_enabled.data:
            for each_measurement in measurements:
                if each_measurement.unique_id in form_mod.measurements_enabled.data:
                    each_measurement.is_enabled = True
                else:
                    each_measurement.is_enabled = False

        # Save Measurement settings
        messages, page_refresh = utils_measurement.measurement_mod_form(
            messages, page_refresh, request_form)

        # Add or delete channels for variable measurement Inputs
        if ('measurements_variable_amount' in dict_controllers[mod_controller.device] and
                dict_controllers[mod_controller.device]['measurements_variable_amount']):

            measurements = DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == form_mod.function_id.data)

            if measurements.count() != form_mod.num_channels.data:
                # Delete measurements/channels
                if form_mod.num_channels.data < measurements.count():
                    for index, each_channel in enumerate(measurements.all()):
                        if index + 1 >= measurements.count():
                            delete_entry_with_id(DeviceMeasurements,
                                                 each_channel.unique_id)

                    if ('channel_quantity_same_as_measurements' in dict_controllers[mod_controller.device] and
                            dict_controllers[mod_controller.device]["channel_quantity_same_as_measurements"]):
                        if form_mod.num_channels.data < channels.count():
                            for index, each_channel in enumerate(channels.all()):
                                if index + 1 >= channels.count():
                                    delete_entry_with_id(FunctionChannel,
                                                         each_channel.unique_id)

                # Add measurements/channels
                elif form_mod.num_channels.data > measurements.count():
                    start_number = measurements.count()
                    for index in range(start_number, form_mod.num_channels.data):
                        new_measurement = DeviceMeasurements()
                        new_measurement.name = ""
                        new_measurement.device_id = mod_controller.unique_id
                        new_measurement.measurement = ""
                        new_measurement.unit = ""
                        new_measurement.channel = index
                        new_measurement.save()

                        if ('channel_quantity_same_as_measurements' in dict_controllers[mod_controller.device] and
                                dict_controllers[mod_controller.device]["channel_quantity_same_as_measurements"]):
                            new_channel = FunctionChannel()
                            new_channel.name = ""
                            new_channel.function_id = mod_controller.unique_id
                            new_channel.channel = index

                            messages["error"], custom_options = custom_channel_options_return_json(
                                messages["error"], dict_controllers, request_form,
                                mod_controller.unique_id, index,
                                device=mod_controller.device, use_defaults=True)
                            new_channel.custom_options = custom_options

                            new_channel.save()

        # Parse pre-save custom options for function device and its channels
        try:
            custom_options_dict_presave = json.loads(mod_controller.custom_options)
        except:
            logger.error("Malformed JSON")
            custom_options_dict_presave = {}

        custom_options_channels_dict_presave = {}
        for each_channel in channels:
            if each_channel.custom_options and each_channel.custom_options != "{}":
                custom_options_channels_dict_presave[each_channel.channel] = json.loads(
                    each_channel.custom_options)
            else:
                custom_options_channels_dict_presave[each_channel.channel] = {}

        # Parse post-save custom options for function device and its channels
        messages["error"], custom_options_json_postsave = custom_options_return_json(
            messages["error"], dict_controllers,
            request_form=request_form,
            mod_dev=mod_controller,
            device=mod_controller.device,
            use_defaults=True,
            custom_options=custom_options_dict_presave)
        custom_options_dict_postsave = json.loads(custom_options_json_postsave)

        custom_options_channels_dict_postsave = {}
        for each_channel in channels:
            messages["error"], custom_options_channels_json_postsave_tmp = custom_channel_options_return_json(
                messages["error"], dict_controllers, request_form,
                form_mod.function_id.data, each_channel.channel,
                device=mod_controller.device, use_defaults=False)
            custom_options_channels_dict_postsave[each_channel.channel] = json.loads(
                custom_options_channels_json_postsave_tmp)

        if 'execute_at_modification' in dict_controllers[mod_controller.device]:
            # pass custom options to module prior to saving to database
            (messages,
             mod_controller,
             custom_options_dict,
             custom_options_channels_dict,
             refresh_page) = dict_controllers[mod_controller.device]['execute_at_modification'](
                messages,
                mod_controller,
                request_form,
                custom_options_dict_presave,
                custom_options_channels_dict_presave,
                custom_options_dict_postsave,
                custom_options_channels_dict_postsave)
            custom_options = json.dumps(custom_options_dict)  # Convert from dict to JSON string
            custom_channel_options = custom_options_channels_dict
            if refresh_page:
                page_refresh = True
        else:
            # Don't pass custom options to module
            custom_options = json.dumps(custom_options_dict_postsave)
            custom_channel_options = custom_options_channels_dict_postsave

        # Finally, save custom options for both function and channels
        mod_controller.custom_options = custom_options
        for each_channel in channels:
            if 'name' in custom_channel_options[each_channel.channel]:
                each_channel.name = custom_channel_options[each_channel.channel]['name']
            each_channel.custom_options = json.dumps(custom_channel_options[each_channel.channel])

        if not messages["error"]:
            db.session.commit()
            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['modify']['title'],
                controller=TRANSLATIONS['controller']['title']))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages, page_refresh


def controller_del(cond_id):
    """Delete a custom Function."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    cond = CustomController.query.filter(
        CustomController.unique_id == cond_id).first()

    # Deactivate controller if active
    if cond.is_activated:
        controller_deactivate(cond_id)

    try:
        if not messages["error"]:
            device_measurements = DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == cond_id).all()
            for each_measurement in device_measurements:
                delete_entry_with_id(
                    DeviceMeasurements,
                    each_measurement.unique_id,
                    flash_message=False)

            delete_entry_with_id(
                CustomController, cond_id, flash_message=False)

            channels = FunctionChannel.query.filter(
                FunctionChannel.function_id == cond_id).all()
            for each_channel in channels:
                delete_entry_with_id(
                    FunctionChannel,
                    each_channel.unique_id,
                    flash_message=False)

            messages["success"].append('{action} {controller}'.format(
                action=TRANSLATIONS['delete']['title'],
                controller=TRANSLATIONS['controller']['title']))

            try:
                file_path = os.path.join(
                    PATH_PYTHON_CODE_USER, 'conditional_{}.py'.format(
                        cond.unique_id))
                os.remove(file_path)
            except:
                pass

            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def controller_activate(controller_id):
    """Activate a Conditional."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": [],
        "period_status": None
    }

    function = CustomController.query.filter(
        CustomController.unique_id == controller_id).first()

    if not function:
        messages["error"].append("Function not found")
    else:
        dict_controllers = parse_function_information()
        custom_options_values_controllers = parse_custom_option_values(
            CustomController.query.all(), dict_controller=dict_controllers)

        if (controller_id in custom_options_values_controllers and
                'period_status' in custom_options_values_controllers[controller_id]):
            messages["period_status"] = custom_options_values_controllers[controller_id]['period_status']

        if ('enable_channel_unit_select' in dict_controllers[function.device] and
                dict_controllers[function.device]['enable_channel_unit_select']):
            device_measurements = DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == controller_id).all()
            for each_measure in device_measurements:
                if (None in [each_measure.measurement, each_measure.unit] or
                        "" in [each_measure.measurement, each_measure.unit]):
                    messages["error"].append(
                        "Measurement CH{} ({}) measurement/unit not set. All Measurements need to have "
                        "the measurement and unit set before the Function can be activated.".format(
                            each_measure.channel, each_measure.name))

    messages = controller_activate_deactivate(
        messages, 'activate', 'Function', controller_id, flash_message=False)

    if not messages["error"]:
        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['activate']['title'],
            controller=TRANSLATIONS['controller']['title']))

    return messages


def controller_deactivate(controller_id):
    """Deactivate a Conditional."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    messages = controller_activate_deactivate(
        messages, 'deactivate', 'Function', controller_id, flash_message=False)

    if not messages["error"]:
        messages["success"].append('{action} {controller}'.format(
            action=TRANSLATIONS['deactivate']['title'],
            controller=TRANSLATIONS['controller']['title']))

    return messages
