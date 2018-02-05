# coding=utf-8
from __future__ import print_function

import calendar
import datetime
import logging
import subprocess
from importlib import import_module

import flask_login
import os
from RPi import GPIO
from dateutil.parser import parse as date_parse
from flask import Response
from flask import current_app
from flask import flash
from flask import jsonify
from flask import redirect
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask.blueprints import Blueprint
from flask_babel import gettext
from flask_csv import send_csv
from flask_influxdb import InfluxDB
from flask_limiter import Limiter

from mycodo.config import INFLUXDB_DATABASE
from mycodo.config import INFLUXDB_PASSWORD
from mycodo.config import INFLUXDB_USER
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import LOG_PATH
from mycodo.config import PATH_CAMERAS
from mycodo.databases.models import Camera
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import Output
from mycodo.devices.camera import camera_record
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.routes_authentication import clear_cookie_auth
from mycodo.mycodo_flask.utils import utils_general
from mycodo.utils.influx import query_string
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import str_is_float

blueprint = Blueprint('routes_general',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')

logger = logging.getLogger(__name__)
influx_db = InfluxDB()

limiter = Limiter()


@blueprint.route('/')
def home():
    """Load the default landing page"""
    if flask_login.current_user.is_authenticated:
        return redirect(url_for('routes_page.page_live'))
    return clear_cookie_auth()


@blueprint.route('/settings', methods=('GET', 'POST'))
@flask_login.login_required
def page_settings():
    return redirect('settings/general')


@blueprint.route('/camera/<camera_unique_id>/<img_type>/<filename>')
@flask_login.login_required
def camera_img_return_path(camera_unique_id, img_type, filename):
    """Return an image from stills or timelapses"""
    camera = Camera.query.filter(Camera.unique_id == camera_unique_id).first()
    camera_path = assure_path_exists(
        os.path.join(PATH_CAMERAS, '{uid}'.format(
            id=camera.id, uid=camera.unique_id)))

    if img_type in ['still', 'timelapse']:
        path = os.path.join(camera_path, img_type)
        if os.path.isdir(path):
            files = (files for files in os.listdir(path)
                if os.path.isfile(os.path.join(path, files)))
        else:
            files = []
        if filename in files:
            path_file = os.path.join(path, filename)
            return send_file(path_file, mimetype='image/jpeg')

    return "Image not found"


@blueprint.route('/camera_acquire_image/<image_type>/<camera_unique_id>/<max_age>')
@flask_login.login_required
def camera_img_acquire(image_type, camera_unique_id, max_age):
    """Capture an image and resturn the filename"""
    if image_type == 'new':
        tmp_filename = None
    elif image_type == 'tmp':
        tmp_filename = '{id}_tmp.jpg'.format(id=camera_unique_id)
    else:
        return
    path, filename = camera_record('photo', camera_unique_id, tmp_filename=tmp_filename)
    image_path = os.path.join(path, filename)
    time_max_age = datetime.datetime.now() - datetime.timedelta(seconds=int(max_age))
    timestamp = os.path.getctime(image_path)
    if datetime.datetime.fromtimestamp(timestamp) > time_max_age:
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return_values = '["{}","{}"]'.format(filename, date_time)
    else:
        return_values = '["max_age_exceeded"]'
    return Response(return_values, mimetype='text/json')


@blueprint.route('/camera_latest_timelapse/<camera_unique_id>/<max_age>')
@flask_login.login_required
def camera_img_latest_timelapse(camera_unique_id, max_age):
    """Capture an image and resturn the filename"""
    _, _, tl_ts, tl_path = utils_general.get_camera_image_info()
    if camera_unique_id in tl_path and tl_path[camera_unique_id]:
        camera_path = assure_path_exists(
            os.path.join(PATH_CAMERAS, '{uid}/timelapse'.format(
                uid=camera_unique_id)))
        image_path_full = os.path.join(camera_path, tl_path[camera_unique_id])
        try:
            timestamp = os.path.getctime(image_path_full)
            time_max_age = datetime.datetime.now() - datetime.timedelta(seconds=int(max_age))
            if datetime.datetime.fromtimestamp(timestamp) > time_max_age:
                return_values = '["{}","{}"]'.format(tl_path[camera_unique_id],
                                                     tl_ts[camera_unique_id])
            else:
                return_values = '["max_age_exceeded"]'
        except FileNotFoundError:
            return_values = '["file_not_found"]'
    else:
        return_values = '["file_not_found"]'
    return Response(return_values, mimetype='text/json')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@blueprint.route('/video_feed/<unique_id>')
@flask_login.login_required
def video_feed(unique_id):
    """Video streaming route. Put this in the src attribute of an img tag."""
    camera_options = Camera.query.filter(Camera.unique_id == unique_id).first()
    camera_stream = import_module('mycodo.mycodo_flask.camera.camera_' + camera_options.library).Camera
    camera_stream.set_camera_options(camera_options)
    return Response(gen(camera_stream(unique_id=unique_id)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@blueprint.route('/gpiostate')
@flask_login.login_required
def gpio_state():
    """Return the GPIO state, for output page status"""
    output = Output.query.all()
    daemon_control = DaemonControl()
    state = {}
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for each_output in output:
        if each_output.relay_type == 'wired' and each_output.pin and -1 < each_output.pin < 40:
            GPIO.setup(each_output.pin, GPIO.OUT)
            if GPIO.input(each_output.pin) == each_output.trigger:
                state[each_output.id] = 'on'
            else:
                state[each_output.id] = 'off'
        elif (each_output.relay_type == 'command' or
                (each_output.relay_type in ['pwm', 'wireless_433MHz_pi_switch'] and
                 each_output.pin and
                 -1 < each_output.pin < 40)):
            state[each_output.id] = daemon_control.relay_state(each_output.id)
        else:
            state[each_output.id] = None

    return jsonify(state)


@blueprint.route('/dl/<dl_type>/<path:filename>')
@flask_login.login_required
def download_file(dl_type, filename):
    """Serve log file to download"""
    if dl_type == 'log':
        return send_from_directory(LOG_PATH, filename, as_attachment=True)

    return '', 204


@blueprint.route('/last/<input_measure>/<input_id>/<input_period>')
@flask_login.login_required
def last_data(input_measure, input_id, input_period):
    """Return the most recent time and value from influxdb"""
    if not str_is_float(input_period):
        return '', 204

    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection
    try:
        query_str = query_string(
            input_measure, input_id, value='LAST',
            past_sec=input_period)
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw
        number = len(raw_data['series'][0]['values'])
        time_raw = raw_data['series'][0]['values'][number - 1][0]
        value = raw_data['series'][0]['values'][number - 1][1]
        value = '{:.3f}'.format(float(value))
        # Convert date-time to epoch (potential bottleneck for data)
        dt = date_parse(time_raw)
        timestamp = calendar.timegm(dt.timetuple()) * 1000
        live_data = '[{},{}]'.format(timestamp, value)
        return Response(live_data, mimetype='text/json')
    except KeyError:
        logger.debug("No Data returned form influxdb")
        return '', 204
    except Exception as e:
        logger.exception("URL for 'last_data' raised and error: "
                         "{err}".format(err=e))
        return '', 204


@blueprint.route('/past/<input_measure>/<input_id>/<past_seconds>')
@flask_login.login_required
def past_data(input_measure, input_id, past_seconds):
    """Return data from past_seconds until present from influxdb"""
    if not str_is_float(past_seconds):
        return '', 204

    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection
    try:
        query_str = query_string(
            input_measure, input_id, past_sec=past_seconds)
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw
        if raw_data:
            return jsonify(raw_data['series'][0]['values'])
        else:
            return '', 204
    except Exception as e:
        logger.debug("URL for 'past_data' raised and error: "
                     "{err}".format(err=e))
        return '', 204


@blueprint.route('/export_data/<measurement>/<unique_id>/<start_seconds>/<end_seconds>')
@flask_login.login_required
def export_data(measurement, unique_id, start_seconds, end_seconds):
    """
    Return data from start_seconds to end_seconds from influxdb.
    Used for exporting data.
    """
    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection

    output = Output.query.filter(Output.unique_id == unique_id).first()
    input = Input.query.filter(Input.unique_id == unique_id).first()
    math = Math.query.filter(Math.unique_id == unique_id).first()

    if output:
        name = output.name
    elif input:
        name = input.name
    elif math:
        name = math.name
    else:
        name = None

    utc_offset_timedelta = datetime.datetime.utcnow() - datetime.datetime.now()
    start = datetime.datetime.fromtimestamp(float(start_seconds))
    start += utc_offset_timedelta
    start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.datetime.fromtimestamp(float(end_seconds))
    end += utc_offset_timedelta
    end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    query_str = query_string(
        measurement, unique_id,
        start_str=start_str, end_str=end_str)
    if query_str == 1:
        flash('Invalid query string', 'error')
        return redirect(url_for('routes_page.page_export'))
    raw_data = dbcon.query(query_str).raw

    if not raw_data or 'series' not in raw_data:
        flash('No measurements to export in this time period', 'error')
        return redirect(url_for('routes_page.page_export'))

    # Generate column names
    col_1 = 'timestamp (UTC)'
    col_2 = '{name} {meas} ({id})'.format(
        name=name, meas=measurement, id=unique_id)
    csv_filename = '{id}_{meas}.csv'.format(id=unique_id, meas=measurement)

    # Populate list of dictionary entries for each column to convert to CSV
    # and send to the user to download
    csv_data = []
    for each_data in raw_data['series'][0]['values']:
        csv_data.append({col_1: str(each_data[0][:-4]).replace('T', ' '),
                         col_2: each_data[1]})

    return send_csv(csv_data, csv_filename, [col_1, col_2])


@blueprint.route('/async/<measurement>/<unique_id>/<start_seconds>/<end_seconds>')
@flask_login.login_required
def async_data(measurement, unique_id, start_seconds, end_seconds):
    """
    Return data from start_seconds to end_seconds from influxdb.
    Used for asynchronous graph display of many points (up to millions).
    """
    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection

    # Set the time frame to the past year if start/end not specified
    if start_seconds == '0' and end_seconds == '0':
        # Get how many points there are in the past year
        query_str = query_string(
            measurement, unique_id, value='COUNT')
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year
        query_str = query_string(
            measurement, unique_id, limit=1)
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        first_point = raw_data['series'][0]['values'][0][0]
        end = datetime.datetime.utcnow()
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    # Set the time frame to the past start epoch to now
    elif start_seconds != '0' and end_seconds == '0':
        start = datetime.datetime.utcfromtimestamp(float(start_seconds))
        start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.datetime.utcnow()
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        query_str = query_string(
            measurement, unique_id,
            value='COUNT', start_str=start_str, end_str=end_str)
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year
        query_str = query_string(
            measurement, unique_id,
            start_str=start_str, end_str=end_str, limit=1)
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        first_point = raw_data['series'][0]['values'][0][0]
    else:
        start = datetime.datetime.utcfromtimestamp(float(start_seconds))
        start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.datetime.utcfromtimestamp(float(end_seconds))
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        query_str = query_string(
            measurement, unique_id,
            value='COUNT', start_str=start_str, end_str=end_str)
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year
        query_str = query_string(
            measurement, unique_id,
            start_str=start_str, end_str=end_str, limit=1)
        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        first_point = raw_data['series'][0]['values'][0][0]

    start = datetime.datetime.strptime(first_point[:26],
                                       '%Y-%m-%dT%H:%M:%S.%f')
    start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    logger.debug('Count = {}'.format(count_points))
    logger.debug('Start = {}'.format(start))
    logger.debug('End   = {}'.format(end))

    # How many seconds between the start and end period
    time_difference_seconds = (end - start).total_seconds()
    logger.debug('Difference seconds = {}'.format(time_difference_seconds))

    # If there are more than 700 points in the time frame, we need to group
    # data points into 700 groups with points averaged in each group.
    if count_points > 700:
        # Average period between input reads
        seconds_per_point = time_difference_seconds / count_points
        logger.debug('Seconds per point = {}'.format(seconds_per_point))

        # How many seconds to group data points in
        group_seconds = int(time_difference_seconds / 700)
        logger.debug('Group seconds = {}'.format(group_seconds))

        try:
            query_str = query_string(
                measurement, unique_id, value='MEAN',
                start_str=start_str, end_str=end_str,
                group_sec=group_seconds)
            if query_str == 1:
                return '', 204
            raw_data = dbcon.query(query_str).raw

            return jsonify(raw_data['series'][0]['values'])
        except Exception as e:
            logger.error("URL for 'async_data' raised and error: "
                         "{err}".format(err=e))
            return '', 204
    else:
        try:
            query_str = query_string(
                measurement, unique_id,
                start_str=start_str, end_str=end_str)
            if query_str == 1:
                return '', 204
            raw_data = dbcon.query(query_str).raw

            return jsonify(raw_data['series'][0]['values'])
        except Exception as e:
            logger.error("URL for 'async_data' raised and error: "
                         "{err}".format(err=e))
            return '', 204


@blueprint.route('/output_mod/<output_id>/<state>/<out_type>/<amount>')
@flask_login.login_required
def output_mod(output_id, state, out_type, amount):
    """Manipulate output"""
    if not utils_general.user_has_permission('edit_controllers'):
        return 'Insufficient user permissions to manipulate outputs'

    daemon = DaemonControl()
    if (state in ['on', 'off'] and out_type == 'sec' and
            (str_is_float(amount) and float(amount) >= 0)):
        return daemon.output_on_off(int(output_id), state, float(amount))
    elif (state == 'on' and out_type == 'pwm' and
              (str_is_float(amount) and float(amount) >= 0)):
        return daemon.relay_on(int(output_id), state, duty_cycle=float(amount))


@blueprint.route('/daemonactive')
@flask_login.login_required
def daemon_active():
    """Return 'alive' if the daemon is running"""
    try:
        control = DaemonControl()
        return control.daemon_status()
    except Exception as e:
        logger.error("URL for 'daemon_active' raised and error: "
                     "{err}".format(err=e))
        return '0'


@blueprint.route('/systemctl/<action>')
@flask_login.login_required
def computer_command(action):
    """Execute one of several commands as root"""
    if not utils_general.user_has_permission('edit_settings'):
        return redirect(url_for('routes_general.home'))

    try:
        if action not in ['restart', 'shutdown', 'daemon_restart', 'frontend_reload']:
            flash("Unrecognized command: {action}".format(
                action=action), "success")
            return redirect('/settings')
        cmd = '{path}/mycodo/scripts/mycodo_wrapper {action} 2>&1'.format(
                path=INSTALL_DIRECTORY, action=action)
        subprocess.Popen(cmd, shell=True)
        if action == 'restart':
            flash(gettext("System rebooting in 10 seconds"), "success")
        elif action == 'shutdown':
            flash(gettext("System shutting down in 10 seconds"), "success")
        elif action == 'daemon_restart':
            flash(gettext("Command to restart the daemon sent"), "success")
        elif action == 'frontend_reload':
            flash(gettext("Command to reload the frontend sent"), "success")
        return redirect('/settings')
    except Exception as e:
        logger.error("System command '{cmd}' raised and error: "
                     "{err}".format(cmd=action, err=e))
        flash("System command '{cmd}' raised and error: "
              "{err}".format(cmd=action, err=e), "error")
        return redirect(url_for('routes_general.home'))
