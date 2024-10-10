# coding=utf-8
"""collection of Page endpoints."""
import calendar
import datetime
import glob
import logging
import os
import resource
import socket
import subprocess
import sys
import time
from collections import OrderedDict
from importlib import import_module

import flask_login
from flask import (current_app, flash, jsonify, redirect, render_template,
                   request, send_file, url_for)
from flask.blueprints import Blueprint
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.config import (ALEMBIC_VERSION, BACKUP_LOG_FILE, CAMERA_INFO,
                           DAEMON_LOG_FILE,
                           DEPENDENCY_LOG_FILE, DOCKER_CONTAINER,
                           FRONTEND_PID_FILE, HTTP_ACCESS_LOG_FILE,
                           HTTP_ERROR_LOG_FILE, IMPORT_LOG_FILE,
                           KEEPUP_LOG_FILE, LOGIN_LOG_FILE, MYCODO_DB_PATH,
                           MYCODO_VERSION, RESTORE_LOG_FILE, THEMES_DARK,
                           UPGRADE_LOG_FILE)
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.databases.models import (PID, AlembicVersion, Camera, Conversion,
                                     CustomController, DeviceMeasurements,
                                     DisplayOrder, EnergyUsage, Input,
                                     Measurement, Misc, Notes, NoteTags,
                                     Output, OutputChannel, Unit, Widget)
from mycodo.devices.camera import camera_record
from mycodo.mycodo_client import DaemonControl, daemon_active
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.forms import forms_camera, forms_misc, forms_notes
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import (utils_camera, utils_dashboard,
                                       utils_export, utils_general, utils_misc,
                                       utils_notes)
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.functions import parse_function_information
from mycodo.utils.inputs import (list_analog_to_digital_converters,
                                 parse_input_information)
from mycodo.utils.outputs import output_types, parse_output_information
from mycodo.utils.system_pi import (
    add_custom_measurements, add_custom_units, csv_to_list_of_str,
    parse_custom_option_values,
    parse_custom_option_values_output_channels_json, return_measurement_info)
from mycodo.utils.tools import (calc_energy_usage, return_energy_usage,
                                return_output_usage)

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
@flask_login.login_required
def inject_functions():
    def epoch_to_time_string(epoch):
        try:
            return datetime.datetime.fromtimestamp(epoch).strftime(
                "%Y-%m-%d %H:%M:%S")
        except:
            return "EPOCH ERROR"

    def get_note_tag_from_unique_id(tag_unique_id):
        tag = NoteTags.query.filter(NoteTags.unique_id == tag_unique_id).first()
        if tag and tag.name:
            return tag.name
        else:
            return 'TAG ERROR'

    def utc_to_local_time(utc_dt):
        try:
            utc_timestamp = calendar.timegm(utc_dt.timetuple())
            return str(datetime.datetime.fromtimestamp(utc_timestamp))
        except:
            return "TIMESTAMP ERROR"

    return dict(epoch_to_time_string=epoch_to_time_string,
                get_note_tag_from_unique_id=get_note_tag_from_unique_id,
                utc_to_local_time=utc_to_local_time)


@blueprint.route('/camera_submit', methods=['POST'])
@flask_login.login_required
def page_camera_submit():
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    page_refresh = False
    dep_unmet = None

    form_camera = forms_camera.Camera()

    if not utils_general.user_has_permission('edit_controllers'):
        messages["error"].append("Your permissions do not allow this action")

    if not messages["error"]:
        if form_camera.camera_mod.data:
            messages = utils_camera.camera_mod(form_camera)
        elif form_camera.camera_del.data:
            messages = utils_camera.camera_del(form_camera)
        elif form_camera.timelapse_generate.data:
            messages = utils_camera.camera_timelapse_video(form_camera)
        else:
            messages["error"].append("Unknown camera directive")

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
        'camera_id': form_camera.camera_id.data,
        'dep_unmet': dep_unmet,
        'messages': messages,
        'page_refresh': page_refresh
    })


@blueprint.route('/camera', methods=('GET', 'POST'))
@flask_login.login_required
def page_camera():
    """
    Page to start/stop video stream or time-lapse, or capture a still image.
    Displays most recent still image and time-lapse image.
    """
    if not utils_general.user_has_permission('view_camera'):
        return redirect(url_for('routes_general.home'))

    form_camera = forms_camera.Camera()

    camera = Camera.query.all()
    misc = Misc.query.first()
    output = Output.query.all()
    output_channel = OutputChannel.query.all()

    opencv_devices = []

    for each_cam in camera:
        if each_cam.library == 'opencv':
            try:
                from mycodo.devices.camera import count_cameras_opencv
                opencv_devices = count_cameras_opencv()
            except Exception:
                opencv_devices = []
            break

    if request.method == 'POST':
        unmet_dependencies = None
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_page.page_camera'))

        mod_camera = Camera.query.filter(
            Camera.unique_id == form_camera.camera_id.data).first()
        if form_camera.camera_add.data:
            unmet_dependencies = utils_camera.camera_add(form_camera)
        elif form_camera.capture_still.data:
            # If a stream is active, stop the stream to take a photo
            if mod_camera.stream_started:
                try:
                    camera_stream = import_module(
                        'mycodo.mycodo_flask.camera.camera_{lib}'.format(
                            lib=mod_camera.library)).Camera
                    if camera_stream(unique_id=mod_camera.unique_id).is_running(mod_camera.unique_id):
                        camera_stream(unique_id=mod_camera.unique_id).stop(mod_camera.unique_id)
                    time.sleep(2)
                except Exception as err:
                    flash(f"Error stopping stream: {err}", "error")
            path, filename = camera_record('photo', mod_camera.unique_id)
            if not path and not filename:
                msg = "Could not acquire image."
                flash(msg, "error")
                logger.error(msg)
        elif form_camera.start_timelapse.data:
            error = []
            if mod_camera.stream_started:
                error.append("Cannot start time-lapse if stream is active.")
            if form_camera.timelapse_runtime_sec.data is None or form_camera.timelapse_runtime_sec.data < 0:
                error.append("Must enter Run Time.")
            if not form_camera.timelapse_interval.data:
                error.append("Must enter Interval.")
            if error:
                for each_err in error:
                    flash(each_err, "error")
                return redirect(url_for('routes_page.page_camera'))

            now = time.time()
            mod_camera.timelapse_started = True
            mod_camera.timelapse_start_time = now
            timelapse_runtime_sec = float(form_camera.timelapse_runtime_sec.data)
            if form_camera.timelapse_runtime_sec.data and timelapse_runtime_sec < 315600000:
                mod_camera.timelapse_end_time = now + timelapse_runtime_sec
            elif form_camera.timelapse_runtime_sec.data == 0:  # Run forever (10 years)
                mod_camera.timelapse_end_time = now + 315600000
            mod_camera.timelapse_interval = form_camera.timelapse_interval.data
            mod_camera.timelapse_next_capture = now
            mod_camera.timelapse_capture_number = 0
            db.session.commit()
        elif form_camera.pause_timelapse.data:
            mod_camera.timelapse_paused = True
            db.session.commit()
        elif form_camera.resume_timelapse.data:
            mod_camera.timelapse_paused = False
            db.session.commit()
        elif form_camera.stop_timelapse.data:
            mod_camera.timelapse_started = False
            mod_camera.timelapse_start_time = None
            mod_camera.timelapse_end_time = None
            mod_camera.timelapse_interval = None
            mod_camera.timelapse_next_capture = None
            mod_camera.timelapse_capture_number = None
            db.session.commit()
        elif form_camera.start_stream.data:
            if mod_camera.timelapse_started:
                flash(gettext(
                    "Cannot start stream if time-lapse is active."), "error")
                return redirect(url_for('routes_page.page_camera'))
            else:
                mod_camera.stream_started = True
                db.session.commit()
        elif form_camera.stop_stream.data:
            try:
                camera_stream = import_module(
                    'mycodo.mycodo_flask.camera.camera_{lib}'.format(
                        lib=mod_camera.library)).Camera
                if camera_stream(unique_id=mod_camera.unique_id).is_running(mod_camera.unique_id):
                    camera_stream(unique_id=mod_camera.unique_id).stop(mod_camera.unique_id)
            except Exception as err:
                flash(f"Error stopping stream: {err}", "error")
            mod_camera.stream_started = False
            db.session.commit()

        if unmet_dependencies:
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device=form_camera.library.data))
        else:
            return redirect(url_for('routes_page.page_camera'))

    # Get the full path and timestamps of the latest still and time-lapse images
    (latest_img_still_ts,
     latest_img_still_size,
     latest_img_still,
     latest_img_tl_ts,
     latest_img_tl_size,
     latest_img_tl,
     time_lapse_imgs) = utils_general.get_camera_image_info()

    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    dict_outputs = parse_output_information()
    choices_output_channels = utils_general.choices_outputs_channels(
        output, output_channel, dict_outputs)

    return render_template('pages/camera.html',
                           camera=camera,
                           camera_info=CAMERA_INFO,
                           choices_output_channels=choices_output_channels,
                           form_camera=form_camera,
                           latest_img_still=latest_img_still,
                           latest_img_still_ts=latest_img_still_ts,
                           latest_img_still_size=latest_img_still_size,
                           latest_img_tl=latest_img_tl,
                           latest_img_tl_ts=latest_img_tl_ts,
                           latest_img_tl_size=latest_img_tl_size,
                           misc=misc,
                           opencv_devices=opencv_devices,
                           output=output,
                           time_lapse_imgs=time_lapse_imgs,
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
                    download_name=
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

    function = CustomController.query.all()
    input_dev = Input.query.all()
    output = Output.query.all()

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    dict_outputs = parse_output_information()

    choices_function = utils_general.choices_functions(
        function, dict_units, dict_measurements)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_output = utils_general.choices_outputs(
        output, OutputChannel, dict_outputs, dict_units, dict_measurements)

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_general.home'))

        if form_export_measurements.export_data_csv.data:
            url = utils_export.export_measurements(form_export_measurements)
            if url:
                return redirect(url)
        elif form_export_settings.export_settings_zip.data:
            file_send = utils_export.export_settings()
            if file_send:
                return file_send
            else:
                flash('Unknown error creating zipped settings database',
                      'error')
        elif form_import_settings.settings_import_upload.data:
            restore_success = utils_export.import_settings(form_import_settings)
            if restore_success:
                return redirect(url_for('routes_authentication.logout'))
            else:
                flash('An error occurred during the settings import.',
                      'error')
        elif form_export_influxdb.export_influxdb_zip.data:
            file_send = utils_export.export_influxdb()
            if file_send:
                return file_send
            else:
                flash('Unknown error creating zipped influxdb database '
                      'and metastore', 'error')

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
                           form_import_settings=form_import_settings,
                           choices_function=choices_function,
                           choices_input=choices_input,
                           choices_output=choices_output)


@blueprint.route('/graph-async', methods=('GET', 'POST'))
@flask_login.login_required
def page_graph_async():
    """Generate graphs using asynchronous data retrieval."""
    if not current_app.config['TESTING']:
        dep_unmet, _, _ = return_dependencies('highstock')
        if dep_unmet:
            return redirect(url_for('routes_admin.admin_dependencies',
                                    device='highstock'))

    function = CustomController.query.all()
    input_dev = Input.query.all()
    device_measurements = DeviceMeasurements.query.all()
    output = Output.query.all()
    pid = PID.query.all()
    tag = NoteTags.query.all()

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    # Get what each measurement uses for a unit
    use_unit = utils_general.use_unit_generate(
        device_measurements, input_dev, output, function)

    dict_outputs = parse_output_information()

    choices_function = utils_general.choices_functions(
        function, dict_units, dict_measurements)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)
    choices_output = utils_general.choices_outputs(
        output, OutputChannel, dict_outputs, dict_units, dict_measurements)
    choices_pid = utils_general.choices_pids(
        pid, dict_units, dict_measurements)
    choices_tag = utils_general.choices_tags(tag)

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
                           function=function,
                           output=output,
                           pid=pid,
                           tag=tag,
                           choices_input=choices_input,
                           choices_function=choices_function,
                           choices_output=choices_output,
                           choices_pid=choices_pid,
                           choices_tag=choices_tag,
                           selected_ids_measures=selected_ids_measures,
                           y_axes=y_axes)


@blueprint.route('/info', methods=('GET', 'POST'))
@flask_login.login_required
def page_info():
    """Display page with system information from command line tools."""
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('routes_general.home'))

    virtualenv_flask = False
    virtualenv_daemon = False
    top_daemon_output = None
    frontend_pid = None
    pstree_frontend_output = None
    top_frontend_output = None

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

    if not current_app.config['TESTING']:
        gpio = subprocess.Popen(
            "gpio readall", stdout=subprocess.PIPE, shell=True)
        (gpio_output, _) = gpio.communicate()
        gpio.wait()
        if gpio_output:
            gpio_output = gpio_output.decode("latin1")
    else:
        gpio_output = ''

    # Search for /dev/i2c- devices and compile a sorted dictionary of each
    # device's integer device number and the corresponding 'i2cdetect -y ID'
    # output for display on the info page
    i2c_devices_sorted = OrderedDict()
    if not current_app.config['TESTING']:
        try:
            i2c_devices = glob.glob("/dev/i2c-*")
            for each_dev in i2c_devices:
                device_int = int(each_dev.replace("/dev/i2c-", ""))
                if device_int in [20, 21]:
                    continue
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

    dmesg = subprocess.Popen(
        "dmesg | tail -n 20", stdout=subprocess.PIPE, shell=True)
    (dmesg_output, _) = dmesg.communicate()
    dmesg.wait()
    if dmesg_output:
        dmesg_output = dmesg_output.decode("latin1")

    ifconfig = subprocess.Popen(
        "ifconfig -a", stdout=subprocess.PIPE, shell=True)
    (ifconfig_output, _) = ifconfig.communicate()
    ifconfig.wait()
    if ifconfig_output:
        ifconfig_output = ifconfig_output.decode("latin1")

    database_version = AlembicVersion.query.first().version_num
    correct_database_version = ALEMBIC_VERSION

    if hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix:
        virtualenv_flask = True

    if not current_app.config['TESTING']:
        daemon_up = daemon_active()
    else:
        daemon_up = False

    if daemon_up is True:
        control = DaemonControl()
        ram_use_daemon = control.ram_use()
        virtualenv_daemon = control.is_in_virtualenv()
    else:
        ram_use_daemon = 0

    if os.path.exists(FRONTEND_PID_FILE):
        with open(FRONTEND_PID_FILE, 'r') as pid_file:
            frontend_pid = int(pid_file.read())

    if frontend_pid:
        pstree_frontend_output, top_frontend_output = output_pstree_top(frontend_pid)

    ram_use_flask = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss / float(1000)

    python_version = sys.version

    return render_template('pages/info.html',
                           daemon_up=daemon_up,
                           gpio_readall=gpio_output,
                           database_version=database_version,
                           correct_database_version=correct_database_version,
                           database_url=MYCODO_DB_PATH,
                           df=df_output,
                           dmesg_output=dmesg_output,
                           free=free_output,
                           frontend_pid=frontend_pid,
                           i2c_devices_sorted=i2c_devices_sorted,
                           ifconfig=ifconfig_output,
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


@blueprint.route('/ram')
def ram():
    """Return how much ram the frontend has used."""
    return f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / float(1000)}"


def output_pstree_top(pid):
    pstree = subprocess.Popen(
        "pstree -p {pid}".format(pid=pid), stdout=subprocess.PIPE, shell=True)
    (pstree_output, _) = pstree.communicate()
    pstree.wait()
    if pstree_output:
        pstree_output = pstree_output.decode("latin1")

    top = subprocess.Popen(
        "top -bH -n 1 -p {pid}".format(pid=pid), stdout=subprocess.PIPE, shell=True)
    (top_output, _) = top.communicate()
    top.wait()
    if top_output:
        top_output = top_output.decode("latin1")

    return pstree_output, top_output


@blueprint.route('/live', methods=('GET', 'POST'))
@flask_login.login_required
def page_live():
    """Page of recent and updating input data."""
    # Get what each measurement uses for a unit
    function = CustomController.query.all()
    device_measurements = DeviceMeasurements.query.all()
    input_dev = Input.query.all()
    output = Output.query.all()

    activated_inputs = Input.query.filter(Input.is_activated).count()
    activated_functions = CustomController.query.filter(CustomController.is_activated).count()

    use_unit = utils_general.use_unit_generate(
        device_measurements, input_dev, output, function)

    # Display orders
    display_order_input = csv_to_list_of_str(DisplayOrder.query.first().inputs)
    display_order_function = csv_to_list_of_str(DisplayOrder.query.first().function)

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    dict_controllers = parse_function_information()
    dict_inputs = parse_input_information()

    custom_options_values_controllers = parse_custom_option_values(
        function, dict_controller=dict_controllers)

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
                           activated_inputs=activated_inputs,
                           activated_functions=activated_functions,
                           custom_options_values_controllers=custom_options_values_controllers,
                           table_device_measurements=DeviceMeasurements,
                           table_input=Input,
                           table_function=CustomController,
                           dict_inputs=dict_inputs,
                           dict_measurements=dict_measurements,
                           dict_units=dict_units,
                           dict_measure_measurements=dict_measure_measurements,
                           dict_measure_units=dict_measure_units,
                           display_order_input=display_order_input,
                           display_order_function=display_order_function,
                           list_devices_adc=list_analog_to_digital_converters(),
                           measurement_units=MEASUREMENTS,
                           use_unit=use_unit)


@blueprint.route('/logview', methods=('GET', 'POST'))
@flask_login.login_required
def page_logview():
    """Display the last (n) lines from a log file."""
    if not utils_general.user_has_permission('view_logs'):
        return redirect(url_for('routes_general.home'))

    form_log_view = forms_misc.LogView()
    log_output = None
    lines = 30
    search = ''
    logfile = ''
    log_field = None
    command = None

    if form_log_view.lines.data:
        lines = form_log_view.lines.data

    if form_log_view.search.data:
        search = form_log_view.search.data

    if form_log_view.log.data:
        log_field = form_log_view.log.data

    # Find which log file was requested, generate command to execute
    if form_log_view.log.data == 'log_nginx':
        if DOCKER_CONTAINER:
            command = f'docker logs -n {lines} mycodo_nginx'
            if search:
                command += f' 2>&1 | grep "{search}"'
        else:
            command = f'journalctl -u nginx -n {lines} --no-pager'
            if search:
                command += f' | grep "{search}"'
    elif form_log_view.log.data == 'log_flask':
        if DOCKER_CONTAINER:
            command = f'docker logs -n {lines} mycodo_flask'
            if search:
                command += f' 2>&1 | grep "{search}"'
        else:
            command = f'journalctl -u mycodoflask -n {lines} --no-pager'
            if search:
                command += f' | grep "{search}"'
    elif form_log_view.log.data == 'log_pid_settings':
        logfile = DAEMON_LOG_FILE
        logrotate_file = logfile + '.1'
        if (logrotate_file and os.path.exists(logrotate_file) and
                logfile and os.path.isfile(logfile)):
            command = f'cat {logrotate_file} {logfile} | grep -a "PID Settings" | tail -n {lines}'
        else:
            command = f'grep -a "PID Settings" {logfile} | tail -n {lines}'
    else:
        if form_log_view.log.data == 'log_login':
            logfile = LOGIN_LOG_FILE
        elif form_log_view.log.data == 'log_http_access':
            logfile = HTTP_ACCESS_LOG_FILE
        elif form_log_view.log.data == 'log_http_error':
            logfile = HTTP_ERROR_LOG_FILE
        elif form_log_view.log.data == 'log_daemon':
            logfile = DAEMON_LOG_FILE
        elif form_log_view.log.data == 'log_dependency':
            logfile = DEPENDENCY_LOG_FILE
        elif form_log_view.log.data == 'log_import':
            logfile = IMPORT_LOG_FILE
        elif form_log_view.log.data == 'log_keepup':
            logfile = KEEPUP_LOG_FILE
        elif form_log_view.log.data == 'log_backup':
            logfile = BACKUP_LOG_FILE
        elif form_log_view.log.data == 'log_restore':
            logfile = RESTORE_LOG_FILE
        elif form_log_view.log.data == 'log_upgrade':
            logfile = UPGRADE_LOG_FILE
        else:
            logfile = DAEMON_LOG_FILE  # Default

        logrotate_file = logfile + '.1'
        if (logrotate_file and os.path.exists(logrotate_file) and
                logfile and os.path.isfile(logfile)):
            command = f'cat {logrotate_file} {logfile} | tail -n {lines}'
            if search:
                command += f' | grep "{search}"'
        elif os.path.isfile(logfile):
            command = f'tail -n {lines} {logfile}'
            if search:
                command += f' | grep "{search}"'

    # Execute command and generate the output to display to the user
    if command:
        log = subprocess.Popen(
            command,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        (log_output, _) = log.communicate()
        log.wait()
        log_output = str(log_output, 'latin-1')
    else:
        log_output = 404

    return render_template('tools/logview.html',
                           form_log_view=form_log_view,
                           lines=lines,
                           log_field=log_field,
                           logfile=logfile,
                           log_output=log_output,
                           search=search)


@blueprint.route('/energy_usage_input_amp', methods=('GET', 'POST'))
@flask_login.login_required
def page_energy_usage_input_amps():
    """Display output usage (duration and energy usage/cost)"""
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('routes_general.home'))

    calculate_pass = False

    form_energy_usage_add = forms_misc.EnergyUsageAdd()
    form_energy_usage_mod = forms_misc.EnergyUsageMod()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('routes_page.page_usage'))

        if form_energy_usage_add.energy_usage_add.data:
            dep_unmet, _, _ = return_dependencies('highstock')
            if dep_unmet:
                return redirect(url_for('routes_admin.admin_dependencies',
                                        device='highstock'))
            utils_misc.energy_usage_add(form_energy_usage_add)
        elif form_energy_usage_mod.energy_usage_mod.data:
            utils_misc.energy_usage_mod(form_energy_usage_mod)
        elif form_energy_usage_mod.energy_usage_delete.data:
            utils_misc.energy_usage_delete(
                form_energy_usage_mod.energy_usage_id.data)
        elif form_energy_usage_mod.energy_usage_range_calc.data:
            calculate_pass = True

        if not calculate_pass:
            return redirect(url_for('routes_page.page_energy_usage_input_amps'))

    energy_usage = EnergyUsage.query.all()
    input_dev = Input.query.all()
    function = CustomController.query.all()
    misc = Misc.query.first()

    # Generate all measurement and units used
    dict_measurements = add_custom_measurements(Measurement.query.all())
    dict_units = add_custom_units(Unit.query.all())

    choices_function = utils_general.choices_functions(
        function, dict_units, dict_measurements)
    choices_input = utils_general.choices_inputs(
        input_dev, dict_units, dict_measurements)

    energy_usage_stats, graph_info = return_energy_usage(
        energy_usage, DeviceMeasurements.query, Conversion.query)

    if calculate_pass:
        start_string = form_energy_usage_mod.energy_usage_date_range.data.split(' - ')[0]
        end_string = form_energy_usage_mod.energy_usage_date_range.data.split(' - ')[1]
        (calculate_usage,
         graph_info,
         picker_start,
         picker_end) = calc_energy_usage(
            form_energy_usage_mod.energy_usage_id.data,
            graph_info,
            start_string,
            end_string,
            EnergyUsage.query,
            DeviceMeasurements.query,
            Conversion.query,
            misc.output_usage_volts)
    else:
        calculate_usage = {}
        picker_start = {}
        picker_end = {}

    picker_end['default'] = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
    picker_start['default'] = datetime.datetime.now() - datetime.timedelta(hours=6)
    picker_start['default'] = picker_start['default'].strftime('%m/%d/%Y %H:%M')

    return render_template('pages/energy_usage_input_amps.html',
                           calculate_usage=calculate_usage,
                           choices_function=choices_function,
                           choices_input=choices_input,
                           energy_usage=energy_usage,
                           energy_usage_stats=energy_usage_stats,
                           form_energy_usage_add=form_energy_usage_add,
                           form_energy_usage_mod=form_energy_usage_mod,
                           graph_info=graph_info,
                           misc=misc,
                           picker_end=picker_end,
                           picker_start=picker_start)


@blueprint.route('/energy_usage_outputs', methods=('GET', 'POST'))
@flask_login.login_required
def page_energy_usage_outputs():
    """Display output usage (duration and energy usage/cost)"""
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('routes_general.home'))

    energy_usage = EnergyUsage.query.all()
    misc = Misc.query.first()
    output = Output.query.all()
    output_channel = OutputChannel.query.all()

    dict_outputs = parse_output_information()

    custom_options_values_output_channels = parse_custom_option_values_output_channels_json(
        output_channel, dict_controller=dict_outputs, key_name='custom_channel_options')

    output_stats = return_output_usage(
        dict_outputs, misc, output, OutputChannel, custom_options_values_output_channels)

    day = misc.output_usage_dayofmonth
    if 4 <= day <= 20 or 24 <= day <= 30:
        date_suffix = 'th'
    else:
        date_suffix = ['st', 'nd', 'rd'][day % 10 - 1]

    # Generate the order to display Outputs
    display_order = []
    for each_output in Output.query.order_by(Output.position_y).all():
        display_order.append(each_output.unique_id)

    return render_template('pages/energy_usage_outputs.html',
                           custom_options_values_output_channels=custom_options_values_output_channels,
                           date_suffix=date_suffix,
                           dict_outputs=dict_outputs,
                           display_order=display_order,
                           misc=misc,
                           output=output,
                           output_stats=output_stats,
                           output_types=output_types(),
                           table_output_channel=OutputChannel,
                           timestamp=time.strftime("%c"))


def dict_custom_colors():
    """
    Generate a dictionary of custom colors from CSV strings saved in the
    database. If custom colors aren't already saved, fill in with a default
    palette.

    :return: dictionary of graph_ids and lists of custom colors
    """
    if flask_login.current_user.theme in THEMES_DARK:
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
    graph = Widget.query.all()
    for each_graph in graph:
        # Only process graph widget types
        if each_graph.graph_type != 'graph':
            continue

        try:
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
                        measurement_name = device_measurement.name
                        conversion = Conversion.query.filter(
                            Conversion.unique_id == device_measurement.conversion_id).first()
                    else:
                        measurement_name = None
                        conversion = None
                    channel, unit, measurement = return_measurement_info(
                        device_measurement, conversion)

                    input_dev = Input.query.filter_by(
                        unique_id=input_unique_id).first()

                    # Custom colors
                    if (index < len(each_graph.input_ids_measurements.split(';')) and
                            len(colors) > index):
                        color = colors[index]
                    else:
                        color = '#FF00AA'

                    # Data grouping
                    disable_data_grouping = False
                    if input_measure_id in each_graph.disable_data_grouping:
                        disable_data_grouping = True

                    if None not in [input_dev, device_measurement]:
                        total.append({
                            'unique_id': input_unique_id,
                            'measure_id': input_measure_id,
                            'type': 'Input',
                            'name': input_dev.name,
                            'channel': channel,
                            'unit': unit,
                            'measure': measurement,
                            'measure_name': measurement_name,
                            'color': color,
                            'disable_data_grouping': disable_data_grouping})
                        index += 1
                index_sum += index

            if each_graph.output_ids:
                index = 0
                for each_set in each_graph.output_ids.split(';'):
                    output_unique_id = each_set.split(',')[0]
                    output_measure_id = each_set.split(',')[1]

                    device_measurement = DeviceMeasurements.query.filter(
                        DeviceMeasurements.unique_id == output_measure_id).first()
                    if device_measurement:
                        measurement_name = device_measurement.name
                        conversion = Conversion.query.filter(
                            Conversion.unique_id == device_measurement.conversion_id).first()
                    else:
                        measurement_name = None
                        conversion = None
                    channel, unit, measurement = return_measurement_info(
                        device_measurement, conversion)

                    output = Output.query.filter_by(
                        unique_id=output_unique_id).first()

                    if (index < len(each_graph.output_ids.split(';')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum + index]
                    else:
                        color = '#FF00AA'

                    # Data grouping
                    disable_data_grouping = False
                    if output_measure_id in each_graph.disable_data_grouping:
                        disable_data_grouping = True

                    if output is not None:
                        total.append({
                            'unique_id': output_unique_id,
                            'measure_id': output_measure_id,
                            'type': 'Output',
                            'name': output.name,
                            'channel': channel,
                            'unit': unit,
                            'measure': measurement,
                            'measure_name': measurement_name,
                            'color': color,
                            'disable_data_grouping': disable_data_grouping})
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
                        measurement_name = device_measurement.name
                        conversion = Conversion.query.filter(
                            Conversion.unique_id == device_measurement.conversion_id).first()
                    else:
                        measurement_name = None
                        conversion = None
                    channel, unit, measurement = return_measurement_info(
                        device_measurement, conversion)

                    pid = PID.query.filter_by(
                        unique_id=pid_unique_id).first()

                    # Custom colors
                    if (index < len(each_graph.pid_ids.split(';')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum + index]
                    else:
                        color = '#FF00AA'

                    # Data grouping
                    disable_data_grouping = False
                    if pid_measure_id in each_graph.disable_data_grouping:
                        disable_data_grouping = True

                    if pid is not None:
                        total.append({
                            'unique_id': pid_unique_id,
                            'measure_id': pid_measure_id,
                            'type': 'PID',
                            'name': pid.name,
                            'channel': channel,
                            'unit': unit,
                            'measure': measurement,
                            'measure_name': measurement_name,
                            'color': color,
                            'disable_data_grouping': disable_data_grouping})
                        index += 1
                index_sum += index

            if each_graph.note_tag_ids:
                index = 0
                for each_set in each_graph.note_tag_ids.split(';'):
                    tag_unique_id = each_set.split(',')[0]

                    device_measurement = NoteTags.query.filter_by(
                        unique_id=tag_unique_id).first()

                    if (index < len(each_graph.note_tag_ids.split(',')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum + index]
                    else:
                        color = '#FF00AA'
                    if device_measurement is not None:
                        total.append({
                            'unique_id': tag_unique_id,
                            'measure_id': None,
                            'type': 'Tag',
                            'name': device_measurement.name,
                            'channel': None,
                            'unit': None,
                            'measure': None,
                            'measure_name': None,
                            'color': color,
                            'disable_data_grouping': None
                        })
                        index += 1
                index_sum += index

            color_count.update({each_graph.unique_id: total})
        except IndexError:
            logger.exception("Index")
        except Exception:
            logger.exception("Exception")

    return color_count


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
