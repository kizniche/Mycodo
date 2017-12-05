# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo configuration settings
#
import os
import collections
from datetime import timedelta
from flask_babel import lazy_gettext

MYCODO_VERSION = '5.4.14'
ALEMBIC_VERSION = 'b9712d4ec64e'

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
    'MYCODO_RAM': ['disk_space'],
    'ADS1x15': ['voltage'],
    'AM2315': ['dewpoint', 'humidity', 'temperature'],
    'ATLAS_PH_I2C': ['ph'],
    'ATLAS_PH_UART': ['ph'],
    'ATLAS_PT1000_I2C': ['temperature'],
    'ATLAS_PT1000_UART': ['temperature'],
    'BH1750': ['lux'],
    'BME280': ['altitude', 'dewpoint', 'humidity', 'pressure', 'temperature'],
    'BMP': ['altitude', 'pressure', 'temperature'],
    'BMP180': ['altitude', 'pressure', 'temperature'],
    'BMP280': ['altitude', 'pressure', 'temperature'],
    'CHIRP': ['lux', 'moisture', 'temperature'],
    'DHT11': ['dewpoint', 'humidity', 'temperature'],
    'DHT22': ['dewpoint', 'humidity', 'temperature'],
    'DS18B20': ['temperature'],
    'EDGE': ['edge'],
    'HTU21D': ['dewpoint', 'humidity', 'temperature'],
    'K30_UART': ['co2'],
    'MH_Z16_I2C': ['co2'],
    'MH_Z16_UART': ['co2'],
    'MH_Z19_UART': ['co2'],
    'MCP342x': ['voltage'],
    'RPi': ['temperature'],
    'RPiCPULoad': ['cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m'],
    'RPiFreeSpace': ['disk_space'],
    'SHT1x_7x': ['dewpoint', 'humidity', 'temperature'],
    'SHT2x': ['dewpoint', 'humidity', 'temperature'],
    'SIGNAL_PWM': ['frequency', 'pulse_width', 'duty_cycle'],
    'SIGNAL_RPM': ['rpm'],
    'TMP006': ['temperature_object', 'temperature_die'],
    'TSL2561': ['lux'],
    'TSL2591': ['lux']
}

# Unit abbreviation for each measurement
MEASUREMENT_UNITS = {
    'altitude': {
        'name': lazy_gettext(u'Altitude'),
        'meas': 'altitude', 'unit': u'm'},
    'co2': {
        'name': lazy_gettext(u'CO2'),
        'meas': 'co2', 'unit': u'ppmv'},
    'dewpoint': {
        'name': lazy_gettext(u'Dewpoint'),
        'meas': 'temperature', 'unit': u'°C'},
    'cpu_load_1m': {
        'name': lazy_gettext(u'CPU Load'),
        'meas': 'cpu_load', 'unit': u'1 min'},
    'cpu_load_5m': {
        'name': lazy_gettext(u'CPU Load'),
        'meas': 'cpu_load', 'unit': u'5 min'},
    'cpu_load_15m': {
        'name': lazy_gettext(u'CPU Load'),
        'meas': 'cpu_load', 'unit': u'15 min'},
    'disk_space': {
        'name': lazy_gettext(u'Disk'),
        'meas': 'disk_space', 'unit': u'MB'},
    'duration_sec': {
        'name': lazy_gettext(u'Duration'),
        'meas': 'duration_sec', 'unit': u'sec'},
    'duty_cycle': {
        'name': lazy_gettext(u'Duty Cycle'),
        'meas': 'duty_cycle', 'unit': u'%'},
    'edge': {
        'name': lazy_gettext(u'Edge'),
        'meas': 'edge', 'unit': u'edge'},
    'frequency': {
        'name': lazy_gettext(u'Frequency'),
        'meas': 'frequency', 'unit': u'Hz'},
    'humidity': {
        'name': lazy_gettext(u'Humidity'),
        'meas': 'humidity', 'unit': u'%'},
    'lux': {
        'name': lazy_gettext(u'Light'),
        'meas': 'lux', 'unit': u'lx'},
    'moisture': {
        'name': lazy_gettext(u'Moisture'),
        'meas': 'moisture', 'unit': u'moisture'},
    'ph': {
        'name': lazy_gettext(u'pH'),
        'meas': 'ph', 'unit': u'pH'},
    'pid_output': {
        'name': lazy_gettext(u'PID Output'),
        'meas': 'pid_output', 'unit': u'sec'},
    'pressure': {
        'name': lazy_gettext(u'Pressure'),
        'meas': 'pressure', 'unit': u'Pa'},
    'pulse_width': {
        'name': lazy_gettext(u'Pulse Width'),
        'meas': 'pulse_width', 'unit': u'µs'},
    'rpm': {
        'name': lazy_gettext(u'Revolutions Per Minute'),
        'meas': 'rpm', 'unit': u'rpm'},
    'setpoint': {
        'name': lazy_gettext(u'Setpoint'),
        'meas': 'setpoint', 'unit': u''},
    'temperature': {
        'name': lazy_gettext(u'Temperature'),
        'meas': 'temperature', 'unit': u'°C'},
    'temperature_object': {
        'name': lazy_gettext(u'Temperature (Obj)'),
        'meas': 'temperature', 'unit': u'°C'},
    'temperature_die': {
        'name': lazy_gettext(u'Temperature (Die)'),
        'meas': 'temperature', 'unit': u'°C'},
    'voltage': {
        'name': lazy_gettext(u'Voltage'),
        'meas': 'voltage', 'unit': u'volts'}
}

# Inputs and description
INPUTS = [
    ('RPi', 'Raspberry Pi: CPU Temperature'),
    ('RPiCPULoad', 'Raspberry Pi: CPU Load'),
    ('RPiFreeSpace', 'Raspberry Pi: Free Disk Space'),
    ('SIGNAL_PWM', 'Raspberry Pi: Pulse-Width Modulation (PWM)'),
    ('SIGNAL_RPM', 'Raspberry Pi: Revolutions Per Minute (RPM)'),
    ('MYCODO_RAM', 'Mycodo: Daemon RAM Usage'),
    ('LinuxCommand', 'Linux Command'),
    ('ADS1x15', 'Analog-to-Digital Converter: ADS1x15'),
    ('MCP342x', 'Analog-to-Digital Converter: MCP342x'),
    ('EDGE', 'Edge Detection: Simple Switch'),
    ('K30_UART', 'CO2: K30 (UART)'),
    ('MH_Z16_I2C', 'CO2: MH-Z16 (I2C)'),
    ('MH_Z16_UART', 'CO2: MH-Z16 (UART)'),
    ('MH_Z19_UART', 'CO2: MH-Z19 (UART)'),
    ('BH1750', 'Luminance: BH1750'),
    ('TSL2561', 'Luminance: TSL2561'),
    ('TSL2591', 'Luminance: TSL2591'),
    ('CHIRP', 'Moisture: Chirp'),
    ('ATLAS_PH_I2C', 'pH: Atlas Scientific (I2C)'),
    ('ATLAS_PH_UART', 'pH: Atlas Scientific (UART)'),
    ('BME280', 'Pressure/Temperature/Humidity: BME 280'),
    ('BMP180', 'Pressure/Temperature: BMP 180/085'),
    ('BMP280', 'Pressure/Temperature: BMP 280'),
    ('DS18B20', 'Temperature: DS18B20'),
    ('ATLAS_PT1000_I2C', 'Temperature: Atlas Scientific PT-1000 (I2C)'),
    ('ATLAS_PT1000_UART', 'Temperature: Atlas Scientific PT-1000 (UART)'),
    ('TMP006', 'Temperature (Contactless): TMP 006/007'),
    ('AM2315', 'Temperature/Humidity: AM2315'),
    ('DHT11', 'Temperature/Humidity: DHT11'),
    ('DHT22', 'Temperature/Humidity: DHT22'),
    ('HTU21D', 'Temperature/Humidity: HTU21D'),
    ('SHT1x_7x', 'Temperature/Humidity: SHT 10/11/15/71/75'),
    ('SHT2x', 'Temperature/Humidity: SHT 21/25')
]

MATHS = [
    ('average', 'Average')
]

# Sensors and description
CALIBRATION_DEVICES = [
    ('calibration_atlas_ph', 'Atlas Scientific pH sensor')
]

# Devices that have a default address that doesn't change
# Used to determine whether or not to present the option to change address
DEVICES_DEFAULT_LOCATION = [
    'AM2315',
    'ATLAS_PH_UART',
    'ATLAS_PT1000_UART',
    'BMP',
    'BMP180',
    'HTU21D',
    'RPi',
    'RPiCPULoad',
    'TSL2591',
    'mycodo_ram'
]

# Devices that use I2C to communicate
LIST_DEVICES_I2C = [
    'ADS1x15',
    'AM2315',
    'ATLAS_PH_I2C',
    'ATLAS_PT1000_I2C',
    'BH1750',
    'BME280',
    'BMP',
    'BMP180',
    'BMP280',
    'CHIRP',
    'HTU21D',
    'MH_Z16_I2C',
    'MCP342x',
    'SHT2x',
    'TMP006',
    'TSL2561',
    'TSL2591'
]

# Conditional actions
CONDITIONAL_ACTIONS = collections.OrderedDict([
    ('relay', lazy_gettext(u'Output')),
    ('command', lazy_gettext(u'Command')),
    ('activate_pid', lazy_gettext(u'Activate PID')),
    ('deactivate_pid', lazy_gettext(u'Deactivate PID')),
    ('email', lazy_gettext(u'Email')),
    ('flash_lcd', lazy_gettext(u'Flash LCD')),
    ('photo', lazy_gettext(u'Photo')),
    ('photo_email', lazy_gettext(u'Email Photo')),
    ('video', lazy_gettext(u'Video')),
    ('video_email', lazy_gettext(u'Email Video'))
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

THEMES_DARK = ['cyborg', 'darkly', 'slate', 'sun', 'superhero']

# SQLite3 databases that stores users and settings
DATABASE_PATH = os.path.join(INSTALL_DIRECTORY, 'databases')
SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# File paths/logging
USAGE_REPORTS_PATH = os.path.join(INSTALL_DIRECTORY, 'relay_usage_reports')
UPGRADE_INIT_FILE = os.path.join(INSTALL_DIRECTORY, '.upgrade')
BACKUP_PATH = '/var/Mycodo-backups'  # Where Mycodo backups are stored
LOG_PATH = '/var/log/mycodo'  # Where generated logs are stored
LOGIN_LOG_FILE = os.path.join(LOG_PATH, 'login.log')
DAEMON_LOG_FILE = os.path.join(LOG_PATH, 'mycodo.log')
KEEPUP_LOG_FILE = os.path.join(LOG_PATH, 'mycodokeepup.log')
BACKUP_LOG_FILE = os.path.join(LOG_PATH, 'mycodobackup.log')
UPGRADE_LOG_FILE = os.path.join(LOG_PATH, 'mycodoupgrade.log')
RESTORE_LOG_FILE = os.path.join(LOG_PATH, 'mycodorestore.log')
HTTP_LOG_FILE = '/var/log/apache2/error.log'

# Lock files
LOCK_PATH = '/var/lock'
ATLAS_PH_LOCK_FILE = os.path.join(LOCK_PATH, 'sensor-atlas-ph.pid')
DAEMON_PID_FILE = os.path.join(LOCK_PATH, 'mycodo.pid')
LOCK_FILE_STREAM = os.path.join(LOCK_PATH, 'mycodo-camera-stream.pid')

# Remote admin
STORED_SSL_CERTIFICATE_PATH = os.path.join(
    INSTALL_DIRECTORY, 'mycodo/mycodo_flask/ssl_certs/remote_admin')

# Camera
CAMERA_LIBRARIES = [
    'picamera',
    'fswebcam',
    'opencv'
]
PATH_CAMERAS = os.path.join(INSTALL_DIRECTORY, 'cameras')

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

# Check for upgrade every 2 days (if enabled)
UPGRADE_CHECK_INTERVAL = 172800


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
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RATELIMIT_ENABLED = False
    SECRET_KEY = '1234'
    TESTING = True
    DEBUG = True
