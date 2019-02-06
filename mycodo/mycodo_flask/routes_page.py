# coding=utf-8
""" collection of Page endpoints """
import calendar
import datetime
import glob
import logging
import resource
import socket
import subprocess
import sys
import time
from collections import OrderedDict
from importlib import import_module

import flask_login
import os
import re
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import url_for
from flask.blueprints import Blueprint
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.config import ALEMBIC_VERSION
from mycodo.config import BACKUP_LOG_FILE
from mycodo.config import CONDITIONAL_CONDITIONS
from mycodo.config import DAEMON_LOG_FILE
from mycodo.config import DAEMON_PID_FILE
from mycodo.config import DEPENDENCY_LOG_FILE
from mycodo.config import FRONTEND_PID_FILE
from mycodo.config import FUNCTION_ACTIONS
from mycodo.config import FUNCTION_TYPES
from mycodo.config import HTTP_ACCESS_LOG_FILE
from mycodo.config import HTTP_ERROR_LOG_FILE
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import KEEPUP_LOG_FILE
from mycodo.config import LOGIN_LOG_FILE
from mycodo.config import MATH_INFO
from mycodo.config import MYCODO_VERSION
from mycodo.config import OUTPUTS
from mycodo.config import OUTPUT_INFO
from mycodo.config import PATH_1WIRE
from mycodo.config import RESTORE_LOG_FILE
from mycodo.config import UPGRADE_LOG_FILE
from mycodo.config import USAGE_REPORTS_PATH
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.databases.models import Actions
from mycodo.databases.models import AlembicVersion
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import Conversion
from mycodo.databases.models import Dashboard
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import EnergyUsage
from mycodo.databases.models import Function
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import LCDData
from mycodo.databases.models import Math
from mycodo.databases.models import Measurement
from mycodo.databases.models import Method
from mycodo.databases.models import Misc
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.databases.models import Output
from mycodo.databases.models import PID
from mycodo.databases.models import Trigger
from mycodo.databases.models import Unit
from mycodo.databases.models import User
from mycodo.devices.camera import camera_record
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_client import daemon_active
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_conditional
from mycodo.mycodo_flask.forms import forms_dashboard
from mycodo.mycodo_flask.forms import forms_function
from mycodo.mycodo_flask.forms import forms_input
from mycodo.mycodo_flask.forms import forms_lcd
from mycodo.mycodo_flask.forms import forms_math
from mycodo.mycodo_flask.forms import forms_misc
from mycodo.mycodo_flask.forms import forms_notes
from mycodo.mycodo_flask.forms import forms_output
from mycodo.mycodo_flask.forms import forms_pid
from mycodo.mycodo_flask.forms import forms_trigger
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_conditional
from mycodo.mycodo_flask.utils import utils_dashboard
from mycodo.mycodo_flask.utils import utils_export
from mycodo.mycodo_flask.utils import utils_function
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_input
from mycodo.mycodo_flask.utils import utils_lcd
from mycodo.mycodo_flask.utils import utils_math
from mycodo.mycodo_flask.utils import utils_misc
from mycodo.mycodo_flask.utils import utils_notes
from mycodo.mycodo_flask.utils import utils_output
from mycodo.mycodo_flask.utils import utils_pid
from mycodo.mycodo_flask.utils import utils_trigger
from mycodo.utils.influx import average_past_seconds
from mycodo.utils.influx import average_start_end_seconds
from mycodo.utils.inputs import list_analog_to_digital_converters
from mycodo.utils.inputs import parse_custom_option_values
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.sunriseset import Sun
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import dpkg_package_exists
from mycodo.utils.system_pi import list_to_csv
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.tools import return_output_usage

logger = logging.getLogger('mycodo.mycodo_flask.routes_page')

blueprint = Blueprint('routes_page',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()


@blueprint.context_processor
def page_functions():
    def epoch_to_time_string(epoch):
        return datetime.datetime.fromtimestamp(epoch).strftime(
            "%Y-%m-%d %H:%M:%S")

    def get_note_tag_from_unique_id(tag_unique_id):
        tag = NoteTags.query.filter(NoteTags.unique_id == tag_unique_id).first()
        if tag and tag.name:
            return tag.name
        else:
            return 'TAG ERROR'

    def utc_to_local_time(utc_dt):
        utc_timestamp = calendar.timegm(utc_dt.timetuple())
        return str(datetime.datetime.fromtimestamp(utc_timestamp))

    return dict(epoch_to_time_string=epoch_to_time_string,
                get_note_tag_from_unique_id=get_note_tag_from_unique_id,
                utc_to_local_time=utc_to_local_time)


@blueprint.route('/camera', methods=('GET', 'POST'))
@flask_login.login_required
def page_camera():
    """
    Page to start/stop video stream or time-lapse, or capture a still image.
    Displays most recent still image and time-lapse image.
    """
    if not utils_general.user_has_permission('view_camera'):
        return redirect(url_for('routes_general.home'))

    form_camera = forms_misc.Camera()
    camera = Camera.query.all()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_page.page_camera'))

        control = DaemonControl()
        mod_camera = Camera.query.filter(
            Camera.unique_id == form_camera.camera_id.data).first()
        if form_camera.capture_still.data:
            # If a stream is active, stop the stream to take a photo
            if mod_camera.stream_started:
                camera_stream = import_module(
                    'mycodo.mycodo_flask.camera.camera_{lib}'.format(
                        lib=mod_camera.library)).Camera
                if camera_stream(unique_id=mod_camera.unique_id).is_running(mod_camera.unique_id):
                    camera_stream(unique_id=mod_camera.unique_id).stop(mod_camera.unique_id)
                time.sleep(2)
            camera_record('photo', mod_camera.unique_id)
        elif form_camera.start_timelapse.data:
            if mod_camera.stream_started:
                flash(gettext("Cannot start time-lapse if stream is active."), "error")
                return redirect('/camera')
            now = time.time()
            mod_camera.timelapse_started = True
            mod_camera.timelapse_start_time = now
            mod_camera.timelapse_end_time = now + float(form_camera.timelapse_runtime_sec.data)
            mod_camera.timelapse_interval = form_camera.timelapse_interval.data
            mod_camera.timelapse_next_capture = now
            mod_camera.timelapse_capture_number = 0
            db.session.commit()
            control.refresh_daemon_camera_settings()
        elif form_camera.pause_timelapse.data:
            mod_camera.timelapse_paused = True
            db.session.commit()
            control.refresh_daemon_camera_settings()
        elif form_camera.resume_timelapse.data:
            mod_camera.timelapse_paused = False
            db.session.commit()
            control.refresh_daemon_camera_settings()
        elif form_camera.stop_timelapse.data:
            mod_camera.timelapse_started = False
            mod_camera.timelapse_start_time = None
            mod_camera.timelapse_end_time = None
            mod_camera.timelapse_interval = None
            mod_camera.timelapse_next_capture = None
            mod_camera.timelapse_capture_number = None
            db.session.commit()
            control.refresh_daemon_camera_settings()
        elif form_camera.start_stream.data:
            if mod_camera.timelapse_started:
                flash(gettext(
                    "Cannot start stream if time-lapse is active."), "error")
                return redirect('/camera')
            else:
                mod_camera.stream_started = True
                db.session.commit()
        elif form_camera.stop_stream.data:
            camera_stream = import_module(
                'mycodo.mycodo_flask.camera.camera_{lib}'.format(
                    lib=mod_camera.library)).Camera
            if camera_stream(unique_id=mod_camera.unique_id).is_running(mod_camera.unique_id):
                camera_stream(unique_id=mod_camera.unique_id).stop(mod_camera.unique_id)
            mod_camera.stream_started = False
            db.session.commit()

        return redirect(url_for('routes_page.page_camera'))

    # Get the full path and timestamps of latest still and time-lapse images
    (latest_img_still_ts,
     latest_img_still,
     latest_img_tl_ts,
     latest_img_tl) = utils_general.get_camera_image_info()

    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template('pages/camera.html',
                           camera=camera,
                           form_camera=form_camera,
                           latest_img_still=latest_img_still,
                           latest_img_still_ts=latest_img_still_ts,
                           latest_img_tl=latest_img_tl,
                           latest_img_tl_ts=latest_img_tl_ts,
                           time_now=time_now)


@blueprint.route('/notes', methods=('GET', 'POST'))
@flask_login.login_required
def page_notes():
    """
    Notes page
    """
    form_note_add = forms_notes.NoteAdd()
    form_note_options = forms_notes.NoteOptions()
    form_note_mod = forms_notes.NoteMod()
    form_tag_add = forms_notes.TagAdd()
    form_tag_options = forms_notes.TagOptions()
    form_note_show = forms_notes.NotesShow()

    total_notes = Notes.query.count()

    notes = Notes.query.order_by(Notes.id.desc()).limit(10)
    tags = NoteTags.query.all()

    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_page.page_notes'))

        if form_note_show.notes_show.data:
            notes = utils_notes.show_notes(form_note_show)
        elif form_note_show.notes_export.data:
            notes, data = utils_notes.export_notes(form_note_show)
            if data:
                # Send zip file to user
                return send_file(
                    data,
                    mimetype='application/zip',
                    as_attachment=True,
                    attachment_filename=
                    'Mycodo_Notes_{mv}_{host}_{dt}.zip'.format(
                        mv=MYCODO_VERSION,
                        host=socket.gethostname().replace(' ', ''),
                        dt=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
                )
        elif form_note_show.notes_import_upload.data:
            utils_notes.import_notes(form_note_show)
        else:
            if form_tag_add.tag_add.data:
                utils_notes.tag_add(form_tag_add)
            elif form_tag_options.tag_rename.data:
                utils_notes.tag_rename(form_tag_options)
            elif form_tag_options.tag_del.data:
                utils_notes.tag_del(form_tag_options)

            elif form_note_add.note_add.data:
                utils_notes.note_add(form_note_add)
            elif form_note_mod.note_save.data:
                utils_notes.note_mod(form_note_mod)
            elif form_note_options.note_del.data:
                utils_notes.note_del(form_note_options)
            elif form_note_options.note_mod.data:
                return redirect(url_for('routes_page.page_note_edit', unique_id=form_note_options.note_unique_id.data))

            return redirect(url_for('routes_page.page_notes'))

    if notes:
        note_count = notes.count()
        notes_all = notes.all()
    else:
        note_count = 0
        notes_all = None
    number_displayed_notes = (note_count, total_notes)

    return render_template('tools/notes.html',
                           form_note_add=form_note_add,
                           form_note_options=form_note_options,
                           form_note_mod=form_note_mod,
                           form_tag_add=form_tag_add,
                           form_tag_options=form_tag_options,
                           form_note_show=form_note_show,
                           notes=notes_all,
                           tags=tags,
                           current_date_time=current_date_time,
                           number_displayed_notes=number_displayed_notes)


@blueprint.route('/note_edit/<unique_id>', methods=('GET', 'POST'))
@flask_login.login_required
def page_note_edit(unique_id):
    """
    Edit note page
    """
    # Used in software tests to verify function is executing as admin
    if unique_id == '0':
        return 'admin logged in'

    this_note = Notes.query.filter(Notes.unique_id == unique_id).first()

    form_note_mod = forms_notes.NoteMod()

    tags = NoteTags.query.all()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('routes_page.page_notes'))

        if form_note_mod.note_save.data:
            utils_notes.note_mod(form_note_mod)
        if form_note_mod.file_rename.data:
            utils_notes.file_rename(form_note_mod)
        if form_note_mod.file_del.data:
            utils_notes.file_del(form_note_mod)
        if form_note_mod.note_del.data:
            utils_notes.note_del(form_note_mod)
            return redirect(url_for('routes_page.page_notes'))
        if form_note_mod.note_cancel.data:
            return redirect(url_for('routes_page.page_notes'))

        return redirect(url_for('routes_page.page_note_edit', unique_id=this_note.unique_id))

    form_note_mod.note.data = this_note.note

    return render_template('tools/note_edit.html',
                           form_note_mod=form_note_mod,
                           this_note=this_note,
                           tags=tags)


@blueprint.route('/export', methods=('GET', 'POST'))
@flask_login.login_required
def page_export():
    """
    Export/Import measurement and settings data
    """
    form_export_measurements = forms_misc.ExportMeasurements()
    form_export_settings = forms_misc.ExportSettings()
    form_import_settings = forms_misc.ImportSettings()
    form_export_influxdb = forms_misc.ExportInfluxdb()
    form_import_influxdb = forms_misc.ImportInfluxdb()

    output = Output.query.all()
    input_dev = Input.query.all()
    math = Math.query.all()

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    output_choices = utils_general.choices_outputs(
        output, dict_units, dict_measurements)
    input_choices = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    math_choices = utils_general.choices_maths(
        math, dict_units, dict_measurements)

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_export_measurements.export_data_csv.data:
            url = utils_export.export_measurements(form_export_measurements)
            if url:
                return redirect(url)
        elif form_export_settings.export_settings_zip.data:
            file_send = utils_export.export_settings(form_export_settings)
            if file_send:
                return file_send
            else:
                flash('Unknown error creating zipped settings database', 'error')
        elif form_import_settings.settings_import_upload.data:
            backup_file = utils_export.import_settings(form_import_settings)
            if backup_file:
                return redirect(url_for('routes_authentication.logout'))
        elif form_export_influxdb.export_influxdb_zip.data:
            file_send = utils_export.export_influxdb(form_export_influxdb)
            if file_send:
                return file_send
            else:
                flash('Unknown error creating zipped influxdb database '
                      'and metastore', 'error')
        elif form_import_influxdb.influxdb_import_upload.data:
            restore_output_list = utils_export.import_influxdb(form_import_influxdb)
            if restore_output_list:
                for each_out in restore_output_list:
                    flash(each_out, 'success')

    # Generate start end end times for date/time picker
    end_picker = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
    start_picker = datetime.datetime.now() - datetime.timedelta(hours=6)
    start_picker = start_picker.strftime('%m/%d/%Y %H:%M')

    return render_template('tools/export.html',
                           start_picker=start_picker,
                           end_picker=end_picker,
                           form_export_influxdb=form_export_influxdb,
                           form_export_measurements=form_export_measurements,
                           form_export_settings=form_export_settings,
                           form_import_influxdb=form_import_influxdb,
                           form_import_settings=form_import_settings,
                           output_choices=output_choices,
                           input_choices=input_choices,
                           math_choices=math_choices)


@blueprint.route('/dashboard', methods=('GET', 'POST'))
@flask_login.login_required
def page_dashboard():
    """
    Generate custom dashboard with various data
    """
    # Retrieve tables from SQL database
    camera = Camera.query.all()
    dashboard = Dashboard.query.all()
    input_dev = Input.query.all()
    device_measurements = DeviceMeasurements.query.all()
    math = Math.query.all()
    misc = Misc.query.first()
    output = Output.query.all()
    pid = PID.query.all()
    tags = NoteTags.query.all()

    # Retrieve the order to display graphs
    display_order_dashboard = csv_to_list_of_str(
        DisplayOrder.query.first().dashboard)

    # Create form objects
    form_base = forms_dashboard.DashboardBase()
    form_camera = forms_dashboard.DashboardCamera()
    form_graph = forms_dashboard.DashboardGraph()
    form_gauge = forms_dashboard.DashboardGauge()
    form_indicator = forms_dashboard.DashboardIndicator()
    form_measurement = forms_dashboard.DashboardMeasurement()
    form_output = forms_dashboard.DashboardOutput()
    form_pid = forms_dashboard.DashboardPIDControl()

    # Detect which form on the page was submitted
    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        # Reorder
        if form_base.reorder.data:
            mod_order = DisplayOrder.query.first()
            mod_order.dashboard = list_to_csv(
                form_base.list_visible_elements.data)
            db.session.commit()
            # Retrieve the order to display graphs
            display_order_dashboard = csv_to_list_of_str(
                DisplayOrder.query.first().dashboard)

        # Determine which form was submitted
        form_dashboard_object = None
        if form_base.create.data or form_base.modify.data:
            if form_base.dashboard_type.data == 'graph':
                form_dashboard_object = form_graph
            elif form_base.dashboard_type.data == 'gauge':
                form_dashboard_object = form_gauge
            elif form_base.dashboard_type.data == 'indicator':
                form_dashboard_object = form_indicator
            elif form_base.dashboard_type.data == 'measurement':
                form_dashboard_object = form_measurement
            elif form_base.dashboard_type.data == 'output':
                form_dashboard_object = form_output
            elif form_base.dashboard_type.data == 'pid_control':
                form_dashboard_object = form_pid
            elif form_base.dashboard_type.data == 'camera':
                form_dashboard_object = form_camera
            else:
                flash("Unknown Dashboard Object type: {type}".format(
                    type=form_base.dashboard_type.data), "error")
                return redirect(url_for('routes_page.page_dashboard'))

        if form_base.create.data:
            utils_dashboard.dashboard_add(
                form_base, form_dashboard_object, display_order_dashboard)
        elif form_base.modify.data:
            utils_dashboard.dashboard_mod(
                form_base, form_dashboard_object, request.form)
        elif form_base.delete.data:
            utils_dashboard.dashboard_del(form_base)
        elif form_base.order_up.data:
            utils_dashboard.dashboard_reorder(
                form_base.dashboard_id.data, display_order_dashboard, 'up')
        elif form_base.order_down.data:
            utils_dashboard.dashboard_reorder(
                form_base.dashboard_id.data, display_order_dashboard, 'down')

        return redirect(url_for('routes_page.page_dashboard'))

    # Create list of hidden dashboard element IDs and dict of names
    dashboard_element_names = {}
    dashboard_elements_hidden = []
    for each_element in dashboard:
        dashboard_element_names[each_element.unique_id] = '[{id}] {name}'.format(
            id=each_element.id, name=each_element.name)
        if (not display_order_dashboard or
                each_element.unique_id not in display_order_dashboard):
            dashboard_elements_hidden.append(each_element.unique_id)

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

    # Retrieve all choices to populate form drop-down menu
    choices_camera = utils_general.choices_id_name(camera)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_math = utils_general.choices_maths(
        math, dict_units, dict_measurements)
    choices_output = utils_general.choices_outputs(
        output, dict_units, dict_measurements)
    choices_pid = utils_general.choices_pids(
        pid, dict_units, dict_measurements)
    choices_note_tag = utils_general.choices_tags(tags)

    device_measurements_dict = {}
    for meas in device_measurements:
        device_measurements_dict[meas.unique_id] = meas

    # Add multi-select values as form choices, for validation
    form_graph.math_ids.choices = []
    form_graph.pid_ids.choices = []
    form_graph.output_ids.choices = []
    form_graph.input_ids.choices = []
    for key, value in choices_math.items():
        form_graph.math_ids.choices.append((key, value))
    for key, value in choices_pid.items():
        form_graph.pid_ids.choices.append((key, value))
    for key, value in choices_output.items():
        form_graph.output_ids.choices.append((key, value))
    for key, value in choices_input.items():
        form_graph.input_ids.choices.append((key, value))

    # Generate dictionary of custom colors for each graph
    colors_graph = dict_custom_colors()

    # Retrieve custom colors for gauges
    colors_gauge_solid = OrderedDict()
    colors_gauge_solid_form = OrderedDict()
    colors_gauge_angular = OrderedDict()
    try:
        for each_graph in dashboard:
            if each_graph.range_colors:  # Split into list
                color_areas = each_graph.range_colors.split(';')
            else:  # Create empty list
                color_areas = []
            colors_gauge_solid_total = []
            colors_gauge_solid_form_total = []
            colors_gauge_angular_total = []
            if each_graph.graph_type == 'gauge_angular':
                for each_range in color_areas:
                    colors_gauge_angular_total.append({
                        'low': each_range.split(',')[0],
                        'high': each_range.split(',')[1],
                        'hex': each_range.split(',')[2]})
                colors_gauge_angular.update(
                    {each_graph.unique_id: colors_gauge_angular_total})
            elif each_graph.graph_type == 'gauge_solid':
                try:
                    gauge_low = each_graph.y_axis_min
                    gauge_high = each_graph.y_axis_max
                    gauge_difference = gauge_high - gauge_low
                    for each_range in color_areas:
                        percent_of_range = float((float(each_range.split(',')[0]) - gauge_low) /
                                                 gauge_difference)
                        colors_gauge_solid_total.append({
                            'stop': '{:.2f}'.format(percent_of_range),
                            'hex': each_range.split(',')[1]})
                        colors_gauge_solid_form_total.append({
                            'stop': each_range.split(',')[0],
                            'hex': each_range.split(',')[1]})
                except:
                    # Prevent mathematical errors from preventing proper page render
                    for each_range in color_areas:
                        colors_gauge_solid_total.append({
                            'stop': '0',
                            'hex': each_range.split(',')[1]})
                        colors_gauge_solid_form_total.append({
                            'stop': '0',
                            'hex': each_range.split(',')[1]})
                colors_gauge_solid.update(
                    {each_graph.unique_id: colors_gauge_solid_total})
                colors_gauge_solid_form.update(
                    {each_graph.unique_id: colors_gauge_solid_form_total})
    except IndexError:
        flash("Colors Index Error", "error")

    # Generate a dictionary of lists of y-axes for each graph/gauge
    y_axes = utils_dashboard.graph_y_axes(dict_measurements)

    # Get what each measurement uses for a unit
    use_unit = utils_general.use_unit_generate(
        device_measurements, input_dev, output, math)

    # Generate a dictionary of each graph's y-axis minimum and maximum
    custom_yaxes = dict_custom_yaxes_min_max(dashboard, y_axes)

    return render_template('pages/dashboard.html',
                           table_conversion=Conversion,
                           table_dashboard=Dashboard,
                           table_input=Input,
                           table_math=Math,
                           table_device_measurements=DeviceMeasurements,
                           choices_camera=choices_camera,
                           choices_input=choices_input,
                           choices_math=choices_math,
                           choices_output=choices_output,
                           choices_pid=choices_pid,
                           choices_note_tag=choices_note_tag,
                           custom_yaxes=custom_yaxes,
                           dashboard_element_names=dashboard_element_names,
                           dashboard_elements_hidden=dashboard_elements_hidden,
                           device_measurements_dict=device_measurements_dict,
                           dict_measure_measurements=dict_measure_measurements,
                           dict_measure_units=dict_measure_units,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           display_order_dashboard=display_order_dashboard,
                           math=math,
                           misc=misc,
                           pid=pid,
                           output=output,
                           input=input_dev,
                           tags=tags,
                           colors_graph=colors_graph,
                           colors_gauge_angular=colors_gauge_angular,
                           colors_gauge_solid=colors_gauge_solid,
                           colors_gauge_solid_form=colors_gauge_solid_form,
                           use_unit=use_unit,
                           form_base=form_base,
                           form_camera=form_camera,
                           form_graph=form_graph,
                           form_gauge=form_gauge,
                           form_indicator=form_indicator,
                           form_measurement=form_measurement,
                           form_output=form_output,
                           form_pid=form_pid,
                           y_axes=y_axes)


@blueprint.route('/graph-async', methods=('GET', 'POST'))
@flask_login.login_required
def page_graph_async():
    """ Generate graphs using asynchronous data retrieval """
    input_dev = Input.query.all()
    device_measurements = DeviceMeasurements.query.all()
    math = Math.query.all()
    output = Output.query.all()
    pid = PID.query.all()
    tag = NoteTags.query.all()

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    # Get what each measurement uses for a unit
    use_unit = utils_general.use_unit_generate(
        device_measurements, input_dev, output, math)

    input_choices = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    math_choices = utils_general.choices_maths(
        math, dict_units, dict_measurements)
    output_choices = utils_general.choices_outputs(
        output, dict_units, dict_measurements)
    pid_choices = utils_general.choices_pids(
        pid, dict_units, dict_measurements)
    tag_choices = utils_general.choices_tags(tag)

    selected_ids_measures = []
    start_time_epoch = 0

    device_measurements_dict = {}
    for meas in device_measurements:
        device_measurements_dict[meas.unique_id] = meas

    dict_measure_measurements = {}
    dict_measure_units = {}

    for each_measurement in device_measurements:
        conversion = Conversion.query.filter(
            Conversion.unique_id == each_measurement.conversion_id).first()
        _, unit, measurement = return_measurement_info(each_measurement, conversion)
        dict_measure_measurements[each_measurement.unique_id] = measurement
        dict_measure_units[each_measurement.unique_id] = unit

    async_height = 600

    if request.method == 'POST':
        if request.form['async_height']:
            async_height = request.form['async_height']
        seconds = 0
        if request.form['submit'] == 'All Data':
            pass
        elif request.form['submit'] == 'Year':
            seconds = 31556952
        elif request.form['submit'] == 'Month':
            seconds = 2629746
        elif request.form['submit'] == 'Week':
            seconds = 604800
        elif request.form['submit'] == 'Day':
            seconds = 86400

        if seconds:
            start_time_epoch = (datetime.datetime.now() -
                                datetime.timedelta(seconds=seconds)).strftime('%s')
        selected_ids_measures = request.form.getlist('selected_measure')

    # Generate a dictionary of lists of y-axes
    y_axes = utils_dashboard.graph_y_axes_async(dict_measurements,
                                                selected_ids_measures)

    return render_template('pages/graph-async.html',
                           conversion=Conversion,
                           async_height=async_height,
                           start_time_epoch=start_time_epoch,
                           device_measurements_dict=device_measurements_dict,
                           dict_measure_measurements=dict_measure_measurements,
                           dict_measure_units=dict_measure_units,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           use_unit=use_unit,
                           input=input_dev,
                           math=math,
                           output=output,
                           pid=pid,
                           tag=tag,
                           input_choices=input_choices,
                           math_choices=math_choices,
                           output_choices=output_choices,
                           pid_choices=pid_choices,
                           tag_choices=tag_choices,
                           selected_ids_measures=selected_ids_measures,
                           y_axes=y_axes)


@blueprint.route('/help', methods=('GET', 'POST'))
@flask_login.login_required
def page_help():
    """ Display Mycodo manual/help """
    return render_template('manual.html')


@blueprint.route('/info', methods=('GET', 'POST'))
@flask_login.login_required
def page_info():
    """ Display page with system information from command line tools """
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('routes_general.home'))

    uptime = subprocess.Popen(
        "uptime", stdout=subprocess.PIPE, shell=True)
    (uptime_output, _) = uptime.communicate()
    uptime.wait()
    if uptime_output:
        uptime_output = uptime_output.decode("latin1")

    uname = subprocess.Popen(
        "uname -a", stdout=subprocess.PIPE, shell=True)
    (uname_output, _) = uname.communicate()
    uname.wait()
    if uname_output:
        uname_output = uname_output.decode("latin1")

    gpio = subprocess.Popen(
        "gpio readall", stdout=subprocess.PIPE, shell=True)
    (gpio_output, _) = gpio.communicate()
    gpio.wait()
    if gpio_output:
        gpio_output = gpio_output.decode("latin1")

    # Search for /dev/i2c- devices and compile a sorted dictionary of each
    # device's integer device number and the corresponding 'i2cdetect -y ID'
    # output for display on the info page
    i2c_devices_sorted = {}
    if not current_app.config['TESTING']:
        try:
            i2c_devices = glob.glob("/dev/i2c-*")
            i2c_devices_sorted = OrderedDict()
            for each_dev in i2c_devices:
                device_int = int(each_dev.replace("/dev/i2c-", ""))
                i2cdetect = subprocess.Popen(
                    "i2cdetect -y {dev}".format(dev=device_int),
                    stdout=subprocess.PIPE,
                    shell=True)
                (i2cdetect_out, _) = i2cdetect.communicate()
                i2cdetect.wait()
                if i2cdetect_out:
                    i2c_devices_sorted[device_int] = i2cdetect_out.decode("latin1")
        except Exception as er:
            flash("Error detecting I2C devices: {er}".format(er=er), "error")
        finally:
            i2c_devices_sorted = OrderedDict(sorted(i2c_devices_sorted.items()))

    df = subprocess.Popen(
        "df -h", stdout=subprocess.PIPE, shell=True)
    (df_output, _) = df.communicate()
    df.wait()
    if df_output:
        df_output = df_output.decode("latin1")

    free = subprocess.Popen(
        "free -h", stdout=subprocess.PIPE, shell=True)
    (free_output, _) = free.communicate()
    free.wait()
    if free_output:
        free_output = free_output.decode("latin1")

    ifconfig = subprocess.Popen(
        "ifconfig -a", stdout=subprocess.PIPE, shell=True)
    (ifconfig_output, _) = ifconfig.communicate()
    ifconfig.wait()
    if ifconfig_output:
        ifconfig_output = ifconfig_output.decode("latin1")

    database_version = AlembicVersion.query.first().version_num
    correct_database_version = ALEMBIC_VERSION

    virtualenv_flask = False
    if hasattr(sys, 'real_prefix'):
        virtualenv_flask = True

    daemon_pid = None
    if os.path.exists(DAEMON_PID_FILE):
        with open(DAEMON_PID_FILE, 'r') as pid_file:
            daemon_pid = int(pid_file.read())

    virtualenv_daemon = False
    pstree_daemon_output = None
    top_daemon_output = None
    daemon_up = daemon_active()
    if daemon_up:
        control = DaemonControl()
        ram_use_daemon = control.ram_use()
        virtualenv_daemon = control.is_in_virtualenv()

        pstree_damon = subprocess.Popen(
            "pstree -p {pid}".format(pid=daemon_pid), stdout=subprocess.PIPE, shell=True)
        (pstree_daemon_output, _) = pstree_damon.communicate()
        pstree_damon.wait()
        if pstree_daemon_output:
            pstree_daemon_output = pstree_daemon_output.decode("latin1")

        top_daemon = subprocess.Popen(
            "top -bH -n 1 -p {pid}".format(pid=daemon_pid), stdout=subprocess.PIPE, shell=True)
        (top_daemon_output, _) = top_daemon.communicate()
        top_daemon.wait()
        if top_daemon_output:
            top_daemon_output = top_daemon_output.decode("latin1")
    else:
        ram_use_daemon = 0

    frontend_pid = None
    if os.path.exists(FRONTEND_PID_FILE):
        with open(FRONTEND_PID_FILE, 'r') as pid_file:
            frontend_pid = int(pid_file.read())

    pstree_frontend_output = None
    top_frontend_output = None
    if frontend_pid:
        pstree_damon = subprocess.Popen(
            "pstree -p {pid}".format(pid=frontend_pid), stdout=subprocess.PIPE, shell=True)
        (pstree_frontend_output, _) = pstree_damon.communicate()
        pstree_damon.wait()
        if pstree_frontend_output:
            pstree_frontend_output = pstree_frontend_output.decode("latin1")

        top_frontend = subprocess.Popen(
            "top -bH -n 1 -p {pid}".format(pid=frontend_pid), stdout=subprocess.PIPE, shell=True)
        (top_frontend_output, _) = top_frontend.communicate()
        top_frontend.wait()
        if top_frontend_output:
            top_frontend_output = top_frontend_output.decode("latin1")

    ram_use_flask = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss / float(1000)

    python_version = sys.version

    return render_template('pages/info.html',
                           daemon_pid=daemon_pid,
                           daemon_up=daemon_up,
                           gpio_readall=gpio_output,
                           database_version=database_version,
                           correct_database_version=correct_database_version,
                           df=df_output,
                           free=free_output,
                           frontend_pid=frontend_pid,
                           i2c_devices_sorted=i2c_devices_sorted,
                           ifconfig=ifconfig_output,
                           pstree_daemon=pstree_daemon_output,
                           pstree_frontend=pstree_frontend_output,
                           python_version=python_version,
                           ram_use_daemon=ram_use_daemon,
                           ram_use_flask=ram_use_flask,
                           top_daemon=top_daemon_output,
                           top_frontend=top_frontend_output,
                           uname=uname_output,
                           uptime=uptime_output,
                           virtualenv_daemon=virtualenv_daemon,
                           virtualenv_flask=virtualenv_flask)


@blueprint.route('/lcd', methods=('GET', 'POST'))
@flask_login.login_required
def page_lcd():
    """ Display LCD output settings """
    lcd = LCD.query.all()
    lcd_data = LCDData.query.all()
    math = Math.query.all()
    pid = PID.query.all()
    output = Output.query.all()
    input_dev = Input.query.all()

    display_order = csv_to_list_of_str(DisplayOrder.query.first().lcd)

    dict_units = add_custom_units(Unit.query.all())
    dict_measurements = add_custom_measurements(Measurement.query.all())

    choices_lcd = utils_general.choices_lcd(
        input_dev, math, pid, output, dict_units, dict_measurements)

    form_lcd_add = forms_lcd.LCDAdd()
    form_lcd_mod = forms_lcd.LCDMod()
    form_lcd_display = forms_lcd.LCDModDisplay()

    if request.method == 'POST':
        unmet_dependencies = None
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_lcd_add.add.data:
            unmet_dependencies = utils_lcd.lcd_add(form_lcd_add)
        elif form_lcd_mod.save.data:
            utils_lcd.lcd_mod(form_lcd_mod)
        elif form_lcd_mod.delete.data:
            utils_lcd.lcd_del(form_lcd_mod.lcd_id.data)
        elif form_lcd_mod.reorder_up.data:
            utils_lcd.lcd_reorder(form_lcd_mod.lcd_id.data,
                                  display_order, 'up')
        elif form_lcd_mod.reorder_down.data:
            utils_lcd.lcd_reorder(form_lcd_mod.lcd_id.data,
                                  display_order, 'down')
        elif form_lcd_mod.activate.data:
            utils_lcd.lcd_activate(form_lcd_mod.lcd_id.data)
        elif form_lcd_mod.deactivate.data:
            utils_lcd.lcd_deactivate(form_lcd_mod.lcd_id.data)
        elif form_lcd_mod.reset_flashing.data:
            utils_lcd.lcd_reset_flashing(form_lcd_mod.lcd_id.data)
        elif form_lcd_mod.add_display.data:
            utils_lcd.lcd_display_add(form_lcd_mod)
        elif form_lcd_display.save_display.data:
            utils_lcd.lcd_display_mod(form_lcd_display)
        elif form_lcd_display.delete_display.data:
            utils_lcd.lcd_display_del(form_lcd_display.lcd_data_id.data)

        if unmet_dependencies:
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device=form_lcd_add.lcd_type.data))
        else:
            return redirect(url_for('routes_page.page_lcd'))

    return render_template('pages/lcd.html',
                           choices_lcd=choices_lcd,
                           lcd=lcd,
                           lcd_data=lcd_data,
                           math=math,
                           measurements=parse_input_information(),
                           pid=pid,
                           output=output,
                           sensor=input_dev,
                           display_order=display_order,
                           form_lcd_add=form_lcd_add,
                           form_lcd_mod=form_lcd_mod,
                           form_lcd_display=form_lcd_display)


@blueprint.route('/live', methods=('GET', 'POST'))
@flask_login.login_required
def page_live():
    """ Page of recent and updating input data """
    # Get what each measurement uses for a unit
    device_measurements = DeviceMeasurements.query.all()
    input_dev = Input.query.all()
    output = Output.query.all()
    math = Math.query.all()

    use_unit = utils_general.use_unit_generate(
        device_measurements, input_dev, output, math)

    # Display orders
    display_order_input = csv_to_list_of_str(
        DisplayOrder.query.first().inputs)
    display_order_math = csv_to_list_of_str(
        DisplayOrder.query.first().math)

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    dict_measure_measurements = {}
    dict_measure_units = {}

    for each_measurement in device_measurements:
        conversion = Conversion.query.filter(
            Conversion.unique_id == each_measurement.conversion_id).first()
        _, unit, measurement = return_measurement_info(each_measurement, conversion)
        dict_measure_measurements[each_measurement.unique_id] = measurement
        dict_measure_units[each_measurement.unique_id] = unit

    return render_template('pages/live.html',
                           and_=and_,
                           table_device_measurements=DeviceMeasurements,
                           table_input=Input,
                           table_math=Math,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           dict_measure_measurements=dict_measure_measurements,
                           dict_measure_units=dict_measure_units,
                           display_order_input=display_order_input,
                           display_order_math=display_order_math,
                           list_devices_adc=list_analog_to_digital_converters(),
                           measurement_units=MEASUREMENTS,
                           use_unit=use_unit)


@blueprint.route('/logview', methods=('GET', 'POST'))
@flask_login.login_required
def page_logview():
    """ Display the last (n) lines from a log file """
    if not utils_general.user_has_permission('view_logs'):
        return redirect(url_for('routes_general.home'))

    form_log_view = forms_misc.LogView()
    log_output = None
    lines = 30
    logfile = ''
    if request.method == 'POST':
        if form_log_view.lines.data:
            lines = form_log_view.lines.data

        if form_log_view.loglogin.data:
            logfile = LOGIN_LOG_FILE
        elif form_log_view.loghttp_access.data:
            logfile = HTTP_ACCESS_LOG_FILE
        elif form_log_view.loghttp_error.data:
            logfile = HTTP_ERROR_LOG_FILE
        elif form_log_view.logdependency.data:
            logfile = DEPENDENCY_LOG_FILE
        elif form_log_view.logdaemon.data:
            logfile = DAEMON_LOG_FILE
        elif form_log_view.logkeepup.data:
            logfile = KEEPUP_LOG_FILE
        elif form_log_view.logbackup.data:
            logfile = BACKUP_LOG_FILE
        elif form_log_view.logrestore.data:
            logfile = RESTORE_LOG_FILE
        elif form_log_view.logupgrade.data:
            logfile = UPGRADE_LOG_FILE

        # Get contents from file
        if os.path.isfile(logfile):
            command = 'tail -n {lines} {log}'.format(lines=lines,
                                                     log=logfile)
            log = subprocess.Popen(
                command, stdout=subprocess.PIPE, shell=True)
            (log_output, _) = log.communicate()
            log.wait()
            log_output = str(log_output, 'latin-1')
        else:
            log_output = 404

    return render_template('tools/logview.html',
                           form_log_view=form_log_view,
                           lines=lines,
                           logfile=logfile,
                           log_output=log_output)


@blueprint.route('/function', methods=('GET', 'POST'))
@flask_login.login_required
def page_function():
    """ Display Function settings """
    camera = Camera.query.all()
    conditional = Conditional.query.all()
    conditional_conditions = ConditionalConditions.query.all()
    function_dev = Function.query.all()
    actions = Actions.query.all()
    input_dev = Input.query.all()
    lcd = LCD.query.all()
    math = Math.query.all()
    method = Method.query.all()
    tags = NoteTags.query.all()
    output = Output.query.all()
    pid = PID.query.all()
    trigger = Trigger.query.all()
    user = User.query.all()

    display_order_function = csv_to_list_of_str(
        DisplayOrder.query.first().function)

    form_base = forms_function.DataBase()
    form_add_function = forms_function.FunctionAdd()
    form_mod_pid_base = forms_pid.PIDModBase()
    form_mod_pid_output_raise = forms_pid.PIDModRelayRaise()
    form_mod_pid_output_lower = forms_pid.PIDModRelayLower()
    form_mod_pid_pwm_raise = forms_pid.PIDModPWMRaise()
    form_mod_pid_pwm_lower = forms_pid.PIDModPWMLower()
    form_function = forms_function.FunctionMod()
    form_trigger = forms_trigger.Trigger()
    form_conditional = forms_conditional.Conditional()
    form_conditional_conditions = forms_conditional.ConditionalConditions()
    form_actions = forms_function.Actions()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        # Reorder
        if form_base.reorder.data:
            mod_order = DisplayOrder.query.first()
            mod_order.function = list_to_csv(
                form_base.list_visible_elements.data)
            db.session.commit()
            display_order_function = csv_to_list_of_str(
                DisplayOrder.query.first().function)

        # Function
        if form_add_function.func_add.data:
            utils_function.function_add(form_add_function)
        elif form_function.save_function.data:
            utils_function.function_mod(
                form_conditional)
        elif form_function.delete_function.data:
            utils_function.function_del(
                form_conditional.function_id.data)
        elif form_function.order_up.data:
            utils_function.function_reorder(
                form_conditional.function_id.data,
                display_order_function, 'up')
        elif form_function.order_down.data:
            utils_function.function_reorder(
                form_conditional.function_id.data,
                display_order_function, 'down')
        elif form_function.execute_all_actions.data:
            utils_function.action_execute_all(
                form_conditional)

        # PID
        elif form_mod_pid_base.pid_autotune.data:
            utils_pid.pid_autotune(form_mod_pid_base)
        elif form_mod_pid_base.pid_mod.data:
            utils_pid.pid_mod(form_mod_pid_base,
                              form_mod_pid_pwm_raise,
                              form_mod_pid_pwm_lower,
                              form_mod_pid_output_raise,
                              form_mod_pid_output_lower)
        elif form_mod_pid_base.pid_delete.data:
            utils_pid.pid_del(
                form_mod_pid_base.function_id.data)
        elif form_mod_pid_base.order_up.data:
            utils_function.function_reorder(
                form_mod_pid_base.function_id.data,
                display_order_function, 'up')
        elif form_mod_pid_base.order_down.data:
            utils_function.function_reorder(
                form_mod_pid_base.function_id.data,
                display_order_function, 'down')
        elif form_mod_pid_base.pid_activate.data:
            utils_pid.pid_activate(
                form_mod_pid_base.function_id.data)
        elif form_mod_pid_base.pid_deactivate.data:
            utils_pid.pid_deactivate(
                form_mod_pid_base.function_id.data)
        elif form_mod_pid_base.pid_hold.data:
            utils_pid.pid_manipulate(
                form_mod_pid_base.function_id.data, 'Hold')
        elif form_mod_pid_base.pid_pause.data:
            utils_pid.pid_manipulate(
                form_mod_pid_base.function_id.data, 'Pause')
        elif form_mod_pid_base.pid_resume.data:
            utils_pid.pid_manipulate(
                form_mod_pid_base.function_id.data, 'Resume')

        # Trigger
        elif form_trigger.save_trigger.data:
            utils_trigger.trigger_mod(
                form_trigger)
        elif form_trigger.delete_trigger.data:
            utils_trigger.trigger_del(
                form_trigger.function_id.data)
        elif form_trigger.deactivate_trigger.data:
            utils_trigger.trigger_deactivate(
                form_trigger.function_id.data)
        elif form_trigger.activate_trigger.data:
            utils_trigger.trigger_activate(
                form_trigger.function_id.data)
        elif form_trigger.order_up.data:
            utils_function.function_reorder(
                form_trigger.function_id.data,
                display_order_function, 'up')
        elif form_trigger.order_down.data:
            utils_function.function_reorder(
                form_trigger.function_id.data,
                display_order_function, 'down')
        elif form_trigger.add_action.data:
            utils_function.action_add(
                form_trigger)
        elif form_trigger.test_all_actions.data:
            utils_function.action_execute_all(
                form_trigger)

        # Conditional
        elif form_conditional.save_conditional.data:
            utils_conditional.conditional_mod(
                form_conditional)
        elif form_conditional.delete_conditional.data:
            utils_conditional.conditional_del(
                form_conditional.function_id.data)
        elif form_conditional.deactivate_cond.data:
            utils_conditional.conditional_deactivate(
                form_conditional.function_id.data)
        elif form_conditional.activate_cond.data:
            utils_conditional.conditional_activate(
                form_conditional.function_id.data)
        elif form_conditional.order_up.data:
            utils_function.function_reorder(
                form_conditional.function_id.data,
                display_order_function, 'up')
        elif form_conditional.order_down.data:
            utils_function.function_reorder(
                form_conditional.function_id.data,
                display_order_function, 'down')
        elif form_conditional.add_condition.data:
            utils_conditional.conditional_condition_add(
                form_conditional)
        elif form_conditional.add_action.data:
            utils_function.action_add(
                form_conditional)
        elif form_conditional.test_all_actions.data:
            utils_function.action_execute_all(
                form_conditional)

        # Conditional conditions
        elif form_conditional_conditions.save_condition.data:
            utils_conditional.conditional_condition_mod(
                form_conditional_conditions)
        elif form_conditional_conditions.delete_condition.data:
            utils_conditional.conditional_condition_del(
                form_conditional_conditions)

        # Actions
        elif form_actions.save_action.data:
            utils_function.action_mod(
                form_actions)
        elif form_actions.delete_action.data:
            utils_function.action_del(
                form_actions)

        return redirect(url_for('routes_page.page_function'))

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_math = utils_general.choices_maths(
        math, dict_units, dict_measurements)
    choices_pid = utils_general.choices_pids(
        pid, dict_units, dict_measurements)

    actions_dict = {
        'conditional': {},
        'trigger': {}
    }
    for each_action in actions:
        if (each_action.function_type == 'conditional' and
                each_action.unique_id not in actions_dict['conditional']):
            actions_dict['conditional'][each_action.function_id] = True
        if (each_action.function_type == 'trigger' and
                each_action.unique_id not in actions_dict['trigger']):
            actions_dict['trigger'][each_action.function_id] = True

    conditions_dict = {}
    for each_condition in conditional_conditions:
        if each_condition.unique_id not in conditions_dict:
            conditions_dict[each_condition.conditional_id] = True

    controllers = []
    controllers_all = [('Conditional', conditional),
                       ('Input', input_dev),
                       ('LCD', lcd),
                       ('Math', math),
                       ('PID', pid),
                       ('Trigger', trigger)]
    for each_controller in controllers_all:
        for each_cont in each_controller[1]:
            controllers.append((each_controller[0],
                                each_cont.unique_id,
                                each_cont.id,
                                each_cont.name))

    # Create dict of Function names
    names_function = {}
    all_elements = [conditional, pid, trigger, function_dev]
    for each_element in all_elements:
        for each_function in each_element:
            names_function[each_function.unique_id] = '[{id}] {name}'.format(
                id=each_function.unique_id.split('-')[0], name=each_function.name)

    # Calculate sunrise/sunset times if conditional controller is set up properly
    sunrise_set_calc = {}
    for each_trigger in trigger:
        if each_trigger.trigger_type == 'trigger_sunrise_sunset':
            sunrise_set_calc[each_trigger.unique_id] = {}
            try:
                sun = Sun(latitude=each_trigger.latitude,
                          longitude=each_trigger.longitude,
                          zenith=each_trigger.zenith)
                sunrise = sun.get_sunrise_time()
                sunset = sun.get_sunset_time()

                # Adjust for date offset
                new_date = datetime.datetime.now() + datetime.timedelta(
                    days=each_trigger.date_offset_days)

                sun = Sun(latitude=each_trigger.latitude,
                          longitude=each_trigger.longitude,
                          zenith=each_trigger.zenith,
                          day=new_date.day,
                          month=new_date.month,
                          year=new_date.year)
                offset_rise = sun.get_sunrise_time()
                offset_set = sun.get_sunset_time()

                # Adjust for time offset
                offset_rise = offset_rise['time_local'] + datetime.timedelta(
                    minutes=each_trigger.time_offset_minutes)
                offset_set = offset_set['time_local'] + datetime.timedelta(
                    minutes=each_trigger.time_offset_minutes)

                sunrise_set_calc[each_trigger.unique_id]['sunrise'] = (
                    sunrise['time_local'].strftime("%Y-%m-%d %H:%M"))
                sunrise_set_calc[each_trigger.unique_id]['sunset'] = (
                    sunset['time_local'].strftime("%Y-%m-%d %H:%M"))
                sunrise_set_calc[each_trigger.unique_id]['offset_sunrise'] = (
                    offset_rise.strftime("%Y-%m-%d %H:%M"))
                sunrise_set_calc[each_trigger.unique_id]['offset_sunset'] = (
                    offset_set.strftime("%Y-%m-%d %H:%M"))
            except:
                sunrise_set_calc[each_trigger.unique_id]['sunrise'] = None
                sunrise_set_calc[each_trigger.unique_id]['sunrise'] = None
                sunrise_set_calc[each_trigger.unique_id]['offset_sunrise'] = None
                sunrise_set_calc[each_trigger.unique_id]['offset_sunset'] = None

    return render_template('pages/function.html',
                           table_input=Input,
                           camera=camera,
                           choices_input=choices_input,
                           choices_math=choices_math,
                           choices_pid=choices_pid,
                           conditional_conditions_list=CONDITIONAL_CONDITIONS,
                           conditional=conditional,
                           conditional_conditions=conditional_conditions,
                           conditions_dict=conditions_dict,
                           actions=actions,
                           actions_dict=actions_dict,
                           function_dev=function_dev,
                           function_types=FUNCTION_TYPES,
                           function_actions_list=FUNCTION_ACTIONS,
                           controllers=controllers,
                           display_order_function=display_order_function,
                           form_base=form_base,
                           form_conditional=form_conditional,
                           form_conditional_conditions=form_conditional_conditions,
                           form_actions=form_actions,
                           form_add_function=form_add_function,
                           form_function=form_function,
                           form_mod_pid_base=form_mod_pid_base,
                           form_mod_pid_pwm_raise=form_mod_pid_pwm_raise,
                           form_mod_pid_pwm_lower=form_mod_pid_pwm_lower,
                           form_mod_pid_output_raise=form_mod_pid_output_raise,
                           form_mod_pid_output_lower=form_mod_pid_output_lower,
                           form_trigger=form_trigger,
                           names_function=names_function,
                           input=input_dev,
                           lcd=lcd,
                           math=math,
                           method=method,
                           output=output,
                           pid=pid,
                           tags=tags,
                           trigger=trigger,
                           units=MEASUREMENTS,
                           user=user,
                           sunrise_set_calc=sunrise_set_calc)


@blueprint.route('/output', methods=('GET', 'POST'))
@flask_login.login_required
def page_output():
    """ Display output status and config """
    camera = Camera.query.all()
    lcd = LCD.query.all()
    misc = Misc.query.first()
    output = Output.query.all()
    user = User.query.all()

    display_order_output = csv_to_list_of_str(
        DisplayOrder.query.first().output)

    form_base = forms_output.DataBase()
    form_add_output = forms_output.OutputAdd()
    form_mod_output = forms_output.OutputMod()

    if request.method == 'POST':
        unmet_dependencies = None
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_page.page_output'))

        # Reorder
        if form_base.reorder.data:
            if form_base.reorder_type.data == 'input':
                mod_order = DisplayOrder.query.first()
                mod_order.output = list_to_csv(form_base.list_visible_elements.data)
                db.session.commit()
                display_order_output = csv_to_list_of_str(DisplayOrder.query.first().output)

        if form_add_output.output_add.data:
            unmet_dependencies = utils_output.output_add(form_add_output)
        elif form_mod_output.save.data:
            utils_output.output_mod(form_mod_output)
        elif form_mod_output.delete.data:
            utils_output.output_del(form_mod_output)
        elif form_mod_output.order_up.data:
            utils_output.output_reorder(form_mod_output.output_id.data,
                                        display_order_output, 'up')
        elif form_mod_output.order_down.data:
            utils_output.output_reorder(form_mod_output.output_id.data,
                                        display_order_output, 'down')

        if unmet_dependencies:
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device=form_add_output.output_type.data.split(',')[0]))
        else:
            return redirect(url_for('routes_page.page_output'))

    # Create dict of Input names
    names_output = {}
    all_elements = output
    for each_element in all_elements:
        names_output[each_element.unique_id] = '[{id}] {name}'.format(
            id=each_element.unique_id.split('-')[0], name=each_element.name)

    # Create list of file names from the output_options directory
    # Used in generating the correct options for each output/device
    output_templates = []
    output_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/output_options')
    for (_, _, file_names) in os.walk(output_path):
        output_templates.extend(file_names)
        break

    return render_template('pages/output.html',
                           camera=camera,
                           conditional_actions_list=FUNCTION_ACTIONS,
                           display_order_output=display_order_output,
                           form_base=form_base,
                           form_add_output=form_add_output,
                           form_mod_output=form_mod_output,
                           lcd=lcd,
                           misc=misc,
                           names_output=names_output,
                           outputs=OUTPUTS,
                           output_info=OUTPUT_INFO,
                           output=output,
                           output_templates=output_templates,
                           user=user)


@blueprint.route('/data', methods=('GET', 'POST'))
@flask_login.login_required
def page_data():
    """ Display Data page """
    pid = PID.query.all()
    output = Output.query.all()
    input_dev = Input.query.all()
    math = Math.query.all()
    user = User.query.all()
    measurement = Measurement.query.all()
    unit = Unit.query.all()

    display_order_input = csv_to_list_of_str(DisplayOrder.query.first().inputs)
    display_order_math = csv_to_list_of_str(DisplayOrder.query.first().math)

    form_base = forms_input.DataBase()

    form_add_input = forms_input.InputAdd()
    form_mod_input = forms_input.InputMod()
    form_mod_input_measurement = forms_input.InputMeasurementMod()

    form_add_math = forms_math.MathAdd()
    form_mod_math = forms_math.MathMod()
    form_mod_math_measurement = forms_math.MathMeasurementMod()
    form_mod_average_single = forms_math.MathModAverageSingle()
    form_mod_redundancy = forms_math.MathModRedundancy()
    form_mod_difference = forms_math.MathModDifference()
    form_mod_equation = forms_math.MathModEquation()
    form_mod_humidity = forms_math.MathModHumidity()
    form_mod_verification = forms_math.MathModVerification()
    form_mod_misc = forms_math.MathModMisc()

    if request.method == 'POST':
        unmet_dependencies = None
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_page.page_data'))

        # Reorder
        if form_base.reorder.data:
            if form_base.reorder_type.data == 'input':
                mod_order = DisplayOrder.query.first()
                mod_order.inputs = list_to_csv(form_base.list_visible_elements.data)
                db.session.commit()
                display_order_input = csv_to_list_of_str(DisplayOrder.query.first().inputs)
            elif form_base.reorder_type.data == 'math':
                mod_order = DisplayOrder.query.first()
                mod_order.math = list_to_csv(form_base.list_visible_elements.data)
                db.session.commit()
                display_order_math = csv_to_list_of_str(DisplayOrder.query.first().math)

        # Misc Input
        if form_mod_input.input_acquire_measurements.data:
            utils_input.force_acquire_measurements(form_mod_input.input_id.data)

        # Add Input
        elif form_add_input.input_add.data:
            unmet_dependencies = utils_input.input_add(form_add_input)

        # Mod Input Measurement
        elif form_mod_input_measurement.input_measurement_mod.data:
            utils_input.measurement_mod(form_mod_input_measurement)

        # Mod other Input settings
        elif form_mod_input.input_mod.data:
            utils_input.input_mod(form_mod_input, request.form)
        elif form_mod_input.input_delete.data:
            utils_input.input_del(form_mod_input.input_id.data)
        elif form_mod_input.input_order_up.data:
            utils_input.input_reorder(form_mod_input.input_id.data,
                                      display_order_input, 'up')
        elif form_mod_input.input_order_down.data:
            utils_input.input_reorder(form_mod_input.input_id.data,
                                      display_order_input, 'down')
        elif form_mod_input.input_activate.data:
            utils_input.input_activate(form_mod_input)
        elif form_mod_input.input_deactivate.data:
            utils_input.input_deactivate(form_mod_input)

        # Add Math
        elif form_add_math.math_add.data:
            unmet_dependencies = utils_math.math_add(form_add_math)

        # Mod Math Measurement
        elif form_mod_math_measurement.math_measurement_mod.data:
            utils_math.math_measurement_mod(form_mod_math_measurement)

        # Mod other Math settings
        elif form_mod_math.math_mod.data:
            math_type = Math.query.filter(
                Math.unique_id == form_mod_math.math_id.data).first().math_type
            if math_type == 'humidity':
                utils_math.math_mod(form_mod_math, form_mod_humidity)
            elif math_type == 'average_single':
                utils_math.math_mod(form_mod_math, form_mod_average_single)
            elif math_type == 'redundancy':
                utils_math.math_mod(form_mod_math, form_mod_redundancy)
            elif math_type == 'difference':
                utils_math.math_mod(form_mod_math, form_mod_difference)
            elif math_type == 'equation':
                utils_math.math_mod(form_mod_math, form_mod_equation)
            elif math_type == 'verification':
                utils_math.math_mod(form_mod_math, form_mod_verification)
            elif math_type == 'vapor_pressure_deficit':
                utils_math.math_mod(form_mod_math, form_mod_misc)
            else:
                utils_math.math_mod(form_mod_math)
        elif form_mod_math.math_delete.data:
            utils_math.math_del(form_mod_math)
        elif form_mod_math.math_order_up.data:
            utils_math.math_reorder(form_mod_math.math_id.data,
                                    display_order_math, 'up')
        elif form_mod_math.math_order_down.data:
            utils_math.math_reorder(form_mod_math.math_id.data,
                                    display_order_math, 'down')
        elif form_mod_math.math_activate.data:
            utils_math.math_activate(form_mod_math)
        elif form_mod_math.math_deactivate.data:
            utils_math.math_deactivate(form_mod_math)

        if unmet_dependencies:
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device=form_add_input.input_type.data.split(',')[0]))
        else:
            return redirect(url_for('routes_page.page_data'))

    dict_inputs = parse_input_information()
    custom_options_values = parse_custom_option_values(input_dev)

    # Generate dict that incorporate user-added measurements/units
    dict_units = add_custom_units(unit)
    dict_measurements = add_custom_measurements(measurement)

    # Create list of choices to be used in dropdown menus
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_math = utils_general.choices_maths(
        math, dict_units, dict_measurements)
    choices_output = utils_general.choices_outputs(
        output, dict_units, dict_measurements)
    choices_unit = utils_general.choices_units(unit)
    choices_measurement = utils_general.choices_measurements(measurement)
    choices_measurements_units = utils_general.choices_measurements_units(measurement, unit)

    # Create dict of Input names
    names_input = {}
    all_elements = input_dev
    for each_element in all_elements:
        names_input[each_element.unique_id] = '[{id}] {name}'.format(
            id=each_element.unique_id.split('-')[0], name=each_element.name)

    # Create dict of Math names
    names_math = {}
    all_elements = math
    for each_element in all_elements:
        names_math[each_element.unique_id] = '[{id}] {name}'.format(
            id=each_element.unique_id.split('-')[0], name=each_element.name)

    # Create list of file names from the math_options directory
    # Used in generating the correct options for each math controller
    math_templates = []
    math_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/data_options/math_options')
    for (_, _, file_names) in os.walk(math_path):
        math_templates.extend(file_names)
        break

    # Create list of file names from the input_options directory
    # Used in generating the correct options for each input controller
    input_templates = []
    input_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/data_options/input_options')
    for (_, _, file_names) in os.walk(input_path):
        input_templates.extend(file_names)
        break

    # If DS18B20 inputs added, compile a list of detected inputs
    devices_1wire_w1thermsensor = []
    if os.path.isdir(PATH_1WIRE):
        for each_name in os.listdir(PATH_1WIRE):
            if 'bus' not in each_name and '-' in each_name:
                devices_1wire_w1thermsensor.append(each_name.split('-')[1])

    # Add 1-wire devices from ow-shell (if installed)
    devices_1wire_ow_shell = []
    if not dpkg_package_exists('ow-shell'):
        logger.debug("Package 'ow-shell' not found")
    else:
        logger.debug("Package 'ow-shell' found")
        try:
            test_cmd = subprocess.check_output(['owdir']).splitlines()
            for each_ow in test_cmd:
                str_ow = re.sub("\ |\/|\'", "", each_ow.decode("utf-8"))  # Strip / and '
                if '.' in str_ow and len(str_ow) == 15:
                    devices_1wire_ow_shell.append(str_ow)
        except Exception:
            logger.exception("Error finding 1-wire devices with 'owdir'")

    return render_template('pages/data.html',
                           and_=and_,
                           choices_input=choices_input,
                           choices_math=choices_math,
                           choices_output=choices_output,
                           choices_measurement=choices_measurement,
                           choices_measurements_units=choices_measurements_units,
                           choices_unit=choices_unit,
                           custom_options_values=custom_options_values,
                           device_info=parse_input_information(),
                           dict_inputs=dict_inputs,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           display_order_input=display_order_input,
                           display_order_math=display_order_math,
                           form_base=form_base,
                           form_add_input=form_add_input,
                           form_add_math=form_add_math,
                           form_mod_input=form_mod_input,
                           form_mod_input_measurement=form_mod_input_measurement,
                           form_mod_average_single=form_mod_average_single,
                           form_mod_redundancy=form_mod_redundancy,
                           form_mod_difference=form_mod_difference,
                           form_mod_equation=form_mod_equation,
                           form_mod_humidity=form_mod_humidity,
                           form_mod_math=form_mod_math,
                           form_mod_math_measurement=form_mod_math_measurement,
                           form_mod_verification=form_mod_verification,
                           form_mod_misc=form_mod_misc,
                           input_templates=input_templates,
                           math_info=MATH_INFO,
                           math_templates=math_templates,
                           names_input=names_input,
                           names_math=names_math,
                           output=output,
                           pid=pid,
                           table_conversion=Conversion,
                           table_device_measurements=DeviceMeasurements,
                           table_input=Input,
                           table_math=Math,
                           user=user,
                           devices_1wire_ow_shell=devices_1wire_ow_shell,
                           devices_1wire_w1thermsensor=devices_1wire_w1thermsensor)


@blueprint.route('/usage', methods=('GET', 'POST'))
@flask_login.login_required
def page_usage():
    """ Display output usage (duration and energy usage/cost) """
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('routes_general.home'))

    calculate_pass = False
    energy_usage_stats = {}

    form_energy_usage_add = forms_misc.EnergyUsageAdd()
    form_energy_usage_mod = forms_misc.EnergyUsageMod()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_page.page_usage'))

        if form_energy_usage_add.energy_usage_add.data:
            utils_misc.energy_usage_add(form_energy_usage_add)
        elif form_energy_usage_mod.energy_usage_mod.data:
            utils_misc.energy_usage_mod(form_energy_usage_mod)
        elif form_energy_usage_mod.energy_usage_delete.data:
            utils_misc.energy_usage_delete(
                form_energy_usage_mod.energy_usage_id.data)
        elif form_energy_usage_mod.energy_usage_range_calc.data:
            calculate_pass = True

        if not calculate_pass:
            return redirect(url_for('routes_page.page_usage'))

    energy_usage = EnergyUsage.query.all()
    input_dev = Input.query.all()
    math = Math.query.all()
    misc = Misc.query.first()
    output = Output.query.all()

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_math = utils_general.choices_maths(
        math, dict_units, dict_measurements)

    graph_info = {}

    # calculate energy usage from Inputs/Maths measuring amps
    for each_energy in energy_usage:
        graph_info[each_energy.unique_id] = {}
        energy_usage_stats[each_energy.unique_id] = {}
        energy_usage_stats[each_energy.unique_id]['hour'] = 0
        energy_usage_stats[each_energy.unique_id]['day'] = 0
        energy_usage_stats[each_energy.unique_id]['week'] = 0
        energy_usage_stats[each_energy.unique_id]['month'] = 0

        device_measurement = DeviceMeasurements.query.filter(
            DeviceMeasurements.unique_id == each_energy.measurement_id).first()
        if device_measurement:
            conversion = Conversion.query.filter(
                Conversion.unique_id == device_measurement.conversion_id).first()
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        graph_info[each_energy.unique_id]['main'] = {}
        graph_info[each_energy.unique_id]['main']['device_id'] = each_energy.device_id
        graph_info[each_energy.unique_id]['main']['measurement_id'] = each_energy.measurement_id
        graph_info[each_energy.unique_id]['main']['channel'] = channel
        graph_info[each_energy.unique_id]['main']['unit'] = unit
        graph_info[each_energy.unique_id]['main']['measurement'] = measurement
        graph_info[each_energy.unique_id]['main']['start_time_epoch'] = (
            datetime.datetime.now() -
            datetime.timedelta(seconds=2629800)).strftime('%s')

        if unit == 'A':  # If unit is amps, proceed
            hour = average_past_seconds(
                each_energy.device_id, unit, channel, 3600,
                measure=measurement)
            if hour:
                energy_usage_stats[each_energy.unique_id]['hour'] = hour
            day = average_past_seconds(
                each_energy.device_id, unit, channel, 86400,
                measure=measurement)
            if day:
                energy_usage_stats[each_energy.unique_id]['day'] = day
            week = average_past_seconds(
                each_energy.device_id, unit, channel, 604800,
                measure=measurement)
            if week:
                energy_usage_stats[each_energy.unique_id]['week'] = week
            month = average_past_seconds(
                each_energy.device_id, unit, channel, 2629800,
                measure=measurement)
            if month:
                energy_usage_stats[each_energy.unique_id]['month'] = month

    output_stats = return_output_usage(misc, output)

    day = misc.output_usage_dayofmonth
    if 4 <= day <= 20 or 24 <= day <= 30:
        date_suffix = 'th'
    else:
        date_suffix = ['st', 'nd', 'rd'][day % 10 - 1]

    display_order = csv_to_list_of_str(DisplayOrder.query.first().output)

    calculate_usage = {}
    picker_start = {}
    picker_end = {}
    if calculate_pass:
        str_start = form_energy_usage_mod.energy_usage_date_range.data.split(' - ')[0]
        start_seconds = int(time.mktime(
            time.strptime(str_start, '%m/%d/%Y %H:%M')))
        str_end = form_energy_usage_mod.energy_usage_date_range.data.split(' - ')[1]
        end_seconds = int(time.mktime(
            time.strptime(str_end, '%m/%d/%Y %H:%M')))

        utc_offset_timedelta = datetime.datetime.utcnow() - datetime.datetime.now()
        start = datetime.datetime.fromtimestamp(float(start_seconds))
        start += utc_offset_timedelta
        start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.datetime.fromtimestamp(float(end_seconds))
        end += utc_offset_timedelta
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        energy_device = EnergyUsage.query.filter(
            EnergyUsage.unique_id == form_energy_usage_mod.energy_usage_id.data).first()
        device_measurement = DeviceMeasurements.query.filter(
            DeviceMeasurements.unique_id == energy_device.measurement_id).first()
        if device_measurement:
            conversion = Conversion.query.filter(
                Conversion.unique_id == device_measurement.conversion_id).first()
        else:
            conversion = None
        channel, unit, measurement = return_measurement_info(
            device_measurement, conversion)

        picker_start[energy_device.unique_id] = form_energy_usage_mod.energy_usage_date_range.data.split(' - ')[0]
        picker_end[energy_device.unique_id] = form_energy_usage_mod.energy_usage_date_range.data.split(' - ')[1]

        graph_info[energy_device.unique_id]['calculate'] = {}
        graph_info[energy_device.unique_id]['calculate']['device_id'] = energy_device.device_id
        graph_info[energy_device.unique_id]['calculate']['measurement_id'] = energy_device.measurement_id
        graph_info[energy_device.unique_id]['calculate']['channel'] = channel
        graph_info[energy_device.unique_id]['calculate']['unit'] = unit
        graph_info[energy_device.unique_id]['calculate']['measurement'] = measurement
        graph_info[energy_device.unique_id]['calculate']['start_time_epoch'] = start_seconds
        graph_info[energy_device.unique_id]['calculate']['end_time_epoch'] = end_seconds

        calculate_usage[energy_device.unique_id] = {}
        calculate_usage[energy_device.unique_id]['average_amps'] = 0
        calculate_usage[energy_device.unique_id]['kwh'] = 0

        average_amps = average_start_end_seconds(
            energy_device.device_id,
            unit,
            channel,
            start_str,
            end_str,
            measure=measurement)

        calculate_usage[energy_device.unique_id]['average_amps'] = 0
        calculate_usage[energy_device.unique_id]['kwh'] = 0
        calculate_usage[energy_device.unique_id]['hours'] = 0
        if average_amps:
            calculate_usage[energy_device.unique_id]['average_amps'] = average_amps
            hours = ((end_seconds - start_seconds) / 3600)
            if hours < 1:
                hours = 1
            calculate_usage[energy_device.unique_id]['kwh'] = misc.output_usage_volts * average_amps / 1000 * hours
            calculate_usage[energy_device.unique_id]['hours'] = hours

    picker_end['default'] = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
    picker_start['default'] = datetime.datetime.now() - datetime.timedelta(hours=6)
    picker_start['default'] = picker_start['default'].strftime('%m/%d/%Y %H:%M')

    return render_template('pages/usage.html',
                           calculate_usage=calculate_usage,
                           choices_input=choices_input,
                           choices_math=choices_math,
                           date_suffix=date_suffix,
                           display_order=display_order,
                           energy_usage=energy_usage,
                           energy_usage_stats=energy_usage_stats,
                           form_energy_usage_add=form_energy_usage_add,
                           form_energy_usage_mod=form_energy_usage_mod,
                           graph_info=graph_info,
                           misc=misc,
                           output=output,
                           output_stats=output_stats,
                           picker_end=picker_end,
                           picker_start=picker_start,
                           timestamp=time.strftime("%c"))


@blueprint.route('/usage_reports')
@flask_login.login_required
def page_usage_reports():
    """ Display output usage (duration and energy usage/cost) """
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('routes_general.home'))

    report_location = os.path.normpath(USAGE_REPORTS_PATH)
    reports = [0, 0]

    return render_template('pages/usage_reports.html',
                           report_location=report_location,
                           reports=reports)


def dict_custom_colors():
    """
    Generate a dictionary of custom colors from CSV strings saved in the
    database. If custom colors aren't already saved, fill in with a default
    palette.

    :return: dictionary of graph_ids and lists of custom colors
    """
    dark_themes = ['cyborg', 'darkly', 'slate', 'sun', 'superhero']
    if flask_login.current_user.theme in dark_themes:
        default_palette = [
            '#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066',
            '#eeaaee', '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'
        ]
    else:
        default_palette = [
            '#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9', '#f15c80',
            '#e4d354', '#2b908f', '#f45b5b', '#91e8e1'
        ]

    color_count = OrderedDict()
    try:
        graph = Dashboard.query.all()
        for each_graph in graph:
            # Get current saved colors
            if each_graph.custom_colors:  # Split into list
                colors = each_graph.custom_colors.split(',')
            else:  # Create empty list
                colors = []
            # Fill end of list with empty strings
            while len(colors) < len(default_palette):
                colors.append('')

            # Populate empty strings with default colors
            for x, _ in enumerate(default_palette):
                if colors[x] == '':
                    colors[x] = default_palette[x]

            index = 0
            index_sum = 0
            total = []
            if each_graph.input_ids_measurements:
                for each_set in each_graph.input_ids_measurements.split(';'):
                    input_unique_id = each_set.split(',')[0]
                    input_measure_id = each_set.split(',')[1]

                    device_measurement = DeviceMeasurements.query.filter(
                        DeviceMeasurements.unique_id == input_measure_id).first()
                    if device_measurement:
                        conversion = Conversion.query.filter(
                            Conversion.unique_id == device_measurement.conversion_id).first()
                    else:
                        conversion = None
                    channel, unit, measurement = return_measurement_info(
                        device_measurement, conversion)

                    input_dev = Input.query.filter_by(
                        unique_id=input_unique_id).first()
                    if (index < len(each_graph.input_ids_measurements.split(';')) and
                            len(colors) > index):
                        color = colors[index]
                    else:
                        color = '#FF00AA'
                    if None not in [input_dev, device_measurement]:
                        total.append({
                            'unique_id': input_unique_id,
                            'name': input_dev.name,
                            'channel': channel,
                            'unit': unit,
                            'measure': measurement,
                            'measure_name': device_measurement.name,
                            'color': color})
                        index += 1
                index_sum += index

            if each_graph.math_ids:
                index = 0
                for each_set in each_graph.math_ids.split(';'):
                    math_unique_id = each_set.split(',')[0]
                    math_measure_id = each_set.split(',')[1]

                    device_measurement = DeviceMeasurements.query.filter(
                        DeviceMeasurements.unique_id == math_measure_id).first()
                    if device_measurement:
                        conversion = Conversion.query.filter(
                            Conversion.unique_id == device_measurement.conversion_id).first()
                    else:
                        conversion = None
                    channel, unit, measurement = return_measurement_info(
                        device_measurement, conversion)

                    math = Math.query.filter_by(
                        unique_id=math_unique_id).first()
                    if (index < len(each_graph.math_ids.split(';')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum + index]
                    else:
                        color = '#FF00AA'
                    if math is not None:
                        total.append({
                            'unique_id': math_unique_id,
                            'name': math.name,
                            'channel': channel,
                            'unit': unit,
                            'measure': measurement,
                            'measure_name': device_measurement.name,
                            'color': color})
                        index += 1
                index_sum += index

            if each_graph.pid_ids:
                index = 0
                for each_set in each_graph.pid_ids.split(';'):
                    pid_unique_id = each_set.split(',')[0]
                    pid_measure_id = each_set.split(',')[1]

                    device_measurement = DeviceMeasurements.query.filter(
                        DeviceMeasurements.unique_id == pid_measure_id).first()
                    if device_measurement:
                        conversion = Conversion.query.filter(
                            Conversion.unique_id == device_measurement.conversion_id).first()
                    else:
                        conversion = None
                    channel, unit, measurement = return_measurement_info(
                        device_measurement, conversion)

                    pid = PID.query.filter_by(
                        unique_id=pid_unique_id).first()
                    if (index < len(each_graph.pid_ids.split(';')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum + index]
                    else:
                        color = '#FF00AA'
                    if pid is not None:
                        total.append({
                            'unique_id': pid_unique_id,
                            'name': pid.name,
                            'channel': channel,
                            'unit': unit,
                            'measure': measurement,
                            'color': color})
                        index += 1

            if each_graph.output_ids:
                index = 0
                for each_set in each_graph.output_ids.split(';'):
                    output_unique_id = each_set.split(',')[0]

                    device_measurement = Output.query.filter_by(
                        unique_id=output_unique_id).first()
                    if device_measurement:
                        conversion = Conversion.query.filter(
                            Conversion.unique_id == device_measurement.conversion_id).first()
                    else:
                        conversion = None
                    channel, unit, measurement = return_measurement_info(
                        device_measurement, conversion)

                    if (index < len(each_graph.output_ids.split(',')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum + index]
                    else:
                        color = '#FF00AA'
                    if device_measurement is not None:
                        total.append({
                            'unique_id': output_unique_id,
                            'name': device_measurement.name,
                            'channel': channel,
                            'unit': unit,
                            'measure': measurement,
                            'color': color})
                        index += 1
                index_sum += index

            color_count.update({each_graph.unique_id: total})
    except IndexError:
        pass

    return color_count


def dict_custom_yaxes_min_max(graph, yaxes):
    """
    Generate a dictionary of the y-axis minimum and maximum for each graph
    :param graph: iterable SQL object of all graph entries
    :param yaxes: list of y-axis measurements
    :return: dictionary of minimum and maximum y-axis values for each graph
    """
    dict_yaxes = {}
    for each_graph in graph:
        dict_yaxes[each_graph.unique_id] = {}

        if each_graph.unique_id in yaxes:
            for each_yaxis in yaxes[each_graph.unique_id]:
                dict_yaxes[each_graph.unique_id][each_yaxis] = {}
                dict_yaxes[each_graph.unique_id][each_yaxis]['minimum'] = 0
                dict_yaxes[each_graph.unique_id][each_yaxis]['maximum'] = 0

                for each_custom_yaxis in each_graph.custom_yaxes.split(';'):
                    if each_custom_yaxis.split(',')[0] == each_yaxis:
                        dict_yaxes[each_graph.unique_id][each_yaxis]['minimum'] = each_custom_yaxis.split(',')[1]
                        dict_yaxes[each_graph.unique_id][each_yaxis]['maximum'] = each_custom_yaxis.split(',')[2]

    return dict_yaxes


def gen(camera):
    """ Video streaming generator function """
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
