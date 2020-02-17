# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo settings
#
import binascii
import sys
from datetime import timedelta

import os
from flask_babel import lazy_gettext

# Append proper path for other software reading this config file
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from config_translations import TRANSLATIONS

MYCODO_VERSION = '8.2.5'
ALEMBIC_VERSION = '0a8a5eb1be4b'

#  FORCE_UPGRADE_MASTER
#  Set True to enable upgrading to the master branch of the Mycodo repository.
#  Set False to enable upgrading to the latest Release version (default).
#  Do not use this feature unless you know what you're doing or have been
#  instructed to do so, as it can really mess up your system.
FORCE_UPGRADE_MASTER = False

# Final release for each major version number
# Used to determine proper upgrade page to display
FINAL_RELEASES = ['5.7.3', '6.4.7', '7.10.0']

# ENABLE FLASK PROFILER
# Accessed at https://127.0.0.1/mycodo-flask-profiler
ENABLE_FLASK_PROFILER = False

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

DASHBOARD_WIDGETS = [
    ('', lazy_gettext('Add Dashboard Widget')),
    ('spacer', lazy_gettext('Spacer')),
    ('graph', lazy_gettext('Graph')),
    ('gauge', lazy_gettext('Gauge')),
    ('indicator', TRANSLATIONS['indicator']['title']),
    ('measurement', TRANSLATIONS['measurement']['title']),
    ('output', TRANSLATIONS['output']['title']),
    ('output_pwm_slider', '{}: {}'.format(
        TRANSLATIONS['output']['title'], lazy_gettext('PWM Slider'))),
    ('pid_control', lazy_gettext('PID Control')),
    ('camera', TRANSLATIONS['camera']['title'])
]

# Camera info
CAMERA_INFO = {
    'fswebcam': {
        'name': 'fswebcam',
        'dependencies_module': [
            ('apt', 'fswebcam', 'fswebcam')
        ]
    },
    'opencv': {
        'name': 'OpenCV',
        'dependencies_module': [
            ('pip-pypi', 'imutils', 'imutils'),
            ('apt', 'python3-opencv', 'python3-opencv'),
        ]
    },
    'picamera': {
        'name': 'PiCamera',
        'dependencies_module': [
            ('pip-pypi', 'picamera', 'picamera')
        ]
    },
}

# LCD info
LCD_INFO = {
    '16x2_generic': {
        'name': '16x2 LCD',
        'dependencies_module': []
    },
    '20x4_generic': {
        'name': '20x4 LCD',
        'dependencies_module': []
    },
    '128x32_pioled': {
        'name': '128x32 OLED (SD1306)',
        'dependencies_module': [
            ('apt', 'libjpeg-dev', 'libjpeg-dev'),
            ('pip-pypi', 'PIL', 'Pillow'),
            ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
            ('pip-pypi', 'Adafruit_PureIO', 'Adafruit_PureIO'),
            ('pip-git', 'Adafruit_SSD1306', 'git://github.com/adafruit/Adafruit_Python_SSD1306.git#egg=adafruit-ssd1306')
        ]
    },
    '128x64_pioled': {
        'name': '128x64 OLED (SD1306)',
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
    ('20x4_generic', LCD_INFO['20x4_generic']['name']),
    ('128x32_pioled', LCD_INFO['128x32_pioled']['name']),
    ('128x64_pioled', LCD_INFO['128x64_pioled']['name'])
]

# Math info
MATH_INFO = {
    'average': {
        'name': lazy_gettext('Average (Last, Multiple Channels)'),
        'dependencies_module': [],
        'enable_measurements_select': True,
        'measure': {}
    },
    'average_single': {
        'name': lazy_gettext('Average (Past, Single Channel)'),
        'dependencies_module': [],
        'enable_measurements_select': False,
        'enable_measurements_convert': True,
        'measure': {}
    },
    'sum': {
        'name': lazy_gettext('Sum (Last, Multiple Channels)'),
        'dependencies_module': [],
        'enable_measurements_select': True,
        'measure': {}
    },
    'sum_single': {
        'name': lazy_gettext('Sum (Past, Single Channel)'),
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
    ('sum', MATH_INFO['sum']['name']),
    ('sum_single', MATH_INFO['sum_single']['name']),
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
        'dependencies_module': [
            ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio')
        ],
        'measure': {
            'duty_cycle': {'percent': {0: {}}}
        }},
    'wireless_rpi_rf': {
        'name': lazy_gettext('Wireless 315/433MHz LPD/SRD (rpi-rf)'),
        'dependencies_module': [
            ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO'),
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
            'volume': {'ml': {0: {}}},
            'duration_time': {'minute': {1: {}}}
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
    ('atlas_ezo_pmp,FTDI', '{} ({})'.format(
        OUTPUT_INFO['atlas_ezo_pmp']['name'], lazy_gettext('FTDI'))),
    ('atlas_ezo_pmp,I2C', '{} ({})'.format(
        OUTPUT_INFO['atlas_ezo_pmp']['name'], lazy_gettext('I2C'))),
    ('atlas_ezo_pmp,UART', '{} ({})'.format(
        OUTPUT_INFO['atlas_ezo_pmp']['name'], lazy_gettext('UART')))
]

# Defines which Outputs are PWM
OUTPUTS_PWM = [
    'pwm', 'command_pwm', 'python_pwm'
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
            'name': '{} ({})'.format(
                TRANSLATIONS['output']['title'],
                TRANSLATIONS['duration']['title'])
        },
        7: {
            'measurement': 'duty_cycle',
            'unit': 'percent',
            'name': '{} ({})'.format(
                TRANSLATIONS['output']['title'],
                TRANSLATIONS['duty_cycle']['title'])
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
    ('measurement', "{} ({}, {})".format(
        TRANSLATIONS['measurement']['title'],
        TRANSLATIONS['single']['title'],
        TRANSLATIONS['last']['title'])),
    ('measurement_past_average', "{} ({}, {}, {})".format(
        TRANSLATIONS['measurement']['title'],
        TRANSLATIONS['single']['title'],
        TRANSLATIONS['past']['title'],
        TRANSLATIONS['average']['title'])),
    ('measurement_past_sum', "{} ({}, {}, {})".format(
        TRANSLATIONS['measurement']['title'],
        TRANSLATIONS['single']['title'],
        TRANSLATIONS['past']['title'],
        TRANSLATIONS['sum']['title'])),
    ('measurement_dict', "{} ({}, {})".format(
        TRANSLATIONS['measurement']['title'],
        TRANSLATIONS['multiple']['title'],
        TRANSLATIONS['past']['title'])),
    ('gpio_state', lazy_gettext('GPIO State')),
    ('output_state', lazy_gettext('Output State')),
    ('output_duration_on', lazy_gettext('Output Duration On')),
    ('controller_status', lazy_gettext("Controller Running")),
]

FUNCTION_INFO = {
    'function_spacer': {
        'name': '{}: {}'.format(
            TRANSLATIONS['function']['title'],
            lazy_gettext('Spacer')),
        'dependencies_module': []
    },
    'function_actions': {
        'name': '{}: {}'.format(
            TRANSLATIONS['function']['title'],
            lazy_gettext('Execute Actions')),
        'dependencies_module': []
    },
    'conditional_conditional': {
        'name': '{}: {}'.format(
            TRANSLATIONS['controller']['title'],
            TRANSLATIONS['conditional']['title']),
        'dependencies_module': []
    },
    'pid_pid': {
        'name': '{}: {}'.format(
            TRANSLATIONS['controller']['title'],
            TRANSLATIONS['pid']['title']),
        'dependencies_module': []
    },
    'trigger_edge': {
        'name': '{}: {}'.format(
            TRANSLATIONS['trigger']['title'],
            TRANSLATIONS['edge']['title']),
        'dependencies_module': []
    },
    'trigger_output': {
        'name': '{}: {} ({}/{})'.format(
            TRANSLATIONS['trigger']['title'],
            TRANSLATIONS['output']['title'],
            TRANSLATIONS['on']['title'],
            TRANSLATIONS['off']['title']),
        'dependencies_module': []
    },
    'trigger_output_pwm': {
        'name': '{}: {} ({})'.format(
            TRANSLATIONS['trigger']['title'],
            TRANSLATIONS['output']['title'],
            TRANSLATIONS['pwm']['title']),
        'dependencies_module': []
    },
    'trigger_timer_daily_time_point': {
        'name': lazy_gettext('Trigger: Timer (Daily Point)'),
        'dependencies_module': []
    },
    'trigger_timer_daily_time_span': {
        'name': '{}: {} ({})'.format(
            TRANSLATIONS['trigger']['title'],
            TRANSLATIONS['timer']['title'],
            lazy_gettext('Daily Span')),
        'dependencies_module': []
    },
    'trigger_timer_duration': {
        'name': '{}: {} ({})'.format(
            TRANSLATIONS['trigger']['title'],
            TRANSLATIONS['timer']['title'],
            TRANSLATIONS['duration']['title']),
        'dependencies_module': []
    },
    'trigger_infrared_remote_input': {
        'name': '{}: {}'.format(
            TRANSLATIONS['trigger']['title'],
            lazy_gettext('Infrared Receive')),
        'dependencies_module': [
            ('apt', 'liblircclient-dev', 'liblircclient-dev'),
            ('apt', 'lirc', 'lirc'),
            ('pip-pypi', 'lirc', 'python-lirc')
        ]
    },
    'trigger_run_pwm_method': {
        'name': '{}: {}'.format(
            TRANSLATIONS['trigger']['title'],
            lazy_gettext('Run PWM Method')),
        'dependencies_module': []
    },
    'trigger_sunrise_sunset': {
        'name': '{}: {}'.format(
            TRANSLATIONS['trigger']['title'],
            lazy_gettext('Sunrise/Sunset')),
        'dependencies_module': []
    }
}

FUNCTIONS = [
    ('function_spacer', FUNCTION_INFO['function_spacer']['name']),
    ('function_actions', FUNCTION_INFO['function_actions']['name']),
    ('conditional_conditional', FUNCTION_INFO['conditional_conditional']['name']),
    ('pid_pid', FUNCTION_INFO['pid_pid']['name']),
    ('trigger_edge', FUNCTION_INFO['trigger_edge']['name']),
    ('trigger_output', FUNCTION_INFO['trigger_output']['name']),
    ('trigger_output_pwm', FUNCTION_INFO['trigger_output_pwm']['name']),
    ('trigger_timer_daily_time_point', FUNCTION_INFO['trigger_timer_daily_time_point']['name']),
    ('trigger_timer_daily_time_span', FUNCTION_INFO['trigger_timer_daily_time_span']['name']),
    ('trigger_timer_duration', FUNCTION_INFO['trigger_timer_duration']['name']),
    ('trigger_infrared_remote_input', FUNCTION_INFO['trigger_infrared_remote_input']['name']),
    ('trigger_run_pwm_method', FUNCTION_INFO['trigger_run_pwm_method']['name']),
    ('trigger_sunrise_sunset', FUNCTION_INFO['trigger_sunrise_sunset']['name'])
]

# Function actions
FUNCTION_ACTION_INFO = {
    'pause_actions': {
        'name': '{} {}'.format(
            TRANSLATIONS['pause']['title'],
            TRANSLATIONS['actions']['title']),
        'dependencies_module': []
    },
    'photo': {
        'name': lazy_gettext('Camera: Capture Photo'),
        'dependencies_module': []
    },
    'activate_controller': {
        'name': '{}: {}'.format(
            TRANSLATIONS['controller']['title'],
            TRANSLATIONS['activate']['title']),
        'dependencies_module': []
    },
    'deactivate_controller': {
        'name': '{}: {}'.format(
            TRANSLATIONS['controller']['title'],
            TRANSLATIONS['deactivate']['title']),
        'dependencies_module': []
    },
    'create_note': {
        'name': TRANSLATIONS['note']['title'],
        'dependencies_module': []
    },
    'email': {
        'name': '{} ({})'.format(TRANSLATIONS['email']['title'],
                                 TRANSLATIONS['single']['title']),
        'dependencies_module': []
    },
    'email_multiple': {
        'name': '{} ({})'.format(TRANSLATIONS['email']['title'],
                                 TRANSLATIONS['multiple']['title']),
        'dependencies_module': []
    },
    'photo_email': {
        'name': lazy_gettext('Email with Photo Attachment'),
        'dependencies_module': []
    },
    'video_email': {
        'name': lazy_gettext('Email with Video Attachment'),
        'dependencies_module': []
    },
    'command': {
        'name': lazy_gettext('Execute Command'),
        'dependencies_module': []
    },
    'infrared_send': {
        'name': lazy_gettext('Infrared Send'),
        'dependencies_module': [
            ('apt', 'liblircclient-dev', 'liblircclient-dev'),
            ('apt', 'lirc', 'lirc'),
            ('pip-pypi', 'lirc', 'python-lirc'),
            ('pip-pypi', 'py_irsend', 'py-irsend')
        ]
    },
    'lcd_backlight_off': {
        'name': '{}: {}'.format(
            TRANSLATIONS['lcd']['title'],
            lazy_gettext('Backlight Off')),
        'dependencies_module': []
    },
    'lcd_backlight_on': {
        'name': '{}: {}'.format(
            TRANSLATIONS['lcd']['title'],
            lazy_gettext('Backlight On')),
        'dependencies_module': []
    },
    'flash_lcd_off': {
        'name': '{}: {}'.format(
            TRANSLATIONS['lcd']['title'],
            lazy_gettext('Flashing Off')),
        'dependencies_module': []
    },
    'flash_lcd_on': {
        'name': '{}: {}'.format(
            TRANSLATIONS['lcd']['title'],
            lazy_gettext('Flashing On')),
        'dependencies_module': []
    },
    'output': {
        'name': '{} ({})'.format(
            TRANSLATIONS['output']['title'],
            TRANSLATIONS['duration']['title']),
        'dependencies_module': []
    },
    'output_pwm': {
        'name': '{} ({})'.format(
            TRANSLATIONS['output']['title'],
            TRANSLATIONS['duty_cycle']['title']),
        'dependencies_module': []
    },
    'output_ramp_pwm': {
        'name': '{} {}'.format(
            TRANSLATIONS['ramp']['title'],
            TRANSLATIONS['duty_cycle']['title']),
        'dependencies_module': []
    },
    'pause_pid': {
        'name': '{}: {}'.format(
            TRANSLATIONS['pid']['title'],
            TRANSLATIONS['pause']['title']),
        'dependencies_module': []
    },
    'resume_pid': {
        'name': '{}: {}'.format(
            TRANSLATIONS['pid']['title'],
            TRANSLATIONS['resume']['title']),
        'dependencies_module': []
    },
    'method_pid': {
        'name': '{}: {}'.format(
            TRANSLATIONS['pid']['title'],
            lazy_gettext('Set Method')),
        'dependencies_module': []
    },
    'setpoint_pid': {
        'name': '{}: {}'.format(
            TRANSLATIONS['pid']['title'],
            lazy_gettext('Set Setpoint')),
        'dependencies_module': []
    },
    'setpoint_pid_raise': {
        'name': '{}: {}'.format(
            TRANSLATIONS['pid']['title'],
            lazy_gettext('Raise Setpoint')),
        'dependencies_module': []
    },
    'setpoint_pid_lower': {
        'name': '{}: {}'.format(
            TRANSLATIONS['pid']['title'],
            lazy_gettext('Lower Setpoint')),
        'dependencies_module': []
    }

    # TODO: These have been disabled until they can be properly tested
    # ('video', lazy_gettext('Video')),
    # ('video_email', lazy_gettext('Email Video'))
}

FUNCTION_ACTIONS = [
    ('pause_actions', FUNCTION_ACTION_INFO['pause_actions']['name']),
    ('photo', FUNCTION_ACTION_INFO['photo']['name']),
    ('activate_controller', FUNCTION_ACTION_INFO['activate_controller']['name']),
    ('deactivate_controller', FUNCTION_ACTION_INFO['deactivate_controller']['name']),
    ('create_note', FUNCTION_ACTION_INFO['create_note']['name']),
    ('email', FUNCTION_ACTION_INFO['email']['name']),
    ('email_multiple', FUNCTION_ACTION_INFO['email_multiple']['name']),
    ('photo_email', FUNCTION_ACTION_INFO['photo_email']['name']),
    ('video_email', FUNCTION_ACTION_INFO['video_email']['name']),
    ('command', FUNCTION_ACTION_INFO['command']['name']),
    ('infrared_send', FUNCTION_ACTION_INFO['infrared_send']['name']),
    ('lcd_backlight_off', FUNCTION_ACTION_INFO['lcd_backlight_off']['name']),
    ('lcd_backlight_on', FUNCTION_ACTION_INFO['lcd_backlight_on']['name']),
    ('flash_lcd_off', FUNCTION_ACTION_INFO['flash_lcd_off']['name']),
    ('flash_lcd_on', FUNCTION_ACTION_INFO['flash_lcd_on']['name']),
    ('output', FUNCTION_ACTION_INFO['output']['name']),
    ('output_pwm', FUNCTION_ACTION_INFO['output_pwm']['name']),
    ('output_ramp_pwm', FUNCTION_ACTION_INFO['output_ramp_pwm']['name']),
    ('pause_pid', FUNCTION_ACTION_INFO['pause_pid']['name']),
    ('resume_pid', FUNCTION_ACTION_INFO['resume_pid']['name']),
    ('method_pid', FUNCTION_ACTION_INFO['method_pid']['name']),
    ('setpoint_pid', FUNCTION_ACTION_INFO['setpoint_pid']['name']),
    ('setpoint_pid_raise', FUNCTION_ACTION_INFO['setpoint_pid_raise']['name']),
    ('setpoint_pid_lower', FUNCTION_ACTION_INFO['setpoint_pid_lower']['name'])
]

# Calibration
CALIBRATION_DEVICES = [
    ('setup_atlas_ec', 'Atlas Scientific Electrical Conductivity Sensor'),
    ('setup_atlas_ezo_pump', 'Atlas Scientific EZO Pump'),
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

# Install path (the parent directory of this script)
INSTALL_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + '/..')

# Database
DATABASE_PATH = os.path.join(INSTALL_DIRECTORY, 'databases')
ALEMBIC_UPGRADE_POST = os.path.join(DATABASE_PATH, 'alembic_post_upgrade_versions')
SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

# Misc paths
PATH_1WIRE = '/sys/bus/w1/devices/'
PATH_CONTROLLERS = os.path.join(INSTALL_DIRECTORY, 'mycodo/controllers')
PATH_INPUTS = os.path.join(INSTALL_DIRECTORY, 'mycodo/inputs')
PATH_CONTROLLERS_CUSTOM = os.path.join(PATH_CONTROLLERS, 'custom_controllers')
PATH_INPUTS_CUSTOM = os.path.join(PATH_INPUTS, 'custom_inputs')
PATH_PYTHON_CODE_USER = os.path.join(INSTALL_DIRECTORY, 'mycodo/user_python_code')
USAGE_REPORTS_PATH = os.path.join(INSTALL_DIRECTORY, 'output_usage_reports')
DEPENDENCY_INIT_FILE = os.path.join(INSTALL_DIRECTORY, '.dependency')
UPGRADE_INIT_FILE = os.path.join(INSTALL_DIRECTORY, '.upgrade')
BACKUP_PATH = '/var/Mycodo-backups'  # Where Mycodo backups are stored

# Log files
LOG_PATH = '/var/log/mycodo'  # Where generated logs are stored
LOGIN_LOG_FILE = os.path.join(LOG_PATH, 'login.log')
DAEMON_LOG_FILE = os.path.join(LOG_PATH, 'mycodo.log')
KEEPUP_LOG_FILE = os.path.join(LOG_PATH, 'mycodokeepup.log')
BACKUP_LOG_FILE = os.path.join(LOG_PATH, 'mycodobackup.log')
DEPENDENCY_LOG_FILE = os.path.join(LOG_PATH, 'mycododependency.log')
UPGRADE_LOG_FILE = os.path.join(LOG_PATH, 'mycodoupgrade.log')
UPGRADE_TMP_LOG_FILE = '/tmp/mycodoupgrade.log'
RESTORE_LOG_FILE = os.path.join(LOG_PATH, 'mycodorestore.log')
HTTP_ACCESS_LOG_FILE = '/var/log/nginx/access.log'
HTTP_ERROR_LOG_FILE = '/var/log/nginx/error.log'

# Lock files
LOCK_PATH = '/var/lock'
ATLAS_PH_LOCK_FILE = os.path.join(LOCK_PATH, 'sensor-atlas-ph.pid')
LOCK_FILE_STREAM = os.path.join(LOCK_PATH, 'mycodo-camera-stream.pid')

# Run files
RUN_PATH = '/var/run'
FRONTEND_PID_FILE = os.path.join(RUN_PATH, 'mycodoflask.pid')
DAEMON_PID_FILE = os.path.join(RUN_PATH, 'mycodo.pid')

# Remote admin
STORED_SSL_CERTIFICATE_PATH = os.path.join(
    INSTALL_DIRECTORY, 'mycodo/mycodo_flask/ssl_certs/remote_admin')

# Cameras
PATH_CAMERAS = os.path.join(INSTALL_DIRECTORY, 'cameras')

# Notes
PATH_NOTE_ATTACHMENTS = os.path.join(INSTALL_DIRECTORY, 'note_attachments')

# Determine if running in a Docker container
if os.environ.get('DOCKER_CONTAINER', False) == 'TRUE':
    DOCKER_CONTAINER = True
else:
    DOCKER_CONTAINER = False

# Pyro5 URI/host, used by mycodo_client.py
if DOCKER_CONTAINER:
    PYRO_URI = 'PYRO:mycodo.pyro_server@mycodo_daemon:9090'
else:
    PYRO_URI = 'PYRO:mycodo.pyro_server@127.0.0.1:9090'

# Influx sensor/device measurement database
INFLUXDB_HOST = 'localhost' if not DOCKER_CONTAINER else 'influxdb'
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

RELEASE_URL = 'https://api.github.com/repos/kizniche/Mycodo/tags'


class ProdConfig(object):
    """ Production Configuration """
    SQL_DATABASE_MYCODO = os.path.join(DATABASE_PATH, 'mycodo.db')
    MYCODO_DB_PATH = 'sqlite:///{}'.format(SQL_DATABASE_MYCODO)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(SQL_DATABASE_MYCODO)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FLASK_PROFILER = {
        "enabled": True,
        "storage": {
            "engine": "sqlalchemy",
            "db_url": 'sqlite:///{}'.format(os.path.join(DATABASE_PATH, 'profile.db'))
        },
        "basicAuth": {
            "enabled": True,
            "username": "admin231",
            "password": "admin421378956"
        },
        "ignore": [
            "^/static/.*",
            "/login",
            "/settings/users"
        ],
        "endpointRoot": "mycodo-flask-profiler"
    }

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
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = '1234'
    TESTING = True
    DEBUG = True
