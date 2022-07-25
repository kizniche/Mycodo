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
    'input_name_unique': 'input_MAX31855_dfrobot_gpio',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31855 (Gravity PT100)',
    'input_library': 'smbus2',
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
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
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
        self.sensor = DFRobotMAX31855(self.input_dev.i2c_bus, 0x10)

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
    '''
      @brief A class to get sensor temperature
    '''

    def __init__(self, bus, addr):
        import smbus2

        self.__addr = addr
        self.i2cbus = smbus2.SMBus(bus)

    def read_celsius(self):
        '''
          @brief Read temperature data of probe
          @return Temperature value
        '''
        rxbuf = self.read_data(0x00, 4)
        if (rxbuf[3] & 0x7):
            return -1
        if (rxbuf[0] & 0x80):
            rxbuf[0] = 0xff - rxbuf[0]
            rxbuf[1] = 0xff - rxbuf[1]
            temp = -((((rxbuf[0] << 8) | (rxbuf[1] & 0xfc)) >> 2) + 1) * 0.25
            return temp
        temp = (((rxbuf[0] << 8) | (rxbuf[1] & 0xfc)) >> 2) * 0.25
        return temp

    def read_data(self, reg, length):
        '''
          @brief read the data from the register
          @param reg register address
          @param length read data length
        '''
        try:
            rslt = self.i2cbus.read_i2c_block_data(self.__addr, reg, length)
            return rslt
        except:
            return -1
