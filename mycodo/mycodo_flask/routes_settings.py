# coding=utf-8
"""collection of Page endpoints."""
import logging
import os
import flask_login
import threading
from io import BytesIO
from flask import flash, jsonify, send_file, redirect, render_template, request, url_for
from flask.blueprints import Blueprint

from mycodo.config import (PATH_ACTIONS_CUSTOM, PATH_FUNCTIONS_CUSTOM,
                           PATH_INPUTS_CUSTOM, PATH_OUTPUTS_CUSTOM,
                           PATH_WIDGETS_CUSTOM, THEMES, USAGE_REPORTS_PATH)
from mycodo.databases.models import (SMTP, Conversion, Measurement, Misc, Role,
                                     Unit, User)
from mycodo.mycodo_flask.forms import forms_settings
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_general, utils_settings
from mycodo.utils.modules import load_module_from_file
from mycodo.utils.system_pi import (add_custom_measurements, add_custom_units,
                                    base64_encode_bytes, cmd_output)

logger = logging.getLogger('mycodo.mycodo_flask.settings')

blueprint = Blueprint('routes_settings',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.context_processor
@flask_login.login_required
def api_key_tools():
    return dict(base64_encode_bytes=base64_encode_bytes)


@blueprint.route('/settings/alerts', methods=('GET', 'POST'))
@flask_login.login_required
def settings_alerts():
    """Display alert settings."""
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


@blueprint.route('/logo.jpg', methods=['GET'])
@flask_login.login_required
def brand_logo():
    """Return logo from database"""
    misc = Misc.query.first()
    if misc.brand_image:
        return send_file(
            BytesIO(misc.brand_image),
            mimetype='image/jpg'
        )


@blueprint.route('/settings/general', methods=('GET', 'POST'))
@flask_login.login_required
def settings_general():
    """Display general settings."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_settings_general = forms_settings.SettingsGeneral()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            messages["error"].append("Your permissions do not allow this action")

        if not messages["error"]:
            messages = utils_settings.settings_general_mod(form_settings_general)

        for each_error in messages["error"]:
            flash(each_error, "error")
        for each_warn in messages["warning"]:
            flash(each_warn, "warning")
        for each_info in messages["info"]:
            flash(each_info, "info")
        for each_success in messages["success"]:
            flash(each_success, "success")

    return render_template('settings/general.html',
                           form_settings_general=form_settings_general,
                           report_path=os.path.normpath(USAGE_REPORTS_PATH))


@blueprint.route('/settings/function', methods=('GET', 'POST'))
@flask_login.login_required
def settings_function():
    """Display function settings."""
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_controller = forms_settings.Controller()
    form_controller_delete = forms_settings.ControllerDel()

    # Get list of custom functions
    excluded_files = ['__init__.py', '__pycache__']

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_controller.import_controller_upload.data:
            utils_settings.settings_function_import(form_controller)
        elif form_controller_delete.delete_controller.data:
            utils_settings.settings_function_delete(form_controller_delete)

        return redirect(url_for('routes_settings.settings_function'))

    dict_controllers = {}

    for each_file in os.listdir(PATH_FUNCTIONS_CUSTOM):
        if each_file not in excluded_files:
            try:
                full_path_file = os.path.join(PATH_FUNCTIONS_CUSTOM, each_file)
                controller_info, status = load_module_from_file(full_path_file, 'functions')

                if controller_info:
                    func_info = controller_info.FUNCTION_INFORMATION
                    dict_controllers[func_info['function_name_unique']] = {}
                    dict_controllers[func_info['function_name_unique']]['function_name'] = func_info['function_name']
            except:
                pass

    return render_template('settings/function.html',
                           dict_controllers=dict_controllers,
                           form_controller=form_controller,
                           form_controller_delete=form_controller_delete)


@blueprint.route('/settings/action', methods=('GET', 'POST'))
@flask_login.login_required
def settings_action():
    """Display action settings."""
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_action = forms_settings.Action()
    form_action_delete = forms_settings.ActionDel()

    # Get list of custom functions
    excluded_files = ['__init__.py', '__pycache__']

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_action.import_action_upload.data:
            utils_settings.settings_action_import(form_action)
        elif form_action_delete.delete_action.data:
            utils_settings.settings_action_delete(form_action_delete)

        return redirect(url_for('routes_settings.settings_action'))

    dict_actions = {}

    for each_file in os.listdir(PATH_ACTIONS_CUSTOM):
        if each_file not in excluded_files:
            try:
                full_path_file = os.path.join(PATH_ACTIONS_CUSTOM, each_file)
                action_info, status = load_module_from_file(full_path_file, 'actions')

                if action_info:
                    func_info = action_info.ACTION_INFORMATION
                    dict_actions[func_info['name_unique']] = {}
                    dict_actions[func_info['name_unique']]['name'] = func_info['name']
            except:
                pass

    return render_template('settings/action.html',
                           dict_actions=dict_actions,
                           form_action=form_action,
                           form_action_delete=form_action_delete)


@blueprint.route('/settings/input', methods=('GET', 'POST'))
@flask_login.login_required
def settings_input():
    """Display measurement settings."""
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_input = forms_settings.Input()
    form_input_delete = forms_settings.InputDel()

    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    # Get list of custom inputs
    excluded_files = ['__init__.py', '__pycache__']

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_input.import_input_upload.data:
            utils_settings.settings_input_import(form_input)
        elif form_input_delete.delete_input.data:
            utils_settings.settings_input_delete(form_input_delete)

        return redirect(url_for('routes_settings.settings_input'))

    dict_inputs = {}

    for each_file in os.listdir(PATH_INPUTS_CUSTOM):
        if each_file not in excluded_files:
            try:
                full_path_file = os.path.join(PATH_INPUTS_CUSTOM, each_file)
                input_info, status = load_module_from_file(full_path_file, 'inputs')

                if input_info:
                    dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']] = {}
                    dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']]['input_name'] = \
                        input_info.INPUT_INFORMATION['input_name']
                    dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']]['input_manufacturer'] = \
                        input_info.INPUT_INFORMATION['input_manufacturer']
                    dict_inputs[input_info.INPUT_INFORMATION['input_name_unique']]['measurements_name'] = \
                        input_info.INPUT_INFORMATION['measurements_name']
            except:
                pass

    return render_template('settings/input.html',
                           dict_inputs=dict_inputs,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           form_input=form_input,
                           form_input_delete=form_input_delete)


@blueprint.route('/settings/output', methods=('GET', 'POST'))
@flask_login.login_required
def settings_output():
    """Display output settings."""
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_output = forms_settings.Output()
    form_output_delete = forms_settings.OutputDel()

    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    # Get list of custom outputs
    excluded_files = ['__init__.py', '__pycache__']

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_output.import_output_upload.data:
            utils_settings.settings_output_import(form_output)
        elif form_output_delete.delete_output.data:
            utils_settings.settings_output_delete(form_output_delete)

        return redirect(url_for('routes_settings.settings_output'))

    dict_outputs = {}

    for each_file in os.listdir(PATH_OUTPUTS_CUSTOM):
        if each_file not in excluded_files:
            try:
                full_path_file = os.path.join(PATH_OUTPUTS_CUSTOM, each_file)
                output_info, status = load_module_from_file(full_path_file, 'outputs')

                if output_info:
                    dict_outputs[output_info.OUTPUT_INFORMATION['output_name_unique']] = {}
                    dict_outputs[output_info.OUTPUT_INFORMATION['output_name_unique']]['output_name'] = \
                        output_info.OUTPUT_INFORMATION['output_name']
                    dict_outputs[output_info.OUTPUT_INFORMATION['output_name_unique']]['measurements_name'] = \
                        output_info.OUTPUT_INFORMATION['measurements_name']
            except:
                pass

    return render_template('settings/output.html',
                           dict_outputs=dict_outputs,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           form_output=form_output,
                           form_output_delete=form_output_delete)


@blueprint.route('/settings/widget', methods=('GET', 'POST'))
@flask_login.login_required
def settings_widget():
    """Display widget settings."""
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_widget = forms_settings.Widget()
    form_widget_delete = forms_settings.WidgetDel()

    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    # Get list of custom widgets
    excluded_files = ['__init__.py', '__pycache__']

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_widget.import_widget_upload.data:
            utils_settings.settings_widget_import(form_widget)
        elif form_widget_delete.delete_widget.data:
            utils_settings.settings_widget_delete(form_widget_delete)

        return redirect(url_for('routes_settings.settings_widget'))

    dict_widgets = {}

    for each_file in os.listdir(PATH_WIDGETS_CUSTOM):
        if each_file not in excluded_files:
            try:
                full_path_file = os.path.join(PATH_WIDGETS_CUSTOM, each_file)
                widget_info, status = load_module_from_file(full_path_file, 'widgets')

                if widget_info:
                    dict_widgets[widget_info.WIDGET_INFORMATION['widget_name_unique']] = {}
                    dict_widgets[widget_info.WIDGET_INFORMATION['widget_name_unique']]['widget_name'] = \
                        widget_info.WIDGET_INFORMATION['widget_name']
                    dict_widgets[widget_info.WIDGET_INFORMATION['widget_name_unique']]['measurements_name'] = \
                        widget_info.WIDGET_INFORMATION['measurements_name']
            except:
                pass

    return render_template('settings/widget.html',
                           dict_widgets=dict_widgets,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           form_widget=form_widget,
                           form_widget_delete=form_widget_delete)


@blueprint.route('/settings/measurement', methods=('GET', 'POST'))
@flask_login.login_required
def settings_measurement():
    """Display measurement settings."""
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



@blueprint.route('/change_preferences', methods=('GET', 'POST'))
@flask_login.login_required
def change_theme():
    """Change theme"""
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    form_prefs = forms_settings.UserPreferences()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_users'):
            return redirect(url_for('routes_general.home'))

        if form_prefs.user_preferences_save.data:
            utils_settings.change_preferences(form_prefs)
    return redirect(url_for('routes_general.home'))


@blueprint.route('/settings/users_submit', methods=['POST'])
@flask_login.login_required
def settings_users_submit():
    """Submit form for User Settings page"""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    page_refresh = False
    logout = False
    user_id = None
    role_id = None
    generated_api_key = None

    if not utils_general.user_has_permission('edit_users'):
        messages["error"].append("Your permissions do not allow this action")

    form_user = forms_settings.User()
    form_mod_user = forms_settings.UserMod()
    form_user_roles = forms_settings.UserRoles()

    if not messages["error"]:
        if form_user.settings_user_save.data:
            messages = utils_settings.user(form_user)
        elif form_mod_user.user_generate_api_key.data:
            (messages,
             generated_api_key) = utils_settings.generate_api_key(
                form_mod_user)
            user_id = form_mod_user.user_id.data
        elif form_mod_user.user_delete.data:
            user_id = form_mod_user.user_id.data
            messages = utils_settings.user_del(form_mod_user)
        elif form_mod_user.user_save.data:
            messages, logout = utils_settings.user_mod(form_mod_user)
            if logout:
                page_refresh = True
        elif (form_user_roles.user_role_save.data or
              form_user_roles.user_role_delete.data):
            role_id = form_user_roles.role_id.data
            messages, page_refresh = utils_settings.user_roles(form_user_roles)

    if page_refresh:
        for each_error in messages["error"]:
            flash(each_error, "error")
        for each_warn in messages["warning"]:
            flash(each_warn, "warning")
        for each_info in messages["info"]:
            flash(each_info, "info")
        for each_success in messages["success"]:
            flash(each_success, "success")

    return jsonify(data={
        'generated_api_key': generated_api_key,
        'user_id': user_id,
        'role_id': role_id,
        'messages': messages,
        'logout': logout
    })


@blueprint.route('/settings/users', methods=('GET', 'POST'))
@flask_login.login_required
def settings_users():
    """Display user settings."""
    if not utils_general.user_has_permission('view_settings'):
        return redirect(url_for('routes_general.home'))

    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    misc = Misc.query.first()
    form_user = forms_settings.User()
    form_add_user = forms_settings.UserAdd()
    form_mod_user = forms_settings.UserMod()
    form_user_roles = forms_settings.UserRoles()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_users'):
            return redirect(url_for('routes_general.home'))

        if form_add_user.user_add.data:
            utils_settings.user_add(form_add_user)
        elif form_user_roles.user_role_add.data:
            messages, page_refresh = utils_settings.user_roles(form_user_roles)

    for each_error in messages["error"]:
        flash(each_error, "error")
    for each_warn in messages["warning"]:
        flash(each_warn, "warning")
    for each_info in messages["info"]:
        flash(each_info, "info")
    for each_success in messages["success"]:
        flash(each_success, "success")

    users = User.query.all()
    user_roles = Role.query.all()

    return render_template('settings/users.html',
                           misc=misc,
                           themes=THEMES,
                           users=users,
                           user_roles=user_roles,
                           form_add_user=form_add_user,
                           form_mod_user=form_mod_user,
                           form_user=form_user,
                           form_user_roles=form_user_roles)


@blueprint.route('/settings/pi', methods=('GET', 'POST'))
@flask_login.login_required
def settings_pi():
    """Display general settings."""
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
    """Display general settings."""
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
        elif form_settings_diagnostic.recreate_influxdb_db_1.data:
            utils_settings.settings_diagnostic_recreate_influxdb_db_1()
        elif form_settings_diagnostic.recreate_influxdb_db_2.data:
            utils_settings.settings_diagnostic_recreate_influxdb_db_2()
        elif form_settings_diagnostic.reset_email_counter.data:
            utils_settings.settings_diagnostic_reset_email_counter()
        elif form_settings_diagnostic.install_dependencies.data:
            utils_settings.settings_diagnostic_install_dependencies()
        elif form_settings_diagnostic.regenerate_widget_html.data:
            regen_widget_html = threading.Thread(target=utils_settings.settings_regenerate_widget_html)
            regen_widget_html.start()
            flash("Widget HTML Regeneration started in the background. "
                  "It may take a few seconds to complete. "
                  "Any errors will appear in the Web Log.", "success")
        elif form_settings_diagnostic.upgrade_master.data:
            utils_settings.settings_diagnostic_upgrade_master()

        return redirect(url_for('routes_settings.settings_diagnostic'))

    return render_template('settings/diagnostic.html',
                           form_settings_diagnostic=form_settings_diagnostic)


def get_raspi_config_settings():
    settings = {
        'i2c_enabled': None,
        'ssh_enabled': None,
        'pi_camera_enabled': None,
        'one_wire_enabled': None,
        'serial_enabled': None,
        'spi_enabled': None,
        'hostname': None
    }
    i2c_status, _, _ = cmd_output("raspi-config nonint get_i2c", user="root")
    if i2c_status:
        settings['i2c_enabled'] = not bool(int(i2c_status))
    ssh_status, _, _ = cmd_output("raspi-config nonint get_ssh", user="root")
    if ssh_status:
        settings['ssh_enabled'] = not bool(int(ssh_status))
    cam_status, _, _ = cmd_output("raspi-config nonint get_camera", user="root")
    if cam_status:
        settings['pi_camera_enabled'] = not bool(int(cam_status))
    one_wire_status, _, _ = cmd_output("raspi-config nonint get_onewire", user="root")
    if one_wire_status:
        settings['one_wire_enabled'] = not bool(int(one_wire_status))
    serial_status, _, _ = cmd_output("raspi-config nonint get_serial", user="root")
    if serial_status:
        settings['serial_enabled'] = not bool(int(serial_status))
    spi_status, _, _ = cmd_output("raspi-config nonint get_spi", user="root")
    if spi_status:
        settings['spi_enabled'] = not bool(int(spi_status))
    hostname_out, _, _ = cmd_output("raspi-config nonint get_hostname", user="root")
    if hostname_out:
        settings['hostname'] = hostname_out.decode("utf-8")
    return settings
