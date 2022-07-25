# coding=utf-8
import copy
import time

from mycodo.inputs.base_input import AbstractInput

measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

INPUT_INFORMATION = {
    'input_name_unique': 'input_MAX31855_dfrobot',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31855 (Gravity PT100)',
    'input_library': 'wiringpi',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31855.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/MAX31855.pdf',
    'url_product_purchase': 'https://www.dfrobot.com/product-1753.html',

    'options_enabled': [
        'period',
        'pre_output'
    ],
    'options_disabled': [
        'interface',
        'i2c_location'
    ],

    'dependencies_module': [
        ('pip-pypi', 'wiringpi', 'wiringpi')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x10'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """A sensor support class that measures the MAX31855's temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.sensor = DFRobotMAX31855()

    def get_measurement(self):
        """Gets the measurement in units by reading the MAX31855."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        list_temps = []
        for _ in range(5):
            try:
                temp = self.sensor.read_celsius()

                if temp < -300 or temp > 1400:
                    self.logger.error(f"Incorrect temperature reading: {temp}")
                    continue

                if temp == -1:
                    self.logger.debug(f"Incorrect temperature reading: {temp}")
                    continue

                list_temps.append(temp)
            finally:
                time.sleep(0.25)

        if list_temps:
            self.value_set(0, sum(list_temps) / len(list_temps))

        return self.return_dict


class DFRobotMAX31855:
    def __init__(self):
        import wiringpi

        self.wiringpi = wiringpi
        self.i2c = self.wiringpi.wiringPiI2CSetup(0x10)

    def read_data(self):
        a = self.wiringpi.wiringPiI2CReadReg8(self.i2c, 0x00)
        b = self.wiringpi.wiringPiI2CReadReg8(self.i2c, 0x01)
        #    c = wiringpi.wiringPiI2CReadReg8(self.i2c,0x02)
        d = self.wiringpi.wiringPiI2CReadReg8(self.i2c, 0x03)

        return a, b, d

    def read_celsius(self):
        a, b, d = self.read_data()

        if d & 0x7:
            return False

        if a & 0x80:
            a = 0xff - a
            b = 0xff - b
            temp = -((((a << 8) | b) >> 2) + 1) * 0.25
            return temp

        temp = (((a << 8) | b) >> 2) * 0.25

        return temp
