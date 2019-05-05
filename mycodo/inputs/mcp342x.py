# coding=utf-8
import logging
from collections import OrderedDict

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = OrderedDict()
for each_channel in range(4):
    measurements_dict[each_channel] = {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP342x',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP342x',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'measurements_rescale': True,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'adc_gain',
        'adc_resolution',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2'),
        ('pip-pypi', 'MCP342x', 'MCP342x==0.3.3')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x68',
        '0x6A',
        '0x6C',
        '0x6E',
        '0x6F'
    ],
    'i2c_address_editable': False,

    'adc_gain': [
        (1, '1'),
        (2, '2'),
        (4, '4'),
        (8, '8')
    ],
    'adc_resolution': [
        (12, '12'),
        (14, '14'),
        (16, '16'),
        (18, '18')
    ]
}


class InputModule(AbstractInput):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger('mycodo.mcp342x')
        self.acquiring_measurement = False

        if not testing:
            from smbus2 import SMBus
            from MCP342x import MCP342x
            self.logger = logging.getLogger(
                'mycodo.mcp342x_{id}'.format(
                    id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.adc_gain = input_dev.adc_gain
            self.adc_resolution = input_dev.adc_resolution

            self.MCP342x = MCP342x
            self.bus = SMBus(self.i2c_bus)

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        return_dict = measurements_dict.copy()

        for each_measure in self.device_measurements.all():
            if each_measure.is_enabled:
                adc = self.MCP342x(self.bus,
                                   self.i2c_address,
                                   channel=each_measure.channel,
                                   gain=self.adc_gain,
                                   resolution=self.adc_resolution)
                return_dict[each_measure.channel]['value'] = adc.convert_and_read()

        # Dummy data for testing
        # import random
        # return_dict[0]['value'] = random.uniform(1.5, 1.9)
        # return_dict[1]['value'] = random.uniform(2.3, 2.5)
        # return_dict[2]['value'] = random.uniform(0.5, 0.6)
        # return_dict[3]['value'] = random.uniform(3.5, 6.2)

        return return_dict


if __name__ == "__main__":
    from types import SimpleNamespace
    settings = SimpleNamespace()
    settings.id = 1
    settings.unique_id='0000-0000'
    settings.i2c_location = '0x68'
    settings.i2c_bus = 1
    settings.adc_gain = 1
    settings.adc_resolution = 12
    settings.channels = 4
    settings.run_main = True

    measurements = InputModule(settings).next()

    print("Measurements: {}".format(measurements))
