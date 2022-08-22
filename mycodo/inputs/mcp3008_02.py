# coding=utf-8
import copy
from collections import OrderedDict

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value

# Measurements
measurements_dict = OrderedDict()
for each_channel in range(4):
    measurements_dict[each_channel] = {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP3008_02',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP3008',
    'input_library': 'MCP3008',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.microchip.com/wwwproducts/en/en010530',
    'url_datasheet': 'http://ww1.microchip.com/downloads/en/DeviceDoc/21295d.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/856',

    'measurements_rescale': True,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096,

    'options_enabled': [
        'measurements_select',
        'channels_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'mcp3008', 'mcp3008==1.0.0')
    ],

    'interfaces': ['UART'],

    'custom_options': [
        {
            'id': 'uart_bus',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'UART Bus',
            'phrase': 'The bus number of the UART'
        },
        {
            'id': 'uart_device',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'UART Device',
            'phrase': 'The device number of the UART'
        },
        {
            'id': 'vref',
            'type': 'float',
            'default_value': 3.3,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'VREF (volts)',
            'phrase': 'Set the VREF voltage'
        }
    ]
}


class InputModule(AbstractInput):
    """ADC Read."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.channels = []

        self.uart_bus = None
        self.uart_device = None
        self.vref = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import mcp3008

        self.sensor = mcp3008

        self.channels = [
            self.sensor.CH0,
            self.sensor.CH1,
            self.sensor.CH2,
            self.sensor.CH3,
            self.sensor.CH4,
            self.sensor.CH5,
            self.sensor.CH6,
            self.sensor.CH7,
        ]

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        with self.sensor.MCP3008(bus=self.uart_bus, device=self.uart_device) as adc:
            for channel in self.channels_measurement:
                if self.is_enabled(channel):
                    self.value_set(channel, ((adc.read([self.channels[channel]]) / 1024.0) * self.vref))

        return self.return_dict
