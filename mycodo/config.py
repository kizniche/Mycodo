# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo settings
#
import binascii
import sys
from datetime import timedelta

import os
from flask_babel import lazy_gettext

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from config_translations import TRANSLATIONS

MYCODO_VERSION = '7.1.5'
ALEMBIC_VERSION = 'ed21c36670f4'

#  FORCE_UPGRADE_MASTER
#  Set True to enable upgrading to the master branch of the Mycodo repository.
#  Set False to enable upgrading to the latest Release version (default).
#  Do not use this feature unless you know what you're doing or have been
#  instructed to do so, as it can really mess up your system.
FORCE_UPGRADE_MASTER = False

# Final release for each major version number
# Used to determine proper upgrade page to display
FINAL_RELEASES = ['5.7.3', '6.4.7']

LANGUAGES = {
    'en': 'English',
    'de': 'Deutsche (German)',
    'es': 'Español (Spanish)',
    'fr': 'Français (French)',
    'it': 'Italiano (Italian)',
    'nl': 'Nederlands (Dutch)',
    'nb': 'Norsk (Norwegian)',
    'pt': 'Português (Portuguese)',
    'ru': 'русский язык (Russian)',
    'sr': 'српски (Serbian)',
    'sv': 'Svenska (Swedish)',
    'zh': '中文 (Chinese)'
}

# LCD info
LCD_INFO = {
    '16x2_generic': {
        'name': '16x2 Generic',
        'dependencies_module': []
    },
    '16x4_generic': {
        'name': '16x4 Generic',
        'dependencies_module': []
    },
    '128x32_pioled': {
        'name': '128x32 OLED',
        'dependencies_module': [
            ('apt', 'libjpeg-dev', 'libjpeg-dev'),
            ('pip-pypi', 'PIL', 'Pillow'),
            ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
            ('pip-pypi', 'Adafruit_PureIO', 'Adafruit_PureIO'),
            ('pip-git', 'Adafruit_SSD1306', 'git://github.com/adafruit/Adafruit_Python_SSD1306.git#egg=adafruit-ssd1306')
        ]
    },
    '128x64_pioled': {
        'name': '128x64 OLED',
        'dependencies_module': [
            ('apt', 'libjpeg-dev', 'libjpeg-dev'),
            ('pip-pypi', 'PIL', 'Pillow'),
            ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
            ('pip-pypi', 'Adafruit_PureIO', 'Adafruit_PureIO'),
            ('pip-git', 'Adafruit_SSD1306', 'git://github.com/adafruit/Adafruit_Python_SSD1306.git#egg=adafruit-ssd1306')
        ]
    }
}

# Math form dropdown
LCDS = [
    ('16x2_generic', LCD_INFO['16x2_generic']['name']),
    ('16x4_generic', LCD_INFO['16x4_generic']['name']),
    ('128x32_pioled', LCD_INFO['128x32_pioled']['name']),
    ('128x64_pioled', LCD_INFO['128x64_pioled']['name'])
]

# Math info
MATH_INFO = {
    'average': {
        'name': lazy_gettext('Average (Multiple Inputs)'),
        'dependencies_module': [],
        'enable_measurements_select': True,
        'measure': {}
    },
    'average_single': {
        'name': lazy_gettext('Average (Single Input)'),
        'dependencies_module': [],
        'enable_measurements_select': False,
        'enable_measurements_convert': True,
        'measure': {}
    },
    'difference': {
        'name': lazy_gettext('Difference'),
        'dependencies_module': [],
        'enable_measurements_select': True,
        'measure': {}
    },
    'equation': {
        'name': lazy_gettext('Equation'),
        'dependencies_module': [],
        'enable_measurements_select': True,
        'measure': {}
    },
    'humidity': {
        'name': lazy_gettext('Humidity (Wet/Dry-Bulb)'),
        'dependencies_module': [],
        'enable_measurements_convert': True,
        'measure': {
            0: {
                'measurement': 'humidity',
                'unit': 'percent'
            },
            1: {
                'measurement': 'humidity_ratio',
                'unit': 'kg_kg'
            },
            2: {
                'measurement': 'specific_enthalpy',
                'unit': 'kJ_kg'
            },
            3: {
                'measurement': 'specific_volume',
                'unit': 'm3_kg'
            }
        }
    },
    'redundancy': {
        'name': lazy_gettext('Redundancy'),
        'dependencies_module': [],
        'enable_measurements_select': True,
        'measure': {}
    },
    'statistics': {
        'name': lazy_gettext('Statistics'),
        'dependencies_module': [],
        'enable_single_measurement_select': True,
        'measure': {
            0: {
                'measurement': '',
                'unit': '',
                'name': 'Mean'
            },
            1: {
                'measurement': '',
                'unit': '',
                'name': 'Median'
            },
            2: {
                'measurement': '',
                'unit': '',
                'name': 'Minimum'
            },
            3: {
                'measurement': '',
                'unit': '',
                'name': 'Maximum'
            },
            4: {
                'measurement': '',
                'unit': '',
                'name': 'Standard Deviation'
            },
            5: {
                'measurement': '',
                'unit': '',
                'name': 'St. Dev. of Mean (upper)'
            },
            6: {
                'measurement': '',
                'unit': '',
                'name': 'St. Dev. of Mean (lower)'
            }
        }
    },
    'verification': {
        'name': lazy_gettext('Verification'),
        'dependencies_module': [],
        'enable_measurements_select': True,
        'measure': {}
    },
    'vapor_pressure_deficit': {
        'name': lazy_gettext('Vapor Pressure Deficit'),
        'dependencies_module': [],
        'enable_measurements_select': False,
        'measure': {
            0: {
                'measurement': 'vapor_pressure_deficit',
                'unit': 'Pa'
            }
        }
    }
}

# Math form dropdown
MATHS = [
    ('average', MATH_INFO['average']['name']),
    ('average_single', MATH_INFO['average_single']['name']),
    ('difference', MATH_INFO['difference']['name']),
    ('equation', MATH_INFO['equation']['name']),
    ('redundancy', MATH_INFO['redundancy']['name']),
    ('verification', MATH_INFO['verification']['name']),
    ('statistics', MATH_INFO['statistics']['name']),
    ('humidity', MATH_INFO['humidity']['name']),
    ('vapor_pressure_deficit', MATH_INFO['vapor_pressure_deficit']['name'])
]

# Method info
METHOD_INFO = {
    'Date': {
        'name': lazy_gettext('Time/Date'),
        'dependencies_module': []
    },
    'Duration': {
        'name': lazy_gettext('Duration'),
        'dependencies_module': []
    },
    'Daily': {
        'name': lazy_gettext('Daily (Time-Based)'),
        'dependencies_module': []
    },
    'DailySine': {
        'name': lazy_gettext('Daily (Sine Wave)'),
        'dependencies_module': []
    },
    'DailyBezier': {
        'name': lazy_gettext('Daily (Bezier Curve)'),
        'dependencies_module': [
            ('apt', 'python3-numpy', 'python3-numpy')
        ]
    }
}

# Method form dropdown
METHODS = [
    ('Date', METHOD_INFO['Date']['name']),
    ('Duration', METHOD_INFO['Duration']['name']),
    ('Daily', METHOD_INFO['Daily']['name']),
    ('DailySine', METHOD_INFO['DailySine']['name']),
    ('DailyBezier', METHOD_INFO['DailyBezier']['name'])
]

# Outputs
OUTPUT_INFO = {
    'wired': {
        'name': lazy_gettext('On/Off (GPIO)'),
        'dependencies_module': [],
        'measure': {
            'duration_time': {'s': {0: {}}}
        }},
    'pwm': {
        'name': lazy_gettext('PWM (GPIO)'),
        'dependencies_module': [],
        'measure': {
            'duty_cycle': {'percent': {0: {}}}
        }},
    'wireless_rpi_rf': {
        'name': lazy_gettext('Wireless 315/433MHz LPD/SRD (rpi-rf)'),
        'dependencies_module': [
            ('pip-pypi', 'rpi_rf', 'rpi_rf')
        ],
        'measure': {
            'duration_time': {'s': {0: {}}}
        }},
    'command': {
        'name': lazy_gettext('On/Off (Linux Command)'),
        'dependencies_module': [],
        'measure': {
            'duration_time': {'s': {0: {}}}
        }},
    'command_pwm': {
        'name': lazy_gettext('PWM (Linux Command)'),
        'dependencies_module': [],
        'measure': {
            'duty_cycle': {'percent': {0: {}}}
        }},
    'python': {
        'name': lazy_gettext('On/Off (Python Command)'),
        'dependencies_module': [],
        'measure': {
            'duration_time': {'s': {0: {}}}
        }},
    'python_pwm': {
        'name': lazy_gettext('PWM (Python Command)'),
        'dependencies_module': [],
        'measure': {
            'duty_cycle': {'percent': {0: {}}}
        }},
    'atlas_ezo_pmp': {
        'name': lazy_gettext('Atlas EZO-PMP'),
        'dependencies_module': [],
        'measure': {
            'volume': {'ml': {0: {}}}
        }}
}

# Output form dropdown
OUTPUTS = [
    ('wired,GPIO', OUTPUT_INFO['wired']['name']),
    ('pwm,GPIO', OUTPUT_INFO['pwm']['name']),
    ('command,GPIO', OUTPUT_INFO['command']['name']),
    ('command_pwm,GPIO', OUTPUT_INFO['command_pwm']['name']),
    ('python,GPIO', OUTPUT_INFO['python']['name']),
    ('python_pwm,GPIO', OUTPUT_INFO['python_pwm']['name']),
    ('wireless_rpi_rf,GPIO', OUTPUT_INFO['wireless_rpi_rf']['name']),
    ('atlas_ezo_pmp,I2C', '{} ({})'.format(
        OUTPUT_INFO['atlas_ezo_pmp']['name'], lazy_gettext('I2C'))),
    ('atlas_ezo_pmp,UART', '{} ({})'.format(
        OUTPUT_INFO['atlas_ezo_pmp']['name'], lazy_gettext('UART')))
]

PID_INFO = {
    'measure': {
        0: {
            'measurement': '',
            'unit': '',
            'name': '{}'.format(TRANSLATIONS['setpoint']['title']),
            'measurement_type': 'setpoint'
        },
        1: {
            'measurement': '',
            'unit': '',
            'name': '{} (Band Min)'.format(TRANSLATIONS['setpoint']['title']),
            'measurement_type': 'setpoint'
        },
        2: {
            'measurement': '',
            'unit': '',
            'name': '{} (Band Max)'.format(TRANSLATIONS['setpoint']['title']),
            'measurement_type': 'setpoint'
        },
        3: {
            'measurement': 'pid_p_value',
            'unit': 'pid_value',
            'name': 'P-value'
        },
        4: {
            'measurement': 'pid_i_value',
            'unit': 'pid_value',
            'name': 'I-value'
        },
        5: {
            'measurement': 'pid_d_value',
            'unit': 'pid_value',
            'name': 'D-value'
        },
        6: {
            'measurement': 'duration_time',
            'unit': 's',
            'name': '{} ({})'.format(TRANSLATIONS['output']['title'], TRANSLATIONS['duration']['title'])
        },
        7: {
            'measurement': 'duty_cycle',
            'unit': 'percent',
            'name': '{} ({})'.format(TRANSLATIONS['output']['title'], TRANSLATIONS['duty_cycle']['title'])
        }
    }
}

# Calibration
CALIBRATION_INFO = {
    'CALIBRATE_DS_TYPE': {
        'name': lazy_gettext('DS-Type Sensor Calibration'),
        'dependencies_module': [
            ('pip-pypi', 'w1thermsensor', 'w1thermsensor')
        ]
    }
}

# Conditional controllers
CONDITIONAL_CONDITIONS = [
    ('measurement', TRANSLATIONS['measurement']['title']),
    ('gpio_state', lazy_gettext('GPIO State'))
]

FUNCTION_TYPES = [
    (
        'function_spacer',
        lazy_gettext('Spacer'),
        '{}: {}'.format(TRANSLATIONS['function']['title'], lazy_gettext('Spacer'))),
    (
        'function_actions',
        TRANSLATIONS['actions']['title'],
        '{}: {}'.format(TRANSLATIONS['function']['title'], lazy_gettext('Execute Actions'))),
    (
        'conditional_conditional',
        TRANSLATIONS['conditional']['title'],
        '{}: {}'.format(TRANSLATIONS['controller']['title'], TRANSLATIONS['conditional']['title'])),
    (
        'pid_pid',
        TRANSLATIONS['pid']['title'],
        '{}: {}'.format(TRANSLATIONS['controller']['title'], TRANSLATIONS['pid']['title'])),
    (
        'trigger_edge',
        TRANSLATIONS['edge']['title'],
        '{}: {}'.format(TRANSLATIONS['trigger']['title'], TRANSLATIONS['edge']['title'])),
    (
        'trigger_output',
        '{} ({}/{})'.format(TRANSLATIONS['output']['title'], TRANSLATIONS['on']['title'],
                            TRANSLATIONS['off']['title']),
        '{}: {} ({}/{})'.format(TRANSLATIONS['trigger']['title'], TRANSLATIONS['output']['title'],
                                TRANSLATIONS['on']['title'], TRANSLATIONS['off']['title'])),
    (
        'trigger_output_duration',
        '{} ({})'.format(TRANSLATIONS['output']['title'], TRANSLATIONS['duration']['title']),
        '{}: {} ({})'.format(TRANSLATIONS['trigger']['title'], TRANSLATIONS['output']['title'],
                             TRANSLATIONS['duration']['title'])),
    (
        'trigger_output_pwm',
        '{} ({})'.format(TRANSLATIONS['output']['title'], TRANSLATIONS['pwm']['title']),
        '{}: {} ({})'.format(TRANSLATIONS['trigger']['title'], TRANSLATIONS['output']['title'],
                             TRANSLATIONS['pwm']['title'])),
    (
        'trigger_timer_daily_time_point',
        'Timer (Daily Point)',
        lazy_gettext('Trigger: Timer (Daily Point)')),
    (
        'trigger_timer_daily_time_span',
        '{} ({})'.format(TRANSLATIONS['timer']['title'], lazy_gettext('Daily Span')),
        '{}: {} ({})'.format(TRANSLATIONS['trigger']['title'], TRANSLATIONS['timer']['title'],
                             lazy_gettext('Daily Span'))),
    (
        'trigger_timer_duration',
        '{} ({})'.format(TRANSLATIONS['timer']['title'], TRANSLATIONS['duration']['title']),
        '{}: {} ({})'.format(TRANSLATIONS['trigger']['title'], TRANSLATIONS['timer']['title'],
                             TRANSLATIONS['duration']['title'])),
    (
        'trigger_run_pwm_method',
        lazy_gettext('Run PWM Method'),
        '{}: ({})'.format(TRANSLATIONS['trigger']['title'], lazy_gettext('Run PWM Method'))),
    (
        'trigger_sunrise_sunset',
        lazy_gettext('Sunrise/Sunset'),
        '{}: ({})'.format(TRANSLATIONS['trigger']['title'], lazy_gettext('Sunrise/Sunset')))
]

# Conditional actions
FUNCTION_ACTIONS = [
    ('pause_actions', '{}: {}'.format(TRANSLATIONS['actions']['title'], TRANSLATIONS['pause']['title'])),
    ('photo', lazy_gettext('Camera: Capture Photo')),
    ('activate_controller', '{}: {}'.format(TRANSLATIONS['controller']['title'], TRANSLATIONS['activate']['title'])),
    ('deactivate_controller', '{}: {}'.format(TRANSLATIONS['controller']['title'], TRANSLATIONS['deactivate']['title'])),
    ('create_note', TRANSLATIONS['note']['title']),
    ('email', TRANSLATIONS['email']['title']),
    ('photo_email', lazy_gettext('Email with Photo Attachment')),
    ('video_email', lazy_gettext('Email with Video Attachment')),
    ('command', lazy_gettext('Execute Command')),
    ('lcd_backlight_off', '{}: {}'.format(TRANSLATIONS['lcd']['title'], lazy_gettext('Backlight Off'))),
    ('lcd_backlight_on', '{}: {}'.format(TRANSLATIONS['lcd']['title'], lazy_gettext('LCD: Backlight On'))),
    ('flash_lcd_off', '{}: {}'.format(TRANSLATIONS['lcd']['title'], lazy_gettext('LCD: Flashing Off'))),
    ('flash_lcd_on', '{}: {}'.format(TRANSLATIONS['lcd']['title'], lazy_gettext('LCD: Flashing On'))),
    ('output', '{}: {}'.format(TRANSLATIONS['output']['title'], TRANSLATIONS['duration']['title'])),
    ('output_pwm', '{}: {}'.format(TRANSLATIONS['output']['title'], TRANSLATIONS['duty_cycle']['title'])),
    ('pause_pid', '{}: {}'.format(TRANSLATIONS['pid']['title'], TRANSLATIONS['pause']['title'])),
    ('resume_pid', '{}: {}'.format(TRANSLATIONS['pid']['title'], TRANSLATIONS['resume']['title'])),
    ('method_pid', '{}: {}'.format(TRANSLATIONS['pid']['title'], lazy_gettext('Set Method'))),
    ('setpoint_pid', '{}: {}'.format(TRANSLATIONS['pid']['title'], lazy_gettext('Set Setpoint'))),

    # TODO: These have been disabled until they can be properly tested
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
         view_settings=False, view_camera=False, view_stats=False, view_logs=False),
    dict(id=5, name='Kiosk',
         edit_settings=False, edit_controllers=False, edit_users=False,
         view_settings=False, view_camera=True, view_stats=True, view_logs=False)
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
    ('pulse', 'Pulse'),
    ('sandstone', 'Sandstone'),
    ('simplex', 'Simplex'),
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
PATH_1WIRE = '/sys/bus/w1/devices/'
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

# Notes
PATH_NOTE_ATTACHMENTS = os.path.join(INSTALL_DIRECTORY, 'note_attachments')

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
