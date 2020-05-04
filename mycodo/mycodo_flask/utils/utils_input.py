# -*- coding: utf-8 -*-
import logging

import os
import sqlalchemy
from flask import current_app
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import PID
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import custom_options_return_string
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv
from mycodo.utils.system_pi import parse_custom_option_values

logger = logging.getLogger(__name__)


#
# Input manipulation
#

def input_add(form_add):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller=TRANSLATIONS['input']['title'])
    error = []

    dict_inputs = parse_input_information()

    # only one comma should be in the input_type string
    if form_add.input_type.data.count(',') > 1:
        error.append("Invalid input module formatting. It appears there is "
                     "a comma in either 'input_name_unique' or 'interfaces'.")

    if form_add.input_type.data.count(',') == 1:
        input_name = form_add.input_type.data.split(',')[0]
        input_interface = form_add.input_type.data.split(',')[1]
    else:
        input_name = ''
        input_interface = ''
        error.append("Invalid input string (must be a comma-separated string)")

    if current_app.config['TESTING']:
        dep_unmet = False
    else:
        dep_unmet, _ = return_dependencies(input_name)
        if dep_unmet:
            list_unmet_deps = []
            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[0])
            error.append("The {dev} device you're trying to add has unmet dependencies: {dep}".format(
                dev=input_name, dep=', '.join(list_unmet_deps)))

    if form_add.validate():
        new_input = Input()
        new_input.device = input_name

        if input_interface:
            new_input.interface = input_interface

        try:
            from RPi import GPIO
            if GPIO.RPI_INFO['P1_REVISION'] == 1:
                new_input.i2c_bus = 0
            else:
                new_input.i2c_bus = 1
        except:
            logger.error(
                "RPi.GPIO and Raspberry Pi required for this action")

        if 'input_name' in dict_inputs[input_name]:
            new_input.name = dict_inputs[input_name]['input_name']
        else:
            new_input.name = 'Input Name'

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

        list_options = []
        if 'custom_options' in dict_inputs[input_name]:
            for each_option in dict_inputs[input_name]['custom_options']:
                if each_option['default_value'] is False:
                    default_value = ''
                else:
                    default_value = each_option['default_value']
                option = '{id},{value}'.format(
                    id=each_option['id'],
                    value=default_value)
                list_options.append(option)
        new_input.custom_options = ';'.join(list_options)

        try:
            if not error:
                new_input.save()

                display_order = csv_to_list_of_str(
                    DisplayOrder.query.first().inputs)

                DisplayOrder.query.first().inputs = add_display_order(
                    display_order, new_input.unique_id)
                db.session.commit()

                #
                # Execute at Creation
                #

                if 'execute_at_creation' in dict_inputs[new_input.device] and not current_app.config['TESTING']:
                    (creation_errors,
                     tuple_code_filename) = dict_inputs[new_input.device]['execute_at_creation'](
                        new_input.unique_id, new_input.cmd_command, dict_inputs[input_name])
                    if creation_errors:
                        for each_error in creation_errors:
                            flash(each_error, 'error')

                #
                # If there are a variable number of measurements
                #

                if ('measurements_variable_amount' in dict_inputs[input_name] and
                        dict_inputs[input_name]['measurements_variable_amount']):
                    # Add first default measurement with empty unit and measurement
                    new_measurement = DeviceMeasurements()
                    new_measurement.name = ""
                    new_measurement.device_id = new_input.unique_id
                    new_measurement.measurement = ""
                    new_measurement.unit = ""
                    new_measurement.channel = 0
                    new_measurement.save()

                #
                # If measurements defined in the Input Module
                #

                elif ('measurements_dict' in dict_inputs[input_name] and
                        dict_inputs[input_name]['measurements_dict'] != []):
                    for each_channel in dict_inputs[input_name]['measurements_dict']:
                        measure_info = dict_inputs[input_name]['measurements_dict'][each_channel]
                        new_measurement = DeviceMeasurements()
                        if 'name' in measure_info:
                            new_measurement.name = measure_info['name']
                        new_measurement.device_id = new_input.unique_id
                        new_measurement.measurement = measure_info['measurement']
                        new_measurement.unit = measure_info['unit']
                        new_measurement.channel = each_channel
                        new_measurement.save()

                flash(gettext(
                    "%(type)s Input with ID %(id)s (%(uuid)s) successfully added",
                    type=input_name,
                    id=new_input.id,
                    uuid=new_input.unique_id),
                      "success")
        except sqlalchemy.exc.OperationalError as except_msg:
            error.append(except_msg)
        except sqlalchemy.exc.IntegrityError as except_msg:
            error.append(except_msg)

        flash_success_errors(error, action, url_for('routes_page.page_data'))
    else:
        flash_form_errors(form_add)

    if dep_unmet:
        return 1


def input_mod(form_mod, request_form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['input']['title'])
    error = []

    dict_inputs = parse_input_information()

    try:
        mod_input = Input.query.filter(
            Input.unique_id == form_mod.input_id.data).first()

        if mod_input.is_activated:
            error.append(gettext(
                "Deactivate controller before modifying its settings"))

        if (mod_input.device == 'AM2315' and
                form_mod.period.data < 7):
            error.append(gettext(
                "Choose a Read Period equal to or greater than 7. The "
                "AM2315 may become unresponsive if the period is "
                "below 7."))

        if (mod_input.device != 'EDGE' and
                (mod_input.pre_output_duration and
                 form_mod.period.data < mod_input.pre_output_duration)):
            error.append(gettext(
                "The Read Period cannot be less than the Pre Output "
                "Duration"))

        if (form_mod.uart_location.data and
                not os.path.exists(form_mod.uart_location.data)):
            error.append(gettext(
                "Invalid device or improper permissions to read device"))

        if ('gpio_location' in dict_inputs[mod_input.device]['options_enabled'] and
                form_mod.gpio_location.data is None):
            error.append(gettext("Pin (GPIO) must be set"))

        mod_input.name = form_mod.name.data

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

        if 'test_before_saving' in dict_inputs[mod_input.device]:
            (constraints_pass,
             constraints_errors,
             mod_input) = dict_inputs[mod_input.device]['test_before_saving'](
                mod_input, request_form)
            if constraints_pass:
                pass
            elif constraints_errors:
                for each_error in constraints_errors:
                    flash(each_error, 'error')

        # Generate string to save from custom options
        error, custom_options = custom_options_return_string(
            error, dict_inputs, mod_input, request_form)

        if not error:
            mod_input.custom_options = custom_options

            # Add or delete channels for variable measurement Inputs
            if ('measurements_variable_amount' in dict_inputs[mod_input.device] and
                    dict_inputs[mod_input.device]['measurements_variable_amount']):
                channels = DeviceMeasurements.query.filter(
                    DeviceMeasurements.device_id == form_mod.input_id.data)

                if channels.count() != form_mod.num_channels.data:
                    # Delete channels
                    if form_mod.num_channels.data < channels.count():
                        for index, each_channel in enumerate(channels.all()):
                            if index + 1 >= channels.count():
                                delete_entry_with_id(DeviceMeasurements,
                                                     each_channel.unique_id)

                    # Add channels
                    elif form_mod.num_channels.data > channels.count():
                        start_number = channels.count()
                        for index in range(start_number, form_mod.num_channels.data):
                            new_measurement = DeviceMeasurements()
                            new_measurement.name = ""
                            new_measurement.device_id = mod_input.unique_id
                            new_measurement.measurement = ""
                            new_measurement.unit = ""
                            new_measurement.channel = index
                            new_measurement.save()

            db.session.commit()

    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def measurement_mod(form):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['measurement']['title'])
    error = []

    try:
        mod_meas = DeviceMeasurements.query.filter(
            DeviceMeasurements.unique_id == form.input_measurement_id.data).first()

        mod_input = Input.query.filter(Input.unique_id == mod_meas.device_id).first()
        if mod_input.is_activated:
            error.append(gettext(
                "Deactivate controller before modifying its settings"))

        mod_meas.name = form.name.data

        if form.input_type.data == 'measurement_select':
            mod_meas.measurement = form.select_measurement_unit.data.split(',')[0]
            mod_meas.unit = form.select_measurement_unit.data.split(',')[1]

        elif form.input_type.data == 'measurement_convert':
            input_info = parse_input_information()
            if ('enable_channel_unit_select' in input_info[mod_input.device] and
                    input_info[mod_input.device]['enable_channel_unit_select']):
                if ',' in form.select_measurement_unit.data:
                    mod_meas.measurement = form.select_measurement_unit.data.split(',')[0]
                    mod_meas.unit = form.select_measurement_unit.data.split(',')[1]
                else:
                    mod_meas.measurement = ''
                    mod_meas.unit = ''

            if form.rescaled_measurement_unit.data != '' and ',' in form.rescaled_measurement_unit.data:
                mod_meas.rescaled_measurement = form.rescaled_measurement_unit.data.split(',')[0]
                mod_meas.rescaled_unit = form.rescaled_measurement_unit.data.split(',')[1]
            elif form.rescaled_measurement_unit.data == '':
                mod_meas.rescaled_measurement = ''
                mod_meas.rescaled_unit = ''

            mod_meas.scale_from_min = form.scale_from_min.data
            mod_meas.scale_from_max = form.scale_from_max.data
            mod_meas.scale_to_min = form.scale_to_min.data
            mod_meas.scale_to_max = form.scale_to_max.data
            mod_meas.invert_scale = form.invert_scale.data
            mod_meas.conversion_id = form.convert_to_measurement_unit.data

        if not error:
            db.session.commit()

    except Exception as except_msg:
        logger.exception(1)
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_del(input_id):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['input']['title'])
    error = []

    try:
        input_dev = Input.query.filter(
            Input.unique_id == input_id).first()

        if input_dev.is_activated:
            input_deactivate_associated_controllers(input_id)
            controller_activate_deactivate('deactivate', 'Input', input_id)

        device_measurements = DeviceMeasurements.query.filter(
            DeviceMeasurements.device_id == input_id).all()

        for each_measurement in device_measurements:
            delete_entry_with_id(DeviceMeasurements, each_measurement.unique_id)

        delete_entry_with_id(Input, input_id)
        try:
            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().inputs)
            display_order.remove(input_id)
            DisplayOrder.query.first().inputs = list_to_csv(display_order)
        except Exception:  # id not in list
            pass

        try:
            file_path = os.path.join(
                PATH_PYTHON_CODE_USER, 'input_python_code_{}.py'.format(
                    input_dev.unique_id))
            os.remove(file_path)
        except:
            pass

        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_reorder(input_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['reorder']['title'],
        controller=TRANSLATIONS['input']['title'])
    error = []

    try:
        status, reord_list = reorder(display_order, input_id, direction)
        if status == 'success':
            DisplayOrder.query.first().inputs = ','.join(map(str, reord_list))
            db.session.commit()
        elif status == 'error':
            error.append(reord_list)
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_activate(form_mod):
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['input']['title'])
    error = []
    dict_inputs = parse_input_information()
    input_id = form_mod.input_id.data
    input_dev = Input.query.filter(Input.unique_id == input_id).first()
    device_measurements = DeviceMeasurements.query.filter(
        DeviceMeasurements.device_id == input_dev.unique_id)
    custom_options_values_inputs = parse_custom_option_values(input_dev)

    #
    # General Input checks
    #
    if not input_dev.period:
        error.append("Period must be set")

    if (input_dev.pre_output_id and
            len(input_dev.pre_output_id) > 1 and
            not input_dev.pre_output_duration):
        error.append("Pre Output Duration must be > 0 if Pre Output is enabled")

    if not device_measurements.filter(DeviceMeasurements.is_enabled == True).count():
        error.append("At least one measurement must be enabled")

    #
    # Check if required custom options are set
    #
    if 'custom_options' in dict_inputs[input_dev.device]:
        for each_option in dict_inputs[input_dev.device]['custom_options']:
            if each_option['id'] not in custom_options_values_inputs[input_dev.unique_id]:
                if ('required' in each_option and each_option['required']):
                    error.append("{} not found and is required to be set. "
                                 "Set option and save Input.".format(
                        each_option['name']))
            else:
                value = custom_options_values_inputs[input_dev.unique_id][each_option['id']]
                if ('required' in each_option and
                        each_option['required'] and
                        not value):
                    error.append("{} is required to be set".format(
                        each_option['name']))

    #
    # Input-specific checks
    #
    if input_dev.device == 'LinuxCommand' and not input_dev.cmd_command:
        error.append("Cannot activate Command Input without a Command set")

    elif ('measurements_variable_amount' in dict_inputs[input_dev.device] and
            dict_inputs[input_dev.device]['measurements_variable_amount']):
        measure_set = True
        for each_channel in device_measurements.all():
            if (not each_channel.name or
                    not each_channel.measurement or
                    not each_channel.unit):
                measure_set = False
        if not measure_set:
            error.append("All measurements must have a name and unit/measurement set")

    if not error:
        controller_activate_deactivate('activate', 'Input',  input_id)
    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_deactivate(form_mod):
    input_id = form_mod.input_id.data
    input_deactivate_associated_controllers(input_id)
    controller_activate_deactivate('deactivate', 'Input', input_id)


# Deactivate any active PID or LCD controllers using this sensor
def input_deactivate_associated_controllers(input_id):
    # Deactivate any activated PIDs using this input
    sensor_unique_id = Input.query.filter(
        Input.unique_id == input_id).first().unique_id
    pid = PID.query.filter(PID.is_activated == True).all()
    for each_pid in pid:
        if sensor_unique_id in each_pid.measurement:
            controller_activate_deactivate('deactivate',
                                           'PID',
                                           each_pid.unique_id)


def force_acquire_measurements(unique_id):
    action = '{action}, {controller}'.format(
        action=gettext("Force Measurements"),
        controller=TRANSLATIONS['input']['title'])
    error = []

    try:
        mod_input = Input.query.filter(
            Input.unique_id == unique_id).first()

        if not mod_input.is_activated:
            error.append(gettext(
                "Activate controller before attempting to force the acquisition of measurements"))

        if not error:
            control = DaemonControl()
            status = control.input_force_measurements(unique_id)
            if status[0]:
                flash("Force Input Measurement: {}".format(status[1]), "error")
            else:
                flash("Force Input Measurement: {}".format(status[1]), "success")
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_data'))


def custom_action(dict_inputs, unique_id, form):
    action = '{action}, {controller}'.format(
        action=gettext("Action"),
        controller=TRANSLATIONS['input']['title'])
    error = []

    try:
        input_dev = Input.query.filter(
            Input.unique_id == unique_id).first()

        if not input_dev:
            return
        elif not input_dev.is_activated:
            error.append(gettext(
                "Activate controller before attempting to use action"))

        option_types = {}
        if 'custom_actions' in dict_inputs[input_dev.device]:
            for each_option in dict_inputs[input_dev.device]['custom_actions']:
                if 'id' in each_option and 'type' in each_option:
                    option_types[each_option['id']] = each_option['type']

        args_dict = {}
        button_id = None
        for key in form.keys():
            if key.startswith('custom_button_'):
                button_id = key[14:]
            else:
                for value in form.getlist(key):
                    if key in option_types:
                        if option_types[key] == 'integer':
                            try:
                                args_dict[key] = int(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent integer: '{}'".format(key, value))
                        elif option_types[key] == 'float':
                            try:
                                args_dict[key] = float(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent float: '{}'".format(key, value))
                        elif option_types[key] == 'bool':
                            try:
                                args_dict[key] = bool(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent bool: '{}'".format(key, value))
                        elif option_types[key] == 'text':
                            try:
                                args_dict[key] = str(value)
                            except:
                                logger.error("Value of option '{}' doesn't represent string: '{}'".format(key, value))
                        else:
                            args_dict[key] = float(value)

        if not button_id:
            return

        if not error and button_id:
            control = DaemonControl()
            status = control.input_custom_button(unique_id, button_id, args_dict)
            if status[0]:
                flash("Custom Button: {}".format(status[1]), "error")
            else:
                flash("Custom Button: {}".format(status[1]), "success")
    except Exception as except_msg:
        error.append(except_msg)
    flash_success_errors(error, action, url_for('routes_page.page_data'))
