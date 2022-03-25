# coding=utf-8
# Copyright (c) 2016
# Author: Vitally Tezhe
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude

# Measurements
measurements_dict = {
    0: {
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    2: {
        'measurement': 'altitude',
        'unit': 'm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BMP280',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BMP280',
    'input_library': 'Adafruit_GPIO',
    'measurements_name': 'Pressure/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/pressure-sensors-bmp280-1.html',
    'url_datasheet': 'https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/2651',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x76', '0x77'],
    'i2c_address_editable': False
}

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


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BMP280's humidity,
    temperature, and pressure, then calculates the altitude and dew point

    """

    def __init__(self, input_dev, mode=BMP280_STANDARD, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self._mode = mode
        self._tfine = 0

        if not testing:
            self.try_initialize()

    def initialize(self):
        import Adafruit_GPIO.I2C

        if self._mode not in [
                BMP280_ULTRALOWPOWER,
                BMP280_STANDARD,
                BMP280_HIGHRES,
                BMP280_ULTRAHIGHRES]:
            raise ValueError(
                'Unexpected mode value {0}.  Set mode to one of '
                'BMP280_ULTRALOWPOWER, BMP280_STANDARD, BMP280_HIGHRES, '
                'or BMP280_ULTRAHIGHRES'.format(self._mode))

        self.sensor = Adafruit_GPIO.I2C.get_i2c_device(
            int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)
        self._load_calibration()  # Load calibration values

    def get_measurement(self):
        """Gets the measurement in units by reading the."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.read_pressure())

        if self.is_enabled(1):
            self.value_set(1, self.read_temperature())

        if self.is_enabled(0):
            self.value_set(2, calculate_altitude(self.value_get(0)))

        return self.return_dict

    def _load_calibration(self):
        self.cal_REGISTER_DIG_T1 = self.sensor.readU16LE(BMP280_REGISTER_DIG_T1)  # UINT16
        self.cal_REGISTER_DIG_T2 = self.sensor.readS16LE(BMP280_REGISTER_DIG_T2)  # INT16
        self.cal_REGISTER_DIG_T3 = self.sensor.readS16LE(BMP280_REGISTER_DIG_T3)  # INT16
        self.cal_REGISTER_DIG_P1 = self.sensor.readU16LE(BMP280_REGISTER_DIG_P1)  # UINT16
        self.cal_REGISTER_DIG_P2 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P2)  # INT16
        self.cal_REGISTER_DIG_P3 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P3)  # INT16
        self.cal_REGISTER_DIG_P4 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P4)  # INT16
        self.cal_REGISTER_DIG_P5 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P5)  # INT16
        self.cal_REGISTER_DIG_P6 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P6)  # INT16
        self.cal_REGISTER_DIG_P7 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P7)  # INT16
        self.cal_REGISTER_DIG_P8 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P8)  # INT16
        self.cal_REGISTER_DIG_P9 = self.sensor.readS16LE(BMP280_REGISTER_DIG_P9)  # INT16

        # self.logger.debug('T1 = {0:6d}'.format(self.cal_REGISTER_DIG_T1))
        # self.logger.debug('T2 = {0:6d}'.format(self.cal_REGISTER_DIG_T2))
        # self.logger.debug('T3 = {0:6d}'.format(self.cal_REGISTER_DIG_T3))
        # self.logger.debug('P1 = {0:6d}'.format(self.cal_REGISTER_DIG_P1))
        # self.logger.debug('P2 = {0:6d}'.format(self.cal_REGISTER_DIG_P2))
        # self.logger.debug('P3 = {0:6d}'.format(self.cal_REGISTER_DIG_P3))
        # self.logger.debug('P4 = {0:6d}'.format(self.cal_REGISTER_DIG_P4))
        # self.logger.debug('P5 = {0:6d}'.format(self.cal_REGISTER_DIG_P5))
        # self.logger.debug('P6 = {0:6d}'.format(self.cal_REGISTER_DIG_P6))
        # self.logger.debug('P7 = {0:6d}'.format(self.cal_REGISTER_DIG_P7))
        # self.logger.debug('P8 = {0:6d}'.format(self.cal_REGISTER_DIG_P8))
        # self.logger.debug('P9 = {0:6d}'.format(self.cal_REGISTER_DIG_P9))

    def _load_datasheet_calibration(self):
        """data from the datasheet example, useful for debug."""
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
        self.sensor.write8(
            BMP280_REGISTER_CONTROL, BMP280_READCMD + (self._mode << 6))
        if self._mode == BMP280_ULTRALOWPOWER:
            time.sleep(0.005)
        elif self._mode == BMP280_HIGHRES:
            time.sleep(0.014)
        elif self._mode == BMP280_ULTRAHIGHRES:
            time.sleep(0.026)
        else:
            time.sleep(0.008)
        msb = self.sensor.readU8(BMP280_REGISTER_TEMPDATA_MSB)
        lsb = self.sensor.readU8(BMP280_REGISTER_TEMPDATA_LSB)
        xlsb = self.sensor.readU8(BMP280_REGISTER_TEMPDATA_XLSB)
        raw = ((msb << 8 | lsb) << 8 | xlsb) >> 4
        self.logger.debug(
            'Raw temperature 0x{0:04X} ({1})'.format(raw & 0xFFFF, raw))
        return raw

    def read_raw_pressure(self):
        """Reads the raw (uncompensated) pressure level from the sensor."""
        self.sensor.write8(BMP280_REGISTER_CONTROL, BMP280_READCMD + (self._mode << 6))
        if self._mode == BMP280_ULTRALOWPOWER:
            time.sleep(0.005)
        elif self._mode == BMP280_HIGHRES:
            time.sleep(0.014)
        elif self._mode == BMP280_ULTRAHIGHRES:
            time.sleep(0.026)
        else:
            time.sleep(0.008)
        msb = self.sensor.readU8(BMP280_REGISTER_PRESSUREDATA_MSB)
        lsb = self.sensor.readU8(BMP280_REGISTER_PRESSUREDATA_LSB)
        xlsb = self.sensor.readU8(BMP280_REGISTER_PRESSUREDATA_XLSB)
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
        var1 = ((1 << 47) + var1) * self.cal_REGISTER_DIG_P1 >> 33

        if var1 == 0:
            return 0

        p = 1048576 - adc_P
        p = int((((p << 31) - var2) * 3125) / var1)
        var1 = (self.cal_REGISTER_DIG_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.cal_REGISTER_DIG_P8 * p) >> 19

        p = ((p + var1 + var2) >> 8) + (self.cal_REGISTER_DIG_P7 << 4)
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
