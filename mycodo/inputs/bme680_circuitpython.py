# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit


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
    'input_name_unique': 'BME680_CP',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME680',
    'input_library': 'Adafruit_CircuitPython_BME680',
    'measurements_name': 'Temperature/Humidity/Pressure/Gas',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/',
    'url_datasheet': 'https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/3660',
        'https://www.sparkfun.com/products/16466'
    ],

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.1'),
        ('pip-pypi', 'adafruit_bme680', 'adafruit-circuitpython-bme680==2.5.4')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x76', '0x77'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'humidity_oversample',
            'type': 'select',
            'default_value': '2',
            'options_select': [
                ('0', 'NONE'),
                ('1', '1X'),
                ('2', '2X'),
                ('4', '4X'),
                ('8', '8X'),
                ('16', '16X')
            ],
            'name': 'Humidity Oversampling',
            'phrase': 'A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.'
        },
        {
            'id': 'temperature_oversample',
            'type': 'select',
            'default_value': '8',
            'options_select': [
                ('0', 'NONE'),
                ('1', '1X'),
                ('2', '2X'),
                ('4', '4X'),
                ('8', '8X'),
                ('16', '16X')
            ],
            'name': 'Temperature Oversampling',
            'phrase': 'A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.'
        },
        {
            'id': 'pressure_oversample',
            'type': 'select',
            'default_value': '4',
            'options_select': [
                ('0', 'NONE'),
                ('1', '1X'),
                ('2', '2X'),
                ('4', '4X'),
                ('8', '8X'),
                ('16', '16X')
            ],
            'name': 'Pressure Oversampling',
            'phrase': 'A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.'
        },
        {
            'id': 'iir_filter',
            'type': 'select',
            'default_value': '3',
            'options_select': [
                ('0', '0'),
                ('1', '1'),
                ('3', '3'),
                ('7', '7'),
                ('15', '15'),
                ('31', '31'),
                ('63', '63'),
                ('127', '127')
            ],
            'name': 'IIR Filter Size',
            'phrase': 'Optionally remove short term fluctuations from the temperature and pressure readings, increasing their resolution but reducing their bandwidth.'
        },
        {
            'id': 'temp_offset',
            'type': 'float',
            'default_value': 0,
            'name': 'Temperature Offset',
            'phrase': 'The amount to offset the temperature, either negative or positive'
        },
        {
            'id': 'sea_level_pressure_ha',
            'type': 'float',
            'default_value': 1013.25,
            'name': 'Sea Level Pressure (ha)',
            'phrase': 'The pressure at sea level for the sensor location'
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

        self.sensor = None

        self.humidity_oversample = None
        self.temperature_oversample = None
        self.pressure_oversample = None
        self.iir_filter = None
        self.temp_offset = None
        self.sea_level_pressure_ha = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import adafruit_bme680
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_bme680.Adafruit_BME680_I2C(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

        # Set oversampling settings (can be tweaked to balance accuracy and noise in data
        self.sensor.humidity_oversample = int(self.humidity_oversample)
        self.sensor.temperature_oversample = int(self.temperature_oversample)
        self.sensor.pressure_oversample = int(self.pressure_oversample)
        self.sensor.filter_size = int(self.iir_filter)

        self.sensor.sea_level_pressure = self.sea_level_pressure_ha

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.temperature + self.temp_offset)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.relative_humidity)

        if self.is_enabled(2):
            self.value_set(2, convert_from_x_to_y_unit('hPa', 'Pa', self.sensor.pressure))

        if self.is_enabled(3):
            self.value_set(3, self.sensor.gas)

        self.logger.debug("Temp: {t}, Hum: {h}, Press: {p}, Gas: {g}".format(
            t=self.value_get(0), h=self.value_get(1), p=self.value_get(2), g=self.value_get(3)))

        if self.is_enabled(0) and self.is_enabled(1) and self.is_enabled(4):
            self.value_set(4, calculate_dewpoint(self.value_get(0), self.value_get(1)))

        if self.is_enabled(5):
            self.value_set(5, self.sensor.altitude)

        if self.is_enabled(0) and self.is_enabled(1) and self.is_enabled(6):
            self.value_set(6, calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1)))

        return self.return_dict
