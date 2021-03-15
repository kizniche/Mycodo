# coding=utf-8
import time

import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'rate_volume',
        'unit': 'l_min'
    },
    1: {
        'measurement': 'volume',
        'unit': 'l'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HALL_FLOW',
    'input_manufacturer': 'Generic',
    'input_name': 'Hall Flow Meter',
    'input_library': 'pigpio',
    'measurements_name': 'Flow Rate, Total Volume',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'gpio_location',
        'weighting',
        'sample_time',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'id': 'k_value',
            'type': 'float',
            'default_value': 1.0,
            'name': lazy_gettext('Pulses per Liter'),
            'phrase': lazy_gettext("Enter the conversion factor for this meter (pulses to Liter).")
        }
    ],

    'weighting': 0.0,
    'sample_time': 2.0,

    'custom_actions_message': 'The total session volume can be cleared with the following button or as a Function Action.',
    'custom_actions': [
        {
            'id': 'clear_session_total_volume',
            'type': 'button',
            'name': lazy_gettext('Clear Total Volume')
        }
    ]

}


class InputModule(AbstractInput):
    """ A sensor support class that monitors flow rate / volume """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor_is_measuring = False
        self.sensor_is_clearing = False

        self.pigpio = None
        self.gpio = None
        self.flow_rate_unit = None
        self.k_value = None
        self.sample_time = None
        self.weighting = None
        self.session_total_volume = 0.0

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import pigpio

        self.pigpio = pigpio
        self.gpio = int(self.input_dev.gpio_location)
        self.weighting = self.input_dev.weighting
        self.sample_time = self.input_dev.sample_time

    def get_measurement(self):
        """ Gets the flow rate and volume """
        pi = self.pigpio.pi()
        if not pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod. Ensure it is running and try again.")
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        while self.sensor_is_clearing:
            time.sleep(0.1)
        self.sensor_is_measuring = True

        total_pulses = None
        flow_rate_raw = None
        flow_rate = None

        read_flow = ReadHall(pi, self.gpio, self.pigpio, self.k_value, self.weighting)
        time.sleep(self.sample_time)

        flow_rate_raw = read_flow.flow()
        if flow_rate_raw:
            flow_rate = float(flow_rate_raw)

        total_pulses = int(read_flow.pulses())

        if total_pulses:
            self.session_total_volume += float(total_pulses * self.k_value)

        read_flow.cancel()
        pi.stop()

        if flow_rate or flow_rate == 0.0:
            self.value_set(0, flow_rate)
        if self.session_total_volume or self.session_total_volume == 0.0:
            self.value_set(1, self.session_total_volume)

        return self.return_dict

    def clear_total_session_volume(self, args_dict):
        while self.sensor_is_measuring:
            time.sleep(0.1)
        self.sensor_is_clearing = True
        self.session_total_volume = float(0.0)
        self.sensor_is_clearing = False
        return 1, "Success"


class ReadHall:
    """
    A class to read pulses and calculate the Flow Rate
    """

    def __init__(self, pi, gpio, pigpio, pulses_per_l=1.0, weight=0.0):
        """
        Instantiate with the Pi and gpio of the signal to monitor.

        Optionally a weighting may be specified. This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading. It defaults to 0 which means
        the old reading has no effect. This may be used to
        smooth the data.
        """
        self.pigpio = pigpio
        self.pi = pi
        self.gpio = int(gpio)
        self.pulses_per_l = float(pulses_per_l)

        self._watchdog = 200  # Milliseconds.

        if weight < 0.0:
            weight = 0.0
        elif weight > 0.99:
            weight = 0.99

        self._new = 1.0 - weight  # Weighting for new reading.
        self._old = weight  # Weighting for old reading.

        self._high_tick = None
        self._period = None
        self._total_pulses = None

        pi.set_mode(self.gpio, self.pigpio.INPUT)

        self._cb = pi.callback(self.gpio, self.pigpio.RISING_EDGE, self._cbf)
        pi.set_watchdog(self.gpio, self._watchdog)

    def _cbf(self, gpio, level, tick):
        if level == 1:  # Rising edge.
            if self._high_tick is not None:
                t = self.pigpio.tickDiff(self._high_tick, tick)
                if self._total_pulses is not None:
                    self._total_pulses += int(1)
                else:
                    self._total_pulses = int(1)
                if self._period is not None:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t
            self._high_tick = tick
        elif level == 2:  # Watchdog timeout.
            if self._period is not None:
                if self._period < 2000000000:
                    self._period += (self._watchdog * 1000)

    def flow(self):
        """
        Returns the Flow Rate.
        """
        flow = 0.0
        if self._period is not None:
            flow = 60000000.0 / (self._period * self.pulses_per_l)
        return flow

    def pulses(self):
        """
        Returns the total pulses.
        """
        if self._total_pulses is not None:
            return self._total_pulses
        else:
            return 0

    def cancel(self):
        """
        Cancels the reader and releases resources.
        """
        self.pi.set_watchdog(self.gpio, 0)  # cancel watchdog
        self._cb.cancel()
