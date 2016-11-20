# coding=utf-8
import atexit
import logging
import time
import pigpio
from sensorutils import dewpoint
from .base_sensor import AbstractSensor

logger = logging.getLogger(__name__)


class DHT22Sensor(AbstractSensor):
    """
    A sensor support class that measures the DHT22's humidity and temperature
    and calculates the dew point

    The sensor is also known as the AM2302.
    The sensor can be powered from the Pi 3V3 or the Pi 5V rail.
    Powering from the 3V3 rail is simpler and safer.  You may need
    to power from 5V if the sensor is connected via a long cable.
    For 3V3 operation connect pin 1 to 3V3 and pin 4 to ground.
    Connect pin 2 to a gpio.
    For 5V operation connect pin 1 to 5V and pin 4 to ground.
    The following pin 2 connection works for me.  Use at YOUR OWN RISK.

    5V--5K_resistor--+--10K_resistor--Ground
                     |
    DHT22 pin 2 -----+
                     |
    gpio ------------+
    """

    def __init__(self, pi, gpio, power=None):
        """
        Instantiate with the Pi and gpio to which the DHT22 output
        pin is connected.

        Optionally a gpio used to power the sensor may be specified.
        This gpio will be set high to power the sensor.  If the sensor
        locks it will be power cycled to restart the readings.

        Taking readings more often than about once every two seconds will
        eventually cause the DHT22 to hang.  A 3 second interval seems OK.
        """
        super(DHT22Sensor, self).__init__()
        self.pi = pi
        self.gpio = gpio
        self.power = power
        self.bad_CS = 0  # Bad checksum count
        self.bad_SM = 0  # Short message count
        self.bad_MM = 0  # Missing message count
        self.bad_SR = 0  # Sensor reset count

        # Power cycle if timeout > MAX_TIMEOUTS
        self.no_response = 0
        self.MAX_NO_RESPONSE = 2

        self.tov = None
        self.high_tick = 0
        self.bit = 40
        self.either_edge_cb = None
        self._dew_point = 0.0
        self._humidity = 0.0
        self._temperature = 0.0

        # Prevent from crashing the mycodo daemon if pigpiod isn't running
        try:
            self.setup()
        except:
            raise Exception('DHT22 could not initialize. Check if gpiod is running.')

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dew_point={dpt})(humidity={hum})(temperature={temp})>".format(
            cls=type(self).__name__,
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Dew Point: {dpt}, Humidity: {hum}, Temperature: {temp}".format(
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ DHT22Sensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(dew_point=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def dew_point(self):
        """ DHT22 dew point in Celsius """
        if not self._dew_point:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ DHT22 relative humidity in percent """
        if not self._humidity:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ DHT22 temperature in Celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        if self.power is not None:
            print("Turning sensor at GPIO {}...".format(self.gpio))
            self.pi.write(self.power, 1)  # Switch sensor on.
            time.sleep(2)
        atexit.register(self.close)
        self.pi.write(self.gpio, pigpio.LOW)
        time.sleep(0.017)  # 17 ms
        self.pi.set_mode(self.gpio, pigpio.INPUT)
        self.pi.set_watchdog(self.gpio, 200)
        time.sleep(0.2)
        self._dew_point = dewpoint(self._temperature, self._humidity)

    def read(self):
        """
        Takes a reading from the DHT22 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            self.get_measurement()
            # self_humidity and self._temperature are set in self._edge_rise()
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1

    def setup(self):
        """
        Clears the internal gpio pull-up/down resistor.
        Kills any watchdogs.
        Setup callbacks
        """
        self.pi.set_pull_up_down(self.gpio, pigpio.PUD_OFF)
        self.pi.set_watchdog(self.gpio, 0)  # Kill any watchdogs.
        self.register_callbacks()

    def register_callbacks(self):
        """
        Monitors RISING_EDGE changes using callback.
        """
        self.either_edge_cb = self.pi.callback(self.gpio,
                                               pigpio.EITHER_EDGE,
                                               self.either_edge_callback)

    def either_edge_callback(self, gpio, level, tick):
        """
        Either Edge callbacks, called each time the gpio edge changes.

        Accumulate the 40 data bits from the dht22 sensor.

        Format into 5 bytes, humidity high,
        humidity low, temperature high, temperature low, checksum.
        """
        level_handlers = {
            pigpio.FALLING_EDGE: self._edge_fall,
            pigpio.RISING_EDGE: self._edge_rise,
            pigpio.EITHER_EDGE: self._edge_either
        }
        handler = level_handlers[level]
        diff = pigpio.tickDiff(self.high_tick, tick)
        handler(tick, diff)

    def _edge_rise(self, tick, diff):
        """
        Handle Rise signal.
        """
        # Edge length determines if bit is 1 or 0.
        if diff >= 50:
            val = 1
            if diff >= 200:  # Bad bit?
                self.CS = 256  # Force bad checksum.
        else:
            val = 0

        if self.bit >= 40:  # Message complete.
            self.bit = 40
        elif self.bit >= 32:  # In checksum byte.
            self.CS = (self.CS << 1) + val
            if self.bit == 39:
                # 40th bit received.
                self.pi.set_watchdog(self.gpio, 0)
                self.no_response = 0
                total = self.hH + self.hL + self.tH + self.tL
                if (total & 255) == self.CS:  # Is checksum ok?
                    self._humidity = ((self.hH << 8) + self.hL) * 0.1
                    if self.tH & 128:  # Negative temperature.
                        mult = -0.1
                        self.tH &= 127
                    else:
                        mult = 0.1
                    self._temperature = ((self.tH << 8) + self.tL) * mult
                    self.tov = time.time()
                else:
                    self.bad_CS += 1
        elif self.bit >= 24:  # in temp low byte
            self.tL = (self.tL << 1) + val
        elif self.bit >= 16:  # in temp high byte
            self.tH = (self.tH << 1) + val
        elif self.bit >= 8:  # in humidity low byte
            self.hL = (self.hL << 1) + val
        elif self.bit >= 0:  # in humidity high byte
            self.hH = (self.hH << 1) + val
        self.bit += 1

    def _edge_fall(self, tick, diff):
        """
        Handle Fall signal.
        """
        # Edge length determines if bit is 1 or 0.
        self.high_tick = tick
        if diff <= 250000:
            return
        self.bit = -2
        self.hH = 0
        self.hL = 0
        self.tH = 0
        self.tL = 0
        self.CS = 0

    def _edge_either(self, tick, diff):
        """
        Handle Either signal or Timeout
        """
        self.pi.set_watchdog(self.gpio, 0)
        if self.bit < 8:  # Too few data bits received.
            self.bad_MM += 1  # Bump missing message count.
            self.no_response += 1
            if self.no_response > self.MAX_NO_RESPONSE:
                self.no_response = 0
                self.bad_SR += 1  # Bump sensor reset count.
                if self.power is not None:
                    self.powered = False
                    self.pi.write(self.power, 0)
                    time.sleep(2)
                    self.pi.write(self.power, 1)
                    time.sleep(2)
                    self.powered = True
        elif self.bit < 39:  # Short message receieved.
            self.bad_SM += 1  # Bump short message count.
            self.no_response = 0
        else:  # Full message received.
            self.no_response = 0

    def staleness(self):
        """Return time since measurement made."""
        if self.tov is not None:
            return time.time() - self.tov
        else:
            return -999

    def bad_checksum(self):
        """Return count of messages received with bad checksums."""
        return self.bad_CS

    def short_message(self):
        """Return count of short messages."""
        return self.bad_SM

    def missing_message(self):
        """Return count of missing messages."""
        return self.bad_MM

    def sensor_resets(self):
        """Return count of power cycles because of sensor hangs."""
        return self.bad_SR

    def close(self):
        """
        Stop reading sensor, remove callbacks.
        """
        self.pi.set_watchdog(self.gpio, 0)
        if self.either_edge_cb:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None
