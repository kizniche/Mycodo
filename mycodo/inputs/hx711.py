# coding=utf-8
#
# hx711.py - Input for HX711 load cell amplifier
#
import copy
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'mass',
        'unit': 'g'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HX711',
    'input_manufacturer': 'Avia Semiconductor',
    'input_name': 'HX711',
    'input_library': 'hx711',
    'measurements_name': 'Mass',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.aviaic.com/',
    'url_datasheet': 'https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf',
    'url_product_purchase': 'https://www.amazon.com/s?k=hx711',

    'message': 'The HX711 is a precision 24-bit analog-to-digital converter (ADC) '
               'designed for weigh scales and industrial control applications. '
               'Connect DT to GPIO data pin and SCK to GPIO clock pin.',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1'),
        ('pip-pypi', 'hx711', 'hx711==1.1.2.3')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'pin_data',
            'type': 'integer',
            'default_value': 27,
            'name': lazy_gettext('Data Pin (DT)'),
            'phrase': lazy_gettext('The GPIO pin connected to the HX711 data pin (DT/DOUT)')
        },
        {
            'id': 'pin_clock',
            'type': 'integer',
            'default_value': 21,
            'name': lazy_gettext('Clock Pin (SCK)'),
            'phrase': lazy_gettext('The GPIO pin connected to the HX711 clock pin (SCK/PD_SCK)')
        },
        {
            'id': 'channel',
            'type': 'select',
            'default_value': 'A',
            'options_select': [
                ('A', 'Channel A'),
                ('B', 'Channel B')
            ],
            'name': lazy_gettext('Channel'),
            'phrase': lazy_gettext('The HX711 channel to read from')
        },
        {
            'id': 'gain',
            'type': 'select',
            'default_value': '128',
            'options_select': [
                ('128', '128 (Channel A)'),
                ('64', '64 (Channel A)'),
                ('32', '32 (Channel B)')
            ],
            'name': lazy_gettext('Gain'),
            'phrase': lazy_gettext('The gain for the HX711. Channel A supports 128 or 64, Channel B supports 32.')
        },
        {
            'id': 'samples',
            'type': 'integer',
            'default_value': 3,
            'name': lazy_gettext('Samples'),
            'phrase': lazy_gettext('The number of samples to average for each measurement')
        },
        {
            'id': 'tare_value',
            'type': 'float',
            'default_value': 0.0,
            'name': lazy_gettext('Tare Value'),
            'phrase': lazy_gettext('The raw value to subtract (tare). Set to 0 for no tare.')
        },
        {
            'id': 'calibration_factor',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Calibration Factor'),
            'phrase': lazy_gettext('The factor to convert raw value to grams. Raw value / calibration_factor = grams')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class for the HX711 load cell amplifier.
    
    The HX711 is a precision 24-bit analog-to-digital converter (ADC)
    designed for weigh scales and industrial control applications.
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.hx711 = None

        # Custom options
        self.pin_data = None
        self.pin_clock = None
        self.channel = None
        self.gain = None
        self.samples = None
        self.tare_value = None
        self.calibration_factor = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from hx711 import HX711

        self.hx711 = HX711(
            dout_pin=self.pin_data,
            pd_sck_pin=self.pin_clock,
            channel=self.channel,
            gain=int(self.gain)
        )
        self.hx711.reset()

    def get_measurement(self):
        """Get the mass measurement from the HX711."""
        if not self.hx711:
            self.logger.error(
                "Error 101: Device not set up. "
                "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            )
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            # Get raw data, averaging over samples
            raw_data = self.hx711.get_raw_data(num_measures=self.samples)
            
            if not raw_data:
                self.logger.error("No data received from HX711")
                return None

            # Calculate average
            raw_average = sum(raw_data) / len(raw_data)

            # Apply tare
            tared_value = raw_average - self.tare_value

            # Apply calibration factor to get grams
            if self.calibration_factor != 0:
                mass_grams = tared_value / self.calibration_factor
            else:
                mass_grams = tared_value

            self.value_set(0, mass_grams)

            return self.return_dict

        except Exception as e:
            self.logger.error("Error reading HX711: {err}".format(err=e))
            return None

    def stop_input(self):
        """Called when the input is stopped."""
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except Exception:
            pass
