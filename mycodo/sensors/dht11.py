# coding=utf-8
# !/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import time
import pigpio
from sensorutils import dewpoint


class DHT11(object):
    """
    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    example code:
    >>> pi = pigpio.pi()
    >>> sensor = DHT11(pi, 4) # 4 is the data GPIO pin connected to your sensor
    >>> for response in sensor:
    ....    print("Temperature: {}".format(response['temperature']))
    ....    print("Humidity: {}".format(response['humidity']))
    """

    def __init__(self, pi, gpio, LED=None, power=None):
        """
        :param pi: an instance of pigpio
        :type pi: pigpio
        :param gpio: gpio pin number
        :type gpio: int
        :param LED: LED pin number
        :type LED: int
        :param power: Power pin number
        :type power: int

        Instantiate with the Pi and gpio to which the DHT11 output
        pin is connected.

        Optionally a LED may be specified.  This will be blinked for
        each successful reading.

        Optionally a gpio used to power the sensor may be specified.
        This gpio will be set high to power the sensor.

        """
        self.pi = pi
        self.gpio = gpio
        self.LED = LED
        self.power = power

        if power is not None:
            print("Turning on sensor at GPIO {}...".format(self.gpio))
            pi.write(power, 1)  # Switch sensor on.
            time.sleep(2)

        self.powered = True
        atexit.register(self.close)

        self._temperature = 0
        self._humidity = 0

        self.high_tick = 0
        self.bit = 40

        self.either_edge_cb = None

        self.running = True
        self.setup()

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
                                               self.either_edge_callback
                                               )

    def either_edge_callback(self, gpio, level, tick):
        """
        Either Edge callbacks, called each time the gpio edge changes.
        Accumulate the 40 data bits from the dht11 sensor.
        """
        level_handlers = {
            pigpio.FALLING_EDGE: self._edge_FALL,
            pigpio.RISING_EDGE: self._edge_RISE,
            pigpio.EITHER_EDGE: self._edge_EITHER
        }
        handler = level_handlers[level]
        diff = pigpio.tickDiff(self.high_tick, tick)
        handler(tick, diff)

    def _edge_RISE(self, tick, diff):
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
                    raise
        elif 16 <= self.bit < 24:  # in temperature byte
            self._temperature = (self._temperature << 1) + val
        elif 0 <= self.bit < 8:  # in humidity byte
            self._humidity = (self._humidity << 1) + val
        else:  # skip header bits
            pass
        self.bit += 1

    def _edge_FALL(self, tick, diff):
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

    def _edge_EITHER(self, tick, diff):
        """
        Handle Either signal.
        """
        self.pi.set_watchdog(self.gpio, 0)

    def read(self):
        """
        Start reading over DHT11 sensor.
        """
        if self.powered:
            if self.LED is not None:
                self.pi.write(self.LED, 1)
            try:
                self.pi.write(self.gpio, pigpio.LOW)
                time.sleep(0.017)  # 17 ms
                self.pi.set_mode(self.gpio, pigpio.INPUT)
                self.pi.set_watchdog(self.gpio, 200)
                time.sleep(0.2)
            except:
                return 1

    def close(self):
        """
        Stop reading sensor, remove callbacks.
        """
        self.pi.set_watchdog(self.gpio, 0)
        if self.either_edge_cb:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity


    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature and humidity information.
        """
        if self.read():
            return None
        response = {
            'humidity': float("{0:.2f}".format(self.humidity)),
            'temperature': float("{0:.2f}".format(self.temperature)),
            'dewpoint': float("{0:.2f}".format(dewpoint(self.temperature, self.humidity)))
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == '__main__':
    pi = pigpio.pi()
    sensor = DHT11(pi, 4)
    try:
        for measurements in sensor:
            print("Temperature: {}".format(measurements['temperature']))
            print("Humidity: {}".format(measurements['humidity']))
            print("Dew Point: {}".format(dewpoint(measurements['temperature'], measurements['humidity'])))
            time.sleep(1)
    except KeyboardInterrupt:
        sensor.close()
        pi.stop()