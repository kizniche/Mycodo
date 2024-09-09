# -*- coding: utf-8 -*-
import json
import logging
import os
import re

import sqlalchemy
from flask import current_app
from flask import flash
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases import clone_model
from mycodo.databases import set_uuid
from mycodo.databases.models import Actions
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import InputChannel
from mycodo.databases.models import PID
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils import utils_measurement
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import custom_channel_options_return_json
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_json
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import parse_custom_option_values

logger = logging.getLogger(__name__)

#
# Input manipulation
#

def input_add(form_add):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    new_input_id = None
    list_unmet_deps = []
    dep_name = None
    dep_message = ''

    dict_inputs = parse_input_information()

    # only one comma should be in the input_type string
    if form_add.input_type.data.count(',') > 1:
        messages["error"].append(
            "Invalid input module formatting. It appears there is "
            "a comma in either 'input_name_unique' or 'interfaces'.")

    if form_add.input_type.data.count(',') == 1:
        input_name = form_add.input_type.data.split(',')[0]
        input_interface = form_add.input_type.data.split(',')[1]
    else:
        input_name = ''
        input_interface = ''
        messages["error"].append("Invalid input string (must be a comma-separated string)")

    if not current_app.config['TESTING']:
        dep_unmet, _, dep_message = return_dependencies(input_name)
        if dep_unmet:
            messages["error"].append(
                f"{input_name} has unmet dependencies. "
                "They must be installed before the Input can be added.")

            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[3])
                if each_dep[2] == 'pip-pypi':
                    dep_message += f" The Python package {each_dep[3]} was not found to be installed because '{each_dep[0]}' could not be imported."

            if input_name in dict_inputs:
                dep_name = dict_inputs[input_name]['input_name']
            else:
                messages["error"].append(f"Input not found: {input_name}")

            return messages, dep_name, list_unmet_deps, dep_message, None

    if form_add.validate():
        new_input = Input()
        new_input.device = input_name
        new_input.position_y = 999

        if input_interface:
            new_input.interface = input_interface

        new_input.i2c_bus = 1

        if 'input_name_short' in dict_inputs[input_name]:
            new_input.name = dict_inputs[input_name]['input_name_short']
        elif 'input_name' in dict_inputs[input_name]:
            new_input.name = dict_inputs[input_name]['input_name']
        else:
            new_input.name = 'Name'

        #
        # Set default values for new input being added
        #

        # input add options
        if input_name in dict_inputs:
            def dict_has_value(key):
                if (key in dict_inputs[input_name] and
                        (dict_inputs[input_name][key] or dict_inputs[input_name][key] == 0)):
                    return True

            #
            # Interfacing options
            #

            if input_interface == 'I2C':
                if dict_has_value('i2c_location'):
                    new_input.i2c_location = dict_inputs[input_name]['i2c_location'][0]  # First entry in list

            if input_interface == 'FTDI':
                if dict_has_value('ftdi_location'):
                    new_input.ftdi_location = dict_inputs[input_name]['ftdi_location']

            if input_interface == 'UART':
                if dict_has_value('uart_location'):
                    new_input.uart_location = dict_inputs[input_name]['uart_location']

            # UART options
            if dict_has_value('uart_baud_rate'):
                new_input.baud_rate = dict_inputs[input_name]['uart_baud_rate']
            if dict_has_value('pin_cs'):
                new_input.pin_cs = dict_inputs[input_name]['pin_cs']
            if dict_has_value('pin_miso'):
                new_input.pin_miso = dict_inputs[input_name]['pin_miso']
            if dict_has_value('pin_mosi'):
                new_input.pin_mosi = dict_inputs[input_name]['pin_mosi']
            if dict_has_value('pin_clock'):
                new_input.pin_clock = dict_inputs[input_name]['pin_clock']

            # Bluetooth (BT) options
            elif input_interface == 'BT':
                if dict_has_value('bt_location'):
                    if not re.match("[0-9a-fA-F]{2}([:]?)[0-9a-fA-F]{2}(\\1[0-9a-fA-F]{2}){4}$",
                                    dict_inputs[input_name]['bt_location']):
                        messages["error"].append("Please specify device MAC-Address in format AA:BB:CC:DD:EE:FF")
                    else:
                        new_input.location = dict_inputs[input_name]['bt_location']
                if dict_has_value('bt_adapter'):
                    new_input.bt_adapter = dict_inputs[input_name]['bt_adapter']

            # GPIO options
            elif input_interface == 'GPIO':
                if dict_has_value('gpio_location'):
                    new_input.gpio_location = dict_inputs[input_name]['gpio_location']

            # Custom location location
            elif dict_has_value('location'):
                new_input.location = dict_inputs[input_name]['location']['options'][0][0]  # First entry in list

            #
            # General options
            #

            if dict_has_value('period'):
                new_input.period = dict_inputs[input_name]['period']

            # Server Ping options
            if dict_has_value('times_check'):
                new_input.times_check = dict_inputs[input_name]['times_check']
            if dict_has_value('deadline'):
                new_input.deadline = dict_inputs[input_name]['deadline']
            if dict_has_value('port'):
                new_input.port = dict_inputs[input_name]['port']

            # Signal options
            if dict_has_value('weighting'):
                new_input.weighting = dict_inputs[input_name]['weighting']
            if dict_has_value('sample_time'):
                new_input.sample_time = dict_inputs[input_name]['sample_time']

            # Analog-to-digital converter options
            if dict_has_value('adc_gain'):
                if len(dict_inputs[input_name]['adc_gain']) == 1:
                    new_input.adc_gain = dict_inputs[input_name]['adc_gain'][0]
                elif len(dict_inputs[input_name]['adc_gain']) > 1:
                    new_input.adc_gain = dict_inputs[input_name]['adc_gain'][0][0]
            if dict_has_value('adc_resolution'):
                if len(dict_inputs[input_name]['adc_resolution']) == 1:
                    new_input.adc_resolution = dict_inputs[input_name]['adc_resolution'][0]
                elif len(dict_inputs[input_name]['adc_resolution']) > 1:
                    new_input.adc_resolution = dict_inputs[input_name]['adc_resolution'][0][0]
            if dict_has_value('adc_sample_speed'):
                if len(dict_inputs[input_name]['adc_sample_speed']) == 1:
                    new_input.adc_sample_speed = dict_inputs[input_name]['adc_sample_speed'][0]
                elif len(dict_inputs[input_name]['adc_sample_speed']) > 1:
                    new_input.adc_sample_speed = dict_inputs[input_name]['adc_sample_speed'][0][0]

            # Linux command
            if dict_has_value('cmd_command'):
                new_input.cmd_command = dict_inputs[input_name]['cmd_command']

            # Misc options
            if dict_has_value('resolution'):
                if len(dict_inputs[input_name]['resolution']) == 1:
                    new_input.resolution = dict_inputs[input_name]['resolution'][0]
                elif len(dict_inputs[input_name]['resolution']) > 1:
                    new_input.resolution = dict_inputs[input_name]['resolution'][0][0]
            if dict_has_value('resolution_2'):
                if len(dict_inputs[input_name]['resolution_2']) == 1:
                    new_input.resolution_2 = dict_inputs[input_name]['resolution_2'][0]
                elif len(dict_inputs[input_name]['resolution_2']) > 1:
                    new_input.resolution_2 = dict_inputs[input_name]['resolution_2'][0][0]
            if dict_has_value('sensitivity'):
                if len(dict_inputs[input_name]['sensitivity']) == 1:
                    new_input.sensitivity = dict_inputs[input_name]['sensitivity'][0]
                elif len(dict_inputs[input_name]['sensitivity']) > 1:
                    new_input.sensitivity = dict_inputs[input_name]['sensitivity'][0][0]
            if dict_has_value('thermocouple_type'):
                if len(dict_inputs[input_name]['thermocouple_type']) == 1:
                    new_input.thermocouple_type = dict_inputs[input_name]['thermocouple_type'][0]
                elif len(dict_inputs[input_name]['thermocouple_type']) > 1:
                    new_input.thermocouple_type = dict_inputs[input_name]['thermocouple_type'][0][0]
            if dict_has_value('sht_voltage'):
                if len(dict_inputs[input_name]['sht_voltage']) == 1:
                    new_input.sht_voltage = dict_inputs[input_name]['sht_voltage'][0]
                elif len(dict_inputs[input_name]['sht_voltage']) > 1:
                    new_input.sht_voltage = dict_inputs[input_name]['sht_voltage'][0][0]
            if dict_has_value('ref_ohm'):
                new_input.ref_ohm = dict_inputs[input_name]['ref_ohm']

        #
        # Custom Options
        #

        # Generate string to save from custom options
        messages["error"], custom_options = custom_options_return_json(
            messages["error"], dict_inputs, device=input_name, use_defaults=True)
        new_input.custom_options = custom_options

        #
        # Execute at Creation
        #

        new_input.unique_id = set_uuid()

        if ('execute_at_creation' in dict_inputs[new_input.device] and
                not current_app.config['TESTING']):
            messages["error"], new_input = dict_inputs[new_input.device]['execute_at_creation'](
                messages["error"], new_input, dict_inputs[new_input.device])

        try:
            if not messages["error"]:
                new_input.save()
                new_input_id = new_input.unique_id

                # Create measurements and channels
                messages = check_input_channels_exist(
                    dict_inputs, new_input.device, new_input.unique_id, messages)

                messages["success"].append(
                    f"{TRANSLATIONS['add']['title']} {TRANSLATIONS['input']['title']}")
        except sqlalchemy.exc.OperationalError as except_msg:
            messages["error"].append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            messages["error"].append(except_msg)

    else:
        for field, errors in form_add.errors.items():
            for error in errors:
                messages["error"].append(
                    gettext("Error in the %(field)s field - %(err)s",
                            field=getattr(form_add, field).label.text,
                            err=error))

    return messages, dep_name, list_unmet_deps, dep_message, new_input_id


def input_duplicate(form_mod):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    mod_input = Input.query.filter(
        Input.unique_id == form_mod.input_id.data).first()

    if not mod_input:
        return None, None

    # Duplicate dashboard with new unique_id and name
    new_input = clone_model(
        mod_input, unique_id=set_uuid(), name=f"Copy of {mod_input.name}")

    # Deactivate Input
    mod_input = Input.query.filter(
        Input.unique_id == new_input.unique_id).first()
    if mod_input:
        mod_input.is_activated = False
        mod_input.save()

        dev_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == form_mod.input_id.data).all()
        for each_dev in dev_measurements:
            clone_model(each_dev, unique_id=set_uuid(), device_id=mod_input.unique_id)

        dev_channels = InputChannel.query.filter(
            InputChannel.input_id == form_mod.input_id.data).all()
        for each_dev in dev_channels:
            clone_model(each_dev, unique_id=set_uuid(), input_id=mod_input.unique_id)

    messages["success"].append(
        f"{TRANSLATIONS['duplicate']['title']} {TRANSLATIONS['input']['title']}")

    return messages, new_input.unique_id


def input_mod(form_mod, request_form):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": [],
        "name": None,
        "return_text": []
    }
    page_refresh = False

    dict_inputs = parse_input_information()

    try:
        mod_input = Input.query.filter(
            Input.unique_id == form_mod.input_id.data).first()

        if mod_input.is_activated:
            messages["error"].append(gettext(
                "Deactivate controller before modifying its settings"))

        if (mod_input.device == 'AM2315' and
                form_mod.period.data < 7):
            messages["error"].append(gettext(
                "Choose a Read Period equal to or greater than 7. The "
                "AM2315 may become unresponsive if the period is "
                "below 7."))

        if (form_mod.period.data and
                form_mod.pre_output_duration.data and
                form_mod.pre_output_id.data and
                form_mod.period.data < form_mod.pre_output_duration.data):
            messages["error"].append(gettext(
                "The Read Period cannot be less than the Pre Output Duration"))

        if (form_mod.uart_location.data and
                not os.path.exists(form_mod.uart_location.data)):
            messages["warning"].append(gettext(
                "Invalid device or improper permissions to read device"))

        if ('options_enabled' in dict_inputs[mod_input.device] and
                'gpio_location' in dict_inputs[mod_input.device]['options_enabled'] and
                form_mod.gpio_location.data is None):
            messages["error"].append(gettext("Pin (GPIO) must be set"))

        mod_input.name = form_mod.name.data
        messages["name"] = form_mod.name.data

        if mod_input.unique_id != form_mod.unique_id.data:
            test_unique_id = Input.query.filter(Input.unique_id == form_mod.unique_id.data).first()
            if test_unique_id:
                messages["error"].append(
                    f"Input ID must be unique. "
                    f"ID already exists: '{form_mod.unique_id.data}'")
            elif not form_mod.unique_id.data:
                messages["error"].append(f"Input ID is required")
            else:
                mod_input.unique_id = form_mod.unique_id.data

        if form_mod.location.data:
            mod_input.location = form_mod.location.data
        if form_mod.i2c_location.data:
            mod_input.i2c_location = form_mod.i2c_location.data
        if form_mod.ftdi_location.data:
            mod_input.ftdi_location = form_mod.ftdi_location.data
        if form_mod.uart_location.data:
            mod_input.uart_location = form_mod.uart_location.data
        if form_mod.gpio_location.data and form_mod.gpio_location.data is not None:
            mod_input.gpio_location = form_mod.gpio_location.data

        if form_mod.power_output_id.data:
            mod_input.power_output_id = form_mod.power_output_id.data
        else:
            mod_input.power_output_id = None

        if form_mod.pre_output_id.data:
            mod_input.pre_output_id = form_mod.pre_output_id.data
        else:
            mod_input.pre_output_id = None

        # Enable/disable Channels
        measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == form_mod.input_id.data).all()
        if form_mod.measurements_enabled.data:
            for each_measurement in measurements:
                if each_measurement.unique_id in form_mod.measurements_enabled.data:
                    each_measurement.is_enabled = True
                else:
                    each_measurement.is_enabled = False

        mod_input.log_level_debug = form_mod.log_level_debug.data
        mod_input.i2c_bus = form_mod.i2c_bus.data
        mod_input.baud_rate = form_mod.baud_rate.data
        mod_input.pre_output_duration = form_mod.pre_output_duration.data
        mod_input.pre_output_during_measure = form_mod.pre_output_during_measure.data

        if form_mod.period.data:
            mod_input.period = form_mod.period.data
        if form_mod.start_offset.data:
            mod_input.start_offset = form_mod.start_offset.data

        mod_input.resolution = form_mod.resolution.data
        mod_input.resolution_2 = form_mod.resolution_2.data
        mod_input.sensitivity = form_mod.sensitivity.data
        mod_input.calibrate_sensor_measure = form_mod.calibrate_sensor_measure.data
        mod_input.cmd_command = form_mod.cmd_command.data
        mod_input.thermocouple_type = form_mod.thermocouple_type.data
        mod_input.ref_ohm = form_mod.ref_ohm.data
        # Serial options
        mod_input.pin_clock = form_mod.pin_clock.data
        mod_input.pin_cs = form_mod.pin_cs.data
        mod_input.pin_mosi = form_mod.pin_mosi.data
        mod_input.pin_miso = form_mod.pin_miso.data
        # Bluetooth options
        mod_input.bt_adapter = form_mod.bt_adapter.data

        mod_input.adc_gain = form_mod.adc_gain.data
        mod_input.adc_resolution = form_mod.adc_resolution.data
        mod_input.adc_sample_speed = form_mod.adc_sample_speed.data

        # Switch options
        mod_input.switch_edge = form_mod.switch_edge.data
        mod_input.switch_bouncetime = form_mod.switch_bouncetime.data
        mod_input.switch_reset_period = form_mod.switch_reset_period.data
        # PWM and RPM options
        mod_input.weighting = form_mod.weighting.data
        mod_input.rpm_pulses_per_rev = form_mod.rpm_pulses_per_rev.data
        mod_input.sample_time = form_mod.sample_time.data
        # Server options
        mod_input.port = form_mod.port.data
        mod_input.times_check = form_mod.times_check.data
        mod_input.deadline = form_mod.deadline.data
        # SHT sensor options
        if form_mod.sht_voltage.data:
            mod_input.sht_voltage = form_mod.sht_voltage.data

        channels = InputChannel.query.filter(
            InputChannel.input_id == form_mod.input_id.data)

        # Ensure all required measurements and channels exist
        messages = check_input_channels_exist(
            dict_inputs, mod_input.device, mod_input.unique_id, messages)

        # Save Measurement settings
        messages, page_refresh = utils_measurement.measurement_mod_form(
            messages, page_refresh, request_form)

        # Add or delete channels for variable measurement Inputs
        if ('measurements_variable_amount' in dict_inputs[mod_input.device] and
                dict_inputs[mod_input.device]['measurements_variable_amount']):
            measurements = DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == form_mod.input_id.data)

            if measurements.count() != form_mod.num_channels.data:
                page_refresh = True

                # Delete measurements/channels
                if form_mod.num_channels.data < measurements.count():
                    for index, each_channel in enumerate(measurements.all()):
                        if index + 1 > form_mod.num_channels.data:
                            delete_entry_with_id(
                                DeviceMeasurements,
                                each_channel.unique_id,
                                flash_message=False)

                    if ('channel_quantity_same_as_measurements' in dict_inputs[mod_input.device] and
                            dict_inputs[mod_input.device]["channel_quantity_same_as_measurements"]):
                        if form_mod.num_channels.data < channels.count():
                            for index, each_channel in enumerate(channels.all()):
                                if index + 1 > form_mod.num_channels.data:
                                    delete_entry_with_id(
                                        InputChannel,
                                        each_channel.unique_id,
                                        flash_message=False)

                # Add measurements/channels
                elif form_mod.num_channels.data > measurements.count():
                    start_number = measurements.count()
                    for index in range(start_number, form_mod.num_channels.data):
                        new_measurement = DeviceMeasurements()
                        new_measurement.name = ""
                        new_measurement.device_id = mod_input.unique_id
                        new_measurement.measurement = ""
                        new_measurement.unit = ""
                        new_measurement.channel = index
                        new_measurement.save()

                        if ('channel_quantity_same_as_measurements' in dict_inputs[mod_input.device] and
                                dict_inputs[mod_input.device]["channel_quantity_same_as_measurements"]):
                            new_channel = InputChannel()
                            new_channel.name = ""
                            new_channel.input_id = mod_input.unique_id
                            new_channel.channel = index

                            messages["error"], custom_options = custom_channel_options_return_json(
                                messages["error"], dict_inputs, request_form,
                                mod_input.unique_id, index,
                                device=mod_input.device, use_defaults=True)
                            new_channel.custom_options = custom_options

                            new_channel.save()

        # Parse pre-save custom options for output device and its channels
        try:
            custom_options_dict_presave = json.loads(mod_input.custom_options)
        except:
            logger.error("Malformed JSON")
            custom_options_dict_presave = {}

        custom_options_channels_dict_presave = {}
        for each_channel in channels.all():
            if each_channel.custom_options and each_channel.custom_options != "{}":
                custom_options_channels_dict_presave[each_channel.channel] = json.loads(
                    each_channel.custom_options)
            else:
                custom_options_channels_dict_presave[each_channel.channel] = {}

        # Parse post-save custom options for output device and its channels
        messages["error"], custom_options_json_postsave = custom_options_return_json(
            messages["error"], dict_inputs, request_form,
            mod_dev=mod_input,
            device=mod_input.device,
            custom_options=custom_options_dict_presave)
        custom_options_dict_postsave = json.loads(custom_options_json_postsave)

        custom_options_channels_dict_postsave = {}
        for each_channel in channels.all():
            messages["error"], custom_options_channels_json_postsave_tmp = custom_channel_options_return_json(
                messages["error"], dict_inputs, request_form,
                form_mod.input_id.data, each_channel.channel,
                device=mod_input.device, use_defaults=False)
            custom_options_channels_dict_postsave[each_channel.channel] = json.loads(
                custom_options_channels_json_postsave_tmp)

        if 'execute_at_modification' in dict_inputs[mod_input.device]:
            # pass custom options to module prior to saving to database
            (messages,
             mod_input,
             custom_options_dict,
             custom_options_channels_dict) = dict_inputs[mod_input.device]['execute_at_modification'](
                messages,
                mod_input,
                request_form,
                custom_options_dict_presave,
                custom_options_channels_dict_presave,
                custom_options_dict_postsave,
                custom_options_channels_dict_postsave)
            custom_options = json.dumps(custom_options_dict)  # Convert from dict to JSON string
            custom_channel_options = custom_options_channels_dict
        else:
            # Don't pass custom options to module
            custom_options = json.dumps(custom_options_dict_postsave)
            custom_channel_options = custom_options_channels_dict_postsave

        # Finally, save custom options for both output and channels
        mod_input.custom_options = custom_options
        for each_channel in channels:
            if 'name' in custom_channel_options[each_channel.channel]:
                each_channel.name = custom_channel_options[each_channel.channel]['name']
            each_channel.custom_options = json.dumps(custom_channel_options[each_channel.channel])

        if not messages["error"]:
            db.session.commit()
            messages["success"].append(
                f"{TRANSLATIONS['modify']['title']} {TRANSLATIONS['input']['title']}")

    except Exception as except_msg:
        logger.exception("input_mod")
        messages["error"].append(str(except_msg))

    return messages, page_refresh


def input_del(input_id):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        input_dev = Input.query.filter(
            Input.unique_id == input_id).first()

        if input_dev.is_activated:
            # messages = input_deactivate_associated_controllers(
            #     messages, input_id)
            messages = controller_activate_deactivate(
                messages, 'deactivate', 'Input', input_id)

        actions = Actions.query.filter(
            Actions.function_id == input_id).all()
        for each_action in actions:
            delete_entry_with_id(
                Actions, each_action.unique_id, flash_message=False)

        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == input_id).all()
        for each_measurement in device_measurements:
            delete_entry_with_id(
                DeviceMeasurements,
                each_measurement.unique_id,
                flash_message=False)

        channels = InputChannel.query.filter(
            InputChannel.input_id == input_id).all()
        for each_channel in channels:
            delete_entry_with_id(
                InputChannel,
                each_channel.unique_id,
                flash_message=False)

        delete_entry_with_id(Input, input_id, flash_message=False)

        try:
            file_path = os.path.join(
                PATH_PYTHON_CODE_USER, f'input_python_code_{input_dev.unique_id}.py')
            os.remove(file_path)
        except:
            pass

        db.session.commit()
        messages["success"].append(
            f"{TRANSLATIONS['delete']['title']} {TRANSLATIONS['input']['title']}")
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def input_activate(form_mod):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    dict_inputs = parse_input_information()
    input_id = form_mod.input_id.data
    input_dev = Input.query.filter(Input.unique_id == input_id).first()
    device_measurements = DeviceMeasurements.query.filter(
        DeviceMeasurements.device_id == input_dev.unique_id)

    custom_options_values_inputs = parse_custom_option_values(
        input_dev, dict_controller=dict_inputs)

    #
    # General Input checks
    #
    if not input_dev.period:
        messages["error"].append("Period must be set")

    if (input_dev.pre_output_id and
            len(input_dev.pre_output_id) > 1 and
            not input_dev.pre_output_duration):
        messages["error"].append("Pre Output Duration must be > 0 if Pre Output is enabled")

    if not device_measurements.filter(DeviceMeasurements.is_enabled.is_(True)).count():
        messages["error"].append("At least one measurement must be enabled")

    #
    # Check if required custom options are set
    #
    if 'custom_options' in dict_inputs[input_dev.device]:
        for each_option in dict_inputs[input_dev.device]['custom_options']:
            if 'id' not in each_option:
                continue

            if each_option['id'] not in custom_options_values_inputs[input_dev.unique_id]:
                if 'required' in each_option and each_option['required']:
                    messages["error"].append(
                        f"{each_option['name']} not found and is required to be set. "
                        "Set option and save Input.")
            else:
                value = custom_options_values_inputs[input_dev.unique_id][each_option['id']]
                if ('required' in each_option and
                        each_option['required'] and
                        value != 0 and
                        not value):
                    messages["error"].append(
                        f"{each_option['name']} is required to be set. "
                        f"Current value: {value}")

    #
    # Input-specific checks
    #
    if input_dev.device == 'LinuxCommand' and not input_dev.cmd_command:
        messages["error"].append("Cannot activate Command Input without a Command set")

    elif ('measurements_variable_amount' in dict_inputs[input_dev.device] and
            dict_inputs[input_dev.device]['measurements_variable_amount']):
        measure_set = True
        for each_channel in device_measurements.all():
            if (not each_channel.name or
                    not each_channel.measurement or
                    not each_channel.unit):
                measure_set = False
        if not measure_set:
            messages["error"].append("All measurements must have a name and unit/measurement set")


    messages = controller_activate_deactivate(
        messages, 'activate', 'Input',  input_id, flash_message=False)

    if not messages["error"]:
        messages["success"].append(
            f"{TRANSLATIONS['activate']['title']} {TRANSLATIONS['input']['title']}")

    return messages


def input_deactivate(form_mod):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        input_id = form_mod.input_id.data
        # messages = input_deactivate_associated_controllers(messages, input_id)
        messages = controller_activate_deactivate(
            messages, 'deactivate', 'Input', input_id, flash_message=False)
        messages["success"].append(
            f"{TRANSLATIONS['deactivate']['title']} {TRANSLATIONS['input']['title']}")
    except Exception as err:
        messages["error"].append(f"Error deactivating Input: {err}")

    return messages


# Deactivate any active PID controllers using this Input
def input_deactivate_associated_controllers(messages, input_id):
    # Deactivate any activated PIDs using this input
    sensor_unique_id = Input.query.filter(
        Input.unique_id == input_id).first().unique_id
    pid = PID.query.filter(PID.is_activated.is_(True)).all()
    for each_pid in pid:
        if sensor_unique_id in each_pid.measurement:
            messages = controller_activate_deactivate(
                messages, 'deactivate', 'PID', each_pid.unique_id)
    return messages


def check_input_channels_exist(dict_inputs, device, unique_id, messages):
    """Ensure all measurements and channels exist for Input"""
    try:
        #
        # If there are a variable number of measurements
        #
        if ('measurements_variable_amount' in dict_inputs[device] and
                dict_inputs[device]['measurements_variable_amount']):
            # Add first default measurement with empty unit and measurement
            measure_exists = DeviceMeasurements.query.filter(
                DeviceMeasurements.device_id == unique_id).count()

            if not measure_exists:
                new_measurement = DeviceMeasurements()
                new_measurement.name = ""
                new_measurement.device_id = unique_id
                new_measurement.measurement = ""
                new_measurement.unit = ""
                new_measurement.channel = 0
                new_measurement.save()

        #
        # If measurements defined in the Input Module
        #

        elif ('measurements_dict' in dict_inputs[device] and
              dict_inputs[device]['measurements_dict']):
            for each_channel in dict_inputs[device]['measurements_dict']:

                measure_exists = DeviceMeasurements.query.filter(
                    and_(DeviceMeasurements.device_id == unique_id,
                         DeviceMeasurements.channel == each_channel)).count()

                if measure_exists:
                    continue

                measure_info = dict_inputs[device]['measurements_dict'][each_channel]
                new_measurement = DeviceMeasurements()
                if 'name' in measure_info:
                    new_measurement.name = measure_info['name']
                new_measurement.device_id = unique_id
                new_measurement.measurement = measure_info['measurement']
                new_measurement.unit = measure_info['unit']
                new_measurement.channel = each_channel
                new_measurement.save()

        if 'channels_dict' in dict_inputs[device]:
            for each_channel, channel_info in dict_inputs[device]['channels_dict'].items():
                channel_exists = InputChannel.query.filter(
                    and_(InputChannel.input_id == unique_id,
                         InputChannel.channel == each_channel)).count()

                if channel_exists:
                    continue

                new_channel = InputChannel()
                new_channel.channel = each_channel
                new_channel.input_id = unique_id

                # Generate string to save from custom options
                messages["error"], custom_options = custom_channel_options_return_json(
                    messages["error"], dict_inputs, None,
                    unique_id, each_channel,
                    device=device, use_defaults=True)
                new_channel.custom_options = custom_options

                new_channel.save()
    except:
        logger.exception("check_input_channels_exist()")

    return messages

def force_acquire_measurements(unique_id):
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        mod_input = Input.query.filter(
            Input.unique_id == unique_id).first()

        if not mod_input.is_activated:
            messages["error"].append(gettext(
                "Activate controller before attempting to force the acquisition of measurements"))

        if not messages["error"]:
            control = DaemonControl()
            status = control.input_force_measurements(unique_id)
            if status[0]:
                messages["error"].append(f"Force Input Measurement: {status[1]}")
            else:
                messages["success"].append(
                    f"{gettext('Force Measurements')}, {TRANSLATIONS['input']['title']}")
                flash(f"Force Input Measurement: {status[1]}", "success")
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages
