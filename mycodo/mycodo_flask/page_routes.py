# coding=utf-8
""" collection of Page endpoints """
import datetime
import flask_login
import glob
import logging
import os
import resource
import subprocess
import sys
import time
from collections import OrderedDict
from flask_babel import gettext
from importlib import import_module
from w1thermsensor import W1ThermSensor

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from flask.blueprints import Blueprint

from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.static_routes import inject_variables
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_client import daemon_active

from mycodo.mycodo_flask.forms import forms_conditional
from mycodo.mycodo_flask.forms import forms_graph
from mycodo.mycodo_flask.forms import forms_input
from mycodo.mycodo_flask.forms import forms_lcd
from mycodo.mycodo_flask.forms import forms_misc
from mycodo.mycodo_flask.forms import forms_output
from mycodo.mycodo_flask.forms import forms_pid
from mycodo.mycodo_flask.forms import forms_timer

from mycodo.mycodo_flask.utils import utils_conditional
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_graph
from mycodo.mycodo_flask.utils import utils_input
from mycodo.mycodo_flask.utils import utils_lcd
from mycodo.mycodo_flask.utils import utils_output
from mycodo.mycodo_flask.utils import utils_pid
from mycodo.mycodo_flask.utils import utils_timer

from mycodo.databases.models import AlembicVersion
from mycodo.databases.models import Camera
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalActions
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import Graph
from mycodo.databases.models import LCD
from mycodo.databases.models import LCDData
from mycodo.databases.models import Method
from mycodo.databases.models import Misc
from mycodo.databases.models import PID
from mycodo.databases.models import Output
from mycodo.databases.models import Input
from mycodo.databases.models import Timer
from mycodo.databases.models import User

from mycodo.devices.camera import camera_record
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import csv_to_list_of_int
from mycodo.utils.tools import return_relay_usage

from mycodo.config import BACKUP_LOG_FILE
from mycodo.config import DAEMON_LOG_FILE
from mycodo.config import HTTP_LOG_FILE
from mycodo.config import KEEPUP_LOG_FILE
from mycodo.config import LOGIN_LOG_FILE
from mycodo.config import RESTORE_LOG_FILE
from mycodo.config import UPGRADE_LOG_FILE

from mycodo.config import CONDITIONAL_ACTIONS
from mycodo.config import DAEMON_PID_FILE
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import MEASUREMENTS
from mycodo.config import MEASUREMENT_UNITS
from mycodo.config import PATH_CAMERAS

from mycodo.config import USAGE_REPORTS_PATH

logger = logging.getLogger('mycodo.mycodo_flask.pages')

blueprint = Blueprint('page_routes',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
def inject_dictionary():
    return inject_variables()


@blueprint.context_processor
def epoch_to_time_string():
    def format_timestamp(epoch):
        return datetime.datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")
    return dict(format_timestamp=format_timestamp)


@blueprint.route('/camera', methods=('GET', 'POST'))
@flask_login.login_required
def page_camera():
    """
    Page to start/stop video stream or time-lapse, or capture a still image.
    Displays most recent still image and time-lapse image.
    """
    if not utils_general.user_has_permission('view_camera'):
        return redirect(url_for('general_routes.home'))

    form_camera = forms_misc.Camera()
    camera = Camera.query.all()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_settings'):
            return redirect(url_for('page_routes.page_camera'))

        control = DaemonControl()
        mod_camera = Camera.query.filter(
            Camera.id == form_camera.camera_id.data).first()
        if form_camera.capture_still.data:
            # If a stream is active, stop the stream to take a photo
            if mod_camera.stream_started:
                camera_stream = import_module(
                    'mycodo.mycodo_flask.camera.camera_{lib}'.format(
                        lib=mod_camera.library)).Camera
                if camera_stream(unique_id=mod_camera.unique_id).is_running(mod_camera.unique_id):
                    camera_stream(unique_id=mod_camera.unique_id).stop(mod_camera.unique_id)
                time.sleep(2)
            camera_record('photo', mod_camera)
        elif form_camera.start_timelapse.data:
            if mod_camera.stream_started:
                flash(gettext(u"Cannot start time-lapse if stream is active."), "error")
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
                    u"Cannot start stream if time-lapse is active."), "error")
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
        return redirect('/camera')

    # Get the full path and timestamps of latest still and time-lapse images
    latest_img_still_ts = {}
    latest_img_still = {}
    latest_img_tl_ts = {}
    latest_img_tl = {}
    for each_camera in camera:
        camera_path = os.path.join(PATH_CAMERAS, '{id}-{uid}'.format(
            id=each_camera.id, uid=each_camera.unique_id))
        try:
            latest_still_img_full_path = max(glob.iglob(
                '{path}/still/Still-{cam_id}-*.jpg'.format(
                    path=camera_path,
                    cam_id=each_camera.id)),
                key=os.path.getmtime)
        except ValueError:
            latest_still_img_full_path = None
        if latest_still_img_full_path:
            ts = os.path.getmtime(latest_still_img_full_path)
            latest_img_still_ts[each_camera.id] = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_img_still[each_camera.id] = os.path.basename(latest_still_img_full_path)
        else:
            latest_img_still[each_camera.id] = None

        try:
            latest_time_lapse_img_full_path = max(glob.iglob(
                '{path}/timelapse/Timelapse-{cam_id}-*.jpg'.format(
                    path=camera_path,
                    cam_id=each_camera.id)),
                key=os.path.getmtime)
        except ValueError:
            latest_time_lapse_img_full_path = None
        if latest_time_lapse_img_full_path:
            ts = os.path.getmtime(latest_time_lapse_img_full_path)
            latest_img_tl_ts[each_camera.id] = datetime.datetime.fromtimestamp(
                ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_img_tl[each_camera.id] = os.path.basename(
                latest_time_lapse_img_full_path)
        else:
            latest_img_tl[each_camera.id] = None

    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template('pages/camera.html',
                           camera=camera,
                           form_camera=form_camera,
                           latest_img_still=latest_img_still,
                           latest_img_still_ts=latest_img_still_ts,
                           latest_img_tl=latest_img_tl,
                           latest_img_tl_ts=latest_img_tl_ts,
                           time_now=time_now)


@blueprint.route('/export', methods=('GET', 'POST'))
@flask_login.login_required
def page_export():
    """
    Export measurement data in CSV format
    """
    export_options = forms_misc.ExportOptions()
    output = Output.query.all()
    input_dev = Input.query.all()
    output_choices = utils_general.choices_id_name(output)
    input_choices = utils_general.choices_inputs(input_dev)

    if request.method == 'POST':
        start_time = export_options.date_range.data.split(' - ')[0]
        start_seconds = int(time.mktime(
            time.strptime(start_time, '%m/%d/%Y %H:%M')))
        end_time = export_options.date_range.data.split(' - ')[1]
        end_seconds = int(time.mktime(
            time.strptime(end_time, '%m/%d/%Y %H:%M')))

        unique_id = export_options.measurement.data.split(',')[0]
        measurement = export_options.measurement.data.split(',')[1]

        url = '/export_data/{meas}/{id}/{start}/{end}'.format(
            meas=measurement,
            id=unique_id,
            start=start_seconds, end=end_seconds)
        return redirect(url)

    # Generate start end end times for date/time picker
    end_picker = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
    start_picker = datetime.datetime.now() - datetime.timedelta(hours=6)
    start_picker = start_picker.strftime('%m/%d/%Y %H:%M')

    return render_template('tools/export.html',
                           start_picker=start_picker,
                           end_picker=end_picker,
                           exportOptions=export_options,
                           relay_choices=output_choices,
                           sensor_choices=input_choices)


@blueprint.route('/graph', methods=('GET', 'POST'))
@flask_login.login_required
def page_graph():
    """
    Generate custom graphs to display input data retrieved from influxdb.
    """
    # Create form objects
    form_add_graph = forms_graph.GraphAdd()
    form_mod_graph = forms_graph.GraphMod()
    form_add_gauge = forms_graph.GaugeAdd()
    form_mod_gauge = forms_graph.GaugeMod()

    # Retrieve the order to display graphs
    display_order = csv_to_list_of_int(DisplayOrder.query.first().graph)

    # Retrieve tables from SQL database
    graph = Graph.query.all()
    pid = PID.query.all()
    output = Output.query.all()
    input_dev = Input.query.all()

    # Retrieve all choices to populate form drop-down menu
    pid_choices = utils_general.choices_pids(pid)
    output_choices = utils_general.choices_outputs(output)
    input_choices = utils_general.choices_inputs(input_dev)

    # Add custom measurement and units to list (From linux command input)
    input_measurements = MEASUREMENT_UNITS
    input_measurements = add_custom_measurements(
        input_dev, input_measurements, MEASUREMENT_UNITS)

    # Add multi-select values as form choices, for validation
    form_mod_graph.pid_ids.choices = []
    form_mod_graph.relay_ids.choices = []
    form_mod_graph.sensor_ids.choices = []
    for key, value in pid_choices.items():
        form_mod_graph.pid_ids.choices.append((key, value))
    for key, value in output_choices.items():
        form_mod_graph.relay_ids.choices.append((key, value))
    for key, value in input_choices.items():
        form_mod_graph.sensor_ids.choices.append((key, value))

    # Generate dictionary of custom colors for each graph
    colors_graph = dict_custom_colors()

    # Retrieve custom colors for gauges
    colors_gauge = OrderedDict()
    for each_graph in graph:
        if each_graph.range_colors:  # Split into list
            color_areas = each_graph.range_colors.split(';')
        else:  # Create empty list
            color_areas = []
        total = []
        if each_graph.graph_type == 'gauge_angular':
            for each_range in color_areas:
                total.append({
                    'low': each_range.split(',')[0],
                    'high': each_range.split(',')[1],
                    'hex': each_range.split(',')[2]})
        elif each_graph.graph_type == 'gauge_solid':
            for each_range in color_areas:
                total.append({
                    'stop': each_range.split(',')[0],
                    'hex': each_range.split(',')[1]})
        colors_gauge.update({each_graph.id: total})

    # Detect which form on the page was submitted
    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('general_routes.home'))

        if form_add_graph.graph_add.data:
            utils_graph.graph_add(form_add_graph, display_order)
        elif form_mod_graph.graph_mod.data:
            utils_graph.graph_mod(form_mod_graph, request.form)
        elif form_mod_graph.graph_del.data:
            utils_graph.graph_del(form_mod_graph)
        elif form_mod_graph.graph_order_up.data:
            utils_graph.graph_reorder(form_mod_graph.graph_id.data,
                                      display_order, 'up')
        elif form_mod_graph.graph_order_down.data:
            utils_graph.graph_reorder(form_mod_graph.graph_id.data,
                                      display_order, 'down')
        elif form_add_gauge.gauge_add.data:
            utils_graph.graph_add(form_add_gauge, display_order)
        elif form_mod_gauge.gauge_mod.data:
            utils_graph.graph_mod(form_mod_gauge, request.form)
        elif form_mod_gauge.gauge_del.data:
            utils_graph.graph_del(form_mod_gauge)
        elif form_mod_gauge.gauge_order_up.data:
            utils_graph.graph_reorder(form_mod_gauge.graph_id.data,
                                      display_order, 'up')
        elif form_mod_gauge.gauge_order_down.data:
            utils_graph.graph_reorder(form_mod_gauge.graph_id.data,
                                      display_order, 'down')

        return redirect('/graph')

    return render_template('pages/graph.html',
                           graph=graph,
                           pid=pid,
                           relay=output,
                           sensor=input_dev,
                           pid_choices=pid_choices,
                           output_choices=output_choices,
                           sensor_choices=input_choices,
                           colors_graph=colors_graph,
                           colors_gauge=colors_gauge,
                           sensor_measurements=input_measurements,
                           measurement_units=MEASUREMENT_UNITS,
                           displayOrder=display_order,
                           form_add_graph=form_add_graph,
                           form_add_gauge=form_add_gauge,
                           form_mod_graph=form_mod_graph,
                           form_mod_gauge=form_mod_gauge)


@blueprint.route('/graph-async', methods=('GET', 'POST'))
@flask_login.login_required
def page_graph_async():
    """ Generate graphs using asynchronous data retrieval """
    input_dev = Input.query.all()
    input_choices = utils_general.choices_inputs(input_dev)
    input_choices_split = OrderedDict()
    for key in input_choices:
        order = key.split(",")
        # Separate input IDs and measurement types
        input_choices_split.update({order[0]: order[1]})

    selected_id = None
    selected_measure = None
    selected_unique_id = None

    if request.method == 'POST':
        selected_id = request.form['selected_measure'].split(",")[0]
        selected_measure = request.form['selected_measure'].split(",")[1]
        selected_unique_id = Input.query.filter(Input.unique_id == selected_id).first().unique_id

    return render_template('pages/graph-async.html',
                           sensor=input_dev,
                           sensor_choices=input_choices,
                           sensor_choices_split=input_choices_split,
                           selected_id=selected_id,
                           selected_measure=selected_measure,
                           selected_unique_id=selected_unique_id)


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
        return redirect(url_for('general_routes.home'))

    uptime = subprocess.Popen(
        "uptime", stdout=subprocess.PIPE, shell=True)
    (uptime_output, _) = uptime.communicate()
    uptime.wait()

    uname = subprocess.Popen(
        "uname -a", stdout=subprocess.PIPE, shell=True)
    (uname_output, _) = uname.communicate()
    uname.wait()

    gpio = subprocess.Popen(
        "gpio readall", stdout=subprocess.PIPE, shell=True)
    (gpio_output, _) = gpio.communicate()
    gpio.wait()

    i2c_devices = {}
    i2cdetect_out = {}
    try:
        from glob import glob
        i2c_devices = glob("/dev/i2c-*")
        for index, each_dev in enumerate(i2c_devices):
            i2c_devices[index] = int(each_dev.strip("/dev/i2c-"))
            df = subprocess.Popen(
                "i2cdetect -y {dev}".format(dev=i2c_devices[index]),
                stdout=subprocess.PIPE,
                shell=True)
            (i2cdetect_out[i2c_devices[index]], _) = df.communicate()
            df.wait()
    except Exception as er:
        flash("Error detecting I2C devices: {er}".format(er=er), "error")

    df = subprocess.Popen(
        "df -h", stdout=subprocess.PIPE, shell=True)
    (df_output, _) = df.communicate()
    df.wait()

    free = subprocess.Popen(
        "free -h", stdout=subprocess.PIPE, shell=True)
    (free_output, _) = free.communicate()
    free.wait()

    ifconfig = subprocess.Popen(
        "ifconfig -a", stdout=subprocess.PIPE, shell=True)
    (ifconfig_output, _) = ifconfig.communicate()
    ifconfig.wait()

    daemon_pid = None
    if os.path.exists(DAEMON_PID_FILE):
        with open(DAEMON_PID_FILE, 'r') as pid_file:
            daemon_pid = int(pid_file.read())

    database_version = []
    for each_ver in AlembicVersion.query.all():
        database_version.append(each_ver.version_num)

    virtualenv_flask = False
    if hasattr(sys, 'real_prefix'):
        virtualenv_flask = True

    virtualenv_daemon = False
    pstree_output = None
    top_output = None
    daemon_up = daemon_active()
    if daemon_up:
        control = DaemonControl()
        ram_use_daemon = control.ram_use()
        virtualenv_daemon = control.is_in_virtualenv()

        pstree = subprocess.Popen(
            "pstree -p {pid}".format(pid=daemon_pid), stdout=subprocess.PIPE, shell=True)
        (pstree_output, _) = pstree.communicate()
        pstree.wait()

        top = subprocess.Popen(
            "top -bH -n 1 -p {pid}".format(pid=daemon_pid), stdout=subprocess.PIPE, shell=True)
        (top_output, _) = top.communicate()
        top.wait()
    else:
        ram_use_daemon = 0

    ram_use_flask = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss / float(1000)

    return render_template('pages/info.html',
                           daemon_pid=daemon_pid,
                           daemon_up=daemon_up,
                           gpio_readall=gpio_output,
                           database_version=database_version,
                           df=df_output,
                           free=free_output,
                           i2c_devices=i2c_devices,
                           i2cdetect_out=i2cdetect_out,
                           ifconfig=ifconfig_output,
                           pstree=pstree_output,
                           ram_use_daemon=ram_use_daemon,
                           ram_use_flask=ram_use_flask,
                           top=top_output,
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
    pid = PID.query.all()
    output = Output.query.all()
    input_dev = Input.query.all()

    display_order = csv_to_list_of_int(DisplayOrder.query.first().lcd)

    form_lcd_add = forms_lcd.LCDAdd()
    form_lcd_mod = forms_lcd.LCDMod()
    form_lcd_display = forms_lcd.LCDModDisplay()

    measurements = MEASUREMENTS

    # Add custom measurement and units to list (From linux command input)
    for each_input in input_dev:
        if each_input.cmd_measurement and each_input.cmd_measurement not in MEASUREMENTS:
            if each_input.cmd_measurement and each_input.cmd_measurement_units:
                measurements.update(
                    {'LinuxCommand': [each_input.cmd_measurement]})

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('general_routes.home'))

        if form_lcd_add.add.data:
            utils_lcd.lcd_add(form_lcd_add.quantity.data)
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
        return redirect('/lcd')

    return render_template('pages/lcd.html',
                           lcd=lcd,
                           lcd_data=lcd_data,
                           measurements=measurements,
                           pid=pid,
                           relay=output,
                           sensor=input_dev,
                           displayOrder=display_order,
                           form_lcd_add=form_lcd_add,
                           form_lcd_mod=form_lcd_mod,
                           form_lcd_display=form_lcd_display)


@blueprint.route('/live', methods=('GET', 'POST'))
@flask_login.login_required
def page_live():
    """ Page of recent and updating input data """
    # Retrieve tables for the data displayed on the live page
    pid = PID.query.all()
    output = Output.query.all()
    input_dev = Input.query.all()
    timer = Timer.query.all()

    # Display orders
    pid_display_order = csv_to_list_of_int(
        DisplayOrder.query.first().pid)
    input_display_order = csv_to_list_of_int(
        DisplayOrder.query.first().sensor)

    # Filter only activated inputs
    input_order_sorted = []
    if input_display_order:
        for each_input_order in input_display_order:
            for each_input in input_dev:
                if (each_input_order == each_input.id and
                        each_input.is_activated):
                    input_order_sorted.append(each_input.id)

    # Retrieve only parent method columns
    method = Method.query.all()

    return render_template('pages/live.html',
                           measurement_units=MEASUREMENT_UNITS,
                           method=method,
                           pid=pid,
                           relay=output,
                           sensor=input_dev,
                           timer=timer,
                           pidDisplayOrder=pid_display_order,
                           sensorDisplayOrderSorted=input_order_sorted)


@blueprint.route('/logview', methods=('GET', 'POST'))
@flask_login.login_required
def page_logview():
    """ Display the last (n) lines from a log file """
    if not utils_general.user_has_permission('view_logs'):
        return redirect(url_for('general_routes.home'))

    form_log_view = forms_misc.LogView()
    log_output = None
    lines = 30
    logfile = ''
    if request.method == 'POST':
        if form_log_view.lines.data:
            lines = form_log_view.lines.data

        if form_log_view.loglogin.data:
            logfile = LOGIN_LOG_FILE
        elif form_log_view.loghttp.data:
            logfile = HTTP_LOG_FILE
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
            log_output = unicode(log_output, 'utf-8')
        else:
            log_output = 404

    return render_template('tools/logview.html',
                           form_log_view=form_log_view,
                           lines=lines,
                           logfile=logfile,
                           log_output=log_output)


@blueprint.route('/pid', methods=('GET', 'POST'))
@flask_login.login_required
def page_pid():
    """ Display PID settings """
    method = Method.query.all()
    pid = PID.query.all()
    output = Output.query.all()
    input_dev = Input.query.all()

    input_choices = utils_general.choices_inputs(input_dev)

    display_order = csv_to_list_of_int(DisplayOrder.query.first().pid)

    form_add_pid = forms_pid.PIDAdd()
    form_mod_pid_base = forms_pid.PIDModBase()
    form_mod_pid_output_raise = forms_pid.PIDModRelayRaise()
    form_mod_pid_output_lower = forms_pid.PIDModRelayLower()
    form_mod_pid_pwm_raise = forms_pid.PIDModPWMRaise()
    form_mod_pid_pwm_lower = forms_pid.PIDModPWMLower()

    # Create list of file names from the pid_options directory
    # Used in generating the correct options for each PID
    pid_templates = []
    pid_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/pid_options')
    for (_, _, file_names) in os.walk(pid_path):
        pid_templates.extend(file_names)
        break

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('general_routes.home'))

        form_name = request.form['form-name']
        if form_name == 'addPID':
            utils_pid.pid_add(form_add_pid)
        elif form_name == 'modPID':
            if form_mod_pid_base.save.data:
                utils_pid.pid_mod(form_mod_pid_base,
                                   form_mod_pid_pwm_raise,
                                   form_mod_pid_pwm_lower,
                                   form_mod_pid_output_raise,
                                   form_mod_pid_output_lower)
            elif form_mod_pid_base.delete.data:
                utils_pid.pid_del(
                    form_mod_pid_base.pid_id.data)
            elif form_mod_pid_base.reorder_up.data:
                utils_pid.pid_reorder(
                    form_mod_pid_base.pid_id.data, display_order, 'up')
            elif form_mod_pid_base.reorder_down.data:
                utils_pid.pid_reorder(
                    form_mod_pid_base.pid_id.data, display_order, 'down')
            elif form_mod_pid_base.activate.data:
                utils_pid.pid_activate(
                    form_mod_pid_base.pid_id.data)
            elif form_mod_pid_base.deactivate.data:
                utils_pid.pid_deactivate(
                    form_mod_pid_base.pid_id.data)
            elif form_mod_pid_base.hold.data:
                utils_pid.pid_manipulate(
                    form_mod_pid_base.pid_id.data, 'Hold')
            elif form_mod_pid_base.pause.data:
                utils_pid.pid_manipulate(
                    form_mod_pid_base.pid_id.data, 'Pause')
            elif form_mod_pid_base.resume.data:
                utils_pid.pid_manipulate(
                    form_mod_pid_base.pid_id.data, 'Resume')

        return redirect('/pid')

    return render_template('pages/pid.html',
                           method=method,
                           pid=pid,
                           pid_templates=pid_templates,
                           relay=output,
                           sensor=input_dev,
                           sensor_choices=input_choices,
                           displayOrder=display_order,
                           form_add_pid=form_add_pid,
                           form_mod_pid_base=form_mod_pid_base,
                           form_mod_pid_pwm_raise=form_mod_pid_pwm_raise,
                           form_mod_pid_pwm_lower=form_mod_pid_pwm_lower,
                           form_mod_pid_relay_raise=form_mod_pid_output_raise,
                           form_mod_pid_relay_lower=form_mod_pid_output_lower)


@blueprint.route('/output', methods=('GET', 'POST'))
@flask_login.login_required
def page_output():
    """ Display output status and config """
    camera = Camera.query.all()
    lcd = LCD.query.all()
    output = Output.query.all()
    user = User.query.all()

    conditional = Conditional.query.filter(
        Conditional.conditional_type == 'relay').all()
    conditional_actions = ConditionalActions.query.all()

    display_order = csv_to_list_of_int(DisplayOrder.query.first().relay)

    form_add_output = forms_output.OutputAdd()
    form_mod_output = forms_output.OutputMod()

    form_conditional = forms_conditional.Conditional()
    form_conditional_actions = forms_conditional.ConditionalActions()

    # Create list of file names from the output_options directory
    # Used in generating the correct options for each output/device
    output_templates = []
    output_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/output_options')
    for (_, _, file_names) in os.walk(output_path):
        output_templates.extend(file_names)
        break

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('page_routes.page_output'))

        if form_add_output.relay_add.data:
            utils_output.relay_add(form_add_output)
        elif form_mod_output.save.data:
            utils_output.relay_mod(form_mod_output)
        elif form_mod_output.delete.data:
            utils_output.relay_del(form_mod_output)
        elif form_mod_output.order_up.data:
            utils_output.relay_reorder(form_mod_output.relay_id.data,
                                       display_order, 'up')
        elif form_mod_output.order_down.data:
            utils_output.relay_reorder(form_mod_output.relay_id.data,
                                       display_order, 'down')
        elif form_conditional.add_cond.data:
            utils_conditional.conditional_add(
                form_conditional.conditional_type.data,
                form_conditional.quantity.data)
        elif form_conditional.delete_cond.data:
            utils_conditional.conditional_mod(form_conditional, 'delete')
        elif form_conditional.save_cond.data:
            utils_conditional.conditional_mod(form_conditional, 'modify')
        elif form_conditional.activate_cond.data:
            utils_conditional.conditional_activate(form_conditional)
        elif form_conditional.deactivate_cond.data:
            utils_conditional.conditional_deactivate(form_conditional)
        elif form_conditional_actions.add_action.data:
            utils_conditional.conditional_action_add(form_conditional_actions)
        elif form_conditional_actions.save_action.data:
            utils_conditional.conditional_action_mod(form_conditional_actions,
                                                     'modify')
        elif form_conditional_actions.delete_action.data:
            utils_conditional.conditional_action_mod(form_conditional_actions,
                                                     'delete')
        return redirect(url_for('page_routes.page_output'))

    return render_template('pages/output.html',
                           camera=camera,
                           conditional=conditional,
                           conditional_actions=conditional_actions,
                           conditional_actions_list=CONDITIONAL_ACTIONS,
                           displayOrder=display_order,
                           form_conditional=form_conditional,
                           form_conditional_actions=form_conditional_actions,
                           form_add_relay=form_add_output,
                           form_mod_relay=form_mod_output,
                           lcd=lcd,
                           relay=output,
                           relay_templates=output_templates,
                           user=user)


@blueprint.route('/input', methods=('GET', 'POST'))
@flask_login.login_required
def page_input():
    """ Display input settings """
    # TCA9548A I2C multiplexer
    multiplexer_addresses = [
        '0x70',
        '0x71',
        '0x72',
        '0x73',
        '0x74',
        '0x75',
        '0x76',
        '0x77'
    ]
    multiplexer_channels = list(range(0, 9))

    camera = Camera.query.all()
    lcd = LCD.query.all()
    pid = PID.query.all()
    output = Output.query.all()
    input_dev = Input.query.all()
    user = User.query.all()

    conditional = Conditional.query.filter(
        Conditional.conditional_type == 'sensor').all()
    conditional_actions = ConditionalActions.query.all()

    display_order = csv_to_list_of_int(DisplayOrder.query.first().sensor)

    form_add_input = forms_input.InputAdd()
    form_mod_input = forms_input.InputMod()

    form_conditional = forms_conditional.Conditional()
    form_conditional_actions = forms_conditional.ConditionalActions()

    # If DS18B20 inputs added, compile a list of detected inputs
    ds18b20_inputs = []
    if Input.query.filter(Input.device == 'DS18B20').count():
        try:
            for each_input in W1ThermSensor.get_available_sensors():
                ds18b20_inputs.append(each_input.id)
        except OSError:
            flash("Unable to detect inputs in '/sys/bus/w1/devices'",
                  "error")

    # Create list of file names from the input_options directory
    # Used in generating the correct options for each input/device
    input_templates = []
    input_path = os.path.join(
        INSTALL_DIRECTORY,
        'mycodo/mycodo_flask/templates/pages/input_options')
    for (_, _, file_names) in os.walk(input_path):
        input_templates.extend(file_names)
        break

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('page_routes.page_input'))

        if form_add_input.sensorAddSubmit.data:
            utils_input.sensor_add(form_add_input)
        elif form_mod_input.modSensorSubmit.data:
            utils_input.sensor_mod(form_mod_input)
        elif form_mod_input.delSensorSubmit.data:
            utils_input.sensor_del(form_mod_input)
        elif form_mod_input.orderSensorUp.data:
            utils_input.sensor_reorder(form_mod_input.modSensor_id.data,
                                       display_order, 'up')
        elif form_mod_input.orderSensorDown.data:
            utils_input.sensor_reorder(form_mod_input.modSensor_id.data,
                                       display_order, 'down')
        elif form_mod_input.activateSensorSubmit.data:
            utils_input.sensor_activate(form_mod_input)
        elif form_mod_input.deactivateSensorSubmit.data:
            utils_input.sensor_deactivate(form_mod_input)

        elif form_conditional.deactivate_cond.data:
            utils_conditional.conditional_deactivate(form_conditional)
        elif form_conditional.activate_cond.data:
            utils_conditional.conditional_activate(form_conditional)
        elif form_mod_input.sensorCondAddSubmit.data:
            utils_conditional.conditional_add(
                'sensor', 1, sensor_id=form_mod_input.modSensor_id.data)
        elif form_conditional.delete_cond.data:
            utils_conditional.conditional_mod(form_conditional, 'delete')
        elif form_conditional.save_cond.data:
            utils_conditional.conditional_mod(form_conditional, 'modify')
        elif form_conditional_actions.add_action.data:
            utils_conditional.conditional_action_add(form_conditional_actions)
        elif form_conditional_actions.save_action.data:
            utils_conditional.conditional_action_mod(form_conditional_actions,
                                                     'modify')
        elif form_conditional_actions.delete_action.data:
            utils_conditional.conditional_action_mod(form_conditional_actions,
                                                     'delete')
        return redirect(url_for('page_routes.page_input'))

    return render_template('pages/input.html',
                           camera=camera,
                           conditional=conditional,
                           conditional_actions=conditional_actions,
                           conditional_actions_list=CONDITIONAL_ACTIONS,
                           displayOrder=display_order,
                           ds18b20_sensors=ds18b20_inputs,
                           form_add_sensor=form_add_input,
                           form_conditional=form_conditional,
                           form_conditional_actions=form_conditional_actions,
                           form_mod_sensor=form_mod_input,
                           lcd=lcd,
                           measurements=MEASUREMENTS,
                           multiplexer_addresses=multiplexer_addresses,
                           multiplexer_channels=multiplexer_channels,
                           pid=pid,
                           relay=output,
                           sensor=input_dev,
                           sensor_templates=input_templates,
                           units=MEASUREMENT_UNITS,
                           user=user)


@blueprint.route('/timer', methods=('GET', 'POST'))
@flask_login.login_required
def page_timer():
    """ Display Timer settings """
    method = Method.query.all()
    timer = Timer.query.all()
    output = Output.query.all()
    output_choices = utils_general.choices_outputs(output)

    display_order = csv_to_list_of_int(DisplayOrder.query.first().timer)

    form_timer_base = forms_timer.TimerBase()
    form_timer_time_point = forms_timer.TimerTimePoint()
    form_timer_time_span = forms_timer.TimerTimeSpan()
    form_timer_duration = forms_timer.TimerDuration()
    form_timer_pwm_method = forms_timer.TimerPWMMethod()

    if request.method == 'POST':
        if not utils_general.user_has_permission('edit_controllers'):
            return redirect(url_for('general_routes.home'))

        form_name = request.form['form-name']
        form_timer = None
        if form_name == 'addTimer' or form_name == 'modTimer':
            if form_timer_base.timer_type.data == 'time_point':
                form_timer = form_timer_time_point
            elif form_timer_base.timer_type.data == 'time_span':
                form_timer = form_timer_time_span
            elif form_timer_base.timer_type.data == 'duration':
                form_timer = form_timer_duration
            elif form_timer_base.timer_type.data == 'pwm_method':
                form_timer = form_timer_pwm_method

        if form_name == 'addTimer' and form_timer:
            utils_timer.timer_add(display_order,
                                 form_timer_base,
                                 form_timer)

        elif form_name == 'modTimer' and form_timer:
            if form_timer_base.delete.data:
                utils_timer.timer_del(form_timer_base)
            elif form_timer_base.order_up.data:
                utils_timer.timer_reorder(form_timer_base.timer_id.data,
                                          display_order, 'up')
            elif form_timer_base.order_down.data:
                utils_timer.timer_reorder(form_timer_base.timer_id.data,
                                          display_order, 'down')
            elif form_timer_base.activate.data:
                utils_timer.timer_activate(form_timer_base)
            elif form_timer_base.deactivate.data:
                utils_timer.timer_deactivate(form_timer_base)
            elif form_timer_base.modify.data:
                utils_timer.timer_mod(form_timer_base, form_timer)
        return redirect(url_for('page_routes.page_timer'))

    return render_template('pages/timer.html',
                           method=method,
                           timer=timer,
                           displayOrder=display_order,
                           output_choices=output_choices,
                           form_timer_base=form_timer_base,
                           form_timer_time_point=form_timer_time_point,
                           form_timer_time_span=form_timer_time_span,
                           form_timer_duration=form_timer_duration,
                           form_timer_pwm_method=form_timer_pwm_method)


@blueprint.route('/usage', methods=('GET', 'POST'))
@flask_login.login_required
def page_usage():
    """ Display output usage (duration and energy usage/cost) """
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('general_routes.home'))

    misc = Misc.query.first()
    output = Output.query.all()

    output_stats = return_relay_usage(misc, output)

    day = misc.relay_usage_dayofmonth
    if 4 <= day <= 20 or 24 <= day <= 30:
        date_suffix = 'th'
    else:
        date_suffix = ['st', 'nd', 'rd'][day % 10 - 1]

    display_order = csv_to_list_of_int(DisplayOrder.query.first().relay)

    return render_template('pages/usage.html',
                           date_suffix=date_suffix,
                           display_order=display_order,
                           misc=misc,
                           relay=output,
                           relay_stats=output_stats,
                           timestamp=time.strftime("%c"))


@blueprint.route('/usage_reports', methods=('GET', 'POST'))
@flask_login.login_required
def page_usage_reports():
    """ Display output usage (duration and energy usage/cost) """
    if not utils_general.user_has_permission('view_stats'):
        return redirect(url_for('general_routes.home'))

    report_location = os.path.normpath(USAGE_REPORTS_PATH)
    reports = [0, 0]

    return render_template('pages/usage_reports.html',
                           report_location=report_location,
                           reports=reports)


def dict_custom_colors():
    """
    Generate lists of custom colors from CSV strings saved in the database.
    If custom colors aren't already saved, fill in with a default palette.

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
        graph = Graph.query.all()
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
            if each_graph.sensor_ids_measurements:
                for each_set in each_graph.sensor_ids_measurements.split(';'):
                    input_unique_id = each_set.split(',')[0]
                    input_measure = each_set.split(',')[1]
                    input_dev = Input.query.filter_by(
                        unique_id=input_unique_id).first()
                    if (index < len(each_graph.sensor_ids_measurements.split(';')) and
                            len(colors) > index):
                        color = colors[index]
                    else:
                        color = '#FF00AA'
                    if input_dev is not None:
                        total.append({
                            'unique_id': input_unique_id,
                            'name': input_dev.name,
                            'measure': input_measure,
                            'color': color})
                        index += 1
                index_sum += index

            if each_graph.relay_ids:
                index = 0
                for each_set in each_graph.relay_ids.split(','):
                    output_unique_id = each_set.split(',')[0]
                    output = Output.query.filter_by(
                        unique_id=output_unique_id).first()
                    if (index < len(each_graph.relay_ids.split(',')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum+index]
                    else:
                        color = '#FF00AA'
                    if output is not None:
                        total.append({
                            'unique_id': output_unique_id,
                            'name': output.name,
                            'measure': 'relay duration',
                            'color': color})
                        index += 1
                index_sum += index

            if each_graph.pid_ids:
                index = 0
                for each_set in each_graph.pid_ids.split(';'):
                    pid_unique_id = each_set.split(',')[0]
                    pid_measure = each_set.split(',')[1]
                    pid = PID.query.filter_by(
                        unique_id=pid_unique_id).first()
                    if (index < len(each_graph.pid_ids.split(';')) and
                            len(colors) > index_sum + index):
                        color = colors[index_sum+index]
                    else:
                        color = '#FF00AA'
                    if pid is not None:
                        total.append({
                            'unique_id': pid_unique_id,
                            'name': pid.name,
                            'measure': pid_measure,
                            'color': color})
                        index += 1

            color_count.update({each_graph.id: total})
    except IndexError:
        # Expected exception from previous version database
        # TODO: Remove this exception in next major version release
        pass

    return color_count


def gen(camera):
    """ Video streaming generator function """
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
