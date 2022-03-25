# coding=utf-8
import copy
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'DHT11',
    'input_manufacturer': 'AOSONG',
    'input_name': 'DHT11',
    'input_library': 'pigpio',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'http://www.adafruit.com/datasheets/DHT11-chinese.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/386',

    'options_enabled': [
        'gpio_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio'),
        ('pip-pypi', 'pigpio', 'pigpio==1.78')
    ],

    'interfaces': ['GPIO']
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the DHT11's humidity and temperature
    and calculates the dew point

    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    """
    def __init__(self, input_dev, testing=False):
        """
        :param gpio: gpio pin number
        :type gpio: int
        :param power: Power pin number
        :type power: int

        Instantiate with the Pi and gpio to which the DHT11 output
        pin is connected.

        Optionally a gpio used to power the sensor may be specified.
        This gpio will be set high to power the sensor.

        """
        super().__init__(input_dev, testing=testing, name=__name__)

        self.pi = None
        self.pigpio = None
        self.gpio = None
        self.control = None

        self.temp_temperature = 0
        self.temp_humidity = 0
        self.temp_dew_point = None
        self.temp_vpd = None
        self.powered = False

        if not testing:
            self.try_initialize()

    def initialize(self):
        import pigpio
        from mycodo.mycodo_client import DaemonControl

        self.gpio = int(self.input_dev.gpio_location)

        self.control = DaemonControl()
        self.pigpio = pigpio
        self.pi = self.pigpio.pi()

        self.high_tick = None
        self.bit = None
        self.either_edge_cb = None

    def get_measurement(self):
        """Gets the humidity and temperature."""
        if not self.pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod. Ensure it is running and try again.")
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        import pigpio
        self.pigpio = pigpio

        # Try twice to get measurement. This prevents an anomaly where
        # the first measurement fails if the sensor has just been powered
        # for the first time.
        for _ in range(2):
            self.measure_sensor()
            if self.temp_dew_point is not None:
                self.value_set(0, self.temp_temperature)
                self.value_set(1, self.temp_humidity)
                self.value_set(2, self.temp_dew_point)
                self.value_set(3, self.temp_vpd)
                return self.return_dict  # success - no errors
            time.sleep(2)

        self.logger.error("Could not acquire a measurement")
        return None

    def measure_sensor(self):
        self.temp_temperature = 0
        self.temp_humidity = 0
        self.temp_dew_point = None
        self.temp_vpd = None

        try:
            try:
                self.setup()
            except Exception as except_msg:
                self.logger.error(
                    'Could not initialize sensor. Check if gpiod is running. Error: {msg}'.format(msg=except_msg))
            self.pi.write(self.gpio, self.pigpio.LOW)
            time.sleep(0.017)  # 17 ms
            self.pi.set_mode(self.gpio, self.pigpio.INPUT)
            self.pi.set_watchdog(self.gpio, 200)
            time.sleep(0.2)
            if self.temp_humidity != 0:
                self.temp_dew_point = calculate_dewpoint(self.temp_temperature, self.temp_humidity)
                self.temp_vpd = calculate_vapor_pressure_deficit(self.temp_temperature, self.temp_humidity)
        except Exception as e:
            self.logger.error("Exception raised when taking a reading: {err}".format(err=e))
        finally:
            self.close()
            return (self.temp_dew_point,
                    self.temp_humidity,
                    self.temp_temperature)

    def setup(self):
        """
        Clears the internal gpio pull-up/down resistor.
        Kills any watchdogs.
        Setup callbacks
        """
        self.high_tick = 0
        self.bit = 40
        self.either_edge_cb = None
        self.pi.set_pull_up_down(self.gpio, self.pigpio.PUD_OFF)
        self.pi.set_watchdog(self.gpio, 0)
        self.register_callbacks()

    def register_callbacks(self):
        """Monitors RISING_EDGE changes using callback."""
        self.either_edge_cb = self.pi.callback(
            self.gpio,
            self.pigpio.EITHER_EDGE,
            self.either_edge_callback)

    def either_edge_callback(self, gpio, level, tick):
        """
        Either Edge callbacks, called each time the gpio edge changes.
        Accumulate the 40 data bits from the DHT11 sensor.
        """
        level_handlers = {
            self.pigpio.FALLING_EDGE: self._edge_fall,
            self.pigpio.RISING_EDGE: self._edge_rise,
            self.pigpio.EITHER_EDGE: self._edge_either
        }
        handler = level_handlers[level]
        diff = self.pigpio.tickDiff(self.high_tick, tick)
        handler(tick, diff)

    def _edge_rise(self, tick, diff):
        """Handle Rise signal."""
        val = 0
        if diff >= 50:
            val = 1
        if diff >= 200:  # Bad bit?
            self.checksum = 256  # Force bad checksum
        if self.bit >= 40:  # Message complete
            self.bit = 40
        elif self.bit >= 32:  # In checksum byte
            self.checksum = (self.checksum << 1) + val
            if self.bit == 39:
                # 40th bit received
                self.pi.set_watchdog(self.gpio, 0)
                total = self.temp_humidity + self.temp_temperature
                # is checksum ok ?
                if not (total & 255) == self.checksum:
                    # For some reason the port from python 2 to python 3 causes
                    # this bad checksum error to happen during every read
                    # TODO: Investigate how to properly check the checksum in python 3
                    self.logger.debug("Exception raised when taking a reading: Bad Checksum.")
        elif 16 <= self.bit < 24:  # in temperature byte
            self.temp_temperature = (self.temp_temperature << 1) + val
        elif 0 <= self.bit < 8:  # in humidity byte
            self.temp_humidity = (self.temp_humidity << 1) + val
        self.bit += 1

    def _edge_fall(self, tick, diff):
        """Handle Fall signal."""
        self.high_tick = tick
        if diff <= 250000:
            return
        self.bit = -2
        self.checksum = 0
        self.temp_temperature = 0
        self.temp_humidity = 0

    def _edge_either(self, tick, diff):
        """Handle Either signal."""
        self.pi.set_watchdog(self.gpio, 0)

    def close(self):
        """Stop reading sensor, remove callbacks."""
        self.pi.set_watchdog(self.gpio, 0)
        if self.either_edge_cb:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None
