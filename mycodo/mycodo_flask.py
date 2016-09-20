#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodo_flask.py - Flask web server for Mycodo, for visualizing data,
#                    configuring the system, and controlling the daemon.
#
#  Copyright (C) 2016  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

from __future__ import print_function # In python 2.7
import sys

import argparse
import calendar
import csv
import datetime
import glob
import gzip
import functools
import logging
import os
import pwd
import random
import socket
import sqlalchemy
import string
import subprocess
import time
import RPi.GPIO as GPIO
from collections import OrderedDict
from cStringIO import StringIO as IO
from dateutil.parser import parse as date_parse
from flask import Flask, after_this_request, flash, make_response, redirect, render_template, request, send_from_directory, session, g, jsonify, Response
from flask_influxdb import InfluxDB
from flask_sslify import SSLify
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm import sessionmaker

import flaskforms
import flaskutils
from databases.utils import session_scope
from databases.mycodo_db.models import CameraStill
from databases.mycodo_db.models import DisplayOrder
from databases.mycodo_db.models import Graph
from databases.mycodo_db.models import LCD
from databases.mycodo_db.models import Log
from databases.mycodo_db.models import Method
from databases.mycodo_db.models import Misc
from databases.mycodo_db.models import PID
from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import RelayConditional
from databases.mycodo_db.models import Remote
from databases.mycodo_db.models import Sensor
from databases.mycodo_db.models import SensorConditional
from databases.mycodo_db.models import SMTP
from databases.mycodo_db.models import Timer
from databases.users_db.models import Users

from utils.camera import camera_record
from utils.method import sine_wave_y_out, bezier_curve_y_out
from utils.statistics import return_stat_file_dict
from utils.system_pi import cmd_output
from utils.system_pi import internet

from devices.camera_pi import CameraStream
from devices.camera_pi import CameraTimelapse

from mycodo_client import DaemonControl

from config import DAEMON_LOG_FILE
from config import FILE_TIMELAPSE_PARAM
from config import HTTP_LOG_FILE
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import INSTALL_DIRECTORY
from config import LOG_PATH
from config import LOGIN_LOG_FILE
from config import LOCK_FILE_STREAM
from config import LOCK_FILE_TIMELAPSE
from config import MYCODO_VERSION
from config import RESTORE_LOG_FILE
from config import SQL_DATABASE_MYCODO
from config import SQL_DATABASE_USER
from config import STATS_CSV
from config import UPDATE_LOG_FILE


MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
USER_DB_PATH = 'sqlite:///' + SQL_DATABASE_USER

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend/static')
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend/templates')

app = Flask(__name__, static_folder=static_dir, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)
app.jinja_env.add_extension('jinja2.ext.do')  # Global values in jinja

influx_db = InfluxDB(app)

# Check user option to force all web connections to use SSL
misc = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Misc, first=True)
if misc.force_https:
    sslify = SSLify(app)


def gzipped(f):
    """
    Allows gzipping the response of any view.
    Just add '@gzipped' after the '@app'.
    Used mainly for sending large amounts of data for graphs.
    """
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)

            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func


@app.before_request
def before_request():
    if (not os.path.isfile(SQL_DATABASE_MYCODO) or
        not os.path.isfile(SQL_DATABASE_USER)):
        return "Error: Cannot find databases. Run \"init_databases.py --install_db all\" to generate them."
    with session_scope(USER_DB_PATH) as new_session:
        user = new_session.query(Users).first()
        if not user.user_id:
            return "Error: No user found. Run \"init_databases.py --addadmin\" to add one"


@app.route('/')
def home():
    if logged_in():
        return redirect('/live')
    return clear_cookie_auth()


@app.route('/<page>', methods=('GET', 'POST'))
def page(page):
    if not logged_in():
        return redirect('/')

    # Default landing page
    if page == 'live':
        display_order_sensor_sorted = []
        pid = flaskutils.db_retrieve_table(MYCODO_DB_PATH, PID)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        sensor = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Sensor)
        timer = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Timer)

        pid_display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).pid
        if pid_display_order_unsplit:
            pid_display_order = pid_display_order_unsplit.split(",")
        else:
            pid_display_order = []

        sensor_display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).sensor
        if sensor_display_order_unsplit:
            sensor_display_order = sensor_display_order_unsplit.split(",")
        else:
            sensor_display_order = []

        for each_sensor_order in sensor_display_order:
            for each_sensor in sensor:
                if each_sensor_order == each_sensor.id and each_sensor.activated:
                    display_order_sensor_sorted.append(each_sensor.id)

        with session_scope(MYCODO_DB_PATH) as new_session:
            method = new_session.query(Method).filter(Method.method_order == 0).all()
            new_session.expunge_all()
            new_session.close()

        return render_template('pages/live.html',
                               method=method,
                               pid=pid,
                               relay=relay,
                               sensor=sensor,
                               timer=timer,
                               pidDisplayOrder=pid_display_order,
                               sensorDisplayOrderSorted=display_order_sensor_sorted)

    elif page == 'graph':
        display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).graph
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []
        graph = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Graph)
        pid = flaskutils.db_retrieve_table(MYCODO_DB_PATH, PID)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        sensor = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Sensor)
        formModGraph = flaskforms.ModGraph()
        formDelGraph = flaskforms.DelGraph()
        formOrderGraph = flaskforms.OrderGraph()
        formAddGraph = flaskforms.AddGraph()

        # retrieve all available measurements and relays
        pid_choices = flaskutils.choices_id_name(pid)
        relay_choices = flaskutils.choices_id_name(relay)
        sensor_choices = flaskutils.choices_sensors(sensor)

        # What units to display for each measurement in the graph legend
        measurement_units = {'cpu_load_1m':'',
                             'cpu_load_5m':'',
                             'cpu_load_15m':'',
                             'temperature':'°C'.decode('utf-8'),
                             'temperature_object':'°C'.decode('utf-8'),
                             'temperature_die':'°C'.decode('utf-8'),
                             'humidity':' %',
                             'dewpoint':'°C'.decode('utf-8'),
                             'co2':' ppmv',
                             'lux':'lx',
                             'pressure':' Pa',
                             'altitude':' m'}

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
            sensor_choices_split.update({order[0]:order[1]})

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

    # Default 'settings' landing page
    elif page == 'settings':
        return redirect('settings/general')

    # Modify sensor SQL database
    elif page == 'sensor':
        display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).sensor
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []
        lcd = flaskutils.db_retrieve_table(MYCODO_DB_PATH, LCD)
        pid = flaskutils.db_retrieve_table(MYCODO_DB_PATH, PID)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        sensor = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Sensor)
        sensor_conditional = flaskutils.db_retrieve_table(MYCODO_DB_PATH, SensorConditional)
        users = flaskutils.db_retrieve_table(USER_DB_PATH, Users)
        formAddSensor = flaskforms.AddSensor()
        formModSensor = flaskforms.ModSensor()
        formModSensorCond = flaskforms.ModSensorConditional()

        # Create list of file names from the sensor_options directory
        # Used in generating the correct options for each sensor/device
        sensor_template_list = []
        sensor_path = "{}/mycodo/frontend/templates/pages/sensor_options/".format(INSTALL_DIRECTORY)
        for (dirpath, dirnames, filenames) in os.walk(sensor_path):
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

    elif page == 'relay':
        display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).relay
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []
        lcd = flaskutils.db_retrieve_table(MYCODO_DB_PATH, LCD)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        relayconditional = flaskutils.db_retrieve_table(MYCODO_DB_PATH, RelayConditional)
        users = flaskutils.db_retrieve_table(USER_DB_PATH, Users)
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

    elif page == 'pid':
        display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).pid
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []

        pids = flaskutils.db_retrieve_table(MYCODO_DB_PATH, PID)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        sensor = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Sensor)
        formModPIDMethod = flaskforms.ModPIDMethod()
        formActivatePID = flaskforms.ActivatePID()
        formAddPID = flaskforms.AddPID()
        formAddPIDSetpoint = flaskforms.AddPIDsetpoint()
        formModPIDSetpoint = flaskforms.ModPIDsetpoint()
        formDeactivatePID = flaskforms.DeactivatePID()
        formDelPID = flaskforms.DelPID()
        formModPID = flaskforms.ModPID()
        formOrderPID = flaskforms.OrderPID()

        with session_scope(MYCODO_DB_PATH) as new_session:
            method = new_session.query(Method).filter(Method.method_order == 0).all()
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
            elif form_name == 'addPIDSetpoint':
                flaskutils.pid_add_setpoint(formAddPIDSetpoint)
            elif form_name == 'modPIDSetpoint':
                flaskutils.pid_mod_setpoint(formModPIDSetpoint)
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
                               formAddPIDSetpoint=formAddPIDSetpoint,
                               formModPIDSetpoint=formModPIDSetpoint,
                               formModPID=formModPID,
                               formDelPID=formDelPID,
                               formActivatePID=formActivatePID,
                               formDeactivatePID=formDeactivatePID)

    elif page == 'lcd':
        display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).lcd
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []
        lcd = flaskutils.db_retrieve_table(MYCODO_DB_PATH, LCD)
        pid = flaskutils.db_retrieve_table(MYCODO_DB_PATH, PID)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        sensor = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Sensor)
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

    elif page == 'log':
        display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).log
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []
        log = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Log)
        sensor = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Sensor)
        formLog = flaskforms.Log()

        # Determine if a log file exists for each log controller
        log_file_exists = {}
        for each_log in log:
            fname = '{}/{}-{}.log'.format(LOG_PATH, each_log.sensor_id, each_log.measure_type)
            if os.path.isfile(fname):
                log_file_exists[each_log.id] = True
            else:
                log_file_exists[each_log.id] = False

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

    elif page == 'timer':
        display_order_unsplit = flaskutils.db_retrieve_table(MYCODO_DB_PATH, DisplayOrder, first=True).timer
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []
        timer = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Timer)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        relay_choices = flaskutils.choices_id_name(relay)
        formTimer = flaskforms.Timer()

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addTimer':
                flaskutils.timer_add(formTimer, request.form['timerType'], display_order)
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


    elif page == 'backup':
        if session['user_group'] == 'guest':
            flash('Guests are not permitted to view backups.', 'error')
            return redirect('/')
        formBackup = flaskforms.Backup()
        backup_dirs = []
        backups_sorted = []
        if not os.path.isdir('/var/Mycodo-backups'):
            flash("Error: Backup directory doesn't exist.", "error")
        else:
            backup_dirs = sorted(next(os.walk('/var/Mycodo-backups'))[1])

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'restore':
                if formBackup.restore.data:
                    flash("Restore functionality is not currently enabled.", "error")
                    # formUpdate.restore.data
                    # restore_command = INSTALL_DIRECTORY+'/mycodo/scripts/mycodo_wrapper restore '+ +'  >> /var/log/mycodo/mycodorestore.log 2>&1'
                    # subprocess.Popen(restore_command, shell=True)

        return render_template('settings/backup.html',
                               formBackup=formBackup,
                               backups_sorted=backup_dirs)


    elif page == 'upgrade':
        if session['user_group'] == 'guest':
            flash('Guests are not permitted to view the upgrade panel.', 'error')
            return redirect('/')
        if not internet():
            flash("Upgrade functionality is disabled because an internet "
                  "connection was unable to be detected.", "error")
            return render_template('settings/upgrade.html',
                                   is_internet=False)
        is_internet = True
        updating = 0
        update_available = False
        backup_directories = []
        list_only_commits = []
        restore_commits_extended = []
        commits_extended_messages = []
        formBackup = flaskforms.Backup()
        formUpdate = flaskforms.Update()

        cmd_output("git fetch origin", su_mycodo=False)
        current_commit, _, _ = cmd_output("git rev-parse --short HEAD", su_mycodo=False)
        commits_behind, _, _ = cmd_output("git log --oneline | head -n 1", su_mycodo=False)
        commits_behind_list = commits_behind.split('\n')
        commits_ahead, commits_ahead_err, _ = cmd_output("git log --oneline master...origin/master", su_mycodo=False)
        commits_ahead_list = commits_ahead.split('\n')
        if commits_ahead and commits_ahead_err is None:
            update_available = True

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'update':
                if formUpdate.update.data:
                    if update_available:
                        subprocess.Popen(INSTALL_DIRECTORY + '/mycodo/scripts/mycodo_wrapper upgrade >> /var/log/mycodo/mycodoupdate.log 2>&1', shell=True)
                        flash("THe upgrade has started. The daemon will be "
                              "stopped during the upgrade. Give the "
                              "process several minutes to complete "
                              "before doing anything. It may seem "
                              "unresponsive at times. When the update "
                              "has successfully finished, the daemon "
                              "status indicator at the top left will "
                              "turn from red to green. You can monitor "
                              "the update progress under Tools->Mycodo Logs"
                              "->Update Log.", "success")
                    else:
                        flash("You cannot update if an update is not available", "error")

        try:
            with open(INSTALL_DIRECTORY + '/.updating') as f:
                updating = int(f.read(1))
        except IOError:
            try:
                with open(INSTALL_DIRECTORY + '/.updating', 'w') as f:
                    f.write('0')
            finally:
                updating = 0

        return render_template('settings/upgrade.html',
                               formBackup=formBackup,
                               formUpdate=formUpdate,
                               current_commit=current_commit,
                               commits_ahead=commits_ahead_list,
                               commits_behind=commits_behind_list,
                               update_available=update_available,
                               updating=updating,
                               is_internet=is_internet)

    elif page == 'info':
        uptime = subprocess.Popen("uptime", stdout=subprocess.PIPE, shell=True)
        (uptime_output, uptime_err) = uptime.communicate()
        uptime_status = uptime.wait()

        uname = subprocess.Popen("uname -a", stdout=subprocess.PIPE, shell=True)
        (uname_output, uname_err) = uname.communicate()
        uname_status = uname.wait()

        gpio_readall = subprocess.Popen("gpio readall", stdout=subprocess.PIPE, shell=True)
        (gpio_readall_output, gpio_readall_err) = gpio_readall.communicate()
        gpio_readall_status = gpio_readall.wait()

        df = subprocess.Popen("df", stdout=subprocess.PIPE, shell=True)
        (df_output, df_err) = df.communicate()
        df_status = df.wait()

        free = subprocess.Popen("free", stdout=subprocess.PIPE, shell=True)
        (free_output, free_err) = free.communicate()
        free_status = free.wait()

        return render_template('tools/info.html',
                               gpio_readall=gpio_readall_output,
                               df=df_output,
                               free=free_output,
                               uname=uname_output,
                               uptime=uptime_output)

    # Display relay usage
    elif page == 'usage':
        display_order_unsplit = flaskutils.db_retrieve_table(
            MYCODO_DB_PATH, DisplayOrder, first=True).relay
        if display_order_unsplit:
            display_order = display_order_unsplit.split(",")
        else:
            display_order = []
        misc = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Misc, first=True)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)

        # Calculate the number of seconds since the nth day of tyhe month
        # Enables usage/cost assessments to align with a power bill cycle
        now = datetime.date.today()
        past_month_seconds = 0
        day = misc.relay_stats_dayofmonth
        if 4 <= day <= 20 or 24 <= day <= 30:
            date_suffix = 'th'
        else:
            date_suffix = ['st', 'nd', 'rd'][day%10-1]
        if misc.relay_stats_dayofmonth == datetime.datetime.today().day:
            past_month_seconds = (now-now.replace(
                hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        elif misc.relay_stats_dayofmonth > datetime.datetime.today().day:
            first_day = now.replace(day=1)
            last_Month = first_day - datetime.timedelta(days=1)
            past_month = last_Month.replace(day=misc.relay_stats_dayofmonth)
            past_month_seconds = (now-past_month).total_seconds()       
        elif misc.relay_stats_dayofmonth < datetime.datetime.today().day:
            past_month = now.replace(day=misc.relay_stats_dayofmonth)
            past_month_seconds = (now-past_month).total_seconds()

        relay_each_duration = {}
        relay_sum_duration = dict.fromkeys(
            ['1d', '1w', '1m', '1m-date', '1y'], 0)
        relay_sum_kwh = dict.fromkeys(
            ['1d', '1w', '1m', '1m-date', '1y'], 0)
        for each_relay in relay:
            relay_each_duration[each_relay.id] = {}
            relay_each_duration[each_relay.id]['1d'] = flaskutils.sum_relay_usage(each_relay.id, 86400)/3600
            relay_each_duration[each_relay.id]['1w'] = flaskutils.sum_relay_usage(each_relay.id, 604800)/3600
            relay_each_duration[each_relay.id]['1m'] = flaskutils.sum_relay_usage(each_relay.id, 2629743)/3600
            relay_each_duration[each_relay.id]['1m-date'] = flaskutils.sum_relay_usage(each_relay.id, int(past_month_seconds))/3600
            relay_each_duration[each_relay.id]['1y'] = flaskutils.sum_relay_usage(each_relay.id, 31556926)/3600
            relay_sum_duration['1d'] += relay_each_duration[each_relay.id]['1d']
            relay_sum_duration['1w'] += relay_each_duration[each_relay.id]['1w']
            relay_sum_duration['1m'] += relay_each_duration[each_relay.id]['1m']
            relay_sum_duration['1m-date'] += relay_each_duration[each_relay.id]['1m-date']
            relay_sum_duration['1y'] += relay_each_duration[each_relay.id]['1y']
            relay_sum_kwh['1d'] += misc.relay_stats_volts*each_relay.amps*relay_each_duration[each_relay.id]['1d']/1000
            relay_sum_kwh['1w'] += misc.relay_stats_volts*each_relay.amps*relay_each_duration[each_relay.id]['1w']/1000
            relay_sum_kwh['1m'] += misc.relay_stats_volts*each_relay.amps*relay_each_duration[each_relay.id]['1m']/1000
            relay_sum_kwh['1m-date'] += misc.relay_stats_volts*each_relay.amps*relay_each_duration[each_relay.id]['1m']/1000
            relay_sum_kwh['1y'] += misc.relay_stats_volts*each_relay.amps*relay_each_duration[each_relay.id]['1y']/1000
        return render_template('tools/usage.html',
                               display_order=display_order,
                               misc=misc,
                               relay=relay,
                               relay_each_duration=relay_each_duration,
                               relay_sum_duration=relay_sum_duration,
                               relay_sum_kwh=relay_sum_kwh,
                               date_suffix=date_suffix)

    # Display log output
    elif page == 'logview':
        if session['user_group'] == 'guest':
            flash('Guests are not permitted to view logs.', 'error')
            return redirect('/')
        formLogView = flaskforms.LogView()
        log_output = None
        lines = 30
        logfile = ''
        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'logview':
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

                if os.path.isfile(logfile):
                    log = subprocess.Popen('tail -n '+str(lines)+' '+logfile, stdout=subprocess.PIPE, shell=True)
                    (log_output, log_err) = log.communicate()
                    log_status = log.wait()
                else:
                    log_output = 404
        return render_template('tools/logview.html',
                               formLogView=formLogView,
                               lines=lines,
                               logfile=logfile,
                               log_output=log_output)

    elif page == 'notes':
        return render_template('tools/notes.html')

    elif page == 'camera':
        formCamera = flaskforms.Camera()
        if 'start_x=1' not in open('/boot/config.txt').read():
            flash("Camera support doesn't appear to be enabled. Please enable it with 'sudo raspi-config'", "error")
            camera_enabled = False
        else:
            camera_enabled = True

        stream_locked = os.path.isfile(LOCK_FILE_STREAM)
        if stream_locked and not CameraStream().is_running():
            os.remove(LOCK_FILE_STREAM)
            stream_locked = False
        stream_locked = os.path.isfile(LOCK_FILE_STREAM)

        timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)
        if timelapse_locked and not os.path.isfile(FILE_TIMELAPSE_PARAM):
            os.remove(LOCK_FILE_TIMELAPSE)
        elif not timelapse_locked and os.path.isfile(FILE_TIMELAPSE_PARAM):
            os.remove(FILE_TIMELAPSE_PARAM)
        timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)

        if request.method == 'POST':
            if session['user_group'] == 'guest':
                flash('Guests are not permitted to use camera options.', 'error')
                return redirect('/camera')
            form_name = request.form['form-name']
            if form_name == 'camera':
                if formCamera.Still.data:
                    if not stream_locked or not timelapse_locked:
                        try:
                            # if CameraStream().is_running():
                            #     CameraStream().terminate()  # Stop camera stream to take a photo
                            #     time.sleep(2)
                            #     stream_locked = True  # Signal to enable camera stream
                            camera = flaskutils.db_retrieve_table(
                                MYCODO_DB_PATH, CameraStill, first=True)
                            camera_record(INSTALL_DIRECTORY, 'photo', camera)
                        except Exception as msg:
                            flash("Camera Error: {}".format(msg), "error")
                    else:
                        flash("Cannot capture still if timelapse or stream is "
                              "active. If they are not active, delete {} and {}.".format(
                              stream_locked, timelapse_locked), "error")

                elif formCamera.StartTimelapse.data:
                    if not stream_locked:
                        # Create lockfile and file with timelapse parameters
                        open(LOCK_FILE_TIMELAPSE, 'a')
                        now = time.time()
                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        uid_gid = pwd.getpwnam('mycodo').pw_uid
                        timelapse_data = [['start_time', timestamp],
                                          ['end_time', now+float(formCamera.TimelapseRunTime.data)],
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
                        flash("Cannot capture still if a stream is active. "
                              "If it is not active, delete {}.".format(
                              stream_locked), "error")
                        
                    # else:
                    #     CameraTimelapse().start_timelapse(
                    #         formCamera.TimelapseInterval.data,
                    #         formCamera.TimelapseRunTime.data)
                    #     open(LOCK_FILE_TIMELAPSE, 'a')
                    #     timelapse_locked = True
                    #     flash("timelapse started {} {}".format(
                    #         formCamera.TimelapseInterval.data,
                    #         formCamera.TimelapseRunTime.data),
                    #         "success")
                        
                elif formCamera.StopTimelapse.data:
                    try:
                        os.remove(FILE_TIMELAPSE_PARAM)
                        os.remove(LOCK_FILE_TIMELAPSE)
                    except:
                        pass

                    # try:
                    #     CameraTimelapse().terminate()
                    #     os.remove(LOCK_FILE_TIMELAPSE)
                    #     timelapse_locked = False
                    # except Exception as msg:
                    #     flash("Could not stop timelapse: {}".format(msg), "error")

                elif formCamera.StartStream.data:
                    if not timelapse_locked:
                        open(LOCK_FILE_STREAM, 'a')
                        stream_locked = True
                        stream = True
                    else:
                        flash("Cannot capture still if a timelapse is active. "
                              "If it is not active, delete {}.".format(
                              timelapse_locked), "error")

                elif formCamera.StopStream.data:
                    if CameraStream().is_running():
                        CameraStream().terminate()
                    if os.path.isfile(LOCK_FILE_STREAM):
                        os.remove(LOCK_FILE_STREAM)
                    stream_locked = False

        timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)
        if timelapse_locked and not os.path.isfile(FILE_TIMELAPSE_PARAM):
            os.remove(LOCK_FILE_TIMELAPSE)
        elif not timelapse_locked and os.path.isfile(FILE_TIMELAPSE_PARAM):
            os.remove(FILE_TIMELAPSE_PARAM)
        timelapse_locked = os.path.isfile(LOCK_FILE_TIMELAPSE)

        try:
            latest_still_img_fullpath = max(glob.iglob(INSTALL_DIRECTORY+'/camera-stills/*.jpg'), key=os.path.getmtime)
            ts = os.path.getmtime(latest_still_img_fullpath)
            latest_still_img_ts = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_still_img = os.path.basename(latest_still_img_fullpath)
        except:
            latest_still_img_ts = None
            latest_still_img = None

        try:
            latest_timelapse_img_fullpath = max(glob.iglob(INSTALL_DIRECTORY+'/camera-timelapse/*.jpg'), key=os.path.getmtime)
            ts = os.path.getmtime(latest_timelapse_img_fullpath)
            latest_timelapse_img_ts = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            latest_timelapse_img = os.path.basename(latest_timelapse_img_fullpath)
        except:
            latest_timelapse_img_ts = None
            latest_timelapse_img = None

        return render_template('pages/camera.html',
                               camera_enabled=camera_enabled,
                               formCamera=formCamera,
                               latest_still_img_ts=latest_still_img_ts,
                               latest_still_img=latest_still_img,
                               latest_timelapse_img_ts=latest_timelapse_img_ts,
                               latest_timelapse_img=latest_timelapse_img,
                               stream_locked=stream_locked,
                               timelapse_locked=timelapse_locked)

    elif page == 'help':
        return render_template('manual.html')

    else:
        return render_template('404.html'), 404

def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


@app.route('/method-data/<method_type>/<method_id>')
def method_data(method_type, method_id):
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return ('', 204)

    with session_scope(MYCODO_DB_PATH) as new_session:
        method = new_session.query(Method)
        new_session.expunge_all()
        new_session.close()

    method_key = method.filter(Method.method_id == method_id)
    method_key = method_key.filter(Method.method_order == 0).first()

    method = method.filter(Method.method_id == method_id)
    method = method.filter(Method.method_order > 0)
    method = method.filter(Method.relay_id == None)
    method = method.order_by(Method.method_order.asc()).all()

    method_list = []

    if method_key.method_type == "Date":
        for each_method in method:
            if each_method.end_setpoint == None:
                end_setpoint = each_method.start_setpoint
            else:
                end_setpoint = each_method.end_setpoint

            start_time = datetime.datetime.strptime(each_method.start_time, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.datetime.strptime(each_method.end_time, '%Y-%m-%d %H:%M:%S')

            is_dst = time.daylight and time.localtime().tm_isdst > 0
            utc_offset_ms = (time.altzone if is_dst else time.timezone)

            method_list.append([(int(start_time.strftime("%s"))-utc_offset_ms)*1000 , each_method.start_setpoint])
            method_list.append([(int(end_time.strftime("%s"))-utc_offset_ms)*1000, end_setpoint])
            method_list.append([(int(start_time.strftime("%s"))-utc_offset_ms)*1000 , None])

    if method_key.method_type == "Daily":
        for each_method in method:
            if each_method.end_setpoint == None:
                end_setpoint = each_method.start_setpoint
            else:
                end_setpoint = each_method.end_setpoint

            method_list.append([get_sec(each_method.start_time)*1000, each_method.start_setpoint])
            method_list.append([get_sec(each_method.end_time)*1000, end_setpoint])
            method_list.append([get_sec(each_method.start_time)*1000, None])

    elif method_key.method_type == "DailyBezier":
        points_x = 700
        seconds_in_day = 60*60*24
        P0 = (method_key.x0, method_key.y0)
        P1 = (method_key.x1, method_key.y1)
        P2 = (method_key.x2, method_key.y2)
        P3 = (method_key.x3, method_key.y3)
        print('TEST {} {} {} {}'.format(P0, P1, P2, P3), file=sys.stderr)
        for n in range(points_x):
            percent = n/float(points_x)
            second_of_day = percent*seconds_in_day
            y = bezier_curve_y_out(method_key.shift_angle, P0, P1, P2, P3, second_of_day)
            method_list.append([percent*seconds_in_day*1000, y])

    elif method_key.method_type == "DailySine":
        points_x = 700
        seconds_in_day = 60*60*24
        for n in range(points_x):
            percent = n/float(points_x)
            angle = n/float(points_x)*360
            y = sine_wave_y_out(method_key.amplitude, method_key.frequency,
                                method_key.shift_angle, method_key.shift_y,
                                angle)
            method_list.append([percent*seconds_in_day*1000, y])

    elif method_key.method_type == "Duration":
        first_entry = True
        start_duration = 0
        end_duration = 0
        for each_method in method:
            if each_method.end_setpoint == None:
                end_setpoint = each_method.start_setpoint
            else:
                end_setpoint = each_method.end_setpoint
            if first_entry:
                method_list.append([0 , each_method.start_setpoint])
                method_list.append([each_method.duration_sec, end_setpoint])
                start_duration += each_method.duration_sec
                first_entry = False
            else:
                end_duration = start_duration+each_method.duration_sec

                method_list.append([start_duration, each_method.start_setpoint])
                method_list.append([end_duration, end_setpoint])

                start_duration += each_method.duration_sec

    return jsonify(method_list)

    try:
        return jsonify(method)
    except:
        return ('', 204)


@app.route('/method', methods=('GET', 'POST'))
def method_list():
    if not logged_in():
        return redirect('/')

    formCreateMethod = flaskforms.CreateMethod()
    with session_scope(MYCODO_DB_PATH) as new_session:
        method = new_session.query(Method)
        new_session.expunge_all()
        new_session.close()
    method_all = method.filter(Method.method_order > 0)
    method_all = method.filter(Method.relay_id == None).all()
    method = method.filter(Method.method_order == 0).all()

    return render_template('pages/method-list.html',
                           method=method,
                           method_all=method_all,
                           formCreateMethod=formCreateMethod)


@app.route('/method-delete/<method_id>')
def method_delete(method_id):
    if not logged_in():
        return redirect('/')
    try:
        with session_scope(MYCODO_DB_PATH) as new_session:
            method = new_session.query(Method)
            method = method.filter(Method.method_id == method_id).delete()
    except Exception as except_msg:
        flash("Error while deleting Method: "
              "{}".format(except_msg), "error")
    # flaskutils.method_del(method_id)
    return redirect('/method')


@app.route('/method-build/<method_type>/<method_id>', methods=('GET', 'POST'))
def method_builder(method_type, method_id):
    if not logged_in():
        return redirect('/')

    if method_type in ['Date', 'Duration', 'Daily', 'DailySine', 'DailyBezier', '0']:
        formCreateMethod = flaskforms.CreateMethod()
        formAddMethod = flaskforms.AddMethod()
        formModMethod = flaskforms.ModMethod()

        # Create new method
        if method_type == '0':
            random_id = ''.join([random.choice(
                string.ascii_letters + string.digits) for n in xrange(8)])
            method_id = random_id
            method_type = formCreateMethod.method_type.data
            form_fail = flaskutils.method_create(formCreateMethod, method_id)
            if not form_fail:
                flash("New Method successfully created. It may now have time "
                      "points added.", "success")
                return redirect('/method-build/{}/{}'.format(
                    method_type, method_id))
            else:
                flash("Could not create method.", "error")

        with session_scope(MYCODO_DB_PATH) as new_session:
            method = new_session.query(Method)
            new_session.expunge_all()
            new_session.close()

        # The single table entry that holds the method type information
        method_key = method.filter(Method.method_id == method_id)
        method_key = method_key.filter(Method.method_order == 0).first()

        # The table entries with time, setpoint, and relay data, sorted by order
        method_list = method.filter(Method.method_order > 0)
        method_list = method_list.order_by(Method.method_order.asc()).all()

        last_end_time = ''
        last_setpoint = ''
        if method_type in ['Date', 'Daily']:
            last_method = method.filter(Method.method_id == method_key.method_id)
            last_method = last_method.filter(Method.method_order > 0)
            last_method = last_method.filter(Method.relay_id == None)
            last_method = last_method.order_by(Method.method_order.desc()).first()

            # Get last entry end time and setpoint to populate the form
            if last_method == None:
                last_end_time = ''
                last_setpoint = ''
            else:
                last_end_time = last_method.end_time
                if last_method.end_setpoint != None:
                    last_setpoint = last_method.end_setpoint
                else:
                    last_setpoint = last_method.start_setpoint

        # method = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Method)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addMethod':
                form_fail = flaskutils.method_add(formAddMethod, method)
            elif form_name in ['modMethod', 'renameMethod']:
                form_fail = flaskutils.method_mod(formModMethod, method)
            if (form_name in ['addMethod', 'modMethod', 'renameMethod'] and not form_fail):
                return redirect('/method-build/{}/{}'.format(
                    method_type, method_id))

        return render_template('pages/method-build.html',
                               method=method,
                               relay=relay,
                               method_key=method_key,
                               method_list=method_list,
                               method_id=method_id,
                               method_type=method_type,
                               last_end_time=last_end_time,
                               last_setpoint=last_setpoint,
                               formCreateMethod=formCreateMethod,
                               formAddMethod=formAddMethod,
                               formModMethod=formModMethod)

    return redirect('/method')


@app.route('/remote/<page>', methods=('GET', 'POST'))
def remote_admin(page):
    """Return pages for remote administraion"""
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return redirect('/')
    if session['user_group'] == 'guest':
        flash('Guests are not permitted to view the romote systems panel.', 'error')
        return redirect('/')

    remote_hosts = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Remote)
    display_order_unsplit = flaskutils.db_retrieve_table(
        MYCODO_DB_PATH, DisplayOrder, first=True).remote_host
    if display_order_unsplit:
        display_order = display_order_unsplit.split(",")
    else:
        display_order = []

    if page == 'setup':
        formSetup = flaskforms.RemoteSetup()
        host_auth = {}
        for each_host in remote_hosts:
            host_auth[each_host.host] = flaskutils.auth_credentials(each_host.host, each_host.username, each_host.password_hash)
        
        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'setup':
                if formSetup.add.data:
                    flaskutils.remote_host_add(formSetup, display_order)
            if form_name == 'mod_remote':
                if formSetup.delete.data:
                    flaskutils.remote_host_del(formSetup, display_order)
            return redirect('/remote/setup')

        return render_template('remote/setup.html',
                               formSetup=formSetup,
                               display_order=display_order,
                               remote_hosts=remote_hosts,
                               host_auth=host_auth)
    else:
        return render_template('404.html'), 404


@app.route('/camera/<img_type>/<filename>')
def camera_img(img_type, filename):
    """Return an image from stills or timelapses"""
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return redirect('/')

    still_path = INSTALL_DIRECTORY+'/camera-stills/'
    timelapse_path = INSTALL_DIRECTORY+'/camera-timelapse/'

    # Get a list of files in each directory
    if os.path.isdir(still_path):
        still_files = (file for file in os.listdir(still_path)
            if os.path.isfile(os.path.join(still_path, file)))
    else:
        still_files = []

    if os.path.isdir(timelapse_path):
        timelapse_files = (file for file in os.listdir(timelapse_path)
                if os.path.isfile(os.path.join(timelapse_path, file)))
    else:
        timelapse_files = []

    if img_type == 'still':
        # Ensure file exists in directory before serving it
        if filename in still_files:
            resp = make_response(open(still_path+filename).read())
            resp.content_type = "image/jpeg"
            return resp
    elif img_type == 'timelapse':
        if filename in timelapse_files:
            resp = make_response(open(timelapse_path+filename).read())
            resp.content_type = "image/jpeg"
            return resp
    return "Image not found"
    

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return redirect('/')

    return Response(gen(CameraStream()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# Settings pages: This will mostly be form submissions to modify the SQL database
@app.route('/settings/<page>', methods=('GET', 'POST'))
def settings(page):
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return redirect('/')

    # User management settings page
    elif page == 'users':
        if session['user_group'] == 'guest':
            flash('Guests are not permitted to view user settings.', 'error')
            return redirect('/settings')

        users = flaskutils.db_retrieve_table(USER_DB_PATH, Users)
        formAddUser = flaskforms.AddUser()
        formModUser = flaskforms.ModUser()
        formDelUser = flaskforms.DelUser()

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addUser':
                flaskutils.user_add(formAddUser)
            elif form_name == 'delUser':
                if flaskutils.user_del(formDelUser) == 'logout':
                    return redirect('/logout')
            elif form_name == 'modUser':
                if flaskutils.user_mod(formModUser) == 'logout':
                    return redirect('/logout')
            return redirect('/settings/users')

        return render_template('settings/users.html',
                               users=users,
                               formAddUser=formAddUser,
                               formModUser=formModUser,
                               formDelUser=formDelUser)

    # Alert email notifification settings
    elif page == 'alerts':
        if session['user_group'] == 'guest':
            flash('Guests are not permitted to view alert settings.', 'error')
            return redirect('/settings')

        smtp = flaskutils.db_retrieve_table(MYCODO_DB_PATH, SMTP)
        formEmailAlert = flaskforms.EmailAlert()
        if request.method == 'POST':
            form_name = request.form['form-name']
            # Update smtp settings table in mycodo SQL database
            if form_name == 'EmailAlert':
                flaskutils.settings_alert_mod(formEmailAlert)
            return redirect('/settings/alerts')

        return render_template('settings/alerts.html',
                               smtp=smtp,
                               formEmailAlert=formEmailAlert)

    # General settings
    elif page == 'general':
        misc = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Misc, first=True)
        formSettingsGeneral = flaskforms.SettingsGeneral()
        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'General':
                flaskutils.settings_general_mod(formSettingsGeneral)
            return redirect('/settings/general')

        return render_template('settings/general.html',
                               misc=misc,
                               formSettingsGeneral=formSettingsGeneral)

    # Camera settings
    elif page == 'camera':
        camera = flaskutils.db_retrieve_table(MYCODO_DB_PATH, CameraStill, first=True)
        formSettingsCamera = flaskforms.SettingsCamera()
        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'Camera':
                flaskutils.settings_camera_mod(formSettingsCamera)
            return redirect('/settings/camera')

        return render_template('settings/camera.html',
                               camera=camera,
                               formSettingsCamera=formSettingsCamera)

    # Display collected statistics
    elif page == 'statistics':
        statistics = return_stat_file_dict(STATS_CSV)
        return render_template('settings/statistics.html',
                               statistics=statistics)

    return render_template('settings/{}.html'.format(page))


@app.route('/login', methods=('GET', 'POST'))
def do_admin_login():
    # Check if the user is banned from logging in
    if flaskutils.banned_from_login():
        return redirect('/')

    # Authenticate with SQL database using form input
    form = flaskforms.Login()
    formNotice = flaskforms.InstallNotice()
    with session_scope(MYCODO_DB_PATH) as db_session:
        misc = db_session.query(Misc).first()
        dismiss_notification = misc.dismiss_notification
        stats_opt_out = misc.stats_opt_out

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'acknowledge':
            try:
                with session_scope(MYCODO_DB_PATH) as db_session:
                    mod_misc = db_session.query(Misc).first()
                    mod_misc.dismiss_notification = 1
                    db_session.commit()
            except Exception as except_msg:
                flash("Acknowledgement not saved: {}".format(except_msg), "error")
        elif form_name == 'login' and form.validate_on_submit():
            with session_scope(USER_DB_PATH) as new_session:
                user = new_session.query(Users).filter(Users.user_name == form.username.data).first()
                new_session.expunge_all()
                new_session.close()
            if not user:
                flaskutils.login_log(form.username.data, 'NA',
                    request.environ['REMOTE_ADDR'], 'NOUSER')
                flaskutils.failed_login()
            elif Users().check_password(form.password.data, user.user_password_hash) == user.user_password_hash:
                flaskutils.login_log(user.user_name, user.user_restriction,
                    request.environ['REMOTE_ADDR'], 'LOGIN')
                session['logged_in'] = True
                session['user_group'] = user.user_restriction
                session['user_name'] = user.user_name
                session['user_theme'] = user.user_theme
                if form.remember.data:
                    response = make_response(redirect('/'))
                    expire_date = datetime.datetime.now()
                    expire_date = expire_date + datetime.timedelta(days=90)
                    response.set_cookie('user_name', user.user_name, expires=expire_date)
                    response.set_cookie('user_pass_hash', user.user_password_hash, expires=expire_date)
                    return response
                return redirect('/')
            else:
                flaskutils.login_log(user.user_name, user.user_restriction,
                    request.environ['REMOTE_ADDR'], 'FAIL')
                flaskutils.failed_login()
        else:
            flaskutils.login_log(form.username.data, 'NA',
                request.environ['REMOTE_ADDR'], 'FAIL')
            flaskutils.failed_login()

        return redirect('/login')

    return render_template('login.html',
                           form=form,
                           formNotice=formNotice,
                           dismiss_notification=dismiss_notification,
                           stats_opt_out=stats_opt_out)


@app.route("/logout")
def logout():
    if session.get('user_name'):
        flaskutils.login_log(session['user_name'], session['user_group'],
        request.environ['REMOTE_ADDR'], 'LOGOUT')
    response = clear_cookie_auth()
    flash('Successfully logged out', 'success')
    return response


def logged_in():
    if (not session.get('logged_in') and
            not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return 0
    elif (session.get('logged_in') or
            (not session.get('logged_in') and
             flaskutils.authenticate_cookies(USER_DB_PATH, Users))):
        return 1


def clear_cookie_auth():
    response = make_response(redirect('/login'))
    session.clear()  # or session['logged_in'] = False
    response.set_cookie('user_name', '', expires=0)
    response.set_cookie('user_pass_hash', '', expires=0)
    return response


@app.route('/gpiostate')
def gpio_state():
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return ('', 204)

    relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
    gpio_state = {}
    GPIO.setmode(GPIO.BCM)
    for each_relay in relay:
        if 0 < each_relay.pin < 40:
            GPIO.setup(each_relay.pin, GPIO.OUT)
            if GPIO.input(each_relay.pin) == each_relay.trigger:
                gpio_state[each_relay.id] = 1
            else:
                gpio_state[each_relay.id] = 0
    return jsonify(gpio_state)


@app.route('/dl/<dl_type>/<path:filename>')
def download_file(dl_type, filename):
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return ('', 204)

    if dl_type == 'log':
        return send_from_directory(LOG_PATH, filename, as_attachment=True)
    return ('', 204)


# Return the most recent time and value from influxdb
@app.route('/last/<sensor_type>/<sensor_measure>/<sensor_id>/<sensor_period>')
def last_data(sensor_type, sensor_measure, sensor_id, sensor_period):
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return ('', 204)

    app.config['INFLUXDB_USER'] = INFLUXDB_USER
    app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
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
        time = raw_data['series'][0]['values'][number-1][0]
        value = raw_data['series'][0]['values'][number-1][1]
        # Convert date-time to epoch (potential bottleneck for data)
        dt =  date_parse(time)
        timestamp = calendar.timegm(dt.timetuple())*1000
        live_data = '[{},{}]'.format(timestamp, value)
        return Response(live_data, mimetype='text/json')
    except:
        return ('', 204)


# Return data from past_seconds until present from influxdb
@app.route('/past/<sensor_type>/<sensor_measure>/<sensor_id>/<past_seconds>')
@gzipped
def past_data(sensor_type, sensor_measure, sensor_id, past_seconds):
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return ('', 204)

    app.config['INFLUXDB_USER'] = INFLUXDB_USER
    app.config['INFLUXDB_PASSWORD'] = INFLUXDB_PASSWORD
    app.config['INFLUXDB_DATABASE'] = INFLUXDB_DATABASE
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
        return jsonify(raw_data['series'][0]['values'])
    except:
        return ('', 204)


# Return 'alive' if the daemon is running
@app.route('/daemonactive')
def daemon_active():
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return ('', 204)
    try:
        control = DaemonControl()
        return control.daemon_status()
    except:
        return '0'


@app.route('/systemctl/<action>')
def computer_command(action):
    """
    Execute one of a set of commands as root

    action sent, command executed
    shutdown, 'shutdown now -h'
    restart, 'shutdown now -r'
    """
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return ('', 204)
    try:
        control = DaemonControl()
        return control.system_control(action)
    except:
        return '0'


@app.route('/newremote/')
def newremote():
    user = request.args.get('user')
    passw = request.args.get('passw')
    with session_scope(USER_DB_PATH) as new_session:
        user = new_session.query(Users).filter(Users.user_name == user).first()
        new_session.expunge_all()
        new_session.close()
    if user:
        if Users().check_password(passw, user.user_password_hash) == user.user_password_hash:
            return jsonify(status=0, message="{}".format(user.user_password_hash))
    return jsonify(status=1, message="Unable to authenticate with user and password.")


@app.route('/auth/')
def data():
    user = request.args.get('user')
    pw_hash = request.args.get('pw_hash')
    with session_scope(USER_DB_PATH) as new_session:
        user = new_session.query(Users).filter(Users.user_name == user).first()
        new_session.expunge_all()
        new_session.close()
    if (user and 
            user.user_restriction == 'admin' and
            pw_hash == user.user_password_hash):
        return "0"
    return "1"


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


# Variables to send with every page request
@app.context_processor
def inject_mycodo_version():
    try:
        control = DaemonControl()
        daemon_status = control.daemon_status()
    except:
        daemon_status = '0'
    
    with session_scope(MYCODO_DB_PATH) as db_session:
        misc = db_session.query(Misc).first()
        return dict(daemon_status=daemon_status,
                    mycodo_version=MYCODO_VERSION,
                    host=socket.gethostname(),
                    hide_alert_success=misc.hide_alert_success,
                    hide_alert_info=misc.hide_alert_info,
                    hide_alert_warning=misc.hide_alert_warning)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mycodo Flask HTTP server.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    options = parser.add_argument_group('Options')
    options.add_argument('-d', '--debug', action='store_true',
                              help="Run Flask with debug=True (Default: False)")
    options.add_argument('-s', '--ssl', action='store_true',
                              help="Run Flask without SSL (Default: Enabled)")

    args = parser.parse_args()

    if args.debug:
        debug=True
    else:
        debug=False

    if args.ssl:
        app.run(host='0.0.0.0', port=80, debug=debug)
    else:
        # locate ssl certificates, if not executing Flask script from the script's directory
        file_path = os.path.abspath(__file__)
        dir_path = os.path.dirname(file_path)
        cert = os.path.join(dir_path, "frontend/ssl_certs/cert.pem")
        privkey = os.path.join(dir_path, "frontend/ssl_certs/privkey.pem")
        # chain = os.path.join(dir_path, "frontend/ssl_certs/chain.pem")
        context = (cert, privkey)
        app.run(host='0.0.0.0', port=443, ssl_context=context, debug=debug)
