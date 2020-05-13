# coding=utf-8
from collections import OrderedDict

from mycodo.inputs.base_input import AbstractInput

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
        'pre_output'
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            from smbus2 import SMBus
            from MCP342x import MCP342x

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.adc_gain = input_dev.adc_gain
            self.adc_resolution = input_dev.adc_resolution

            self.MCP342x = MCP342x
            self.bus = SMBus(self.i2c_bus)

    def get_measurement(self):
        self.return_dict = measurements_dict.copy()

        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                adc = self.MCP342x(self.bus,
                                   self.i2c_address,
                                   channel=channel,
                                   gain=self.adc_gain,
                                   resolution=self.adc_resolution)
                self.value_set(channel, adc.convert_and_read())

        # Dummy data for testing
        # import random
        # return_dict[0]['value'] = random.uniform(1.5, 1.9)
        # return_dict[1]['value'] = random.uniform(2.3, 2.5)
        # return_dict[2]['value'] = random.uniform(0.5, 0.6)
        # return_dict[3]['value'] = random.uniform(3.5, 6.2)

        return self.return_dict
