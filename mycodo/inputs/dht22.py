# coding=utf-8
import logging
import time

from .base_input import AbstractInput
from sensorutils import dewpoint
from mycodo.databases.models import Output
from mycodo.utils.database import db_retrieve_table_daemon


class DHT22Sensor(AbstractInput):
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
    def __init__(self, sensor_id, gpio, power=None, testing=False):
        """
        :param gpio: gpio pin number
        :type gpio: int
        :param power: Power pin number
        :type power: int

        Instantiate with the Pi and gpio to which the DHT22 output
        pin is connected.

        Optionally a gpio used to power the sensor may be specified.
        This gpio will be set high to power the sensor.  If the sensor
        locks it will be power cycled to restart the readings.

        Taking readings more often than about once every two seconds will
        eventually cause the DHT22 to hang.  A 3 second interval seems OK.
        """
        super(DHT22Sensor, self).__init__()
        self.logger = logging.getLogger('mycodo.inputs.dht22')

        self._dew_point = None
        self._humidity = None
        self._temperature = None

        self._temp_dew_point = None
        self._temp_humidity = None
        self._temp_temperature = None

        if not testing:
            import pigpio
            from mycodo.mycodo_client import DaemonControl
            self.control = DaemonControl()
    
            self.pigpio = pigpio
            self.pi = pigpio.pi()
            self.gpio = gpio
            self.power_relay_id = power
            self.powered = False
    
            self.bad_CS = 0  # Bad checksum count
            self.bad_SM = 0  # Short message count
            self.bad_MM = 0  # Missing message count
            self.bad_SR = 0  # Sensor reset count
    
            # Power cycle if timeout > MAX_NO_RESPONSE
            self.MAX_NO_RESPONSE = 3
            self.no_response = None
            self.tov = None
            self.high_tick = None
            self.bit = None
            self.either_edge_cb = None
    
            self.start_sensor()

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dewpoint={dpt})(humidity={hum})(temperature={temp})>".format(
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
        return dict(dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def dew_point(self):
        """ DHT22 dew point in Celsius """
        if self._dew_point is None:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ DHT22 relative humidity in percent """
        if self._humidity is None:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ DHT22 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self._dew_point = None
        self._humidity = None
        self._temperature = None

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
        for _ in range(3):
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
                self._temp_dew_point = dewpoint(self._temp_temperature, self._temp_humidity)
            except Exception as e:
                self.logger.exception(
                    "Exception when taking a reading: {err}".format(
                        err=e))
            finally:
                self.close()
            if self._humidity is not None:
                return self._temp_dew_point, self._temp_humidity, self._temp_temperature
            time.sleep(2)

        # Measurement failure, power cycle the sensor (if enabled)
        # Then try two more times to get a measurement
        if self.power_relay_id is not None:
            self.stop_sensor()
            time.sleep(5)
            self.start_sensor()
            for _ in range(2):
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
                    self._temp_dew_point = dewpoint(self._temp_temperature, self._temp_humidity)
                except Exception as e:
                    self.logger.exception(
                        "Exception when taking a reading: {err}".format(
                            err=e))
                finally:
                    self.close()
                if self._humidity is not None:
                    return self._temp_dew_point, self._temp_humidity, self._temp_temperature
                time.sleep(2)

        self.logger.debug("Could not acquire a measurement")
            

    def read(self):
        """
        Takes a reading from the DHT22 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            self._dew_point, self._humidity, self._temperature = self.get_measurement()
            if self._dew_point is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

    def setup(self):
        """
        Clears the internal gpio pull-up/down resistor.
        Kills any watchdogs.
        Setup callbacks
        """
        self._temp_humidity = None
        self._temp_temperature = None
        self._temp_dew_point = None
        self.no_response = 0
        self.tov = None
        self.high_tick = 0
        self.bit = 40
        self.either_edge_cb = None
        self.pi.set_pull_up_down(self.gpio, self.pigpio.PUD_OFF)
        self.pi.set_watchdog(self.gpio, 0)  # Kill any watchdogs
        self.register_callbacks()

    def register_callbacks(self):
        """ Monitors RISING_EDGE changes using callback """
        self.either_edge_cb = self.pi.callback(self.gpio,
                                               self.pigpio.EITHER_EDGE,
                                               self.either_edge_callback)

    def either_edge_callback(self, gpio, level, tick):
        """
        Either Edge callbacks, called each time the gpio edge changes.
        Accumulate the 40 data bits from the DHT22 sensor.

        Format into 5 bytes, humidity high,
        humidity low, temperature high, temperature low, checksum.
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
                    self._temp_humidity = ((self.hH << 8) + self.hL) * 0.1
                    if self.tH & 128:  # Negative temperature.
                        mult = -0.1
                        self.tH &= 127
                    else:
                        mult = 0.1
                    self._temp_temperature = ((self.tH << 8) + self.tL) * mult
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
        """ Handle Fall signal """
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
        """ Handle Either signal or Timeout """
        self.pi.set_watchdog(self.gpio, 0)
        if self.bit < 8:  # Too few data bits received.
            self.bad_MM += 1  # Bump missing message count.
            self.no_response += 1
            if self.no_response > self.MAX_NO_RESPONSE:
                self.no_response = 0
                self.bad_SR += 1  # Bump sensor reset count.
                if self.power_relay_id is not None:
                    self.logger.error(
                        "Invalid data, power cycling sensor.")
                    self.stop_sensor()
                    time.sleep(2)
                    self.start_sensor()
        elif self.bit < 39:  # Short message received.
            self.bad_SM += 1  # Bump short message count.
            self.no_response = 0
        else:  # Full message received.
            self.no_response = 0

    def staleness(self):
        """ Return time since measurement made """
        if self.tov is not None:
            return time.time() - self.tov
        else:
            return -999

    def bad_checksum(self):
        """ Return count of messages received with bad checksums """
        return self.bad_CS

    def short_message(self):
        """ Return count of short messages """
        return self.bad_SM

    def missing_message(self):
        """ Return count of missing messages """
        return self.bad_MM

    def sensor_resets(self):
        """ Return count of power cycles because of sensor hangs """
        return self.bad_SR

    def close(self):
        """ Stop reading sensor, remove callbacks """
        self.pi.set_watchdog(self.gpio, 0)
        if self.either_edge_cb:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None

    def start_sensor(self):
        """ Turn the sensor on """
        if self.power_relay_id:
            self.logger.info("Turning on sensor")
            self.control.relay_on(self.power_relay_id, 0)
            time.sleep(2)
            self.powered = True

    def stop_sensor(self):
        """ Turn the sensor off """
        if self.power_relay_id:
            self.logger.info("Turning off sensor")
            self.control.relay_off(self.power_relay_id)
            self.powered = False
