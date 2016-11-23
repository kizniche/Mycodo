# coding=utf-8
import atexit
import logging
import time
import pigpio
from sensorutils import dewpoint
from .base_sensor import AbstractSensor

logger = logging.getLogger(__name__)


class DHT11Sensor(AbstractSensor):
    """
    A sensor support class that measures the AM2315's humidity and temperature
    and calculates the dew point

    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    example code:
    >>> pi = pigpio.pi()
    >>> sensor = DHT11Sensor(pi, 4) # 4 is the data GPIO pin connected to your sensor
    >>> for response in sensor:
    ....    print("Temperature: {}".format(response['temperature']))
    ....    print("Humidity: {}".format(response['humidity']))
    """

    def __init__(self, pi, gpio, power=None):
        """
        :param pi: an instance of pigpio
        :type pi: pigpio
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
        self.pi = pi
        self.gpio = gpio
        self.power = power
        self.high_tick = 0
        self.bit = 40
        self.either_edge_cb = None
        self._dew_point = 0.0
        self._humidity = 0.0
        self._temperature = 0.0

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
        """ AM2315Sensor iterates through live measurement readings """
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
        """ AM2315 dew point in Celsius """
        if not self._dew_point:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ AM2315 relative humidity in percent """
        if not self._humidity:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ AM2315 temperature in Celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        if self.power is not None:
            print("Turning on sensor at GPIO {}...".format(self.gpio))
            self.pi.write(self.power, 1)  # Switch sensor on.
            time.sleep(2)
        atexit.register(self.close)
        self.setup()
        self.pi.write(self.gpio, pigpio.LOW)
        time.sleep(0.017)  # 17 ms
        self.pi.set_mode(self.gpio, pigpio.INPUT)
        self.pi.set_watchdog(self.gpio, 200)
        time.sleep(0.2)
        self._dew_point = dewpoint(self._temperature, self._humidity)

    def read(self):
        """
        Takes a reading from the AM2315 and updates the self.dew_point,
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
        self.pi.set_watchdog(self.gpio, 0)
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
        Accumulate the 40 data bits from the dht11 sensor.
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
                total = self._humidity + self._temperature
                # is checksum ok ?
                if not (total & 255) == self.checksum:
                    raise Exception
        elif 16 <= self.bit < 24:  # in temperature byte
            self._temperature = (self._temperature << 1) + val
        elif 0 <= self.bit < 8:  # in humidity byte
            self._humidity = (self._humidity << 1) + val
        self.bit += 1

    def _edge_fall(self, tick, diff):
        """
        Handle Fall signal.
        """
        self.high_tick = tick
        if diff <= 250000:
            return
        self.bit = -2
        self.checksum = 0
        self._temperature = 0
        self._humidity = 0

    def _edge_either(self, tick, diff):
        """
        Handle Either signal.
        """
        self.pi.set_watchdog(self.gpio, 0)

    def close(self):
        """
        Stop reading sensor, remove callbacks.
        """
        self.pi.set_watchdog(self.gpio, 0)
        if self.either_edge_cb:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None
