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
    'input_name_unique': 'MCP3208',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP3208',
    'input_library': 'MCP3208',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.microchip.com/en-us/product/MCP3208',
    'url_datasheet': 'http://ww1.microchip.com/downloads/en/devicedoc/21298e.pdf',

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
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3'),
    ],

    'interfaces': ['SPI'],

    'custom_options': [
            {
            'id': 'spi_bus',
            'type': 'integer',
            'default_value': 0,
            'name': 'SPI Bus',
            'phrase': 'The SPI bus ID.'
        },
        {
            'id': 'spi_device',
            'type': 'integer',
            'default_value': 0,
            'name': 'SPI Device',
            'phrase': 'The SPI device ID.'
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
        self.spi_bus = None
        self.spi_device = None
        self.vref = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import Adafruit_GPIO.SPI as SPI

        self.sensor = MCP3208(SPI, self.spi_bus, self.spi_device)

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.value_set(channel, ((self.sensor.read(channel) / 1024.0) * self.vref))

        return self.return_dict


class MCP3208(object):
    def __init__(self, spi, spi_bus=0, spi_device=0):
        self.spi = spi.SpiDev(spi_bus, spi_device, max_speed_hz=1000000)
        self.spi.set_mode(0)
        self.spi.set_bit_order(spi.MSBFIRST)

    def __del__(self):
        self.spi.close()

    def read(self, ch):
        if 7 <= ch <= 0:
            raise Exception('MCP3208 channel must be 0-7: ' + str(ch))

        cmd = 128  # 1000 0000
        cmd += 64  # 1100 0000
        cmd += ((ch & 0x07) << 3)
        ret = self.spi.transfer([cmd, 0x0, 0x0])

        # get the 12b out of the return
        val = (ret[0] & 0x01) << 11  # only B11 is here
        val |= ret[1] << 3           # B10:B3
        val |= ret[2] >> 5           # MSB has B2:B0 ... need to move down to LSB

        return val & 0x0FFF  # ensure we are only sending 12b
