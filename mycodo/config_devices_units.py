# -*- coding: utf-8 -*-
#
#  config_units.py - Mycodo unit settings
#

from flask_babel import lazy_gettext


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
    ('COZIR_CO2', 'CO2/Temperature/Humidity: COZIR (Serial)'),
    ('K30_UART', 'CO2: K30 (Serial)'),
    ('MH_Z16_I2C', 'CO2: MH-Z16 (I2C)'),
    ('MH_Z16_UART', 'CO2: MH-Z16 (Serial)'),
    ('MH_Z19_UART', 'CO2: MH-Z19 (Serial)'),
    ('CCS811', 'CO2/VOC/Temperature: CCS811 (I2C)'),
    ('ATLAS_EC_I2C', 'Electrical Conductivity: Atlas Scientific (I2C)'),
    ('ATLAS_EC_UART', 'Electrical Conductivity: Atlas Scientific (Serial)'),
    ('BH1750', 'Luminance: BH1750 (I2C)'),
    ('TSL2561', 'Luminance: TSL2561 (I2C)'),
    ('TSL2591', 'Luminance: TSL2591 (I2C)'),
    ('CHIRP', 'Moisture/Temperature/Light: Chirp (I2C)'),
    ('MIFLORA', 'Moisture/Temperature/Light/EC: Miflora (Bluetooth)'),
    ('ATLAS_PH_I2C', 'pH: Atlas Scientific (I2C)'),
    ('ATLAS_PH_UART', 'pH: Atlas Scientific (Serial)'),
    ('BMP180', 'Pressure/Temperature: BMP 180/085 (I2C)'),
    ('BMP280', 'Pressure/Temperature: BMP 280 (I2C)'),
    ('BME280', 'Pressure/Temperature/Humidity: BME 280 (I2C)'),
    ('DS18B20', 'Temperature: DS18B20 (1-Wire)'),
    ('DS18S20', 'Temperature: DS18S20 (1-Wire)'),
    ('DS1822', 'Temperature: DS1822 (1-Wire)'),
    ('DS28EA00', 'Temperature: DS28EA00 (1-Wire)'),
    ('DS1825', 'Temperature: DS1825 (1-Wire)'),
    ('ATLAS_PT1000_I2C', 'Temperature: Atlas Scientific PT-1000 (I2C)'),
    ('ATLAS_PT1000_UART', 'Temperature: Atlas Scientific PT-1000 (Serial)'),
    ('MAX31850K', 'Temperature: MAX31850K + K-type thermocouple'),
    ('MAX31855', 'Temperature: MAX31855K + K-type thermocouple'),
    ('MAX31856', 'Temperature: MAX31856 + K/J/N/R/S/T/E/B-type thermocouple'),
    ('MAX31865', 'Temperature: MAX31865 + PT100 or PT1000 probe'),
    ('TMP006', 'Temperature (Contactless): TMP 006/007 (I2C)'),
    ('AM2315', 'Temperature/Humidity: AM2315 (I2C)'),
    ('DHT11', 'Temperature/Humidity: DHT11 (GPIO)'),
    ('DHT22', 'Temperature/Humidity: DHT22 (GPIO)'),
    ('HDC1000', 'Temperature/Humidity: HDC1000/HDC1080 (I2C)'),
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
        'py-dependencies': ['Adafruit_ADS1x15', 'Adafruit_GPIO'],
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
        'measure': ['light']},
    'BME280': {
        'name': 'BME280',
        'i2c-addresses': ['0x76'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_BME280', 'Adafruit_GPIO'],
        'measure': ['altitude', 'dewpoint', 'humidity', 'pressure', 'temperature']},
    'BMP180': {
        'name': 'BMP180',
        'i2c-addresses': ['0x77'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_BMP', 'Adafruit_GPIO'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'BMP280': {
        'name': 'BMP280',
        'i2c-addresses': ['0x77'],
        'i2c-address-change': False,
        'py-dependencies': ['Adafruit_GPIO'],
        'measure': ['altitude', 'pressure', 'temperature']},
    'CCS811': {
        'name': 'CCS811',
        'i2c-addresses': ['0x5A', '0x5B'],
        'i2c-address-change': True,
        'py-dependencies': ['Adafruit_CCS811', 'Adafruit_GPIO'],
        'measure': ['co2', 'voc', 'temperature']},
    'CHIRP': {
        'name': 'Chirp',
        'i2c-addresses': ['0x40'],
        'i2c-address-change': True,
        'py-dependencies': ['smbus'],
        'measure': ['light', 'moisture', 'temperature']},
    'COZIR_CO2': {
        'name': 'COZIR',
        'py-dependencies': ['cozir'],
        'measure': ['co2', 'humidity', 'temperature']},
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
    'DS18S20': {
        'name': 'DS18S20',
        'py-dependencies': ['w1thermsensor'],
        'measure': ['temperature']},
    'DS1822': {
        'name': 'DS1822',
        'py-dependencies': ['w1thermsensor'],
        'measure': ['temperature']},
    'DS1825': {
        'name': 'DS1825',
        'py-dependencies': ['w1thermsensor'],
        'measure': ['temperature']},
    'DS28EA00': {
        'name': 'DS28EA00',
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
    'HDC1000': {
        'name': 'HDC1000',
        'i2c-addresses': ['0x40'],
        'i2c-address-change': False,
        'py-dependencies': [],
        'measure': ['dewpoint', 'humidity', 'temperature']},
    'K30_UART': {
        'name': 'K-30 (Serial)',
        'py-dependencies': ['serial'],
        'measure': ['co2']},
    'LinuxCommand': {
        'name': 'Linux Command',
        'py-dependencies': [],
        'measure': []},
    'MAX31850K': {
        'name': 'MAX31850K',
        'py-dependencies': ['w1thermsensor'],
        'measure': ['temperature']},
    'MAX31855': {
        'name': 'MAX13855K',
        'py-dependencies': ['Adafruit_MAX31855', 'Adafruit_GPIO'],
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
    'MIFLORA': {
        'name': 'MiFlora',
        'py-dependencies': ['miflora', 'bluepy', 'btlewrap'],
        'measure': ['battery', 'electrical_conductivity', 'light', 'moisture', 'temperature']},
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
        'measure': ['light']},
    'TSL2591': {
        'name': 'TSL2591',
        'i2c-addresses': ['0x29'],
        'i2c-address-change': False,
        'py-dependencies': ['tsl2591'],
        'measure': ['light']}
}


# Measurement information
# First unit in list is the default unit when Input is created
MEASUREMENT_UNITS = {
    'altitude': {
        'name': lazy_gettext('Altitude'),
        'meas': 'altitude',
        'units': ['m', 'ft']},
    'battery': {
        'name': lazy_gettext('Battery'),
        'meas': 'battery',
        'units': ['percent']},
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
        'units': ['unitless']},
    'cpu_load_5m': {
        'name': lazy_gettext('CPU Load 5 min'),
        'meas': 'cpu_load',
        'units': ['unitless']},
    'cpu_load_15m': {
        'name': lazy_gettext('CPU Load 15 min'),
        'meas': 'cpu_load',
        'units': ['unitless']},
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
        'units': ['second', 'minute']},
    'duty_cycle': {
        'name': lazy_gettext('Duty Cycle'),
        'meas': 'duty_cycle',
        'units': ['unitless']},
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
        'units': ['percent']},
    'humidity_ratio': {
        'name': lazy_gettext('Humidity Ratio'),
        'meas': 'humidity_ratio',
        'units': ['kg_kg']},
    'light': {
        'name': lazy_gettext('Light'),
        'meas': 'light',
        'units': ['lux']},
    'moisture': {
        'name': lazy_gettext('Moisture'),
        'meas': 'moisture',
        'units': ['moisture']},
    'ph': {
        'name': lazy_gettext('pH'),
        'meas': 'ph',
        'units': ['pH']},
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
    'rpm': {
        'name': lazy_gettext('Revolutions Per Minute'),
        'meas': 'rpm',
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
    'C': {
        'name': 'Celsius',
        'unit': '°C'},
    'cpu_load': {
        'name': 'CPU Load',
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
    'moisture': {
        'name': 'Moisture',
        'unit': ''},
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
        'unit': 'RPM'},
    'second': {
        'name': 'Second',
        'unit': 's'},
    'setpoint': {
        'name': 'Setpoint',
        'unit': ''},
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

    # Pressure
    'Pa_to_kPa': 'x/1000',
    'kPa_to_Pa': 'x*1000'
}
