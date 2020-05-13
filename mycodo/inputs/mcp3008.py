# coding=utf-8
import argparse
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
    'input_name_unique': 'MCP3008',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP3008',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
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
        ('pip-pypi', 'Adafruit_MCP3008', 'Adafruit_MCP3008')
    ],

    'interfaces': ['UART'],
    'pin_cs': 8,
    'pin_miso': 9,
    'pin_mosi': 10,
    'pin_clock': 11
}


class InputModule(AbstractInput):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.adc = None

        if not testing:
            import Adafruit_MCP3008

            self.pin_clock = input_dev.pin_clock
            self.pin_cs = input_dev.pin_cs
            self.pin_miso = input_dev.pin_miso
            self.pin_mosi = input_dev.pin_mosi
            self.scale_from_max = input_dev.scale_from_max

            self.adc = Adafruit_MCP3008.MCP3008(
                clk=self.pin_clock,
                cs=self.pin_cs,
                miso=self.pin_miso,
                mosi=self.pin_mosi)

    def get_measurement(self):
        self.return_dict = measurements_dict.copy()

        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.value_set(channel, (
                    (self.adc.read_adc(channel) / 1023.0) * self.scale_from_max))

        return self.return_dict


def parse_args(parser):
    """ Add arguments for argparse """
    parser.add_argument('--clockpin', metavar='CLOCKPIN', type=int,
                        help='SPI Clock Pin',
                        required=True)
    parser.add_argument('--misopin', metavar='MISOPIN', type=int,
                        help='SPI MISO Pin',
                        required=True)
    parser.add_argument('--mosipin', metavar='MOSIPIN', type=int,
                        help='SPI MOSI Pin',
                        required=True)
    parser.add_argument('--cspin', metavar='CSPIN', type=int,
                        help='SPI CS Pin',
                        required=True)
    parser.add_argument('--adcchannel', metavar='ADCCHANNEL', type=int,
                        help='channel to read from the ADC (0 - 7)',
                        required=False, choices=range(0,8))
    return parser.parse_args()


if __name__ == '__main__':
    import Adafruit_MCP3008
    parser = argparse.ArgumentParser(
        description='MCP3008 Analog-to-Digital Converter Read Test Script')
    args = parse_args(parser)

    # Example Software SPI pins: CLK = 18, MISO = 23, MOSI = 24, CS = 25
    mcp = Adafruit_MCP3008.MCP3008(clk=args.clockpin,
                                   cs=args.cspin,
                                   miso=args.misopin,
                                   mosi=args.mosipin)

    if -1 < args.adcchannel < 8:
        # Read the specified channel
        value = mcp.read_adc(args.adcchannel)
        print("ADC Channel: {chan}, Output: {out}".format(
            chan=args.adcchannel, out=value))
    else:
        # Create a list for the ADC channel values
        values = [0] * 8

        # Conduct measurements of channels 0 - 7, add them to the list
        for i in range(8):
            values[i] = mcp.read_adc(i)

        # Print the list of ADC values
        print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))
