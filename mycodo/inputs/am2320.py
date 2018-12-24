# coding=utf-8
import logging
from time import sleep

from struct import unpack

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.database import db_retrieve_table_daemon

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
        'pre_output'
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
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger('mycodo.inputs.am2320')
        self.name = INPUT_INFORMATION['input_name_unique']
        self._measurements = None
        self.powered = False
        self.sensor = None

        if not testing:
            from mycodo.mycodo_client import DaemonControl
            self.logger = logging.getLogger(
                'mycodo.am2320_{id}'.format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_bus = input_dev.i2c_bus
            self.power_output_id = input_dev.power_output_id
            self.control = DaemonControl()
            self.start_sensor()
            self.sensor = AM2320(self.i2c_bus,logger=self.logger)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        return_dict = measurements_dict.copy()

        self.sensor.read()

        if self.is_enabled(0):
            return_dict[0]['value'] = self.sensor.temperature

        if self.is_enabled(1):
            return_dict[1]['value'] = self.sensor.humidity

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            return_dict[2]['value'] = calculate_dewpoint(
                return_dict[0]['value'], return_dict[1]['value'])

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            return_dict[3]['value'] = calculate_vapor_pressure_deficit(
                return_dict[0]['value'], return_dict[1]['value'])

        return return_dict


class AM2320(object):
    """
    AM2320 temperature and humidity sensor class.
    
    original source: https://github.com/8devices/IoTPy/

    :param interface:  I2C interface id.
    :type interface: :int
    :param sensor_address: AM2320 sensor I2C address. Optional, default 0x5C (92).
    :type sensor_address: int
    """

    I2C_ADDR_AM2320 = 0x5c  # 0xB8 >> 1
    PARAM_AM2320_READ = 0x03
    REG_AM2320_HUMIDITY_MSB = 0x00
    REG_AM2320_HUMIDITY_LSB = 0x01
    REG_AM2320_TEMPERATURE_MSB = 0x02
    REG_AM2320_TEMPERATURE_LSB = 0x03
    REG_AM2320_DEVICE_ID_BIT_24_31 = 0x0B

    def __init__(self, interface, sensor_address=0x5c, logger=None):
        from smbus2 import SMBus
        self.logger = logger
        self.interface = interface
        self.address = sensor_address
        self.temperature = -1000.0
        self.humidity = -1
        self.bus = SMBus(interface)

    def _read_raw(self, command, regaddr, regcount):
        try:
            self.bus.write_i2c_block_data(
                self.address, 0x00, [])
            self.bus.write_i2c_block_data(
                self.address, command, [regaddr, regcount])

            sleep(0.002)

            buf = self.bus.read_i2c_block_data(self.address, 0, 8)
        except Exception:
            self.logger.error("AM2320 Read error")
            return None

        buf_str = "".join(chr(x) for x in buf)

        crc = unpack('<H', buf_str[-2:])[0]
        if crc != self._am_crc16(buf[:-2]):
            self.logger.error("AM2320 CRC error.")
        return buf_str[2:-2]

    def _am_crc16(self, buf):
        crc = 0xFFFF
        for c in buf:
            crc ^= c
            for i in range(8):
                if crc & 0x01:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def read_uid(self):
        """
        Read and return unique 32bit sensor ID.

        :return: A unique 32bit sensor ID.
        :rtype: int
        """
        resp = self._read_raw(
            self.PARAM_AM2320_READ,
            self.REG_AM2320_DEVICE_ID_BIT_24_31, 4)
        uid = unpack('>I', resp)[0]
        return uid

    def read(self):
        """
        Read and store temperature and humidity value.

        Read temperature and humidity registers from the sensor,
        then convert and store them.
        Use :func:`temperature` and :func:`humidity` to retrieve these values.
        """
        raw_data = self._read_raw(
            self.PARAM_AM2320_READ,
            self.REG_AM2320_HUMIDITY_MSB, 4)
        self.temperature = unpack('>H', raw_data[-2:])[0] / 10.0
        self.humidity = unpack('>H', raw_data[-4:2])[0] / 10.0
