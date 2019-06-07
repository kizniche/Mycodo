# coding=utf-8
# From https://github.com/sandnabba/am2320-python
import time
from fcntl import ioctl

import os

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'AM2320',
    'input_manufacturer': 'AOSONG',
    'input_name': 'AM2320',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_rescale': False,

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x5c'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the AM2320's humidity and temperature
    and calculates the dew point

    """
    I2C_ADDR = 0x5c
    I2C_SLAVE = 0x0703

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.powered = False
        self.i2c_address = 0x5C

        if not testing:
            self.i2c_bus = input_dev.i2c_bus

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self.return_dict = measurements_dict.copy()

        temperature, humidity = self.read_sensor()

        if self.is_enabled(0):
            self.value_set(0, temperature)

        if self.is_enabled(1):
            self.value_set(1, humidity)

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(2, calculate_dewpoint(
                self.value_get(0), self.value_get(1)))

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(3, calculate_vapor_pressure_deficit(
                self.value_get(0), self.value_get(1)))

        return self.return_dict

    @staticmethod
    def _calc_crc16(data):
        crc = 0xFFFF
        for x in data:
            crc = crc ^ x
            for bit in range(0, 8):
                if (crc & 0x0001) == 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    @staticmethod
    def _combine_bytes(msb, lsb):
        return msb << 8 | lsb

    def read_sensor(self):
        fd = os.open("/dev/i2c-%d" % self.i2c_bus, os.O_RDWR)

        ioctl(fd, self.I2C_SLAVE, self.I2C_ADDR)

        # wake AM2320 up, goes to sleep to not warm up and affect the humidity sensor
        # This write will fail as AM2320 won't ACK this write
        try:
            os.write(fd, b'\0x00')
        except:
            pass
        time.sleep(0.001)  # Wait at least 0.8ms, at most 3ms

        # write at addr 0x03, start reg = 0x00, num regs = 0x04 */
        os.write(fd, b'\x03\x00\x04')
        time.sleep(0.0016)  # Wait at least 1.5ms for result

        # Read out 8 bytes of result data
        # Byte 0: Should be Modbus function code 0x03
        # Byte 1: Should be number of registers to read (0x04)
        # Byte 2: Humidity msb
        # Byte 3: Humidity lsb
        # Byte 4: Temperature msb
        # Byte 5: Temperature lsb
        # Byte 6: CRC lsb byte
        # Byte 7: CRC msb byte
        data = bytearray(os.read(fd, 8))

        # Close the file descriptor:
        os.close(fd)

        # Check data[0] and data[1]
        if data[0] != 0x03 or data[1] != 0x04:
            raise Exception("First two read bytes are a mismatch")

        # CRC check
        if self._calc_crc16(data[0:6]) != self._combine_bytes(data[7], data[6]):
            raise Exception("CRC failed")

        # Temperature resolution is 16Bit,
        # temperature highest bit (Bit15) is equal to 1 indicates a
        # negative temperature, the temperature highest bit (Bit15)
        # is equal to 0 indicates a positive temperature;
        # temperature in addition to the most significant bit (Bit14 ~ Bit0)
        # indicates the temperature sensor string value.
        # Temperature sensor value is a string of 10 times the
        # actual temperature value.
        temp = self._combine_bytes(data[4], data[5])
        if temp & 0x8000:
            temp = -(temp & 0x7FFF)
        temp /= 10.0

        humi = self._combine_bytes(data[2], data[3]) / 10.0

        return temp, humi