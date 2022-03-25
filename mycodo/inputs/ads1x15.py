# coding=utf-8
import timeit
from collections import OrderedDict

import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput


def constraints_pass_measurement_repetitions(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: integer
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure 1 <= value <= 1000
    if value < 1 or value > 1000:
        all_passed = False
        errors.append("Must be a positive value between 1 and 1000")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = OrderedDict()
for each_channel in range(4):
    measurements_dict[each_channel] = {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADS1x15',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1x15',
    'input_library': 'Adafruit_ADS1x15 [DEPRECATED]',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'measurements_rescale': True,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096,

    'message': "The Adafruit_ADS1x15 is deprecated. It's advised to use The Circuit Python ADS1x15 Input.",

    'options_enabled': [
        'measurements_select',
        'channels_convert',
        'i2c_location',
        'adc_gain',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3'),
        ('pip-pypi', 'Adafruit_ADS1x15', 'Adafruit-ADS1x15==1.0.2')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49', '0x4A', '0x4B'],
    'i2c_address_editable': False,

    'adc_gain': [(0, '2/3 (±6.144 V)'),
                 (1, '1 (±4.096 V)'),
                 (2, '2 (±2.048 V)'),
                 (4, '4 (±1.024 V)'),
                 (8, '8 (±0.512 V)'),
                 (16, '16 (±0.256 V)')],

    'custom_options': [
        {
            'id': 'measurements_for_average',
            'type': 'integer',
            'default_value': 5,
            'constraints_pass': constraints_pass_measurement_repetitions,
            'name': lazy_gettext('Measurements to Average'),
            'phrase': lazy_gettext(
                'The number of times to measure each channel. An average of the measurements will be stored.')
        },
    ]
}


class InputModule(AbstractInput):
    """
    Read ADC

    Choose a gain of 1 for reading measurements from 0 to 4.09V.
    Or pick a different gain to change the range of measurements that are read:
     - 2/3 = ±6.144 V
     -   1 = ±4.096 V
     -   2 = ±2.048 V
     -   4 = ±1.024 V
     -   8 = ±0.512 V
     -  16 = ±0.256 V
    See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
    """
    def __init__(self, input_dev, testing=False,):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.adc = None
        self.adc_gain = None

        self.dict_gains = {
            2/3: 0.1875,
            1: 0.125,
            2: 0.0625,
            4: 0.03125,
            8: 0.015625,
            16: 0.0078125,
        }

        self.measurements_for_average = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)

            self.try_initialize()

    def initialize(self):
        import Adafruit_ADS1x15

        if self.input_dev.adc_gain == 0:
            self.adc_gain = 2/3
        else:
            self.adc_gain = self.input_dev.adc_gain

        self.adc = Adafruit_ADS1x15.ADS1115(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)

    def get_measurement(self):
        if not self.adc:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        measurement_range = 1
        if self.measurements_for_average:
            measurement_range = self.measurements_for_average

        # Conduct multiple measurements for averaging
        measurement_totals = {}
        time_start = timeit.default_timer()
        for _ in range(measurement_range):
            for channel in self.channels_measurement:
                if self.is_enabled(channel):
                    if channel not in measurement_totals:
                        measurement_totals[channel] = 0
                    measurement_totals[channel] += (
                        self.adc.read_adc(channel, gain=self.adc_gain) * self.dict_gains[self.adc_gain] / 1000.0)

        self.logger.debug("All measurements completed in {:.3f} seconds".format(
            timeit.default_timer() - time_start))

        # Store average measurement for each channel
        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.value_set(
                    channel,
                    measurement_totals[channel] / measurement_range)

        return self.return_dict
