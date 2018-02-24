# coding=utf-8
""" collection of Page endpoints """
import logging

import flask_login
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
from flask.blueprints import Blueprint
from flask_babel import gettext
from sqlalchemy import or_

from mycodo.config import DEVICES
from mycodo.databases.models import Input
from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
from mycodo.mycodo_flask.forms import forms_calibration
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.calibration import AtlasScientificCommand
from mycodo.utils.system_pi import str_is_float

logger = logging.getLogger('mycodo.mycodo_flask.calibration')

blueprint = Blueprint('routes_calibration',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
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


@blueprint.route('/calibration_atlas_ph', methods=('GET', 'POST'))
@flask_login.login_required
def calibration_atlas_ph():
    """
    Step-by-step tool for calibrating the Atlas Scientific pH sensor
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))

    form_ph_calibrate = forms_calibration.CalibrationAtlasph()

    input_dev = Input.query.filter(
        or_(Input.device == 'ATLAS_PH_UART',
            Input.device == 'ATLAS_PH_I2C')).all()
    stage = 0
    next_stage = None
    selected_input = None
    input_device_name = None
    complete_with_error = None

    if form_ph_calibrate.hidden_next_stage.data is not None:
        next_stage = int(form_ph_calibrate.hidden_next_stage.data)

    # Clear Calibration memory
    if form_ph_calibrate.clear_calibration.data:
        selected_input = Input.query.filter_by(
            unique_id=form_ph_calibrate.selected_sensor_id.data).first()
        atlas_command = AtlasScientificCommand(selected_input)
        status, message = atlas_command.calibrate('clear_calibration')
        if status:
            flash(message, "error")
        else:
            flash(message, "success")

    # Begin calibration from Selected input
    elif form_ph_calibrate.go_from_first_stage.data:
        stage = 1
        selected_input = Input.query.filter_by(
            unique_id=form_ph_calibrate.selected_sensor_id.data).first()
        if not selected_input:
            flash('Input not found: {}'.format(
                form_ph_calibrate.selected_sensor_id.data), 'error')
        else:
            for each_input in DEVICES:
                if selected_input.device == each_input[0]:
                    input_device_name = each_input[1]

    # Continue calibration from selected input
    elif (form_ph_calibrate.go_to_next_stage.data or
            form_ph_calibrate.go_to_last_stage.data or
            (next_stage is not None and next_stage > 1)):
        selected_input = Input.query.filter_by(
            unique_id=form_ph_calibrate.hidden_sensor_id.data).first()
        for each_input in DEVICES:
            if selected_input.device == each_input[0]:
                input_device_name = each_input[1]

    if next_stage == 2:
        if form_ph_calibrate.temperature.data is None:
            flash(gettext("A valid temperature is required: %(temp)s is invalid.",
                          temp=form_ph_calibrate.temperature.data), "error")
            stage = 1
        else:
            temp = '{temp:.2f}'.format(
                temp=form_ph_calibrate.temperature.data)
            stage, complete_with_error = dual_commands_to_sensor(
                selected_input, 'temperature', temp, 'continuous', 1)
    elif next_stage == 3:
        stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'mid', '7.0', 'continuous', 2)
    elif next_stage == 4:
        stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'low', '4.0', 'continuous', 3)
    elif next_stage == 5:
        stage, complete_with_error = dual_commands_to_sensor(
            selected_input, 'high', '10.0', 'end', 4)

    return render_template('tools/calibration_atlas_ph.html',
                           complete_with_error=complete_with_error,
                           form_ph_calibrate=form_ph_calibrate,
                           sensor=input_dev,
                           sensor_device_name=input_device_name,
                           selected_sensor=selected_input,
                           stage=stage)


@blueprint.route('/calibration_atlas_ph_measure/<input_id>')
@flask_login.login_required
def calibration_atlas_ph_measure(input_id):
    """
    Acquire a measurement from the Atlas Scientific pH input and return it
    Used during calibration to display the current pH to the user
    """
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_page.page_atlas_ph_calibrate'))

    selected_input = Input.query.filter_by(unique_id=input_id).first()

    ph = None
    error = None

    if selected_input.interface == 'UART':
        ph_input_uart = AtlasScientificUART(
            selected_input.device_loc, baudrate=selected_input.baud_rate)
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
            i2c_address=selected_input.i2c_address,
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
                            second_cmd, current_stage):
    """
    Handles the Atlas Scientific pH sensor calibration:
    Sends two consecutive commands to the sensor board
    Denies advancement to the next stage if any commands fail
    Permits advancement to the next stage if all commands succeed
    Prints any errors or successes
    """
    return_error = None
    set_temp = None

    if first_cmd == 'temperature':
        unit = 'C'
        set_temp = amount
    else:
        unit = 'pH'

    atlas_command = AtlasScientificCommand(input_sel)

    first_status, first_return_str = atlas_command.calibrate(first_cmd, temperature=set_temp)
    info_str = "{act}: {lvl} ({amt} {unit}): {resp}".format(
        act=gettext('Calibration'), lvl=first_cmd, amt=amount, unit=unit, resp=first_return_str)

    if first_status:
        flash(info_str, "error")
        return_error = first_return_str
        return_stage = current_stage
    else:
        flash(info_str, "success")
        second_status, second_return_str = atlas_command.calibrate(second_cmd)
        second_info_str = "{act}: {cmd}: {resp}".format(
            act=gettext('Command'), cmd=second_cmd, resp=second_return_str)
        if second_status:
            flash(second_info_str, "error")
            return_error = second_return_str
            return_stage = current_stage
        else:
            flash(second_info_str, "success")
            # Advance to the next stage
            return_stage = current_stage + 1

    return return_stage, return_error
