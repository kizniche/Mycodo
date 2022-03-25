# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'full'
    },
    1: {
        'measurement': 'light',
        'unit': 'ir'
    },
    2: {
        'measurement': 'light',
        'unit': 'lux'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TSL2561',
    'input_manufacturer': 'AMS',
    'input_name': 'TSL2561',
    'input_library': 'tsl2561',
    'measurements_name': 'Light',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://ams.com/tsl2561',
    'url_datasheet': 'https://ams.com/documents/20143/36005/TSL2561_DS000110_3-00.pdf/18a41097-2035-4333-c70e-bfa544c0a98b',
    'url_product_purchase': 'https://www.adafruit.com/product/439',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3'),
        ('pip-pypi', 'Adafruit_PureIO', 'Adafruit-PureIO==1.1.8'),
        ('pip-pypi', 'tsl2561', 'tsl2561==3.4.0')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x29', '0x39', '0x49'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the TSL2561's lux."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from tsl2561 import TSL2561

        self.sensor = TSL2561(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)

    def get_lux(self):
        self.return_dict = copy.deepcopy(measurements_dict)
        full, ir = self.sensor._get_luminosity()

        self.value_set(0, full)
        self.value_set(1, ir)

        if self.is_enabled(2):
            self.value_set(2, self.sensor.lux())

    def get_measurement(self):
        """Gets the TSL2561's lux."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        from tsl2561.constants import TSL2561_INTEGRATIONTIME_402MS
        self.sensor.set_integration_time(TSL2561_INTEGRATIONTIME_402MS)
        saturated = False
        try:
            self.get_lux()
            return self.return_dict
        except Exception as err:
            if 'saturated' in repr(err):
                self.logger.error(
                    "Could not obtain measurement: Sensor is saturated. "
                    "Setting integration time to 101 ms and trying again")
                saturated = True
            else:
                self.logger.exception("get_measurement() Error")

        if saturated:
            from tsl2561.constants import TSL2561_INTEGRATIONTIME_101MS
            self.sensor.set_integration_time(TSL2561_INTEGRATIONTIME_101MS)
            saturated = False
            try:
                self.get_lux()
                return self.return_dict
            except Exception as err:
                if 'saturated' in repr(err):
                    self.logger.error(
                        "Could not obtain measurement: Sensor is saturated. "
                        "Setting integration time to 13 ms and trying again")
                    saturated = True
                else:
                    self.logger.exception("get_measurement() Error")

        if saturated:
            from tsl2561.constants import TSL2561_INTEGRATIONTIME_13MS
            self.sensor.set_integration_time(TSL2561_INTEGRATIONTIME_13MS)
            try:
                self.get_lux()
                return self.return_dict
            except Exception as err:
                if 'saturated' in repr(err):
                    self.logger.error(
                        "Could not obtain measurement: Sensor is saturated. "
                        "Recording value as 65536.")
                    self.value_set(0, 65536.0)
                    return self.return_dict
                else:
                    self.logger.exception("get_measurement() Error")
