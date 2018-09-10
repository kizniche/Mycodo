# -*- coding: utf-8 -*-
import logging

import os
import sqlalchemy
from RPi import GPIO
from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from flask_babel import gettext

from mycodo.config import DEVICES_DEFAULT_LOCATION
from mycodo.config import LIST_DEVICES_ADC
from mycodo.config import LIST_DEVICES_SPI
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Input
from mycodo.databases.models import PID
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_form_errors
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import reorder
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


#
# Input manipulation
#


def input_add(form_add):
    action = '{action} {controller}'.format(
        action=gettext("Add"),
        controller=gettext("Input"))
    error = []

    dict_inputs = parse_input_information()

    # only one comma should be in the input_type string
    if form_add.input_type.data.count(',') > 1:
        error.append("Invalid input module formatting. It appears there is "
                     "a comma in either 'unique_name_input' or 'interfaces'.")

    if form_add.input_type.data.count(',') == 1:
        input_name = form_add.input_type.data.split(',')[0]
        input_interface = form_add.input_type.data.split(',')[1]
    else:
        input_name = ''
        input_interface = ''
        error.append("Invalid input string (must be a comma-separated string)")

    if current_app.config['TESTING']:
        unmet_deps = False
    else:
        unmet_deps = return_dependencies(input_name)
        if unmet_deps:
            error.append("The {dev} device you're trying to add has unmet dependencies: {dep}".format(
                dev=input_name, dep=unmet_deps))

    if form_add.validate():
        new_input = Input()
        new_input.device = input_name

        if input_interface:
            new_input.interface = input_interface

        if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
            new_input.i2c_bus = 1
        else:
            new_input.i2c_bus = 0

        if 'common_name_input' in dict_inputs[input_name]:
            new_input.name = dict_inputs[input_name]['common_name_input']
        else:
            new_input.name = 'Input Name'

        if ('unique_name_measurements' in dict_inputs[input_name] and
                dict_inputs[input_name]['unique_name_measurements'] != []):
            new_input.measurements = ",".join(dict_inputs[input_name]['unique_name_measurements'])
        elif input_name == 'LinuxCommand':
            pass
        else:
            error.append("No measurements defined for this input.")

        #
        # Set default values for new input being added
        #

        # Set the default measurement values
        list_units = []
        if 'unique_name_measurements' in dict_inputs[input_name]:
            for each_measurement in dict_inputs[input_name]['unique_name_measurements']:
                if each_measurement in MEASUREMENTS:
                    entry = '{measure},{unit}'.format(
                        measure=each_measurement,
                        unit=MEASUREMENTS[each_measurement]['units'][0])
                    list_units.append(entry)
                else:
                    error.append("Measurement '{measure}' not recognized.".format(
                        measure=each_measurement))
            new_input.convert_to_unit = ";".join(list_units)

        # input add options
        if input_name in dict_inputs:
            def dict_has_value(key):
                if (key in dict_inputs[input_name] and
                        (dict_inputs[input_name][key] or dict_inputs[input_name][key] == 0)):
                    return True

            #
            # Interfacing options
            #

            # I2C options
            if input_interface == 'I2C':
                if dict_has_value('i2c_location'):
                    new_input.i2c_location = dict_inputs[input_name]['i2c_location'][0]  # First entry in list

            # UART options
            elif input_interface == 'UART':
                if dict_has_value('uart_location'):
                    new_input.uart_location = dict_inputs[input_name]['uart_location']
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
            if dict_has_value('convert_to_unit'):
                new_input.convert_to_unit = ','.join(dict_inputs[input_name]['convert_to_unit'])

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
            if dict_has_value('adc_channel'):
                if len(dict_inputs[input_name]['adc_channel']) == 1:
                    new_input.adc_channel = dict_inputs[input_name]['adc_channel'][0]
                elif len(dict_inputs[input_name]['adc_channel']) > 1:
                    new_input.adc_channel = dict_inputs[input_name]['adc_channel'][0][0]
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
            if dict_has_value('adc_volts_min'):
                new_input.adc_volts_min = dict_inputs[input_name]['adc_volts_min']
            if dict_has_value('adc_volts_max'):
                new_input.adc_volts_max = dict_inputs[input_name]['adc_volts_max']
            if dict_has_value('adc_units_min'):
                new_input.adc_units_min = dict_inputs[input_name]['adc_units_min']
            if dict_has_value('adc_units_max'):
                new_input.adc_units_max = dict_inputs[input_name]['adc_units_max']
            if dict_has_value('adc_inverse_unit_scale'):
                new_input.adc_inverse_unit_scale = dict_inputs[input_name]['adc_inverse_unit_scale']

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
            if dict_has_value('ref_ohm'):
                new_input.ref_ohm = dict_inputs[input_name]['ref_ohm']

        try:
            if not error:
                new_input.save()

                display_order = csv_to_list_of_str(
                    DisplayOrder.query.first().inputs)

                DisplayOrder.query.first().inputs = add_display_order(
                    display_order, new_input.unique_id)
                db.session.commit()

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

    if unmet_deps:
        return 1


def input_mod(form_mod, request_form):
    action = '{action} {controller}'.format(
        action=gettext("Modify"),
        controller=gettext("Input"))
    error = []

    dict_inputs = parse_input_information()

    try:
        mod_input = Input.query.filter(
            Input.unique_id == form_mod.input_id.data).first()

        if mod_input.is_activated:
            error.append(gettext(
                "Deactivate sensor controller before modifying its "
                "settings"))
        if (mod_input.device == 'AM2315' and
                form_mod.period.data < 7):
            error.append(gettext(
                "Choose a Read Period equal to or greater than 7. The "
                "AM2315 may become unresponsive if the period is "
                "below 7."))
        if (form_mod.selected_measurement_unit.data == '' and
                (mod_input.device == 'LinuxCommand' or
                 mod_input.device in LIST_DEVICES_ADC)):
            error.append(gettext(
                "A unit measurement must be selected."))
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

        if not error:
            mod_input.name = form_mod.name.data

            if form_mod.location.data:
                mod_input.location = form_mod.location.data
            if form_mod.i2c_location.data:
                mod_input.i2c_location = form_mod.i2c_location.data
            if form_mod.uart_location.data:
                mod_input.uart_location = form_mod.uart_location.data
            if form_mod.gpio_location.data:
                mod_input.gpio_location = form_mod.gpio_location.data

            if form_mod.power_output_id.data:
                mod_input.power_output_id = form_mod.power_output_id.data
            else:
                mod_input.power_output_id = None

            if form_mod.pre_output_id.data:
                mod_input.pre_output_id = form_mod.pre_output_id.data
            else:
                mod_input.pre_output_id = None

            if (mod_input.device == 'LinuxCommand' or
                    ('analog_to_digital_converter' in dict_inputs[mod_input.device] and
                     dict_inputs[mod_input.device]['analog_to_digital_converter'])):
                mod_input.convert_to_unit = form_mod.selected_measurement_unit.data

            short_list = []
            mod_units = False
            for key in request_form.keys():
                if 'convert_unit' in key:
                    mod_units = True
                    for value in request_form.getlist(key):
                        if value == 'default':
                            pass
                        elif (len(value.split(',')) < 2 or
                                value.split(',')[0] == '' or value.split(',')[1] == ''):
                            error.append("Invalid custom unit")
                        else:
                            short_list.append(value)
            if mod_units:
                mod_input.convert_to_unit = ';'.join(short_list)

            mod_input.i2c_bus = form_mod.i2c_bus.data
            mod_input.baud_rate = form_mod.baud_rate.data
            mod_input.pre_output_duration = form_mod.pre_output_duration.data
            mod_input.pre_output_during_measure = form_mod.pre_output_during_measure.data
            mod_input.period = form_mod.period.data
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
            # ADC options
            mod_input.adc_channel = form_mod.adc_channel.data
            mod_input.adc_gain = form_mod.adc_gain.data
            mod_input.adc_resolution = form_mod.adc_resolution.data
            mod_input.adc_volts_min = form_mod.adc_volts_min.data
            mod_input.adc_volts_max = form_mod.adc_volts_max.data
            mod_input.adc_units_min = form_mod.adc_units_min.data
            mod_input.adc_units_max = form_mod.adc_units_max.data
            mod_input.adc_inverse_unit_scale = form_mod.adc_inverse_unit_scale.data
            # Switch options
            mod_input.switch_edge = form_mod.switch_edge.data
            mod_input.switch_bouncetime = form_mod.switch_bounce_time.data
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
            db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_del(form_mod):
    action = '{action} {controller}'.format(
        action=gettext("Delete"),
        controller=gettext("Input"))
    error = []

    input_id = form_mod.input_id.data

    try:
        input_dev = Input.query.filter(
            Input.unique_id == input_id).first()
        if input_dev.is_activated:
            input_deactivate_associated_controllers(input_id)
            controller_activate_deactivate('deactivate', 'Input', input_id)

        delete_entry_with_id(Input, input_id)
        try:
            display_order = csv_to_list_of_str(
                DisplayOrder.query.first().inputs)
            display_order.remove(input_id)
            DisplayOrder.query.first().inputs = list_to_csv(display_order)
        except Exception:  # id not in list
            pass
        db.session.commit()
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_data'))


def input_reorder(input_id, display_order, direction):
    action = '{action} {controller}'.format(
        action=gettext("Reorder"),
        controller=gettext("Input"))
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
    input_id = form_mod.input_id.data
    input_dev = Input.query.filter(Input.unique_id == input_id).first()
    if input_dev.device in LIST_DEVICES_SPI:
        if None in [form_mod.pin_clock.data,
                    form_mod.pin_cs.data,
                    form_mod.pin_miso.data]:
            flash("Cannot activate without Serial pins set.", "error")
            return redirect(url_for('routes_page.page_data'))
    elif (input_dev.device == 'LinuxCommand' and
          input_dev.cmd_command is ''):
        flash("Cannot activate Input without a command set.", "error")
        return redirect(url_for('routes_page.page_data'))
    elif (input_dev.device != 'LinuxCommand' and
            not input_dev.location and
            input_dev.device not in DEVICES_DEFAULT_LOCATION):
        flash("Cannot activate Input without the location (GPIO/I2C "
              "Address/Port/etc.) to communicate with it set.", "error")
        return redirect(url_for('routes_page.page_data'))
    controller_activate_deactivate('activate', 'Input',  input_id)


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
