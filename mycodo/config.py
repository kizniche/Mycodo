#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo configuration settings
#
#  Copyright (C) 2015  Kyle T. Gabriel
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

import os

MYCODO_VERSION = '4.0.25'

INSTALL_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/..'

LOCK_PATH = '/var/lock'
DAEMON_PID_FILE = os.path.join(LOCK_PATH, 'mycodo.pid')

LOG_PATH = '/var/log/mycodo' # Where generated logs are stored

LOGIN_LOG_FILE = os.path.join(LOG_PATH, 'login.log')
DAEMON_LOG_FILE = os.path.join(LOG_PATH, 'mycodo.log')
HTTP_LOG_FILE = '/var/log/apache2/error.log'
UPDATE_LOG_FILE = os.path.join(LOG_PATH, 'mycodoupdate.log')
RESTORE_LOG_FILE = os.path.join(LOG_PATH, 'mycodorestore.log')

# Logs that are on the tempfs and are written to every sensor read
# DAEMON_LOG_FILE_TMP = os.path.join(LOG_PATH, "daemon-tmp.log")
# SENSOR_T_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-t-tmp.log")
# SENSOR_HT_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-ht-tmp.log")
# SENSOR_CO2_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-co2-tmp.log")
# SENSOR_PRESS_LOG_FILE_TMP = os.path.join(LOG_PATH, "sensor-press-tmp.log")
# RELAY_LOG_FILE_TMP = os.path.join(LOG_PATH, "relay-tmp.log")

# Logs that are periodically concatenated (every 6 hours) to the SD card
# DAEMON_LOG_FILE = os.path.join(LOG_PATH, "daemon.log")
# SENSOR_T_LOG_FILE = os.path.join(LOG_PATH, "sensor-t.log")
# SENSOR_HT_LOG_FILE = os.path.join(LOG_PATH, "sensor-ht.log")
# SENSOR_CO2_LOG_FILE = os.path.join(LOG_PATH, "sensor-co2.log")
# SENSOR_PRESS_LOG_FILE = os.path.join(LOG_PATH, "sensor-press.log")
# RELAY_LOG_FILE = os.path.join(LOG_PATH, "relay.log")

DATABASE_PATH = os.path.join(INSTALL_DIRECTORY, 'databases')
SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
SQL_DATABASE_USER = os.path.join(DATABASE_PATH, 'users.db')
SQL_DATABASE_NOTE = os.path.join(DATABASE_PATH, 'notes.db')
MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
USER_DB_PATH = 'sqlite:///' + SQL_DATABASE_USER

# Influxdb
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USER = 'mycodo'
INFLUXDB_PASSWORD = 'mmdu77sj3nIoiajjs'
INFLUXDB_DATABASE = 'mycodo_db'

# Anonymous usage statistics
STATS_CSV = os.path.join(DATABASE_PATH, 'statistics.csv')
ID_FILE = os.path.join(DATABASE_PATH, 'statistics.id')

# Camera
LOCK_FILE_STREAM = os.path.join(DATABASE_PATH, 'mycodo-camera-stream.pid')
LOCK_FILE_TIMELAPSE = os.path.join(DATABASE_PATH, 'mycodo-camera-timelapse.pid')
FILE_TIMELAPSE_PARAM = os.path.join(DATABASE_PATH, 'timelapse_parameters.csv')

# Anonymous statistics
STATS_INTERVAL = 86400  # 1 day
STATS_HOST = 'fungi.kylegabriel.com'
STATS_PORT = 8086
STATS_USER = 'mycodo_stats'
STATS_PASSWORD = 'Io8Nasr5JJDdhPOj32222'
STATS_DATABASE = 'mycodo_stats'

# Login
LOGIN_ATTEMPTS = 5
LOGIN_BAN_TIME_SECONDS = 600 # 10 minutes

# Relay
MAX_AMPS = 15


class ProdConfig(object):
    """ Production Configuration """
    SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
    SQL_DATABASE_USER = os.path.join(DATABASE_PATH, 'users.db')
    SQL_DATABASE_NOTE = os.path.join(DATABASE_PATH, 'notes.db')

    MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
    USER_DB_PATH = 'sqlite:///' + SQL_DATABASE_USER


class TestConfig(object):
    """ Testing Configuration """
    SQL_DATABASE_USER = ''  # defined later when tests run
    SQL_DATABASE_MYCODO = '' # defined later when tests run
    SQL_DATABASE_NOTE = '' # defined later when tests run
    MYCODO_DB_PATH = ''  # defined later when tests run
    NOTES_DB_PATH = ''  # defined later when tests run
    USER_DB_PATH = ''  # defined later when tests run

    TESTING = True
    DEBUG = True
