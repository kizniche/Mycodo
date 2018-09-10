# coding=utf-8
import argparse
import logging

import Adafruit_MCP3008

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'MCP3008',
    'input_manufacturer': 'Microchip',
    'common_name_input': 'MCP3008 (Analog-to-Digital Converter)',
    'common_name_measurements': 'Voltage',
    'unique_name_measurements': ['voltage'],  # List of strings
    'dependencies_pypi': ['Adafruit_MCP3008'],  # List of strings
    'interfaces': ['UART'],  # List of strings
    'analog_to_digital_converter': True,  # Boolean
    'pin_cs': 8,
    'pin_miso': 9,
    'pin_mosi': 10,
    'pin_clock': 11,
    'adc_channel': [(0, 'Channel 0'),
                    (1, 'Channel 1'),
                    (2, 'Channel 2'),
                    (3, 'Channel 3')],  # List of tuples
    'adc_volts_min': -4.096,  # Float
    'adc_volts_max': 4.096,  # Float
    'options_enabled': ['pin_cs', 'pin_miso', 'pin_mosi', 'pin_clock', 'adc_channel', 'adc_options', 'period', 'pre_output'],
    'options_disabled': ['interface']
}

class ADCModule(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.mcp3008')
        self.acquiring_measurement = False
        self._voltage = None
        self.adc = None

        self.pin_clock = input_dev.pin_clock
        self.pin_cs = input_dev.pin_cs
        self.pin_miso = input_dev.pin_miso
        self.pin_mosi = input_dev.pin_mosi
        self.adc_channel = input_dev.adc_channel
        self.adc_volts_max = input_dev.adc_volts_max

        if not testing:
            self.logger = logging.getLogger(
                'mycodo.mcp3008_{id}'.format(id=input_dev.id))
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
        return dict(voltage=float('{0:.4f}'.format(self._voltage)))

    @property
    def voltage(self):
        return self._voltage

    def get_measurement(self):
        self._voltage = None
        voltage = (self.adc.read_adc(self.adc_channel) / 1023.0) * self.adc_volts_max
        return voltage

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
            self._voltage = self.get_measurement()
            if self._voltage is not None:
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
