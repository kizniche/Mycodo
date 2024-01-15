# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Temperature Sensor'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Humidity Sensor'
    },
    2: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Pressure Sensor'
    },
    3: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    4: {
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    5: {
        'measurement': 'direction',
        'unit': 'bearing',
        'name': 'Compass'
    },
    6: {
        'measurement': 'magnetic_flux_density',
        'unit': 'uT',
        'name': 'x'
    },
    7: {
        'measurement': 'magnetic_flux_density',
        'unit': 'uT',
        'name': 'y'
    },
    8: {
        'measurement': 'magnetic_flux_density',
        'unit': 'uT',
        'name': 'z'
    },
    9: {
        'measurement': 'angle',
        'unit': 'degree',
        'name': 'Pitch'
    },
    10: {
        'measurement': 'angle',
        'unit': 'degree',
        'name': 'Roll'
    },
    11: {
        'measurement': 'angle',
        'unit': 'degree',
        'name': 'Yaw'
    },
    12: {
        'measurement': 'acceleration_x',
        'unit': 'g_force'
    },
    13: {
        'measurement': 'acceleration_y',
        'unit': 'g_force'
    },
    14: {
        'measurement': 'acceleration_z',
        'unit': 'g_force'
    }
}

INPUT_INFORMATION = {
    'input_name_unique': 'PI_SENSE_HAT',
    'input_manufacturer': 'Raspberry Pi Foundation',
    'input_name': 'Sense HAT',
    'input_library': 'sense-hat',
    'measurements_name': 'hum/temp/press/compass/magnet/accel/gyro',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.raspberrypi.org/products/sense-hat/',

    'message': 'This module acquires measurements from the Raspberry Pi Sense HAT sensors, '
               'which include the LPS25H, LSM9DS1, and HTS221.',

    'dependencies_module': [
        ('apt', 'git', 'git'),
        ('bash-commands',
         [
             '/opt/Mycodo/env/RTIMULib_installed',
         ],
         [
             'cd /tmp',
             'git clone https://github.com/RPi-Distro/RTIMULib',
             'cd ./RTIMULib/Linux/python/',
             '/opt/Mycodo/env/bin/python setup.py build',
             '/opt/Mycodo/env/bin/python setup.py install',
             'touch /opt/Mycodo/env/RTIMULib_installed'
         ]),
        ('pip-pypi', 'sense_hat', 'sense-hat==2.2.0')
    ],

    'interfaces': ['I2C'],

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface']
}

class InputModule(AbstractInput):
    """A sensor support class that measures."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        """Initialize the Sense HAT sensor class."""
        from sense_hat import SenseHat

        self.sensor = SenseHat()

    def get_measurement(self):
        """Get measurements and store in the database."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            try:
                self.value_set(0, self.sensor.get_temperature())
            except Exception as e:
                self.logger.error("Temperature (temperature sensor) read failure: {}".format(e))

        if self.is_enabled(1):
            try:
                self.value_set(1, self.sensor.get_temperature_from_humidity())
            except Exception as e:
                self.logger.error("Temperature (humidity sensor) read failure: {}".format(e))

        if self.is_enabled(2):
            try:
                self.value_set(2, self.sensor.get_temperature_from_pressure())
            except Exception as e:
                self.logger.error("Temperature (pressure sensor) read failure: {}".format(e))

        if self.is_enabled(3):
            try:
                self.value_set(3, self.sensor.get_humidity())
            except Exception as e:
                self.logger.error("Humidity read failure: {}".format(e))

        if self.is_enabled(4):
            try:
                self.value_set(4, self.sensor.get_pressure())
            except Exception as e:
                self.logger.error("Pressure read failure: {}".format(e))

        if self.is_enabled(5):
            try:
                self.value_set(5, self.sensor.get_compass())
            except Exception as e:
                self.logger.error("Compass read failure: {}".format(e))

        if self.is_enabled(6) or self.is_enabled(7) or self.is_enabled(8):
            magnetism = self.sensor.get_compass_raw()
            if self.is_enabled(6):
                try:
                    self.value_set(6, magnetism["x"])
                except Exception as e:
                    self.logger.error("Compass raw x read failure: {}".format(e))
            if self.is_enabled(7):
                try:
                    self.value_set(7, magnetism["y"])
                except Exception as e:
                    self.logger.error("Compass raw y read failure: {}".format(e))
            if self.is_enabled(8):
                try:
                    self.value_set(8, magnetism["z"])
                except Exception as e:
                    self.logger.error("Compass raw z read failure: {}".format(e))

        if self.is_enabled(9) or self.is_enabled(10) or self.is_enabled(11):
            gyroscope = self.sensor.get_gyroscope()
            if self.is_enabled(9):
                try:
                    self.value_set(9, gyroscope["pitch"])
                except Exception as e:
                    self.logger.error("Gyroscope pitch read failure: {}".format(e))
            if self.is_enabled(10):
                try:
                    self.value_set(10, gyroscope["roll"])
                except Exception as e:
                    self.logger.error("Gyroscope roll read failure: {}".format(e))
            if self.is_enabled(11):
                try:
                    self.value_set(11, gyroscope["yaw"])
                except Exception as e:
                    self.logger.error("Gyroscope yaw read failure: {}".format(e))

        if self.is_enabled(12) or self.is_enabled(13) or self.is_enabled(14):
            acceleration = self.sensor.get_accelerometer_raw()
            if self.is_enabled(12):
                try:
                    self.value_set(12, acceleration["x"])
                except Exception as e:
                    self.logger.error("Acceleration x read failure: {}".format(e))
            if self.is_enabled(13):
                try:
                    self.value_set(13, acceleration["y"])
                except Exception as e:
                    self.logger.error("Acceleration y read failure: {}".format(e))
            if self.is_enabled(14):
                try:
                    self.value_set(14, acceleration["z"])
                except Exception as e:
                    self.logger.error("Acceleration z read failure: {}".format(e))

        return self.return_dict
