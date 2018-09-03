# coding=utf-8
# Copyright (c) 2016
# Author: Vitally Tezhe
import logging
import time

from .base_input import AbstractInput
from .sensorutils import altitude
from .sensorutils import convert_units

# Operating Modes
BMP280_ULTRALOWPOWER = 0
BMP280_STANDARD = 1
BMP280_HIGHRES = 2
BMP280_ULTRAHIGHRES = 3

# BMP280 Temperature Registers
BMP280_REGISTER_DIG_T1 = 0x88
BMP280_REGISTER_DIG_T2 = 0x8A
BMP280_REGISTER_DIG_T3 = 0x8C
# BMP280 Pressure Registers
BMP280_REGISTER_DIG_P1 = 0x8E
BMP280_REGISTER_DIG_P2 = 0x90
BMP280_REGISTER_DIG_P3 = 0x92
BMP280_REGISTER_DIG_P4 = 0x94
BMP280_REGISTER_DIG_P5 = 0x96
BMP280_REGISTER_DIG_P6 = 0x98
BMP280_REGISTER_DIG_P7 = 0x9A
BMP280_REGISTER_DIG_P8 = 0x9C
BMP280_REGISTER_DIG_P9 = 0x9E

BMP280_REGISTER_CONTROL = 0xF4
# Pressure measurments
BMP280_REGISTER_PRESSUREDATA_MSB = 0xF7
BMP280_REGISTER_PRESSUREDATA_LSB = 0xF8
BMP280_REGISTER_PRESSUREDATA_XLSB = 0xF9
# Temperature measurments
BMP280_REGISTER_TEMPDATA_MSB = 0xFA
BMP280_REGISTER_TEMPDATA_LSB = 0xFB
BMP280_REGISTER_TEMPDATA_XLSB = 0xFC

# Commands
BMP280_READCMD = 0x3F


class BMP280Sensor(AbstractInput):
    """
    A sensor support class that measures the BMP280's humidity,
    temperature, and pressure, then calculates the altitude and dew point

    """

    def __init__(self, input_dev, mode=BMP280_STANDARD, testing=False):
        super(BMP280Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.bmp280")
        self._altitude = None
        self._pressure = None
        self._temperature = None

        if not testing:
            import Adafruit_GPIO.I2C as I2C
            self.logger = logging.getLogger(
                "mycodo.inputs.bmp280_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            if mode not in [BMP280_ULTRALOWPOWER,
                            BMP280_STANDARD,
                            BMP280_HIGHRES,
                            BMP280_ULTRAHIGHRES]:
                raise ValueError(
                    'Unexpected mode value {0}.  Set mode to one of '
                    'BMP280_ULTRALOWPOWER, BMP280_STANDARD, BMP280_HIGHRES, '
                    'or BMP280_ULTRAHIGHRES'.format(mode))
            self._mode = mode
            # Create I2C device.
            i2c = I2C
            self._device = i2c.get_i2c_device(self.i2c_address,
                                              busnum=self.i2c_bus)
            # Load calibration values.
            self._load_calibration()
            self._tfine = 0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})(pressure={press})" \
               "(altitude={alt})>".format(
                cls=type(self).__name__,
                alt="{0:.6f}".format(self._altitude),
                press="{0:.6f}".format(self._pressure),
                temp="{0:.6f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Temperature: {temp}, Pressure: {press}, " \
               "Altitude: {alt}".format(
                alt="{0:.6f}".format(self._altitude),
                press="{0:.6f}".format(self._pressure),
                temp="{0:.6f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(altitude=float(self._altitude),
                    pressure=float(self._pressure),
                    temperature=float(self._temperature))

    @property
    def altitude(self):
        """ BMP280 altitude in meters """
        if self._altitude is None:  # update if needed
            self.read()
        return self._altitude

    @property
    def pressure(self):
        """ BME280 pressure in Pascals """
        if self._pressure is None:  # update if needed
            self.read()
        return self._pressure

    @property
    def temperature(self):
        """ BMP280 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self._altitude = None
        self._pressure = None
        self._temperature = None

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            self.read_temperature())

        pressure_pa = self.read_pressure()
        pressure = convert_units(
            'pressure', 'Pa', self.convert_to_unit,
            pressure_pa)

        alt = convert_units(
            'altitude', 'm', self.convert_to_unit,
            altitude(pressure_pa))

        return temperature, pressure, alt

    def read(self):
        """
        Takes a reading from the BMP280 and updates the self._humidity and
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._temperature,
             self._pressure,
             self._altitude) = self.get_measurement()
            if None not in [self._temperature,
                            self._pressure,
                            self._altitude]:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

    def _load_calibration(self):
        self.cal_REGISTER_DIG_T1 = self._device.readU16LE(BMP280_REGISTER_DIG_T1)  # UINT16
        self.cal_REGISTER_DIG_T2 = self._device.readS16LE(BMP280_REGISTER_DIG_T2)  # INT16
        self.cal_REGISTER_DIG_T3 = self._device.readS16LE(BMP280_REGISTER_DIG_T3)  # INT16
        self.cal_REGISTER_DIG_P1 = self._device.readU16LE(BMP280_REGISTER_DIG_P1)  # UINT16
        self.cal_REGISTER_DIG_P2 = self._device.readS16LE(BMP280_REGISTER_DIG_P2)  # INT16
        self.cal_REGISTER_DIG_P3 = self._device.readS16LE(BMP280_REGISTER_DIG_P3)  # INT16
        self.cal_REGISTER_DIG_P4 = self._device.readS16LE(BMP280_REGISTER_DIG_P4)  # INT16
        self.cal_REGISTER_DIG_P5 = self._device.readS16LE(BMP280_REGISTER_DIG_P5)  # INT16
        self.cal_REGISTER_DIG_P6 = self._device.readS16LE(BMP280_REGISTER_DIG_P6)  # INT16
        self.cal_REGISTER_DIG_P7 = self._device.readS16LE(BMP280_REGISTER_DIG_P7)  # INT16
        self.cal_REGISTER_DIG_P8 = self._device.readS16LE(BMP280_REGISTER_DIG_P8)  # INT16
        self.cal_REGISTER_DIG_P9 = self._device.readS16LE(BMP280_REGISTER_DIG_P9)  # INT16

        self.logger.debug('T1 = {0:6d}'.format(self.cal_REGISTER_DIG_T1))
        self.logger.debug('T2 = {0:6d}'.format(self.cal_REGISTER_DIG_T2))
        self.logger.debug('T3 = {0:6d}'.format(self.cal_REGISTER_DIG_T3))
        self.logger.debug('P1 = {0:6d}'.format(self.cal_REGISTER_DIG_P1))
        self.logger.debug('P2 = {0:6d}'.format(self.cal_REGISTER_DIG_P2))
        self.logger.debug('P3 = {0:6d}'.format(self.cal_REGISTER_DIG_P3))
        self.logger.debug('P4 = {0:6d}'.format(self.cal_REGISTER_DIG_P4))
        self.logger.debug('P5 = {0:6d}'.format(self.cal_REGISTER_DIG_P5))
        self.logger.debug('P6 = {0:6d}'.format(self.cal_REGISTER_DIG_P6))
        self.logger.debug('P7 = {0:6d}'.format(self.cal_REGISTER_DIG_P7))
        self.logger.debug('P8 = {0:6d}'.format(self.cal_REGISTER_DIG_P8))
        self.logger.debug('P9 = {0:6d}'.format(self.cal_REGISTER_DIG_P9))

    def _load_datasheet_calibration(self):
        """data from the datasheet example, useful for debug"""
        self.cal_REGISTER_DIG_T1 = 27504
        self.cal_REGISTER_DIG_T2 = 26435
        self.cal_REGISTER_DIG_T3 = -1000
        self.cal_REGISTER_DIG_P1 = 36477
        self.cal_REGISTER_DIG_P2 = -10685
        self.cal_REGISTER_DIG_P3 = 3024
        self.cal_REGISTER_DIG_P4 = 2855
        self.cal_REGISTER_DIG_P5 = 140
        self.cal_REGISTER_DIG_P6 = -7
        self.cal_REGISTER_DIG_P7 = 15500
        self.cal_REGISTER_DIG_P8 = -14600
        self.cal_REGISTER_DIG_P9 = 6000
        # reading raw data from registers, and combining into one raw measurement

    def read_raw_temp(self):
        """Reads the raw (uncompensated) temperature from the sensor."""
        self._device.write8(
            BMP280_REGISTER_CONTROL, BMP280_READCMD + (self._mode << 6))
        if self._mode == BMP280_ULTRALOWPOWER:
            time.sleep(0.005)
        elif self._mode == BMP280_HIGHRES:
            time.sleep(0.014)
        elif self._mode == BMP280_ULTRAHIGHRES:
            time.sleep(0.026)
        else:
            time.sleep(0.008)
        msb = self._device.readU8(BMP280_REGISTER_TEMPDATA_MSB)
        lsb = self._device.readU8(BMP280_REGISTER_TEMPDATA_LSB)
        xlsb = self._device.readU8(BMP280_REGISTER_TEMPDATA_XLSB)
        raw = ((msb << 8 | lsb) << 8 | xlsb) >> 4
        self.logger.debug(
            'Raw temperature 0x{0:04X} ({1})'.format(raw & 0xFFFF, raw))
        return raw

    def read_raw_pressure(self):
        """Reads the raw (uncompensated) pressure level from the sensor."""
        self._device.write8(BMP280_REGISTER_CONTROL, BMP280_READCMD + (self._mode << 6))
        if self._mode == BMP280_ULTRALOWPOWER:
            time.sleep(0.005)
        elif self._mode == BMP280_HIGHRES:
            time.sleep(0.014)
        elif self._mode == BMP280_ULTRAHIGHRES:
            time.sleep(0.026)
        else:
            time.sleep(0.008)
        msb = self._device.readU8(BMP280_REGISTER_PRESSUREDATA_MSB)
        lsb = self._device.readU8(BMP280_REGISTER_PRESSUREDATA_LSB)
        xlsb = self._device.readU8(BMP280_REGISTER_PRESSUREDATA_XLSB)
        raw = ((msb << 8 | lsb) << 8 | xlsb) >> 4
        self.logger.debug('Raw pressure 0x{0:04X} ({1})'.format(raw & 0xFFFF, raw))
        return raw

    def read_temperature(self):
        """Gets the compensated temperature in degrees celsius."""
        adc_T = self.read_raw_temp()
        TMP_PART1 = (((adc_T >> 3) - (self.cal_REGISTER_DIG_T1 << 1)) * self.cal_REGISTER_DIG_T2) >> 11
        TMP_PART2 = (((((adc_T >> 4) - self.cal_REGISTER_DIG_T1) * (
            (adc_T >> 4) - self.cal_REGISTER_DIG_T1)) >> 12) * self.cal_REGISTER_DIG_T3) >> 14
        TMP_FINE = TMP_PART1 + TMP_PART2
        self._tfine = TMP_FINE
        temp = ((TMP_FINE * 5 + 128) >> 8) / 100.0
        self.logger.debug('Calibrated temperature {0} C'.format(temp))
        return temp

    def read_pressure(self):
        """Gets the compensated pressure in Pascals."""
        # for pressure calculation we need a temperature, checking if we have one, and reading data if not
        if self._tfine == 0:
            self.read_temperature()

        adc_P = self.read_raw_pressure()
        var1 = self._tfine - 128000
        var2 = var1 * var1 * self.cal_REGISTER_DIG_P6
        var2 = var2 + ((var1 * self.cal_REGISTER_DIG_P5) << 17)
        var2 = var2 + (self.cal_REGISTER_DIG_P4 << 35)
        var1 = ((var1 * var1 * self.cal_REGISTER_DIG_P3) >> 8) + ((var1 * self.cal_REGISTER_DIG_P2) << 12)
        var1 = (((1) << 47) + var1) * self.cal_REGISTER_DIG_P1 >> 33

        if var1 == 0:
            return 0

        p = 1048576 - adc_P
        p = int((((p << 31) - var2) * 3125) / var1)
        var1 = (self.cal_REGISTER_DIG_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.cal_REGISTER_DIG_P8 * p) >> 19

        p = ((p + var1 + var2) >> 8) + ((self.cal_REGISTER_DIG_P7) << 4)
        return p / 256.0

    def read_altitude(self, sealevel_pa=101325.0):
        """Calculates the altitude in meters."""
        pressure = float(self.read_pressure())
        altitude = 44330.0 * (1.0 - pow(pressure / sealevel_pa, (1.0 / 5.255)))
        self.logger.debug('Altitude {0} m'.format(altitude))
        return altitude

    def read_sealevel_pressure(self, altitude_m=0.0):
        """
        Calculates the pressure at sealevel when given a known altitude in
        meters. Returns a value in Pascals.
        """
        pressure = float(self.read_pressure())
        p0 = pressure / pow(1.0 - altitude_m / 44330.0, 5.255)
        self.logger.debug('Sealevel pressure {0} Pa'.format(p0))
        return p0
