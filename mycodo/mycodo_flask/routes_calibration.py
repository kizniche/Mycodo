# coding=utf-8
""" collection of Page endpoints """
import logging
import time

import flask_login
import os
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
from flask.blueprints import Blueprint
from flask_babel import gettext

from mycodo.config import PATH_1WIRE
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Input
from mycodo.databases.models import Output
from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
from mycodo.mycodo_flask.forms import forms_calibration
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils.utils_general import generate_form_input_list
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.calibration import AtlasScientificCommand
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import str_is_float

logger = logging.getLogger('mycodo.mycodo_flask.calibration')

blueprint = Blueprint('routes_calibration',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.route('/calibration', methods=('GET', 'POST'))
@flask_login.login_required
def calibration_select():
    """
    Landing page to initially select the device to calibrate
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))

    form_calibration = forms_calibration.Calibration()

    if form_calibration.submit.data:
        route = 'routes_calibration.{page}'.format(
            page=form_calibration.selection.data)
        return redirect(url_for(route))
    return render_template('tools/calibration.html',
                           form_calibration=form_calibration)


@blueprint.route('/setup_atlas_ezo_pump', methods=('GET', 'POST'))
@flask_login.login_required
def setup_atlas_ezo_pump():
    """
    Step-by-step tool for calibrating the Atlas Scientific pH sensor
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))

    form_ezo_pump_calibrate = forms_calibration.CalibrationAtlasEZOPump()

    output = Output.query.filter(Output.output_type == 'atlas_ezo_pmp').all()

    ui_stage = 'start'
    backend_stage = None
    selected_output = None
    output_device_name = None
    complete_with_error = None

    if form_ezo_pump_calibrate.hidden_current_stage.data:
        backend_stage = form_ezo_pump_calibrate.hidden_current_stage.data

    if form_ezo_pump_calibrate.go_to_last_stage.data:
        selected_output = Output.query.filter(
            Output.unique_id == form_ezo_pump_calibrate.hidden_output_id.data).first()
        output_device_name = selected_output.name

    def connect_atlas_ezo_pump(selected_output):
        atlas_command = None
        if selected_output.interface == 'FTDI':
            atlas_command = AtlasScientificFTDI(selected_output.ftdi_location)
        elif selected_output.interface == 'I2C':
            atlas_command = AtlasScientificI2C(
                i2c_address=int(str(selected_output.location), 16),
                i2c_bus=selected_output.i2c_bus)
        elif selected_output.interface == 'UART':
            atlas_command = AtlasScientificUART(
                selected_output.location,
                baudrate=selected_output.baud_rate)
        return atlas_command

    # Clear Calibration memory
    if form_ezo_pump_calibrate.clear_calibration.data:
        selected_output = Output.query.filter(
            Output.unique_id == form_ezo_pump_calibrate.selected_output_id.data).first()
        if not selected_output:
            flash('Output not found: {}'.format(
                form_ezo_pump_calibrate.selected_output_id.data), 'error')
        else:
            atlas_command = connect_atlas_ezo_pump(selected_output)
            if atlas_command:
                write_cmd = 'Cal,clear'
                logger.error("EZO-PMP command: {}".format(write_cmd))
                status, msg = atlas_command.query(write_cmd)
                info_str = "{act}: {lvl}: {resp}".format(
                    act=TRANSLATIONS['calibration']['title'],
                    lvl=write_cmd,
                    resp=msg)
                if status == 'success':
                    flash(info_str, 'success')
                else:
                    flash(info_str, 'error')
            else:
                flash("Error initializing pump class", 'error')

    elif form_ezo_pump_calibrate.start_calibration.data:
        ui_stage = 'question_ml_dispensed'
        selected_output = Output.query.filter(
            Output.unique_id == form_ezo_pump_calibrate.selected_output_id.data).first()
        if not selected_output:
            flash('Output not found: {}'.format(
                form_ezo_pump_calibrate.selected_output_id.data), 'error')
        else:
            output_device_name = selected_output.name
            atlas_command = connect_atlas_ezo_pump(selected_output)
            if atlas_command:
                if (form_ezo_pump_calibrate.ml_to_dispense.data and
                        form_ezo_pump_calibrate.ml_to_dispense.data > 0):
                    write_cmd = 'D,{}'.format(
                        form_ezo_pump_calibrate.ml_to_dispense.data)
                    logger.error("EZO-PMP command: {}".format(write_cmd))
                    status, msg = atlas_command.query(write_cmd)
                    info_str = "{act}: {lvl}: {resp}".format(
                        act=TRANSLATIONS['calibration']['title'],
                        lvl=write_cmd,
                        resp=msg)
                    if status == 'success':
                        flash(info_str, 'success')
                    else:
                        flash(info_str, 'error')
                else:
                    flash("Invalid amount to dispense: '{}'".format(
                        form_ezo_pump_calibrate.ml_to_dispense.data), 'error')
            else:
                flash("Error initializing pump class", 'error')

    elif backend_stage == 'question_ml_dispensed':
        ui_stage = 'complete'
        output_device_name = selected_output.name
        atlas_command = connect_atlas_ezo_pump(selected_output)
        if atlas_command:
            if (form_ezo_pump_calibrate.ml_dispensed.data and
                    form_ezo_pump_calibrate.ml_dispensed.data > 0):
                write_cmd = 'Cal,{}'.format(
                    form_ezo_pump_calibrate.ml_dispensed.data)
                logger.error("EZO-PMP command: {}".format(write_cmd))
                status, msg = atlas_command.query(write_cmd)
                info_str = "{act}: {lvl}: {resp}".format(
                    act=TRANSLATIONS['calibration']['title'],
                    lvl=write_cmd,
                    resp=msg)
                if status == 'success':
                    flash(info_str, 'success')
                else:
                    flash(info_str, 'error')
            else:
                flash("Invalid amount dispensed: '{}'".format(
                    form_ezo_pump_calibrate.ml_dispensed.data), 'error')
        else:
            flash("Error initializing pump class", 'error')

    return render_template('tools/calibration_options/atlas_ezo_pump.html',
                           complete_with_error=complete_with_error,
                           form_ezo_pump_calibrate=form_ezo_pump_calibrate,
                           output=output,
                           output_device_name=output_device_name,
                           selected_output=selected_output,
                           ui_stage=ui_stage)


@blueprint.route('/setup_atlas_ec', methods=('GET', 'POST'))
@flask_login.login_required
def setup_atlas_ec():
    """
    Step-by-step tool for calibrating the Atlas Scientific pH sensor
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))

    form_ec_calibrate = forms_calibration.CalibrationAtlasEC()

    input_dev = Input.query.filter(Input.device == 'ATLAS_EC').all()

    ui_stage = 'start'
    backend_stage = None
    next_stage = None
    selected_input = None
    selected_point_calibration = None
    input_device_name = None
    complete_with_error = None

    if form_ec_calibrate.hidden_current_stage.data:
        backend_stage = form_ec_calibrate.hidden_current_stage.data

    if form_ec_calibrate.hidden_selected_point_calibration.data:
        selected_point_calibration = form_ec_calibrate.hidden_selected_point_calibration.data
    elif form_ec_calibrate.point_calibration.data:
        selected_point_calibration = form_ec_calibrate.point_calibration.data

    if selected_point_calibration:
        list_point_calibrations = selected_point_calibration.split(',')
    else:
        list_point_calibrations = []

    if form_ec_calibrate.point_low_uS.data:
        point_low_uS = form_ec_calibrate.point_low_uS.data
    else:
        point_low_uS = form_ec_calibrate.hidden_point_low_uS.data

    if form_ec_calibrate.point_high_uS.data:
        point_high_uS = form_ec_calibrate.point_high_uS.data
    else:
        point_high_uS = form_ec_calibrate.hidden_point_high_uS.data

    # Begin calibration from Selected input
    if form_ec_calibrate.start_calibration.data:
        ui_stage = 'point_enter_uS'
        selected_input = Input.query.filter_by(
            unique_id=form_ec_calibrate.selected_input_id.data).first()
        dict_inputs = parse_input_information()
        list_inputs_sorted = generate_form_input_list(dict_inputs)
        if not selected_input:
            flash('Input not found: {}'.format(
                form_ec_calibrate.selected_input_id.data), 'error')
        else:
            for each_input in list_inputs_sorted:
                if selected_input.device == each_input[0]:
                    input_device_name = each_input[1]

    # Continue calibration from selected input
    elif (form_ec_calibrate.go_to_next_stage.data or
          form_ec_calibrate.go_to_last_stage.data or
          (backend_stage is not None and backend_stage not in ['start', 'point_enter_uS'])):
        selected_input = Input.query.filter_by(
            unique_id=form_ec_calibrate.hidden_input_id.data).first()
        dict_inputs = parse_input_information()
        list_inputs_sorted = generate_form_input_list(dict_inputs)
        for each_input in list_inputs_sorted:
            if selected_input.device == each_input[0]:
                input_device_name = each_input[1]

    if backend_stage in ['point_enter_uS', 'dry', 'low', 'high']:
        time.sleep(2)  # Sleep makes querying sensor more stable

        # Determine next ui_stage
        if backend_stage == 'point_enter_uS':
            next_stage = 'dry'
            logger.error("next_stage: {}".format(next_stage))
        elif backend_stage == 'dry':
            next_stage = list_point_calibrations[0]
            logger.error("next_stage: {}".format(next_stage))
        else:
            current_stage_index = list_point_calibrations.index(backend_stage)
            if current_stage_index == len(list_point_calibrations) - 1:
                next_stage = 'complete'
            else:
                next_stage = list_point_calibrations[current_stage_index + 1]

    if backend_stage == 'point_enter_uS':
        ui_stage = next_stage
        complete_with_error = None
    elif backend_stage == 'dry':
        ui_stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'ec_dry', None, 'continuous',
            current_stage='dry', next_stage=next_stage)
    elif backend_stage == 'low':
        ui_stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'ec_low', point_low_uS, 'continuous',
            current_stage='low', next_stage=next_stage)
    elif backend_stage == 'high':
        ui_stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'ec_high', point_high_uS, 'end',
            current_stage='high', next_stage=next_stage)

    return render_template('tools/calibration_options/atlas_ec.html',
                           complete_with_error=complete_with_error,
                           form_ec_calibrate=form_ec_calibrate,
                           input=input_dev,
                           input_device_name=input_device_name,
                           point_high_uS=point_high_uS,
                           point_low_uS=point_low_uS,
                           selected_input=selected_input,
                           selected_point_calibration=selected_point_calibration,
                           ui_stage=ui_stage)


@blueprint.route('/setup_atlas_ec_measure/<input_id>')
@flask_login.login_required
def setup_atlas_ec_measure(input_id):
    """
    Acquire a measurement from the Atlas Scientific pH input and return it
    Used during calibration to display the current pH to the user
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_page.page_atlas_ec_calibrate'))

    selected_input = Input.query.filter_by(unique_id=input_id).first()

    ec = None
    error = None

    if selected_input.interface == 'FTDI':
        ec_input_ftdi = AtlasScientificFTDI(selected_input.ftdi_location)
        lines = ec_input_ftdi.query('R')
        logger.debug("All Lines: {lines}".format(lines=lines))

        if 'check probe' in lines:
            error = '"check probe" returned from input'
        elif not lines:
            error = 'Nothing returned from input'
        elif str_is_float(lines[0]):
            ec = lines[0]
            logger.debug('Value[0] is float: {val}'.format(val=ec))
        else:
            error = 'Value[0] is not float or "check probe": {val}'.format(
                val=lines[0])

    elif selected_input.interface == 'UART':
        ec_input_uart = AtlasScientificUART(
            selected_input.uart_location, baudrate=selected_input.baud_rate)
        lines = ec_input_uart.query('R')
        logger.debug("All Lines: {lines}".format(lines=lines))

        if 'check probe' in lines:
            error = '"check probe" returned from input'
        elif not lines:
            error = 'Nothing returned from input'
        elif str_is_float(lines[0]):
            ec = lines[0]
            logger.debug('Value[0] is float: {val}'.format(val=ec))
        else:
            error = 'Value[0] is not float or "check probe": {val}'.format(
                val=lines[0])

    elif selected_input.interface == 'I2C':
        ec_input_i2c = AtlasScientificI2C(
            i2c_address=int(str(selected_input.i2c_location), 16),
            i2c_bus=selected_input.i2c_bus)
        ec_status, ec_str = ec_input_i2c.query('R')
        if ec_status == 'error':
            error = "Input read unsuccessful: {err}".format(err=ec_str)
        elif ec_status == 'success':
            ec = ec_str

    if error:
        logger.error(error)
        return error, 204
    else:
        return ec


@blueprint.route('/setup_atlas_ph', methods=('GET', 'POST'))
@flask_login.login_required
def setup_atlas_ph():
    """
    Step-by-step tool for calibrating the Atlas Scientific pH sensor
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))

    form_ph_calibrate = forms_calibration.CalibrationAtlasph()

    input_dev = Input.query.filter(Input.device == 'ATLAS_PH').all()

    ui_stage = 'start'
    backend_stage = None
    next_stage = None
    selected_input = None
    selected_point_calibration = None
    input_device_name = None
    complete_with_error = None

    if form_ph_calibrate.hidden_current_stage.data:
        backend_stage = form_ph_calibrate.hidden_current_stage.data

    if form_ph_calibrate.hidden_selected_point_calibration.data:
        selected_point_calibration = form_ph_calibrate.hidden_selected_point_calibration.data
    elif form_ph_calibrate.point_calibration.data:
        selected_point_calibration = form_ph_calibrate.point_calibration.data

    if selected_point_calibration:
        list_point_calibrations = selected_point_calibration.split(',')
    else:
        list_point_calibrations = []

    # Clear Calibration memory
    if form_ph_calibrate.clear_calibration.data:
        selected_input = Input.query.filter_by(
            unique_id=form_ph_calibrate.selected_input_id.data).first()
        atlas_command = AtlasScientificCommand(selected_input)
        status, message = atlas_command.calibrate('clear_calibration')

        sensor_measurement = atlas_command.get_sensor_measurement()

        if isinstance(message, tuple):
            message_status = message[0]
            message_info = message[1]
            message = "Calibration command returned from sensor: {}".format(
                message_status)
            if message_info:
                message += ": {}".format(message_info)
        else:
            message = "Calibration command returned from sensor: {}".format(
                message)

        if sensor_measurement != 'NA':
            message = "{} {}".format(sensor_measurement, message)

        if status:
            flash(message, "error")
        else:
            flash(message, "success")

    # Begin calibration from Selected input
    elif form_ph_calibrate.start_calibration.data:
        ui_stage = 'temperature'
        selected_input = Input.query.filter_by(
            unique_id=form_ph_calibrate.selected_input_id.data).first()
        dict_inputs = parse_input_information()
        list_inputs_sorted = generate_form_input_list(dict_inputs)
        if not selected_input:
            flash('Input not found: {}'.format(
                form_ph_calibrate.selected_input_id.data), 'error')
        else:
            for each_input in list_inputs_sorted:
                if selected_input.device == each_input[0]:
                    input_device_name = each_input[1]

    # Continue calibration from selected input
    elif (form_ph_calibrate.go_to_next_stage.data or
            form_ph_calibrate.go_to_last_stage.data or
            (backend_stage is not None and backend_stage not in ['start', 'temperature'])):
        selected_input = Input.query.filter_by(
            unique_id=form_ph_calibrate.hidden_input_id.data).first()
        dict_inputs = parse_input_information()
        list_inputs_sorted = generate_form_input_list(dict_inputs)
        for each_input in list_inputs_sorted:
            if selected_input.device == each_input[0]:
                input_device_name = each_input[1]

    if backend_stage in ['temperature', 'low', 'mid', 'high']:
        time.sleep(2)  # Sleep makes querying sensor more stable

        # Determine next ui_stage
        if backend_stage == 'temperature':
            next_stage = list_point_calibrations[0]
            logger.error("next_stage: {}".format(next_stage))
        else:
            current_stage_index = list_point_calibrations.index(backend_stage)
            if current_stage_index == len(list_point_calibrations) - 1:
                next_stage = 'complete'
            else:
                next_stage = list_point_calibrations[current_stage_index + 1]

    if form_ph_calibrate.clear_calibration.data:
        pass
    elif backend_stage == 'temperature':
        if form_ph_calibrate.temperature.data is None:
            flash(gettext(
                "A valid temperature is required: %(temp)s is invalid.",
                temp=form_ph_calibrate.temperature.data), "error")
            ui_stage = 'start'
        else:
            temp = '{temp:.2f}'.format(
                temp=float(form_ph_calibrate.temperature.data))
            ui_stage, complete_with_error = dual_commands_to_sensor(
                selected_input, 'temperature', temp, 'continuous',
                current_stage='temperature', next_stage=next_stage)
    elif backend_stage == 'low':
        ui_stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'low', '4.0', 'continuous',
            current_stage='low', next_stage=next_stage)
    elif backend_stage == 'mid':
        ui_stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'mid', '7.0', 'continuous',
            current_stage='mid', next_stage=next_stage)
    elif backend_stage == 'high':
        ui_stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'high', '10.0', 'end',
            current_stage='high', next_stage=next_stage)

    return render_template('tools/calibration_options/atlas_ph.html',
                           complete_with_error=complete_with_error,
                           form_ph_calibrate=form_ph_calibrate,
                           input=input_dev,
                           input_device_name=input_device_name,
                           selected_input=selected_input,
                           selected_point_calibration=selected_point_calibration,
                           ui_stage=ui_stage)


@blueprint.route('/setup_atlas_ph_measure/<input_id>')
@flask_login.login_required
def setup_atlas_ph_measure(input_id):
    """
    Acquire a measurement from the Atlas Scientific pH input and return it
    Used during calibration to display the current pH to the user
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_page.page_atlas_ph_calibrate'))

    selected_input = Input.query.filter_by(unique_id=input_id).first()

    ph = None
    error = None

    if selected_input.interface == 'FTDI':
        ph_input_ftdi = AtlasScientificFTDI(selected_input.ftdi_location)
        lines = ph_input_ftdi.query('R')
        logger.debug("All Lines: {lines}".format(lines=lines))

        if 'check probe' in lines:
            error = '"check probe" returned from input'
        elif not lines:
            error = 'Nothing returned from input'
        elif str_is_float(lines[0]):
            ph = lines[0]
            logger.debug('Value[0] is float: {val}'.format(val=ph))
        else:
            error = 'Value[0] is not float or "check probe": {val}'.format(
                val=lines[0])

    elif selected_input.interface == 'UART':
        ph_input_uart = AtlasScientificUART(
            selected_input.uart_location, baudrate=selected_input.baud_rate)
        lines = ph_input_uart.query('R')
        logger.debug("All Lines: {lines}".format(lines=lines))

        if 'check probe' in lines:
            error = '"check probe" returned from input'
        elif not lines:
            error = 'Nothing returned from input'
        elif str_is_float(lines[0]):
            ph = lines[0]
            logger.debug('Value[0] is float: {val}'.format(val=ph))
        else:
            error = 'Value[0] is not float or "check probe": {val}'.format(
                val=lines[0])

    elif selected_input.interface == 'I2C':
        ph_input_i2c = AtlasScientificI2C(
            i2c_address=int(str(selected_input.i2c_location), 16),
            i2c_bus=selected_input.i2c_bus)
        ph_status, ph_str = ph_input_i2c.query('R')
        if ph_status == 'error':
            error = "Input read unsuccessful: {err}".format(err=ph_str)
        elif ph_status == 'success':
            ph = ph_str

    if error:
        logger.error(error)
        return error, 204
    else:
        return ph


def dual_commands_to_sensor(input_sel, first_cmd, amount,
                            second_cmd, current_stage, next_stage=None):
    """
    Handles the Atlas Scientific pH sensor calibration:
    Sends two consecutive commands to the sensor board
    Denies advancement to the next stage if any commands fail
    Permits advancement to the next stage if all commands succeed
    Prints any errors or successes
    """
    return_error = None
    set_amount = None

    if first_cmd == 'temperature':
        unit = '°C'
        set_amount = amount
    elif first_cmd in ['ec_dry', 'ec_low', 'ec_high']:
        unit = 'μS'
        set_amount = amount
    else:
        unit = 'pH'

    atlas_command = AtlasScientificCommand(input_sel)

    sensor_measurement = atlas_command.get_sensor_measurement()

    first_status, first_return_str = atlas_command.calibrate(
        first_cmd, set_amount=set_amount)

    if isinstance(first_return_str, tuple):
        message_status = first_return_str[0]
        message_info = first_return_str[1]
        first_return_message = "{}".format(message_status)
        if message_info:
            first_return_message += ": {}".format(message_info)
    else:
        first_return_message = first_return_str

    first_info_str = "{act}: {lvl} ({amt} {unit}): {resp}".format(
        act=TRANSLATIONS['calibration']['title'],
        lvl=first_cmd,
        amt=amount,
        unit=unit,
        resp=first_return_message)

    if sensor_measurement != 'NA':
        first_info_str = "{} {}".format(
            sensor_measurement, first_info_str)

    if first_status:
        flash(first_info_str, "error")
        return_error = first_return_str
        return_stage = current_stage
    else:
        flash(first_info_str, "success")
        time.sleep(0.1)  # Add space between commands
        second_status, second_return_str = atlas_command.calibrate(second_cmd)

        if isinstance(second_return_str, tuple):
            message_status = second_return_str[0]
            message_info = second_return_str[1]
            second_return_message = "{}".format(message_status)
            if message_info:
                second_return_message += ": {}".format(message_info)
        else:
            second_return_message = second_return_str

        second_info_str = "{act}: {cmd}: {resp}".format(
            act=gettext('Command'),
            cmd=second_cmd,
            resp=second_return_message)

        if sensor_measurement != 'NA':
            second_info_str = "{} {}".format(
                sensor_measurement, second_info_str)

        if second_status:
            flash(second_info_str, "error")
            return_error = second_return_str
            return_stage = current_stage
        else:
            flash(second_info_str, "success")
            # Advance to the next stage
            return_stage = next_stage

    return return_stage, return_error


@blueprint.route('/setup_ds_resolution', methods=('GET', 'POST'))
@flask_login.login_required
def setup_ds_resolution():
    """
    Set DS Sensor resolution
    """
    form_ds = forms_calibration.SetupDS18B20()

    inputs = Input.query.all()

    # Check if w1thermsensor library is installed
    if not current_app.config['TESTING']:
        dep_unmet, _ = return_dependencies('CALIBRATE_DS_TYPE')
        if dep_unmet:
            list_unmet_deps = []
            for each_dep in dep_unmet:
                list_unmet_deps.append(each_dep[0])
            flash("The device you're trying to calibrate has unmet "
                  "dependencies: {dep}".format(
                    dep=', '.join(list_unmet_deps)), 'error')
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device='CALIBRATE_DS_TYPE'))

    # If DS inputs exist, compile a list of detected inputs
    ds_inputs = []
    try:
        if os.path.isdir(PATH_1WIRE):
            for each_name in os.listdir(PATH_1WIRE):
                if 'bus' not in each_name:
                    input_dev = Input.query.filter(
                        Input.location == each_name).first()
                    if input_dev:
                        ds_inputs.append((input_dev.device, each_name))
    except OSError:
        flash("Unable to detect 1-wire devices in '/sys/bus/w1/devices'. "
              "Make 1-wire support is enabled with 'sudo raspi-config'.",
              "error")

    if (not current_app.config['TESTING'] and
            form_ds.set_resolution.data and
            form_ds.device_id.data):
        try:
            from w1thermsensor import W1ThermSensor
            device_name = form_ds.device_id.data.split(',')[0]
            device_id = form_ds.device_id.data.split(',')[1]
            input_type = None
            if device_name == 'DS18B20':
                input_type = W1ThermSensor.THERM_SENSOR_DS18B20
            if device_name == 'DS18S20':
                input_type = W1ThermSensor.THERM_SENSOR_DS18S20
            if device_name == 'DS1822':
                input_type = W1ThermSensor.THERM_SENSOR_DS1822
            if device_name == 'DS28EA00':
                input_type = W1ThermSensor.THERM_SENSOR_DS28EA00
            if device_name == 'DS1825':
                input_type = W1ThermSensor.THERM_SENSOR_DS1825
            if device_name == 'MAX31850K':
                input_type = W1ThermSensor.THERM_SENSOR_MAX31850K
            else:
                flash("Unknown input type: {}".format(device_name),
                      "error")

            if input_type:
                sensor = W1ThermSensor(
                    sensor_type=input_type, sensor_id=device_id)
                sensor.set_resolution(
                    form_ds.set_resolution.data, persist=True)
            flash("Successfully set sensor {id} resolution to "
                  "{bit}-bit".format(id=form_ds.device_id.data,
                                     bit=form_ds.set_resolution.data),
                  "success")
        except Exception as msg:
            flash("Error while setting resolution of sensor with ID {id}: "
                  "{err}".format(id=form_ds.device_id.data, err=msg), "error")

    return render_template('tools/calibration_options/ds_resolution.html',
                           ds_inputs=ds_inputs,
                           form_ds=form_ds,
                           inputs=inputs)
