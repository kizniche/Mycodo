# coding=utf-8
import time

import copy

from mycodo.inputs.base_input import AbstractInput

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
    'input_manufacturer': 'AMS',
    'input_name': 'CCS811 (with Temperature)',
    'input_name_short': 'CCS811 (w/ temp)',
    'input_library': 'Adafruit_CCS811',
    'measurements_name': 'CO2/VOC/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sciosense.com/products/environmental-sensors/ccs811-gas-sensor-solution/',
    'url_datasheet': 'https://www.sciosense.com/wp-content/uploads/2020/01/CCS811-Datasheet.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/3566',
        'https://www.sparkfun.com/products/14193'
    ],

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_CCS811', 'Adafruit_CCS811==0.2.1'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x5a', '0x5b'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the CC2811's voc, temperature, and co2
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from Adafruit_CCS811 import Adafruit_CCS811

        self.sensor = Adafruit_CCS811(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)

        while not self.sensor.available():
            time.sleep(0.1)

        self.sensor.tempOffset = self.sensor.calculateTemperature() - 25.0

    def get_measurement(self):
        """Gets the CO2, VOC, and temperature."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.sensor.available():
            temp = self.sensor.calculateTemperature()
            if not self.sensor.readData():
                if self.is_enabled(0):
                    self.value_set(0, self.sensor.geteCO2())
                if self.is_enabled(1):
                    self.value_set(1, self.sensor.getTVOC())
                if self.is_enabled(2):
                    self.value_set(2, temp)
            else:
                self.logger.error("Sensor error")
                return

            return self.return_dict
