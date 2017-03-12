#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo configuration settings
#
import os
import collections

from datetime import timedelta

MYCODO_VERSION = '5.0.0'
ALEMBIC_VERSION = ''

LANGUAGES = {
    'en': 'English',
    'fr': 'Français (French)',
    'es': 'Español (Spanish)',
    'ko': '한국어 (Korean)'
}

# Install path, the parent directory this script resides
INSTALL_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/..'

# Measurements for each sensor/device
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

# Unit abbreviation for each measurement
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

# Sensors and description
SENSORS = [
    ('RPi', 'Raspberry Pi: CPU Temperature'),
    ('RPiCPULoad', 'Raspberry Pi: CPU Load'),
    ('RPiFreeSpace', 'Raspberry Pi: Free Disk Space'),
    ('ADS1x15', 'Analog-to-Digital Converter: ADS1x15'),
    ('MCP342x', 'Analog-to-Digital Converter: MCP342x'),
    ('EDGE', 'Edge Detection: Simple Switch'),
    ('K30', 'CO2: K30'),
    ('TSL2561', 'Luminance: TSL2561'),
    ('CHIRP', 'Moisture: Chirp'),
    ('BME280', 'Pressure/Temperature/Humidity: BME 280'),
    ('BMP', 'Pressure/Temperature: BMP 180/085'),
    ('DS18B20', 'Temperature: DS18B20'),
    ('TMP006', 'Temperature (Contactless): TMP 006/007'),
    ('ATLAS_PT1000', 'Temperature: Atlas Scientific, PT-1000'),
    ('AM2315', 'Temperature/Humidity: AM2315'),
    ('DHT11', 'Temperature/Humidity: DHT11'),
    ('DHT22', 'Temperature/Humidity: DHT22'),
    ('HTU21D', 'Temperature/Humidity: HTU21D'),
    ('SHT1x_7x', 'Temperature/Humidity: SHT 10/11/15/71/75'),
    ('SHT2x', 'Temperature/Humidity: SHT 21/25')
]

# Devices that have a default address that doesn't change
# Used to determine whether or not to present the option to change address
DEVICES_DEFAULT_LOCATION = [
    'AM2315', 'ATLAS_PT1000', 'BMP', 'HTU21D', 'K30', 'RPi', 'RPiCPULoad'
]

# Conditional actions
CONDITIONAL_ACTIONS = collections.OrderedDict([
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
])

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

# Web UI themes
THEMES = [
    ('cerulean', 'Cerulean'),
    ('cosmo', 'Cosmo'),
    ('cyborg', 'Cyborg'),
    ('darkly', 'Darkly'),
    ('flatly', 'Flatly'),
    ('journal', 'Journal'),
    ('lumen', 'Lumen'),
    ('paper', 'Paper'),
    ('readable', 'Readable'),
    ('sadstone', 'Sadstone'),
    ('simplex', 'Simplex'),
    ('slate', 'Slate'),
    ('spacelab', 'Spacelab'),
    ('sun', 'Sun'),
    ('superhearo', 'Superhearo'),
    ('united', 'United'),
    ('yeti', 'Yeti')
]

# SQLite3 databases that stores users and settings
DATABASE_PATH = os.path.join(INSTALL_DIRECTORY, 'databases')
SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# File paths/logging
USAGE_REPORTS_PATH = os.path.join(INSTALL_DIRECTORY, 'relay_usage_reports')
LOG_PATH = '/var/log/mycodo'  # Where generated logs are stored
LOGIN_LOG_FILE = os.path.join(LOG_PATH, 'login.log')
DAEMON_LOG_FILE = os.path.join(LOG_PATH, 'mycodo.log')
UPGRADE_LOG_FILE = os.path.join(LOG_PATH, 'mycodoupgrade.log')
RESTORE_LOG_FILE = os.path.join(LOG_PATH, 'mycodorestore.log')
HTTP_LOG_FILE = '/var/log/apache2/error.log'
LOCK_PATH = '/var/lock'
DAEMON_PID_FILE = os.path.join(LOCK_PATH, 'mycodo.pid')

# Camera
CAMERAS = {
    'Raspberry Pi': 'picamera',
    'USB Camera': 'opencv'
}
PATH_CAMERAS = os.path.join(INSTALL_DIRECTORY, 'cameras')
LOCK_FILE_STREAM = os.path.join(DATABASE_PATH, 'mycodo-camera-stream.pid')

# Influx sensor/device measurement database
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USER = 'mycodo'
INFLUXDB_PASSWORD = 'mmdu77sj3nIoiajjs'
INFLUXDB_DATABASE = 'mycodo_db'

# Anonymous statistics
STATS_INTERVAL = 86400
STATS_HOST = 'fungi.kylegabriel.com'
STATS_PORT = 8086
STATS_USER = 'mycodo_stats'
STATS_PASSWORD = 'Io8Nasr5JJDdhPOj32222'
STATS_DATABASE = 'mycodo_stats'
STATS_CSV = os.path.join(DATABASE_PATH, 'statistics.csv')
ID_FILE = os.path.join(DATABASE_PATH, 'statistics.id')

# Login restrictions
LOGIN_ATTEMPTS = 5
LOGIN_BAN_SECONDS = 600  # 10 minutes

# Relay amp restrictions. If the sum of current draws of all relay currently
# on, plus the one directed to turn on, surpasses this maximum, the relay
# will be prevented from turning on. Prevents exceeding current rating of
# the electrical system.
MAX_AMPS = 15


class ProdConfig(object):
    """ Production Configuration """
    SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
    MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQL_DATABASE_MYCODO
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REMEMBER_COOKIE_DURATION = timedelta(days=90)

    # Ensure file containing the Flask secret_key exists
    FLASK_SECRET_KEY_PATH = os.path.join(DATABASE_PATH, 'flask_secret_key')
    if not os.path.isfile(FLASK_SECRET_KEY_PATH):
        with open(FLASK_SECRET_KEY_PATH, 'w') as file:
            file.write(os.urandom(24))
    SECRET_KEY = open(FLASK_SECRET_KEY_PATH, 'rb').read()


class TestConfig(object):
    """ Testing Configuration """
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # in-memory db only. tests drop the tables after they run

    SECRET_KEY = '1234'
    TESTING = True
    DEBUG = True
