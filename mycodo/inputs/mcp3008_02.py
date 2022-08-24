# coding=utf-8
import copy
from collections import OrderedDict

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_value

# Measurements
measurements_dict = OrderedDict()
for each_channel in range(8):
    measurements_dict[each_channel] = {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP3008_circuitpython',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP3008',
    'input_library': 'Adafruit_CircuitPython_MCP3xxx',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.microchip.com/wwwproducts/en/en010530',
    'url_datasheet': 'http://ww1.microchip.com/downloads/en/DeviceDoc/21295d.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/856',

    'measurements_rescale': True,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096,

    'options_enabled': [
        'pin_cs',
        'pin_miso',
        'pin_mosi',
        'pin_clock',
        'measurements_select',
        'channels_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'adafruit_mcp3xxx', 'adafruit-circuitpython-mcp3xxx==1.4.11')
    ],

    'interfaces': ['UART'],
    'pin_cs': 8,
    'pin_miso': 9,
    'pin_mosi': 10,
    'pin_clock': 11,

    'custom_options': [
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

        self.channels = []
        self.vref = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import board
        import busio
        import digitalio
        import adafruit_mcp3xxx.mcp3008 as MCP
        from adafruit_mcp3xxx.analog_in import AnalogIn

        bcm_to_board = [
            board.D1,
            board.D2,
            board.D3,
            board.D4,
            board.D5,
            board.D6,
            board.D7,
            board.D8,
            board.D9,
            board.D10,
            board.D11,
            board.D12,
            board.D13,
            board.D14,
            board.D15,
            board.D16,
            board.D17,
            board.D18,
            board.D19,
            board.D20,
            board.D21,
            board.D22,
            board.D23,
            board.D24,
            board.D25,
            board.D26,
            board.D27
        ]

        # create the spi bus
        spi = busio.SPI(clock=self.input_dev.pin_clock, MISO=self.input_dev.pin_miso, MOSI=self.input_dev.pin_mosi)

        if self.input_dev.pin_cs < 1 or self.input_dev.pin_cs > 26:
            self.logger.error("CS Pin must be between 1 - 26.")
            return

        # create the cs (chip select)
        cs = digitalio.DigitalInOut(bcm_to_board[self.input_dev.pin_cs - 1])

        # create the mcp object
        mcp = MCP.MCP3008(spi, cs, ref_voltage=self.vref)

        self.channels = [
            AnalogIn(mcp, MCP.P0),
            AnalogIn(mcp, MCP.P1),
            AnalogIn(mcp, MCP.P2),
            AnalogIn(mcp, MCP.P3),
            AnalogIn(mcp, MCP.P4),
            AnalogIn(mcp, MCP.P5),
            AnalogIn(mcp, MCP.P6),
            AnalogIn(mcp, MCP.P7)
        ]

    def get_measurement(self):
        if not self.channels:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.value_set(channel, self.channels[channel].voltage)

        return self.return_dict
