# coding=utf-8
""" collection of Page endpoints """
import logging
import os
import csv
import datetime
import glob
import pwd
import subprocess
import time
from collections import OrderedDict

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask_babel import gettext
from flask.blueprints import Blueprint

# Classes
from mycodo.databases.mycodo_db.models import (
    CameraStill,
    DisplayOrder,
    Graph,
    LCD,
    Method,
    Misc,
    PID,
    Relay,
    RelayConditional,
    Sensor,
    SensorConditional,
    Timer
)
from databases.users_db.models import Users
from mycodo.devices.camera_pi import CameraStream

# Functions
from mycodo import flaskforms
from mycodo import flaskutils
from mycodo.mycodo_flask.general_routes import (
    before_blueprint_request,
    inject_mycodo_version,
    logged_in
)
from mycodo.devices.camera_pi import camera_record
from mycodo.utils.database import db_retrieve_table
from mycodo.utils.influx import sum_relay_usage


# Config
from config import (
    DAEMON_LOG_FILE,
    FILE_TIMELAPSE_PARAM,
    HTTP_LOG_FILE,
    INSTALL_DIRECTORY,
    LOGIN_LOG_FILE,
    LOCK_FILE_STREAM,
    LOCK_FILE_TIMELAPSE,
    MEASUREMENT_UNITS,
    RESTORE_LOG_FILE,
    UPGRADE_LOG_FILE,
)

logger = logging.getLogger('mycodo.mycodo_flask.pages')

blueprint = Blueprint('page_routes',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')
blueprint.before_request(before_blueprint_request)  # check if admin was created


@blueprint.context_processor
def inject_dictionary():
    return inject_mycodo_version()


@blueprint.route('/camera', methods=('GET', 'POST'))
def page_camera():
    """
    Page to start/stop video stream or time-lapse, or capture a still image.
    Displays most recent still image and time-lapse image.
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    form_camera = flaskforms.Camera()

    camera_enabled = False
    try:
        if 'start_x=1' in open('/boot/config.txt').read():
            camera_enabled = True
        else:
            flash(gettext("Camera support doesn't appear to be enabled. "
                          "Please enable it with 'sudo raspi-config'"),
                  "error")
    except IOError as e:
        logger.error("Camera IOError raised in '/camera' endpoint: "
                     "{err}".format(err=e))

    # Check if a video stream is active
    stream_locked = os.path.isfile(LOCK_FILE_STREAM)
    if stream_locked and not CameraStream().is_running():
        os.remove(LOCK_FILE_STREAM)
    stream_locked = os.path.isfile(LOCK_FILE_STREAM)

    if request.method == 'POST':
        form_name = request.form['form-name']
        if session['user_group'] == 'guest':
            flaskutils.deny_guest_user()
            return redirect('/camera')
        elif form_name == 'camera':
            if form_camera.Still.data:
                if not stream_locked:
                    try:
                        if CameraStream().is_running():
                            CameraStream().terminate_controller()  # Stop camera stream
                            time.sleep(2)
                        camera = db_retrieve_table(
                            current_app.config['MYCODO_DB_PATH'],
                            CameraStill, entry='first')
                        camera_record('photo', camera)
                    except Exception as msg:
                        flash("Camera Error: {}".format(msg), "error")
                else:
                    flash(gettext("Cannot capture still if stream is active. "
                                  "If it is not active, delete %(file)s.",
                                  file=LOCK_FILE_STREAM),
                          "error")

            elif form_camera.StartTimelapse.data:
                if not stream_locked:
                    # Create lock file and file with time-lapse parameters
                    open(LOCK_FILE_TIMELAPSE, 'a')

                    # Save time-lapse parameters to a csv file to resume
                    # if there is a power outage or reboot.
                    now = time.time()
                    timestamp = datetime.datetime.now().strftime(
                        '%Y-%m-%d_%H-%M-%S')
                    uid_gid = pwd.getpwnam('mycodo').pw_uid
                    timelapse_data = [
                        ['start_time', timestamp],
                        ['end_time', now + float(form_camera.TimelapseRunTime.data)],
                        ['interval', form_camera.TimelapseInterval.data],
                        ['next_capture', now],
                        ['capture_number', 0]]
                    with open(FILE_TIMELAPSE_PARAM, 'w') as time_lapse_file:
                        write_csv = csv.writer(time_lapse_file)
                        for row in timelapse_data:
                            write_csv.writerow(row)
                    os.chown(FILE_TIMELAPSE_PARAM, uid_gid, uid_gid)
                    os.chmod(FILE_TIMELAPSE_PARAM, 0664)
                else:
                    flash(gettext("Cannot start time-lapse if a video stream "
                                  "is active. If it is not active, delete "
                                  "%(file)s.", file=LOCK_FILE_STREAM),
                          "error")

            elif form_camera.StopTimelapse.data:
                try:
                    os.remove(FILE_TIMELAPSE_PARAM)
                    os.remove(LOCK_FILE_TIMELAPSE)
                except IOError as e:
                    logger.error("Camera IOError raised in '/camera' "
                                 "endpoint: {err}".format(err=e))

            elif form_camera.StartStream.data:
                if not is_time_lapse_locked():
                    open(LOCK_FILE_STREAM, 'a')
                    stream_locked = True
                else:
                    flash(gettext("Cannot start stream if a time-lapse is "
                                  "active. If not active, delete %(file)s.",
                                  file=LOCK_FILE_TIMELAPSE),
                          "error")

            elif form_camera.StopStream.data:
                if CameraStream().is_running():
                    CameraStream().terminate()
                if os.path.isfile(LOCK_FILE_STREAM):
                    os.remove(LOCK_FILE_STREAM)
                stream_locked = False

    # Get the full path of latest still image
    try:
        latest_still_img_full_path = max(glob.iglob(
            '{path}/camera-stills/*.jpg'.format(path=INSTALL_DIRECTORY)),
            key=os.path.getmtime)
        ts = os.path.getmtime(latest_still_img_full_path)
        latest_still_img_ts = datetime.datetime.fromtimestamp(ts).strftime("%c")
        latest_still_img = os.path.basename(latest_still_img_full_path)
    except Exception as e:
        logger.error(
            "Exception raised in '/camera' endpoint: {err}".format(err=e))
        latest_still_img_ts = None
        latest_still_img = None

    # Get the full path of latest timelapse image
    try:
        latest_time_lapse_img_full_path = max(glob.iglob(
            '{path}/camera-timelapse/*.jpg'.format(path=INSTALL_DIRECTORY)),
            key=os.path.getmtime)
        ts = os.path.getmtime(latest_time_lapse_img_full_path)
        latest_time_lapse_img_ts = datetime.datetime.fromtimestamp(ts).strftime("%c")
        latest_time_lapse_img = os.path.basename(
            latest_time_lapse_img_full_path)
    except Exception as e:
        logger.error(
            "Exception raised in '/camera' endpoint: {err}".format(err=e))
        latest_time_lapse_img_ts = None
        latest_time_lapse_img = None

    # If time-lapse active, retrieve parameters for display
    dict_time_lapse = {}
    time_now = datetime.datetime.now().strftime('%c')
    if (os.path.isfile(FILE_TIMELAPSE_PARAM) and
            os.path.isfile(LOCK_FILE_TIMELAPSE)):
        with open(FILE_TIMELAPSE_PARAM, mode='r') as infile:
            reader = csv.reader(infile)
            dict_time_lapse = OrderedDict((row[0], row[1]) for row in reader)
        dict_time_lapse['start_time'] = datetime.datetime.strptime(
            dict_time_lapse['start_time'], "%Y-%m-%d_%H-%M-%S")
        dict_time_lapse['start_time'] = dict_time_lapse['start_time'].strftime('%c')
        dict_time_lapse['end_time'] = datetime.datetime.fromtimestamp(
            float(dict_time_lapse['end_time'])).strftime('%c')
        dict_time_lapse['next_capture'] = datetime.datetime.fromtimestamp(
            float(dict_time_lapse['next_capture'])).strftime('%c')

    return render_template('pages/camera.html',
                           camera_enabled=camera_enabled,
                           form_camera=form_camera,
                           latest_still_img_ts=latest_still_img_ts,
                           latest_still_img=latest_still_img,
                           latest_time_lapse_img_ts=latest_time_lapse_img_ts,
                           latest_time_lapse_img=latest_time_lapse_img,
                           stream_locked=stream_locked,
                           time_lapse_locked=is_time_lapse_locked(),
                           time_now=time_now,
                           tl_parameters_dict=dict_time_lapse)


@blueprint.route('/export', methods=('GET', 'POST'))
def page_export():
    """
    Export measurement data in CSV format
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    export_options = flaskforms.ExportOptions()
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    sensor = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Sensor, entry='all')
    relay_choices = flaskutils.choices_id_name(relay)
    sensor_choices = flaskutils.choices_sensors(sensor)

    if request.method == 'POST':
        start_time = export_options.date_range.data.split(' - ')[0]
        start_seconds = int(time.mktime(
            time.strptime(start_time, '%m/%d/%Y %H:%M')))
        end_time = export_options.date_range.data.split(' - ')[1]
        end_seconds = int(time.mktime(
            time.strptime(end_time, '%m/%d/%Y %H:%M')))
        url = '/export_data/{meas}/{id}/{start}/{end}'.format(
            meas=export_options.measurement.data.split(',')[1],
            id=export_options.measurement.data.split(',')[0],
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
                           relay_choices=relay_choices,
                           sensor_choices=sensor_choices)


@blueprint.route('/graph', methods=('GET', 'POST'))
def page_graph():
    """
    Generate custom graphs to display sensor data retrieved from influxdb.
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    # Create form objects
    form_mod_graph = flaskforms.ModGraph()
    form_del_graph = flaskforms.DelGraph()
    form_order_graph = flaskforms.OrderGraph()
    form_add_graph = flaskforms.AddGraph()

    # Retrieve the order to display graphs
    display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').graph
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    # Retrieve tables from SQL database
    graph = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Graph, entry='all')
    pid = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], PID, entry='all')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    sensor = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Sensor, entry='all')

    # Retrieve all choices to populate form drop-down menu
    pid_choices = flaskutils.choices_id_name(pid)
    relay_choices = flaskutils.choices_id_name(relay)
    sensor_choices = flaskutils.choices_sensors(sensor)

    # Add multi-select values as form choices, for validation
    form_mod_graph.pidIDs.choices = []
    form_mod_graph.relayIDs.choices = []
    form_mod_graph.sensorIDs.choices = []
    for key, value in pid_choices.iteritems():
        form_mod_graph.pidIDs.choices.append((key, value))
    for key, value in relay_choices.iteritems():
        form_mod_graph.relayIDs.choices.append((key, value))
    for key, value in sensor_choices.iteritems():
        form_mod_graph.sensorIDs.choices.append((key, value))

    # Generate dictionary of custom colors for each graph
    dict_colors = dict_custom_colors(graph)

    # Detect which form on the page was submitted
    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'modGraph':
            flaskutils.graph_mod(form_mod_graph, request.form)
        elif form_name == 'delGraph':
            flaskutils.graph_del(form_del_graph, display_order)
        elif form_name == 'orderGraph':
            flaskutils.graph_reorder(form_order_graph, display_order)
        elif form_name == 'addGraph':
            flaskutils.graph_add(form_add_graph, display_order)
        return redirect('/graph')

    return render_template('pages/graph.html',
                           graph=graph,
                           pid=pid,
                           relay=relay,
                           sensor=sensor,
                           pid_choices=pid_choices,
                           relay_choices=relay_choices,
                           sensor_choices=sensor_choices,
                           dict_colors=dict_colors,
                           measurement_units=MEASUREMENT_UNITS,
                           displayOrder=display_order,
                           form_mod_graph=form_mod_graph,
                           form_del_graph=form_del_graph,
                           form_order_graph=form_order_graph,
                           form_add_graph=form_add_graph)


@blueprint.route('/graph-async', methods=('GET', 'POST'))
def page_graph_async():
    """ Generate graphs using asynchronous data retrieval """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    sensor = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Sensor, entry='all')
    sensor_choices = flaskutils.choices_sensors(sensor)
    sensor_choices_split = OrderedDict()
    for key, _ in sensor_choices.iteritems():
        order = key.split(",")
        # Separate sensor IDs and measurement types
        sensor_choices_split.update({order[0]: order[1]})

    selected_id = None
    selected_measure = None
    if request.method == 'POST':
        selected_id = request.form['selected_measure'].split(",")[0]
        selected_measure = request.form['selected_measure'].split(",")[1]

    return render_template('pages/graph-async.html',
                           sensor=sensor,
                           sensor_choices=sensor_choices,
                           sensor_choices_split=sensor_choices_split,
                           selected_id=selected_id,
                           selected_measure=selected_measure)


@blueprint.route('/help', methods=('GET', 'POST'))
def page_help():
    """ Display Mycodo manual/help """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    return render_template('manual.html')


@blueprint.route('/info', methods=('GET', 'POST'))
def page_info():
    """ Display page with system information from command line tools """
    if not logged_in():
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

    return render_template('tools/info.html',
                           gpio_readall=gpio_output,
                           df=df_output,
                           free=free_output,
                           ifconfig=ifconfig_output,
                           uname=uname_output,
                           uptime=uptime_output)


@blueprint.route('/lcd', methods=('GET', 'POST'))
def page_lcd():
    """ Display LCD output settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    lcd = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], LCD, entry='all')
    pid = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], PID, entry='all')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    sensor = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Sensor, entry='all')

    display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').lcd
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    form_activate_lcd = flaskforms.ActivateLCD()
    form_add_lcd = flaskforms.AddLCD()
    form_deactivate_lcd = flaskforms.DeactivateLCD()
    form_del_lcd = flaskforms.DelLCD()
    form_mod_lcd = flaskforms.ModLCD()
    form_order_lcd = flaskforms.OrderLCD()
    form_reset_flashing_lcd = flaskforms.ResetFlashingLCD()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'orderLCD':
            flaskutils.lcd_reorder(form_order_lcd, display_order)
        elif form_name == 'addLCD':
            flaskutils.lcd_add(form_add_lcd, display_order)
        elif form_name == 'modLCD':
            flaskutils.lcd_mod(form_mod_lcd)
        elif form_name == 'delLCD':
            flaskutils.lcd_del(form_del_lcd, display_order)
        elif form_name == 'activateLCD':
            flaskutils.lcd_activate(form_activate_lcd)
        elif form_name == 'deactivateLCD':
            flaskutils.lcd_deactivate(form_deactivate_lcd)
        elif form_name == 'resetFlashingLCD':
            flaskutils.lcd_reset_flashing(form_reset_flashing_lcd)
        return redirect('/lcd')

    return render_template('pages/lcd.html',
                           lcd=lcd,
                           pid=pid,
                           relay=relay,
                           sensor=sensor,
                           displayOrder=display_order,
                           form_order_lcd=form_order_lcd,
                           form_add_lcd=form_add_lcd,
                           form_mod_lcd=form_mod_lcd,
                           form_del_lcd=form_del_lcd,
                           form_activate_lcd=form_activate_lcd,
                           form_deactivate_lcd=form_deactivate_lcd,
                           form_reset_flashing_lcd=form_reset_flashing_lcd)


@blueprint.route('/live', methods=('GET', 'POST'))
def page_live():
    """ Page of recent and updating sensor data """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    # Retrieve tables for the data displayed on the live page
    pid = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], PID, entry='all')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    sensor = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Sensor, entry='all')
    timer = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Timer, entry='all')

    # Retrieve the display order of the controllers
    pid_display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').pid
    if pid_display_order_unsplit:
        pid_display_order = pid_display_order_unsplit.split(",")
    else:
        pid_display_order = []

    sensor_display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').sensor
    if sensor_display_order_unsplit:
        sensor_display_order = sensor_display_order_unsplit.split(",")
    else:
        sensor_display_order = []

    # Filter only activated sensors
    sensor_order_sorted = []
    for each_sensor_order in sensor_display_order:
        for each_sensor in sensor:
            if (each_sensor_order == each_sensor.id and
                    each_sensor.activated):
                sensor_order_sorted.append(each_sensor.id)

    # Retrieve only parent method columns
    method = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Method)
    method = method.filter(
        Method.method_order == 0).all()

    return render_template('pages/live.html',
                           method=method,
                           pid=pid,
                           relay=relay,
                           sensor=sensor,
                           timer=timer,
                           pidDisplayOrder=pid_display_order,
                           sensorDisplayOrderSorted=sensor_order_sorted)


@blueprint.route('/logview', methods=('GET', 'POST'))
def page_logview():
    """ Display the last (n) lines from a log file """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    form_log_view = flaskforms.LogView()
    log_output = None
    lines = 30
    logfile = ''
    if request.method == 'POST':
        if session['user_group'] == 'guest':
            flaskutils.deny_guest_user()
            return redirect('/logview')
        if form_log_view.lines.data:
            lines = form_log_view.lines.data
        if form_log_view.loglogin.data:
            logfile = LOGIN_LOG_FILE
        elif form_log_view.loghttp.data:
            logfile = HTTP_LOG_FILE
        elif form_log_view.logdaemon.data:
            logfile = DAEMON_LOG_FILE
        elif form_log_view.logupgrade.data:
            logfile = UPGRADE_LOG_FILE
        elif form_log_view.logrestore.data:
            logfile = RESTORE_LOG_FILE

        # Get contents from file
        if os.path.isfile(logfile):
            log = subprocess.Popen('tail -n ' + str(lines) + ' ' + logfile,
                                   stdout=subprocess.PIPE,
                                   shell=True)
            (log_output, _) = log.communicate()
            log.wait()
        else:
            log_output = 404

    return render_template('tools/logview.html',
                           form_log_view=form_log_view,
                           lines=lines,
                           logfile=logfile,
                           log_output=log_output)


@blueprint.route('/notes', methods=('GET', 'POST'))
def page_notes():
    """ Display notes viewer/editor """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    return render_template('tools/notes.html')


@blueprint.route('/pid', methods=('GET', 'POST'))
def page_pid():
    """ Display PID settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    pids = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], PID, entry='all')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    sensor = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Sensor, entry='all')

    display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').pid
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    form_add_pid = flaskforms.AddPID()
    form_mod_pid = flaskforms.ModPID()

    method = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Method)
    method = method.filter(
        Method.method_order == 0).all()

    if request.method == 'POST':
        if session['user_group'] == 'guest':
            flaskutils.deny_guest_user()
            return redirect('/pid')
        form_name = request.form['form-name']
        if form_name == 'addPID':
            flaskutils.pid_add(form_add_pid, display_order)
        elif form_name == 'modPID':
            if form_mod_pid.mod_pid_del.data:
                flaskutils.pid_del(
                    form_mod_pid.modPID_id.data, display_order)
            elif form_mod_pid.mod_pid_order_up.data:
                flaskutils.pid_reorder(
                    form_mod_pid.modPID_id.data, display_order, 'up')
            elif form_mod_pid.mod_pid_order_down.data:
                flaskutils.pid_reorder(
                    form_mod_pid.modPID_id.data, display_order, 'down')
            elif form_mod_pid.mod_pid_activate.data:
                flaskutils.pid_activate(
                    form_mod_pid.modPID_id.data)
            elif form_mod_pid.mod_pid_deactivate.data:
                flaskutils.pid_deactivate(
                    form_mod_pid.modPID_id.data)
            elif form_mod_pid.mod_pid_hold.data:
                flaskutils.pid_manipulate(
                    form_mod_pid.modPID_id.data, 'Hold')
            elif form_mod_pid.mod_pid_pause.data:
                flaskutils.pid_manipulate(
                    form_mod_pid.modPID_id.data, 'Pause')
            elif form_mod_pid.mod_pid_resume.data:
                flaskutils.pid_manipulate(
                    form_mod_pid.modPID_id.data, 'Resume')
            else:
                flaskutils.pid_mod(form_mod_pid)

        return redirect('/pid')

    return render_template('pages/pid.html',
                           method=method,
                           pids=pids,
                           relay=relay,
                           sensor=sensor,
                           displayOrder=display_order,
                           form_add_pid=form_add_pid,
                           form_mod_pid=form_mod_pid)


@blueprint.route('/relay', methods=('GET', 'POST'))
def page_relay():
    """ Display relay status and config """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    lcd = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], LCD, entry='all')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    relayconditional = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], RelayConditional, entry='all')
    users = db_retrieve_table(
        current_app.config['USER_DB_PATH'], Users, entry='all')

    display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').relay
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    form_add_relay = flaskforms.AddRelay()
    form_del_relay = flaskforms.DelRelay()
    form_mod_relay = flaskforms.ModRelay()
    form_order_relay = flaskforms.OrderRelay()
    form_relay_on_off = flaskforms.RelayOnOff()
    form_add_relay_cond = flaskforms.AddRelayConditional()
    form_mod_relay_cond = flaskforms.ModRelayConditional()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'RelayOnOff':
            flaskutils.relay_on_off(form_relay_on_off)
        elif form_name == 'addRelay':
            flaskutils.relay_add(form_add_relay, display_order)
        elif form_name == 'modRelay':
            flaskutils.relay_mod(form_mod_relay)
        elif form_name == 'delRelay':
            flaskutils.relay_del(form_del_relay, display_order)
        elif form_name == 'orderRelay':
            flaskutils.relay_reorder(form_order_relay, display_order)
        elif form_name == 'addRelayConditional':
            flaskutils.relay_conditional_add(form_add_relay_cond)
        elif form_name == 'modRelayConditional':
            flaskutils.relay_conditional_mod(form_mod_relay_cond)
        return redirect('/relay')

    return render_template('pages/relay.html',
                           lcd=lcd,
                           relay=relay,
                           relayconditional=relayconditional,
                           users=users,
                           displayOrder=display_order,
                           form_order_relay=form_order_relay,
                           form_add_relay=form_add_relay,
                           form_mod_relay=form_mod_relay,
                           form_del_relay=form_del_relay,
                           form_relay_on_off=form_relay_on_off,
                           form_add_relay_cond=form_add_relay_cond,
                           form_mod_relay_cond=form_mod_relay_cond)


@blueprint.route('/sensor', methods=('GET', 'POST'))
def page_sensor():
    """ Display sensor settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    lcd = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], LCD, entry='all')
    pid = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], PID, entry='all')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    sensor = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Sensor, entry='all')
    sensor_conditional = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], SensorConditional, entry='all')
    users = db_retrieve_table(
        current_app.config['USER_DB_PATH'], Users, entry='all')

    display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').sensor
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    form_add_sensor = flaskforms.AddSensor()
    form_mod_sensor = flaskforms.ModSensor()
    form_mod_sensor_cond = flaskforms.ModSensorConditional()

    # Create list of file names from the sensor_options directory
    # Used in generating the correct options for each sensor/device
    sensor_template_list = []
    sensor_path = "{path}/mycodo/mycodo_flask/templates/pages/sensor_options/".format(
        path=INSTALL_DIRECTORY)
    for (_, _, file_names) in os.walk(sensor_path):
        sensor_template_list.extend(file_names)
        break
    sensor_templates = []
    for each_file_name in sensor_template_list:
        sensor_templates.append(each_file_name.split(".")[0])

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addSensor':
            flaskutils.sensor_add(form_add_sensor, display_order)
        elif form_name == 'modSensor':
            if form_mod_sensor.modSensorSubmit.data:
                flaskutils.sensor_mod(form_mod_sensor)
            elif form_mod_sensor.delSensorSubmit.data:
                flaskutils.sensor_del(form_mod_sensor, display_order)
            elif (form_mod_sensor.orderSensorUp.data or
                    form_mod_sensor.orderSensorDown.data):
                flaskutils.sensor_reorder(form_mod_sensor, display_order)
            elif form_mod_sensor.activateSensorSubmit.data:
                flaskutils.sensor_activate(form_mod_sensor)
            elif form_mod_sensor.deactivateSensorSubmit.data:
                flaskutils.sensor_deactivate(form_mod_sensor)
            elif form_mod_sensor.sensorCondAddSubmit.data:
                flaskutils.sensor_conditional_add(form_mod_sensor)
        elif form_name == 'modSensorConditional':
            flaskutils.sensor_conditional_mod(form_mod_sensor_cond)
        return redirect('/sensor')

    return render_template('pages/sensor.html',
                           lcd=lcd,
                           pid=pid,
                           relay=relay,
                           sensor=sensor,
                           sensor_conditional=sensor_conditional,
                           sensor_templates=sensor_templates,
                           users=users,
                           displayOrder=display_order,
                           form_add_sensor=form_add_sensor,
                           form_mod_sensor=form_mod_sensor,
                           form_mod_sensor_cond=form_mod_sensor_cond)


@blueprint.route('/timer', methods=('GET', 'POST'))
def page_timer():
    """ Display Timer settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    timer = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Timer, entry='all')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')
    relay_choices = flaskutils.choices_id_name(relay)

    display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').timer
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    form_timer = flaskforms.Timer()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addTimer':
            flaskutils.timer_add(form_timer,
                                 request.form['timer_type'],
                                 display_order)
        elif form_name == 'modTimer':
            if form_timer.timerDel.data:
                flaskutils.timer_del(form_timer, display_order)
            elif (form_timer.orderTimerUp.data or
                    form_timer.orderTimerDown.data):
                flaskutils.timer_reorder(form_timer, display_order)
            elif form_timer.activate.data:
                flaskutils.timer_activate(form_timer)
            elif form_timer.deactivate.data:
                flaskutils.timer_deactivate(form_timer)
            elif form_timer.timerMod.data:
                flaskutils.timer_mod(form_timer)
        return redirect('/timer')

    return render_template('pages/timer.html',
                           timer=timer,
                           displayOrder=display_order,
                           relay_choices=relay_choices,
                           form_timer=form_timer)


@blueprint.route('/usage', methods=('GET', 'POST'))
def page_usage():
    """ Display relay usage (duration and energy usage/cost) """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    misc = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Misc, entry='first')
    relay = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay, entry='all')

    display_order_unsplit = db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, entry='first').relay
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    # Calculate the number of seconds since the (n)th day of tyhe month
    # Enables usage/cost assessments to align with a power bill cycle
    now = datetime.date.today()
    past_month_seconds = 0
    day = misc.relay_stats_dayofmonth
    if 4 <= day <= 20 or 24 <= day <= 30:
        date_suffix = 'th'
    else:
        date_suffix = ['st', 'nd', 'rd'][day % 10 - 1]
    if misc.relay_stats_dayofmonth == datetime.datetime.today().day:
        dt_now = datetime.datetime.now()
        past_month_seconds = (dt_now - dt_now.replace(
            hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    elif misc.relay_stats_dayofmonth > datetime.datetime.today().day:
        first_day = now.replace(day=1)
        last_month = first_day - datetime.timedelta(days=1)
        past_month = last_month.replace(day=misc.relay_stats_dayofmonth)
        past_month_seconds = (now - past_month).total_seconds()
    elif misc.relay_stats_dayofmonth < datetime.datetime.today().day:
        past_month = now.replace(day=misc.relay_stats_dayofmonth)
        past_month_seconds = (now - past_month).total_seconds()

    # Calculate relay on duration for different time periods
    relay_each_duration = {}
    relay_sum_duration = dict.fromkeys(
        ['1d', '1w', '1m', '1m-date', '1y'], 0)
    relay_sum_kwh = dict.fromkeys(
        ['1d', '1w', '1m', '1m-date', '1y'], 0)
    for each_relay in relay:
        relay_each_duration[each_relay.id] = {}
        relay_each_duration[each_relay.id]['1d'] = sum_relay_usage(
            each_relay.id, 86400) / 3600
        relay_each_duration[each_relay.id]['1w'] = sum_relay_usage(
            each_relay.id, 604800) / 3600
        relay_each_duration[each_relay.id]['1m'] = sum_relay_usage(
            each_relay.id, 2629743) / 3600
        relay_each_duration[each_relay.id]['1m-date'] = sum_relay_usage(
            each_relay.id, int(past_month_seconds)) / 3600
        relay_each_duration[each_relay.id]['1y'] = sum_relay_usage(
            each_relay.id, 31556926) / 3600
        relay_sum_duration['1d'] += relay_each_duration[each_relay.id]['1d']
        relay_sum_duration['1w'] += relay_each_duration[each_relay.id]['1w']
        relay_sum_duration['1m'] += relay_each_duration[each_relay.id]['1m']
        relay_sum_duration['1m-date'] += relay_each_duration[each_relay.id]['1m-date']
        relay_sum_duration['1y'] += relay_each_duration[each_relay.id]['1y']
        relay_sum_kwh['1d'] += (
            misc.relay_stats_volts * each_relay.amps *
            relay_each_duration[each_relay.id]['1d'] / 1000)
        relay_sum_kwh['1w'] += (
            misc.relay_stats_volts * each_relay.amps *
            relay_each_duration[each_relay.id]['1w'] / 1000)
        relay_sum_kwh['1m'] += (
            misc.relay_stats_volts * each_relay.amps *
            relay_each_duration[each_relay.id]['1m'] / 1000)
        relay_sum_kwh['1m-date'] += (
            misc.relay_stats_volts * each_relay.amps *
            relay_each_duration[each_relay.id]['1m-date'] / 1000)
        relay_sum_kwh['1y'] += (
            misc.relay_stats_volts * each_relay.amps *
            relay_each_duration[each_relay.id]['1y'] / 1000)

    return render_template('tools/usage.html',
                           display_order=display_order,
                           misc=misc,
                           relay=relay,
                           relay_each_duration=relay_each_duration,
                           relay_sum_duration=relay_sum_duration,
                           relay_sum_kwh=relay_sum_kwh,
                           date_suffix=date_suffix)


def dict_custom_colors(graph):
    """
    Generate lists of custom colors from CSV strings saved in the database.
    If custom colors aren't already saved, fill in with a default palette.

    :param graph: graph SQL object
    :return: dictionary of graph_ids and lists of custom colors
    """
    # Count how many lines will need a custom color input
    dark_themes = ['cyborg', 'darkly', 'slate', 'sun', 'superhero']
    if session['user_theme'] in dark_themes:
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
    for each_graph in graph:
        # Get current saved colors
        if each_graph.colors:  # Split into list
            colors = each_graph.colors.split(',')
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
        if each_graph.sensor_ids:
            for each_set in each_graph.sensor_ids.split(';'):
                if (index < len(each_graph.sensor_ids.split(';')) and
                        len(colors) > index):
                    total.append([
                        '{id} {measure}'.format(
                            id=each_set.split(',')[0],
                            measure=each_set.split(',')[1]),
                        colors[index]])
                else:
                    total.append([
                        '{id} {measure}'.format(
                            id=each_set.split(',')[0],
                            measure=each_set.split(',')[1]),
                        '#FF00AA'])
                index += 1
            index_sum += index

        if each_graph.relay_ids:
            index = 0
            for each_set in each_graph.relay_ids.split(','):
                if (index < len(each_graph.relay_ids.split(',')) and
                        len(colors) > index_sum + index):
                    total.append([
                        '{id} Relay'.format(id=each_set.split(',')[0]),
                        colors[index_sum+index]])
                else:
                    total.append([
                        '{id} Relay'.format(id=each_set.split(',')[0]),
                        '#FF00AA'])
                index += 1
            index_sum += index

        if each_graph.pid_ids:
            index = 0
            for each_set in each_graph.pid_ids.split(','):
                if (index < len(each_graph.pid_ids.split(',')) and
                        len(colors) > index_sum + index):
                    total.append([
                        '{id} PID Setpoint'.format(id=each_set.split(',')[0]),
                        colors[index_sum+index]])
                else:
                    total.append([
                        '{id} PID Setpoint'.format(id=each_set.split(',')[0]),
                        '#FF00AA'])
                index += 1

        color_count.update({each_graph.id: total})

    return color_count


def gen(camera):
    """ Video streaming generator function """
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def is_time_lapse_locked():
    """Check if a time-lapse is active"""
    time_lapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)
    if time_lapse_locked and not os.path.isfile(FILE_TIMELAPSE_PARAM):
        os.remove(LOCK_FILE_TIMELAPSE)
    elif not time_lapse_locked and os.path.isfile(FILE_TIMELAPSE_PARAM):
        os.remove(FILE_TIMELAPSE_PARAM)
    return os.path.isfile(LOCK_FILE_TIMELAPSE)
