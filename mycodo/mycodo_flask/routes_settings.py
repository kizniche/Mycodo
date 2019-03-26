# coding=utf-8
""" collection of Page endpoints """
import logging

import flask_login
import operator
import os
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.blueprints import Blueprint

from mycodo.config import CAMERA_LIBRARIES
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import LANGUAGES
from mycodo.config import THEMES
from mycodo.databases.models import Camera
from mycodo.databases.models import Conversion
from mycodo.databases.models import Measurement
from mycodo.databases.models import Misc
from mycodo.databases.models import Output
from mycodo.databases.models import Role
from mycodo.databases.models import SMTP
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.mycodo_flask.forms import forms_settings
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_settings
from mycodo.utils.inputs import load_module_from_file
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import cmd_output

logger = logging.getLogger('mycodo.mycodo_flask.settings')

blueprint = Blueprint('routes_settings',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.route('/settings/alerts', methods=('GET', 'POST'))
@flask_login.login_required
def settings_alerts():
    """ Display alert settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    smtp = SMTP.query.first()
    form_email_alert = forms_settings.SettingsEmail()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        form_name = request.form['form-name']
        if form_name == 'EmailAlert':
            utils_settings.settings_alert_mod(form_email_alert)
        return redirect(url_for('routes_settings.settings_alerts'))

    return render_template('settings/alerts.html',
                           smtp=smtp,
                           form_email_alert=form_email_alert)


@blueprint.route('/settings/camera', methods=('GET', 'POST'))
@flask_login.login_required
def settings_camera():
    """ Display camera settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_camera = forms_settings.SettingsCamera()

    camera = Camera.query.all()
    output = Output.query.all()

    pi_camera_enabled = False
    try:
        if 'start_x=1' in open('/boot/config.txt').read():
            pi_camera_enabled = True
    except IOError as e:
        logger.error("Camera IOError raised in '/settings/camera' endpoint: "
                     "{err}".format(err=e))

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        if form_camera.camera_add.data:
            utils_settings.camera_add(form_camera)
        elif form_camera.camera_mod.data:
            utils_settings.camera_mod(form_camera)
        elif form_camera.camera_del.data:
            utils_settings.camera_del(form_camera)
        return redirect(url_for('routes_settings.settings_camera'))

    return render_template('settings/camera.html',
                           camera=camera,
                           camera_libraries=CAMERA_LIBRARIES,
                           form_camera=form_camera,
                           pi_camera_enabled=pi_camera_enabled,
                           output=output)


@blueprint.route('/settings/general', methods=('GET', 'POST'))
@flask_login.login_required
def settings_general():
    """ Display general settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    misc = Misc.query.first()
    form_settings_general = forms_settings.SettingsGeneral()

    languages_sorted = sorted(LANGUAGES.items(), key=operator.itemgetter(1))

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        form_name = request.form['form-name']
        if form_name == 'General':
            utils_settings.settings_general_mod(form_settings_general)
        return redirect(url_for('routes_settings.settings_general'))

    return render_template('settings/general.html',
                           misc=misc,
                           languages=languages_sorted,
                           form_settings_general=form_settings_general)


@blueprint.route('/settings/input', methods=('GET', 'POST'))
@flask_login.login_required
def settings_input():
    """ Display measurement settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_input = forms_settings.Input()
    form_input_delete = forms_settings.InputDel()

    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    # Get list of custom inputs
    excluded_files = ['__init__.py', '__pycache__']
    install_dir = os.path.abspath(INSTALL_DIRECTORY)
    path_custom_inputs = os.path.join(install_dir, 'mycodo/inputs/custom_inputs')

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_input.import_input_upload.data:
            utils_settings.settings_input_import(form_input)
        elif form_input_delete.delete_input.data:
            utils_settings.settings_input_delete(form_input_delete)

        return redirect(url_for('routes_settings.settings_input'))

    dict_inputs = {}

    for each_file in os.listdir(path_custom_inputs):
        if each_file not in excluded_files:
            try:
                full_path_file = os.path.join(path_custom_inputs, each_file)
                input_info = load_module_from_file(full_path_file)
                dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']] = {}
                dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']]['input_name'] = \
                    input_info.INPUT_INFORMATION['input_name']
                dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']]['input_manufacturer'] = \
                    input_info.INPUT_INFORMATION['input_manufacturer']
                dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']]['measurements_name'] = \
                    input_info.INPUT_INFORMATION['measurements_name']
            except:
                pass

    # dict_inputs = parse_input_information()

    return render_template('settings/input.html',
                           dict_inputs=dict_inputs,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           form_input=form_input,
                           form_input_delete=form_input_delete)


@blueprint.route('/settings/measurement', methods=('GET', 'POST'))
@flask_login.login_required
def settings_measurement():
    """ Display measurement settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    measurement = Measurement.query.all()
    unit = Unit.query.all()
    conversion = Conversion.query.all()
    form_add_measurement = forms_settings.MeasurementAdd()
    form_mod_measurement = forms_settings.MeasurementMod()
    form_add_unit = forms_settings.UnitAdd()
    form_mod_unit = forms_settings.UnitMod()
    form_add_conversion = forms_settings.ConversionAdd()
    form_mod_conversion = forms_settings.ConversionMod()

    choices_units = utils_general.choices_units(unit)

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(measurement)
    dict_units = add_custom_units(unit)

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_add_measurement.add_measurement.data:
            utils_settings.settings_measurement_add(form_add_measurement)
        elif form_mod_measurement.save_measurement.data:
            utils_settings.settings_measurement_mod(form_mod_measurement)
        elif form_mod_measurement.delete_measurement.data:
            utils_settings.settings_measurement_del(form_mod_measurement.measurement_id.data)

        elif form_add_unit.add_unit.data:
            utils_settings.settings_unit_add(form_add_unit)
        elif form_mod_unit.save_unit.data:
            utils_settings.settings_unit_mod(form_mod_unit)
        elif form_mod_unit.delete_unit.data:
            utils_settings.settings_unit_del(form_mod_unit.unit_id.data)

        elif form_add_conversion.add_conversion.data:
            utils_settings.settings_convert_add(form_add_conversion)
        elif form_mod_conversion.save_conversion.data:
            utils_settings.settings_convert_mod(form_mod_conversion)
        elif form_mod_conversion.delete_conversion.data:
            utils_settings.settings_convert_del(form_mod_conversion.conversion_id.data)

        return redirect(url_for('routes_settings.settings_measurement'))

    return render_template('settings/measurement.html',
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           choices_units=choices_units,
                           measurement=measurement,
                           unit=unit,
                           conversion=conversion,
                           form_add_measurement=form_add_measurement,
                           form_mod_measurement=form_mod_measurement,
                           form_add_unit=form_add_unit,
                           form_mod_unit=form_mod_unit,
                           form_add_conversion=form_add_conversion,
                           form_mod_conversion=form_mod_conversion)


@blueprint.route('/settings/users', methods=('GET', 'POST'))
@flask_login.login_required
def settings_users():
    """ Display user settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    users = User.query.all()
    user_roles = Role.query.all()
    form_add_user = forms_settings.UserAdd()
    form_mod_user = forms_settings.UserMod()
    form_user_roles = forms_settings.UserRoles()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_users'):
            return redirect(url_for('routes_general.home'))

        if form_add_user.add_user.data:
            utils_settings.user_add(form_add_user)
        elif form_mod_user.delete.data:
            if utils_settings.user_del(form_mod_user) == 'logout':
                return redirect('/logout')
        elif form_mod_user.save.data:
            if utils_settings.user_mod(form_mod_user) == 'logout':
                return redirect('/logout')
        elif (form_user_roles.add_role.data or
                form_user_roles.save_role.data or
                form_user_roles.delete_role.data):
            utils_settings.user_roles(form_user_roles)
        return redirect(url_for('routes_settings.settings_users'))

    return render_template('settings/users.html',
                           themes=THEMES,
                           users=users,
                           user_roles=user_roles,
                           form_add_user=form_add_user,
                           form_mod_user=form_mod_user,
                           form_user_roles=form_user_roles)


@blueprint.route('/settings/pi', methods=('GET', 'POST'))
@flask_login.login_required
def settings_pi():
    """ Display general settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    misc = Misc.query.first()
    form_settings_pi = forms_settings.SettingsPi()

    pi_settings = get_raspi_config_settings()

    # Determine what state pigpiod is currently in
    pigpiod_sample_rate = ''
    if os.path.exists('/etc/systemd/system/pigpiod_uninstalled.service'):
        pigpiod_sample_rate = 'uninstalled'
    elif os.path.exists('/etc/systemd/system/pigpiod_disabled.service'):
        pigpiod_sample_rate = 'disabled'
    elif os.path.exists('/etc/systemd/system/pigpiod_low.service'):
        pigpiod_sample_rate = 'low'
    elif os.path.exists('/etc/systemd/system/pigpiod_high.service'):
        pigpiod_sample_rate = 'high'
    elif os.path.exists('/etc/systemd/system/pigpiod.service'):
        pigpiod_sample_rate = 'low'

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        form_name = request.form['form-name']
        if form_name == 'Pi':
            utils_settings.settings_pi_mod(form_settings_pi)
        return redirect(url_for('routes_settings.settings_pi'))

    return render_template('settings/pi.html',
                           misc=misc,
                           pi_settings=pi_settings,
                           pigpiod_sample_rate=pigpiod_sample_rate,
                           form_settings_pi=form_settings_pi)


@blueprint.route('/settings/diagnostic', methods=('GET', 'POST'))
@flask_login.login_required
def settings_diagnostic():
    """ Display general settings """
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_settings_diagnostic = forms_settings.SettingsDiagnostic()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_general.home'))

        if form_settings_diagnostic.delete_dashboard_elements.data:
            utils_settings.settings_diagnostic_delete_dashboard_elements()
        elif form_settings_diagnostic.delete_inputs.data:
            utils_settings.settings_diagnostic_delete_inputs()
        elif form_settings_diagnostic.delete_maths.data:
            utils_settings.settings_diagnostic_delete_maths()
        elif form_settings_diagnostic.delete_notes_tags.data:
            utils_settings.settings_diagnostic_delete_notes_tags()
        elif form_settings_diagnostic.delete_outputs.data:
            utils_settings.settings_diagnostic_delete_outputs()
        elif form_settings_diagnostic.delete_settings_database.data:
            utils_settings.settings_diagnostic_delete_settings_database()
        elif form_settings_diagnostic.delete_file_dependency.data:
            utils_settings.settings_diagnostic_delete_file('dependency')
        elif form_settings_diagnostic.delete_file_upgrade.data:
            utils_settings.settings_diagnostic_delete_file('upgrade')
        elif form_settings_diagnostic.reset_email_counter.data:
            utils_settings.settings_diagnostic_reset_email_counter()

        return redirect(url_for('routes_settings.settings_diagnostic'))

    return render_template('settings/diagnostic.html',
                           form_settings_diagnostic=form_settings_diagnostic)


def get_raspi_config_settings():
    settings = {}
    i2c_status, _, _ = cmd_output("raspi-config nonint get_i2c")
    settings['i2c_enabled'] = not bool(int(i2c_status))
    ssh_status, _, _ = cmd_output("raspi-config nonint get_ssh")
    settings['ssh_enabled'] = not bool(int(ssh_status))
    cam_status, _, _ = cmd_output("raspi-config nonint get_camera")
    settings['pi_camera_enabled'] = not bool(int(cam_status))
    one_wire_status, _, _ = cmd_output("raspi-config nonint get_onewire")
    settings['one_wire_enabled'] = not bool(int(one_wire_status))
    serial_status, _, _ = cmd_output("raspi-config nonint get_serial")
    settings['serial_enabled'] = not bool(int(serial_status))
    spi_status, _, _ = cmd_output("raspi-config nonint get_spi")
    settings['spi_enabled'] = not bool(int(spi_status))
    hostname_out, _, _ = cmd_output("raspi-config nonint get_hostname")
    settings['hostname'] = hostname_out.decode("utf-8")
    return settings
