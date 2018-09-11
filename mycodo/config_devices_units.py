# -*- coding: utf-8 -*-
#
#  config_units.py - Mycodo unit settings
#

from flask_babel import lazy_gettext


# Measurement information
# First unit in list is the default unit when Input is created
MEASUREMENTS = {
    'altitude': {
        'name': lazy_gettext('Altitude'),
        'meas': 'altitude',
        'units': ['m', 'ft']},
    'battery': {
        'name': lazy_gettext('Battery'),
        'meas': 'battery',
        'units': ['percent', 'decimal']},
    'boolean': {
        'name': lazy_gettext('Boolean'),
        'meas': 'boolean',
        'units': ['bool']},
    'co2': {
        'name': lazy_gettext('CO2'),
        'meas': 'co2',
        'units': ['ppm', 'ppb']},
    'cpu_load_1m': {
        'name': lazy_gettext('CPU Load 1 min'),
        'meas': 'cpu_load',
        'units': ['cpu_load']},
    'cpu_load_5m': {
        'name': lazy_gettext('CPU Load 5 min'),
        'meas': 'cpu_load',
        'units': ['cpu_load']},
    'cpu_load_15m': {
        'name': lazy_gettext('CPU Load 15 min'),
        'meas': 'cpu_load',
        'units': ['cpu_load']},
    'dewpoint': {
        'name': lazy_gettext('Dewpoint'),
        'meas': 'temperature',
        'units': ['C', 'F', 'K']},
    'disk_space': {
        'name': lazy_gettext('Disk'),
        'meas': 'disk_space',
        'units': ['MB', 'kB', 'GB']},
    'duration_time': {
        'name': lazy_gettext('Duration'),
        'meas': 'duration_time',
        'units': ['second']},
    'duty_cycle': {
        'name': lazy_gettext('Duty Cycle'),
        'meas': 'duty_cycle',
        'units': ['percent', 'decimal']},
    'edge': {
        'name': lazy_gettext('GPIO Edge'),
        'meas': 'edge',
        'units': ['bool']},
    'electrical_conductivity': {
        'name': lazy_gettext('Electrical Conductivity'),
        'meas': 'electrical_conductivity',
        'units': ['μS_cm']},
    'frequency': {
        'name': lazy_gettext('Frequency'),
        'meas': 'frequency',
        'units': ['Hz', 'kHz', 'MHz']},
    'gpio_state': {
        'name': lazy_gettext('GPIO State'),
        'meas': 'gpio_state',
        'units': ['bool']},
    'humidity': {
        'name': lazy_gettext('Humidity'),
        'meas': 'humidity',
        'units': ['percent', 'decimal']},
    'humidity_ratio': {
        'name': lazy_gettext('Humidity Ratio'),
        'meas': 'humidity_ratio',
        'units': ['kg_kg']},
    'ion_concentration': {
        'name': lazy_gettext('Ion Concentration'),
        'meas': 'ion_concentration',
        'units': ['pH']},
    'light': {
        'name': lazy_gettext('Light'),
        'meas': 'light',
        'units': ['lux']},
    'moisture': {
        'name': lazy_gettext('Moisture'),
        'meas': 'moisture',
        'units': ['unitless']},
    'particulate_matter_1_0': {
        'name': lazy_gettext('PM1'),
        'meas': 'particulate_matter_1_0',
        'units': ['μg_m3']},
    'particulate_matter_2_5': {
        'name': lazy_gettext('PM2.5'),
        'meas': 'particulate_matter_2_5',
        'units': ['μg_m3']},
    'particulate_matter_10_0': {
        'name': lazy_gettext('PM10'),
        'meas': 'particulate_matter_10_0',
        'units': ['μg_m3']},
    'pid_p_value': {
        'name': lazy_gettext('PID P-Value'),
        'meas': 'pid_value',
        'units': ['pid_value']},
    'pid_i_value': {
        'name': lazy_gettext('PID I-Value'),
        'meas': 'pid_value',
        'units': ['pid_value']},
    'pid_d_value': {
        'name': lazy_gettext('PID D-Value'),
        'meas': 'pid_value',
        'units': ['pid_value']},
    'pressure': {
        'name': lazy_gettext('Pressure'),
        'meas': 'pressure',
        'units': ['Pa', 'kPa']},
    'pulse_width': {
        'name': lazy_gettext('Pulse Width'),
        'meas': 'pulse_width',
        'units': ['µs']},
    'revolutions': {
        'name': lazy_gettext('Revolutions'),
        'meas': 'revolutions',
        'units': ['rpm']},
    'setpoint': {
        'name': lazy_gettext('Setpoint'),
        'meas': 'setpoint',
        'units': ['setpoint']},
    'setpoint_band_min': {
        'name': lazy_gettext('Band Min'),
        'meas': 'setpoint_band_min',
        'units': ['setpoint']},
    'setpoint_band_max': {
        'name': lazy_gettext('Band Max'),
        'meas': 'setpoint_band_max',
        'units': ['setpoint']},
    'specific_enthalpy': {
        'name': lazy_gettext('Specific Enthalpy'),
        'meas': 'specific_enthalpy',
        'units': ['kJ_kg']},
    'specific_volume': {
        'name': lazy_gettext('Specific Volume'),
        'meas': 'specific_volume',
        'units': ['m3_kg']},
    'temperature': {
        'name': lazy_gettext('Temperature'),
        'meas': 'temperature',
        'units': ['C', 'F', 'K']},
    'temperature_object': {
        'name': lazy_gettext('Temperature (Obj)'),
        'meas': 'temperature',
        'units': ['C', 'F', 'K']},
    'temperature_die': {
        'name': lazy_gettext('Temperature (Die)'),
        'meas': 'temperature',
        'units': ['C', 'F', 'K']},
    'voc': {
        'name': lazy_gettext('VOC'),
        'meas': 'voc',
        'units': ['ppb', 'ppm']},
    'voltage': {
        'name': lazy_gettext('Voltage'),
        'meas': 'voltage',
        'units': ['volts']},
}

# Measurement units
UNITS = {
    'unitless': {
        'name': '',
        'unit': ''},
    'µs': {
        'name': 'Microsecond',
        'unit': 'µs'},
    'μS_cm': {
        'name': 'Microsiemens per centimeter',
        'unit': 'μS/cm'},
    'bool': {
        'name': 'Boolean',
        'unit': 'bool'},
    'C': {
        'name': 'Celsius',
        'unit': '°C'},
    'cpu_load': {
        'name': 'CPU Load',
        'unit': ''},
    'decimal': {
        'name': 'Decimal',
        'unit': ''},
    'F': {
        'name': 'Fahrenheit',
        'unit': '°F'},
    'ft': {
        'name': 'Feet',
        'unit': 'ft'},
    'GB': {
        'name': 'Gigabyte',
        'unit': 'GB'},
    'Hz': {
        'name': 'Hertz',
        'unit': 'Hz'},
    'K': {
        'name': 'Kelvin',
        'unit': '°K'},
    'kB': {
        'name': 'Kilobyte',
        'unit': 'kB'},
    'kg_kg': {
        'name': 'Kilogram per kilogram',
        'unit': 'kg/kg'},
    'kHz': {
        'name': 'Kilohertz',
        'unit': 'kHz'},
    'kJ_kg': {
        'name': 'Kilojoule per kilogram',
        'unit': 'kJ/kg'},
    'kPa': {
        'name': 'Kilopascals',
        'unit': 'kPa'},
    'lux': {
        'name': 'Lux',
        'unit': 'lx'},
    'm': {
        'name': 'Meters',
        'unit': 'm'},
    'm3_kg': {
        'name': 'Cubic meters per kilogram',
        'unit': 'm^3/kg'},
    'MHz': {
        'name': 'Megahertz',
        'unit': 'MHz'},
    'MB': {
        'name': 'Megabyte',
        'unit': 'MB'},
    'minute': {
        'name': 'Minute',
        'unit': 'm'},
    'Pa': {
        'name': 'Pascals',
        'unit': 'Pa'},
    'percent': {
        'name': 'Percent',
        'unit': '%'},
    'pH': {
        'name': 'pH',
        'unit': 'pH'},
    'pid_value': {
        'name': 'PID values',
        'unit': ''},
    'ppb': {
        'name': 'Parts per billion',
        'unit': 'ppb'},
    'ppm': {
        'name': 'Parts per million',
        'unit': 'ppm'},
    'rpm': {
        'name': 'RPM',
        'unit': 'Revolutions per minute'},
    'second': {
        'name': 'Second',
        'unit': 's'},
    'setpoint': {
        'name': 'Setpoint',
        'unit': ''},
    'μg_m3': {
        'name': 'Microgram per cubic meter',
        'unit': 'μg/m^3'},
    'volts': {
        'name': 'Volts',
        'unit': 'V'}
}

# Supported conversions
UNIT_CONVERSIONS = {
    # Temperature
    'C_to_F': 'x*(9/5)+32',
    'C_to_K': 'x+273.15',
    'F_to_C': '(x-32)*5/9',
    'F_to_K': '(x+459.67)*5/9',
    'K_to_C': 'x-273.15',
    'K_to_F': '(x*9/5)−459.67',

    # Frequency
    'Hz_to_kHz': 'x/1000',
    'Hz_to_MHz': 'x/1000000',
    'kHz_to_Hz': 'x*1000',
    'kHz_to_MHz': 'x/1000',
    'MHz_to_Hz': 'x*1000000',
    'MHz_to_kHz': 'x*1000',

    # Length
    'm_to_ft': 'x*3.2808399',
    'ft_to_m': 'x/3.2808399',

    # Disk size
    'kB_to_MB': 'x/1000',
    'kB_to_GB': 'x/1000000',
    'MB_to_kB': 'x*1000',
    'MB_to_GB': 'x/1000',
    'GB_to_kB': 'x*1000000',
    'GB_to_MB': 'X*1000',

    # Concentration
    'ppm_to_ppb': 'x*1000',
    'ppb_to_ppm': 'x/1000',

    # Number
    'percent_to_decimal': 'x/100',
    'decimal_to_percent': 'x*100',

    # Pressure
    'Pa_to_kPa': 'x/1000',
    'kPa_to_Pa': 'x*1000',

    # Time
    'second_to_minute': 'x/60',
    'minute_to_second': 'x*60'
}
