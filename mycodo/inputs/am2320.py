# coding=utf-8
import logging
import time

from mycodo.databases.models import DeviceMeasurements
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
    'input_name_unique': 'AM2320',
    'input_manufacturer': 'AOSONG',
    'input_name': 'AM2320',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_rescale': False,

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x5c'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the AM2320's humidity and temperature
    and calculates the dew point

    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.setup_logger(name=__name__)
        self.powered = False
        self.sensor = None
        self.i2c_address = 0x5C

        if not testing:
            from smbus2 import SMBus

            self.setup_logger(
                name=__name__, log_id=input_dev.unique_id.split('-')[0])

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_bus = input_dev.i2c_bus
            self.power_output_id = input_dev.power_output_id
            self.start_sensor()
            self.sensor = SMBus(self.i2c_bus)

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.return_dict = measurements_dict.copy()

        temperature, humidity = self.read()

        if self.is_enabled(0):
            self.set_value(0, temperature)

        if self.is_enabled(1):
            self.set_value(1, humidity)

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.set_value(2, calculate_dewpoint(
                self.get_value(0), self.get_value(1)))

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.set_value(3, calculate_vapor_pressure_deficit(
                self.get_value(0), self.get_value(1)))

        return self.return_dict

    def read(self):
        try:
            self.sensor.write_i2c_block_data(
                self.i2c_address, 0x03, [0x00, 0x04])
        except OSError as e:
            self.logger.error(e)
        time.sleep(0.02)

        blocks = self.sensor.read_i2c_block_data(self.i2c_address, 0, 6)

        humidity = ((blocks[2] << 8) + blocks[3]) / 10.0
        temperature = ((blocks[4] << 8) + blocks[5]) / 10.0

        return temperature, humidity

    def setup(self):
        try:
            self.sensor.write_i2c_block_data(self.i2c_address, 0x00, [])
        except OSError as e:
            self.logger.error(e)
        time.sleep(0.1)
