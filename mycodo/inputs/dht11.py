# coding=utf-8
import logging
import time

from mycodo.databases.models import Output
from mycodo.utils.database import db_retrieve_table_daemon
from .base_input import AbstractInput
from .sensorutils import convert_units
from .sensorutils import dewpoint


class DHT11Sensor(AbstractInput):
    """
    A sensor support class that measures the DHT11's humidity and temperature
    and calculates the dew point

    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    """
    def __init__(self, sensor_id, gpio, power=None, convert_to_unit=None, testing=False):
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
        super(DHT11Sensor, self).__init__()
        self.logger = logging.getLogger('mycodo.inputs.dht11')

        self._dew_point = None
        self._humidity = None
        self._temperature = None

        self.temp_temperature = 0
        self.temp_humidity = 0
        self.temp_dew_point = None

        self.convert_to_unit = convert_to_unit
        self.power_relay_id = power
        self.powered = False

        if not testing:
            import pigpio
            from mycodo.mycodo_client import DaemonControl

            self.logger = logging.getLogger(
                'mycodo.inputs.dht11_{id}'.format(id=sensor_id))

            self.control = DaemonControl()

            self.pigpio = pigpio
            self.pi = self.pigpio.pi()
            self.gpio = gpio

            self.high_tick = None
            self.bit = None
            self.either_edge_cb = None

        self.start_sensor()

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dewpoint={dpt})(humidity={hum})(temperature={temp})>".format(
            cls=type(self).__name__,
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(float(self._humidity)),
            temp="{0:.2f}".format(float(self._temperature)))

    def __str__(self):
        """ Return measurement information """
        return "Dew Point: {dpt}, Humidity: {hum}, Temperature: {temp}".format(
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(float(self._humidity)),
            temp="{0:.2f}".format(float(self._temperature)))

    def __iter__(self):  # must return an iterator
        """ DHT11Sensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float("{0:.2f}".format(float(self._humidity))),
                    temperature=float("{0:.2f}".format(float(self._temperature))))

    @property
    def dew_point(self):
        """ DHT11 dew point in Celsius """
        if self._dew_point is None:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ DHT11 relative humidity in percent """
        if self._humidity is None:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ DHT11 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        if not self.pi.connected:  # Check if pigpiod is running
            self.logger.error("Could not connect to pigpiod."
                              "Ensure it is running and try again.")
            return None, None, None

        import pigpio
        self.pigpio = pigpio

        # Ensure if the power pin turns off, it is turned back on
        if (self.power_relay_id and
                not db_retrieve_table_daemon(Output, device_id=self.power_relay_id).is_on()):
            self.logger.error(
                'Sensor power relay {rel} detected as being off. '
                'Turning on.'.format(rel=self.power_relay_id))
            self.start_sensor()
            time.sleep(2)

        # Try twice to get measurement. This prevents an anomaly where
        # the first measurement fails if the sensor has just been powered
        # for the first time.
        for _ in range(2):
            self.measure_sensor()
            if self.temp_dew_point is not None:
                self.temp_dew_point = convert_units(
                    'dewpoint', 'celsius', self.convert_to_unit,
                    self.temp_dew_point)
                self.temp_temperature = convert_units(
                    'temperature', 'celsius', self.convert_to_unit,
                    self.temp_temperature)
                return (self.temp_dew_point,
                        self.temp_humidity,
                        self.temp_temperature)  # success - no errors
            time.sleep(2)

        # Measurement failure, power cycle the sensor (if enabled)
        # Then try two more times to get a measurement
        if self.power_relay_id is not None:
            self.stop_sensor()
            time.sleep(2)
            self.start_sensor()
            for _ in range(2):
                self.measure_sensor()
                if self.temp_dew_point is not None:
                    self.temp_dew_point = convert_units(
                        'dewpoint', 'celsius', self.convert_to_unit,
                        self.temp_dew_point)
                    self.temp_temperature = convert_units(
                        'temperature', 'celsius', self.convert_to_unit,
                        self.temp_temperature)
                    return (self.temp_dew_point,
                            self.temp_humidity,
                            self.temp_temperature)  # success - no errors
                time.sleep(2)

        self.logger.error("Could not acquire a measurement")
        return None, None, None

    def read(self):
        """
        Takes a reading from the DHT11 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._dew_point,
             self._humidity,
             self._temperature) = self.get_measurement()
            if self._dew_point is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

    def measure_sensor(self):
        self.temp_temperature = 0
        self.temp_humidity = 0
        self.temp_dew_point = None

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
                self.temp_dew_point = dewpoint(
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
        self._humidity = 0
        self._temperature = 0
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

    def start_sensor(self):
        """ Power the sensor """
        if self.power_relay_id:
            self.logger.info("Turning on sensor")
            self.control.relay_on(self.power_relay_id, 0)
            time.sleep(2)
            self.powered = True

    def stop_sensor(self):
        """ Depower the sensor """
        if self.power_relay_id:
            self.logger.info("Turning off sensor")
            self.control.relay_off(self.power_relay_id)
            self.powered = False
