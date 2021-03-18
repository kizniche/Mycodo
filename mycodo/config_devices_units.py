# -*- coding: utf-8 -*-
#
#  config_devices_units.py - Mycodo device unit settings
#

from flask_babel import lazy_gettext


# Measurement information
# First unit in list is the default unit when Input is created
MEASUREMENTS = {
    'acceleration': {
        'name': lazy_gettext('Acceleration'),
        'meas': 'acceleration',
        'units': ['g_force', 'm_s_s']},
    'acceleration_x': {
        'name': lazy_gettext('Acceleration (X)'),
        'meas': 'acceleration_x',
        'units': ['g_force', 'm_s_s']},
    'acceleration_y': {
        'name': lazy_gettext('Acceleration (Y)'),
        'meas': 'acceleration_y',
        'units': ['g_force', 'm_s_s']},
    'acceleration_z': {
        'name': lazy_gettext('Acceleration (Z)'),
        'meas': 'acceleration_z',
        'units': ['g_force', 'm_s_s']},
    'adc': {
        'name': lazy_gettext('ADC'),
        'meas': 'adc',
        'units': ['none']},
    'altitude': {
        'name': lazy_gettext('Altitude'),
        'meas': 'altitude',
        'units': ['m', 'ft']},
    'angle': {
        'name': lazy_gettext('Angle'),
        'meas': 'angle',
        'units': ['degree']},
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
        'units': ['ppm', 'ppb', 'percent']},
    'color_red': {
        'name': lazy_gettext('Color (Red)'),
        'meas': 'color_red',
        'units': ['eight_bit_color']},
    'color_green': {
        'name': lazy_gettext('Color (Green)'),
        'meas': 'color_green',
        'units': ['eight_bit_color']},
    'color_blue': {
        'name': lazy_gettext('Color (Blue)'),
        'meas': 'color_blue',
        'units': ['eight_bit_color']},
    'color_x': {
        'name': lazy_gettext('Color (x)'),
        'meas': 'color_x',
        'units': ['cie']},
    'color_y': {
        'name': lazy_gettext('Color (y)'),
        'meas': 'color_y',
        'units': ['cie']},
    'color_Y': {
        'name': lazy_gettext('Color (Y)'),
        'meas': 'color_Y',
        'units': ['cie']},
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
    'direction': {
        'name': lazy_gettext('Direction'),
        'meas': 'direction',
        'units': ['bearing']},
    'disk_space': {
        'name': lazy_gettext('Disk'),
        'meas': 'disk_space',
        'units': ['MB', 'kB', 'GB']},
    'dissolved_oxygen': {
        'name': lazy_gettext('Dissolved Oxygen'),
        'meas': 'dissolved_oxygen',
        'units': ['mg_L']},
    'duration_time': {
        'name': lazy_gettext('Duration'),
        'meas': 'duration_time',
        'units': ['s', 'minute', 'h']},
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
        'units': ['uS_cm']},
    'electrical_current': {
        'name': lazy_gettext('Electrical Current'),
        'meas': 'electrical_current',
        'units': ['A', 'mA']},
    'electrical_potential': {
        'name': lazy_gettext('Electrical Potential'),
        'meas': 'electrical_potential',
        'units': ['V', 'mV']},
    'energy': {
        'name': lazy_gettext('Energy'),
        'meas': 'energy',
        'units': ['kWh']},
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
    'length': {
        'name': lazy_gettext('Length'),
        'meas': 'length',
        'units': ['ft', 'cm', 'm', 'mm']},
    'light': {
        'name': lazy_gettext('Light'),
        'meas': 'light',
        'units': ['full', 'ir', 'lux']},
    'magnetic_flux_density': {
        'name': lazy_gettext('Magnetic Flux Density'),
        'meas': 'magnetic_flux_density',
        'units': ['uT']},
    'moisture': {
        'name': lazy_gettext('Moisture'),
        'meas': 'moisture',
        'units': ['none']},
    'oxidation_reduction_potential': {
        'name': lazy_gettext('Oxidation Reduction Potential'),
        'meas': 'oxidation_reduction_potential',
        'units': ['mV', 'V']},
    'particulate_matter_1_0': {
        'name': 'PM1',
        'meas': 'particulate_matter_1_0',
        'units': ['ug_m3']},
    'particulate_matter_2_5': {
        'name': 'PM2.5',
        'meas': 'particulate_matter_2_5',
        'units': ['ug_m3']},
    'particulate_matter_10_0': {
        'name': 'PM10',
        'meas': 'particulate_matter_10_0',
        'units': ['ug_m3']},
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
    'power': {
        'name': lazy_gettext('Power'),
        'meas': 'power',
        'units': ['W']},
    'pressure': {
        'name': lazy_gettext('Pressure'),
        'meas': 'pressure',
        'units': ['cm_water', 'psi', 'hPa', 'Pa', 'kPa']},
    'pulse_width': {
        'name': lazy_gettext('Pulse Width'),
        'meas': 'pulse_width',
        'units': ['us']},
    'radiation_dose_rate': {
        'name': lazy_gettext('Radiation Dose Rate'),
        'meas': 'radiation_dose_rate',
        'units': ['cpm', 'uSv_hr']},
    'rate_volume': {
        'name': lazy_gettext('Volume Flow Rate'),
        'meas': 'rate_volume',
        'units': ['l_hr', 'l_min', 'l_s']},
    'resistance': {
        'name': lazy_gettext('Resistance'),
        'meas': 'resistance',
        'units': ['Ohm']},
    'rotation': {
        'name': lazy_gettext('Rotation'),
        'meas': 'rotation',
        'units': ['steps']},
    'revolutions': {  # TODO: Move revolutions to rotations
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
    'speed': {
        'name': lazy_gettext('Speed'),
        'meas': 'speed',
        'units': ['m_s', 'mph', 'kn']},
    'temperature': {
        'name': lazy_gettext('Temperature'),
        'meas': 'temperature',
        'units': ['C', 'F', 'K']},
    'unitless': {
        'name': lazy_gettext('Unitless'),
        'meas': 'unitless',
        'units': ['none']},
    'vapor_pressure_deficit': {
        'name': lazy_gettext('Vapor Pressure Deficit'),
        'meas': 'vapor_pressure_deficit',
        'units': ['hPa', 'Pa', 'kPa']},
    'version': {
        'name': lazy_gettext('Version'),
        'meas': 'version',
        'units': ['none']},
    'voc': {
        'name': lazy_gettext('VOC'),
        'meas': 'voc',
        'units': ['ppb', 'ppm']},
    'volume': {
        'name': lazy_gettext('Volume'),
        'meas': 'volume',
        'units': ['l', 'ml']}
}

# Measurement units
UNITS = {
    'unitless': {  # TODO: This unit and "none" are redundant. remove one.
        'name': '',
        'unit': ''},
    'us': {
        'name': lazy_gettext('Microsecond'),
        'unit': 'µs'},
    'uS_cm': {
        'name': lazy_gettext('Microsiemens per centimeter'),
        'unit': 'μS/cm'},
    'uSv_hr': {
        'name': lazy_gettext('Microsieverts per hour'),
        'unit': 'μSv/hr'},
    'A': {
        'name': lazy_gettext('Amp'),
        'unit': 'A'},
    'bearing': {
        'name': lazy_gettext('Bearing'),
        'unit': 'bearing'},
    'bool': {
        'name': lazy_gettext('Boolean'),
        'unit': 'bool'},
    'C': {
        'name': lazy_gettext('Celsius'),
        'unit': '°C'},
    'cie': {
        'name': lazy_gettext('CIE'),
        'unit': 'cie'},
    'cm': {
        'name': lazy_gettext('Centimeter'),
        'unit': 'cm'},
    'cm_water': {
        'name': lazy_gettext('Centimeters of water'),
        'unit': 'cm_water'},
    'cpm': {
        'name': lazy_gettext('Counts per minute'),
        'unit': 'cpm'},
    'cpu_load': {
        'name': lazy_gettext('CPU Load'),
        'unit': 'Proc.'},
    'decimal': {
        'name': lazy_gettext('Decimal'),
        'unit': ''},
    'degree': {
        'name': lazy_gettext('Degree'),
        'unit': '°'},
    'eight_bit_color': {
        'name': lazy_gettext('8-Bit Color'),
        'unit': '8-bit'},
    'F': {
        'name': lazy_gettext('Fahrenheit'),
        'unit': '°F'},
    'ft': {
        'name': lazy_gettext('Foot'),
        'unit': 'ft'},
    'full': {
        'name': lazy_gettext('Full'),
        'unit': 'full'},
    'g_force': {
        'name': lazy_gettext('G-Force'),
        'unit': 'g'},
    'GB': {
        'name': lazy_gettext('Gigabyte'),
        'unit': 'GB'},
    'h': {
        'name': lazy_gettext('Hour'),
        'unit': 'h'},
    'hPa': {
        'name': lazy_gettext('Hectopascals'),
        'unit': 'hPa'},
    'Hz': {
        'name': lazy_gettext('Hertz'),
        'unit': 'Hz'},
    'ir': {
        'name': lazy_gettext('Infrared'),
        'unit': 'IR'},
    'K': {
        'name': lazy_gettext('Kelvin'),
        'unit': '°K'},
    'kB': {
        'name': lazy_gettext('Kilobyte'),
        'unit': 'kB'},
    'kg_kg': {
        'name': lazy_gettext('Kilogram per kilogram'),
        'unit': 'kg/kg'},
    'kHz': {
        'name': lazy_gettext('Kilohertz'),
        'unit': 'kHz'},
    'kJ_kg': {
        'name': lazy_gettext('Kilojoule per kilogram'),
        'unit': 'kJ/kg'},
    'kn': {
        'name': lazy_gettext('Knot'),
        'unit': 'knot'},
    'kPa': {
        'name': lazy_gettext('Kilopascal'),
        'unit': 'kPa'},
    'kWh': {
        'name': lazy_gettext('Kilowatt-hour'),
        'unit': 'kWh'},
    'l': {
        'name': lazy_gettext('Liter'),
        'unit': 'l'},
    'l_hr': {
        'name': lazy_gettext('Liters per Hour'),
        'unit': 'l/hr'},
    'l_min': {
        'name': lazy_gettext('Liters per Minute'),
        'unit': 'l/min'},
    'l_s': {
        'name': lazy_gettext('Liters Per Second'),
        'unit': 'l/s'},
    'lux': {
        'name': lazy_gettext('Lux'),
        'unit': 'lx'},
    'm': {
        'name': lazy_gettext('Meter'),
        'unit': 'm'},
    'm_s': {
        'name': lazy_gettext('Meters per second'),
        'unit': 'm/s'},
    'm_s_s': {
        'name': lazy_gettext('Meters per second per second'),
        'unit': 'm/s/s'},
    'mg_L': {
        'name': lazy_gettext('Milligram per Liter'),
        'unit': 'mg/L'},
    'minute': {
        'name': lazy_gettext('Minute'),
        'unit': 'min'},
    'mA': {
        'name': lazy_gettext('Milliamp'),
        'unit': 'mA'},
    'ml': {
        'name': lazy_gettext('Milliliter'),
        'unit': 'ml'},
    'mm': {
        'name': lazy_gettext('Millimeter'),
        'unit': 'mm'},
    'mph': {
        'name': lazy_gettext('Miles per hour'),
        'unit': 'mph'},
    'mV': {
        'name': lazy_gettext('Millivolt'),
        'unit': 'mV'},
    'm3_kg': {
        'name': lazy_gettext('Cubic meters per kilogram'),
        'unit': 'm^3/kg'},
    'MHz': {
        'name': lazy_gettext('Megahertz'),
        'unit': 'MHz'},
    'MB': {
        'name': lazy_gettext('Megabyte'),
        'unit': 'MB'},
    'none': {
        'name': lazy_gettext('Unitless'),
        'unit': ''},
    'Ohm': {
        'name': lazy_gettext('Ohm'),
        'unit': 'Ω'},
    'Pa': {
        'name': lazy_gettext('Pascal'),
        'unit': 'Pa'},
    'percent': {
        'name': lazy_gettext('Percent'),
        'unit': '%'},
    'pH': {
        'name': lazy_gettext('Ion Concentration'),
        'unit': 'pH'},
    'pid_value': {
        'name': lazy_gettext('PID values'),
        'unit': ''},
    'ppb': {
        'name': lazy_gettext('Parts per billion'),
        'unit': 'ppb'},
    'ppm': {
        'name': lazy_gettext('Parts per million'),
        'unit': 'ppm'},
    'psi': {
        'name': lazy_gettext('Pounds per square inch'),
        'unit': 'psi'},
    'rpm': {
        'name': lazy_gettext('Revolutions per minute'),
        'unit': 'rpm'},
    's': {
        'name': lazy_gettext('Second'),
        'unit': 's'},
    'setpoint': {
        'name': lazy_gettext('Setpoint'),
        'unit': ''},
    'steps': {
        'name': lazy_gettext('Steps'),
        'unit': 'steps'},
    'ug_m3': {
        'name': lazy_gettext('Microgram per cubic meter'),
        'unit': 'μg/m^3'},
    'uT': {
        'name': lazy_gettext('Microtesla'),
        'unit': 'μT'},
    'V': {
        'name': lazy_gettext('Volt'),
        'unit': 'V'},
    'W': {
        'name': lazy_gettext('Watt'),
        'unit': 'W'}
}

# Initial conversions
# These are added to the SQLite database when it's created
# Users may add or delete after that
UNIT_CONVERSIONS = [
    # Speed
    ('m_s', 'mph', 'x*2.2369362920544'),
    ('m_s', 'kn', 'x*1.9438444924406'),
    ('mph', 'm_s', 'x/2.2369362920544'),
    ('mph', 'kn', 'x/1.1507794480235'),
    ('kn', 'm_s', 'x/1.9438444924406'),
    ('kn', 'mph', 'x*1.1507794480235'),

    # Acceleration
    ('g_force', 'm_s_s', 'x*9.80665'),
    ('m_s_s', 'g_force', 'x/9.80665'),

    # Temperature
    ('C', 'F', 'x*(9/5)+32'),
    ('C', 'K', 'x+273.15'),
    ('F', 'C', '(x-32)*5/9'),
    ('F', 'K', '(x+459.67)*5/9'),
    ('K', 'C', 'x-273.15'),
    ('K', 'F', '(x*9/5)−459.67'),

    # Frequency
    ('Hz', 'kHz', 'x/1000'),
    ('Hz', 'MHz', 'x/1000000'),
    ('kHz', 'Hz', 'x*1000'),
    ('kHz', 'MHz', 'x/1000'),
    ('MHz', 'Hz', 'x*1000000'),
    ('MHz', 'kHz', 'x*1000'),

    # Length
    ('ft', 'm', 'x/3.2808399'),
    ('m', 'ft', 'x*3.2808399'),
    ('m', 'cm', 'x*100'),
    ('m', 'mm', 'x*1000'),
    ('mm', 'cm', 'x/10'),
    ('mm', 'm', 'x/1000'),
    ('cm', 'mm', 'x*10'),
    ('cm', 'm', 'x/100'),

    # Disk size
    ('kB', 'MB', 'x/1000'),
    ('kB', 'GB', 'x/1000000'),
    ('MB', 'kB', 'x*1000'),
    ('MB', 'GB', 'x/1000'),
    ('GB', 'kB', 'x*1000000'),
    ('GB', 'MB', 'X*1000'),

    # Concentration
    ('ppm', 'ppb', 'x*1000'),
    ('ppb', 'ppm', 'x/1000'),
    ('ppm', 'percent', 'x/10000'),
    ('ppb', 'percent', 'x/10000000'),
    ('percent', 'ppm', 'x*10000'),
    ('percent', 'ppb', 'x*10000000'),

    # Number
    ('percent', 'decimal', 'x/100'),
    ('decimal', 'percent', 'x*100'),

    # Pressure
    ('Pa', 'kPa', 'x*1000'),
    ('Pa', 'hPa', 'x/100'),
    ('hPa', 'Pa', 'x*100'),
    ('hPa', 'kPa', 'x/10'),
    ('kPa', 'Pa', 'x/1000'),
    ('kPa', 'hPa', 'x*10'),
    ('psi', 'cm_water', 'x*70.306957964239'),
    ('psi', 'kPa', 'x*6.8947572932'),
    ('kPa', 'psi', 'x/6.8947572932'),

    # Rate - Volume
    ('l_s', 'l_min', 'x*60'),
    ('l_s', 'l_hr', 'x*60*60'),
    ('l_min', 'l_s', 'x/60'),
    ('l_min', 'l_hr', 'x*60'),
    ('l_hr', 'l_s', 'x/60/60'),
    ('l_hr', 'l_min', 'x/60'),

    # Time
    ('s', 'minute', 'x/60'),
    ('s', 'h', 'x/60/60'),
    ('minute', 's', 'x*60'),
    ('minute', 'h', 'x/60'),
    ('h', 's', 'x*60*60'),
    ('h', 'minute', 'x*60'),

    # Volt
    ('V', 'mV', 'x*1000'),
    ('mV', 'V', 'x/1000'),

    # Electrical Current
    ('A', 'mA', 'x*1000'),
    ('mA', 'A', 'x/1000'),

    # Volume
    ('l', 'ml', 'x*1000'),
    ('ml', 'l', 'x/1000')
]
