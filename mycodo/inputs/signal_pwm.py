# coding=utf-8
import logging
import time

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'frequency': {
        'Hz': {0: {}}
    },
    'pulse_width': {
        'µs': {0: {}}
    },
    'duty_cycle': {
        'percent': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SIGNAL_PWM',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Signal (PWM)',
    'measurements_name': 'Frequency/Pulse Width/Duty Cycle',
    'measurements_dict': measurements,

    'options_enabled': [
        'gpio_location',
        'measurements_select',
        'measurements_convert',
        'weighting',
        'sample_time',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'pip-exists pigpio', 'pigpio')
    ],

    'interfaces': ['GPIO'],
    'weighting': 0.0,
    'sample_time': 2.0
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors pwm """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.signal_pwm")
        self._measurements = None

        if not testing:
            import pigpio
            self.logger = logging.getLogger(
                "mycodo.signal_pwm_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.gpio = int(input_dev.gpio_location)
            self.weighting = input_dev.weighting
            self.sample_time = input_dev.sample_time
            self.pigpio = pigpio

    def get_measurement(self):
        """ Gets the pwm """
        return_dict = {
            'frequency': {
                'Hz': {}
            },
            'pulse_width': {
                'µs': {}
            },
            'duty_cycle': {
                'percent': {}
            },
        }

        pi = self.pigpio.pi()
        if not pi.connected:  # Check if pigpiod is running
            self.logger.error(
                "Could not connect to pigpiod."
                "Ensure it is running and try again.")
            return None

        read_pwm = ReadPWM(pi, self.gpio, self.pigpio, self.weighting)

        time.sleep(self.sample_time)

        if self.is_enabled('frequency', 'Hz', 0):
            return_dict['frequency']['Hz'][0] = read_pwm.frequency()

        if self.is_enabled('pulse_width', 'µs', 0):
            return_dict['pulse_width']['µs'][0] = int(read_pwm.pulse_width() + 0.5)

        if self.is_enabled('duty_cycle', 'percent', 0):
            return_dict['duty_cycle']['percent'][0] = read_pwm.duty_cycle()

        read_pwm.cancel()
        pi.stop()

        return return_dict


class ReadPWM:
    """
    A class to read PWM pulses and calculate their frequency
    and duty cycle. The frequency is how often the pulse
    happens per second. The duty cycle is the percentage of
    pulse high time per cycle.
    """

    def __init__(self, pi, gpio, pigpio, weighting=0.0):
        """
        Instantiate with the Pi and gpio of the PWM signal
        to monitor.

        Optionally a weighting may be specified.  This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading.  It defaults to 0 which means
        the old reading has no effect.  This may be used to
        smooth the data.
        """
        self.pi = pi
        self.gpio = gpio
        self.pigpio = pigpio

        if weighting < 0.0:
            weighting = 0.0
        elif weighting > 0.99:
            weighting = 0.99

        self._new = 1.0 - weighting  # Weighting for new reading.
        self._old = weighting  # Weighting for old reading.

        self._high_tick = None
        self._period = None
        self._high = None

        pi.set_mode(gpio, pigpio.INPUT)
        self._cb = pi.callback(gpio, self.pigpio.EITHER_EDGE, self._cbf)

    def _cbf(self, gpio, level, tick):
        if level == 1:
            if self._high_tick is not None:
                t = self.pigpio.tickDiff(self._high_tick, tick)
                if self._period is not None:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t
            self._high_tick = tick
        elif level == 0:
            if self._high_tick is not None:
                t = self.pigpio.tickDiff(self._high_tick, tick)
                if self._high is not None:
                    self._high = (self._old * self._high) + (self._new * t)
                else:
                    self._high = t

    def frequency(self):
        """
        Returns the PWM frequency.
        """
        if self._period is not None:
            return 1000000.0 / self._period
        else:
            return 0.0

    def pulse_width(self):
        """
        Returns the PWM pulse width in microseconds.
        """
        if self._high is not None:
            return self._high
        else:
            return 0.0

    def duty_cycle(self):
        """
        Returns the PWM duty cycle percentage.
        """
        if self._high is not None:
            return 100.0 * self._high / self._period
        else:
            return 0.0

    def cancel(self):
        """
        Cancels the reader and releases resources.
        """
        self._cb.cancel()
