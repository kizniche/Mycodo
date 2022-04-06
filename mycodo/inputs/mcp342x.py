# coding=utf-8
from collections import OrderedDict

import copy

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
    'input_name': 'MCP342x (x=2,3,4,6,7,8)',
    'input_name_short': 'MCP342x',
    'input_library': 'MCP342x',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': [
        'https://www.microchip.com/wwwproducts/en/MCP3422',
        'https://www.microchip.com/wwwproducts/en/MCP3423',
        'https://www.microchip.com/wwwproducts/en/MCP3424',
        'https://www.microchip.com/wwwproducts/en/MCP3426'
        'https://www.microchip.com/wwwproducts/en/MCP3427',
        'https://www.microchip.com/wwwproducts/en/MCP3428',
    ],
    'url_datasheet': [
        'http://ww1.microchip.com/downloads/en/DeviceDoc/22088c.pdf',
        'http://ww1.microchip.com/downloads/en/DeviceDoc/22226a.pdf'
    ],

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
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1'),
        ('pip-pypi', 'MCP342x', 'MCP342x==0.3.4')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x68', '0x6A', '0x6C', '0x6E', '0x6F'],
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
    """ADC Read."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.bus = None
        self.i2c_address = None
        self.adc_gain = None
        self.adc_resolution = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from smbus2 import SMBus
        from MCP342x import MCP342x

        self.sensor = MCP342x
        self.bus = SMBus(self.input_dev.i2c_bus)

        self.i2c_address = int(str(self.input_dev.i2c_location), 16)
        self.adc_gain = self.input_dev.adc_gain
        self.adc_resolution = self.input_dev.adc_resolution

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                adc = self.sensor(self.bus,
                                  self.i2c_address,
                                  channel=channel,
                                  gain=self.adc_gain,
                                  resolution=self.adc_resolution)
                self.value_set(channel, adc.convert_and_read())

        return self.return_dict
