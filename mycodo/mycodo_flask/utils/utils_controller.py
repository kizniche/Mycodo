# -*- coding: utf-8 -*-
import json
import logging

import os
import sqlalchemy
from flask import url_for
from flask_babel import gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import FunctionChannel
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import custom_channel_options_return_json
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_json
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.utils.functions import parse_function_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


def controller_mod(form_mod, request_form):
    """Modify a Custom Function"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['controller']['title'])

    dict_controllers = parse_function_information()

    try:
        mod_controller = CustomController.query.filter(
            CustomController.unique_id == form_mod.function_id.data).first()

        if mod_controller.is_activated:
            error.append(gettext(
                "Deactivate controller before modifying its settings"))

        mod_controller.name = form_mod.name.data
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

        channels = FunctionChannel.query.filter(
            FunctionChannel.function_id == form_mod.function_id.data)

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
                            new_measurement.channel = index

                            error, custom_options = custom_channel_options_return_json(
                                error, dict_controllers, request_form,
                                mod_controller.unique_id, index,
                                device=mod_controller.device, use_defaults=True)
                            new_channel.custom_options = custom_options

                            new_channel.save()

        # Generate string to save from custom options
        error, custom_options = custom_options_return_json(
            error, dict_controllers,
            request_form=request_form,
            device=mod_controller.device,
            use_defaults=True)
        mod_controller.custom_options = custom_options

        if not error:
            db.session.commit()

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def controller_del(cond_id):
    """Delete a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['controller']['title'])

    cond = CustomController.query.filter(
        CustomController.unique_id == cond_id).first()

    # Deactivate controller if active
    if cond.is_activated:
        controller_deactivate(cond_id)

    try:
        if not error:
            device_measurements = DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == cond_id).all()
            for each_measurement in device_measurements:
                delete_entry_with_id(DeviceMeasurements, each_measurement.unique_id)

            delete_entry_with_id(CustomController, cond_id)

            channels = FunctionChannel.query.filter(
                FunctionChannel.function_id == cond_id).all()
            for each_channel in channels:
                delete_entry_with_id(FunctionChannel, each_channel.unique_id)

            display_order = csv_to_list_of_str(DisplayOrder.query.first().function)
            display_order.remove(cond_id)
            DisplayOrder.query.first().function = list_to_csv(display_order)

            try:
                file_path = os.path.join(
                    PATH_PYTHON_CODE_USER, 'conditional_{}.py'.format(
                        cond.unique_id))
                os.remove(file_path)
            except:
                pass

            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def controller_activate(controller_id):
    """Activate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['controller']['title'])

    function = CustomController.query.filter(
        CustomController.unique_id == controller_id).first()

    dict_controllers = parse_function_information()

    if ('enable_channel_unit_select' in dict_controllers[function.device] and
            dict_controllers[function.device]['enable_channel_unit_select']):
        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == controller_id).all()
        for each_measure in device_measurements:
            if (None in [each_measure.measurement, each_measure.unit] or
                    "" in [each_measure.measurement, each_measure.unit]):
                error.append(
                    "Measurement CH{} ({}) measurement/unit not set. All Measurements need to have "
                    "the measurement and unit set before the Function can be activated.".format(
                        each_measure.channel, each_measure.name))

    if not error:
        controller_activate_deactivate('activate', 'Function', controller_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def controller_deactivate(controller_id):
    """Deactivate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['deactivate']['title'],
        controller=TRANSLATIONS['controller']['title'])

    if not error:
        controller_activate_deactivate('deactivate', 'Function', controller_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))
