# -*- coding: utf-8 -*-
import json
import logging

import os
import sqlalchemy
from flask import current_app
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases import set_uuid
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import custom_channel_options_return_json
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_json
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# Output manipulation
#

def output_add(form_add, request_form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['output']['title'])
    error = []

    dict_outputs = parse_output_information()

    if current_app.config['TESTING']:
        dep_unmet = False
    else:
        dep_unmet, _ = return_dependencies(form_add.output_type.data.split(',')[0])
        if dep_unmet:
            list_unmet_deps = []
            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[0])
            error.append("The {dev} device you're trying to add has unmet dependencies: {dep}".format(
                dev=form_add.output_type.data.split(',')[0], dep=', '.join(list_unmet_deps)))

    if not is_int(form_add.output_quantity.data, check_range=[1, 20]):
        error.append("{error}. {accepted_values}: 1-20".format(
            error=gettext("Invalid quantity"),
            accepted_values=gettext("Acceptable values")
        ))

    if form_add.output_type.data.count(',') == 1:
        output_type = form_add.output_type.data.split(',')[0]
        output_interface = form_add.output_type.data.split(',')[1]
    else:
        output_type = ''
        output_interface = ''
        error.append("Invalid output string (must be a comma-separated string)")

    if not error:
        for _ in range(0, form_add.output_quantity.data):
            try:
                new_output = Output()
                try:
                    from RPi import GPIO
                    if GPIO.RPI_INFO['P1_REVISION'] == 1:
                        new_output.i2c_bus = 0
                    else:
                        new_output.i2c_bus = 1
                except:
                    logger.error(
                        "RPi.GPIO and Raspberry Pi required for this action")

                new_output.name = "Name"
                new_output.output_type = output_type
                new_output.interface = output_interface

                #
                # Set default values for new input being added
                #

                # input add options
                if output_type in dict_outputs:
                    def dict_has_value(key):
                        if (key in dict_outputs[output_type] and
                                dict_outputs[output_type][key] is not None):
                            return True

                    #
                    # Interfacing options
                    #

                    if output_interface == 'I2C':
                        if dict_has_value('i2c_address_default'):
                            new_output.i2c_location = dict_outputs[output_type]['i2c_address_default']
                        elif dict_has_value('i2c_location'):
                            new_output.i2c_location = dict_outputs[output_type]['i2c_location'][0]  # First list entry

                    if output_interface == 'FTDI':
                        if dict_has_value('ftdi_location'):
                            new_output.ftdi_location = dict_outputs[output_type]['ftdi_location']

                    if output_interface == 'UART':
                        if dict_has_value('uart_location'):
                            new_output.uart_location = dict_outputs[output_type]['uart_location']

                    # UART options
                    if dict_has_value('uart_baud_rate'):
                        new_output.baud_rate = dict_outputs[output_type]['uart_baud_rate']
                    if dict_has_value('pin_cs'):
                        new_output.pin_cs = dict_outputs[output_type]['pin_cs']
                    if dict_has_value('pin_miso'):
                        new_output.pin_miso = dict_outputs[output_type]['pin_miso']
                    if dict_has_value('pin_mosi'):
                        new_output.pin_mosi = dict_outputs[output_type]['pin_mosi']
                    if dict_has_value('pin_clock'):
                        new_output.pin_clock = dict_outputs[output_type]['pin_clock']

                    # Bluetooth (BT) options
                    elif output_interface == 'BT':
                        if dict_has_value('bt_location'):
                            new_output.location = dict_outputs[output_type]['bt_location']
                        if dict_has_value('bt_adapter'):
                            new_output.bt_adapter = dict_outputs[output_type]['bt_adapter']

                    # GPIO options
                    elif output_interface == 'GPIO':
                        if dict_has_value('gpio_pin'):
                            new_output.pin = dict_outputs[output_type]['gpio_pin']

                    # Custom location location
                    elif dict_has_value('location'):
                        new_output.location = dict_outputs[output_type]['location']['options'][0][0]  # First entry in list

                # Generate string to save from custom options
                error, custom_options = custom_options_return_json(
                    error, dict_outputs, request_form, device=output_type, use_defaults=True)
                new_output.custom_options = custom_options

                #
                # Execute at Creation
                #

                new_output.unique_id = set_uuid()

                if 'execute_at_creation' in dict_outputs[output_type] and not current_app.config['TESTING']:
                    dict_outputs[output_type]['execute_at_creation'](
                        new_output, dict_outputs[output_type])

                if not error:
                    new_output.save()

                    display_order = csv_to_list_of_str(
                        DisplayOrder.query.first().output)
                    DisplayOrder.query.first().output = add_display_order(
                        display_order, new_output.unique_id)

                    db.session.commit()

                    #
                    # If measurements defined in the Output Module
                    #

                    if ('measurements_dict' in dict_outputs[output_type] and
                            dict_outputs[output_type]['measurements_dict'] != []):
                        for each_measurement in dict_outputs[output_type]['measurements_dict']:
                            measure_info = dict_outputs[output_type]['measurements_dict'][each_measurement]
                            new_measurement = DeviceMeasurements()
                            if 'name' in measure_info:
                                new_measurement.name = measure_info['name']
                            new_measurement.device_id = new_output.unique_id
                            new_measurement.measurement = measure_info['measurement']
                            new_measurement.unit = measure_info['unit']
                            new_measurement.channel = each_measurement
                            new_measurement.save()

                    for each_channel, channel_info in dict_outputs[output_type]['channels_dict'].items():
                        new_channel = OutputChannel()
                        new_channel.channel = each_channel
                        new_channel.output_id = new_output.unique_id

                        # Generate string to save from custom options
                        error, custom_options = custom_channel_options_return_json(
                            error, dict_outputs, request_form,
                            new_output.unique_id, each_channel,
                            device=output_type, use_defaults=True)
                        new_channel.custom_options = custom_options

                        new_channel.save()

                    # Refresh output settings
                    if not current_app.config['TESTING']:
                        manipulate_output('Add', new_output.unique_id)

                    flash(gettext("{dev} with ID %(id)s successfully added".format(
                        dev=dict_outputs[output_type]['output_name']), id=new_output.id),
                        "success")
            except sqlalchemy.exc.OperationalError as except_msg:
                error.append(except_msg)
            except sqlalchemy.exc.IntegrityError as except_msg:
                error.append(except_msg)
            except Exception:
                logger.exception(1)

    return dep_unmet


def output_mod(form_output, request_form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['output']['title'])
    error = []

    dict_outputs = parse_output_information()

    try:
        channels = OutputChannel.query.filter(
            OutputChannel.output_id == form_output.output_id.data).all()
        mod_output = Output.query.filter(
            Output.unique_id == form_output.output_id.data).first()

        if (form_output.uart_location.data and
                not os.path.exists(form_output.uart_location.data)):
            error.append(gettext(
                "Invalid device or improper permissions to read device"))

        mod_output.name = form_output.name.data

        if form_output.location.data:
            mod_output.location = form_output.location.data
        if form_output.i2c_location.data:
            mod_output.i2c_location = form_output.i2c_location.data
        if form_output.ftdi_location.data:
            mod_output.ftdi_location = form_output.ftdi_location.data
        if form_output.uart_location.data:
            mod_output.uart_location = form_output.uart_location.data
        if form_output.gpio_location.data:
            if not is_int(form_output.gpio_location.data):
                error.append("BCM GPIO Pin must be an integer")
            else:
                mod_output.pin = form_output.gpio_location.data

        if form_output.i2c_bus.data is not None:
            mod_output.i2c_bus = form_output.i2c_bus.data
        if form_output.baud_rate.data:
            mod_output.baud_rate = form_output.baud_rate.data

        mod_output.log_level_debug = form_output.log_level_debug.data

        # Parse pre-save custom options for output device and its channels
        try:
            custom_options_dict_presave = json.loads(mod_output.custom_options)
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

        # Parse post-save custom options for output device and its channels
        error, custom_options_json_postsave = custom_options_return_json(
            error, dict_outputs, request_form, device=mod_output.output_type)
        custom_options_dict_postsave = json.loads(custom_options_json_postsave)

        custom_options_channels_dict_postsave = {}
        for each_channel in channels:
            error, custom_options_channels_json_postsave_tmp = custom_channel_options_return_json(
                error, dict_outputs, request_form,
                form_output.output_id.data, each_channel.channel,
                device=mod_output.output_type, use_defaults=True)
            custom_options_channels_dict_postsave[each_channel.channel] = json.loads(
                custom_options_channels_json_postsave_tmp)

        if 'execute_at_modification' in dict_outputs[mod_output.output_type]:
            # pass custom options to module prior to saving to database
            (allow_saving,
             mod_output,
             custom_options_dict,
             custom_options_channels_dict) = dict_outputs[mod_output.output_type]['execute_at_modification'](
                mod_output,
                request_form,
                custom_options_dict_presave,
                custom_options_channels_dict_presave,
                custom_options_dict_postsave,
                custom_options_channels_dict_postsave)
            custom_options = json.dumps(custom_options_dict)  # Convert from dict to JSON string
            custom_channel_options = custom_options_channels_dict
            if not allow_saving:
                error.append("execute_at_modification() would not allow output options to be saved")
        else:
            # Don't pass custom options to module
            custom_options = json.dumps(custom_options_dict_postsave)
            custom_channel_options = custom_options_channels_dict_postsave

        # Finally, save custom options for both output and channels
        mod_output.custom_options = custom_options
        for each_channel in channels:
            if 'name' in custom_channel_options[each_channel.channel]:
                each_channel.name = custom_channel_options[each_channel.channel]['name']
            each_channel.custom_options = json.dumps(custom_channel_options[each_channel.channel])

        if not error:
            db.session.commit()
            manipulate_output('Modify', form_output.output_id.data)
    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_output'))


def output_del(form_output):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['output']['title'])
    error = []

    try:
        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == form_output.output_id.data).all()

        for each_measurement in device_measurements:
            delete_entry_with_id(
                DeviceMeasurements, each_measurement.unique_id)

        delete_entry_with_id(Output, form_output.output_id.data)

        channels = OutputChannel.query.filter(
            OutputChannel.output_id == form_output.output_id.data).all()
        for each_channel in channels:
            delete_entry_with_id(OutputChannel, each_channel.unique_id)

        display_order = csv_to_list_of_str(DisplayOrder.query.first().output)
        display_order.remove(form_output.output_id.data)
        DisplayOrder.query.first().output = list_to_csv(display_order)
        db.session.commit()

        if not current_app.config['TESTING']:
            manipulate_output('Delete', form_output.output_id.data)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_output'))


def manipulate_output(action, output_id):
    """
    Add, delete, and modify output settings while the daemon is active

    :param output_id: output ID in the SQL database
    :type output_id: str
    :param action: "Add", "Delete", or "Modify"
    :type action: str
    """
    try:
        control = DaemonControl()
        return_values = control.output_setup(action, output_id)
        if return_values and len(return_values) > 1:
            if return_values[0]:
                flash(gettext("%(err)s",
                              err='{action} Output: Daemon response: {msg}'.format(
                                  action=action,
                                  msg=return_values[1])),
                      "error")
            else:
                flash(gettext("%(err)s",
                              err='{action} Output: Daemon response: {msg}'.format(
                                  action=gettext(action),
                                  msg=return_values[1])),
                      "success")
    except Exception as msg:
        flash(gettext("%(err)s",
                      err='{action} Output: Could not connect to Daemon: {error}'.format(
                          action=action, error=msg)),
              "error")


def get_all_output_states():
    daemon_control = DaemonControl()
    return daemon_control.output_states_all()
