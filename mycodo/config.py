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
import collections

MYCODO_VERSION = '5.0.0'
ALEMBIC_VERSION = ''

LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français'
}

# Install path, the parent directory this script resides
INSTALL_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/..'

# Sensor/device information
MEASUREMENTS = {
    'ADS1x15': ['voltage'],
    'AM2315': ['dewpoint', 'humidity', 'temperature'],
    'ATLAS_PT1000': ['temperature'],
    'BME280': ['altitude', 'dewpoint', 'humidity', 'pressure', 'temperature'],
    'BMP': ['temperature'],
    'CHIRP': ['lux', 'moisture', 'temperature'],
    'DHT11': ['dewpoint', 'humidity', 'temperature'],
    'DHT22': ['dewpoint', 'humidity', 'temperature'],
    'DS18B20': ['temperature'],
    'EDGE': ['edge'],
    'HTU21D': ['dewpoint', 'humidity', 'temperature'],
    'K30': ['co2'],
    'MCP342x': ['voltage'],
    'RPi': ['temperature'],
    'RPiCPULoad': ['cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m'],
    'RPiFreeSpace': ['free_space'],
    'SHT1x_7x': ['dewpoint', 'humidity', 'temperature'],
    'SHT2x': ['dewpoint', 'humidity', 'temperature'],
    'TMP006': ['temperature_object', 'temperature_die'],
    'TSL2561': ['lux']
}
# Devices that have a default address that doesn't change
DEVICES_DEFAULT_LOCATION = [
    'AM2315', 'ATLAS_PT1000', 'BMP', 'HTU21D', 'K30', 'RPi', 'RPiCPULoad'
]
MEASUREMENT_UNITS = {
    'altitude': 'm',
    'co2': 'ppmv',
    'dewpoint': 'C',
    'cpu_load_1m': '',
    'cpu_load_5m': '',
    'cpu_load_15m': '',
    'duration_sec': 'sec',
    'edge': 'edge',
    'free_space': 'MB',
    'humidity': '%',
    'lux': 'lx',
    'moisture': 'moisture',
    'pressure': 'Pa',
    'temperature': 'C',
    'temperature_object': 'C',
    'temperature_die': 'C',
    'voltage': 'volts'
}
# Conditional actions
CONDITIONAL_ACTIONS = collections.OrderedDict(
    [
        ('relay', 'Relay'),
        ('command', 'Command'),
        ('activate_pid', 'Activate PID'),
        ('deactivate_pid', 'Deactivate PID'),
        ('email', 'Email'),
        ('flash_lcd', 'Flash LCD'),
        ('photo', 'Photo'),
        ('photo_email', 'Email Photo'),
        ('video', 'Video'),
        ('video_email', 'Email Video')
    ]
)


# User Roles
USER_ROLES = [
    dict(id=1, name='Admin',
         edit_settings=True, edit_controllers=True, edit_users=True,
         view_settings=True, view_camera=True, view_stats=True,
         view_logs=True),
    dict(id=2, name='Editor',
         edit_settings=True, edit_controllers=True, edit_users=False,
         view_settings=True, view_camera=True, view_stats=True,
         view_logs=True),
    dict(id=3, name='Monitor',
         edit_settings=False, edit_controllers=False, edit_users=False,
         view_settings=True, view_camera=True, view_stats=True,
         view_logs=True),
    dict(id=4, name='Guest',
         edit_settings=False, edit_controllers=False, edit_users=False,
         view_settings=False, view_camera=False, view_stats=False,
         view_logs=False)
]

# SQLite3 databases that stores users and settings
DATABASE_PATH = os.path.join(INSTALL_DIRECTORY, 'databases')
SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# Lock file paths
LOCK_PATH = '/var/lock'
DAEMON_PID_FILE = os.path.join(LOCK_PATH, 'mycodo.pid')

# Logging
LOG_PATH = '/var/log/mycodo'  # Where generated logs are stored
LOGIN_LOG_FILE = os.path.join(LOG_PATH, 'login.log')
DAEMON_LOG_FILE = os.path.join(LOG_PATH, 'mycodo.log')
UPGRADE_LOG_FILE = os.path.join(LOG_PATH, 'mycodoupgrade.log')
RESTORE_LOG_FILE = os.path.join(LOG_PATH, 'mycodorestore.log')
HTTP_LOG_FILE = '/var/log/apache2/error.log'

# Camera
PATH_CAMERA_STILL = os.path.join(INSTALL_DIRECTORY, 'camera-stills')
PATH_CAMERA_TIMELAPSE = os.path.join(INSTALL_DIRECTORY, 'camera-timelapse')
CAMERAS_SUPPORTED = {
    'Raspberry Pi': 'picamera',
    'USB Camera': 'opencv'
}
LOCK_FILE_STREAM = os.path.join(DATABASE_PATH, 'mycodo-camera-stream.pid')

# Influx sensor/device measurement database
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USER = 'mycodo'
INFLUXDB_PASSWORD = 'mmdu77sj3nIoiajjs'
INFLUXDB_DATABASE = 'mycodo_db'

# Anonymous usage statistics files
STATS_CSV = os.path.join(DATABASE_PATH, 'statistics.csv')
ID_FILE = os.path.join(DATABASE_PATH, 'statistics.id')

# Anonymous statistics
STATS_INTERVAL = 86400  # 1 day
STATS_HOST = 'fungi.kylegabriel.com'
STATS_PORT = 8086
STATS_USER = 'mycodo_stats'
STATS_PASSWORD = 'Io8Nasr5JJDdhPOj32222'
STATS_DATABASE = 'mycodo_stats'

# Login
LOGIN_ATTEMPTS = 5
LOGIN_BAN_SECONDS = 600  # 10 minutes

# Relay
MAX_AMPS = 15


class ProdConfig(object):
    """ Production Configuration """
    SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
    MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQL_DATABASE_MYCODO
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(object):
    """ Testing Configuration """
    SQL_DATABASE_MYCODO = ''  # defined later when tests run
    MYCODO_DB_PATH = ''  # defined later when tests run

    TESTING = True
    DEBUG = True
