# coding=utf-8
import copy
import fcntl
import io
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import is_device

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'K30',
    'input_manufacturer': 'CO2Meter',
    'input_name': 'K30',
    'input_library': 'serial (UART)',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.co2meter.com/products/k-30-co2-sensor-module',
    'url_datasheet': 'http://co2meters.com/Documentation/Datasheets/DS_SE_0118_CM_0024_Revised9%20(1).pdf',

    'options_enabled': [
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['I2C', 'UART'],
    'i2c_location': ['0x68'],
    'i2c_address_editable': False,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the K30's CO2 concentration."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.interface = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import serial

        self.interface = self.input_dev.interface
        self.logger.debug(f"K30 Interface: {self.interface}")

        if self.interface == 'UART':
            if self.input_dev.uart_location and is_device(self.input_dev.uart_location):
                try:
                    self.sensor = serial.Serial(
                        port=self.input_dev.uart_location,
                        baudrate=self.input_dev.baud_rate,
                        timeout=1,
                        writeTimeout=5)
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error('Could not open "{dev}". Check the device location is correct.'.format(
                    dev=self.input_dev.uart_location))
        elif self.interface == 'I2C':
            self.sensor = K30Sensor(bus=f"/dev/i2c-{self.input_dev.i2c_bus}", logger=self.logger)

    def get_measurement(self):
        """Gets the K30's CO2 concentration in ppmv via UART or I2C."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.interface == 'UART':
            try:
                self.sensor.flushInput()
                time.sleep(1)
                self.sensor.write(bytearray([0xfe, 0x44, 0x00, 0x08, 0x02, 0x9f, 0x25]))
                time.sleep(0.5)
                resp = self.sensor.read(7)
                if len(resp) != 0:
                    high = resp[3]
                    low = resp[4]
                    co2 = (high * 256) + low
                    self.value_set(0, co2)
                    self.logger.debug(f"CO2: {co2}")
            except:
                self.logger.exception("UART")
        elif self.interface == 'I2C':
            try:
                co2, csum_ret, csum_calc = self.sensor.read_co2_ppm()

                checksum_str = "GOOD" if csum_calc == csum_ret else "BAD"
                self.logger.debug(f"CO2: {co2}, Checksum {checksum_str} (returned: {csum_ret}, calculated: {csum_calc})")

                if co2 < 0 or co2 > 10000:
                    self.logger.error(f"CO2 measurement must be between 0 and 10,000 ppm (measured: {co2})")
                else:
                    self.value_set(0, co2)
            except:
                self.logger.exception("I2C")

        return self.return_dict

    def pre_stop(self):
        if self.interface == 'I2C':
            self.sensor.close()

class K30Sensor:
    """
    From https://gist.github.com/galexite/12c9e4a5b21070d05619b31a1c970933
    Copyright (c) 2019 George White.
    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
    COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    Changes: Updated to work with Python 3
    """
    I2C_SLAVE = 0x0703
    CMD_READ_REG = 0x22
    REG_CO2_PPM = 0x08

    def __init__(self, bus, addr=0x68, logger=None):
        self.logger = logger

        self.fr = io.open(bus, "rb", buffering=0)
        self.fw = io.open(bus, "wb", buffering=0)
        
        fcntl.ioctl(self.fr, self.I2C_SLAVE, addr)
        fcntl.ioctl(self.fw, self.I2C_SLAVE, addr)

    def write(self, *data):
        if type(data) is list or type(data) is tuple:
            data = bytes(data)
        self.fw.write(data)

    def read(self, count):
        s = self.fr.read(count)
        l = []
        if len(s) != 0:
            for n in s:
                l.append(n)
        return l

    def read_co2_ppm(self):
        checksum = (self.CMD_READ_REG + self.REG_CO2_PPM) & 0xFF
        self.write(self.CMD_READ_REG, 0, self.REG_CO2_PPM, checksum)
        time.sleep(0.5)
        response = self.read(4)
        if self.logger:
            self.logger.debug(f"K30 sensor response: {response}")
        checksum_calculated = response[0] + response[1] + response[2]
        checksum_returned = response[3]
        co2 = ((response[1] & 0xFF) << 8) | (response[2] & 0xFF)
        return co2, checksum_returned, checksum_calculated

    def close(self):
        self.fw.close()
        self.fr.close()
