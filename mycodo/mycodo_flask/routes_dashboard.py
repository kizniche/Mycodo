# coding=utf-8
"""collection of Page endpoints."""
import flask_login
import logging
import os
import subprocess
from flask import redirect, render_template, request, url_for
from flask.blueprints import Blueprint
from sqlalchemy import and_

from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import PATH_TEMPLATE_USER
from mycodo.databases.models import (PID, Camera, Conditional, Conversion,
                                     CustomController, Dashboard,
                                     DeviceMeasurements, Input, Measurement,
                                     Method, Misc, NoteTags, Output,
                                     OutputChannel, Trigger, Unit, Widget)
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_dashboard
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_dashboard, utils_general
from mycodo.utils.outputs import output_types, parse_output_information
from mycodo.utils.system_pi import (
    add_custom_measurements, add_custom_units, parse_custom_option_values_json,
    parse_custom_option_values_output_channels_json, return_measurement_info)
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger('mycodo.mycodo_flask.routes_dashboard')

blueprint = Blueprint('routes_dashboard',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.route('/save_dashboard_layout', methods=['POST'])
def save_dashboard_layout():
    """Save positions and sizes of widgets of a particular dashboard."""
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))
    data = request.get_json()
    keys = ('id', 'x', 'y', 'w', 'h')
    for index, each_widget in enumerate(data):
        if all(k in each_widget for k in keys):
            widget_mod = Widget.query.filter(
                Widget.unique_id == each_widget['id']).first()
            if widget_mod:
                widget_mod.position_x = each_widget['x']
                widget_mod.position_y = each_widget['y']
                widget_mod.width = each_widget['w']
                widget_mod.height = each_widget['h']
    db.session.commit()
    return "success"


@blueprint.route('/dashboard', methods=('GET', 'POST'))
@flask_login.login_required
def page_dashboard_default():
    """Load default dashboard."""
    dashboard = Dashboard.query.first()
    return redirect(url_for(
        'routes_dashboard.page_dashboard', dashboard_id=dashboard.unique_id))


@blueprint.route('/dashboard-add', methods=('GET', 'POST'))
@flask_login.login_required
def page_dashboard_add():
    """Add a dashboard."""
    if not utils_general.user_has_permission('edit_controllers'):
        return redirect(url_for('routes_general.home'))
    dashboard_id = utils_dashboard.dashboard_add()
    return redirect(url_for(
        'routes_dashboard.page_dashboard', dashboard_id=dashboard_id))


@blueprint.route('/dashboard/<dashboard_id>', methods=('GET', 'POST'))
@flask_login.login_required
def page_dashboard(dashboard_id):
    """Generate custom dashboard with various data."""
    # Retrieve tables from SQL database
    this_dashboard = Dashboard.query.filter(
        Dashboard.unique_id == dashboard_id).first()
    if not this_dashboard:
        return redirect(url_for('routes_dashboard.page_dashboard_default'))

    camera = Camera.query.all()
    conditional = Conditional.query.all()
    function = CustomController.query.all()
    widget = Widget.query.all()
    input_dev = Input.query.all()
    device_measurements = DeviceMeasurements.query.all()
    method = Method.query.all()
    misc = Misc.query.first()
    output = Output.query.all()
    output_channel = OutputChannel.query.all()
    pid = PID.query.all()
    tags = NoteTags.query.all()

    # Create form objects
    form_base = forms_dashboard.DashboardBase()
    form_dashboard = forms_dashboard.DashboardConfig()

    if request.method == 'POST':
        unmet_dependencies = None
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        # Dashboard
        if form_dashboard.dash_modify.data:
            utils_dashboard.dashboard_mod(form_dashboard)
        elif form_dashboard.dash_duplicate.data:
            utils_dashboard.dashboard_copy(form_dashboard)
        elif form_dashboard.lock.data:
            utils_dashboard.dashboard_lock(form_dashboard.dashboard_id.data, True)
        elif form_dashboard.unlock.data:
            utils_dashboard.dashboard_lock(form_dashboard.dashboard_id.data, False)
        elif form_dashboard.dash_delete.data:
            utils_dashboard.dashboard_del(form_dashboard)
            return redirect(url_for('routes_dashboard.page_dashboard_default'))

        # Widget
        elif form_base.widget_add.data:
            unmet_dependencies, reload_flask = utils_dashboard.widget_add(form_base, request.form)
            if not unmet_dependencies and reload_flask:
                return redirect(url_for(
                    'routes_dashboard.restart_flask_auto_advance_page',
                    dashboard_id=this_dashboard.unique_id))
        elif form_base.widget_mod.data:
            utils_dashboard.widget_mod(form_base, request.form)
        elif form_base.widget_delete.data:
            utils_dashboard.widget_del(form_base)

        if unmet_dependencies:
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device=form_base.widget_type.data))

        return redirect(url_for(
            'routes_dashboard.page_dashboard', dashboard_id=this_dashboard.unique_id))

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    # Generate dictionary of each measurement ID with the correct measurement/unit used with it
    dict_measure_measurements = {}
    dict_measure_units = {}

    for each_measurement in device_measurements:
        # If the measurement is a PID setpoint, set unit to PID measurement.
        measurement = None
        unit = None
        if each_measurement.measurement_type == 'setpoint':
            setpoint_pid = PID.query.filter(PID.unique_id == each_measurement.device_id).first()
            if setpoint_pid and ',' in setpoint_pid.measurement:
                pid_measurement = setpoint_pid.measurement.split(',')[1]
                setpoint_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == pid_measurement).first()
                if setpoint_measurement:
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == setpoint_measurement.conversion_id).first()
                    _, unit, measurement = return_measurement_info(setpoint_measurement, conversion)
        else:
            conversion = Conversion.query.filter(
                Conversion.unique_id == each_measurement.conversion_id).first()
            _, unit, measurement = return_measurement_info(each_measurement, conversion)
        if unit:
            dict_measure_measurements[each_measurement.unique_id] = measurement
            dict_measure_units[each_measurement.unique_id] = unit

    dict_outputs = parse_output_information()
    dict_widgets = parse_widget_information()

    custom_options_values_widgets = parse_custom_option_values_json(
        widget, dict_controller=dict_widgets)

    custom_options_values_output_channels = parse_custom_option_values_output_channels_json(
        output_channel, dict_controller=dict_outputs, key_name='custom_channel_options')

    widget_types_on_dashboard = []
    custom_widget_variables = {}
    widgets_dash = Widget.query.filter(Widget.dashboard_id == dashboard_id).all()
    for each_dash_widget in widgets_dash:
        # Make list of widget types on this particular dashboard
        if each_dash_widget.graph_type not in widget_types_on_dashboard:
            widget_types_on_dashboard.append(each_dash_widget.graph_type)

        # Generate dictionary of returned values from widget modules on this particular dashboard
        if 'generate_page_variables' in dict_widgets[each_dash_widget.graph_type]:
            custom_widget_variables[each_dash_widget.unique_id] = dict_widgets[each_dash_widget.graph_type]['generate_page_variables'](
                each_dash_widget.unique_id, custom_options_values_widgets[each_dash_widget.unique_id])

    # generate lists of html files to include in dashboard template
    list_html_files_body = {}
    list_html_files_title_bar = {}
    list_html_files_head = {}
    list_html_files_configure_options = {}
    list_html_files_js = {}
    list_html_files_js_ready = {}
    list_html_files_js_ready_end = {}

    for each_widget_type in widget_types_on_dashboard:
        file_html_head = "widget_template_{}_head.html".format(each_widget_type)
        path_html_head = os.path.join(PATH_TEMPLATE_USER, file_html_head)
        if os.path.exists(path_html_head):
            list_html_files_head[each_widget_type] = file_html_head

        file_html_title_bar = "widget_template_{}_title_bar.html".format(each_widget_type)
        path_html_title_bar = os.path.join(PATH_TEMPLATE_USER, file_html_title_bar)
        if os.path.exists(path_html_title_bar):
            list_html_files_title_bar[each_widget_type] = file_html_title_bar

        file_html_body = "widget_template_{}_body.html".format(each_widget_type)
        path_html_body = os.path.join(PATH_TEMPLATE_USER, file_html_body)
        if os.path.exists(path_html_body):
            list_html_files_body[each_widget_type] = file_html_body

        file_html_configure_options = "widget_template_{}_configure_options.html".format(each_widget_type)
        path_html_configure_options = os.path.join(PATH_TEMPLATE_USER, file_html_configure_options)
        if os.path.exists(path_html_configure_options):
            list_html_files_configure_options[each_widget_type] = file_html_configure_options

        file_html_js = "widget_template_{}_js.html".format(each_widget_type)
        path_html_js = os.path.join(PATH_TEMPLATE_USER, file_html_js)
        if os.path.exists(path_html_js):
            list_html_files_js[each_widget_type] = file_html_js

        file_html_js_ready = "widget_template_{}_js_ready.html".format(each_widget_type)
        path_html_js_ready = os.path.join(PATH_TEMPLATE_USER, file_html_js_ready)
        if os.path.exists(path_html_js_ready):
            list_html_files_js_ready[each_widget_type] = file_html_js_ready

        file_html_js_ready_end = "widget_template_{}_js_ready_end.html".format(each_widget_type)
        path_html_js_ready_end = os.path.join(PATH_TEMPLATE_USER, file_html_js_ready_end)
        if os.path.exists(path_html_js_ready_end):
            list_html_files_js_ready_end[each_widget_type] = file_html_js_ready_end

    # Retrieve all choices to populate form drop-down menu
    choices_camera = utils_general.choices_id_name(camera)
    choices_function = utils_general.choices_functions(
        function, dict_units, dict_measurements)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_method = utils_general.choices_methods(method)
    choices_output = utils_general.choices_outputs(
        output, OutputChannel, dict_outputs, dict_units, dict_measurements)
    choices_output_channels = utils_general.choices_outputs_channels(
        output, output_channel, dict_outputs)
    choices_output_channels_measurements = utils_general.choices_outputs_channels_measurements(
        output, OutputChannel, dict_outputs, dict_units, dict_measurements)
    choices_output_pwm = utils_general.choices_outputs_pwm(
        output, OutputChannel, dict_outputs, dict_units, dict_measurements)
    choices_pid = utils_general.choices_pids(
        pid, dict_units, dict_measurements)
    choices_pid_devices = utils_general.choices_pids_devices(pid)
    choices_tag = utils_general.choices_tags(tags)

    device_measurements_dict = {}
    for meas in device_measurements:
        device_measurements_dict[meas.unique_id] = meas

    # Get what each measurement uses for a unit
    use_unit = utils_general.use_unit_generate(
        device_measurements, input_dev, output, function)

    return render_template('pages/dashboard.html',
                           and_=and_,
                           conditional=conditional,
                           custom_options_values_output_channels=custom_options_values_output_channels,
                           custom_options_values_widgets=custom_options_values_widgets,
                           custom_widget_variables=custom_widget_variables,
                           table_conversion=Conversion,
                           table_function=CustomController,
                           table_widget=Widget,
                           table_input=Input,
                           table_output=Output,
                           table_output_channel=OutputChannel,
                           table_pid=PID,
                           table_device_measurements=DeviceMeasurements,
                           table_camera=Camera,
                           table_conditional=Conditional,
                           table_trigger=Trigger,
                           choices_camera=choices_camera,
                           choices_function=choices_function,
                           choices_input=choices_input,
                           choices_method=choices_method,
                           choices_output=choices_output,
                           choices_output_channels=choices_output_channels,
                           choices_output_channels_measurements=choices_output_channels_measurements,
                           choices_output_pwm=choices_output_pwm,
                           choices_pid=choices_pid,
                           choices_pid_devices=choices_pid_devices,
                           choices_tag=choices_tag,
                           dashboard_id=this_dashboard.unique_id,
                           device_measurements_dict=device_measurements_dict,
                           dict_measure_measurements=dict_measure_measurements,
                           dict_measure_units=dict_measure_units,
                           dict_measurements=dict_measurements,
                           dict_outputs=dict_outputs,
                           dict_units=dict_units,
                           dict_widgets=dict_widgets,
                           list_html_files_head=list_html_files_head,
                           list_html_files_title_bar=list_html_files_title_bar,
                           list_html_files_body=list_html_files_body,
                           list_html_files_configure_options=list_html_files_configure_options,
                           list_html_files_js=list_html_files_js,
                           list_html_files_js_ready=list_html_files_js_ready,
                           list_html_files_js_ready_end=list_html_files_js_ready_end,
                           camera=camera,
                           function=function,
                           misc=misc,
                           pid=pid,
                           output=output,
                           output_types=output_types(),
                           input=input_dev,
                           tags=tags,
                           this_dashboard=this_dashboard,
                           use_unit=use_unit,
                           form_base=form_base,
                           form_dashboard=form_dashboard,
                           widget=widget)


@blueprint.route('/reload_flask/<dashboard_id>')
@flask_login.login_required
def restart_flask_auto_advance_page(dashboard_id=""):
    """Wait then automatically load next page"""
    logger.info("Reloading frontend in 10 seconds")
    cmd = f"sleep 10 && {INSTALL_DIRECTORY}/mycodo/scripts/mycodo_wrapper frontend_reload 2>&1"
    subprocess.Popen(cmd, shell=True)

    return render_template('pages/wait_and_autoload.html',
                           dashboard_id=dashboard_id)
