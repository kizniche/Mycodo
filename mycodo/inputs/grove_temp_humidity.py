# coding=utf-8
import time

import copy
from flask_babel import lazy_gettext
import sys
sys.path.insert(1, '/usr/local/bin')

from mycodo.databases.models import Output
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.database import db_retrieve_table_daemon

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
    'input_manufacturer': 'Grove',
    'input_name': 'DHT11_DHT22',
    'input_library': 'grovepi',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'https://wiki.seeedstudio.com/Grove-TemperatureAndHumidity_Sensor/',
    'url_product_purchase': 'https://wiki.seeedstudio.com/Grove-TemperatureAndHumidity_Sensor/',
    'message': "Enter the Grove Pi+ GPIO pin to which the sensor is attached and select the sensor type.",

    'options_enabled': [
        'gpio_location',
        'measurements_select',
        'period',
    ],
    'options_disabled': [
        'interface',
        'pre_output'
        ],

    'custom_options': [
        {
            'id': 'sensor_type',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (0, 'Blue'),
                (1, 'White')
            ],
            'name': lazy_gettext('Sensor Type'),
            'phrase': 'Sensor type'
        },
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x04'],
    'i2c_address_editable': False,
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the DHT11's humidity and temperature
    and calculates the dew point

    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    """
    def __init__(self, input_dev, testing=False):
        """
        :param gpio: gpio pin number
        :type gpio: int

        Instantiate with the Pi and gpio to which the DHT11 output
        pin is connected.

        """
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.gpio = None
        self.control = None

        self.temp_temperature = 0
        self.temp_humidity = 0
        self.temp_dew_point = None
        self.temp_vpd = None
        self.powered = False
        self.sensor_type = 0
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.initialize_input()

        self.logger.info("DHT sensor initialization complete, pin={}, type={}.".format(self.gpio, self.sensor_type))

    def initialize_input(self):
        from mycodo.mycodo_client import DaemonControl

        self.gpio = int(self.input_dev.gpio_location)

        self.control = DaemonControl()

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.return_dict = copy.deepcopy(measurements_dict)

        import os.path

        if os.path.isfile('/home/pi/Dexter/GrovePi/Software/Python/grovepi.py'):
            self.logger.info("------------> File exists")
        else:
            self.logger.info("------------> File not exists")

        # Try twice to get measurement. This prevents an anomaly where
        # the first measurement fails if the sensor has just been powered
        # for the first time.
        for _ in range(2):
            self.measure_sensor()
            if self.temp_dew_point is not None:
                self.value_set(0, self.temp_temperature)
                self.value_set(1, self.temp_humidity)
                self.value_set(2, self.temp_dew_point)
                self.value_set(3, self.temp_vpd)
                return self.return_dict  # success - no errors
            time.sleep(2)

        self.logger.error("Could not acquire a measurement")
        return None

    def measure_sensor(self):
        self.temp_temperature = 0
        self.temp_humidity = 0
        self.temp_dew_point = None
        self.temp_vpd = None

        try:
            try:
                self.setup()
            except Exception as except_msg:
                self.logger.error(
                    'Could not initialize sensor. Check if gpiod is running. Error: {msg}'.format(msg=except_msg))
            self.logger.info("Starting reading on pin {} for sensor type {}".format(self.gpio, self.sensor_type))
            import grovepid
            [self.temp_temperature, self.temp_humidity] = grovepid.dht(self.gpio, self.sensor_type)
            self.logger.info("Temp: {}, Hum: {}".format(self.temp_temperature, self.temp_humidity))
            if self.temp_humidity != 0:
                self.temp_dew_point = calculate_dewpoint(self.temp_temperature, self.temp_humidity)
                self.temp_vpd = calculate_vapor_pressure_deficit(self.temp_temperature, self.temp_humidity)
        except Exception as e:
            self.logger.error("Exception raised when taking a reading: {err}".format(err=e))
        finally:
            self.close()
            return (self.temp_dew_point,
                    self.temp_humidity,
                    self.temp_temperature)

    def setup(self):
        """ """
        return

    def close(self):
        """ Stop reading sensor """
        return

    def stop_input(self):
        return

