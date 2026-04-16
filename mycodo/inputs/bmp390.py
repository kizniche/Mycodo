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
    },
    3: {
        'measurement': 'altitude',
        'unit': 'ft'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BMP390',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BMP390',
    'input_library': 'Adafruit_GPIO',
    'measurements_name': 'Pressure/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.bosch-sensortec.com/en/products/environmental-sensors/pressure-sensors/pressure-sensors-bmp390.html',
    'url_datasheet': 'https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp390-ds002.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/4816',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'altitude_sea_level_pa'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x76', '0x77'],
    'i2c_address_editable': False
}

# BMP390 Chip ID
BMP390_CHIP_ID = 0x60
# BMP388 Chip ID
BMP388_CHIP_ID = 0x50

# Registers
BMP390_REGISTER_CHIPID = 0x00
BMP390_REGISTER_STATUS = 0x03
BMP390_REGISTER_PRESSUREDATA = 0x04
BMP390_REGISTER_TEMPDATA = 0x07
BMP390_REGISTER_CONTROL = 0x1B
BMP390_REGISTER_OSR = 0x1C
BMP390_REGISTER_ODR = 0x1D
BMP390_REGISTER_CONFIG = 0x1F
BMP390_REGISTER_CALIB00 = 0x31
BMP390_REGISTER_CMD = 0x7E

# Mode and settings
BMP390_MODE_SLEEP = 0x00
BMP390_MODE_FORCED = 0x11
BMP390_MODE_NORMAL = 0x33

BMP390_CMD_SOFTRESET = 0xB6


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BMP390's
    temperature and pressure, then calculates the altitude.
    """

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self._t_calib = []
        self._p_calib = []

        if not testing:
            self.try_initialize()

    def initialize(self):
        import Adafruit_GPIO.I2C

        self.sensor = Adafruit_GPIO.I2C.get_i2c_device(
            int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)

        # Soft reset
        self.sensor.write8(BMP390_REGISTER_CMD, BMP390_CMD_SOFTRESET)
        time.sleep(0.01)

        # Check chip ID
        chip_id = self.sensor.readU8(BMP390_REGISTER_CHIPID)
        if chip_id not in [BMP390_CHIP_ID, BMP388_CHIP_ID]:
            raise ValueError(f"Unexpected chip ID 0x{chip_id:02X}. Expected 0x60 (BMP390) or 0x50 (BMP388).")

        self._load_calibration()

        # Configure settings: OSR (4x oversampling for both), ODR (50Hz), Config (IIR filter)
        self.sensor.write8(BMP390_REGISTER_OSR, 0x12)  # OSR_P x8, OSR_T x2
        self.sensor.write8(BMP390_REGISTER_ODR, 0x03)  # 25Hz
        self.sensor.write8(BMP390_REGISTER_CONFIG, 0x02)  # Coeff 3
        
        # Set to Normal mode, enable Pressure and Temperature
        self.sensor.write8(BMP390_REGISTER_CONTROL, BMP390_MODE_NORMAL | 0x03)
        time.sleep(0.01)

    def get_measurement(self):
        """Gets the measurement in units by reading the sensor."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        # Get readings
        temp_c, pressure_pa = self.read_data()
        self.logger.debug(f"Temperature: {temp_c} C, Pressure: {pressure_pa} Pa")

        # Altitude calculation
        try:
            sea_level_pa = self.input_dev.altitude_sea_level_pa
        except AttributeError:
            sea_level_pa = 101325.0

        altitude_m = calculate_altitude(pressure_pa, sea_level_pa=sea_level_pa)
        self.logger.debug(f"Altitude: {altitude_m} m (Sea level pressure: {sea_level_pa} Pa)")

        if self.is_enabled(0):
            self.value_set(0, pressure_pa)

        if self.is_enabled(1):
            self.value_set(1, temp_c)

        if self.is_enabled(2):
            self.value_set(2, altitude_m)

        if self.is_enabled(3):
            self.value_set(3, altitude_m * 3.28084)

        return self.return_dict

    def _load_calibration(self):
        import struct
        # Reading 21 bytes starting from 0x31
        calib = []
        for i in range(21):
            calib.append(self.sensor.readU8(BMP390_REGISTER_CALIB00 + i))
        
        # Unpack the calibration data
        # Order: T1-T3, P1-P11
        # Data format: <HHbhhbbHHbbhbb (21 bytes)
        # Based on Bosch Datasheet/Adafruit driver
        data = struct.unpack("<HHbhhbbHHbbhbb", bytes(calib))
        
        # T1-T3
        self._t_calib = [
            data[0] / 2**-8.0,  # T1
            data[1] / 2**30.0,  # T2
            data[2] / 2**48.0   # T3
        ]
        
        # P1-P11
        self._p_calib = [
            (data[3] - 2**14.0) / 2**20.0,   # P1
            (data[4] - 2**14.0) / 2**29.0,   # P2
            data[5] / 2**32.0,               # P3
            data[6] / 2**37.0,               # P4
            data[7] / 2**-3.0,               # P5
            data[8] / 2**6.0,                # P6
            data[9] / 2**8.0,                # P7
            data[10] / 2**15.0,              # P8
            data[11] / 2**48.0,              # P9
            data[12] / 2**48.0,              # P10
            data[13] / 2**65.0               # P11
        ]

    def read_data(self):
        """Reads raw data and applies compensation."""
        # Read 6 bytes for pressure and temperature starting from 0x04
        # Format is 3-byte pressure followed by 3-byte temperature (each 24-bit little endian)
        raw_p = self.sensor.readU8(0x04) | (self.sensor.readU8(0x05) << 8) | (self.sensor.readU8(0x06) << 16)
        raw_t = self.sensor.readU8(0x07) | (self.sensor.readU8(0x08) << 8) | (self.sensor.readU8(0x09) << 16)

        # Temperature compensation (floating point format from datasheet)
        pd1 = raw_t - self._t_calib[0]
        pd2 = pd1 * self._t_calib[1]
        temp_c = pd2 + (pd1 * pd1) * self._t_calib[2]

        # Pressure compensation
        pd1 = self._p_calib[5] * temp_c
        pd2 = self._p_calib[6] * (temp_c**2)
        pd3 = self._p_calib[7] * (temp_c**3)
        po1 = self._p_calib[4] + pd1 + pd2 + pd3

        pd1 = self._p_calib[1] * temp_c
        pd2 = self._p_calib[2] * (temp_c**2)
        pd3 = self._p_calib[3] * (temp_c**3)
        po2 = raw_p * (self._p_calib[0] + pd1 + pd2 + pd3)

        pd1 = raw_p**2
        pd2 = self._p_calib[8] + self._p_calib[9] * temp_c
        pd3 = pd1 * pd2
        pd4 = pd3 + (raw_p**3) * self._p_calib[10]

        pressure_pa = po1 + po2 + pd4

        return temp_c, pressure_pa
