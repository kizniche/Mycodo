# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo settings
#
import binascii
import collections
from datetime import timedelta

import os
from flask_babel import lazy_gettext

MYCODO_VERSION = '5.6.0'
ALEMBIC_VERSION = 'ba31c9ef6eab'

#  FORCE_UPGRADE_MASTER
#  Set True to enable upgrading to the master branch of the Mycodo repository.
#  Set False to enable upgrading to the latest Release version (default).
FORCE_UPGRADE_MASTER = False

LANGUAGES = {
    'en': 'English',
    'fr': 'Français (French)',
    'es': 'Español (Spanish)'
}


# Devices and descriptions (for Data page)
DEVICES = [
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
    ('ADS1x15', 'Analog-to-Digital Converter: ADS1x15 (I2C)'),
    ('MCP3008', 'Analog-to-Digital Converter: MCP3008 (Serial)'),
    ('MCP342x', 'Analog-to-Digital Converter: MCP342x (I2C)'),
    ('K30_UART', 'CO2: K30 (Serial)'),
    ('MH_Z16_I2C', 'CO2: MH-Z16 (I2C)'),
    ('MH_Z16_UART', 'CO2: MH-Z16 (Serial)'),
    ('MH_Z19_UART', 'CO2: MH-Z19 (Serial)'),
    ('BH1750', 'Luminance: BH1750 (I2C)'),
    ('TSL2561', 'Luminance: TSL2561 (I2C)'),
    ('TSL2591', 'Luminance: TSL2591 (I2C)'),
    ('CHIRP', 'Moisture: Chirp (I2C)'),
    ('ATLAS_PH_I2C', 'pH: Atlas Scientific (I2C)'),
    ('ATLAS_PH_UART', 'pH: Atlas Scientific (Serial)'),
    ('BME280', 'Pressure/Temperature/Humidity: BME 280 (I2C)'),
    ('BMP180', 'Pressure/Temperature: BMP 180/085 (I2C)'),
    ('BMP280', 'Pressure/Temperature: BMP 280 (I2C)'),
    ('DS18B20', 'Temperature: DS18B20 (1-Wire)'),
    ('ATLAS_PT1000_I2C', 'Temperature: Atlas Scientific PT-1000 (I2C)'),
    ('ATLAS_PT1000_UART', 'Temperature: Atlas Scientific PT-1000 (Serial)'),
    ('TMP006', 'Temperature (Contactless): TMP 006/007 (I2C)'),
    ('AM2315', 'Temperature/Humidity: AM2315 (I2C)'),
    ('DHT11', 'Temperature/Humidity: DHT11 (GPIO)'),
    ('DHT22', 'Temperature/Humidity: DHT22 (GPIO)'),
    ('HTU21D', 'Temperature/Humidity: HTU21D (I2C)'),
    ('SHT1x_7x', 'Temperature/Humidity: SHT 10/11/15/71/75'),
    ('SHT2x', 'Temperature/Humidity: SHT 21/25 (I2C)')
]

# Device information
DEVICE_INFO = {
    'MYCODO_RAM': {
        'dependencies': [],
        'measure': ['disk_space']},
    'ADS1x15': {
        'dependencies': ['Adafruit_ADS1x15'],
        'measure': ['voltage']},
    'AM2315': {
        'dependencies': ['quick2wire'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'ATLAS_PH_I2C': {
        'dependencies': [],
        'measure': ['ph']},
    'ATLAS_PH_UART': {
        'dependencies': ['serial'],
        'measure': ['ph']},
    'ATLAS_PT1000_I2C': {
        'dependencies': [],
        'measure': ['temperature']},
    'ATLAS_PT1000_UART': {
        'dependencies': ['serial'],
        'measure': ['temperature']},
    'BH1750': {
        'dependencies': ['smbus'],
        'measure': ['lux']},
    'BME280': {
        'dependencies': ['Adafruit_BME280'],
        'measure': ['altitude', 'dewpoint', 'humidity', 'pressure', 'temperature']},
    'BMP': {  # TODO: Remove in next major version. BMP180 replaced this name
        'dependencies': ['Adafruit_BMP'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'BMP180': {
        'dependencies': ['Adafruit_BMP'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'BMP280': {
        'dependencies': ['Adafruit_GPIO'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'CHIRP': {
        'dependencies': ['smbus'],
        'measure': ['lux', 'moisture', 'temperature']},
    'DHT11': {
        'dependencies': ['pigpio'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'DHT22': {
        'dependencies': ['pigpio'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'DS18B20': {
        'dependencies': ['w1thermsensor'],
        'measure': ['temperature']},
    'EDGE': {
        'dependencies': ['RPi.GPIO'],
        'measure': ['edge']},
    'GPIO_STATE': {
        'dependencies': ['RPi.GPIO'],
        'measure': ['gpio_state']},
    'HTU21D': {
        'dependencies': ['pigpio'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'K30_UART': {
        'dependencies': ['serial'],
        'measure': ['co2']},
    'MH_Z16_I2C': {
        'dependencies': ['smbus'],
        'measure': ['co2']},
    'MH_Z16_UART': {
        'dependencies': ['serial'],
        'measure': ['co2']},
    'MH_Z19_UART': {
        'dependencies': ['serial'],
        'measure': ['co2']},
    'MCP3008': {
        'dependencies': ['Adafruit_MCP3008'],
        'measure': ['voltage']},
    'MCP342x': {
        'dependencies': ['MCP342x'],
        'measure': ['voltage']},
    'RPi': {
        'dependencies': [],
        'measure': ['temperature']},
    'RPiCPULoad': {
        'dependencies': [],
        'measure': ['cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m']},
    'RPiFreeSpace': {
        'dependencies': [],
        'measure': ['disk_space']},
    'SERVER_PING': {
        'dependencies': [],
        'measure': ['boolean']},
    'SERVER_PORT_OPEN': {
        'dependencies': [],
        'measure': ['boolean']},
    'SHT1x_7x': {
        'dependencies': ['sht_sensor'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'SHT2x': {
        'dependencies': ['smbus'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'SIGNAL_PWM': {
        'dependencies': ['pigpio'],
        'measure': ['frequency','pulse_width', 'duty_cycle']},
    'SIGNAL_RPM': {
        'dependencies': ['pigpio'],
        'measure': ['rpm']},
    'TMP006': {
        'dependencies': ['Adafruit_TMP'],
        'measure': ['temperature_object', 'temperature_die']},
    'TSL2561': {
        'dependencies': ['tsl2561'],
        'measure': ['lux']},
    'TSL2591': {
        'dependencies': ['tsl2591'],
        'measure': ['lux']}
}

# Measurement information
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
    'pid_value': {
        'name': lazy_gettext('PID Values'),
        'meas': 'pid_value', 'unit': ''},
    'pid_p_value': {
        'name': lazy_gettext('PID P-Value'),
        'meas': 'pid_value', 'unit': ''},
    'pid_i_value': {
        'name': lazy_gettext('PID I-Value'),
        'meas': 'pid_value', 'unit': ''},
    'pid_d_value': {
        'name': lazy_gettext('PID D-Value'),
        'meas': 'pid_value', 'unit': ''},
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

# Math controllers
MATHS = [
    ('average', 'Average (Multiple Measurements)'),
    ('average_single', 'Average (Single Measurement)'),
    ('difference', 'Difference'),
    ('equation', 'Equation'),
    ('median', 'Median'),
    ('maximum', 'Maximum'),
    ('minimum', 'Minimum'),
    ('humidity', 'Humidity'),
    ('verification', 'Verification')
]

# Calibration
CALIBRATION_DEVICES = [
    ('calibration_atlas_ph', 'Atlas Scientific pH sensor')
]

# Measurements that must be stured in influxdb as an integer instead of a float
MEASUREMENT_INTEGERS = [
    'pressure'
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

# Analog-to-Digital Converters
LIST_DEVICES_ADC = [
    'ADS1x15',
    'MCP3008',
    'MCP342x'
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

# Devices that use SPI to communicate
LIST_DEVICES_SPI = [
    'MCP3008'
]

# Devices that use serial to communicate
LIST_DEVICES_SERIAL = [
    'ATLAS_PH_UART',
    'ATLAS_PT1000_UART',
    'K30_UART',
    'MH_Z16_UART',
    'MH_Z19_UART'
]

# Devices that use 1-wire to communicate
LIST_DEVICES_ONE_WIRE = [
    'DS18B20'
]

# Devices that communicate to the Pi itself or operating system
LIST_DEVICES_INTERNAL_PI = [
    'MYCODO_RAM',
    'RPi',
    'RPiCPULoad',
    'RPiFreeSpace',
    'SERVER_PING',
    'SERVER_PORT_OPEN',
    'SIGNAL_PWM',
    'SIGNAL_RPM'
]

# Conditional actions
# TODO: Some have been disabled until they can be properly tested
CONDITIONAL_ACTIONS = collections.OrderedDict([
    ('output', lazy_gettext('Output')),
    ('command', lazy_gettext('Command')),
    ('activate_pid', lazy_gettext('Activate PID')),
    ('deactivate_pid', lazy_gettext('Deactivate PID')),
    ('resume_pid', lazy_gettext('Resume PID')),
    ('pause_pid', lazy_gettext('Pause PID')),
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
