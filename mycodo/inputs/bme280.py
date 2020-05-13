# coding=utf-8
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

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
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    4: {
        'measurement': 'altitude',
        'unit': 'm'
    },
    5: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }

}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BME280',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME280',
    'input_library': 'Adafruit_BME280',
    'measurements_name': 'Pressure/Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-git', 'Adafruit_BME280', 'git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x76',
        '0x77'
    ],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            from Adafruit_BME280 import BME280

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = BME280(
                address=self.i2c_address,
                busnum=self.i2c_bus)

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_temperature())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_humidity())

        if self.is_enabled(2):
            self.value_set(2, self.sensor.read_pressure())

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(3, calculate_dewpoint(
                self.value_get(0), self.value_get(1)))

        if self.is_enabled(4) and self.is_enabled(2):
            self.value_set(4, calculate_altitude(self.value_get(2)))

        if (self.is_enabled(5) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(5, calculate_vapor_pressure_deficit(
                self.value_get(0), self.value_get(1)))

        return self.return_dict
