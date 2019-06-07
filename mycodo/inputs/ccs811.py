# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    },
    1: {
        'measurement': 'voc',
        'unit': 'ppb'
    },
    2: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'CCS811',
    'input_manufacturer': 'Ams',
    'input_name': 'CCS811',
    'measurements_name': 'CO2/VOC/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_CCS811', 'Adafruit_CCS811'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x5a', '0x5b'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the CC2811's voc, temperature
    and co2

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self._co2 = None
        self._voc = None
        self._temperature = None

        if not testing:
            from Adafruit_CCS811 import Adafruit_CCS811

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = Adafruit_CCS811(
                address=self.i2c_address,
                busnum=self.i2c_bus)
            while not self.sensor.available():
                pass
            temp = self.sensor.calculateTemperature()
            self.sensor.tempOffset = temp - 25.0

    def get_measurement(self):
        """ Gets the CO2, VOC, and temperature """
        self.return_dict = measurements_dict.copy()

        if self.sensor.available():

            temp = self.sensor.calculateTemperature()

            if self.is_enabled(2):
                self.set_value(2, temp)

            if not self.sensor.readData():

                if self.is_enabled(0):
                    self.set_value(0, self.sensor.geteCO2())

                if self.is_enabled(1):
                    self.set_value(1, self.sensor.getTVOC())

            else:
                self.logger.error("Sensor error")
                return

            return self.return_dict
