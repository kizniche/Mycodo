# coding=utf-8
#
# Copyright 2014 Matt Heitzenroder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Python wrapper exposes the capabilities of the AOSONG AM2315 humidity
# and temperature sensor.
# The datasheet for the device can be found here:
# http://www.adafruit.com/datasheets/AM2315.pdf
#
# Portions of this code were inspired by Joehrg Ehrsam's am2315-python-api
# code. http://code.google.com/p/am2315-python-api/
#
# This library was originally authored by Sopwith:
#     http://sopwith.ismellsmoke.net/?p=104
import logging
import math
import time

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Output
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
    'input_name_unique': 'AM2315',
    'input_manufacturer': 'AOSONG',
    'input_name': 'AM2315',
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
        ('pip-pypi', 'quick2wire', 'quick2wire-api')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x5c'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the AM2315's humidity and temperature
    and calculates the dew point

    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger('mycodo.inputs.am2315')
        self.powered = False
        self.am = None

        if not testing:
            from mycodo.mycodo_client import DaemonControl
            self.logger = logging.getLogger(
                'mycodo.am2315_{id}'.format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_bus = input_dev.i2c_bus
            self.power_output_id = input_dev.power_output_id
            self.control = DaemonControl()
            self.start_sensor()
            self.am = AM2315(self.i2c_bus)

    def get_measurement(self):
        """ Gets the humidity and temperature """
        return_dict = measurements_dict.copy()

        temperature = None
        humidity = None
        dew_point = None
        measurements_success = False

        # Ensure if the power pin turns off, it is turned back on
        if (self.power_output_id and
                db_retrieve_table_daemon(Output, unique_id=self.power_output_id) and
                self.control.output_state(self.power_output_id) == 'off'):
            self.logger.error(
                'Sensor power output {rel} detected as being off. '
                'Turning on.'.format(rel=self.power_output_id))
            self.start_sensor()
            time.sleep(2)

        # Try twice to get measurement. This prevents an anomaly where
        # the first measurement fails if the sensor has just been powered
        # for the first time.
        for _ in range(2):
            dew_point, humidity, temperature = self.return_measurements()
            if dew_point is not None:
                measurements_success = True
                break
            time.sleep(2)

        # Measurement failure, power cycle the sensor (if enabled)
        # Then try two more times to get a measurement
        if self.power_output_id and not measurements_success:
            self.stop_sensor()
            time.sleep(2)
            self.start_sensor()
            for _ in range(2):
                dew_point, humidity, temperature = self.return_measurements()
                if dew_point is not None:
                    measurements_success = True
                    break
                time.sleep(2)

        if measurements_success:
            if self.is_enabled(0):
                return_dict[0]['value'] = temperature

            if self.is_enabled(1):
                return_dict[1]['value'] = humidity

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
        else:
            self.logger.debug("Could not acquire a measurement")

    def return_measurements(self):
        # Retry measurement if CRC fails
        for num_measure in range(3):
            humidity, temperature = self.am.data()
            if humidity is None:
                self.logger.debug(
                    "Measurement {num} returned failed CRC".format(
                        num=num_measure))
                pass
            else:
                dew_pt = calculate_dewpoint(temperature, humidity)
                return dew_pt, humidity, temperature
            time.sleep(2)

        self.logger.error("All measurements returned failed CRC")
        return None, None, None

    def start_sensor(self):
        """ Turn the sensor on """
        if self.power_output_id:
            self.logger.info("Turning on sensor")
            self.control.output_on(self.power_output_id, 0)
            time.sleep(2)
            self.powered = True

    def stop_sensor(self):
        """ Turn the sensor off """
        if self.power_output_id:
            self.logger.info("Turning off sensor")
            self.control.output_off(self.power_output_id)
            self.powered = False


class AM2315:
    """Wrapping for an AOSONG AM2315 humidity and temperature sensor.

    Provides simple access to a AM2315 chip using the quickwire i2c module
    Attributes:
        bus:       Int containing the smbus channel.
        address:   AM2315 bus address
        bus:       quickwire i2c object instance.
        lastError: String containing the last error string.Formatter
        debug:     bool containing debug state
    """
    def __init__(self, bus, address=0x5C, debug=False):
        import quick2wire.i2c as i2c
        self.i2c = i2c
        self.channel = bus
        self.address = address   				  # Default address 0x5C
        self.bus = self.i2c.I2CMaster(int(bus))        # quick2wire master
        self.lastError = None   				  # Contains last error string
        self.debug = debug       				  # Debug flag

    def data(self):
        """ Reads the humidity and temperature from the AS2315.

        Returns:
            Tuple containing the following fields:
                humidity    - float
                temperature - float (Celsius)
        """
        data = None

        # Send a wakeup call to the sensor. This call will always fail
        try:
            self.bus.transaction(self.i2c.writing(self.address, bytes([0x03,0x0,0x04])))
        except:
             pass

        time.sleep(0.125)
        # Now that the device is awake, read the data
        try:
            self.bus.transaction(self.i2c.writing(self.address, bytes([0x03,0x0,0x04])))
            data = self.bus.transaction(self.i2c.reading(self.address, 0x08))
            data = bytearray(data[0])
        except IOError as e:
            self.lastError = 'I/O Error({0}): {1}'.format(e.errno,e.strerror)
            return None, None

        # 0x03-returned command, 0x04-no bytes read.
        if data[0] != 0x03 and data[1] != 0x04:
            self.lastError = 'Error reading data from AM2315 device.'
            return None, None

        # Parse the data list
        cmd_code = data[0]
        byte_cnt = data[1]
        humid_H  = data[2]
        humid_L  = data[3]
        temp_H   = data[4]
        temp_L   = data[5]
        crc_H    = data[6]
        crc_L    = data[7]

        negative = False
        humidity = (humid_H*256+humid_L)/10

        # Check for negative temp
        # 16-Sep-2014
        # Thanks to Ethan for pointing out this bug!
        # ethansimpson@xtra.co.nz
        if temp_H&0x08:
           negative = True
        # Mask the negative flag
        temp_H &=0x7F

        tempC = (temp_H * 256 + temp_L) / 10

        if negative:
            tempC = -abs(tempC)

        # tempF = self.c_to_f(tempC)

        # Verify CRC
        crc = 256*data[7] + data[6]
        t = bytearray([data[0], data[1], data[2], data[3], data[4], data[5]])
        c = self.verify_crc(t)

        if crc != c:
            self.lastError = 'CRC error in sensor data.'
            return None, None

        return humidity, tempC

    def humidity(self):
        """Read humidity data from the sensor.

        Returns:
            float = humidity reading, None if error
        """
        time.sleep(.25)
        data = self.data()
        if data is not None:
            return self.data()[0]
        return None

    def temperature(self, fahrenheit=False):
        """Read temperature data from the sensor. (Celsius is default)

        Args:
            bool - if True returns temp in Fahrenheit. Default=False
        Returns:
            float = humidity reading, None if error
        """
        time.sleep(.25)
        data = self.data()
        if data is None:
            return None
        if fahrenheit:
            return self.data()[2]
        return self.data()[1]

    def fahrenheit(self):
        return self.temperature(True)

    def celsius(self):
        return self.temperature()

    @staticmethod
    def verify_crc(char):
        """Returns the 16-bit CRC of sensor data"""
        crc = 0xFFFF
        for l in char:
            crc = crc ^ l
            for i in range(1,9):
                if crc & 0x01:
                    crc = crc >> 1
                    crc = crc ^ 0xA001
                else:
                    crc = crc >> 1
        return crc

    def c_to_f(self, celsius):
        """Convert Celsius to Fahrenheit.

        Params:
            celsius: int containing C temperature

        Returns:
            String with Fahrenheit conversion. None if error.
        """
        if celsius is None:
           return

        if celsius == 0:
            return 32

        try:
            temp_f = float((celsius * 9 / 5) + 32)
            return (math.trunc(temp_f * 10)) / 10
        except Exception:
            self.lastError = 'Error converting %s celsius to fahrenheit' % celsius
            return None

    def last_error(self):
        return self.lastError
