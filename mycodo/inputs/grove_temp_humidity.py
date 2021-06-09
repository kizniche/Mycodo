# coding=utf-8
import copy
import time

from mycodo.inputs.base_input import AbstractInput
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
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'GROVE_TEMP_AND_HUMIDITY',
    'input_manufacturer': 'Seeedstudio',
    'input_name': 'DHT11/22',
    'input_library': 'grovepi',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': [
        'https://wiki.seeedstudio.com/Grove-Temperature_and_Humidity_Sensor_Pro/',
        'https://wiki.seeedstudio.com/Grove-TemperatureAndHumidity_Sensor/',
    ],
    'message': "Enter the Grove Pi+ GPIO pin connected to the sensor and select the sensor type.",

    'options_enabled': [
        'gpio_location',
        'measurements_select',
        'period',
    ],
    'options_disabled': [
        'interface',
        'pre_output'
    ],

    'dependencies_module': [
        ('apt', 'libatlas-base-dev', 'libatlas-base-dev'),
        ('pip-pypi', 'grovepi', 'grovepi==1.0.4')
    ],

    'custom_options': [
        {
            'id': 'sensor_type',
            'type': 'select',
            'default_value': '0',
            'options_select': [
                ('0', 'DHT11 (Blue)'),
                ('1', 'DHT22 (White)')
            ],
            'name': 'Sensor Type',
            'phrase': 'Sensor type'
        },
    ],

    'interfaces': ['GROVE']
}


class InputModule(AbstractInput):
    """
    This module is a modified version of the DHT11/22 module from the Mycodo 
    distribution.  This version interfaces to the sensor through the Grove Pi+
    hat for the Raspberry Pi.  The GPIO pin is the pin on the Grove Pi+.  The
    sensor type is either blue for the DHT11 or blue for the DHT22.

    A sensor support class that measures the DHT11's humidity and temperature
    and calculates the dew point.

    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    """
    def __init__(self, input_dev, testing=False):
        """
        Instantiate with the Pi and gpio to which the DHT11 output
        pin is connected.

        """
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.grovepi = None
        self.gpio = None
        self.sensor_type = 0

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import grovepi

        self.grovepi = grovepi
        self.gpio = int(self.input_dev.gpio_location)
        self.sensor_type = int(self.sensor_type)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.return_dict = copy.deepcopy(measurements_dict)

        # Try twice to get measurement. This prevents an anomaly where
        # the first measurement fails if the sensor has just been powered
        # for the first time.
        for _ in range(2):
            try:
                self.logger.debug("GPIO: {}, Sensor Type: {}".format(
                    self.gpio, self.sensor_type))

                [temp_temperature,
                 temp_humidity] = self.grovepi.dht(self.gpio, self.sensor_type)

                self.logger.debug("Temp: {}, Hum: {}".format(
                    temp_temperature, temp_humidity))

                if temp_humidity:
                    temp_dew_point = calculate_dewpoint(
                        temp_temperature, temp_humidity)
                    temp_vpd = calculate_vapor_pressure_deficit(
                        temp_temperature, temp_humidity)
                else:
                    self.logger.error("Could not acquire measurement")
                    continue

                if temp_dew_point is not None:
                    if self.is_enabled(0):
                        self.value_set(0, temp_temperature)
                    if self.is_enabled(1):
                        self.value_set(1, temp_humidity)
                    if self.is_enabled(2):
                        self.value_set(2, temp_dew_point)
                    if self.is_enabled(3):
                        self.value_set(3, temp_vpd)
                    break
            except Exception as err:
                self.logger.exception("get_measurement() error: {}".format(err))
            time.sleep(2)

        return self.return_dict
