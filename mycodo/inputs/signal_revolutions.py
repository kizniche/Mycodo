# coding=utf-8
import logging
import time

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
    'input_manufacturer': 'Mycodo',
    'input_name': 'Signal (Revolutions)',
    'measurements_name': 'RPM',
    'measurements_dict': measurements_dict,

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
        ('internal', 'apt python3-pigpio', 'pigpio')
    ],

    'interfaces': ['GPIO'],
    'weighting': 0.0,
    'sample_time': 2.0,
    'rpm_pulses_per_rev': 1.0
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors rpm """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.signal_revolutions")

        if not testing:
            import pigpio
            self.logger = logging.getLogger(
                "mycodo.signal_revolutions_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.gpio = int(input_dev.gpio_location)
            self.weighting = input_dev.weighting
            self.rpm_pulses_per_rev = input_dev.rpm_pulses_per_rev
            self.sample_time = input_dev.sample_time
            self.pigpio = pigpio

    def get_measurement(self):
        """ Gets the revolutions """
        return_dict = measurements_dict.copy()

        pi = self.pigpio.pi()
        if not pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod."
                              "Ensure it is running and try again.")
            return None

        read_revolutions = ReadRPM(pi,
                                   self.gpio,
                                   self.pigpio,
                                   self.rpm_pulses_per_rev,
                                   self.weighting)
        time.sleep(self.sample_time)

        rpm = read_revolutions.RPM()
        if rpm:
            rpm = int(rpm + 0.5)

        read_revolutions.cancel()
        pi.stop()

        if rpm or rpm == 0:
            return_dict[0]['value'] = rpm
            return return_dict


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
                    self._period += (self._watchdog * 1000)

    def RPM(self):
        """
        Returns the RPM.
        """
        RPM = 0
        if self._period is not None:
            RPM = 60000000.0 / (self._period * self.pulses_per_rev)
        return RPM

    def cancel(self):
        """
        Cancels the reader and releases resources.
        """
        self.pi.set_watchdog(self.gpio, 0)  # cancel watchdog
        self._cb.cancel()
