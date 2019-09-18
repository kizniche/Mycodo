# coding=utf-8
import time

from mycodo.databases.models import Output
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.database import db_retrieve_table_daemon

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
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'gpio_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio')
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.temp_temperature = 0
        self.temp_humidity = 0
        self.temp_dew_point = None
        self.temp_vpd = None
        self.power_output_id = None
        self.powered = False

        if not testing:
            import pigpio
            from mycodo.mycodo_client import DaemonControl

            self.gpio = int(input_dev.gpio_location)
            self.power_output_id = input_dev.power_output_id

            self.control = DaemonControl()
            self.pigpio = pigpio
            self.pi = self.pigpio.pi()

            self.high_tick = None
            self.bit = None
            self.either_edge_cb = None

        self.start_input()

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.return_dict = measurements_dict.copy()

        if not self.pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod."
                              "Ensure it is running and try again.")
            return None, None, None

        import pigpio
        self.pigpio = pigpio

        # Ensure if the power pin turns off, it is turned back on
        if (self.power_output_id and
                db_retrieve_table_daemon(Output, unique_id=self.power_output_id) and
                self.control.output_state(self.power_output_id) == 'off'):
            self.logger.error(
                'Sensor power output {rel} detected as being off. '
                'Turning on.'.format(rel=self.power_output_id))
            self.start_input()
            time.sleep(2)

        # Try twice to get measurement. This prevents an anomaly where
        # the first measurement fails if the sensor has just been powered
        # for the first time.
        for _ in range(2):
            self.measure_sensor()
            if self.temp_dew_point is not None:
                if self.is_enabled(0):
                    self.value_set(0, self.temp_temperature)
                if self.is_enabled(1):
                    self.value_set(1, self.temp_humidity)
                if (self.is_enabled(2) and
                        self.is_enabled(0) and
                        self.is_enabled(1)):
                    self.value_set(2, self.temp_dew_point)
                if (self.is_enabled(3) and
                        self.is_enabled(0) and
                        self.is_enabled(1)):
                    self.value_set(3, self.temp_vpd)
                return self.return_dict  # success - no errors
            time.sleep(2)

        # Measurement failure, power cycle the sensor (if enabled)
        # Then try two more times to get a measurement
        if self.power_output_id is not None and self.running:
            self.stop_input()
            time.sleep(2)
            self.start_input()
            for _ in range(2):
                self.measure_sensor()
                if self.temp_dew_point is not None:
                    if self.is_enabled(0):
                        self.value_set(0, self.temp_temperature)
                    if self.is_enabled(1):
                        self.value_set(1, self.temp_humidity)
                    if (self.is_enabled(2) and
                            self.is_enabled(0) and
                            self.is_enabled(1)):
                        self.value_set(2, self.temp_dew_point)
                    if (self.is_enabled(3) and
                            self.is_enabled(0) and
                            self.is_enabled(1)):
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
                    'Could not initialize sensor. Check if gpiod is running. '
                    'Error: {msg}'.format(msg=except_msg))
            self.pi.write(self.gpio, self.pigpio.LOW)
            time.sleep(0.017)  # 17 ms
            self.pi.set_mode(self.gpio, self.pigpio.INPUT)
            self.pi.set_watchdog(self.gpio, 200)
            time.sleep(0.2)
            if self.temp_humidity != 0:
                self.temp_dew_point = calculate_dewpoint(
                    self.temp_temperature, self.temp_humidity)
                self.temp_vpd = calculate_vapor_pressure_deficit(
                    self.temp_temperature, self.temp_humidity)
        except Exception as e:
            self.logger.error(
                "Exception raised when taking a reading: {err}".format(
                    err=e))
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
        """ Monitors RISING_EDGE changes using callback """
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
        """ Handle Rise signal """
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
                    self.logger.debug(
                        "Exception raised when taking a reading: "
                        "Bad Checksum.")
        elif 16 <= self.bit < 24:  # in temperature byte
            self.temp_temperature = (self.temp_temperature << 1) + val
        elif 0 <= self.bit < 8:  # in humidity byte
            self.temp_humidity = (self.temp_humidity << 1) + val
        self.bit += 1

    def _edge_fall(self, tick, diff):
        """ Handle Fall signal """
        self.high_tick = tick
        if diff <= 250000:
            return
        self.bit = -2
        self.checksum = 0
        self.temp_temperature = 0
        self.temp_humidity = 0

    def _edge_either(self, tick, diff):
        """ Handle Either signal """
        self.pi.set_watchdog(self.gpio, 0)

    def close(self):
        """ Stop reading sensor, remove callbacks """
        self.pi.set_watchdog(self.gpio, 0)
        if self.either_edge_cb:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None

    def start_input(self):
        """ Power the sensor """
        if self.power_output_id:
            self.logger.info("Turning on sensor")
            self.control.output_on(
                self.control.pyro_server._pyroUri,
                self.power_output_id, 0)
            time.sleep(2)
            self.powered = True

    def stop_input(self):
        """ Depower the sensor """
        if self.power_output_id:
            self.logger.info("Turning off sensor")
            self.control.output_off(
                self.control.pyro_server._pyroUri,
                self.power_output_id)
            self.powered = False
