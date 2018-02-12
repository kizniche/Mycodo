# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo settings
#
import binascii
import collections
from datetime import timedelta

import os
from flask_babel import lazy_gettext

MYCODO_VERSION = '5.5.20'
ALEMBIC_VERSION = 'def4bf9c6f84'

#  FORCE_UPGRADE_MASTER
#  Set True to enable upgrading to the master branch of the Mycodo repository.
#  Set False to enable upgrading to the latest Release version (default).
FORCE_UPGRADE_MASTER = False

LANGUAGES = {
    'en': 'English',
    'fr': 'Français (French)',
    'es': 'Español (Spanish)'
}

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
    'GPIO_STATE': ['gpio_state'],
    'HTU21D': ['dewpoint', 'humidity', 'temperature'],
    'K30_UART': ['co2'],
    'MH_Z16_I2C': ['co2'],
    'MH_Z16_UART': ['co2'],
    'MH_Z19_UART': ['co2'],
    'MCP342x': ['voltage'],
    'RPi': ['temperature'],
    'RPiCPULoad': ['cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m'],
    'RPiFreeSpace': ['disk_space'],
    'SERVER_PING': ['boolean'],
    'SERVER_PORT_OPEN': ['boolean'],
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
        'name': lazy_gettext('Altitude'),
        'meas': 'altitude', 'unit': 'm'},
    'boolean': {
        'name': lazy_gettext('Boolean'),
        'meas': 'boolean', 'unit': ''},
    'co2': {
        'name': lazy_gettext('CO2'),
        'meas': 'co2', 'unit': 'ppmv'},
    'dewpoint': {
        'name': lazy_gettext('Dewpoint'),
        'meas': 'temperature', 'unit': '°C'},
    'cpu_load': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load', 'unit': ''},
    'cpu_load_1m': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load', 'unit': '1 min'},
    'cpu_load_5m': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load', 'unit': '5 min'},
    'cpu_load_15m': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load', 'unit': '15 min'},
    'disk_space': {
        'name': lazy_gettext('Disk'),
        'meas': 'disk_space', 'unit': 'MB'},
    'duration_sec': {
        'name': lazy_gettext('Duration'),
        'meas': 'duration_sec', 'unit': 'sec'},
    'duty_cycle': {
        'name': lazy_gettext('Duty Cycle'),
        'meas': 'duty_cycle', 'unit': '%'},
    'edge': {
        'name': lazy_gettext('GPIO Edge'),
        'meas': 'edge', 'unit': ''},
    'frequency': {
        'name': lazy_gettext('Frequency'),
        'meas': 'frequency', 'unit': 'Hz'},
    'gpio_state': {
        'name': lazy_gettext('GPIO State'),
        'meas': 'gpio_state', 'unit': ''},
    'humidity': {
        'name': lazy_gettext('Humidity'),
        'meas': 'humidity', 'unit': '%'},
    'humidity_ratio': {
        'name': lazy_gettext('Humidity Ratio'),
        'meas': 'humidity_ratio', 'unit': 'kg/kg'},
    'lux': {
        'name': lazy_gettext('Light'),
        'meas': 'lux', 'unit': 'lx'},
    'moisture': {
        'name': lazy_gettext('Moisture'),
        'meas': 'moisture', 'unit': 'moisture'},
    'ph': {
        'name': lazy_gettext('pH'),
        'meas': 'ph', 'unit': 'pH'},
    'pid_output': {
        'name': lazy_gettext('PID Output'),
        'meas': 'pid_output', 'unit': 'sec'},
    'pressure': {
        'name': lazy_gettext('Pressure'),
        'meas': 'pressure', 'unit': 'Pa'},
    'pulse_width': {
        'name': lazy_gettext('Pulse Width'),
        'meas': 'pulse_width', 'unit': 'µs'},
    'rpm': {
        'name': lazy_gettext('Revolutions Per Minute'),
        'meas': 'rpm', 'unit': 'rpm'},
    'setpoint': {
        'name': lazy_gettext('Setpoint'),
        'meas': 'setpoint', 'unit': ''},
    'setpoint_band_min': {
        'name': lazy_gettext('Band Min'),
        'meas': 'setpoint_band_min', 'unit': ''},
    'setpoint_band_max': {
        'name': lazy_gettext('Band Max'),
        'meas': 'setpoint_band_max', 'unit': ''},
    'specific_enthalpy': {
        'name': lazy_gettext('Specific Enthalpy'),
        'meas': 'specific_enthalpy', 'unit': 'kJ/kg'},
    'specific_volume': {
        'name': lazy_gettext('Specific Volume'),
        'meas': 'specific_volume', 'unit': 'm^3/kg'},
    'temperature': {
        'name': lazy_gettext('Temperature'),
        'meas': 'temperature', 'unit': '°C'},
    'temperature_object': {
        'name': lazy_gettext('Temperature (Obj)'),
        'meas': 'temperature', 'unit': '°C'},
    'temperature_die': {
        'name': lazy_gettext('Temperature (Die)'),
        'meas': 'temperature', 'unit': '°C'},
    'voltage': {
        'name': lazy_gettext('Voltage'),
        'meas': 'voltage', 'unit': 'volts'}
}

# Inputs and description
INPUTS = [
    ('RPi', 'Raspberry Pi: CPU Temperature'),
    ('RPiCPULoad', 'Raspberry Pi: CPU Load'),
    ('RPiFreeSpace', 'Raspberry Pi: Free Disk Space'),
    ('GPIO_STATE', 'Raspberry Pi GPIO: State Detection'),
    ('EDGE', 'Raspberry Pi GPIO: Edge Detection'),
    ('SIGNAL_PWM', 'Raspberry Pi GPIO: Pulse-Width Modulation (PWM)'),
    ('SIGNAL_RPM', 'Raspberry Pi GPIO: Revolutions Per Minute (RPM)'),
    ('MYCODO_RAM', 'Mycodo: Daemon RAM Usage'),
    ('LinuxCommand', 'Linux Command'),
    ('SERVER_PING', 'Server Ping'),
    ('SERVER_PORT_OPEN', 'Server Port Open'),
    ('ADS1x15', 'Analog-to-Digital Converter: ADS1x15'),
    ('MCP342x', 'Analog-to-Digital Converter: MCP342x'),
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
    ('average', 'Average'),
    ('difference', 'Difference'),
    ('equation', 'Equation'),
    ('median', 'Median'),
    ('maximum', 'Maximum'),
    ('minimum', 'Minimum'),
    ('humidity', 'Humidity'),
    ('verification', 'Verification')
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
# TODO: Some have been disabled until they can be properly tested
CONDITIONAL_ACTIONS = collections.OrderedDict([
    ('output', lazy_gettext('Output')),
    ('command', lazy_gettext('Command')),
    ('activate_pid', lazy_gettext('Activate PID')),
    ('deactivate_pid', lazy_gettext('Deactivate PID')),
    ('email', lazy_gettext('Email')),
    ('flash_lcd_off', lazy_gettext('Flash LCD Off')),
    ('flash_lcd_on', lazy_gettext('Flash LCD On')),
    ('lcd_backlight_off', lazy_gettext('LCD Backlight Off')),
    ('lcd_backlight_on', lazy_gettext('LCD Backlight On')),
    ('photo', lazy_gettext('Photo')),
    # ('photo_email', lazy_gettext('Email Photo')),
    # ('video', lazy_gettext('Video')),
    # ('video_email', lazy_gettext('Email Video'))
])

# User Roles
USER_ROLES = [
    dict(id=1, name='Admin',
         edit_settings=True, edit_controllers=True, edit_users=True,
         view_settings=True, view_camera=True, view_stats=True, view_logs=True),
    dict(id=2, name='Editor',
         edit_settings=True, edit_controllers=True, edit_users=False,
         view_settings=True, view_camera=True, view_stats=True, view_logs=True),
    dict(id=3, name='Monitor',
         edit_settings=False, edit_controllers=False, edit_users=False,
         view_settings=True, view_camera=True, view_stats=True, view_logs=True),
    dict(id=4, name='Guest',
         edit_settings=False, edit_controllers=False, edit_users=False,
         view_settings=False, view_camera=False, view_stats=False, view_logs=False)
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

# Install path, the parent directory this script resides
INSTALL_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/..'

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
HTTP_ACCESS_LOG_FILE = '/var/log/nginx/access.log'
HTTP_ERROR_LOG_FILE = '/var/log/nginx/error.log'

# Lock files
LOCK_PATH = '/var/lock'
ATLAS_PH_LOCK_FILE = os.path.join(LOCK_PATH, 'sensor-atlas-ph.pid')
FRONTEND_PID_FILE = os.path.join(LOCK_PATH, 'mycodoflask.pid')
DAEMON_PID_FILE = os.path.join(LOCK_PATH, 'mycodo.pid')
LOCK_FILE_STREAM = os.path.join(LOCK_PATH, 'mycodo-camera-stream.pid')

# Remote admin
STORED_SSL_CERTIFICATE_PATH = os.path.join(
    INSTALL_DIRECTORY, 'mycodo/mycodo_flask/ssl_certs/remote_admin')

# Camera
CAMERA_LIBRARIES = [
    'picamera',
    'fswebcam'
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
        secret_key = binascii.hexlify(os.urandom(32)).decode()
        with open(FLASK_SECRET_KEY_PATH, 'w') as file:
            file.write(secret_key)
    SECRET_KEY = open(FLASK_SECRET_KEY_PATH, 'rb').read()


class TestConfig(object):
    """ Testing Configuration """
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # in-memory db only. tests drop the tables after they run
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RATELIMIT_ENABLED = False
    SECRET_KEY = '1234'
    TESTING = True
    DEBUG = True
