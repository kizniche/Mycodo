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

import logging
import time

from .base_input import AbstractInput
from .sensorutils import convert_units


class MAX31856Sensor(AbstractInput):
    """
    A sensor support class that measures the MAX31856's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, clk, cs, miso, mosi, thermocouple_type='K', convert_to_unit=None, testing=False):
        super(MAX31856Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.max31855")
        self._temperature = None
        self._temperature_die = None

        self.clk = clk
        self.cs = cs
        self.miso = miso
        self.mosi = mosi
        self.convert_to_unit = convert_to_unit

        if not testing:
            self.sensor = max31856(self.logger, cs, miso, mosi, clk)
            if thermocouple_type == 'B':
                self.sensor.writeRegister(1, 0x00) #for B Type
            elif thermocouple_type == 'E':
                self.sensor.writeRegister(1, 0x01) #for E Type
            elif thermocouple_type == 'J':
                self.sensor.writeRegister(1, 0x02) #for J Type
            elif thermocouple_type == 'K':
                self.sensor.writeRegister(1, 0x03) #for K Type
            elif thermocouple_type == 'N':
                self.sensor.writeRegister(1, 0x04) #for N Type
            elif thermocouple_type == 'R':
                self.sensor.writeRegister(1, 0x05) #for R Type
            elif thermocouple_type == 'S':
                self.sensor.writeRegister(1, 0x06) #for S Type
            elif thermocouple_type == 'T':
                self.sensor.writeRegister(1, 0x07) #for T Type

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature_die={tdie})(temperature={temp})>".format(
            cls=type(self).__name__,
            tdie="{0:.2f}".format(self._temperature_die),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Temperature (Die): {tdie}, Temperature: {temp}".format(
            tdie="{0:.2f}".format(self._temperature_die),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SensorClass iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature_die=float('{0:.2f}'.format(self._temperature_die)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ MAX31856 temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    @property
    def temperature_die(self):
        """ MAX31856 temperature in Celsius """
        if self._temperature_die is None:  # update if needed
            self.read()
        return self._temperature_die

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self._temperature = None
        self._temperature_die = None

        temp = self.sensor.readThermocoupleTemp()
        temp = convert_units(
            'temperature', 'celsius', self.convert_to_unit, temp)
        temp_die = self.sensor.readJunctionTemp()
        temp_die = convert_units(
            'temperature_die', 'celsius', self.convert_to_unit, temp_die)

        return temp, temp_die

    def read(self):
        """
        Takes a reading from the MAX31856 and updates the
        self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._temperature,
             self._temperature_die) = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1


class max31856(object):
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

        if (tc_highByte & 0x80):
            temp -= 0x80000

        temp_C = temp * 0.0078125

        fault = out[3]

        if ((fault & 0x80) != 0):
            self.logger.error("Cold Junction Out-of-Range")
        elif ((fault & 0x40) != 0):
            self.logger.error("Thermocouple Out-of-Range")
        elif ((fault & 0x20) != 0):
            self.logger.error("Cold-Junction High Fault")
        elif ((fault & 0x10) != 0):
            self.logger.error("Cold-Junction Low Fault")
        elif ((fault & 0x08) != 0):
            self.logger.error("Thermocouple Temperature High Fault")
        elif ((fault & 0x04) != 0):
            self.logger.error("Thermocouple Temperature Low Fault")
        elif ((fault & 0x02) != 0):
            self.logger.error("Overvoltage or Undervoltage Input Fault")
        elif ((fault & 0x01) != 0):
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

        if (junc_msb & 0x80):
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
        addressByte = 0x80 | regNum;

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
            if (byte & 0x80):
                self.GPIO.output(self.mosiPin, self.GPIO.HIGH)
            else:
                self.GPIO.output(self.mosiPin, self.GPIO.LOW)
            byte <<= 1
            self.GPIO.output(self.clkPin, self.GPIO.LOW)

    def recvByte(self):
        byte = 0x00
        for bit in range(8):
            self.GPIO.output(self.clkPin, self.GPIO.HIGH)
            byte <<= 1
            if self.GPIO.input(self.misoPin):
                byte |= 0x1
            self.GPIO.output(self.clkPin, self.GPIO.LOW)
        return byte
