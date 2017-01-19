# coding=utf-8
"""
This module is a temporary holding area for the mycodo_flask routes while they are organized into
their own logical packages and modules.  See https://github.com/kizniche/Mycodo/issues/129

If you are looking for something to do then breaking up these routes is a great start.  You
will see that many of the routes accept a range of variable rules and return one of multiple
pages based on the variable for the route.  Moving towards smaller sections of code for specific
endpoints is the ultimate goal because it will be easier to test, read, and modify along with
being less error prone.
"""
from __future__ import print_function
import calendar
import csv
import datetime
import logging
import os
import socket
import subprocess
import sys
import StringIO
import time
from RPi import GPIO
from dateutil.parser import parse as date_parse

from flask.blueprints import Blueprint
from flask import current_app
from flask import flash
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import Response
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_babel import gettext
from flask_influxdb import InfluxDB

from mycodo import flaskforms
from mycodo import flaskutils

from mycodo.flaskutils import gzipped
from mycodo_flask.authentication_routes import admin_exists
from mycodo_flask.authentication_routes import clear_cookie_auth
from mycodo_flask.authentication_routes import logged_in

from databases.utils import session_scope
from databases.mycodo_db.models import DisplayOrder
from databases.mycodo_db.models import Misc
from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import Remote
from databases.users_db.models import Users
from devices.camera_pi import CameraStream
from mycodo_client import DaemonControl

from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import INSTALL_DIRECTORY
from config import LOG_PATH
from config import MYCODO_VERSION

blueprint = Blueprint('general_routes',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')

logger = logging.getLogger(__name__)
influx_db = InfluxDB()


def before_blueprint_request():
    """
    Ensure databases exist and at least one user is in the user database.
    """
    if not admin_exists():
        return redirect(url_for("authentication_routes.create_admin"))
blueprint.before_request(before_blueprint_request)


@blueprint.route('/')
def home():
    """Load the default landing page"""
    if logged_in():
        return redirect(url_for('page_routes.page_live'))
    return clear_cookie_auth()


@blueprint.route('/settings', methods=('GET', 'POST'))
def page_settings():
    return redirect('settings/general')


@blueprint.route('/remote/<page>', methods=('GET', 'POST'))
def remote_admin(page):
    """Return pages for remote administraion"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    elif session['user_group'] == 'guest':
        flaskutils.deny_guest_user()
        return redirect(url_for('general_routes.home'))

    remote_hosts = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Remote)
    display_order_unsplit = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'],
        DisplayOrder,
        first=True).remote_host
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    if page == 'setup':
        form_setup = flaskforms.RemoteSetup()
        host_auth = {}
        for each_host in remote_hosts:
            host_auth[each_host.host] = flaskutils.auth_credentials(
                each_host.host, each_host.username, each_host.password_hash)

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'setup':
                if form_setup.add.data:
                    flaskutils.remote_host_add(form_setup, display_order)
            if form_name == 'mod_remote':
                if form_setup.delete.data:
                    flaskutils.remote_host_del(form_setup, display_order)
            return redirect('/remote/setup')

        return render_template('remote/setup.html',
                               form_setup=form_setup,
                               display_order=display_order,
                               remote_hosts=remote_hosts,
                               host_auth=host_auth)
    else:
        return render_template('404.html'), 404


@blueprint.route('/camera/<img_type>/<filename>')
def camera_img(img_type, filename):
    """Return an image from stills or timelapses"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    still_path = INSTALL_DIRECTORY + '/camera-stills/'
    timelapse_path = INSTALL_DIRECTORY + '/camera-timelapse/'

    # Get a list of files in each directory
    if os.path.isdir(still_path):
        still_files = (files for files in os.listdir(still_path)
                       if os.path.isfile(os.path.join(still_path, files)))
    else:
        still_files = []

    if os.path.isdir(timelapse_path):
        timelapse_files = (files for files in os.listdir(timelapse_path)
                           if os.path.isfile(os.path.join(timelapse_path, files)))
    else:
        timelapse_files = []

    if img_type == 'still':
        # Ensure file exists in directory before serving it
        if filename in still_files:
            resp = make_response(open(still_path + filename).read())
            resp.content_type = "image/jpeg"
            return resp
    elif img_type == 'timelapse':
        if filename in timelapse_files:
            resp = make_response(open(timelapse_path + filename).read())
            resp.content_type = "image/jpeg"
            return resp

    return "Image not found"


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@blueprint.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    return Response(gen(CameraStream()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@blueprint.route('/gpiostate')
def gpio_state():
    """Return the GPIO state, for relay page status"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    relay = flaskutils.db_retrieve_table(
        current_app.config['MYCODO_DB_PATH'], Relay)
    gpio_state = {}
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for each_relay in relay:
        if 0 < each_relay.pin < 40:
            GPIO.setup(each_relay.pin, GPIO.OUT)
            if GPIO.input(each_relay.pin) == each_relay.trigger:
                gpio_state[each_relay.id] = 1
            else:
                gpio_state[each_relay.id] = 0
    return jsonify(gpio_state)


@blueprint.route('/dl/<dl_type>/<path:filename>')
def download_file(dl_type, filename):
    """Serve log file to download"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    elif dl_type == 'log':
        return send_from_directory(LOG_PATH, filename, as_attachment=True)

    return '', 204


@blueprint.route('/last/<sensor_type>/<sensor_measure>/<sensor_id>/<sensor_period>')
def last_data(sensor_type, sensor_measure, sensor_id, sensor_period):
    """Return the most recent time and value from influxdb"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection
    try:
        raw_data = dbcon.query("""SELECT last(value)
                                  FROM {}
                                  WHERE device_type='{}'
                                        AND device_id='{}'
                                        AND time > now() - {}m
                               """.format(sensor_measure,
                                          sensor_type,
                                          sensor_id,
                                          sensor_period)).raw
        number = len(raw_data['series'][0]['values'])
        time_raw = raw_data['series'][0]['values'][number - 1][0]
        value = raw_data['series'][0]['values'][number - 1][1]
        # Convert date-time to epoch (potential bottleneck for data)
        dt = date_parse(time_raw)
        timestamp = calendar.timegm(dt.timetuple()) * 1000
        live_data = '[{},{}]'.format(timestamp, value)
        return Response(live_data, mimetype='text/json')
    except Exception as e:
        logger.error("URL for 'last_data' raised and error: "
                     "{err}".format(err=e))
        return '', 204


@blueprint.route('/past/<sensor_type>/<sensor_measure>/<sensor_id>/<past_seconds>')
@gzipped
def past_data(sensor_type, sensor_measure, sensor_id, past_seconds):
    """Return data from past_seconds until present from influxdb"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection
    try:
        raw_data = dbcon.query("""SELECT value
                                  FROM {}
                                  WHERE device_type='{}'
                                        AND device_id='{}'
                                        AND time > now() - {}s;
                               """.format(sensor_measure,
                                          sensor_type,
                                          sensor_id,
                                          past_seconds)).raw
        if raw_data:
            return jsonify(raw_data['series'][0]['values'])
        else:
            return '', 204
    except Exception as e:
        logger.error("URL for 'past_data' raised and error: "
                     "{err}".format(err=e))
        return '', 204


@blueprint.route('/export_data/<sensor_measure>/<sensor_id>/<start_seconds>/<end_seconds>')
@gzipped
def export_data(sensor_measure, sensor_id, start_seconds, end_seconds):
    """
    Return data from start_seconds to end_seconds from influxdb.
    Used for exporting data.
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection

    start = datetime.datetime.fromtimestamp(float(start_seconds))
    start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.datetime.fromtimestamp(float(end_seconds))
    end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    raw_data = dbcon.query("""SELECT value
                              FROM {}
                              WHERE device_id='{}'
                                    AND time >= '{}'
                                    AND time <= '{}'
                           """.format(sensor_measure,
                                      sensor_id,
                                      start_str,
                                      end_str)).raw
    if not raw_data:
        return '', 204

    def iter_csv(data_in):
        line = StringIO.StringIO()
        writer = csv.writer(line)
        writer.writerow(('timestamp', '{id}-{meas}'.format(
            id=sensor_id, meas=sensor_measure)))
        for csv_line in data_in:
            writer.writerow((csv_line[0][:-4], csv_line[1]))
            line.seek(0)
            yield line.read()
            line.truncate(0)

    response = Response(iter_csv(raw_data['series'][0]['values']), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename={id}_{meas}.csv'.format(
        id=sensor_id, meas=sensor_measure)
    return response


@blueprint.route('/async/<sensor_measure>/<sensor_id>/<start_seconds>/<end_seconds>')
@gzipped
def async_data(sensor_measure, sensor_id, start_seconds, end_seconds):
    """
    Return data from start_seconds to end_seconds from influxdb.
    Used for asynchronous graph display of many points (up to millions).
    """
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    current_app.config['INFLUXDB_USER'] = INFLUXDB_USER
    current_app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    current_app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
    dbcon = influx_db.connection

    # Set the time frame to the past year if start/end not specified
    if start_seconds == '0' and end_seconds == '0':
        # Get how many points there are in the past year
        raw_data = dbcon.query("""SELECT COUNT(value)
                                  FROM {}
                                  WHERE device_id='{}'
                               """.format(sensor_measure,
                                          sensor_id)).raw
        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year
        raw_data = dbcon.query("""SELECT value
                                  FROM {}
                                  WHERE device_id='{}'
                                        GROUP BY * LIMIT 1
                               """.format(sensor_measure,
                                          sensor_id)).raw
        first_point = raw_data['series'][0]['values'][0][0]
        end = datetime.datetime.utcnow()
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        start = datetime.datetime.utcfromtimestamp(float(start_seconds))
        start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.datetime.utcfromtimestamp(float(end_seconds))
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        raw_data = dbcon.query("""SELECT COUNT(value)
                                  FROM {}
                                  WHERE device_id='{}'
                                        AND time >= '{}'
                                        AND time <= '{}'
                               """.format(sensor_measure,
                                          sensor_id,
                                          start_str,
                                          end_str)).raw
        count_points = raw_data['series'][0]['values'][0][1]
        # Get the timestamp of the first point in the past year
        raw_data = dbcon.query("""SELECT value
                                  FROM {}
                                  WHERE device_id='{}'
                                        AND time >= '{}'
                                        AND time <= '{}'
                                        GROUP BY * LIMIT 1
                               """.format(sensor_measure,
                                          sensor_id,
                                          start_str,
                                          end_str)).raw
        first_point = raw_data['series'][0]['values'][0][0]

    start = datetime.datetime.strptime(first_point[:26],
                                       '%Y-%m-%dT%H:%M:%S.%f')
    start_str = start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    logger.debug('Count = {}'.format(count_points), file=sys.stderr)
    logger.debug('Start = {}'.format(start), file=sys.stderr)
    logger.debug('End   = {}'.format(end), file=sys.stderr)

    # How many seconds between the start and end period
    time_difference_seconds = (end - start).total_seconds()
    logger.debug('Difference seconds = {}'.format(time_difference_seconds),
                 file=sys.stderr)

    # If there are more than 700 points in the time frame, we need to group
    # data points into 700 groups with points averaged in each group.
    if count_points > 700:
        # Average period between sensor reads
        seconds_per_point = time_difference_seconds / count_points
        logger.debug('Seconds per point = {}'.format(seconds_per_point),
                     file=sys.stderr)

        # How many seconds to group data points in
        group_seconds = int(time_difference_seconds / 700)
        logger.debug('Group seconds = {}'.format(group_seconds),
                     file=sys.stderr)

        try:
            raw_data = dbcon.query("""SELECT MEAN(value)
                                      FROM {}
                                      WHERE device_id='{}'
                                            AND time >= '{}'
                                            AND time <= '{}' GROUP BY TIME({}s)
                                   """.format(sensor_measure,
                                              sensor_id,
                                              start_str,
                                              end_str,
                                              group_seconds)).raw
            return jsonify(raw_data['series'][0]['values'])
        except Exception as e:
            logger.error("URL for 'async_data' raised and error: "
                         "{err}".format(err=e))
            return '', 204
    else:
        try:
            raw_data = dbcon.query("""SELECT value
                                      FROM {}
                                      WHERE device_id='{}'
                                            AND time >= '{}'
                                            AND time <= '{}'
                                   """.format(sensor_measure,
                                              sensor_id,
                                              start_str,
                                              end_str)).raw
            return jsonify(raw_data['series'][0]['values'])
        except Exception as e:
            logger.error("URL for 'async_data' raised and error: "
                         "{err}".format(err=e))
            return '', 204


@blueprint.route('/daemonactive')
def daemon_active():
    """Return 'alive' if the daemon is running"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    try:
        control = DaemonControl()
        return control.daemon_status()
    except Exception as e:
        logger.error("URL for 'daemon_active' raised and error: "
                     "{err}".format(err=e))
        return '0'


@blueprint.route('/systemctl/<action>')
def computer_command(action):
    """Execute one of several commands as root"""
    if not logged_in():
        return redirect(url_for('general_routes.home'))

    if session['user_group'] == 'guest':
        flaskutils.deny_guest_user()
        return redirect(url_for('general_routes.home'))

    try:
        if action not in ['restart', 'shutdown']:
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
        return redirect('/settings')
    except Exception as e:
        logger.error("System command '{cmd}' raised and error: "
                     "{err}".format(cmd=action, err=e))
        flash("System command '{cmd}' raised and error: "
              "{err}".format(cmd=action, err=e), "error")
        return redirect(url_for('general_routes.home'))


@blueprint.route('/newremote/')
def newremote():
    """Verify authentication as a client computer to the remote admin"""
    user = request.args.get('user')
    pass_word = request.args.get('passw')
    with session_scope(current_app.config['USER_DB_PATH']) as new_session:
        user = new_session.query(Users).filter(
            Users.user_name == user).first()
        new_session.expunge_all()
        new_session.close()
    # TODO: Change sleep() to max requests per duration of time
    time.sleep(1)  # Slow down requests (hackish, prevent brute force attack)
    if user:
        if Users().check_password(pass_word, user.user_password_hash) == user.user_password_hash:
            return jsonify(status=0,
                           message="{hash}".format(
                               hash=user.user_password_hash))
    return jsonify(status=1,
                   message="Unable to authenticate with user and password.")


@blueprint.route('/auth/')
def data():
    """Checks authentication for remote admin"""
    user = request.args.get('user')
    password_hash = request.args.get('pw_hash')
    with session_scope(current_app.config['USER_DB_PATH']) as new_session:
        user = new_session.query(Users).filter(
            Users.user_name == user).first()
        new_session.expunge_all()
        new_session.close()
    # TODO: Change sleep() to max requests per duration of time
    time.sleep(1)  # Slow down requests (hackish, prevents brute force attack)
    if (user and
            user.user_restriction == 'admin' and
            password_hash == user.user_password_hash):
        return "0"
    return "1"


@blueprint.route('/robots.txt')
def static_from_root():
    """Return static robots.txt"""
    return send_from_directory(current_app.static_folder, request.path[1:])


@blueprint.context_processor
def inject_mycodo_version():
    """Variables to send with every page request"""
    try:
        control = DaemonControl()
        daemon_status = control.daemon_status()
    except Exception as e:
        logger.error(gettext("URL for 'inject_mycodo_version' raised and "
                             "error: %(err)s", err=e))
        daemon_status = '0'

    with session_scope(current_app.config['MYCODO_DB_PATH']) as db_session:
        misc = db_session.query(Misc).first()
        return dict(daemon_status=daemon_status,
                    mycodo_version=MYCODO_VERSION,
                    host=socket.gethostname(),
                    hide_alert_success=misc.hide_alert_success,
                    hide_alert_info=misc.hide_alert_info,
                    hide_alert_warning=misc.hide_alert_warning)


@blueprint.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404
