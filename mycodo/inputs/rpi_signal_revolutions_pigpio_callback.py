# coding=utf-8
import time

import copy
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value

# Measurements
measurements_dict = {
    0: {
        'measurement': 'revolutions',
        'unit': 'rpm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SIGNAL_RPM_PIGPIO',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'Signal (Revolutions) (pigpio method #2)',
    'input_name_short': 'Signal, RPM (#2)',
    'input_library': 'pigpio',
    'measurements_name': 'RPM',
    'measurements_dict': measurements_dict,

    'message': 'This is an alternate method to calculate RPM from pulses on a pin using pigpio, and has been found to be more accurate than the method #1 module. This is typically used to measure the speed of a fan from a tachometer pin, however this can be used to measure any 3.3-volt pulses from a wire. Use a resistor to pull the measurement pin to 3.3 volts, set pigpio to the lowest latency (1 ms) on the Configure -> Raspberry Pi page. Note 1: Not setting pigpio to the lowest latency will hinder accuracy. Note 2: accuracy decreases as RPM increases.',

    'options_enabled': [
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/Mycodo/pigpio_installed', 'pigpio'),
        ('pip-pypi', 'pigpio', 'pigpio==1.78')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'pin',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {} ({})".format(lazy_gettext('Pin'), lazy_gettext('GPIO'), lazy_gettext('BCM')),
            'phrase': 'The pin to measure pulses from'
        },
        {
            'id': 'sample_time',
            'type': 'float',
            'default_value': 5.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(TRANSLATIONS['sample_time']['title'], lazy_gettext('Seconds')),
            'phrase': TRANSLATIONS['sample_time']['phrase']
        },
        {
            'id': 'pulse_factor',
            'type': 'float',
            'default_value': 15.8,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': TRANSLATIONS['rpm_pulses_per_rev']['title'],
            'phrase': TRANSLATIONS['rpm_pulses_per_rev']['phrase']
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors rpm."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.pigpio = None

        self.pin = None
        self.sample_time = None
        self.pulse_factor = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import pigpio

        self.pigpio = pigpio

    def get_measurement(self):
        """Gets the revolutions."""
        pi = self.pigpio.pi()
        if not pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod. Ensure it is running and try again.")
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        callback = pi.callback(self.pin)
        start = time.time()
        time.sleep(self.sample_time)
        count = callback.tally()
        end = time.time()
        count_seconds = end - start
        callback.cancel()
        pi.stop()

        rpm = int(float(count / self.pulse_factor) * 60 / count_seconds)

        self.logger.debug(f"Counted {count} pulses in {count_seconds:.5f}s. Calculates to {rpm} RPM")

        self.value_set(0, rpm)

        return self.return_dict
