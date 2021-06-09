# coding=utf-8
import copy
import time

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
            'phrase': "Enter the conversion factor for this meter (pulses to Liter)."
        }
    ],

    'custom_actions_message': 'The total session volume can be cleared with the following button or as a Function Action.',
    'custom_actions': [
        {
            'id': 'clear_total_session_volume',
            'type': 'button',
            'name': lazy_gettext('Clear Total Volume')
        }
    ]

}


class InputModule(AbstractInput):
    """ A sensor support class that monitors flow rate / volume """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.pi = None
        self.gpio = None
        self.flow_rate_unit = None
        self.k_value = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import pigpio

        self.pi = pigpio.pi()
        self.gpio = int(self.input_dev.gpio_location)

        self.sensor = ReadHall(
            self.logger, self.pi, self.gpio, pigpio, self.k_value)

    def get_measurement(self):
        """ Gets the flow rate and volume """
        if not self.pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod. Ensure it is running and try again.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        l_min, pulses = self.sensor.flow_period()
        total_pulses = self.sensor.total_pulses()
        total_volume = self.sensor.total_volume()

        self.logger.debug(
            "fLow: {} l/min, pulses: {}, total pulses: {}, total volume: {}".format(
                l_min, pulses, total_pulses, total_volume))

        self.value_set(0, l_min)
        self.value_set(1, total_volume)

        return self.return_dict

    def stop_input(self):
        self.sensor.cancel()
        self.pi.stop()

    def clear_total_session_volume(self, args_dict):
        self.sensor.clear_totals()


class ReadHall:
    """A class to read pulses and calculate the Flow Rate"""
    def __init__(self, logger, pi, gpio, pigpio, pulses_per_l=1.0):
        self.logger = logger

        self.pigpio = pigpio
        self.pi = pi
        self.gpio = gpio
        self.pulses_per_l = pulses_per_l

        self._watchdog = 200  # Milliseconds.

        self._high_tick = None
        self._total_pulses = 0
        self._period_pulses = 0
        self._last_time = time.time()

        pi.set_mode(self.gpio, self.pigpio.INPUT)

        self._cb = pi.callback(self.gpio, self.pigpio.RISING_EDGE, self._cbf)
        pi.set_watchdog(self.gpio, self._watchdog)

    def _cbf(self, gpio, level, tick):
        if level == 1:  # Rising edge
            self.logger.debug("Rising edge detected")
            if self._high_tick is not None:
                t = self.pigpio.tickDiff(self._high_tick, tick)
                self._total_pulses += 1
                self._period_pulses += 1
            self._high_tick = tick

    def flow_period(self):
        """Returns the Flow Rate in l/min"""
        l_min = 0
        pulses = self.period_pulses()
        minutes = (time.time() - self._last_time) / 60
        if pulses:
            liters = pulses / self.pulses_per_l
            l_min = float(liters / minutes)
        self._last_time = time.time()
        return l_min, pulses

    def period_pulses(self):
        try:
            return self._period_pulses
        finally:
            self._period_pulses = 0

    def total_pulses(self):
        """Returns the total pulses"""
        return self._total_pulses

    def total_volume(self):
        """Returns the total volume in liters"""
        volume = 0
        if self._total_pulses:
            volume = float(self._total_pulses / self.pulses_per_l)
        return volume

    def cancel(self):
        """Cancels the reader and releases resources"""
        self.pi.set_watchdog(self.gpio, 0)  # cancel watchdog
        self._cb.cancel()

    def clear_totals(self):
        self._total_pulses = 0
