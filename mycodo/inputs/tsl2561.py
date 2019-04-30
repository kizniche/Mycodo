# coding=utf-8
import logging

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
        'pre_output',
        'log_level_debug'
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

    def __init__(self, input_dev, testing=False, run_main=True):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tsl2561")
        self.run_main = run_main

        if not testing:
            from tsl2561 import TSL2561
            self.logger = logging.getLogger(
                "mycodo.tsl2561_{id}".format(id=input_dev.unique_id.split('-')[0]))
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.tsl = TSL2561(address=self.i2c_address, busnum=self.i2c_bus)

        if input_dev.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the TSL2561's lux """
        return_dict = measurements_dict.copy()

        from tsl2561.constants import TSL2561_INTEGRATIONTIME_402MS
        self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_402MS)
        saturated = False
        try:
            full, ir = self.tsl._get_luminosity()

            if self.is_enabled(0):
                return_dict[0]['value'] = full

            if self.is_enabled(1):
                return_dict[1]['value'] = ir

            if (self.is_enabled(2) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                return_dict[2]['value'] = self.tsl._calculate_lux(
                    return_dict[0]['value'], return_dict[1]['value'])

            return return_dict
        except Exception as err:
            if 'saturated' in repr(err):
                self.logger.error(
                    "Could not obtain measurement: Sensor is saturated. "
                    "Setting integration time to 101 ms and trying again")
                saturated = True
            else:
                self.logger.exception("Error: {}".format(err))

        if saturated:
            from tsl2561.constants import TSL2561_INTEGRATIONTIME_101MS
            self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_101MS)
            saturated = False
            try:
                full, ir = self.tsl._get_luminosity()

                if self.is_enabled(0):
                    return_dict[0]['value'] = full

                if self.is_enabled(1):
                    return_dict[1]['value'] = ir

                if (self.is_enabled(2) and
                        self.is_enabled(0) and
                        self.is_enabled(1)):
                    return_dict[2]['value'] = self.tsl._calculate_lux(
                        return_dict[0]['value'], return_dict[1]['value'])

                return return_dict
            except Exception as err:
                if 'saturated' in repr(err):
                    self.logger.error(
                        "Could not obtain measurement: Sensor is saturated. "
                        "Setting integration time to 13 ms and trying again")
                    saturated = True
                else:
                    self.logger.exception("Error: {}".format(err))

        if saturated:
            from tsl2561.constants import TSL2561_INTEGRATIONTIME_13MS
            self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_13MS)
            try:
                full, ir = self.tsl._get_luminosity()

                if self.is_enabled(0):
                    return_dict[0]['value'] = full

                if self.is_enabled(1):
                    return_dict[1]['value'] = ir

                if (self.is_enabled(2) and
                        self.is_enabled(0) and
                        self.is_enabled(1)):
                    return_dict[2]['value'] = self.tsl._calculate_lux(
                        return_dict[0]['value'], return_dict[1]['value'])

                return return_dict
            except Exception as err:
                if 'saturated' in repr(err):
                    self.logger.error(
                        "Could not obtain measurement: Sensor is saturated. "
                        "Recording value as 65536.")
                    return_dict[0]['value'] = 65536.0
                    return return_dict
                else:
                    self.logger.exception("Error: {}".format(err))


if __name__ == "__main__":
    from types import SimpleNamespace
    settings = SimpleNamespace()
    settings.id = 1
    settings.unique_id = '0000-0000'
    settings.i2c_location = '0x39'
    settings.i2c_bus = 1
    settings.run_main = True

    measurements = InputModule(settings, run_main=True).next()
    print("Measurements: {}".format(measurements))
