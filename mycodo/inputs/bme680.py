# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

def constraints_pass_oversample(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: string
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['OS_NONE', 'OS_1X', 'OS_2X', 'OS_4X', 'OS_8X', 'OS_16X']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input

def constraints_pass_iir_filter(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: string
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = [
        'FILTER_SIZE_0',
        'FILTER_SIZE_1',
        'FILTER_SIZE_3',
        'FILTER_SIZE_7',
        'FILTER_SIZE_15',
        'FILTER_SIZE_31',
        'FILTER_SIZE_63',
        'FILTER_SIZE_127'
    ]
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input

def constraints_pass_gas_heater_temperature(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: integer
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure 200 <= value <= 400
    if value < 200 or value > 400:
        all_passed = False
        errors.append("Must be between 200 and 400")
    return all_passed, errors, mod_input

def constraints_pass_gas_heater_duration(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: integer
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure 1 <= value <= 4032
    if value < 1 or value > 4032:
        all_passed = False
        errors.append("Must be between 1 and 4032")
    return all_passed, errors, mod_input

def constraints_pass_gas_heater_profile(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: integer
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    range_pass = ['', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    if value not in range_pass:
        all_passed = False
        errors.append("Invalid range. Need one of {}".format(range_pass))
    return all_passed, errors, mod_input

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    3: {
        'measurement': 'resistance',
        'unit': 'Ohm'
    },
    4: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    5: {
        'measurement': 'altitude',
        'unit': 'm'
    },
    6: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BME680',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME680',
    'input_library': 'bme680',
    'measurements_name': 'Temperature/Humidity/Pressure/Gas',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug',
        'custom_options'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'bme680', 'bme680'),
        ('pip-pypi', 'smbus2', 'smbus2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x76',
        '0x77'
    ],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'humidity_oversample',
            'type': 'select',
            'default_value': 'OS_NONE',
            'options_select': [
                ('OS_NONE', 'OS_NONE'),
                ('OS_1X', 'OS_1X'),
                ('OS_2X', 'OS_2X'),
                ('OS_4X', 'OS_4X'),
                ('OS_8X', 'OS_8X'),
                ('OS_16X', 'OS_16X')
            ],
            'constraints_pass': constraints_pass_oversample,
            'name': lazy_gettext('Humidity Oversampling'),
            'phrase': lazy_gettext('A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.')
        },
        {
            'id': 'temperature_oversample',
            'type': 'select',
            'default_value': 'OS_NONE',
            'options_select': [
                ('OS_NONE', 'OS_NONE'),
                ('OS_1X', 'OS_1X'),
                ('OS_2X', 'OS_2X'),
                ('OS_4X', 'OS_4X'),
                ('OS_8X', 'OS_8X'),
                ('OS_16X', 'OS_16X')
            ],
            'constraints_pass': constraints_pass_oversample,
            'name': lazy_gettext('Temperature Oversampling'),
            'phrase': lazy_gettext('A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.')
        },
        {
            'id': 'pressure_oversample',
            'type': 'select',
            'default_value': 'OS_NONE',
            'options_select': [
                ('OS_NONE', 'OS_NONE'),
                ('OS_1X', 'OS_1X'),
                ('OS_2X', 'OS_2X'),
                ('OS_4X', 'OS_4X'),
                ('OS_8X', 'OS_8X'),
                ('OS_16X', 'OS_16X')
            ],
            'constraints_pass': constraints_pass_oversample,
            'name': lazy_gettext('Pressure Oversampling'),
            'phrase': lazy_gettext('A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.')
        },
        {
            'id': 'iir_filter',
            'type': 'select',
            'default_value': 'FILTER_SIZE_0',
            'options_select': [
                ('FILTER_SIZE_0', 'FILTER_SIZE_0'),
                ('FILTER_SIZE_1', 'FILTER_SIZE_1'),
                ('FILTER_SIZE_3', 'FILTER_SIZE_3'),
                ('FILTER_SIZE_7', 'FILTER_SIZE_7'),
                ('FILTER_SIZE_15', 'FILTER_SIZE_15'),
                ('FILTER_SIZE_31', 'FILTER_SIZE_31'),
                ('FILTER_SIZE_63', 'FILTER_SIZE_63'),
                ('FILTER_SIZE_127', 'FILTER_SIZE_127')
            ],
            'constraints_pass': constraints_pass_iir_filter,
            'name': lazy_gettext('IIR Filter Size'),
            'phrase': lazy_gettext('Optionally remove short term fluctuations from the temperature and pressure readings, increasing their resolution but reducing their bandwidth.')
        },
        {
            'id': 'gas_heater_temperature',
            'type': 'integer',
            'default_value': 320,
            'constraints_pass': constraints_pass_gas_heater_temperature,
            'name': lazy_gettext('Gas Heater Temperature (°C)'),
            'phrase': lazy_gettext('What temperature to set')
        },
        {
            'id': 'gas_heater_duration',
            'type': 'integer',
            'default_value': 150,
            'constraints_pass': constraints_pass_gas_heater_duration,
            'name': lazy_gettext('Gas Heater Duration (ms)'),
            'phrase': lazy_gettext('How long of a duration to heat. 20-30 ms are necessary for the heater to reach the intended target temperature.')
        },
        {
            'id': 'gas_heater_profile',
            'type': 'select',
            'default_value': '',
            'options_select': [
                ('', 'Disabled'),
                ('0', '0'),
                ('1', '1'),
                ('2', '2'),
                ('3', '3'),
                ('4', '4'),
                ('5', '5'),
                ('6', '6'),
                ('7', '7'),
                ('8', '8'),
                ('9', '9')
            ],
            'constraints_pass': constraints_pass_gas_heater_profile,
            'name': lazy_gettext('Gas Heater Profile'),
            'phrase': lazy_gettext('Select one of the 10 configured heating durations/set points')
        }
    ],
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BME680's humidity, temperature,
    pressure, calculates the altitude and dew point, and measures a gas resistance.
    The gas resistance can be averaged to give a relative air quality level.

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.humidity_oversample = None
        self.temperature_oversample = None
        self.pressure_oversample = None
        self.iir_filter = None
        self.gas_heater_temperature = None
        self.gas_heater_duration = None
        self.gas_heater_profile = None

        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:

            import bme680
            from smbus2 import SMBus

            if self.humidity_oversample == 'OS_NONE':
                self.humidity_oversample = bme680.OS_NONE
            elif self.humidity_oversample == 'OS_1X':
                self.humidity_oversample = bme680.OS_1X
            elif self.humidity_oversample == 'OS_2X':
                self.humidity_oversample = bme680.OS_2X
            elif self.humidity_oversample == 'OS_4X':
                self.humidity_oversample = bme680.OS_4X
            elif self.humidity_oversample == 'OS_8X':
                self.humidity_oversample = bme680.OS_8X
            elif self.humidity_oversample == 'OS_16X':
                self.humidity_oversample = bme680.OS_16X

            if self.temperature_oversample == 'OS_NONE':
                self.temperature_oversample = bme680.OS_NONE
            elif self.temperature_oversample == 'OS_1X':
                self.temperature_oversample = bme680.OS_1X
            elif self.temperature_oversample == 'OS_2X':
                self.temperature_oversample = bme680.OS_2X
            elif self.temperature_oversample == 'OS_4X':
                self.temperature_oversample = bme680.OS_4X
            elif self.temperature_oversample == 'OS_8X':
                self.temperature_oversample = bme680.OS_8X
            elif self.temperature_oversample == 'OS_16X':
                self.temperature_oversample = bme680.OS_16X

            if self.pressure_oversample == 'OS_NONE':
                self.pressure_oversample = bme680.OS_NONE
            elif self.pressure_oversample == 'OS_1X':
                self.pressure_oversample = bme680.OS_1X
            elif self.pressure_oversample == 'OS_2X':
                self.pressure_oversample = bme680.OS_2X
            elif self.pressure_oversample == 'OS_4X':
                self.pressure_oversample = bme680.OS_4X
            elif self.pressure_oversample == 'OS_8X':
                self.pressure_oversample = bme680.OS_8X
            elif self.pressure_oversample == 'OS_16X':
                self.pressure_oversample = bme680.OS_16X

            if self.iir_filter == 'FILTER_SIZE_0':
                self.iir_filter = bme680.FILTER_SIZE_0
            elif self.iir_filter == 'FILTER_SIZE_1':
                self.iir_filter = bme680.FILTER_SIZE_1
            elif self.iir_filter == 'FILTER_SIZE_3':
                self.iir_filter = bme680.FILTER_SIZE_3
            elif self.iir_filter == 'FILTER_SIZE_7':
                self.iir_filter = bme680.FILTER_SIZE_7
            elif self.iir_filter == 'FILTER_SIZE_15':
                self.iir_filter = bme680.FILTER_SIZE_15
            elif self.iir_filter == 'FILTER_SIZE_31':
                self.iir_filter = bme680.FILTER_SIZE_31
            elif self.iir_filter == 'FILTER_SIZE_63':
                self.iir_filter = bme680.FILTER_SIZE_63
            elif self.iir_filter == 'FILTER_SIZE_127':
                self.iir_filter = bme680.FILTER_SIZE_127

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = bme680.BME680(
                i2c_addr=self.i2c_address,
                i2c_device=SMBus(self.i2c_bus))

            # Set oversampling settings (can be tweaked to balance accuracy and noise in data
            self.sensor.set_humidity_oversample(self.humidity_oversample)
            self.sensor.set_temperature_oversample(self.temperature_oversample)
            self.sensor.set_pressure_oversample(self.pressure_oversample)
            self.sensor.set_filter(self.iir_filter)

            if self.is_enabled(3):
                self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
                self.sensor.set_gas_heater_temperature(self.gas_heater_temperature)
                self.sensor.set_gas_heater_duration(self.gas_heater_duration)
                if self.gas_heater_profile:
                    self.sensor.select_gas_heater_profile(int(self.gas_heater_profile))
            else:
                self.sensor.set_gas_status(bme680.DISABLE_GAS_MEAS)

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self.return_dict = measurements_dict.copy()
        self.sensor.get_sensor_data()

        if self.is_enabled(0):
            self.value_set(0, self.sensor.data.temperature)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.data.humidity)

        if self.is_enabled(2):
            self.value_set(2, self.sensor.data.pressure)

        if self.is_enabled(3):
            if self.sensor.data.heat_stable:
                self.value_set(3, self.sensor.data.gas_resistance)

        self.logger.debug("Temp: {t}, Hum: {h}, Press: {p}, Gas: {g}".format(
            t=self.value_get(0),
            h=self.value_get(1),
            p=self.value_get(2),
            g=self.value_get(3)))

        if (self.is_enabled(4) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(4, calculate_dewpoint(
                self.value_get(0), self.value_get(1)))

        if self.is_enabled(5) and self.is_enabled(2):
            self.value_set(5, calculate_altitude(self.value_get(2)))

        if (self.is_enabled(6) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(6, calculate_vapor_pressure_deficit(
                self.value_get(0), self.value_get(1)))

        return self.return_dict
