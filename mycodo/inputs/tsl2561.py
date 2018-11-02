# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements = {
    'light': {
        'lux': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TSL2561',
    'input_manufacturer': 'TAOS',
    'input_name': 'TSL2561',
    'measurements_name': 'Light',
    'measurements_dict': measurements,

    'options_enabled': [
        'i2c_location',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'tsl2561', 'tsl2561')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x39'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TSL2561's lux """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tsl2561")
        self._measurements = None

        if not testing:
            from tsl2561 import TSL2561
            self.logger = logging.getLogger(
                "mycodo.tsl2561_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.tsl = TSL2561(address=self.i2c_address, busnum=self.i2c_bus)

    def get_measurement(self):
        """ Gets the TSL2561's lux """
        return_dict = {
            'light': {
                'lux': {}
            }
        }

        saturated = False
        try:
            return_dict['light']['lux'][0] = self.tsl.lux()
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
                return_dict['light']['lux'][0] = self.tsl.lux()
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
                return_dict['light']['lux'][0] = self.tsl.lux()
                return return_dict
            except Exception as err:
                if 'saturated' in repr(err):
                    self.logger.error(
                        "Could not obtain measurement: Sensor is saturated. "
                        "Recording value as 65536.")
                    return_dict['light']['lux'][0] = 65536.0
                    return return_dict
                else:
                    self.logger.exception("Error: {}".format(err))
