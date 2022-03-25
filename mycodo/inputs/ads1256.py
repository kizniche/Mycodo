# coding=utf-8
from collections import OrderedDict

import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = OrderedDict()
for each_channel in range(8):
    measurements_dict[each_channel] = {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADS1256',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1256',
    'input_library': 'wiringpi, kizniche/PiPyADC-py3',
    'measurements_name': 'Voltage (Waveshare, Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'measurements_rescale': True,
    'scale_from_min': 0.0,
    'scale_from_max': 5.0,

    'options_enabled': [
        'measurements_select',
        'adc_gain',
        'adc_sample_speed',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'wiringpi', 'wiringpi'),
        ('pip-pypi', 'pipyadc_py3', 'git+https://github.com/kizniche/PiPyADC-py3.git')  # PiPyADC ported to Python3
    ],
    'interfaces': ['UART'],

    'adc_gain': [
        (1, '1'),
        (2, '2'),
        (4, '4'),
        (8, '8'),
        (16, '16'),
        (32, '32'),
        (64, '64')
    ],
    'adc_sample_speed': [
        ('30000', '30,000'),
        ('15000', '15,000'),
        ('7500', '7,500'),
        ('3750', '3,750'),
        ('2000', '2,000'),
        ('1000', '1,000'),
        ('500', '500'),
        ('100', '100'),
        ('60', '60'),
        ('50', '50'),
        ('30', '30'),
        ('25', '25'),
        ('15', '15'),
        ('10', '10'),
        ('5', '5'),
        ('2d5', '2.5')
    ],

    'custom_options': [
        {
            'id': 'adc_calibration',
            'type': 'select',
            'default_value': '',
            'options_select': [
                ('', 'No Calibration'),
                ('SELFOCAL', 'Self Offset'),
                ('SELFGCAL', 'Self Gain'),
                ('SELFCAL', 'Self Offset + Self Gain'),
                ('SYSOCAL', 'System Offset'),
                ('SYSGCAL', 'System Gain')
            ],
            'name': lazy_gettext('Calibration'),
            'phrase': lazy_gettext('Set the calibration method to perform during Input activation')
        }
    ],
}


class InputModule(AbstractInput):
    """ADC Read."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.CH_SEQUENCE = None
        self.adc_gain = None
        self.adc_sample_speed = None

        self.adc_calibration = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import glob
        from pipyadc_py3 import ADS1256
        from pipyadc_py3.ADS1256_definitions import POS_AIN0
        from pipyadc_py3.ADS1256_definitions import POS_AIN1
        from pipyadc_py3.ADS1256_definitions import POS_AIN2
        from pipyadc_py3.ADS1256_definitions import POS_AIN3
        from pipyadc_py3.ADS1256_definitions import POS_AIN4
        from pipyadc_py3.ADS1256_definitions import POS_AIN5
        from pipyadc_py3.ADS1256_definitions import POS_AIN6
        from pipyadc_py3.ADS1256_definitions import POS_AIN7
        from pipyadc_py3.ADS1256_definitions import NEG_AINCOM

        # Input pin for the potentiometer on the Waveshare Precision ADC board
        POTI = POS_AIN0 | NEG_AINCOM

        # Light dependant resistor
        LDR = POS_AIN1 | NEG_AINCOM

        # The other external input screw terminals of the Waveshare board
        EXT2, EXT3, EXT4 = POS_AIN2 | NEG_AINCOM, POS_AIN3 | NEG_AINCOM, POS_AIN4 | NEG_AINCOM
        EXT5, EXT6, EXT7 = POS_AIN5 | NEG_AINCOM, POS_AIN6 | NEG_AINCOM, POS_AIN7 | NEG_AINCOM

        channels = {
            0: POTI,
            1: LDR,
            2: EXT2,
            3: EXT3,
            4: EXT4,
            5: EXT5,
            6: EXT6,
            7: EXT7
        }

        # Generate the channel sequence for enabled channels
        self.CH_SEQUENCE = []
        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.CH_SEQUENCE.append(channels[channel])
        self.CH_SEQUENCE = tuple(self.CH_SEQUENCE)

        self.adc_gain = self.input_dev.adc_gain
        self.adc_sample_speed = self.input_dev.adc_sample_speed

        if glob.glob('/dev/spi*'):
            self.sensor = ADS1256()

            # Perform selected calibration
            if self.adc_calibration == 'SELFOCAL':
                self.sensor.cal_self_offset()
            elif self.adc_calibration == 'SELFGCAL':
                self.sensor.cal_self_gain()
            elif self.adc_calibration == 'SELFCAL':
                self.sensor.cal_self()
            elif self.adc_calibration == 'SYSOCAL':
                self.sensor.cal_system_offset()
            elif self.adc_calibration == 'SYSGCAL':
                self.sensor.cal_system_gain()

        else:
            raise Exception(
                "SPI device /dev/spi* not found. Ensure SPI is enabled and the device is recognized/setup by linux.")

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        # 2 attempts to get valid measurement
        voltages_list = []
        for _ in range(2):
            raw_channels = self.sensor.read_sequence(self.CH_SEQUENCE)
            voltages_list = [i * self.sensor.v_per_digit for i in raw_channels]
            if 0 not in voltages_list:
                break

        if not voltages_list or 0 in voltages_list:
            self.logger.error("ADC returned measurement of 0 (indicating something is wrong).")
            return

        index = 0
        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.value_set(channel, voltages_list[index])
                index += 1

        return self.return_dict
