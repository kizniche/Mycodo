# coding=utf-8
#
# Created in part from github.com/switchdoclabs/SDL_Pi_HDC1000
#
import array
import fcntl
import logging
import time

import io

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'temperature': {
        'C': {0: {}}
    },
    'humidity': {
        'percent': {0: {}}
    },
    'dewpoint': {
        'C': {0: {}}
    },
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'HDC1000',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'HDC1000',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'measurements_convert',
        'period',
        'resolution',
        'resolution_2',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': False,
    'resolution': [
        (11, 'Temperature 11-bit'),
        (14, 'Temperature 14-bit')
    ],
    'resolution_2': [
        (8, 'Humidity 8-bit'),
        (11, 'Humidity 11-bit'),
        (14, 'Humidity 14-bit')
    ]
}

# I2C Address
HDC1000_ADDRESS = 0x40  # 1000000

# Registers
HDC1000_TEMPERATURE_REGISTER = 0x00
HDC1000_HUMIDITY_REGISTER = 0x01
HDC1000_CONFIGURATION_REGISTER = 0x02
HDC1000_MANUFACTURERID_REGISTER = 0xFE
HDC1000_DEVICEID_REGISTER = 0xFF
HDC1000_SERIALIDHIGH_REGISTER = 0xFB
HDC1000_SERIALIDMID_REGISTER = 0xFC
HDC1000_SERIALIDBOTTOM_REGISTER = 0xFD

# Configuration Register Bits
HDC1000_CONFIG_RESET_BIT = 0x8000
HDC1000_CONFIG_HEATER_ENABLE = 0x2000
HDC1000_CONFIG_ACQUISITION_MODE = 0x1000
HDC1000_CONFIG_BATTERY_STATUS = 0x0800
HDC1000_CONFIG_TEMPERATURE_RESOLUTION = 0x0400
HDC1000_CONFIG_HUMIDITY_RESOLUTION_HBIT = 0x0200
HDC1000_CONFIG_HUMIDITY_RESOLUTION_LBIT = 0x0100

HDC1000_CONFIG_TEMPERATURE_RESOLUTION_14BIT = 0x0000
HDC1000_CONFIG_TEMPERATURE_RESOLUTION_11BIT = 0x0400

HDC1000_CONFIG_HUMIDITY_RESOLUTION_14BIT = 0x0000
HDC1000_CONFIG_HUMIDITY_RESOLUTION_11BIT = 0x0100
HDC1000_CONFIG_HUMIDITY_RESOLUTION_8BIT = 0x0200

I2C_SLAVE = 0x0703


class InputModule(AbstractInput):
    """
    A sensor support class that measures the HDC1000's humidity and temperature
    and calculates the dew point

    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.hdc1000")
        self._measurements = None

        self.resolution_temperature = input_dev.resolution
        self.resolution_humidity = input_dev.resolution_2

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.hdc1000_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id)

            self.i2c_bus = input_dev.i2c_bus
            self.i2c_address = 0x40  # HDC1000-F Address

            self.HDC1000_fr = io.open("/dev/i2c-" + str(self.i2c_bus), "rb", buffering=0)
            self.HDC1000_fw = io.open("/dev/i2c-" + str(self.i2c_bus), "wb", buffering=0)

            # set device address
            fcntl.ioctl(self.HDC1000_fr, I2C_SLAVE, self.i2c_address)
            fcntl.ioctl(self.HDC1000_fw, I2C_SLAVE, self.i2c_address)
            time.sleep(0.015)  # 15ms startup time

            config = HDC1000_CONFIG_ACQUISITION_MODE

            s = [HDC1000_CONFIGURATION_REGISTER, config >> 8, 0x00]
            s2 = bytearray(s)
            self.HDC1000_fw.write(s2)  # sending config register bytes
            time.sleep(0.015)  # From the data sheet

            # Set resolutions
            if self.resolution_temperature == 11:
                self.set_temperature_resolution(HDC1000_CONFIG_TEMPERATURE_RESOLUTION_11BIT)
            elif self.resolution_temperature == 14:
                self.set_temperature_resolution(HDC1000_CONFIG_TEMPERATURE_RESOLUTION_14BIT)

            if self.resolution_humidity == 8:
                self.set_humidity_resolution(HDC1000_CONFIG_HUMIDITY_RESOLUTION_8BIT)
            elif self.resolution_humidity == 11:
                self.set_humidity_resolution(HDC1000_CONFIG_HUMIDITY_RESOLUTION_11BIT)
            elif self.resolution_humidity == 14:
                self.set_humidity_resolution(HDC1000_CONFIG_HUMIDITY_RESOLUTION_14BIT)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        return_dict = {
            'temperature': {
                'C': {}
            },
            'humidity': {
                'percent': {}
            },
            'dewpoint': {
                'C': {}
            },
        }

        temperature = self.read_temperature()

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = temperature

        humidity = self.read_humidity()

        if self.is_enabled('humidity', 'percent', 0):
            return_dict['humidity']['percent'][0] = humidity

        if self.is_enabled('dewpoint', 'C', 0):
            return_dict['dewpoint']['C'][0] = calculate_dewpoint(
                temperature, humidity)

        return return_dict

    def read_temperature(self):
        s = [HDC1000_TEMPERATURE_REGISTER]  # temp
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet

        data = self.HDC1000_fr.read(2)  # read 2 byte temperature data
        buf = array.array('B', data)
        # print ( "Temp: %f 0x%X %X" % (  ((((buf[0]<<8) + (buf[1]))/65536.0)*165.0 ) - 40.0   ,buf[0],buf[1] )  )

        # Convert the data
        temp = (buf[0] * 256) + buf[1]
        temp_c = (temp / 65536.0) * 165.0 - 40
        return temp_c

    def read_humidity(self):
        # Send humidity measurement command, 0x01(01)
        time.sleep(0.015)  # From the data sheet

        s = [HDC1000_HUMIDITY_REGISTER]  # hum
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet

        data = self.HDC1000_fr.read(2)  # read 2 byte humidity data
        buf = array.array('B', data)
        # print ( "Humidity: %f 0x%X %X " % (  ((((buf[0]<<8) + (buf[1]))/65536.0)*100.0 ),  buf[0], buf[1] ) )
        humidity = (buf[0] * 256) + buf[1]
        humidity = (humidity / 65536.0) * 100.0
        return humidity

    def read_config_register(self):
        # Read config register
        s = [HDC1000_CONFIGURATION_REGISTER]  # temp
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet
        data = self.HDC1000_fr.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        # print "register=%X %X"% (buf[0], buf[1])
        return buf[0] * 256 + buf[1]

    def turn_heater_on(self):
        # Read config register
        config = self.read_config_register()
        config = config | HDC1000_CONFIG_HEATER_ENABLE
        s = [HDC1000_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)  # sending config register bytes
        time.sleep(0.015)  # From the data sheet
        return

    def turn_heater_off(self):
        # Read config register
        config = self.read_config_register()
        config = config & ~HDC1000_CONFIG_HEATER_ENABLE
        s = [HDC1000_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)  # sending config register bytes
        time.sleep(0.015)  # From the data sheet
        return

    def set_humidity_resolution(self, resolution):
        # Read config register
        config = self.read_config_register()
        config = (config & ~0x0300) | resolution
        s = [HDC1000_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)  # sending config register bytes
        time.sleep(0.015)  # From the data sheet
        return

    def set_temperature_resolution(self, resolution):
        # Read config register
        config = self.read_config_register()
        config = (config & ~0x0400) | resolution
        s = [HDC1000_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)  # sending config register bytes
        time.sleep(0.015)  # From the data sheet
        return

    def read_battery_status(self):
        # Read config register
        config = self.read_config_register()
        config = config & ~ HDC1000_CONFIG_HEATER_ENABLE
        if config == 0:
            return True
        else:
            return False

    def read_manufacturer_id(self):
        s = [HDC1000_MANUFACTURERID_REGISTER]  # temp
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet
        data = self.HDC1000_fr.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        return buf[0] * 256 + buf[1]

    def read_device_id(self):
        s = [HDC1000_DEVICEID_REGISTER]  # temp
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet
        data = self.HDC1000_fr.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        return buf[0] * 256 + buf[1]

    def read_serial_number(self):
        s = [HDC1000_SERIALIDHIGH_REGISTER]  # temp
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet
        data = self.HDC1000_fr.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        serial_number = buf[0] * 256 + buf[1]

        s = [HDC1000_SERIALIDMID_REGISTER]  # temp
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet
        data = self.HDC1000_fr.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        serial_number *= 256 + buf[0] * 256 + buf[1]

        s = [HDC1000_SERIALIDBOTTOM_REGISTER]  # temp
        s2 = bytearray(s)
        self.HDC1000_fw.write(s2)
        time.sleep(0.0625)  # From the data sheet
        data = self.HDC1000_fr.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        serial_number *= 256 + buf[0] * 256 + buf[1]
        return serial_number
