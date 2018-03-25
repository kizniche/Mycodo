# -*- coding: utf-8 -*-
#
#  config.py - Global Mycodo settings
#
import binascii
import collections
from datetime import timedelta

import os
from flask_babel import lazy_gettext

MYCODO_VERSION = '5.6.8'
ALEMBIC_VERSION = '01ba9473fc96'

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
    ('ATLAS_EC_I2C', 'Electrical Conductivity: Atlas Scientific (I2C)'),
    ('ATLAS_EC_UART', 'Electrical Conductivity: Atlas Scientific (Serial)'),
    ('BH1750', 'Luminance: BH1750 (I2C)'),
    ('TSL2561', 'Luminance: TSL2561 (I2C)'),
    ('TSL2591', 'Luminance: TSL2591 (I2C)'),
    ('CHIRP', 'Moisture/Temperature/Luminance: Chirp (I2C)'),
    ('ATLAS_PH_I2C', 'pH: Atlas Scientific (I2C)'),
    ('ATLAS_PH_UART', 'pH: Atlas Scientific (Serial)'),
    ('BMP180', 'Pressure/Temperature: BMP 180/085 (I2C)'),
    ('BMP280', 'Pressure/Temperature: BMP 280 (I2C)'),
    ('BME280', 'Pressure/Temperature/Humidity: BME 280 (I2C)'),
    ('DS18B20', 'Temperature: DS18B20 (1-Wire)'),
    ('ATLAS_PT1000_I2C', 'Temperature: Atlas Scientific PT-1000 (I2C)'),
    ('ATLAS_PT1000_UART', 'Temperature: Atlas Scientific PT-1000 (Serial)'),
    ('MAX31855', 'Temperature: MAX31855K + K-type thermocouple'),
    ('MAX31856', 'Temperature: MAX31856 + K/J/N/R/S/T/E/B-type thermocouple'),
    ('MAX31865', 'Temperature: MAX31865 + PT100 or PT1000 probe'),
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
        'name': 'Mycodo RAM',
        'py-dependencies': [],
        'measure': ['disk_space']},
    'ADS1x15': {
        'name': 'ADS1x15',
        'i2c-addresses': ['0x48'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_ADS1x15'],
        'measure': ['voltage']},
    'AM2315': {
        'name': 'AM2315',
        'i2c-addresses': ['0x5c'],
        'i2c-address-change': False,
        'py-dependencies': ['quick2wire'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'ATLAS_EC_I2C': {
        'name': 'Atlas Electrical Conductivity (I2C)',
        'i2c-addresses': ['0x01'],
        'i2c-address-change': False,
        'py-dependencies': [],
        'measure': ['electrical_conductivity']},
    'ATLAS_EC_UART': {
        'name': 'Atlas Electrical Conductivity (Serial)',
        'py-dependencies': ['serial'],
        'measure': ['electrical_conductivity']},
    'ATLAS_PH_I2C': {
        'name': 'Atlas pH (I2C)',
        'i2c-addresses': ['0x63'],
        'i2c-address-change': False,
        'py-dependencies': [],
        'measure': ['ph']},
    'ATLAS_PH_UART': {
        'name': 'Atlas pH (Serial)',
        'py-dependencies': ['serial'],
        'measure': ['ph']},
    'ATLAS_PT1000_I2C': {
        'name': 'Atlas PT-1000 (I2C)',
        'i2c-addresses': ['0x66'],
        'i2c-address-change': False,
        'py-dependencies': [],
        'measure': ['temperature']},
    'ATLAS_PT1000_UART': {
        'name': 'Atlas PT-1000 (Serial)',
        'py-dependencies': ['serial'],
        'measure': ['temperature']},
    'BH1750': {
        'name': 'BH1750',
        'i2c-addresses': ['0x23'],
        'i2c-address-change': False,
        'py-dependencies': ['smbus'],
        'measure': ['lux']},
    'BME280': {
        'name': 'BME280',
        'i2c-addresses': ['0x76'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_BME280'],
        'measure': ['altitude', 'dewpoint', 'humidity', 'pressure', 'temperature']},
    'BMP': {  # TODO: Remove in next major version. BMP180 replaced this name
        'name': 'BMP180',
        'i2c-addresses': ['0x77'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_BMP'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'BMP180': {
        'name': 'BMP180',
        'i2c-addresses': ['0x77'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_BMP'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'BMP280': {
        'name': 'BMP280',
        'i2c-addresses': ['0x77'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_GPIO'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'CHIRP': {
        'name': 'Chirp',
        'i2c-addresses': ['0x40'],
        'i2c-address-change': True,
        'py-dependencies': ['smbus'],
        'measure': ['lux', 'moisture', 'temperature']},
    'DHT11': {
        'name': 'DHT11',
        'py-dependencies': ['pigpio'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'DHT22': {
        'name': 'DHT22',
        'py-dependencies': ['pigpio'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'DS18B20': {
        'name': 'DS18B20',
        'py-dependencies': ['w1thermsensor'],
        'measure': ['temperature']},
    'EDGE': {
        'name': 'Edge',
        'py-dependencies': ['RPi.GPIO'],
        'measure': ['edge']},
    'GPIO_STATE': {
        'name': 'GPIO State',
        'py-dependencies': ['RPi.GPIO'],
        'measure': ['gpio_state']},
    'HTU21D': {
        'name': 'HTU21D',
        'i2c-addresses': ['0x40'],
        'i2c-address-change': False,
        'py-dependencies': ['pigpio'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'K30_UART': {
        'name': 'K-30 (Serial)',
        'py-dependencies': ['serial'],
        'measure': ['co2']},
    'LinuxCommand': {
        'name': 'Linux Command',
        'py-dependencies': [],
        'measure': []},
    'MAX31855': {
        'name': 'MAX13855K',
        'py-dependencies': ['Adafruit_MAX31855'],
        'measure': ['temperature', 'temperature_die']},
    'MAX31856': {
        'name': 'MAX31856',
        'py-dependencies': ['RPi.GPIO'],
        'measure': ['temperature', 'temperature_die']},
    'MAX31865': {
        'name': 'MAX31865',
        'py-dependencies': ['RPi.GPIO'],
        'measure': ['temperature']},
    'MH_Z16_I2C': {
        'name': 'MH-Z16 (I2C)',
        'i2c-addresses': ['0x63'],
        'i2c-address-change': False,
        'py-dependencies': ['smbus'],
        'measure': ['co2']},
    'MH_Z16_UART': {
        'name': 'MH-Z16 (Serial)',
        'py-dependencies': ['serial'],
        'measure': ['co2']},
    'MH_Z19_UART': {
        'name': 'MH-Z19 (Serial)',
        'py-dependencies': ['serial'],
        'measure': ['co2']},
    'MCP3008': {
        'name': 'MCP3008',
        'py-dependencies': ['Adafruit_MCP3008'],
        'measure': ['voltage']},
    'MCP342x': {
        'name': 'MCP342x',
        'i2c-addresses': ['0x68'],
        'i2c-address-change': False,
        'py-dependencies': ['MCP342x'],
        'measure': ['voltage']},
    'RPi': {
        'name': 'RPi CPU Temperature',
        'py-dependencies': [],
        'measure': ['temperature']},
    'RPiCPULoad': {
        'name': 'RPi CPU Load',
        'py-dependencies': [],
        'measure': ['cpu_load_1m', 'cpu_load_5m', 'cpu_load_15m']},
    'RPiFreeSpace': {
        'name': 'RPi Free Space',
        'py-dependencies': [],
        'measure': ['disk_space']},
    'SERVER_PING': {
        'name': 'Server Ping',
        'py-dependencies': [],
        'measure': ['boolean']},
    'SERVER_PORT_OPEN': {
        'name': 'Port Open',
        'py-dependencies': [],
        'measure': ['boolean']},
    'SHT1x_7x': {
        'name': 'SHT1x-7x',
        'py-dependencies': ['sht_sensor'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'SHT2x': {
        'name': 'SHT2x',
        'i2c-addresses': ['0x40'],
        'i2c-address-change': False,
        'py-dependencies': ['smbus'],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'SIGNAL_PWM': {
        'name': 'Signal (PWM)',
        'py-dependencies': ['pigpio'],
        'measure': ['frequency','pulse_width', 'duty_cycle']},
    'SIGNAL_RPM': {
        'name': 'Signal (RPM)',
        'py-dependencies': ['pigpio'],
        'measure': ['rpm']},
    'TMP006': {
        'name': 'TMP006',
        'py-dependencies': ['Adafruit_TMP'],
        'measure': ['temperature_object', 'temperature_die']},
    'TSL2561': {
        'name': 'TSL2561',
        'i2c-addresses': ['0x39'],
        'i2c-address-change': False,
        'py-dependencies': ['tsl2561'],
        'measure': ['lux']},
    'TSL2591': {
        'name': 'TSL2591',
        'i2c-addresses': ['0x29'],
        'i2c-address-change': False,
        'py-dependencies': ['tsl2591'],
        'measure': ['lux']}
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
        'py-dependencies': [],
        'measure': []},
    'average_single': {
        'name': 'Average (Single)',
        'py-dependencies': [],
        'measure': []},
    'difference': {
        'name': 'Difference',
        'py-dependencies': [],
        'measure': []},
    'equation': {
        'name': 'Equation',
        'py-dependencies': [],
        'measure': []},
    'median': {
        'name': 'Median',
        'py-dependencies': [],
        'measure': []},
    'maximum': {
        'name': 'Maximum',
        'py-dependencies': [],
        'measure': []},
    'minimum': {
        'name': 'Minimum',
        'py-dependencies': [],
        'measure': []},
    'humidity': {
        'name': 'Humidity (Wet-Bulb)',
        'py-dependencies': [],
        'measure': ['humidity', 'humidity_ratio', 'specific_enthalpy', 'specific_volume']},
    'verification': {
        'name': 'Verification',
        'py-dependencies': [],
        'measure': []}
}

# Method info
METHOD_INFO = {
    'DailyBezier': {
        'name': 'DailyBezier',
        'py-dependencies': ['numpy']}
}

# Math controllers
OUTPUTS = [
    ('wired', 'GPIO (On/Off)'),
    ('pwm', 'GPIO (PWM)'),
    ('command', 'Command (On/Off)'),
    ('command_pwm', 'Command (PWM)'),
    ('wireless_433MHz_pi_switch', 'Wireless (433MHz)')
]

# Output info
OUTPUT_INFO = {
    'wired': {
        'name': 'GPIO (On/Off)',
        'py-dependencies': [],
        'measure': []},
    'pwm': {
        'name': 'GPIO (PWM)',
        'py-dependencies': [],
        'measure': []},
    'wireless_433MHz_pi_switch': {
        'name': 'Wireless (433MHz)',
        'py-dependencies': ['rpi_rf'],
        'measure': []},
    'command': {
        'name': 'Command (On/Off)',
        'py-dependencies': [],
        'measure': []},
    'command_pwm': {
        'name': 'Command (PWM)',
        'py-dependencies': [],
        'measure': []},
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
    'electrical_conductivity': {
        'name': lazy_gettext('Electrical Conductivity'),
        'meas': 'electrical_conductivity', 'unit': 'μS/cm'},
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
    'ATLAS_EC_I2C',
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
    'MAX31855',
    'MAX31856',
    'MAX31865',
    'MCP3008'
]

# Devices that use serial to communicate
LIST_DEVICES_SERIAL = [
    'ATLAS_EC_UART',
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
    'RPiFreeSpace',
    'SERVER_PING',
    'SERVER_PORT_OPEN',
    'SIGNAL_PWM',
    'SIGNAL_RPM'
]

# Conditional Types
CONDITIONAL_TYPES = {
    'conditional_measurement': {
        'name': lazy_gettext('Measurement')},
    'conditional_output': {
        'name': lazy_gettext('Output')},
    'conditional_edge': {
        'name': lazy_gettext('Edge')},
}

# Conditional actions
# TODO: Some have been disabled until they can be properly tested
CONDITIONAL_ACTIONS = collections.OrderedDict([
    ('output', lazy_gettext('Output (Duration)')),
    ('output_pwm', lazy_gettext('Output (Duty Cycle)')),
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
USAGE_REPORTS_PATH = os.path.join(INSTALL_DIRECTORY, 'relay_usage_reports')
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
