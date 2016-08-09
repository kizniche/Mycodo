# coding=utf-8

import csv
import datetime
import filecmp
import geocoder
import grp
import logging
import os
import picamera
import pwd
import random
import resource
import smtplib
import socket
import string
import subprocess
import time
from collections import OrderedDict
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email import Encoders
from influxdb import InfluxDBClient
from lockfile import LockFile
from sqlalchemy import func

from config import ID_FILE
from config import INSTALL_DIRECTORY
from config import MYCODO_VERSION
from config import SQL_DATABASE_MYCODO
from config import SQL_DATABASE_USER
from config import STATS_CSV
from config import STATS_INTERVAL
from databases.mycodo_db.models import LCD
from databases.mycodo_db.models import Log
from databases.mycodo_db.models import Method
from databases.mycodo_db.models import PID
from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import Sensor
from databases.mycodo_db.models import Timer
from databases.users_db.models import Users
from databases.utils import session_scope

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
USER_DB_PATH = 'sqlite:///' + SQL_DATABASE_USER



#
# Filesystem and command tools
#

def cmd_output(command):
    """Executed command and returns a list of lines from the output"""
    full_cmd = 'su mycodo && {}'.format(command)
    cmd = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, shell=True)
    cmd_output, cmd_err = cmd.communicate()
    cmd_status = cmd.wait()
    return cmd_output, cmd_err, cmd_status


def assure_path_exists(new_dir):
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
        set_user_grp(new_dir, 'mycodo', 'mycodo')


def set_user_grp(filepath, user, group):
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    os.chown(filepath, uid, gid)



#
# Camera record
#

def camera_record(record_type, duration_sec=10):
    now = time.time()
    timestamp = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d_%H-%M-%S')
    try:
        if record_type == 'photo':
            path_stills = '{}/camera-stills'.format(INSTALL_DIRECTORY)
            still_filename = 'Still-{}.jpg'.format(timestamp)
            output_filepath = '{}/{}'.format(path_stills, still_filename)
            assure_path_exists(path_stills)
            with picamera.PiCamera() as camera:
                camera.resolution = (1296, 972)
                camera.hflip = True
                camera.vflip = True
                camera.start_preview()
                time.sleep(2)  # Camera warm-up time
                camera.capture(output_filepath, use_video_port=True)
        elif record_type == 'video':
            path_video = '{}/camera-video'.format(INSTALL_DIRECTORY)
            video_filename = 'Video-{}.h264'.format(timestamp)
            output_filepath = '{}/{}'.format(path_video, video_filename)
            assure_path_exists(path_video)
            with picamera.PiCamera() as camera:
                camera.resolution = (1296, 972)
                camera.hflip = True
                camera.vflip = True
                camera.start_preview()
                time.sleep(2)
                camera.start_recording(output_filepath, format='h264', quality=20)
                camera.wait_recording(duration_sec)
                camera.stop_recording()
    except:
        pass

    try:
        set_user_grp(output_filepath, 'mycodo', 'mycodo')
    except:
        pass


#
# Email notification
#

def email(logging, smtp_host, smtp_ssl,
          smtp_port, smtp_user, smtp_pass,
          smtp_email_from, email_to, message,
          attachment_file=False, attachment_type=False):
    """
    Email a specific recipient or recipients a message.

    :return: success (0) or failure (1)
    :rtype: bool

    :param email_to: Who to email
    :type email_to: str or list
    :param message: Message in the body of the email
    :type message: str
    """
    try:
        if smtp_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
            server.starttls()
        server.login(smtp_user, smtp_pass)
        msg = MIMEMultipart()
        msg['Subject'] = "Mycodo Notification ({})".format(socket.gethostname())
        msg['From'] = smtp_email_from
        msg['To'] = email_to
        msg_body = MIMEText(message.decode('utf-8'), 'plain', 'utf-8')
        msg.attach(msg_body)

        if attachment_file and attachment_type == 'still':
            img_data = open(attachment_file, 'rb').read()
            image = MIMEImage(img_data, name=os.path.basename(attachment_file))
            msg.attach(image)
        elif attachment_file and attachment_type == 'video':
            out_filename = '{}-compressed.h264'.format(attachment_file)
            cmd_output('avconv -i "{}" -vf scale=-1:768 -c:v libx264 -preset veryfast -crf 22 -c:a copy "{}"'.format(attachment_file, out_filename))
            set_user_grp(out_filename, 'mycodo', 'mycodo')
            f = open(attachment_file, 'rb').read()
            video = MIMEBase('application', 'octet-stream')
            video.set_payload(f)
            Encoders.encode_base64(video)
            video.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(attachment_file)))
            msg.attach(video)

        server.sendmail(msg['From'], msg['To'].split(","), msg.as_string())
        server.quit()
        return 0
    except Exception as error:
        if logging:
            logging.exception("[Email Notification] Cound not send email to {} "
                            "with message: {}. Error: {}".format(email_to, message, error))
        return 1


#
# Influxdb
#

def read_last_influxdb(host, port, user, password,
                       dbname, device_id, measure_type, duration_min=1):
    """
    Query Influxdb for the last entry within the past minute,
    for a set of conditions.

    example:
        read_last_influxdb('localhost', 8086, 'mycodo', 'password123',
                           'mycodo_db', '00000001', 'temperature')

    :return: list of time and value
    :rtype: list

    :param host: What influxdb address
    :type host: str
    :param port: What influxdb port
    :type port: int
    :param user: What user to connect to influxdb with
    :type user: str
    :param password: What password to supply for Influxdb user
    :type password: str
    :param dbname: What Influxdb database name to write to
    :type dbname: str
    :param device_id: What device_id tag to query in the Influxdb
        database (ex. '00000001')
    :type device_id: str
    :param measure_type: What measurement to query in the Influxdb
        database (ex. 'temperature', 'duration')
    :type measure_type: str
    :param duration_min: How many minutes to look for a past measurement
    :type duration_min: int
    """
    client = InfluxDBClient(host, port, user, password, dbname)
    query = """SELECT value
                   FROM   {}
                   WHERE  device_id = '{}'
                          AND TIME > Now() - {}m
                          ORDER BY time
                          DESC LIMIT 1;
            """.format(measure_type, device_id, duration_min)
    return client.query(query)


def read_duration_influxdb(host, port, user, password, dbname,
                           device_id, measure_type, duration):
    """
    Query Influxdb for all entries within the past <duration> minutes,
    for a set of conditions.

    example:
        read_last_influxdb('localhost', 8086, 'mycodo', 'password123',
                           'mycodo_db', '00000001', 'temperature', 10)

    :return: list of times and values
    :rtype: list

    :param host: What influxdb address
    :type host: str
    :param port: What influxdb port
    :type port: int
    :param user: What user to connect to influxdb with
    :type user: str
    :param password: What password to supply for Influxdb user
    :type password: str
    :param dbname: What Influxdb database name to write to
    :type dbname: str
    :param device_id: What device_id tag to query in the Influxdb
        database (ex. '00000001')
    :type device_id: str
    :param measure_type: What measurement to query in the Influxdb
        database (ex. 'temperature', 'duration')
    :type measure_type: str
    :param duration: How long in the past, from now, should data be
        queried from the Influxdb database
    :type duration: int
    """
    client = InfluxDBClient(host, port, user, password, dbname)
    query = """SELECT value
                   FROM   {}
                   WHERE  device_id = '{}'
                          AND TIME > Now() - {}m;
            """.format(measure_type, device_id, duration)
    return client.query(query)


def write_influxdb(logger, host, port, user, password,
                   dbname, device_type, device_id,
                   measure_type, value):
    """
    Write an entry into an Influxdb database

    example:
        write_influxdb('localhost', 8086, 'mycodo', 'password123',
                       'mycodo_db', '00000001', 'temperature', 37.5)

    :return: success (0) or failure (1)
    :rtype: bool

    :param host: What influxdb address
    :type host: str
    :param port: What influxdb port
    :type port: int
    :param user: What user to connect to influxdb with
    :type user: str
    :param password: What password to supply for Influxdb user
    :type password: str
    :param dbname: What Influxdb database name to write to
    :type dbname: str
    :param device_type: What device_type tag to enter in the Influxdb
        database (ex. 'tsensor', 'relay')
    :type device_type: str
    :param device_id: What device_id tag to enter in the Influxdb
        database (ex. '00000001')
    :type device_id: str
    :param measure_type: What type of measurement for the Influxdb
        database entry (ex. 'temperature')
    :type measure_type: str
    :param value: The value being entered into the Influxdb database
    :type value: int or float
    """
    client = InfluxDBClient(host, port, user, password, dbname)
    data = format_influxdb_data(device_type,
                                device_id,
                                measure_type,
                                value)
    try:
        client.write_points(data)
        # logger.debug('Write {} {} to {}, '
        #       'device_id={} device_type={}'.format(value,
        #                                            measure_type,
        #                                            dbname,
        #                                            device_id,
        #                                            device_type))
        return 0
    except Exception as except_msg:
        logger.debug('Failed to write measurement to influxdb (Device ID: '
                         '{}). Data that was submitted for writing: {}. '
                         'Exception: {}'.format(device_id, data, except_msg))
        return 1


def write_influxdb_list(logger, host, port, user, password,
                        dbname, data):
    """
    Write an entry into an Influxdb database

    example:
        write_influxdb('localhost', 8086, 'mycodo', 'password123',
                       'mycodo_db', data_list_of_dictionaries)

    :return: success (0) or failure (1)
    :rtype: bool

    :param host: What influxdb address
    :type host: str
    :param port: What influxdb port
    :type port: int
    :param user: What user to connect to influxdb with
    :type user: str
    :param password: What password to supply for Influxdb user
    :type password: str
    :param dbname: What Influxdb database name to write to
    :type dbname: str
    :param data_list_of_dictionaries: The data being entered into the Influxdb
        database. See controller_sensor.py function addMeasurementInfluxdb()
    :type data_list_of_dictionaries: list of dictionaries
    """
    client = InfluxDBClient(host, port, user, password, dbname)
    try:
        client.write_points(data)
        return 0
    except Exception as except_msg:
        logger.debug('Failed to write measurements to influxdb (Device ID: '
                         '{}). Data that was submitted for writing: {}. '
                         'Exception: {}'.format(device_id, data, except_msg))
        return 1


def format_influxdb_data(device_type, device_id, measure_type, value):
    """
    Format data for entry into an Influxdb database

    example:
        format_influxdb_data('tsensor', '00000001', 'temperature', 37.5)
        format_influxdb_data('relay', '00000002', 'duration', 15.2)

    :return: list of measurement type, tags, and value
    :rtype: list

    :param device_type: The type of device (ex. 'tsensor', 'htsensor',
        'co2sensor', 'relay')
    :type device_type: str
    :param device_id: 8-character alpha-numeric ID associated with device
    :type device_id: str
    :param measure_type: The type of data being entered into the Influxdb
        database (ex. 'temperature', 'duration')
    :type measure_type: str
    :param value: The value being entered into the Influxdb database
    :type value: int or float

    """
    return [
        {
            "measurement": measure_type,
            "tags": {
                "device_id": device_id,
                "device_type": device_type
            },
            "fields": {
                "value": value
            }
        }
    ]

#
# Usage Statictics
#

def get_pi_revision():
    """
    Return the Raspbery Pi board revision ID from /proc/cpuinfo

    """
    # Extract board revision from cpuinfo file
    myrevision = "0000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:8]=='Revision':
                length=len(line)
                myrevision = line[11:length-1]
        f.close()
    except:
        myrevision = "0000"
    return myrevision


#
# Anonymous usage statistics collection and transmission
#

def return_stat_file_dict():
    """
    Read the statistics file and return as keys and values in a dictionary

    """
    with open(STATS_CSV, mode='r') as infile:
        reader = csv.reader(infile)
        return OrderedDict((row[0], row[1]) for row in reader)


def recreate_stat_file():
    """
    Create a statistics file with basic stats

    if anonymous_id is not provided, generate one

    """
    uid_gid = pwd.getpwnam('mycodo').pw_uid
    if not os.path.isfile(ID_FILE):
        anonymous_id = ''.join([random.choice(
            string.ascii_letters + string.digits) for n in xrange(12)])
        with open(ID_FILE, 'w') as write_file:
            write_file.write('{}'.format(anonymous_id))
        os.chown(ID_FILE, uid_gid, uid_gid)
        os.chmod(ID_FILE, 0664)

    with open(ID_FILE, 'r') as read_file:
        stat_id = read_file.read()

    new_stat_data=[['stat', 'value'],
                   ['id', stat_id],
                   ['next_send', time.time()+STATS_INTERVAL],
                   ['RPi_revision', get_pi_revision()],
                   ['Mycodo_revision', MYCODO_VERSION],
                   ['country', 'None'],
                   ['daemon_startup_seconds', 0.0],
                   ['ram_use_mb', 0.0],
                   ['num_users_admin', 0],
                   ['num_users_guest', 0],
                   ['num_lcds', 0],
                   ['num_lcds_active', 0],
                   ['num_logs', 0],
                   ['num_logs_active', 0],
                   ['num_methods', 0],
                   ['num_methods_in_pid', 0],
                   ['num_pids', 0],
                   ['num_pids_active', 0],
                   ['num_relays', 0],
                   ['num_sensors', 0],
                   ['num_sensors_active', 0],
                   ['num_timers', 0],
                   ['num_timers_active', 0]]
             
    with open(STATS_CSV, 'w') as csv_stat_file:
        write_csv = csv.writer(csv_stat_file)
        for row in new_stat_data:
            write_csv.writerow(row)
    os.chown(STATS_CSV, uid_gid, uid_gid)
    os.chmod(STATS_CSV, 0664)


def increment_stat(logger, stat, amount):
    """
    Increment the value in the statistics file by amount

    """
    stat_dict = return_stat_file_dict()
    add_update_stat(logger, stat, int(stat_dict[stat])+amount)


def add_update_stat(logger, stat, value):
    """
    Either add or update the value in the statistics file with the new value.
    If the key exists, update the value.
    If the key doesn't exist, add the key and value.

    """
    try:
        stats_dict = {stat:value}
        tempfilename = os.path.splitext(STATS_CSV)[0] + '.bak'
        try:
            os.remove(tempfilename)  # delete any existing temp file
        except OSError:
            pass
        os.rename(STATS_CSV, tempfilename)

        # create a temporary dictionary from the input file
        with open(tempfilename, mode='r') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # skip and save header
            temp_dict = OrderedDict((row[0], row[1]) for row in reader)

        # only add items from my_dict that weren't already present
        temp_dict.update({key: value for (key, value) in stats_dict.items()
                              if key not in temp_dict})

        # only update items from my_dict that are already present
        temp_dict.update({key: value for (key, value) in stats_dict.items()})

        # create updated version of file    
        with open(STATS_CSV, mode='w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(temp_dict.items())

        uid_gid = pwd.getpwnam('mycodo').pw_uid
        os.chown(STATS_CSV, uid_gid, uid_gid)
        os.chmod(STATS_CSV, 0664)
        os.remove(tempfilename)  # delete backed-up original
    except Exception as except_msg:
        logger.exception('[Statistics] Could not update stat csv: '
            '{}'.format(except_msg))
        os.rename(tempfilename, STATS_CSV)  # rename temp file to original


def send_stats(logger, host, port, user, password, dbname):
    """
    Send anonymous usage statistics

    Example use:
        current_stat = return_stat_file_dict()
        add_update_stat(logger, 'stat', current_stat['stat'] + 5)
    """
    try:
        client = InfluxDBClient(host, port, user, password, dbname)
        # Prepare stats before sending
        with session_scope(MYCODO_DB_PATH) as new_session:
            relays = new_session.query(Relay)
            add_update_stat(logger, 'num_relays', get_count(relays))

            sensors = new_session.query(Sensor)
            add_update_stat(logger, 'num_sensors', get_count(sensors))
            add_update_stat(logger, 'num_sensors_active', get_count(sensors.filter(
                Sensor.activated == True)))

            pids = new_session.query(PID)
            add_update_stat(logger, 'num_pids', get_count(pids))
            add_update_stat(logger, 'num_pids_active', get_count(pids.filter(
                PID.activated == True)))

            lcds = new_session.query(LCD)
            add_update_stat(logger, 'num_lcds', get_count(lcds))
            add_update_stat(logger, 'num_lcds_active', get_count(lcds.filter(
                LCD.activated == True)))

            logs = new_session.query(Log)
            add_update_stat(logger, 'num_logs', get_count(logs))
            add_update_stat(logger, 'num_logs_active', get_count(logs.filter(
                Log.activated == True)))

            methods = new_session.query(Method)
            add_update_stat(logger, 'num_methods', get_count(methods.filter(
                Method.method_order == 0)))
            add_update_stat(logger, 'num_methods_in_pid', get_count(pids.filter(
                PID.method_id != '')))
            
            timers = new_session.query(Timer)
            add_update_stat(logger, 'num_timers', get_count(timers))
            add_update_stat(logger, 'num_timers_active', get_count(timers.filter(
                Timer.activated == True)))

        add_update_stat(logger, 'country', geocoder.ip('me').country)
        add_update_stat(logger, 'ram_use_mb', resource.getrusage(
            resource.RUSAGE_SELF).ru_maxrss / float(1000))
        
        user_count = 0
        admin_count = 0
        with session_scope(USER_DB_PATH) as db_session:
            users = db_session.query(Users).all()
            for each_user in users:
                user_count += 1
                if each_user.user_restriction == 'admin':
                    admin_count += 1
        add_update_stat(logger, 'num_users_admin', admin_count)
        add_update_stat(logger, 'num_users_guest', user_count-admin_count)

        add_update_stat(logger, 'Mycodo_revision', MYCODO_VERSION)

        # Combine stats into list of dictionaries to be pushed to influxdb
        new_stats_dict = return_stat_file_dict()
        formatted_stat_dict = []
        for each_key, each_value in new_stats_dict.iteritems():
            if each_key != 'stat':  # Do not send header row
                formatted_stat_dict = add_stat_dict(formatted_stat_dict,
                                                    new_stats_dict['id'],
                                                    each_key,
                                                    each_value)

        # Send stats to influxdb
        client.write_points(formatted_stat_dict)
        logger.debug("[Daemon] Sent anonymous usage statistics")
        return 0
    except Exception as except_msg:
        logger.exception('[Daemon] Could not send anonymous usage statictics: '
            '{}'.format(except_msg))
        return 1


def get_count(q):
    """Count the number of rows from an SQL query"""
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def add_stat_dict(stats_dict, anonymous_id, measurement, value):
    """Format statistics data for entry into Influxdb database"""
    # anonymous_id =  # get anonymous_id from stat file
    new_stat_entry = {
        "measurement": measurement,
        "tags": {
            "anonymous_id": anonymous_id
        },
        "fields": {
            "value": value
        }
    }
    stats_dict.append(new_stat_entry)
    return stats_dict
