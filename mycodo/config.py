# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo settings
#
import binascii
from datetime import timedelta

import os
from flask_babel import lazy_gettext

MYCODO_VERSION = '6.3.9'
ALEMBIC_VERSION = '1421f1a02f25'

#  FORCE_UPGRADE_MASTER
#  Set True to enable upgrading to the master branch of the Mycodo repository.
#  Set False to enable upgrading to the latest Release version (default).
#  Do not use this feature unless you know what you're doing or have been
#  instructed to do so, as it can really mess up your system.
FORCE_UPGRADE_MASTER = False

# Final release for each major version number
# Used to determine proper upgrade page to display
FINAL_RELEASES = ['5.7.3']

LANGUAGES = {
    'en': 'English',
    'de': 'Deutsche (German)',
    'es': 'Español (Spanish)',
    'fr': 'Français (French)',
    'it': 'Italiano (Italian)',
    'pt': 'Português (Portuguese)',
    'ru': 'русский язык (Russian)',
    'zh': '中文 (Chinese)'
}

# Math controllers
MATHS = [
    ('average', 'Average (Multiple Inputs)'),
    ('average_single', 'Average (Single Input)'),
    ('difference', 'Difference'),
    ('equation', 'Equation'),
    ('median', 'Median'),
    ('maximum', 'Maximum'),
    ('minimum', 'Minimum'),
    ('humidity', 'Humidity (Wet/Dry-Bulb)'),
    ('verification', 'Verification')
]

# Math info
MATH_INFO = {
    'average': {
        'name': 'Average (Multi)',
        'dependencies_module': [],
        'measure': []},
    'average_single': {
        'name': 'Average (Single)',
        'dependencies_module': [],
        'measure': []},
    'difference': {
        'name': 'Difference',
        'dependencies_module': [],
        'measure': []},
    'equation': {
        'name': 'Equation',
        'dependencies_module': [],
        'measure': []},
    'median': {
        'name': 'Median',
        'dependencies_module': [],
        'measure': []},
    'maximum': {
        'name': 'Maximum',
        'dependencies_module': [],
        'measure': []},
    'minimum': {
        'name': 'Minimum',
        'dependencies_module': [],
        'measure': []},
    'humidity': {
        'name': 'Humidity (Wet-Bulb)',
        'dependencies_module': [],
        'measure': ['humidity', 'humidity_ratio', 'specific_enthalpy', 'specific_volume']},
    'verification': {
        'name': 'Verification',
        'dependencies_module': [],
        'measure': []}
}

# Methods
METHODS = [
    ('Date', 'Time/Date'),
    ('Duration', 'Duration'),
    ('Daily', 'Daily (Time-Based)'),
    ('DailySine', 'Daily (Sine Wave)'),
    ('DailyBezier', 'Daily (Bezier Curve)')
]

# Method info
METHOD_INFO = {
    'DailyBezier': {
        'name': 'DailyBezier',
        'dependencies_module': [('apt', 'python3-numpy', 'python3-numpy')]}
}

# Math controllers
OUTPUTS = [
    ('wired', 'GPIO (On/Off)'),
    ('pwm', 'GPIO (PWM)'),
    ('command', 'Command (On/Off)'),
    ('command_pwm', 'Command (PWM)'),
    ('wireless_433MHz_pi_switch', 'Wireless (433MHz)')
]

# Outputs
OUTPUT_INFO = {
    'wired': {
        'name': 'GPIO (On/Off)',
        'dependencies_module': [],
        'measure': []},
    'pwm': {
        'name': 'GPIO (PWM)',
        'dependencies_module': [],
        'measure': []},
    'wireless_433MHz_pi_switch': {
        'name': 'Wireless (433MHz)',
        'dependencies_module': [
            ('pip-pypi', 'rpi_rf', 'rpi_rf')
        ],
        'measure': []},
    'command': {
        'name': 'Command (On/Off)',
        'dependencies_module': [],
        'measure': []},
    'command_pwm': {
        'name': 'Command (PWM)',
        'dependencies_module': [],
        'measure': []},
}

# Calibration
CALIBRATION_INFO = {
    'CALIBRATE_DS_TYPE': {
        'name': 'DS-Type Sensor Calibration',
        'dependencies_module': [
            ('pip-pypi', 'w1thermsensor', 'w1thermsensor')
        ]
    }
}

# PID controllers
PIDS = [
    ('pid', 'PID Controller')
]

def generate_conditional_name(name):
    return '{}: {}'.format(lazy_gettext('Conditional'), lazy_gettext(name))

# Conditional controllers
CONDITIONALS = [
    ('conditional_measurement', generate_conditional_name('Measurement')),
    ('conditional_output', generate_conditional_name('Output (On/Off)')),
    ('conditional_output_duration', generate_conditional_name('Output (On Duration)')),
    ('conditional_output_pwm', generate_conditional_name('Output (PWM)')),
    ('conditional_edge', generate_conditional_name('Edge')),
    ('conditional_run_pwm_method', generate_conditional_name('Run PWM Method')),
    ('conditional_sunrise_sunset', generate_conditional_name('Sunrise/Sunset')),
    ('conditional_timer_daily_time_point', generate_conditional_name('Timer (Daily Point)')),
    ('conditional_timer_daily_time_span', generate_conditional_name('Timer (Daily Span)')),
    ('conditional_timer_duration', generate_conditional_name('Timer (Duration)'))
]

# Conditional actions
CONDITIONAL_ACTIONS = [
    ('output', lazy_gettext('Output (Duration)')),
    ('output_pwm', lazy_gettext('Output (Duty Cycle)')),
    ('command', lazy_gettext('Execute Command')),
    ('activate_controller', lazy_gettext('Activate Controller')),
    ('deactivate_controller', lazy_gettext('Deactivate Controller')),
    ('pause_pid', lazy_gettext('PID Pause')),
    ('resume_pid', lazy_gettext('PID Resume')),
    ('method_pid', lazy_gettext('PID Set Method')),
    ('setpoint_pid', lazy_gettext('PID Set Setpoint')),
    ('email', lazy_gettext('Email Notification')),
    ('flash_lcd_off', lazy_gettext('LCD Flashing Off')),
    ('flash_lcd_on', lazy_gettext('LCD Flashing On')),
    ('lcd_backlight_off', lazy_gettext('LCD Backlight Off')),
    ('lcd_backlight_on', lazy_gettext('LCD Backlight On')),
    ('photo', lazy_gettext('Capture Photo')),

    # TODO: These have been disabled until they can be properly tested
    # ('photo_email', lazy_gettext('Email Photo')),
    # ('video', lazy_gettext('Video')),
    # ('video_email', lazy_gettext('Email Video'))
]

# Calibration
CALIBRATION_DEVICES = [
    ('setup_atlas_ph', 'Atlas Scientific pH Sensor'),
    ('setup_ds_resolution', 'DS-Type Temperature Sensors (e.g. DS18B20)')
]


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
    ('literia', 'Literia'),
    ('lumen', 'Lumen'),
    ('lux', 'Lux'),
    ('materia', 'Materia'),
    ('minty', 'Minty'),
    ('sandstone', 'Sandstone'),
    ('simplex', 'Simplex'),
    ('sketchy', 'Sketchy'),
    ('slate', 'Slate'),
    ('solar', 'Solar'),
    ('spacelab', 'Spacelab'),
    ('superhero', 'Superhero'),
    ('united', 'United'),
    ('yeti', 'Yeti')
]

THEMES_DARK = ['cyborg', 'darkly', 'slate', 'solar', 'superhero']

# Install path, the parent directory this script resides
INSTALL_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/..'

# SQLite3 databases that stores users and settings
DATABASE_PATH = os.path.join(INSTALL_DIRECTORY, 'databases')
SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# File paths/logging
USAGE_REPORTS_PATH = os.path.join(INSTALL_DIRECTORY, 'output_usage_reports')
DEPENDENCY_INIT_FILE = os.path.join(INSTALL_DIRECTORY, '.dependency')
UPGRADE_INIT_FILE = os.path.join(INSTALL_DIRECTORY, '.upgrade')
BACKUP_PATH = '/var/Mycodo-backups'  # Where Mycodo backups are stored
LOG_PATH = '/var/log/mycodo'  # Where generated logs are stored
LOGIN_LOG_FILE = os.path.join(LOG_PATH, 'login.log')
DAEMON_LOG_FILE = os.path.join(LOG_PATH, 'mycodo.log')
KEEPUP_LOG_FILE = os.path.join(LOG_PATH, 'mycodokeepup.log')
BACKUP_LOG_FILE = os.path.join(LOG_PATH, 'mycodobackup.log')
DEPENDENCY_LOG_FILE = os.path.join(LOG_PATH, 'mycododependency.log')
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
