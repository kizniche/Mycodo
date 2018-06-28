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
        'measure': ['lux']},
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
        'measure': ['lux', 'moisture', 'temperature']},
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
        'measure': ['battery', 'electrical_conductivity', 'lux', 'moisture', 'temperature']},
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


# Measurement information
MEASUREMENT_UNITS = {
    'altitude': {
        'name': lazy_gettext('Altitude'),
        'meas': 'altitude',
        'unit': 'm',
        'units': ['feet', 'meters']},
    'battery': {
        'name': lazy_gettext('Battery'),
        'meas': 'battery',
        'unit': '%'},
    'boolean': {
        'name': lazy_gettext('Boolean'),
        'meas': 'boolean',
        'unit': ''},
    'co2': {
        'name': lazy_gettext('CO2'),
        'meas': 'co2',
        'unit': 'ppm',
        'units': ['ppb', 'ppm']},
    'cpu_load': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load',
        'unit': ''},
    'cpu_load_1m': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load',
        'unit': '1 min'},
    'cpu_load_5m': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load',
        'unit': '5 min'},
    'cpu_load_15m': {
        'name': lazy_gettext('CPU Load'),
        'meas': 'cpu_load',
        'unit': '15 min'},
    'dewpoint': {
        'name': lazy_gettext('Dewpoint'),
        'meas': 'temperature',
        'unit': '°C',
        'units': ['celsius', 'fahrenheit', 'kelvin']},
    'disk_space': {
        'name': lazy_gettext('Disk'),
        'meas': 'disk_space',
        'unit': 'MB'},
    'duration_sec': {
        'name': lazy_gettext('Duration'),
        'meas': 'duration_sec',
        'unit': 'sec'},
    'duty_cycle': {
        'name': lazy_gettext('Duty Cycle'),
        'meas': 'duty_cycle',
        'unit': '%'},
    'edge': {
        'name': lazy_gettext('GPIO Edge'),
        'meas': 'edge',
        'unit': ''},
    'electrical_conductivity': {
        'name': lazy_gettext('Electrical Conductivity'),
        'meas': 'electrical_conductivity',
        'unit': 'μS/cm'},
    'frequency': {
        'name': lazy_gettext('Frequency'),
        'meas': 'frequency',
        'unit': 'Hz'},
    'gpio_state': {
        'name': lazy_gettext('GPIO State'),
        'meas': 'gpio_state',
        'unit': ''},
    'humidity': {
        'name': lazy_gettext('Humidity'),
        'meas': 'humidity',
        'unit': '%'},
    'humidity_ratio': {
        'name': lazy_gettext('Humidity Ratio'),
        'meas': 'humidity_ratio',
        'unit': 'kg/kg'},
    'lux': {
        'name': lazy_gettext('Light'),
        'meas': 'lux',
        'unit': 'lx'},
    'moisture': {
        'name': lazy_gettext('Moisture'),
        'meas': 'moisture',
        'unit': 'moisture'},
    'ph': {
        'name': lazy_gettext('pH'),
        'meas': 'ph',
        'unit': 'pH'},
    'pid_value': {
        'name': lazy_gettext('PID Values'),
        'meas': 'pid_value',
        'unit': ''},
    'pid_p_value': {
        'name': lazy_gettext('PID P-Value'),
        'meas': 'pid_value',
        'unit': ''},
    'pid_i_value': {
        'name': lazy_gettext('PID I-Value'),
        'meas': 'pid_value',
        'unit': ''},
    'pid_d_value': {
        'name': lazy_gettext('PID D-Value'),
        'meas': 'pid_value',
        'unit': ''},
    'pressure': {
        'name': lazy_gettext('Pressure'),
        'meas': 'pressure',
        'unit': 'Pa',
        'units': ['pascals', 'kilopascals']},
    'pulse_width': {
        'name': lazy_gettext('Pulse Width'),
        'meas': 'pulse_width',
        'unit': 'µs'},
    'rpm': {
        'name': lazy_gettext('Revolutions Per Minute'),
        'meas': 'rpm',
        'unit': 'rpm'},
    'setpoint': {
        'name': lazy_gettext('Setpoint'),
        'meas': 'setpoint', 'unit': ''},
    'setpoint_band_min': {
        'name': lazy_gettext('Band Min'),
        'meas': 'setpoint_band_min',
        'unit': ''},
    'setpoint_band_max': {
        'name': lazy_gettext('Band Max'),
        'meas': 'setpoint_band_max',
        'unit': ''},
    'specific_enthalpy': {
        'name': lazy_gettext('Specific Enthalpy'),
        'meas': 'specific_enthalpy',
        'unit': 'kJ/kg'},
    'specific_volume': {
        'name': lazy_gettext('Specific Volume'),
        'meas': 'specific_volume',
        'unit': 'm^3/kg'},
    'temperature': {
        'name': lazy_gettext('Temperature'),
        'meas': 'temperature',
        'unit': '°C',
        'units': ['celsius', 'fahrenheit', 'kelvin']},
    'temperature_object': {
        'name': lazy_gettext('Temperature (Obj)'),
        'meas': 'temperature',
        'unit': '°C',
        'units': ['celsius', 'fahrenheit', 'kelvin']},
    'temperature_die': {
        'name': lazy_gettext('Temperature (Die)'),
        'meas': 'temperature', 'unit': '°C',
        'units': ['celsius', 'fahrenheit', 'kelvin']},
    'voc': {
        'name': lazy_gettext('VOC'),
        'meas': 'voc',
        'unit': 'ppb',
        'units': ['ppb', 'ppm']},
    'voltage': {
        'name': lazy_gettext('Voltage'),
        'meas': 'voltage',
        'unit': 'volts'},
}

# Measurement units
UNITS = {
    'celsius': {
        'name': 'Celsius',
        'unit': '°C'},
    'fahrenheit': {
        'name': 'Fahrenheit',
        'unit': '°F'},
    'feet': {
        'name': 'Feet',
        'unit': 'ft'},
    'kelvin': {
        'name': 'Kelvin',
        'unit': '°K'},
    'pascals': {
        'name': 'Pascals',
        'unit': 'Pa'},
    'kilopascals': {
        'name': 'kiloPascals',
        'unit': 'kPa'},
    'meters': {
        'name': 'Meters',
        'unit': 'm'},
    'ppm': {
        'name': 'Parts Per Million',
        'unit': 'ppm'},
    'ppb': {
        'name': 'Parts Per Billion',
        'unit': 'ppb'}
}

# Supported conversions
UNIT_CONVERSIONS = {
    'celsius_to_fahrenheit': 'x*(9/5)+32',
    'celsius_to_kelvin': 'x+274.15',
    'meters_to_feet': 'x*3.2808399',
    'ppm_to_ppb': 'x*1000',
    'ppb_to_ppm': 'x/1000',
    'pascals_to_kilopascals': 'x/1000',
    'kilopascals_to_pascals': 'x*1000'
}
