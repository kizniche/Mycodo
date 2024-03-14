# coding=utf-8
import time

import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'revolutions',
        'unit': 'rpm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SIGNAL_RPM',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'Signal (Revolutions) (pigpio method #1)',
    'input_name_short': 'Signal, RPM (#1)',
    'input_library': 'pigpio',
    'measurements_name': 'RPM',
    'measurements_dict': measurements_dict,

'message': 'This calculates RPM from pulses on a pin using pigpio, but has been found to be less accurate than the method #2 module. This is typically used to measure the speed of a fan from a tachometer pin, however this can be used to measure any 3.3-volt pulses from a wire. Use a resistor to pull the measurement pin to 3.3 volts, set pigpio to the lowest latency (1 ms) on the Configure -> Raspberry Pi page. Note 1: Not setting pigpio to the lowest latency will hinder accuracy. Note 2: accuracy decreases as RPM increases.',

    'options_enabled': [
        'gpio_location',
        'rpm_pulses_per_rev',
        'weighting',
        'sample_time',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/Mycodo/pigpio_installed', 'pigpio'),
        ('pip-pypi', 'pigpio', 'pigpio==1.78')
    ],

    'interfaces': ['GPIO'],
    'weighting': 0.0,
    'sample_time': 2.0,
    'rpm_pulses_per_rev': 1.0
}


class InputModule(AbstractInput):
    """A sensor support class that monitors rpm."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.pigpio = None
        self.gpio = None
        self.weighting = None
        self.rpm_pulses_per_rev = None
        self.sample_time = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import pigpio

        self.pigpio = pigpio

        self.gpio = int(self.input_dev.gpio_location)
        self.weighting = self.input_dev.weighting
        self.rpm_pulses_per_rev = self.input_dev.rpm_pulses_per_rev
        self.sample_time = self.input_dev.sample_time

    def get_measurement(self):
        """Gets the revolutions."""
        pi = self.pigpio.pi()
        if not pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod. Ensure it is running and try again.")
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        read_revolutions = ReadRPM(pi, self.gpio, self.pigpio, self.rpm_pulses_per_rev, self.weighting)
        time.sleep(self.sample_time)

        rpm = read_revolutions.RPM()

        read_revolutions.cancel()
        pi.stop()

        self.value_set(0, rpm)

        return self.return_dict


class ReadRPM:
    """
    A class to read pulses and calculate the RPM
    """

    def __init__(self, pi, gpio, pigpio, pulses_per_rev=1.0, weighting=0.0):
        """
        Instantiate with the Pi and gpio of the RPM signal
        to monitor.

        Optionally the number of pulses for a complete revolution
        may be specified. It defaults to 1.

        Optionally a weighting may be specified. This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading. It defaults to 0 which means
        the old reading has no effect. This may be used to
        smooth the data.
        """
        self.pigpio = pigpio
        self.pi = pi
        self.gpio = gpio
        self.pulses_per_rev = pulses_per_rev

        self._watchdog = 200  # Milliseconds.

        if weighting < 0.0:
            weighting = 0.0
        elif weighting > 0.99:
            weighting = 0.99

        self._new = 1.0 - weighting  # Weighting for new reading.
        self._old = weighting  # Weighting for old reading.

        self._high_tick = None
        self._period = None

        pi.set_mode(self.gpio, self.pigpio.INPUT)

        self._cb = pi.callback(self.gpio, self.pigpio.RISING_EDGE, self._cbf)
        pi.set_watchdog(self.gpio, self._watchdog)

    def _cbf(self, gpio, level, tick):
        if level == 1:  # Rising edge.
            if self._high_tick is not None:
                t = self.pigpio.tickDiff(self._high_tick, tick)
                if self._period is not None:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t
            self._high_tick = tick
        elif level == 2:  # Watchdog timeout.
            if self._period is not None:
                if self._period < 2000000000:
                    self._period += self._watchdog * 1000

    def RPM(self):
        """
        Returns the RPM.
        """
        rpm = 0
        if self._period is not None:
            rpm = 60000000.0 / (self._period * self.pulses_per_rev)
        return rpm

    def cancel(self):
        """
        Cancels the reader and releases resources.
        """
        self.pi.set_watchdog(self.gpio, 0)  # cancel watchdog
        self._cb.cancel()
