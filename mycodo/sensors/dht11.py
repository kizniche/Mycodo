# coding=utf-8
import logging
import time
import pigpio

from .base_sensor import AbstractSensor
from sensorutils import dewpoint
from mycodo.databases.mycodo_db.models import Relay
from mycodo.utils.database import db_retrieve_table_daemon

from mycodo.mycodo_client import DaemonControl


class DHT11Sensor(AbstractSensor):
    """
    A sensor support class that measures the DHT11's humidity and temperature
    and calculates the dew point

    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    """
    def __init__(self, sensor_id, gpio, power=None):
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
        self.logger = logging.getLogger(
            'mycodo.sensor_{id}'.format(id=sensor_id))

        self.control = DaemonControl()

        self.pi = pigpio.pi()
        self.gpio = gpio
        self.power_relay_id = power
        self.powered = False
        self.high_tick = None
        self.bit = None
        self.either_edge_cb = None
        self._dew_point = 0.0
        self._humidity = 0
        self._temperature = 0

        self.start_sensor()
        time.sleep(2)

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
        if not self._dew_point:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ DHT11 relative humidity in percent """
        if not self._humidity:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ DHT11 temperature in Celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self._humidity = 0.0
        self._temperature = 0.0

        # Ensure if the power pin turns off, it is turned back on
        if (self.power_relay_id and
                not db_retrieve_table_daemon(Relay, device_id=self.power_relay_id).is_on()):
            self.logger.error(
                'Sensor power relay {rel} detected as being off. '
                'Turning on.'.format(rel=self.power_relay_id))
            self.start_sensor()
            time.sleep(2)

        try:
            try:
                self.setup()
            except Exception as except_msg:
                self.logger.error(
                    'Could not initialize sensor. Check if gpiod is running. '
                    'Error: {msg}'.format(msg=except_msg))
            self.pi.write(self.gpio, pigpio.LOW)
            time.sleep(0.017)  # 17 ms
            self.pi.set_mode(self.gpio, pigpio.INPUT)
            self.pi.set_watchdog(self.gpio, 200)
            time.sleep(0.2)
            self._dew_point = dewpoint(self._temperature, self._humidity)
        except Exception as e:
            self.logger.error(
                "Exception raised when taking a reading: {err}".format(
                    err=e))
        finally:
            self.close()

    def read(self):
        """
        Takes a reading from the DHT11 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            self.get_measurement()
            if self._humidity != 0 or self._temperature != 0:
                return  # success - no errors
            self.logger.debug("Could not acquire a measurement")
        except Exception as e:
            self.logger.error(
                "Exception raised when taking a reading: {err}".format(
                    err=e))
        return 1

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
        self.pi.set_pull_up_down(self.gpio, pigpio.PUD_OFF)
        self.pi.set_watchdog(self.gpio, 0)
        self.register_callbacks()

    def register_callbacks(self):
        """ Monitors RISING_EDGE changes using callback """
        self.either_edge_cb = self.pi.callback(
            self.gpio,
            pigpio.EITHER_EDGE,
            self.either_edge_callback)

    def either_edge_callback(self, gpio, level, tick):
        """
        Either Edge callbacks, called each time the gpio edge changes.
        Accumulate the 40 data bits from the DHT11 sensor.
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
                total = self._humidity + self._temperature
                # is checksum ok ?
                if not (total & 255) == self.checksum:
                    self.logger.error(
                        "Exception raised when taking a reading: "
                        "Bad Checksum.")
        elif 16 <= self.bit < 24:  # in temperature byte
            self._temperature = (self._temperature << 1) + val
        elif 0 <= self.bit < 8:  # in humidity byte
            self._humidity = (self._humidity << 1) + val
        self.bit += 1

    def _edge_fall(self, tick, diff):
        """ Handle Fall signal """
        self.high_tick = tick
        if diff <= 250000:
            return
        self.bit = -2
        self.checksum = 0

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
