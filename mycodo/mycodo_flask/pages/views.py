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

from flask.blueprints import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from databases.mycodo_db.models import CameraStill
from databases.mycodo_db.models import DisplayOrder
from databases.mycodo_db.models import Graph
from databases.mycodo_db.models import LCD
from databases.mycodo_db.models import Log
from databases.mycodo_db.models import Misc
from databases.mycodo_db.models import PID
from databases.mycodo_db.models import RelayConditional
from databases.mycodo_db.models import Sensor
from databases.mycodo_db.models import SensorConditional
from databases.mycodo_db.models import Timer
from databases.users_db.models import Users

from devices.camera_pi import CameraStream
from utils.camera import camera_record

from config import DAEMON_LOG_FILE
from config import FILE_TIMELAPSE_PARAM
from config import HTTP_LOG_FILE
from config import INSTALL_DIRECTORY
from config import LOG_PATH
from config import LOGIN_LOG_FILE
from config import LOCK_FILE_STREAM
from config import LOCK_FILE_TIMELAPSE
from config import RESTORE_LOG_FILE
from config import UPDATE_LOG_FILE

from mycodo.databases.utils import session_scope
from mycodo.databases.mycodo_db.models import Method, Relay

from mycodo import flaskforms
from mycodo import flaskutils
from mycodo.mycodo_flask.general_routes import (before_blueprint_request,
                                                inject_mycodo_version,
                                                logged_in)


logger = logging.getLogger('mycodo.mycodo_flask.pages')

blueprint = Blueprint('page_routes', __name__, static_folder='../static', template_folder='../templates')
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

    formCamera = flaskforms.Camera()

    camera_enabled = False
    try:
        if 'start_x=1' in open('/boot/config.txt').read():
            camera_enabled = True
        else:
            flash("Camera support doesn't appear to be enabled. Please "
                  "enable it with 'sudo raspi-config'", "error")
    except IOError as e:
        logger.error("Camera IOError raised in '/camera' endpoint: {err}".format(err=e))

    # Check if a video stream is active
    stream_locked = os.path.isfile(LOCK_FILE_STREAM)
    if stream_locked and not CameraStream().is_running():
        os.remove(LOCK_FILE_STREAM)
        stream_locked = False
    stream_locked = os.path.isfile(LOCK_FILE_STREAM)

    # Check if a timelapse is active
    timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)
    if timelapse_locked and not os.path.isfile(FILE_TIMELAPSE_PARAM):
        os.remove(LOCK_FILE_TIMELAPSE)
    elif not timelapse_locked and os.path.isfile(FILE_TIMELAPSE_PARAM):
        os.remove(FILE_TIMELAPSE_PARAM)
    timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)

    if request.method == 'POST':
        form_name = request.form['form-name']
        if session['user_group'] == 'guest':
            flash("Guests are not permitted to use camera options.",
                  "error")
            return redirect('/camera')
        elif form_name == 'camera':
            if formCamera.Still.data:
                if not stream_locked:
                    try:
                        if CameraStream().is_running():
                            CameraStream().terminate()  # Stop camera stream
                            time.sleep(2)
                        camera = flaskutils.db_retrieve_table(
                            current_app.config['MYCODO_DB_PATH'], CameraStill, first=True)
                        camera_record(INSTALL_DIRECTORY, 'photo', camera)
                    except Exception as msg:
                        flash("Camera Error: {}".format(msg), "error")
                else:
                    flash("Cannot capture still if stream is"
                          " active. If it is not active, delete "
                          "{sfile}.".format(sfile=LOCK_FILE_STREAM),
                          "error")

            elif formCamera.StartTimelapse.data:
                if not stream_locked:
                    # Create lockfile and file with time-lapse parameters
                    open(LOCK_FILE_TIMELAPSE, 'a')

                    # Save time-lapse parameters to a csv file to resume
                    # if there is a power outage or reboot.
                    now = time.time()
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    uid_gid = pwd.getpwnam('mycodo').pw_uid
                    timelapse_data = [['start_time', timestamp],
                                      ['end_time', now + float(formCamera.TimelapseRunTime.data)],
                                      ['interval', formCamera.TimelapseInterval.data],
                                      ['next_capture', now],
                                      ['capture_number', 0]]
                    with open(FILE_TIMELAPSE_PARAM, 'w') as timelapse_file:
                        write_csv = csv.writer(timelapse_file)
                        for row in timelapse_data:
                            write_csv.writerow(row)
                    os.chown(FILE_TIMELAPSE_PARAM, uid_gid, uid_gid)
                    os.chmod(FILE_TIMELAPSE_PARAM, 0664)
                else:
                    flash("Cannot start time-lapse if a stream is active. "
                          "If it is not active, delete {}.".format(
                            LOCK_FILE_STREAM), "error")

            elif formCamera.StopTimelapse.data:
                try:
                    os.remove(FILE_TIMELAPSE_PARAM)
                    os.remove(LOCK_FILE_TIMELAPSE)
                except IOError as e:
                    logger.error("Camera IOError raised in '/camera' endpoint: {err}".format(err=e))

            elif formCamera.StartStream.data:
                if not timelapse_locked:
                    open(LOCK_FILE_STREAM, 'a')
                    stream_locked = True
                else:
                    flash("Cannot start stream if a timelapse is active. "
                          "If not active, delete {}.".format(LOCK_FILE_TIMELAPSE),
                          "error")

            elif formCamera.StopStream.data:
                if CameraStream().is_running():
                    CameraStream().terminate()
                if os.path.isfile(LOCK_FILE_STREAM):
                    os.remove(LOCK_FILE_STREAM)
                stream_locked = False

    # Check again if timelapse is active to catch if it started
    timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)
    if timelapse_locked and not os.path.isfile(FILE_TIMELAPSE_PARAM):
        os.remove(LOCK_FILE_TIMELAPSE)
    elif not timelapse_locked and os.path.isfile(FILE_TIMELAPSE_PARAM):
        os.remove(FILE_TIMELAPSE_PARAM)
    timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)

    # Get the full path of latest still image
    try:
        latest_still_img_fullpath = max(glob.iglob(INSTALL_DIRECTORY + '/camera-stills/*.jpg'),
                                        key=os.path.getmtime)
        ts = os.path.getmtime(latest_still_img_fullpath)
        latest_still_img_ts = datetime.datetime.fromtimestamp(ts).strftime("%c")
        latest_still_img = os.path.basename(latest_still_img_fullpath)
    except Exception as e:
        logger.error("Exception raised in '/camera' endpoint: {err}".format(err=e))
        latest_still_img_ts = None
        latest_still_img = None

    # Get the full path of latest timelapse image
    try:
        latest_timelapse_img_fullpath = max(glob.iglob(INSTALL_DIRECTORY + '/camera-timelapse/*.jpg'),
                                            key=os.path.getmtime)
        ts = os.path.getmtime(latest_timelapse_img_fullpath)
        latest_timelapse_img_ts = datetime.datetime.fromtimestamp(ts).strftime("%c")
        latest_timelapse_img = os.path.basename(latest_timelapse_img_fullpath)
    except Exception as e:
        logger.error("Exception raised in '/camera' endpoint: {err}".format(err=e))
        latest_timelapse_img_ts = None
        latest_timelapse_img = None

    # If timelapse active, retrieve parameters for display
    dict_timelapse = {}
    time_now = datetime.datetime.now().strftime('%c')
    if (os.path.isfile(FILE_TIMELAPSE_PARAM) and
            os.path.isfile(LOCK_FILE_TIMELAPSE)):
        with open(FILE_TIMELAPSE_PARAM, mode='r') as infile:
            reader = csv.reader(infile)
            dict_timelapse = OrderedDict((row[0], row[1]) for row in reader)
        dict_timelapse['start_time'] = datetime.datetime.strptime(dict_timelapse['start_time'], "%Y-%m-%d_%H-%M-%S")
        dict_timelapse['start_time'] = dict_timelapse['start_time'].strftime('%c')
        dict_timelapse['end_time'] = datetime.datetime.fromtimestamp(float(dict_timelapse['end_time'])).strftime(
            '%c')
        dict_timelapse['next_capture'] = datetime.datetime.fromtimestamp(
            float(dict_timelapse['next_capture'])).strftime('%c')

    return render_template('pages/camera.html',
                           camera_enabled=camera_enabled,
                           formCamera=formCamera,
                           latest_still_img_ts=latest_still_img_ts,
                           latest_still_img=latest_still_img,
                           latest_timelapse_img_ts=latest_timelapse_img_ts,
                           latest_timelapse_img=latest_timelapse_img,
                           stream_locked=stream_locked,
                           timelapse_locked=timelapse_locked,
                           time_now=time_now,
                           tl_parameters_dict=dict_timelapse)


@blueprint.route('/graph', methods=('GET', 'POST'))
def page_graph():
    """
    Generate custom graphs to display sensor data retrieved from influxdb.
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    graph = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Graph)
    pid = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], PID)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).graph
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    # Create form objects
    formModGraph = flaskforms.ModGraph()
    formDelGraph = flaskforms.DelGraph()
    formOrderGraph = flaskforms.OrderGraph()
    formAddGraph = flaskforms.AddGraph()

    # Units to display for each measurement in the graph legend
    measurement_units = {'cpu_load_1m': '',
                         'cpu_load_5m': '',
                         'cpu_load_15m': '',
                         'temperature': '°C'.decode('utf-8'),
                         'temperature_object': '°C'.decode('utf-8'),
                         'temperature_die': '°C'.decode('utf-8'),
                         'humidity': ' %',
                         'dewpoint': '°C'.decode('utf-8'),
                         'co2': ' ppmv',
                         'lux': 'lx',
                         'pressure': ' Pa',
                         'altitude': ' m'}

    # Retrieve all choices to populate form dropdowns
    pid_choices = flaskutils.choices_id_name(pid)
    relay_choices = flaskutils.choices_id_name(relay)
    sensor_choices = flaskutils.choices_sensors(sensor)

    formModGraph.pidIDs.choices = []
    formModGraph.relayIDs.choices = []
    formModGraph.sensorIDs.choices = []

    for key, value in pid_choices.iteritems():
        formModGraph.pidIDs.choices.append((key, value))
    for key, value in relay_choices.iteritems():
        formModGraph.relayIDs.choices.append((key, value))
    sensor_choices_split = OrderedDict()
    for key, value in sensor_choices.iteritems():
        # Add miltiselect values as form choices, for validation
        formModGraph.sensorIDs.choices.append((key, value))
        order = key.split(",")
        # Separate sensor IDs and measurement types
        sensor_choices_split.update({order[0]: order[1]})

    # Detect which form on the page was submitted
    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'modGraph':
            flaskutils.graph_mod(formModGraph)
        elif form_name == 'delGraph':
            flaskutils.graph_del(formDelGraph, display_order)
        elif form_name == 'orderGraph':
            flaskutils.graph_reorder(formOrderGraph, display_order)
        elif form_name == 'addGraph':
            flaskutils.graph_add(formAddGraph, display_order)
        return redirect('/graph')

    return render_template('pages/graph.html',
                           graph=graph,
                           pid=pid,
                           relay=relay,
                           sensor=sensor,
                           pid_choices=pid_choices,
                           relay_choices=relay_choices,
                           sensor_choices=sensor_choices,
                           sensor_choices_split=sensor_choices_split,
                           measurement_units=measurement_units,
                           displayOrder=display_order,
                           formModGraph=formModGraph,
                           formDelGraph=formDelGraph,
                           formOrderGraph=formOrderGraph,
                           formAddGraph=formAddGraph)


@blueprint.route('/graph-async', methods=('GET', 'POST'))
def page_graph_async():
    """ Generate graphs using ascynchronous data retrieval """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)
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

    lcd = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], LCD)
    pid = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], PID)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).lcd
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    formActivateLCD = flaskforms.ActivateLCD()
    formAddLCD = flaskforms.AddLCD()
    formDeactivateLCD = flaskforms.DeactivateLCD()
    formDelLCD = flaskforms.DelLCD()
    formModLCD = flaskforms.ModLCD()
    formOrderLCD = flaskforms.OrderLCD()
    formResetFlashingLCD = flaskforms.ResetFlashingLCD()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'orderLCD':
            flaskutils.lcd_reorder(formOrderLCD, display_order)
        elif form_name == 'addLCD':
            flaskutils.lcd_add(formAddLCD, display_order)
        elif form_name == 'modLCD':
            flaskutils.lcd_mod(formModLCD)
        elif form_name == 'delLCD':
            flaskutils.lcd_del(formDelLCD, display_order)
        elif form_name == 'activateLCD':
            flaskutils.lcd_activate(formActivateLCD)
        elif form_name == 'deactivateLCD':
            flaskutils.lcd_deactivate(formDeactivateLCD)
        elif form_name == 'resetFlashingLCD':
            flaskutils.lcd_reset_flashing(formResetFlashingLCD)
        return redirect('/lcd')

    return render_template('pages/lcd.html',
                           lcd=lcd,
                           pid=pid,
                           relay=relay,
                           sensor=sensor,
                           displayOrder=display_order,
                           formOrderLCD=formOrderLCD,
                           formAddLCD=formAddLCD,
                           formModLCD=formModLCD,
                           formDelLCD=formDelLCD,
                           formActivateLCD=formActivateLCD,
                           formDeactivateLCD=formDeactivateLCD,
                           formResetFlashingLCD=formResetFlashingLCD)


@blueprint.route('/live', methods=('GET', 'POST'))
def page_live():
    """ Page of recent and updating sensor data """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    # Retrieve tables for the data displayed on the live page
    pid = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], PID)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)
    timer = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Timer)

    # Retrieve the display order of the controllers
    pid_display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).pid
    if pid_display_order_unsplit:
        pid_display_order = pid_display_order_unsplit.split(",")
    else:
        pid_display_order = []

    sensor_display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).sensor
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
    with session_scope(current_app.config['MYCODO_DB_PATH']) as new_session:
        method = new_session.query(Method).filter(
            Method.method_order == 0).all()
        new_session.expunge_all()
        new_session.close()

    return render_template('pages/live.html',
                           method=method,
                           pid=pid,
                           relay=relay,
                           sensor=sensor,
                           timer=timer,
                           pidDisplayOrder=pid_display_order,
                           sensorDisplayOrderSorted=sensor_order_sorted)


@blueprint.route('/log', methods=('GET', 'POST'))
def page_log():
    """ Display log settings (writing logs of data from influxdb) """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    log = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Log)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).log
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    formLog = flaskforms.Log()

    # Determine if a log file exists for each log controller
    log_file_exists = {}
    for each_log in log:
        fname = '{}/{}-{}.log'.format(LOG_PATH,
                                      each_log.sensor_id,
                                      each_log.measure_type)
        log_file_exists[each_log.id] = bool(os.path.isfile(fname))

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addLog':
            flaskutils.log_add(formLog, display_order)
        elif form_name == 'modLog':
            if formLog.logDel.data:
                flaskutils.log_del(formLog, display_order)
            elif formLog.orderLogUp.data or formLog.orderLogDown.data:
                flaskutils.log_reorder(formLog, display_order)
            elif formLog.activate.data:
                flaskutils.log_activate(formLog)
            elif formLog.deactivate.data:
                flaskutils.log_deactivate(formLog)
            elif formLog.logMod.data:
                flaskutils.log_mod(formLog)
        return redirect('/log')

    return render_template('pages/log.html',
                           log=log,
                           sensor=sensor,
                           displayOrder=display_order,
                           log_file_exists=log_file_exists,
                           formLog=formLog)


@blueprint.route('/logview', methods=('GET', 'POST'))
def page_logview():
    """ Display the last (n) lines from a log file """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    formLogView = flaskforms.LogView()

    log_output = None
    lines = 30
    logfile = ''
    if request.method == 'POST':
        if session['user_group'] == 'guest':
            flash('Guests are not permitted to view logs.', 'error')
            return redirect('/logview')
        if formLogView.lines.data:
            lines = formLogView.lines.data
        if formLogView.loglogin.data:
            logfile = LOGIN_LOG_FILE
        elif formLogView.loghttp.data:
            logfile = HTTP_LOG_FILE
        elif formLogView.logdaemon.data:
            logfile = DAEMON_LOG_FILE
        elif formLogView.logupdate.data:
            logfile = UPDATE_LOG_FILE
        elif formLogView.logrestore.data:
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
                           formLogView=formLogView,
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

    pids = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], PID)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).pid
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    formModPIDMethod = flaskforms.ModPIDMethod()
    formActivatePID = flaskforms.ActivatePID()
    formAddPID = flaskforms.AddPID()
    formDeactivatePID = flaskforms.DeactivatePID()
    formDelPID = flaskforms.DelPID()
    formModPID = flaskforms.ModPID()
    formOrderPID = flaskforms.OrderPID()

    with session_scope(current_app.config['MYCODO_DB_PATH']) as new_session:
        method = new_session.query(Method)
        method = method.filter(Method.method_order == 0).all()
        new_session.expunge_all()
        new_session.close()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addPID':
            flaskutils.pid_add(formAddPID, display_order)
        elif form_name == 'modPID':
            flaskutils.pid_mod(formModPID)
        elif form_name == 'modPIDMethod':
            flaskutils.pid_mod_method(formModPIDMethod)
        elif form_name == 'delPID':
            flaskutils.pid_del(formDelPID, display_order)
        elif form_name == 'orderPID':
            flaskutils.pid_reorder(formOrderPID, display_order)
        elif form_name == 'activatePID':
            flaskutils.pid_activate(formActivatePID)
        elif form_name == 'deactivatePID':
            flaskutils.pid_deactivate(formDeactivatePID)
        return redirect('/pid')

    return render_template('pages/pid.html',
                           method=method,
                           pids=pids,
                           relay=relay,
                           sensor=sensor,
                           displayOrder=display_order,
                           formModPIDMethod=formModPIDMethod,
                           formOrderPID=formOrderPID,
                           formAddPID=formAddPID,
                           formModPID=formModPID,
                           formDelPID=formDelPID,
                           formActivatePID=formActivatePID,
                           formDeactivatePID=formDeactivatePID)


@blueprint.route('/relay', methods=('GET', 'POST'))
def page_relay():
    """ Display relay status and config """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    lcd = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], LCD)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)
    relayconditional = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], RelayConditional)
    users = flaskutils.db_retrieve_table(current_app.config['USER_DB_PATH'], Users)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).relay
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    formAddRelay = flaskforms.AddRelay()
    formDelRelay = flaskforms.DelRelay()
    formModRelay = flaskforms.ModRelay()
    formOrderRelay = flaskforms.OrderRelay()
    formRelayOnOff = flaskforms.RelayOnOff()
    formAddRelayCond = flaskforms.AddRelayConditional()
    formModRelayCond = flaskforms.ModRelayConditional()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'RelayOnOff':
            flaskutils.relay_on_off(formRelayOnOff)
        elif form_name == 'addRelay':
            flaskutils.relay_add(formAddRelay, display_order)
        elif form_name == 'modRelay':
            flaskutils.relay_mod(formModRelay)
        elif form_name == 'delRelay':
            flaskutils.relay_del(formDelRelay, display_order)
        elif form_name == 'orderRelay':
            flaskutils.relay_reorder(formOrderRelay, display_order)
        elif form_name == 'addRelayConditional':
            flaskutils.relay_conditional_add(formAddRelayCond)
        elif form_name == 'modRelayConditional':
            flaskutils.relay_conditional_mod(formModRelayCond)
        return redirect('/relay')

    return render_template('pages/relay.html',
                           lcd=lcd,
                           relay=relay,
                           relayconditional=relayconditional,
                           users=users,
                           displayOrder=display_order,
                           formOrderRelay=formOrderRelay,
                           formAddRelay=formAddRelay,
                           formModRelay=formModRelay,
                           formDelRelay=formDelRelay,
                           formRelayOnOff=formRelayOnOff,
                           formAddRelayCond=formAddRelayCond,
                           formModRelayCond=formModRelayCond)


@blueprint.route('/sensor', methods=('GET', 'POST'))
def page_sensor():
    """ Display sensor settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    lcd = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], LCD)
    pid = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], PID)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)
    sensor = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Sensor)
    sensor_conditional = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], SensorConditional)
    users = flaskutils.db_retrieve_table(current_app.config['USER_DB_PATH'], Users)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).sensor
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    formAddSensor = flaskforms.AddSensor()
    formModSensor = flaskforms.ModSensor()
    formModSensorCond = flaskforms.ModSensorConditional()

    # Create list of file names from the sensor_options directory
    # Used in generating the correct options for each sensor/device
    sensor_template_list = []
    sensor_path = "{}/mycodo/mycodo_flask/templates/pages/sensor_options/".format(INSTALL_DIRECTORY)
    for (_, _, filenames) in os.walk(sensor_path):
        sensor_template_list.extend(filenames)
        break
    sensor_templates = []
    for each_fname in sensor_template_list:
        sensor_templates.append(each_fname.split(".")[0])

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addSensor':
            flaskutils.sensor_add(formAddSensor, display_order)
        elif form_name == 'modSensor':
            if formModSensor.modSensorSubmit.data:
                flaskutils.sensor_mod(formModSensor)
            elif formModSensor.delSensorSubmit.data:
                flaskutils.sensor_del(formModSensor, display_order)
            elif formModSensor.orderSensorUp.data or formModSensor.orderSensorDown.data:
                flaskutils.sensor_reorder(formModSensor, display_order)
            elif formModSensor.activateSensorSubmit.data:
                flaskutils.sensor_activate(formModSensor)
            elif formModSensor.deactivateSensorSubmit.data:
                flaskutils.sensor_deactivate(formModSensor)
            elif formModSensor.sensorCondAddSubmit.data:
                flaskutils.sensor_conditional_add(formModSensor)
        elif form_name == 'modSensorConditional':
            flaskutils.sensor_conditional_mod(formModSensorCond)
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
                           formAddSensor=formAddSensor,
                           formModSensor=formModSensor,
                           formModSensorCond=formModSensorCond)


@blueprint.route('/timer', methods=('GET', 'POST'))
def page_timer():
    """ Display Timer settings """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    timer = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Timer)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)
    relay_choices = flaskutils.choices_id_name(relay)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).timer
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    formTimer = flaskforms.Timer()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'addTimer':
            flaskutils.timer_add(formTimer,
                                 request.form['timerType'],
                                 display_order)
        elif form_name == 'modTimer':
            if formTimer.timerDel.data:
                flaskutils.timer_del(formTimer, display_order)
            elif formTimer.orderTimerUp.data or formTimer.orderTimerDown.data:
                flaskutils.timer_reorder(formTimer, display_order)
            elif formTimer.activate.data:
                flaskutils.timer_activate(formTimer)
            elif formTimer.deactivate.data:
                flaskutils.timer_deactivate(formTimer)
            elif formTimer.timerMod.data:
                flaskutils.timer_mod(formTimer, request.form['timerType'])
        return redirect('/timer')

    return render_template('pages/timer.html',
                           timer=timer,
                           displayOrder=display_order,
                           relay_choices=relay_choices,
                           formTimer=formTimer)


@blueprint.route('/usage', methods=('GET', 'POST'))
def page_usage():
    """ Display relay usage (duration and energy usage/cost) """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    misc = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Misc, first=True)
    relay = flaskutils.db_retrieve_table(current_app.config['MYCODO_DB_PATH'], Relay)

    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], DisplayOrder, first=True).relay
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
        past_month_seconds = (now - now.replace(
            hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    elif misc.relay_stats_dayofmonth > datetime.datetime.today().day:
        first_day = now.replace(day=1)
        last_Month = first_day - datetime.timedelta(days=1)
        past_month = last_Month.replace(day=misc.relay_stats_dayofmonth)
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
        relay_each_duration[each_relay.id]['1d'] = flaskutils.sum_relay_usage(each_relay.id, 86400) / 3600
        relay_each_duration[each_relay.id]['1w'] = flaskutils.sum_relay_usage(each_relay.id, 604800) / 3600
        relay_each_duration[each_relay.id]['1m'] = flaskutils.sum_relay_usage(each_relay.id, 2629743) / 3600
        relay_each_duration[each_relay.id]['1m-date'] = flaskutils.sum_relay_usage(each_relay.id,
                                                                                   int(past_month_seconds)) / 3600
        relay_each_duration[each_relay.id]['1y'] = flaskutils.sum_relay_usage(each_relay.id, 31556926) / 3600
        relay_sum_duration['1d'] += relay_each_duration[each_relay.id]['1d']
        relay_sum_duration['1w'] += relay_each_duration[each_relay.id]['1w']
        relay_sum_duration['1m'] += relay_each_duration[each_relay.id]['1m']
        relay_sum_duration['1m-date'] += relay_each_duration[each_relay.id]['1m-date']
        relay_sum_duration['1y'] += relay_each_duration[each_relay.id]['1y']
        relay_sum_kwh['1d'] += misc.relay_stats_volts * each_relay.amps * relay_each_duration[each_relay.id][
            '1d'] / 1000
        relay_sum_kwh['1w'] += misc.relay_stats_volts * each_relay.amps * relay_each_duration[each_relay.id][
            '1w'] / 1000
        relay_sum_kwh['1m'] += misc.relay_stats_volts * each_relay.amps * relay_each_duration[each_relay.id][
            '1m'] / 1000
        relay_sum_kwh['1m-date'] += misc.relay_stats_volts * each_relay.amps * relay_each_duration[each_relay.id][
            '1m'] / 1000
        relay_sum_kwh['1y'] += misc.relay_stats_volts * each_relay.amps * relay_each_duration[each_relay.id][
            '1y'] / 1000

    return render_template('tools/usage.html',
                           display_order=display_order,
                           misc=misc,
                           relay=relay,
                           relay_each_duration=relay_each_duration,
                           relay_sum_duration=relay_sum_duration,
                           relay_sum_kwh=relay_sum_kwh,
                           date_suffix=date_suffix)


def gen(camera):
    """ Video streaming generator function """
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
