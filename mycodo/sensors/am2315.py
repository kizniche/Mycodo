# coding=utf-8
import logging
import time
from tentacle_pi import AM2315
from sensorutils import dewpoint
from .base_sensor import AbstractSensor

from mycodo.databases.models import Relay
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.mycodo_client import DaemonControl


class AM2315Sensor(AbstractSensor):
    """
    A sensor support class that measures the AM2315's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, sensor_id, bus, power=None):
        super(AM2315Sensor, self).__init__()
        self.logger = logging.getLogger(
            'mycodo.sensor_{id}'.format(id=sensor_id))

        self.control = DaemonControl()

        self.I2C_bus_number = str(bus)
        self.power_relay_id = power
        self.powered = False
        self._dew_point = 0.0
        self._humidity = 0.0
        self._temperature = 0.0
        self.am = None

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
        """ AM2315Sensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    def info(self):
        conditions_measured = [
            ("Dew Point", "dewpoint", "float", "0.00",
             self._dew_point, self.dew_point),
            ("Humidity", "humidity", "float", "0.00",
             self._humidity, self.humidity),
            ("Temperature", "temperature", "float", "0.00",
             self._temperature, self.temperature)
        ]
        return conditions_measured

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
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        # Ensure if the power pin turns off, it is turned back on
        if (self.power_relay_id and
                not db_retrieve_table_daemon(Relay, device_id=self.power_relay_id).is_on()):
            self.logger.error(
                'Sensor power relay {rel} detected as being off. '
                'Turning on.'.format(rel=self.power_relay_id))
            self.start_sensor()
            time.sleep(2)

        self.am = AM2315.AM2315(0x5c, "/dev/i2c-" + self.I2C_bus_number)

        # Retry measurement if CRC fails
        for num_measure in range(3):
            temperature, humidity, crc_check = self.am.sense()
            if crc_check != 1:
                self.logger.debug("Measurement {num} returned failed CRC".format(
                    num=num_measure))
                pass
            else:
                dew_pt = dewpoint(temperature, humidity)
                return dew_pt, humidity, temperature
            time.sleep(3)

        self.logger.error("All measurements returned failed CRC")
        return None, None, None

    def read(self):
        """
        Takes a reading from the AM2315 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            # Try twice to get measurement. This prevents an anomaly where
            # the first measurement fails if the sensor has just been powered
            # for the first time.
            for _ in range(2):
                self._dew_point, self._humidity, self._temperature = self.get_measurement()
                if self._dew_point is not None:
                    return  # success - no errors
                time.sleep(2)

            # Measurement failure, power cycle the sensor (if enabled)
            # Then try two more times to get a measurement
            if self.power_relay_id is not None:
                self.stop_sensor()
                time.sleep(2)
                self.start_sensor()
                for _ in range(2):
                    self._dew_point, self._humidity, self._temperature = self.get_measurement()
                    if self._dew_point is not None:
                        return  # success - no errors
                    time.sleep(2)

            self.logger.debug("Could not acquire a measurement")
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

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