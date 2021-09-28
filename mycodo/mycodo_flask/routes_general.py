# coding=utf-8
import calendar
import datetime
import logging
import subprocess
import time
from importlib import import_module

import flask_login
import os
from dateutil.parser import parse as date_parse
from flask import Response
from flask import flash
from flask import jsonify
from flask import redirect
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask.blueprints import Blueprint
from flask_babel import gettext
from flask_limiter import Limiter
from influxdb import InfluxDBClient
from sqlalchemy import and_

from mycodo.config import DOCKER_CONTAINER
from mycodo.config import INFLUXDB_DATABASE
from mycodo.config import INFLUXDB_HOST
from mycodo.config import INFLUXDB_PASSWORD
from mycodo.config import INFLUXDB_PORT
from mycodo.config import INFLUXDB_USER
from mycodo.config import INSTALL_DIRECTORY
from mycodo.config import LOG_PATH
from mycodo.config import PATH_CAMERAS
from mycodo.config import PATH_NOTE_ATTACHMENTS
from mycodo.databases.models import Camera
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
from mycodo.databases.models import Math
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.devices.camera import camera_record
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.routes_authentication import clear_cookie_auth
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils.utils_general import get_ip_address
from mycodo.mycodo_flask.utils.utils_output import get_all_output_states
from mycodo.utils.database import db_retrieve_table
from mycodo.utils.image import generate_thermal_image_from_pixels
from mycodo.utils.influx import influx_time_str_to_milliseconds
from mycodo.utils.influx import query_string
from mycodo.utils.system_pi import assure_path_exists
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.system_pi import str_is_float

blueprint = Blueprint('routes_general',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_ip_address)


@blueprint.route('/')
def home():
    """Load the default landing page"""
    try:
        if flask_login.current_user.is_authenticated:
            if flask_login.current_user.landing_page == 'live':
                return redirect(url_for('routes_page.page_live'))
            elif flask_login.current_user.landing_page == 'dashboard':
                return redirect(url_for('routes_dashboard.page_dashboard_default'))
            elif flask_login.current_user.landing_page == 'info':
                return redirect(url_for('routes_page.page_info'))
            return redirect(url_for('routes_page.page_live'))
    except:
        logger.error("User may not be logged in. Clearing cookie auth.")
    return clear_cookie_auth()

@blueprint.route('/index_page')
def index_page():
    """Load the index page"""
    try:
        if not flask_login.current_user.index_page:
            return home()
        elif flask_login.current_user.index_page == 'landing':
            return home()
        else:
            if flask_login.current_user.is_authenticated:
                if flask_login.current_user.index_page == 'live':
                    return redirect(url_for('routes_page.page_live'))
                elif flask_login.current_user.index_page == 'dashboard':
                    return redirect(url_for('routes_dashboard.page_dashboard_default'))
                elif flask_login.current_user.index_page == 'info':
                    return redirect(url_for('routes_page.page_info'))
                return redirect(url_for('routes_page.page_live'))
    except:
        logger.error("User may not be logged in. Clearing cookie auth.")
    return clear_cookie_auth()

@blueprint.route('/settings', methods=('GET', 'POST'))
@flask_login.login_required
def page_settings():
    return redirect('settings/general')


@blueprint.route('/note_attachment/<filename>')
@flask_login.login_required
def send_note_attachment(filename):
    """Return a file from the note attachment directory"""
    file_path = os.path.join(PATH_NOTE_ATTACHMENTS, filename)
    if file_path is not None:
        try:
            return send_file(file_path, as_attachment=True)
        except Exception:
            logger.exception("Send note attachment")


@blueprint.route('/camera/<camera_unique_id>/<img_type>/<filename>')
@flask_login.login_required
def camera_img_return_path(camera_unique_id, img_type, filename):
    """Return an image from stills or time-lapses"""
    camera = Camera.query.filter(Camera.unique_id == camera_unique_id).first()
    camera_path = assure_path_exists(
        os.path.join(PATH_CAMERAS, '{uid}'.format(uid=camera.unique_id)))
    if img_type == 'still':
        if camera.path_still:
            path = camera.path_still
        else:
            path = os.path.join(camera_path, img_type)
    elif img_type == 'timelapse':
        if camera.path_timelapse:
            path = camera.path_timelapse
        else:
            path = os.path.join(camera_path, img_type)
    else:
        return "Unknown Image Type"

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
    """Capture an image and return the filename"""
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
    """Capture an image and/or return a filename"""
    camera = Camera.query.filter(
            Camera.unique_id == camera_unique_id).first()

    _, tl_path = utils_general.get_camera_paths(camera)

    timelapse_file_path = os.path.join(tl_path, str(camera.timelapse_last_file))

    if camera.timelapse_last_file is not None and os.path.exists(timelapse_file_path):
        time_max_age = datetime.datetime.now() - datetime.timedelta(seconds=int(max_age))
        if datetime.datetime.fromtimestamp(camera.timelapse_last_ts) > time_max_age:
            ts = datetime.datetime.fromtimestamp(camera.timelapse_last_ts).strftime("%Y-%m-%d %H:%M:%S")
            return_values = '["{}","{}"]'.format(camera.timelapse_last_file, ts)
        else:
            return_values = '["max_age_exceeded"]'
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


@blueprint.route('/outputstate')
@flask_login.login_required
def gpio_state():
    """Return all output states"""
    return jsonify(get_all_output_states())


@blueprint.route('/outputstate_unique_id/<unique_id>/<channel_id>')
@flask_login.login_required
def gpio_state_unique_id(unique_id, channel_id):
    """Return the GPIO state, for dashboard output """
    channel = OutputChannel.query.filter(OutputChannel.unique_id == channel_id).first()
    daemon_control = DaemonControl()
    state = daemon_control.output_state(unique_id, channel.channel)
    return jsonify(state)


@blueprint.route('/widget_execute/<unique_id>')
@flask_login.login_required
def widget_execute(unique_id):
    """Return the response from the execution of widget code """
    daemon_control = DaemonControl()
    return_value = daemon_control.widget_execute(unique_id)
    return jsonify(return_value)


@blueprint.route('/time')
@flask_login.login_required
def get_time():
    """ Return the current time """
    return jsonify(datetime.datetime.now().strftime('%m/%d %H:%M'))


@blueprint.route('/dl/<dl_type>/<path:filename>')
@flask_login.login_required
def download_file(dl_type, filename):
    """Serve log file to download"""
    if dl_type == 'log':
        return send_from_directory(LOG_PATH, filename, as_attachment=True)

    return '', 204


@blueprint.route('/last/<unique_id>/<measure_type>/<measurement_id>/<period>')
@flask_login.login_required
def last_data(unique_id, measure_type, measurement_id, period):
    """Return the most recent time and value from influxdb"""
    if not str_is_float(period):
        return '', 204

    if measure_type in ['input', 'math', 'function', 'output', 'pid']:
        dbcon = InfluxDBClient(
            INFLUXDB_HOST,
            INFLUXDB_PORT,
            INFLUXDB_USER,
            INFLUXDB_PASSWORD,
            INFLUXDB_DATABASE)

        if measure_type in ['input', 'math', 'function', 'output', 'pid']:
            measure = DeviceMeasurements.query.filter(
                DeviceMeasurements.unique_id == measurement_id).first()
        else:
            return '', 204

        if measure:
            conversion = Conversion.query.filter(
                Conversion.unique_id == measure.conversion_id).first()
        else:
            conversion = None

        channel, unit, measurement = return_measurement_info(
            measure, conversion)

        if hasattr(measure, 'measurement_type') and measure.measurement_type == 'setpoint':
            setpoint_pid = PID.query.filter(PID.unique_id == measure.device_id).first()
            if setpoint_pid and ',' in setpoint_pid.measurement:
                pid_measurement = setpoint_pid.measurement.split(',')[1]
                setpoint_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == pid_measurement).first()
                if setpoint_measurement:
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == setpoint_measurement.conversion_id).first()
                    _, unit, measurement = return_measurement_info(setpoint_measurement, conversion)
        try:
            if period != '0':
                query_str = query_string(
                    unit, unique_id,
                    measure=measurement, channel=channel,
                    value='LAST', past_sec=period)
            else:
                query_str = query_string(
                    unit, unique_id,
                    measure=measurement, channel=channel,
                    value='LAST')
            if query_str == 1:
                return '', 204

            raw_data = dbcon.query(query_str).raw

            number = len(raw_data['series'][0]['values'])
            time_raw = raw_data['series'][0]['values'][number - 1][0]
            value = raw_data['series'][0]['values'][number - 1][1]
            value = float(value)
            # Convert date-time to epoch (potential bottleneck for data)
            dt = date_parse(time_raw)
            timestamp = calendar.timegm(dt.timetuple()) * 1000
            live_data = '[{},{}]'.format(timestamp, value)

            return Response(live_data, mimetype='text/json')
        except KeyError:
            logger.debug("No Data returned form influxdb")
            return '', 204
        except IndexError:
            logger.debug("No Data returned form influxdb")
            return '', 204
        except Exception as e:
            logger.exception("URL for 'last_data' raised and error: "
                             "{err}".format(err=e))
            return '', 204


@blueprint.route('/past/<unique_id>/<measure_type>/<measurement_id>/<past_seconds>')
@flask_login.login_required
def past_data(unique_id, measure_type, measurement_id, past_seconds):
    """Return data from past_seconds until present from influxdb"""
    if not str_is_float(past_seconds):
        return '', 204

    if measure_type == 'tag':
        notes_list = []

        tag = NoteTags.query.filter(NoteTags.unique_id == unique_id).first()
        notes = Notes.query.filter(
            Notes.date_time >= (datetime.datetime.utcnow() - datetime.timedelta(seconds=int(past_seconds)))).all()

        for each_note in notes:
            if tag.unique_id in each_note.tags.split(','):
                notes_list.append(
                    [each_note.date_time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"), each_note.name, each_note.note])

        if notes_list:
            return jsonify(notes_list)
        else:
            return '', 204

    elif measure_type in ['input', 'math', 'function', 'output', 'pid']:
        dbcon = InfluxDBClient(
            INFLUXDB_HOST,
            INFLUXDB_PORT,
            INFLUXDB_USER,
            INFLUXDB_PASSWORD,
            INFLUXDB_DATABASE)

        if measure_type in ['input', 'math', 'function', 'output', 'pid']:
            measure = DeviceMeasurements.query.filter(
                DeviceMeasurements.unique_id == measurement_id).first()
        else:
            measure = None

        if not measure:
            return "Could not find measurement"

        if measure:
            conversion = Conversion.query.filter(
                Conversion.unique_id == measure.conversion_id).first()
        else:
            conversion = None

        channel, unit, measurement = return_measurement_info(
            measure, conversion)

        if hasattr(measure, 'measurement_type') and measure.measurement_type == 'setpoint':
            setpoint_pid = PID.query.filter(PID.unique_id == measure.device_id).first()
            if setpoint_pid and ',' in setpoint_pid.measurement:
                pid_measurement = setpoint_pid.measurement.split(',')[1]
                setpoint_measurement = DeviceMeasurements.query.filter(
                    DeviceMeasurements.unique_id == pid_measurement).first()
                if setpoint_measurement:
                    conversion = Conversion.query.filter(
                        Conversion.unique_id == setpoint_measurement.conversion_id).first()
                    _, unit, measurement = return_measurement_info(setpoint_measurement, conversion)

        try:
            query_str = query_string(
                unit, unique_id,
                measure=measurement,
                channel=channel,
                past_sec=past_seconds)

            if query_str == 1:
                return '', 204

            raw_data = dbcon.query(query_str).raw

            if 'series' in raw_data and raw_data['series']:
                return jsonify(raw_data['series'][0]['values'])
            else:
                return '', 204
        except Exception as e:
            logger.debug("URL for 'past_data' raised and error: "
                         "{err}".format(err=e))
            return '', 204


@blueprint.route('/generate_thermal_image/<unique_id>/<timestamp>')
@flask_login.login_required
def generate_thermal_image_from_timestamp(unique_id, timestamp):
    """Return a file from the note attachment directory"""
    ts_now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    camera_path = assure_path_exists(
        os.path.join(PATH_CAMERAS, '{uid}'.format(uid=unique_id)))
    filename = 'Still-{uid}-{ts}.jpg'.format(
        uid=unique_id,
        ts=ts_now).replace(" ", "_")
    save_path = assure_path_exists(os.path.join(camera_path, 'thermal'))
    assure_path_exists(save_path)
    path_file = os.path.join(save_path, filename)

    dbcon = InfluxDBClient(
        INFLUXDB_HOST,
        INFLUXDB_PORT,
        INFLUXDB_USER,
        INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE)

    input_dev = Input.query.filter(Input.unique_id == unique_id).first()
    pixels = []
    success = True

    start = int(int(timestamp) / 1000.0)  # Round down
    end = start + 1  # Round up

    start_timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000000000Z', time.gmtime(start))
    end_timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000000000Z', time.gmtime(end))

    for each_channel in range(input_dev.channels):
        measurement = 'channel_{chan}'.format(
            chan=each_channel)
        query_str = query_string(measurement, unique_id,
                                 start_str=start_timestamp,
                                 end_str=end_timestamp)
        if query_str == 1:
            logger.error('Invalid query string')
            success = False
        else:
            raw_data = dbcon.query(query_str).raw
            if not raw_data or 'series' not in raw_data or not raw_data['series']:
                logger.error('No measurements to export in this time period')
                success = False
            else:
                pixels.append(raw_data['series'][0]['values'][0][1])

    # logger.error("generate_thermal_image_from_timestamp: success: {}, pixels: {}".format(success, pixels))

    if success:
        generate_thermal_image_from_pixels(pixels, 8, 8, path_file)
        return send_file(path_file, mimetype='image/jpeg')
    else:
        return "Could not generate image"


@blueprint.route('/export_data/<unique_id>/<measurement_id>/<start_seconds>/<end_seconds>')
@flask_login.login_required
def export_data(unique_id, measurement_id, start_seconds, end_seconds):
    """
    Return data from start_seconds to end_seconds from influxdb.
    Used for exporting data.
    """
    dbcon = InfluxDBClient(
        INFLUXDB_HOST,
        INFLUXDB_PORT,
        INFLUXDB_USER,
        INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE, timeout=100)

    output = Output.query.filter(Output.unique_id == unique_id).first()
    input_dev = Input.query.filter(Input.unique_id == unique_id).first()
    math = Math.query.filter(Math.unique_id == unique_id).first()

    if output:
        name = output.name
    elif input_dev:
        name = input_dev.name
    elif math:
        name = math.name
    else:
        name = None

    device_measurement = DeviceMeasurements.query.filter(
        DeviceMeasurements.unique_id == measurement_id).first()
    if device_measurement:
        conversion = Conversion.query.filter(
            Conversion.unique_id == device_measurement.conversion_id).first()
    else:
        conversion = None
    channel, unit, measurement = return_measurement_info(
        device_measurement, conversion)

    utc_offset_timedelta = datetime.datetime.utcnow() - datetime.datetime.now()
    start = datetime.datetime.fromtimestamp(float(start_seconds))
    start += utc_offset_timedelta
    start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.datetime.fromtimestamp(float(end_seconds))
    end += utc_offset_timedelta
    end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    query_str = query_string(
        unit, unique_id,
        measure=measurement, channel=channel,
        start_str=start_str, end_str=end_str)
    if query_str == 1:
        flash('Invalid query string', 'error')
        return redirect(url_for('routes_page.page_export'))
    raw_data = dbcon.query(query_str).raw

    if not raw_data or 'series' not in raw_data or not raw_data['series']:
        flash('No measurements to export in this time period', 'error')
        return redirect(url_for('routes_page.page_export'))

    # Generate column names
    col_1 = 'timestamp (UTC)'
    col_2 = '{name} {meas} ({id})'.format(
        name=name, meas=measurement, id=unique_id)
    csv_filename = '{id}_{name}_{meas}.csv'.format(
        id=unique_id, name=name, meas=measurement)
    import csv
    from io import StringIO

    def iter_csv(data):
        """ Stream CSV file to user for download """
        line = StringIO()
        writer = csv.writer(line)
        writer.writerow([col_1, col_2])
        for csv_line in data:
            writer.writerow([
                str(csv_line[0][:-4]).replace('T', ' '),
                csv_line[1]
            ])
            line.seek(0)
            yield line.read()
            line.truncate(0)
            line.seek(0)

    response = Response(iter_csv(raw_data['series'][0]['values']), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(csv_filename)
    return response


@blueprint.route('/async/<device_id>/<device_type>/<measurement_id>/<start_seconds>/<end_seconds>')
@flask_login.login_required
def async_data(device_id, device_type, measurement_id, start_seconds, end_seconds):
    """
    Return data from start_seconds to end_seconds from influxdb.
    Used for asynchronous graph display of many points (up to millions).
    """
    if device_type == 'tag':
        notes_list = []
        tag = NoteTags.query.filter(NoteTags.unique_id == device_id).first()

        start = datetime.datetime.utcfromtimestamp(float(start_seconds))
        if end_seconds == '0':
            end = datetime.datetime.utcnow()
        else:
            end = datetime.datetime.utcfromtimestamp(float(end_seconds))

        notes = Notes.query.filter(
            and_(Notes.date_time >= start, Notes.date_time <= end)).all()
        for each_note in notes:
            if tag.unique_id in each_note.tags.split(','):
                notes_list.append(
                    [each_note.date_time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"), each_note.name, each_note.note])

        if notes_list:
            return jsonify(notes_list)
        else:
            return '', 204

    dbcon = InfluxDBClient(
        INFLUXDB_HOST,
        INFLUXDB_PORT,
        INFLUXDB_USER,
        INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE)

    if device_type in ['input', 'math', 'function', 'output', 'pid']:
        measure = DeviceMeasurements.query.filter(
            DeviceMeasurements.unique_id == measurement_id).first()
    else:
        measure = None

    if not measure:
        return "Could not find measurement"

    if measure:
        conversion = Conversion.query.filter(
            Conversion.unique_id == measure.conversion_id).first()
    else:
        conversion = None
    channel, unit, measurement = return_measurement_info(
        measure, conversion)

    # Set the time frame to the past year if start/end not specified
    if start_seconds == '0' and end_seconds == '0':
        # Get how many points there are in the past year
        query_str = query_string(
            unit, device_id,
            measure=measurement,
            channel=channel,
            value='COUNT')

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year
        query_str = query_string(
            unit, device_id,
            measure=measurement,
            channel=channel,
            limit=1)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        try:
            first_point = raw_data['series'][0]['values'][0][0]
        except:
            return '', 204

        end = datetime.datetime.utcnow()
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    # Set the time frame to the past start epoch to now
    elif start_seconds != '0' and end_seconds == '0':
        start = datetime.datetime.utcfromtimestamp(float(start_seconds))
        start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.datetime.utcnow()
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        query_str = query_string(
            unit, device_id,
            measure=measurement,
            channel=channel,
            value='COUNT',
            start_str=start_str,
            end_str=end_str)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        try:
            count_points = raw_data['series'][0]['values'][0][1]
        except:
            return '', 204

        # Get the timestamp of the first point in the past year
        query_str = query_string(
            unit, device_id,
            measure=measurement,
            channel=channel,
            start_str=start_str,
            end_str=end_str,
            limit=1)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        try:
            first_point = raw_data['series'][0]['values'][0][0]
        except:
            return '', 204
    else:
        start = datetime.datetime.utcfromtimestamp(float(start_seconds))
        start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.datetime.utcfromtimestamp(float(end_seconds))
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        query_str = query_string(
            unit, device_id,
            measure=measurement,
            channel=channel,
            value='COUNT',
            start_str=start_str,
            end_str=end_str)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        try:
            count_points = raw_data['series'][0]['values'][0][1]
        except:
            return '', 204

        # Get the timestamp of the first point in the past year
        query_str = query_string(
            unit, device_id,
            measure=measurement,
            channel=channel,
            start_str=start_str,
            end_str=end_str,
            limit=1)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        try:
            first_point = raw_data['series'][0]['values'][0][0]
        except:
            return '', 204

    start = datetime.datetime.strptime(
        influx_time_str_to_milliseconds(first_point),
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
                unit, device_id,
                measure=measurement,
                channel=channel,
                value='MEAN',
                start_str=start_str,
                end_str=end_str,
                group_sec=group_seconds)

            if query_str == 1:
                return '', 204
            raw_data = dbcon.query(query_str).raw

            try:
                return jsonify(raw_data['series'][0]['values'])
            except:
                return '', 204
        except Exception as e:
            logger.error("URL for 'async_data' raised and error: "
                         "{err}".format(err=e))
            return '', 204
    else:
        try:
            query_str = query_string(
                unit, device_id,
                measure=measurement,
                channel=channel,
                start_str=start_str,
                end_str=end_str)

            if query_str == 1:
                return '', 204
            raw_data = dbcon.query(query_str).raw

            return jsonify(raw_data['series'][0]['values'])
        except Exception as e:
            logger.error("URL for 'async_data' raised and error: "
                         "{err}".format(err=e))
            return '', 204


@blueprint.route('/async_usage/<device_id>/<unit>/<channel>/<start_seconds>/<end_seconds>')
@flask_login.login_required
def async_usage_data(device_id, unit, channel, start_seconds, end_seconds):
    """
    Return data from start_seconds to end_seconds from influxdb.
    Used for asynchronous energy usage display of many points (up to millions).
    """
    dbcon = InfluxDBClient(
        INFLUXDB_HOST,
        INFLUXDB_PORT,
        INFLUXDB_USER,
        INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE)

    # Set the time frame to the past year if start/end not specified
    if start_seconds == '0' and end_seconds == '0':
        # Get how many points there are in the past year
        query_str = query_string(
            unit, device_id,
            channel=channel,
            value='COUNT')

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year
        query_str = query_string(
            unit, device_id,
            channel=channel,
            limit=1)

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
            unit, device_id,
            channel=channel,
            value='COUNT',
            start_str=start_str,
            end_str=end_str)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year

        query_str = query_string(
            unit, device_id,
            channel=channel,
            start_str=start_str,
            end_str=end_str,
            limit=1)

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
            unit, device_id,
            channel=channel,
            value='COUNT',
            start_str=start_str,
            end_str=end_str)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year

        query_str = query_string(
            unit, device_id,
            channel=channel,
            start_str=start_str,
            end_str=end_str,
            limit=1)

        if query_str == 1:
            return '', 204
        raw_data = dbcon.query(query_str).raw

        first_point = raw_data['series'][0]['values'][0][0]

    start = datetime.datetime.strptime(
        influx_time_str_to_milliseconds(first_point),
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
                unit, device_id,
                channel=channel,
                value='MEAN',
                start_str=start_str,
                end_str=end_str,
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
                unit, device_id,
                channel=channel,
                start_str=start_str,
                end_str=end_str)

            if query_str == 1:
                return '', 204
            raw_data = dbcon.query(query_str).raw

            return jsonify(raw_data['series'][0]['values'])
        except Exception as e:
            logger.error("URL for 'async_usage' raised and error: "
                         "{err}".format(err=e))
            return '', 204


@blueprint.route('/output_mod/<output_id>/<channel>/<state>/<output_type>/<amount>')
@flask_login.login_required
def output_mod(output_id, channel, state, output_type, amount):
    """ Manipulate output (using non-unique ID) """
    if not utils_general.user_has_permission('edit_controllers'):
        return 'Insufficient user permissions to manipulate outputs'

    if is_int(channel):
        # if an integer was returned
        output_channel = int(channel)
    else:
        # if a channel ID was returned
        channel_dev = db_retrieve_table(OutputChannel).filter(
            OutputChannel.unique_id == channel).first()
        if channel_dev:
            output_channel = channel_dev.channel
        else:
            return "Could not determine channel number from channel ID '{}'".format(channel)

    daemon = DaemonControl()
    if (state in ['on', 'off'] and str_is_float(amount) and
            (
                (output_type in ['sec', 'pwm'] and float(amount) >= 0) or
                output_type == 'vol' or
                output_type == 'value'
            )):
        out_status = daemon.output_on_off(
            output_id,
            state,
            output_type=output_type,
            amount=float(amount),
            output_channel=output_channel)
        if out_status[0]:
            return 'ERROR: {}'.format(out_status[1])
        else:
            return 'SUCCESS: {}'.format(out_status[1])
    else:
        return 'ERROR: unknown parameters: ' \
               'output_id: {}, channel: {}, state: {}, output_type: {}, amount: {}'.format(
                output_id, channel, state, output_type, amount)


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

        if DOCKER_CONTAINER:
            if action == 'daemon_restart':
                control = DaemonControl()
                control.terminate_daemon()
                flash(gettext("Command to restart the daemon sent"), "success")
            elif action == 'frontend_reload':
                subprocess.Popen('docker restart mycodo_flask 2>&1', shell=True)
                flash(gettext("Command to reload the frontend sent"), "success")
        else:
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


#
# PID Dashboard object routes
#

def return_point_timestamp(dev_id, unit, period, measurement=None, channel=None):
    dbcon = InfluxDBClient(
        INFLUXDB_HOST,
        INFLUXDB_PORT,
        INFLUXDB_USER,
        INFLUXDB_PASSWORD,
        INFLUXDB_DATABASE)

    query_str = query_string(
        unit,
        dev_id,
        measure=measurement,
        channel=channel,
        value='LAST',
        past_sec=period)
    if query_str == 1:
        return [None, None]

    try:
        raw_data = dbcon.query(query_str).raw
        number = len(raw_data['series'][0]['values'])
        time_raw = raw_data['series'][0]['values'][number - 1][0]
        value = raw_data['series'][0]['values'][number - 1][1]
        value = '{:.3f}'.format(float(value))
        # Convert date-time to epoch (potential bottleneck for data)
        dt = date_parse(time_raw)
        timestamp = calendar.timegm(dt.timetuple()) * 1000
        return [timestamp, value]
    except KeyError:
        return [None, None]
    except Exception:
        return [None, None]


@blueprint.route('/last_pid/<pid_id>/<input_period>')
@flask_login.login_required
def last_data_pid(pid_id, input_period):
    """Return the most recent time and value from influxdb"""
    if not str_is_float(input_period):
        return '', 204

    try:
        pid = PID.query.filter(PID.unique_id == pid_id).first()

        if len(pid.measurement.split(',')) == 2:
            device_id = pid.measurement.split(',')[0]
            measurement_id = pid.measurement.split(',')[1]
        else:
            device_id = None
            measurement_id = None

        actual_measurement = DeviceMeasurements.query.filter(
            DeviceMeasurements.unique_id == measurement_id).first()
        if actual_measurement:
            actual_conversion = Conversion.query.filter(
                Conversion.unique_id == actual_measurement.conversion_id).first()
        else:
            actual_conversion = None

        (actual_channel,
         actual_unit,
         actual_measurement) = return_measurement_info(
            actual_measurement, actual_conversion)

        setpoint_unit = None
        if pid and ',' in pid.measurement:
            pid_measurement = pid.measurement.split(',')[1]
            setpoint_measurement = DeviceMeasurements.query.filter(
                DeviceMeasurements.unique_id == pid_measurement).first()
            if setpoint_measurement:
                conversion = Conversion.query.filter(
                    Conversion.unique_id == setpoint_measurement.conversion_id).first()
                _, setpoint_unit, _ = return_measurement_info(setpoint_measurement, conversion)

        p_value = return_point_timestamp(
            pid_id, 'pid_value', input_period, measurement='pid_p_value')
        i_value = return_point_timestamp(
            pid_id, 'pid_value', input_period, measurement='pid_i_value')
        d_value = return_point_timestamp(
            pid_id, 'pid_value', input_period, measurement='pid_d_value')
        if None not in (p_value[1], i_value[1], d_value[1]):
            pid_value = [p_value[0], '{:.3f}'.format(float(p_value[1]) + float(i_value[1]) + float(d_value[1]))]
        else:
            pid_value = None

        setpoint_band = None
        if pid.band:
            try:
                daemon = DaemonControl()
                setpoint_band = daemon.pid_get(pid.unique_id, 'setpoint_band')
            except:
                logger.debug("Couldn't get setpoint")

        live_data = {
            'activated': pid.is_activated,
            'paused': pid.is_paused,
            'held': pid.is_held,
            'setpoint': return_point_timestamp(
                pid_id, setpoint_unit, input_period, channel=0),
            'setpoint_band': setpoint_band,
            'pid_p_value': p_value,
            'pid_i_value': i_value,
            'pid_d_value': d_value,
            'pid_pid_value': pid_value,
            'duration_time': return_point_timestamp(
                pid_id, 's', input_period, measurement='duration_time'),
            'duty_cycle': return_point_timestamp(
                pid_id, 'percent', input_period, measurement='duty_cycle'),
            'actual': return_point_timestamp(
                device_id,
                actual_unit,
                input_period,
                measurement=actual_measurement,
                channel=actual_channel)
        }
        return jsonify(live_data)
    except KeyError:
        logger.debug("No Data returned form influxdb")
        return '', 204
    except Exception as e:
        logger.exception("URL for 'last_pid' raised and error: "
                         "{err}".format(err=e))
        return '', 204


@blueprint.route('/pid_mod_unique_id/<unique_id>/<state>')
@flask_login.login_required
def pid_mod_unique_id(unique_id, state):
    """ Manipulate output (using unique ID) """
    if not utils_general.user_has_permission('edit_controllers'):
        return 'Insufficient user permissions to manipulate PID'

    pid = PID.query.filter(PID.unique_id == unique_id).first()

    daemon = DaemonControl()
    if state == 'activate_pid':
        pid.is_activated = True
        pid.save()
        _, return_str = daemon.controller_activate(pid.unique_id)
        return return_str
    elif state == 'deactivate_pid':
        pid.is_activated = False
        pid.is_paused = False
        pid.is_held = False
        pid.save()
        _, return_str = daemon.controller_deactivate(pid.unique_id)
        return return_str
    elif state == 'pause_pid':
        pid.is_paused = True
        pid.save()
        if pid.is_activated:
            return_str = daemon.pid_pause(pid.unique_id)
        else:
            return_str = "PID Paused (Note: PID is not currently active)"
        return return_str
    elif state == 'hold_pid':
        pid.is_held = True
        pid.save()
        if pid.is_activated:
            return_str = daemon.pid_hold(pid.unique_id)
        else:
            return_str = "PID Held (Note: PID is not currently active)"
        return return_str
    elif state == 'resume_pid':
        pid.is_held = False
        pid.is_paused = False
        pid.save()
        if pid.is_activated:
            return_str = daemon.pid_resume(pid.unique_id)
        else:
            return_str = "PID Resumed (Note: PID is not currently active)"
        return return_str
    elif 'set_setpoint_pid' in state:
        pid.setpoint = state.split('|')[1]
        pid.save()
        if pid.is_activated:
            return_str = daemon.pid_set(pid.unique_id, 'setpoint', float(state.split('|')[1]))
        else:
            return_str = "PID Setpoint changed (Note: PID is not currently active)"
        return return_str


# import flask_login
# from mycodo.mycodo_flask.api import api
# @blueprint.route('/export_swagger')
# @flask_login.login_required
# def export_swagger():
#     """Export swagger JSON to swagger.json file"""
#     from mycodo.mycodo_flask.utils import utils_general
#     import json
#     if not utils_general.user_has_permission('view_settings'):
#         return 'You do not have permission to access this.', 401
#     with open("/home/pi/swagger.json", "w") as text_file:
#         text_file.write(json.dumps(api.__schema__, indent=2))
#     return 'success'
