# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP9808',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP9808',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        (
            'pip-pypi',
            'Adafruit_GPIO',
            'Adafruit_GPIO'
         ),
        (
            'pip-git',
            'Adafruit_MCP9808',
            'git://github.com/adafruit/Adafruit_Python_MCP9808.git#egg=adafruit-mcp9808'
        ),
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x18',
        '0x19',
        '0x1a',
        '0x1b',
        '0x1c',
        '0x1d',
        '0x1e',
        '0x1f'
    ],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the MCP9808's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.mcp9808")

        if not testing:
            from Adafruit_MCP9808 import MCP9808
            self.logger = logging.getLogger(
                "mycodo.mcp9808_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus

            self.sensor = MCP9808.MCP9808(
                address=self.i2c_address, busnum=self.i2c_bus)
            self.sensor.begin()

        if input_dev.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the MCP9808's temperature in Celsius """
        return_dict = measurements_dict.copy()

        try:
            return_dict[0]['value'] = self.sensor.readTempC()
            return return_dict
        except Exception as msg:
            self.logger.exception("Inout read failure: {}".format(msg))
