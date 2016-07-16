#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# views.py - mycodo_flask flask views
#

import argparse
import calendar
import datetime
import glob
import logging
import os
import random
import socket
import sqlalchemy
import subprocess
import time
import RPi.GPIO as GPIO
from collections import OrderedDict
from dateutil.parser import parse as date_parse
from flask import Flask, flash, make_response, redirect, render_template, request, send_from_directory, session, g, jsonify, Response
from flask_influxdb import InfluxDB
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm import sessionmaker

import flaskforms
import flaskutils
from databases.utils import session_scope
from databases.users_db.models import Users
from databases.mycodo_db.models import DisplayOrder
from databases.mycodo_db.models import Graph
from databases.mycodo_db.models import LCD
from databases.mycodo_db.models import Log
from databases.mycodo_db.models import Misc
from databases.mycodo_db.models import PID
from databases.mycodo_db.models import PIDSetpoints
from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import RelayConditional
from databases.mycodo_db.models import Remote
from databases.mycodo_db.models import Sensor
from databases.mycodo_db.models import SensorConditional
from databases.mycodo_db.models import SMTP
from databases.mycodo_db.models import Timer
from daemonutils import camera_record, return_stat_file_dict, email
from devices.camera_pi import CameraStream
from devices.camera_pi import CameraTimelapse
from mycodo_client import DaemonControl

from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import INSTALL_DIRECTORY
from config import MYCODO_VERSION
from config import SQL_DATABASE_USER
from config import SQL_DATABASE_MYCODO
from config import LOG_PATH
from config import LOGIN_LOG_FILE
from config import DAEMON_LOG_FILE
from config import HTTP_LOG_FILE
from config import UPDATE_LOG_FILE
from config import RESTORE_LOG_FILE

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
USER_DB_PATH = 'sqlite:///' + SQL_DATABASE_USER

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend/static')
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend/templates')

app = Flask(__name__, static_folder=static_dir, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)
app.jinja_env.add_extension('jinja2.ext.do')  # Global values in jinja

influx_db = InfluxDB(app)


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
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        logout()
        return redirect('/login')
    return redirect('/live')


@app.route('/<page>', methods=('GET', 'POST'))
def page(page):
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
        return redirect('/')

    # Default landing page
    if page == 'live':
        display_order_sensor_sorted = []
        pid = flaskutils.db_retrieve_table(MYCODO_DB_PATH, PID)
        relay = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Relay)
        sensor = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Sensor)
        timer = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Timer)
        # Sort PID tracking by start time, earlest to latest
        with session_scope(MYCODO_DB_PATH) as new_session:
            pidsetpoints = new_session.query(PIDSetpoints).order_by(PIDSetpoints.start_time.asc()).all()
            new_session.expunge_all()
            new_session.close()

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

        return render_template('pages/live.html',
                               pid=pid,
                               pidsetpoints=pidsetpoints,
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
        formActivatePID = flaskforms.ActivatePID()
        formAddPID = flaskforms.AddPID()
        formAddPIDSetpoint = flaskforms.AddPIDsetpoint()
        formModPIDSetpoint = flaskforms.ModPIDsetpoint()
        formDeactivatePID = flaskforms.DeactivatePID()
        formDelPID = flaskforms.DelPID()
        formModPID = flaskforms.ModPID()
        formOrderPID = flaskforms.OrderPID()

        # Sort by start time earlest to latest
        with session_scope(MYCODO_DB_PATH) as new_session:
            pidsetpoints = new_session.query(PIDSetpoints).order_by(PIDSetpoints.start_time.asc()).all()
            new_session.expunge_all()
            new_session.close()

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addPID':
                flaskutils.pid_add(formAddPID, display_order)
            elif form_name == 'modPID':
                flaskutils.pid_mod(formModPID)
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
                               pids=pids,
                               pidsetpoints=pidsetpoints,
                               relay=relay,
                               sensor=sensor,
                               displayOrder=display_order,
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
        formBackup = flaskforms.Backup()
        internet = True
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
                               internet=internet,
                               backups_sorted=backup_dirs)


    elif page == 'update':
        if not flaskutils.internet():
            flash("Update functionality is disabled because an internet "
                  "connection was unable to be detected.", "error")
            return render_template('settings/update.html',
                                   internet=False)
        internet = True
        updating = 0
        update_available = False
        backup_directories = []
        list_only_commits = []
        restore_commits_extended = []
        commits_extended_messages = []
        formBackup = flaskforms.Backup()
        formUpdate = flaskforms.Update()

        flaskutils.cmd_output("git fetch origin")
        current_commit, _, _ = flaskutils.cmd_output("git rev-parse --short HEAD")
        commits_behind, _, _ = flaskutils.cmd_output("git log --oneline | head -n 1")
        commits_behind_list = commits_behind.split('\n')
        commits_ahead, commits_ahead_err, _ = flaskutils.cmd_output("git log --oneline master...origin/master")
        commits_ahead_list = commits_ahead.split('\n')
        if commits_ahead and commits_ahead_err is None:
            update_available = True

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'update':
                if formUpdate.update.data:
                    if update_available:
                        subprocess.Popen(INSTALL_DIRECTORY + '/mycodo/scripts/mycodo_wrapper upgrade >> /var/log/mycodo/mycodoupdate.log 2>&1', shell=True)
                        flash("Upgrade started. The daemon will be "
                              "stopped during the upgrade. Give the "
                              "process a minute or two to complete "
                              "before doing anything. When the update "
                              "has successfully finished, the daemon "
                              "status indicator at the top left will "
                              "turn from red to green.", "success")
                    else:
                        flash("You cannot update if an update is not available", "error")

        try:
            with open(INSTALL_DIRECTORY + '/.updating') as f:
                updating = int(f.read(1))
        except IOError:
            with open(INSTALL_DIRECTORY + '/.updating', 'w') as f:
                f.write('0')
            updating = 0

        return render_template('settings/update.html',
                               formBackup=formBackup,
                               formUpdate=formUpdate,
                               current_commit=current_commit,
                               commits_ahead=commits_ahead_list,
                               commits_behind=commits_behind_list,
                               update_available=update_available,
                               updating=updating,
                               internet=internet)

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
        lock_file_stream = '/var/lock/mycodo-camera-stream.lock'
        lock_file_timelapse = '/var/lock/mycodo-camera-timelapse.lock'

        if 'start_x=1' not in open('/boot/config.txt').read():
            flash("Camera support doesn't appear to be enabled. Please enable it with 'sudo raspi-config'", "error")
            camera_enabled = False
        else:
            camera_enabled = True

        stream_locked = os.path.isfile(lock_file_stream)
        if stream_locked and not CameraStream().is_running():
            os.remove('/var/lock/mycodo-camera-stream.lock')
            stream_locked = False

        timelapse_locked = os.path.isfile(lock_file_timelapse)
        if timelapse_locked and not CameraTimelapse().is_running():
            os.remove('/var/lock/mycodo-camera-timelapse.lock')
            timelapse_locked = False

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'camera':
                if formCamera.Still.data:
                    try:
                        # if CameraStream().is_running():
                        #     CameraStream().terminate()  # Stop camera stream to take a photo
                        #     time.sleep(2)
                        #     stream_locked = True  # Signal to enable camera stream
                        camera_record('photo')
                    except Exception as msg:
                        flash("Camera Error: {}".format(msg), "error")
                elif formCamera.StartTimelapse.data:
                    CameraTimelapse().start_timelapse(
                        formCamera.TimelapseInterval.data,
                        formCamera.TimelapseRunTime.data)
                    open('/var/lock/mycodo-camera-timelapse.lock', 'a')
                    timelapse_locked = True
                    flash("timelapse started {} {}".format(formCamera.TimelapseInterval.data, formCamera.TimelapseRunTime.data), "success")
                elif formCamera.StopTimelapse.data:
                    CameraTimelapse().terminate()
                    os.remove('/var/lock/mycodo-camera-timelapse.lock')
                    timelapse_locked = False
                elif formCamera.StartStream.data:
                    pass
                    # open(lock_file_stream, 'a')
                    # stream_locked = True
                    # stream = True
                elif formCamera.StopStream.data:
                    pass
                    # if CameraStream().is_running():
                    #     CameraStream().terminate()
                    # if os.path.isfile(lock_file_stream):
                    #     os.remove(lock_file_stream)
                    # stream_locked = False
        try:
            latest_still_img_fullpath = max(glob.iglob(INSTALL_DIRECTORY+'/camera-stills/*.jpg'), key=os.path.getctime)
            ts = os.path.getmtime(latest_still_img_fullpath)
            latest_still_img_ts = datetime.datetime.fromtimestamp(ts)
            latest_still_img = os.path.basename(latest_still_img_fullpath)
        except:
            latest_still_img_ts = None
            latest_still_img = None

        return render_template('pages/camera.html',
                               camera_enabled=camera_enabled,
                               formCamera=formCamera,
                               latest_still_img_ts=latest_still_img_ts,
                               latest_still_img=latest_still_img,
                               stream_locked=stream_locked,
                               timelapse_locked=timelapse_locked)

    elif page == 'help':
        return render_template('manual.html')

    else:
        return render_template('404.html'), 404


@app.route('/remote/<page>', methods=('GET', 'POST'))
def remote_admin(page):
    """Return pages for remote administraion"""
    if (not session.get('logged_in') and
        not flaskutils.authenticate_cookies(USER_DB_PATH, Users)):
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

    if img_type == 'still':
        resp = make_response(open(INSTALL_DIRECTORY+'/camera-stills/'+filename).read())
        resp.content_type = "image/jpeg"
        return resp
    elif img_type == 'timestamp':
        resp = flask.make_response(open(INSTALL_DIRECTORY+'/camera-timelapse/'+filename).read())
        resp.content_type = "image/jpeg"
        return resp
    else:
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
        users = flaskutils.db_retrieve_table(USER_DB_PATH, Users)
        formAddUser = flaskforms.AddUser()
        formModUser = flaskforms.ModUser()
        formDelUser = flaskforms.DelUser()

        if request.method == 'POST':
            form_name = request.form['form-name']
            if form_name == 'addUser':
                flaskutils.user_add(formAddUser)
            elif form_name == 'delUser':
                flaskutils.user_del(formDelUser)
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
        misc = flaskutils.db_retrieve_table(MYCODO_DB_PATH, Misc)
        formSettingsGeneral = flaskforms.SettingsGeneral()
        if request.method == 'POST':
            form_name = request.form['form-name']
            # Update smtp settings table in mycodo SQL database
            if form_name == 'General':
                flaskutils.settings_general_mod(formSettingsGeneral)
            return redirect('/settings/general')

        return render_template('settings/general.html',
                               misc=misc,
                               formSettingsGeneral=formSettingsGeneral)

    # Display collected statistics
    elif page == 'statistics':
        statistics = return_stat_file_dict()
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
                    expire_date = expire_date + datetime.timedelta(days=30)
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
    response = make_response(redirect('/login'))
    flaskutils.login_log(session['user_name'], session['user_group'],
        request.environ['REMOTE_ADDR'], 'LOGOUT')
    session.clear()  # or session['logged_in'] = False
    response.set_cookie('user_name', '', expires=0)
    response.set_cookie('user_pass_hash', '', expires=0)
    flash('Successfully logged out', "success")
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
    try:
        control = DaemonControl()
        return control.daemon_status()
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


@app.errorhandler(500)
def handle_error(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    return render_template('500.html'), 500
    # return jsonify(error=str(e)), code


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
