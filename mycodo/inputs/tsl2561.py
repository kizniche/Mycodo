# coding=utf-8
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
    'input_manufacturer': 'TAOS',
    'input_name': 'TSL2561',
    'measurements_name': 'Light',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-pypi', 'Adafruit_PureIO', 'Adafruit_PureIO'),
        ('pip-pypi', 'tsl2561', 'tsl2561')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x39'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TSL2561's lux """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            from tsl2561 import TSL2561

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.tsl = TSL2561(
                address=self.i2c_address,
                busnum=self.i2c_bus)

    def get_lux(self):
        self.return_dict = measurements_dict.copy()
        full, ir = self.tsl._get_luminosity()

        if self.is_enabled(0):
            self.value_set(0, full)

        if self.is_enabled(1):
            self.value_set(1, ir)

        if self.is_enabled(2):
            self.value_set(2, self.tsl.lux())

    def get_measurement(self):
        """ Gets the TSL2561's lux """
        self.return_dict = measurements_dict.copy()

        from tsl2561.constants import TSL2561_INTEGRATIONTIME_402MS
        self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_402MS)
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
            self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_101MS)
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
            self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_13MS)
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


if __name__ == "__main__":
    from types import SimpleNamespace
    settings = SimpleNamespace()
    settings.id = 1
    settings.unique_id = '0000-0000'
    settings.i2c_location = '0x39'
    settings.i2c_bus = 1

    measurements = InputModule(settings).next()
    print("Measurements: {}".format(measurements))
