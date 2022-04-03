# coding=utf-8
# The MIT License (MIT)
#
# Copyright (c) 2015 Stephen P. Smith
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import time

import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Object'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Die'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MAX31856',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31856',
    'input_library': 'RPi.GPIO',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/sensors/MAX31856.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/MAX31856.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/3263',

    'options_enabled': [
        'thermocouple_type',
        'pin_cs',
        'pin_miso',
        'pin_mosi',
        'pin_clock',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1')
    ],

    'interfaces': ['UART'],
    'pin_cs': 8,
    'pin_miso': 9,
    'pin_mosi': 10,
    'pin_clock': 11,
    'thermocouple_type': [
        ('B', 'Type-B'),
        ('E', 'Type-E'),
        ('J', 'Type-J'),
        ('K', 'Type-K'),
        ('N', 'Type-N'),
        ('R', 'Type-R'),
        ('S', 'Type-S'),
        ('T', 'Type-T')
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that measures the MAX31856's temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.sensor = MAX31856(
            self.logger,
            self.input_dev.pin_cs,
            self.input_dev.pin_miso,
            self.input_dev.pin_mosi,
            self.input_dev.pin_clock)

        if self.input_dev.thermocouple_type == 'B':
            self.sensor.writeRegister(1, 0x00)  # B Type
        elif self.input_dev.thermocouple_type == 'E':
            self.sensor.writeRegister(1, 0x01)  # E Type
        elif self.input_dev.thermocouple_type == 'J':
            self.sensor.writeRegister(1, 0x02)  # J Type
        elif self.input_dev.thermocouple_type == 'K':
            self.sensor.writeRegister(1, 0x03)  # K Type
        elif self.input_dev.thermocouple_type == 'N':
            self.sensor.writeRegister(1, 0x04)  # N Type
        elif self.input_dev.thermocouple_type == 'R':
            self.sensor.writeRegister(1, 0x05)  # R Type
        elif self.input_dev.thermocouple_type == 'S':
            self.sensor.writeRegister(1, 0x06)  # S Type
        elif self.input_dev.thermocouple_type == 'T':
            self.sensor.writeRegister(1, 0x07)  # T Type

    def get_measurement(self):
        """Get measurements and store in the database."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.readThermocoupleTemp())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.readJunctionTemp())

        return self.return_dict


class MAX31856(object):
    """Read Temperature on the Raspberry PI from the MAX31856 chip using GPIO
       Any pins can be used for CS (chip select), MISO, MOSI and CLK
    """

    def __init__(self, logger, csPin=8, misoPin=9, mosiPin=10, clkPin=11):
        import RPi.GPIO as GPIO
        self.logger = logger
        self.GPIO = GPIO
        self.csPin = csPin
        self.misoPin = misoPin
        self.mosiPin = mosiPin
        self.clkPin = clkPin
        self.setupGPIO()
        #
        # Config Register 2
        # ------------------
        # bit 7: Reserved                                -> 0
        # bit 6: Averaging Mode 1 Sample                 -> 0 (default)
        # bit 5: Averaging Mode 1 Sample                 -> 0 (default)
        # bit 4: Averaging Mode 1 Sample                 -> 0 (default)
        # bit 3: Thermocouple Type -> K Type (default)   -> 0 (default)
        # bit 2: Thermocouple Type -> K Type (default)   -> 0 (default)
        # bit 1: Thermocouple Type -> K Type (default)   -> 1 (default)
        # bit 0: Thermocouple Type -> K Type (default)   -> 1 (default)
        #
        # select thermocouple type
        # self.writeRegister(1, 0x00) #for B Type
        # self.writeRegister(1, 0x01) #for E Type
        # self.writeRegister(1, 0x02) #for J Type
        # self.writeRegister(1, 0x03) #for K Type
        # self.writeRegister(1, 0x04) #for N Type
        # self.writeRegister(1, 0x05) #for R Type
        # self.writeRegister(1, 0x06) #for S Type
        # self.writeRegister(1, 0x07) #for T Type

    def setupGPIO(self):
        self.GPIO.setwarnings(False)
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.csPin, self.GPIO.OUT)
        self.GPIO.setup(self.misoPin, self.GPIO.IN)
        self.GPIO.setup(self.mosiPin, self.GPIO.OUT)
        self.GPIO.setup(self.clkPin, self.GPIO.OUT)

        self.GPIO.output(self.csPin, self.GPIO.HIGH)
        self.GPIO.output(self.clkPin, self.GPIO.LOW)
        self.GPIO.output(self.mosiPin, self.GPIO.LOW)

    def readThermocoupleTemp(self):
        self.requestTempConv()

        # read 4 registers starting with register 12
        out = self.readRegisters(0x0c, 4)

        [tc_highByte, tc_middleByte, tc_lowByte] = [out[0], out[1], out[2]]
        temp = ((tc_highByte << 16) | (tc_middleByte << 8) | tc_lowByte) >> 5

        if tc_highByte & 0x80:
            temp -= 0x80000

        temp_C = temp * 0.0078125

        fault = out[3]

        if (fault & 0x80) != 0:
            self.logger.error("Cold Junction Out-of-Range")
        elif (fault & 0x40) != 0:
            self.logger.error("Thermocouple Out-of-Range")
        elif (fault & 0x20) != 0:
            self.logger.error("Cold-Junction High Fault")
        elif (fault & 0x10) != 0:
            self.logger.error("Cold-Junction Low Fault")
        elif (fault & 0x08) != 0:
            self.logger.error("Thermocouple Temperature High Fault")
        elif (fault & 0x04) != 0:
            self.logger.error("Thermocouple Temperature Low Fault")
        elif (fault & 0x02) != 0:
            self.logger.error("Overvoltage or Undervoltage Input Fault")
        elif (fault & 0x01) != 0:
            self.logger.error("Thermocouple Open-Circuit Fault")
        else:
            return temp_C

    def readJunctionTemp(self):
        self.requestTempConv()

        # read 3 registers starting with register 9
        out = self.readRegisters(0x09, 3)

        offset = out[0]

        [junc_msb, junc_lsb] = [out[1], out[2]]

        temp = ((junc_msb << 8) | junc_lsb) >> 2
        temp = offset + temp

        if junc_msb & 0x80:
            temp -= 0x4000

        temp_C = temp * 0.015625

        return temp_C

    def requestTempConv(self):
        #
        # Config Register 1
        # ------------------
        # bit 7: Conversion Mode                         -> 0 (Normally Off Mode)
        # bit 6: 1-shot                                  -> 1 (ON)
        # bit 5: open-circuit fault detection            -> 0 (off)
        # bit 4: open-circuit fault detection            -> 0 (off)
        # bit 3: Cold-junction temerature sensor enabled -> 0 (default)
        # bit 2: Fault Mode                              -> 0 (default)
        # bit 1: fault status clear                      -> 1 (clear any fault)
        # bit 0: 50/60 Hz filter select                  -> 0 (60Hz)
        #
        # write config register 0
        self.writeRegister(0, 0x42)
        # conversion time is less than 150ms
        time.sleep(.2)  # give it 200ms for conversion

    def writeRegister(self, regNum, dataByte):
        self.GPIO.output(self.csPin, self.GPIO.LOW)

        # 0x8x to specify 'write register value'
        addressByte = 0x80 | regNum

        # first byte is address byte
        self.sendByte(addressByte)
        # the rest are data bytes
        self.sendByte(dataByte)

        self.GPIO.output(self.csPin, self.GPIO.HIGH)

    def readRegisters(self, regNumStart, numRegisters):
        out = []
        self.GPIO.output(self.csPin, self.GPIO.LOW)

        # 0x to specify 'read register value'
        self.sendByte(regNumStart)

        for _ in range(numRegisters):
            data = self.recvByte()
            out.append(data)

        self.GPIO.output(self.csPin, self.GPIO.HIGH)
        return out

    def sendByte(self, byte):
        for _ in range(8):
            self.GPIO.output(self.clkPin, self.GPIO.HIGH)
            if byte & 0x80:
                self.GPIO.output(self.mosiPin, self.GPIO.HIGH)
            else:
                self.GPIO.output(self.mosiPin, self.GPIO.LOW)
            byte <<= 1
            self.GPIO.output(self.clkPin, self.GPIO.LOW)

    def recvByte(self):
        byte = 0x00
        for _ in range(8):
            self.GPIO.output(self.clkPin, self.GPIO.HIGH)
            byte <<= 1
            if self.GPIO.input(self.misoPin):
                byte |= 0x1
            self.GPIO.output(self.clkPin, self.GPIO.LOW)
        return byte
