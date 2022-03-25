# coding=utf-8
#
# I2C code created in part by:
# Author: Tiequan Shao (info@sandboxelectronics.com)
# License: CC BY-NC-SA 3.0
#
# UART Code created in part by:
# Author: Zion Orent <zorent@ics.com>
# Copyright (c) 2015 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
import time

import copy

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
    'input_name_unique': 'MH_Z16',
    'input_manufacturer': 'Winsen',
    'input_name': 'MH-Z16',
    'input_library': 'smbus2/serial',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.winsen-sensor.com/sensors/co2-sensor/mh-z16.html',
    'url_datasheet': 'https://www.winsen-sensor.com/d/files/MH-Z16.pdf',

    'options_enabled': [
        'i2c_location',
        'uart_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
    ],

    'interfaces': ['UART', 'I2C'],
    'i2c_location': ['0x63'],
    'i2c_address_editable': True
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the MH-Z16's CO2 concentration."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.ser = None
        self.i2c = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        if self.input_dev.interface == 'UART':
            import serial

            if is_device(self.input_dev.uart_location):
                try:
                    self.ser = serial.Serial(
                        port=self.input_dev.uart_location,
                        timeout=1,
                        writeTimeout=5)
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.input_dev.uart_location))

        elif self.input_dev.interface == 'I2C':
            from smbus2 import SMBus

            self.i2c_address = int(str(self.input_dev.i2c_location), 16)
            self.cmd_measure = [0xFF, 0x01, 0x9C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x63]
            self.IOCONTROL = 0X0E << 3
            self.FCR = 0X02 << 3
            self.LCR = 0X03 << 3
            self.DLL = 0x00 << 3
            self.DLH = 0X01 << 3
            self.THR = 0X00 << 3
            self.RHR = 0x00 << 3
            self.TXLVL = 0X08 << 3
            self.RXLVL = 0X09 << 3
            self.i2c = SMBus(self.input_dev.i2c_bus)
            self.begin()

    def get_measurement(self):
        """Gets the MH-Z16's CO2 concentration in ppmv."""
        self.return_dict = copy.deepcopy(measurements_dict)

        co2 = None

        if self.input_dev.interface == 'UART':
            if not self.ser:
                self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
                return

            self.ser.flushInput()
            time.sleep(1)
            self.ser.write(bytearray([0xff, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]))
            time.sleep(.01)
            resp = self.ser.read(9)
            if len(resp) != 0:
                high = resp[2]
                low = resp[3]
                co2 = (high * 256) + low

        elif self.input_dev.interface == 'I2C':
            if not self.i2c:
                self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
                return

            self.write_register(self.FCR, 0x07)
            self.send(self.cmd_measure)
            try:
                co2 = self.parse(self.receive())
            except Exception:
                co2 = None

        self.value_set(0, co2)

        return self.return_dict

    def begin(self):
        try:
            self.write_register(self.IOCONTROL, 0x08)
        except IOError:
            pass

        self.write_register(self.FCR, 0x07)
        self.write_register(self.LCR, 0x83)
        self.write_register(self.DLL, 0x60)
        self.write_register(self.DLH, 0x00)
        self.write_register(self.LCR, 0x03)

    @staticmethod
    def parse(response):
        checksum = 0

        if len(response) < 9:
            return None

        for i in range(0, 9):
            checksum += response[i]

        if response[0] == 0xFF:
            if response[1] == 0x9C:
                if checksum % 256 == 0xFF:
                    return (response[2] << 24) + (response[3] << 16) + (response[4] << 8) + response[5]

        return None

    def read_register(self, reg_addr):
        time.sleep(0.01)
        return self.i2c.read_byte_data(self.i2c_address, reg_addr)

    def write_register(self, reg_addr, val):
        time.sleep(0.01)
        self.i2c.write_byte_data(self.i2c_address, reg_addr, val)

    def send(self, command):
        if self.read_register(self.TXLVL) >= len(command):
            self.i2c.write_i2c_block_data(self.i2c_address, self.THR, command)

    def receive(self):
        n = 9
        buf = []
        start = time.clock()

        while n > 0:
            rx_level = self.read_register(self.RXLVL)

            if rx_level > n:
                rx_level = n

            buf.extend(self.i2c.read_i2c_block_data(self.i2c_address, self.RHR, rx_level))
            n = n - rx_level

            if time.clock() - start > 0.2:
                break
        return buf
