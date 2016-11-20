# coding=utf-8
#
# Used, in part, from:
# http://www.raspberrypi-spy.co.uk/2016/07/using-bme280-i2c-temperature-pressure-sensor-in-python/

import logging
import smbus
import time
from ctypes import c_short
from sensorutils import dewpoint
from sensorutils import altitude
from .base_sensor import AbstractSensor

logger = logging.getLogger(__name__)


class BME280Sensor(AbstractSensor):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, address, bus):
        super(BME280Sensor, self).__init__()
        self.i2c_address = address
        self.bus = smbus.SMBus(bus)
        self._altitude = 0.0
        self._dew_point = 0.0
        self._humidity = 0.0
        self._pressure = 0
        self._temperature = 0.0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(altitude={alt})(dew_point={dpt})" \
               "(humidity={hum})(temperature={temp})>".format(
                cls=type(self).__name__,
                alt="{0:.2f}".format(self._altitude),
                dpt="{0:.2f}".format(self._dew_point),
                hum="{0:.2f}".format(self._humidity),
                press=self._pressure,
                temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Altitude: {alt}, Dew Point: {dpt}, " \
               "Humidity: {hum}, Pressure: {press}, " \
               "Temperature: {temp}".format(
                alt="{0:.2f}".format(self._altitude),
                dpt="{0:.2f}".format(self._dew_point),
                hum="{0:.2f}".format(self._humidity),
                press=self._pressure,
                temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(altitude=float('{0:.2f}'.format(self._altitude)),
                    dew_point=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    pressure=int(self._pressure),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        time.sleep(2)
        temperature, humidity, pressure = self.read_bme280_all()
        alt = altitude(pressure)
        dew_pt = dewpoint(temperature, humidity)
        return alt, dew_pt, humidity, pressure, temperature

    @property
    def altitude(self):
        """ BME280 altitude in meters """
        if not self._altitude:  # update if needed
            self.read()
        return self._altitude

    @property
    def dew_point(self):
        """ BME280 dew point in Celsius """
        if not self._dew_point:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ BME280 relative humidity in percent """
        if not self._humidity:  # update if needed
            self.read()
        return self._humidity

    @property
    def pressure(self):
        """ BME280 pressure in Pescals """
        if not self._pressure:  # update if needed
            self.read()
        return self._pressure

    @property
    def temperature(self):
        """ BME280 temperature in Celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def read(self):
        """
        Takes a reading from the BME280 and updates the self._humidity and
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._altitude,
             self._dew_point,
             self._humidity,
             self._pressure,
             self._temperature) = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1

    @staticmethod
    def get_short(data, index):
        # return two bytes from data as a signed 16-bit value
        return c_short((data[index + 1] << 8) + data[index]).value

    @staticmethod
    def get_ushort(data, index):
        # return two bytes from data as an unsigned 16-bit value
        return (data[index + 1] << 8) + data[index]

    @staticmethod
    def get_char(data, index):
        # return one byte from data as a signed char
        result = data[index]
        if result > 127:
            result -= 256
        return result

    @staticmethod
    def get_uchar(data, index):
        # return one byte from data as an unsigned char
        result = data[index] & 0xFF
        return result

    def read_bme280_id(self):
        # Chip ID Register self.i2c_address
        reg_id = 0xD0
        (chip_id, chip_version) = self.bus.read_i2c_block_data(self.i2c_address, reg_id, 2)
        return chip_id, chip_version

    def read_bme280_all(self):
        # Register self.i2c_address
        reg_data = 0xF7
        reg_control = 0xF4

        # REG_CONFIG  = 0xF5
        #
        # REG_HUM_MSB = 0xFD
        # REG_HUM_LSB = 0xFE

        # Oversample setting - page 27
        oversample_temp = 2
        oversample_pres = 2
        mode = 1

        control = oversample_temp << 5 | oversample_pres << 2 | mode
        self.bus.write_byte_data(self.i2c_address, reg_control, control)

        # Read blocks of calibration data from EEPROM
        # See Page 22 data sheet
        cal1 = self.bus.read_i2c_block_data(self.i2c_address, 0x88, 24)
        cal2 = self.bus.read_i2c_block_data(self.i2c_address, 0xA1, 1)
        cal3 = self.bus.read_i2c_block_data(self.i2c_address, 0xE1, 7)

        # Convert byte data to word values
        dig_t1 = self.get_ushort(cal1, 0)
        dig_t2 = self.get_short(cal1, 2)
        dig_t3 = self.get_short(cal1, 4)

        dig_p1 = self.get_ushort(cal1, 6)
        dig_p2 = self.get_short(cal1, 8)
        dig_p3 = self.get_short(cal1, 10)
        dig_p4 = self.get_short(cal1, 12)
        dig_p5 = self.get_short(cal1, 14)
        dig_p6 = self.get_short(cal1, 16)
        dig_p7 = self.get_short(cal1, 18)
        dig_p8 = self.get_short(cal1, 20)
        dig_p9 = self.get_short(cal1, 22)

        dig_h1 = self.get_uchar(cal2, 0)
        dig_h2 = self.get_short(cal3, 0)
        dig_h3 = self.get_uchar(cal3, 2)

        dig_h4 = self.get_char(cal3, 3)
        dig_h4 = (dig_h4 << 24) >> 20
        dig_h4 |= self.get_char(cal3, 4) & 0x0F

        dig_h5 = self.get_char(cal3, 5)
        dig_h5 = (dig_h5 << 24) >> 20
        dig_h5 |= self.get_uchar(cal3, 4) >> 4 & 0x0F

        dig_h6 = self.get_char(cal3, 6)

        # Read temperature/pressure/humidity
        data = self.bus.read_i2c_block_data(self.i2c_address, reg_data, 8)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]

        # Refine temperature
        var1 = (((temp_raw >> 3) - (dig_t1 << 1)) * dig_t2) >> 11
        var2 = (((((temp_raw >> 4) - dig_t1) * ((temp_raw >> 4) - dig_t1)) >> 12) * dig_t3) >> 14
        t_fine = var1 + var2
        temperature = float(((t_fine * 5) + 128) >> 8)

        # Refine pressure and adjust for temperature
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * dig_p6 / 32768.0
        var2 += var1 * dig_p5 * 2.0
        var2 = var2 / 4.0 + dig_p4 * 65536.0
        var1 = (dig_p3 * var1 * var1 / 524288.0 + dig_p2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * dig_p1
        if var1 == 0:
            pressure = 0
        else:
            pressure = 1048576.0 - pres_raw
            pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
            var1 = dig_p9 * pressure * pressure / 2147483648.0
            var2 = pressure * dig_p8 / 32768.0
            pressure += (var1 + var2 + dig_p7) / 16.0

        # Refine humidity
        humidity = t_fine - 76800.0
        humidity = (hum_raw - (dig_h4 * 64.0 + dig_h5 / 16384.8 * humidity)) * (
            dig_h2 / 65536.0 * (1.0 + dig_h6 / 67108864.0 * humidity * (1.0 + dig_h3 / 67108864.0 * humidity)))
        humidity *= 1.0 - dig_h1 * humidity / 524288.0
        if humidity > 100:
            humidity = 100
        elif humidity < 0:
            humidity = 0

        return temperature / 100.0, humidity, pressure / 100.0
