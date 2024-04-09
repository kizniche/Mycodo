# coding=utf-8
import copy
import time

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
    'input_name_unique': 'DHT20',
    'input_manufacturer': 'AOSONG',
    'input_name': 'DHT20',
    'input_library': 'smbus2',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_datasheet': 'http://www.aosong.com/userfiles/files/media/Data%20Sheet%20DHT20%20%20A1.pdf',
    'url_product_purchase': [
        'https://www.seeedstudio.com/Grove-Temperature-Humidity-Sensor-V2-0-DHT20-p-4967.html',
        'https://www.antratek.de/humidity-and-temperature-sensor-dht20',
        'https://www.adafruit.com/product/5183'],
    'url_manufacturer': 'https://asairsensors.com/product/dht20-sip-packaged-temperature-and-humidity-sensor/',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],

    'options_disabled': [
        'interface',
        'i2c_location',
    ],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x38'],
    'self.i2c_address_editable': False,
}


class InputModule(AbstractInput):
    """
    This module is a modified version of the DHT20 module from the Mycodo 
    distribution.

    A sensor support class that measures the DHT20's humidity and temperature
    and calculates the dew point.

    """
    def __init__(self, input_dev, testing=False):
        """
        Instantiate with the Pi and gpio to which the DHT20 output
        pin is connected.

        """
        super().__init__(input_dev, testing=testing, name=__name__)

        self.i2c_address = None
        self.dht20 = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from smbus2 import SMBus

        # Wait 100ms after power-on
        time.sleep(0.1)

        self.i2c_address = int(str(self.input_dev.i2c_location), 16)
        self.dht20 = SMBus(self.input_dev.i2c_bus)

        # Check if Sensor is ready
        status_word = self.dht20.read_byte(self.i2c_address)
        if status_word != 0x18:
            buffer = bytearray(b'\x00\x00')
            # Initialize the 0x1B, 0x1C, 0x1E registers
            self.dht20.write_i2c_block_data(self.i2c_address, 0x1B, buffer)
            self.dht20.write_i2c_block_data(self.i2c_address, 0x1C, buffer)
            self.dht20.write_i2c_block_data(self.i2c_address, 0x1E, buffer)
            time.sleep(1)

            if self.dht20.read_byte(self.i2c_address) != 0x18:
                self.logger.error("Could not initialize DHT20.")
            else:
                self.logger.debug("Initialize DHT20 successfully.")

    def calculate_crc(self, data):
        data = data[:-1]
        crc = 0xFF  # Initial value of CRC
        polynomial = 0x31  # CRC8 check polynomial: 1 + X^4 + X^5 + X^8

        for byte in data:
            crc ^= byte  # XOR operation with the current byte
            for _ in range(8):
                if crc & 0x80:  # Check if the most significant bit is 1
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
        return crc & 0xFF  # Return only the 8 least significant bits

    def get_measurement(self):
        """Gets the humidity and temperature

        'temperature': temperature (°C),
        'raw_temperature': the 'raw' temperature as produced by the ADC,
        'humidity': relative humidity (%RH),
        'raw_humidity': the 'raw' relative humidity as produced by the ADC,
        'crc_ok': indicates if the data was received correctly

        """
        self.return_dict = copy.deepcopy(measurements_dict)

        time.sleep(0.01)
        # trigger measurement
        self.dht20.write_i2c_block_data(self.i2c_address,0xAC,[0x33,0x00])
        time.sleep(0.08)

        # read measurement data
        data = self.dht20.read_i2c_block_data(self.i2c_address,0x71,7)

        received_crc = data[-1]
        crc_ok = self.calculate_crc(data) == received_crc

        if crc_ok:
            raw_temperature = ((data[3] & 0xf) << 16) + (data[4] << 8) + data[5]
            temperature = 200*float(raw_temperature)/2**20 - 50

            raw_humidity = ((data[3] & 0xf0) >> 4) + (data[1] << 12) + (data[2] << 4)
            humidity = 100*float(raw_humidity)/2**20

            self.logger.debug(f"Temperature: {temperature}, Humidity: {humidity}, CRC OK: {crc_ok}")

            if humidity:
                temp_dew_point = calculate_dewpoint(temperature, humidity)
                temp_vpd = calculate_vapor_pressure_deficit(temperature, humidity)
            else:
                self.logger.error("Could not acquire measurement")

            if temp_dew_point is not None:
                if self.is_enabled(0):
                    self.value_set(0, temperature)
                if self.is_enabled(1):
                    self.value_set(1, humidity)
                if self.is_enabled(2):
                    self.value_set(2, temp_dew_point)
                if self.is_enabled(3):
                    self.value_set(3, temp_vpd)

        else:
            self.logger.error("CRC check was not successfully")

        return self.return_dict
