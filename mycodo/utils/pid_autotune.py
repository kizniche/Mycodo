# coding=utf-8
import logging
import math
from collections import deque, namedtuple
from time import time

# Based on:
# https://raw.githubusercontent.com/hirschmann/pid-autotune
# See https://github.com/t0mpr1c3/Arduino-PID-AutoTune-Library

class PIDAutotune(object):
    """
    Determines viable parameters for a PID controller.

    Args:
        setpoint (float): The target value.
        out_step (float): The value by which the output will be
            increased/decreased when stepping up/down.
        sampletime (float): The interval between run() calls.
        loockback (float): The reference period for local minima/maxima.
        out_min (float): Lower output limit.
        out_max (float): Upper output limit.
        noiseband (float): Determines by how much the input value must
            overshoot/undershoot the setpoint before the state changes.
        time (function): A function which returns the current time in seconds.
    """
    PIDParams = namedtuple('PIDParams', ['Kp', 'Ki', 'Kd'])

    PEAK_AMPLITUDE_TOLERANCE = 0.05
    STATE_OFF = 'off'
    STATE_RELAY_STEP_UP = 'relay step up'
    STATE_RELAY_STEP_DOWN = 'relay step down'
    STATE_SUCCEEDED = 'succeeded'
    STATE_FAILED = 'failed'

    _tuning_rules = {
        # rule: [Kp_divisor, Ki_divisor, Kd_divisor]
        "ziegler-nichols": [34, 40, 160],
        "tyreus-luyben": [44,  9, 126],
        "ciancone-marlin": [66, 88, 162],
        "pessen-integral": [28, 50, 133],
        "some-overshoot": [60, 40,  60],
        "no-overshoot": [100, 40,  60],
        "brewing": [2.5, 6, 380]
    }

    def __init__(self, setpoint, out_step=10, sampletime=5, lookback=60,
                 out_min=float('-inf'), out_max=float('inf'), noiseband=0.5, time=time):
        if setpoint is None:
            raise ValueError('setpoint must be specified')
        if out_step < 1:
            raise ValueError('out_step must be greater or equal to 1')
        if sampletime < 1:
            raise ValueError('sampletime must be greater or equal to 1')
        if lookback < sampletime:
            raise ValueError('lookback must be greater or equal to sampletime')
        if out_min >= out_max:
            raise ValueError('out_min must be less than out_max')

        self._time = time
        self._logger = logging.getLogger(type(self).__name__)
        self._inputs = deque(maxlen=round(lookback / sampletime))
        self._sampletime = sampletime * 1000
        self._setpoint = setpoint
        self._outputstep = out_step
        self._noiseband = noiseband
        self._out_min = out_min
        self._out_max = out_max
        self._state = PIDAutotune.STATE_OFF
        self._peak_timestamps = deque(maxlen=5)
        self._peaks = deque(maxlen=5)
        self._output = 0
        self._last_run_timestamp = 0
        self._peak_type = 0
        self._peak_count = 0
        self._initial_output = 0
        self._induced_amplitude = 0
        self._Ku = 0
        self._Pu = 0

    @property
    def state(self):
        """Get the current state."""
        return self._state

    @property
    def output(self):
        """Get the last output value."""
        return self._output

    @property
    def tuning_rules(self):
        """Get a list of all available tuning rules."""
        return self._tuning_rules.keys()

    def get_pid_parameters(self, tuning_rule='ziegler-nichols'):
        """Get PID parameters.

        Args:
            tuning_rule (str): Sets the rule which should be used to calculate
                the parameters.
        """
        divisors = self._tuning_rules[tuning_rule]
        kp = self._Ku / divisors[0]
        ki = kp / (self._Pu / divisors[1])
        kd = kp * (self._Pu / divisors[2])
        return PIDAutotune.PIDParams(kp, ki, kd)

    def run(self, input_val):
        """To autotune a system, this method must be called periodically.

        Args:
            input_val (float): The input value.

        Returns:
            `true` if tuning is finished, otherwise `false`.
        """
        now = self._time() * 1000

        if (self._state == PIDAutotune.STATE_OFF
                or self._state == PIDAutotune.STATE_SUCCEEDED
                or self._state == PIDAutotune.STATE_FAILED):
            self._init_tuner(input_val, now)
        elif (now - self._last_run_timestamp) < self._sampletime:
            return False

        self._last_run_timestamp = now

        # check input and change relay state if necessary
        if (self._state == PIDAutotune.STATE_RELAY_STEP_UP
                and input_val > self._setpoint + self._noiseband):
            self._state = PIDAutotune.STATE_RELAY_STEP_DOWN
            self._logger.debug('switched state: {0}'.format(self._state))
            self._logger.debug('input: {0}'.format(input_val))
        elif (self._state == PIDAutotune.STATE_RELAY_STEP_DOWN
                and input_val < self._setpoint - self._noiseband):
            self._state = PIDAutotune.STATE_RELAY_STEP_UP
            self._logger.debug('switched state: {0}'.format(self._state))
            self._logger.debug('input: {0}'.format(input_val))

        # set output
        if self._state == PIDAutotune.STATE_RELAY_STEP_UP:
            self._output = self._initial_output + self._outputstep
        elif self._state == PIDAutotune.STATE_RELAY_STEP_DOWN:
            self._output = self._initial_output - self._outputstep

        # respect output limits
        self._output = min(self._output, self._out_max)
        self._output = max(self._output, self._out_min)

        # identify peaks
        is_max = True
        is_min = True

        for val in self._inputs:
            is_max = is_max and (input_val >= val)
            is_min = is_min and (input_val <= val)

        self._inputs.append(input_val)

        # we don't want to trust the maxes or mins until the input array is full
        if len(self._inputs) < self._inputs.maxlen:
            return False

        # increment peak count and record peak time for maxima and minima
        inflection = False

        # peak types:
        # -1: minimum
        # +1: maximum
        if is_max:
            if self._peak_type == -1:
                inflection = True
            self._peak_type = 1
        elif is_min:
            if self._peak_type == 1:
                inflection = True
            self._peak_type = -1

        # update peak times and values
        if inflection:
            self._peak_count += 1
            self._peaks.append(input_val)
            self._peak_timestamps.append(now)
            self._logger.debug('found peak: {0}'.format(input_val))
            self._logger.debug('peak count: {0}'.format(self._peak_count))

        # check for convergence of induced oscillation
        # convergence of amplitude assessed on last 4 peaks (1.5 cycles)
        self._induced_amplitude = 0

        if inflection and (self._peak_count > 4):
            abs_max = self._peaks[-2]
            abs_min = self._peaks[-2]
            for i in range(0, len(self._peaks) - 2):
                self._induced_amplitude += abs(self._peaks[i] - self._peaks[i+1])
                abs_max = max(self._peaks[i], abs_max)
                abs_min = min(self._peaks[i], abs_min)

            self._induced_amplitude /= 6.0

            # check convergence criterion for amplitude of induced oscillation
            amplitude_dev = ((0.5 * (abs_max - abs_min) - self._induced_amplitude)
                             / self._induced_amplitude)

            self._logger.debug('amplitude: {0}'.format(self._induced_amplitude))
            self._logger.debug('amplitude deviation: {0}'.format(amplitude_dev))

            if amplitude_dev < PIDAutotune.PEAK_AMPLITUDE_TOLERANCE:
                self._state = PIDAutotune.STATE_SUCCEEDED

        # if the autotune has not already converged
        # terminate after 10 cycles
        if self._peak_count >= 20:
            self._output = 0
            self._state = PIDAutotune.STATE_FAILED
            return True

        if self._state == PIDAutotune.STATE_SUCCEEDED:
            self._output = 0

            # calculate ultimate gain
            self._Ku = 4.0 * self._outputstep / (self._induced_amplitude * math.pi)

            # calculate ultimate period in seconds
            period1 = self._peak_timestamps[3] - self._peak_timestamps[1]
            period2 = self._peak_timestamps[4] - self._peak_timestamps[2]
            self._Pu = 0.5 * (period1 + period2) / 1000.0
            return True
        return False

    def _init_tuner(self, inputValue, timestamp):
        self._peak_type = 0
        self._peak_count = 0
        self._output = 0
        self._initial_output = 0
        self._Ku = 0
        self._Pu = 0
        self._inputs.clear()
        self._peaks.clear()
        self._peak_timestamps.clear()
        self._peak_timestamps.append(timestamp)
        self._state = PIDAutotune.STATE_RELAY_STEP_UP
