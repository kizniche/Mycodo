# coding=utf-8
import argparse
import logging

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP3008',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP3008',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': ['channel_{}'.format(i) for i in range(4)],  # 4 Channels
    'channels': 4,
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

    'measurements_convert_enabled': True,
    'channels_measurement': 'electrical_potential',
    'channels_unit': 'V',
    'dependencies_module': [
        ('pip-pypi', 'Adafruit_MCP3008', 'Adafruit_MCP3008')
    ],
    'interfaces': ['UART'],
    'pin_cs': 8,
    'pin_miso': 9,
    'pin_mosi': 10,
    'pin_clock': 11,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096
}


class ChannelModule(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.mcp3008')
        self.acquiring_measurement = False
        self._voltages = None
        self.adc = None

        self.pin_clock = input_dev.pin_clock
        self.pin_cs = input_dev.pin_cs
        self.pin_miso = input_dev.pin_miso
        self.pin_mosi = input_dev.pin_mosi
        self.scale_from_max = input_dev.scale_from_max
        self.channels = input_dev.channels

        self.measurements_selected = []
        for each_channel in input_dev.measurements_selected.split(','):
            self.measurements_selected.append(int(each_channel))

        if not testing:
            import Adafruit_MCP3008
            self.logger = logging.getLogger(
                'mycodo.mcp3008_{id}'.format(id=input_dev.unique_id.split('-')[0]))
            self.adc = Adafruit_MCP3008.MCP3008(clk=self.pin_clock,
                                                cs=self.pin_cs,
                                                miso=self.pin_miso,
                                                mosi=self.pin_mosi)

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return voltage information.
        """
        if self.read():
            return None
        return self._voltages

    @property
    def voltages(self):
        return self._voltages

    def get_measurement(self):
        self._voltages = None
        voltages_dict = {}

        for each_channel in self.measurements_selected:
            voltages_dict['channel_{}'.format(each_channel)] = (
                (self.adc.read_adc(each_channel) / 1023.0) * self.scale_from_max)

        if voltages_dict:
            return voltages_dict

    def read(self):
        """
        Takes a reading

        :returns: None on success or 1 on error
        """
        if self.acquiring_measurement:
            self.logger.error("Attempting to acquire a measurement when a"
                              " measurement is already being acquired.")
            return 1
        try:
            self.acquiring_measurement = True
            self._voltages = self.get_measurement()
            if self._voltages:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        finally:
            self.acquiring_measurement = False
        return 1


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
