# coding=utf-8

import logging
import time
from .base_input import AbstractInput

logger = logging.getLogger("mycodo.inputs.signal_pwm")


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


class SignalPWMInput(AbstractInput):
    """ A sensor support class that monitors pwm """

    def __init__(self, pin, weighting, sample_time, testing=False):
        super(SignalPWMInput, self).__init__()
        self._frequency = None
        self._pulse_width = None
        self._duty_cycle = None

        self.pin = pin
        self.weighting = weighting
        self.sample_time = sample_time

        if not testing:
            import pigpio
            self.pigpio = pigpio

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(frequency={f})(pulse_width={pw})(duty_cycle={dc})>".format(
            cls=type(self).__name__,
            f="{0:.2f}".format(self._frequency),
            pw="{0:.2f}".format(self._pulse_width),
            dc="{0:.2f}".format(self._duty_cycle))

    def __str__(self):
        """ Return pwm information """
        return "Frequency: {f:.2f}, Pulse Width: {pw:.2f}, " \
               "Duty Cycle: {dc:.2f}".format(f=self._frequency,
                                             pw=self._pulse_width,
                                             dc=self._duty_cycle)

    def __iter__(self):  # must return an iterator
        """ Iterates through live pwm readings """
        return self

    def next(self):
        """ Get next pwm reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(frequency=float('{0:.2f}'.format(self._frequency)),
                    pulse_width=float('{0:.2f}'.format(self._pulse_width)),
                    duty_cycle=float('{0:.2f}'.format(self._duty_cycle)))

    @property
    def frequency(self):
        """ frequency """
        if self._frequency is None:  # update if needed
            self.read()
        return self._frequency

    @property
    def pulse_width(self):
        """ pulse width """
        if self._pulse_width is None:  # update if needed
            self.read()
        return self._pulse_width

    @property
    def duty_cycle(self):
        """ duty cycle """
        if self._duty_cycle is None:  # update if needed
            self.read()
        return self._duty_cycle

    def get_measurement(self):
        """ Gets the pwm """
        self._frequency = None
        self._pulse_width = None
        self._duty_cycle = None

        pi = self.pigpio.pi()
        read_pwm = ReadPWM(pi, self.pin, self.pigpio, self.weighting)
        time.sleep(self.sample_time)
        frequency = read_pwm.frequency()
        pulse_width = read_pwm.pulse_width()
        duty_cycle = read_pwm.duty_cycle()
        read_pwm.cancel()
        pi.stop()
        return frequency, int(pulse_width + 0.5), duty_cycle

    def read(self):
        """
        Takes a reading from the pin and updates the self._pwm value

        :returns: None on success or 1 on error
        """
        try:
            (self._frequency,
             self._pulse_width,
             self._duty_cycle) = self.get_measurement()
            if self._frequency is not None:
                return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1
