# coding=utf-8
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


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
    'input_name_unique': 'SHT35',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT35',
    'measurements_name': 'Humidity/Temperature (grove.py)',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-git', 'grove', 'git://github.com/Seeed-Studio/grove.py.git#egg=grove')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x44',
        '0x45'
    ],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT35 (Grove) humidity and temperature,
    them calculates the dew point and vapor pressure deficit
    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.measurement_count = 0

        if not testing:
            from grove.i2c import Bus

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.bus = Bus(self.i2c_bus)

    def get_measurement(self):
        self.return_dict = measurements_dict.copy()

        # high repeatability, clock stretching disabled
        self.bus.write_i2c_block_data(self.i2c_address, 0x24, [0x00])

        # measurement duration < 16 ms
        time.sleep(0.016)

        # read 6 bytes back
        # Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
        data = self.bus.read_i2c_block_data(0x45, 0x00, 6)
        temperature = data[0] * 256 + data[1]
        celsius = -45 + (175 * temperature / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
        if data[2] != self.crc(data[:2]):
            self.logger.error("temperature CRC mismatch")
        elif self.is_enabled(0):
            self.value_set(0, celsius)
        if data[5] != self.crc(data[3:5]):
            self.logger.error("humidity CRC mismatch")
        elif self.is_enabled(1):
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
    def crc(data):
        crc = 0xff
        for s in data:
            crc ^= s
            for i in range(8):
                if crc & 0x80:
                    crc <<= 1
                    crc ^= 0x131
                else:
                    crc <<= 1
        return crc
