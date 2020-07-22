# coding=utf-8
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
    'input_name': 'CCS811',
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
