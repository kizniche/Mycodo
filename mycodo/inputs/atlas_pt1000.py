# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements = {
    'temperature': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_PT1000',
    'input_manufacturer': 'Atlas',
    'input_name': 'Atlas PT-1000',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'i2c_location',
        'uart_location',
        'measurements_convert',
        'period',
        'pre_output'],
    'options_disabled': ['interface'],

    'interfaces': ['I2C', 'UART'],
    'i2c_location': ['0x66'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0'
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the PT1000's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.atlas_pt1000")
        self._measurements = None
        self.atlas_sensor_uart = None
        self.atlas_sensor_i2c = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_pt1000_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.interface = input_dev.interface
            if self.interface == 'UART':
                self.uart_location = input_dev.uart_location
            elif self.interface == 'I2C':
                self.i2c_address = int(str(input_dev.i2c_location), 16)
                self.i2c_bus = input_dev.i2c_bus
            self.initialize_sensor()

    def initialize_sensor(self):
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        if self.interface == 'UART':
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_pt1000_{loc}".format(
                    loc=self.uart_location))
            self.atlas_sensor_uart = AtlasScientificUART(self.uart_location)
        elif self.interface == 'I2C':
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_pt1000_{bus}_{add}".format(
                    bus=self.i2c_bus, add=self.i2c_address))
            self.atlas_sensor_i2c = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)
        else:
            self.logger = logging.getLogger("mycodo.inputs.atlas_pt1000")

    def get_measurement(self):
        """ Gets the Atlas PT1000's temperature in Celsius """
        self._measurements = None
        temp = None

        return_dict = {
            'temperature': {
                'C': {}
            }
        }

        if self.interface == 'UART':
            if self.atlas_sensor_uart.setup:
                lines = self.atlas_sensor_uart.query('R')
                self.logger.debug("All Lines: {lines}".format(lines=lines))

                if 'check probe' in lines:
                    self.logger.error('"check probe" returned from sensor')
                elif str_is_float(lines[0]):
                    temp = float(lines[0])
                    self.logger.debug(
                        'Value[0] is float: {val}'.format(val=temp))
                else:
                    self.logger.error(
                        'Value[0] is not float or "check probe": '
                        '{val}'.format(val=lines[0]))
            else:
                self.logger.error('UART device is not set up. '
                                  'Check the log for errors.')

        elif self.interface == 'I2C':
            if self.atlas_sensor_i2c.setup:
                temp_status, temp_str = self.atlas_sensor_i2c.query('R')
                if temp_status == 'error':
                    self.logger.error(
                        "Sensor read unsuccessful: {err}".format(
                            err=temp_str))
                elif temp_status == 'success':
                    temp = float(temp_str)
            else:
                self.logger.error('I2C device is not set up.'
                                  'Check the log for errors.')

        return_dict['temperature']['C'][0] = temp

        if return_dict['temperature']['C'][0] is not None:
            return return_dict
