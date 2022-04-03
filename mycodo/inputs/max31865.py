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
import math
import time

import copy

from mycodo.inputs.base_input import AbstractInput

# import numpy  # Used for more accurate temperature calculation

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MAX31865',
    'input_manufacturer': 'MAXIM',
    'input_name': 'MAX31865',
    'input_library': 'RPi.GPIO',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31865.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/3328',

    'message': 'Note: This module does not allow for multiple sensors to be connected at the same time. '
               'For multi-sensor support, use the MAX31865 CircuitPython Input.',

    'options_enabled': [
        'thermocouple_type',
        'pin_cs',
        'pin_miso',
        'pin_mosi',
        'pin_clock',
        'ref_ohm',
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
        ('PT100', 'PT-100'),
        ('PT1000', 'PT-1000')
    ],
    'ref_ohm': 0
}


class InputModule(AbstractInput):
    """A sensor support class that measures the MAX31865's temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.thermocouple_type = None
        self.ref_ohm = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.thermocouple_type = self.input_dev.thermocouple_type
        self.ref_ohm = self.input_dev.ref_ohm

        self.sensor = max31865_sen(
            self.logger,
            self.input_dev.pin_cs,
            self.input_dev.pin_miso,
            self.input_dev.pin_mosi,
            self.input_dev.pin_clock)

    def get_measurement(self):
        """Gets the measurement in units by reading the."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        self.value_set(0, self.sensor.readTemp(self.thermocouple_type, self.ref_ohm))

        return self.return_dict

    def stop_input(self):
        """Called by InputController class when sensors are deactivated."""
        self.sensor.cleanupGPIO()
        self.running = False


class max31865_sen(object):
    """Reading Temperature from the MAX31865 with GPIO using
       the Raspberry Pi.  Any pins can be used.
       Numpy can be used to completely solve the Callendar-Van Dusen equation
       but it slows the temp reading down.  I commented it out in the code.
       Both the quadratic formula using Callendar-Van Dusen equation (ignoring the
       3rd and 4th degree parts of the polynomial) and the straight line approx.
       temperature is calculated with the quadratic formula one being the most accurate.
    """

    def __init__(self, logger, csPin=8, misoPin=9, mosiPin=10, clkPin=11):
        self.logger = logger
        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        self.csPin = csPin
        self.misoPin = misoPin
        self.mosiPin = mosiPin
        self.clkPin = clkPin
        self.setupGPIO()

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

    def cleanupGPIO(self):
        self.GPIO.cleanup()

    def readTemp(self, device, resistor_ref):
        """
        Read the temperature of a PT100 or PT1000 probe
        :param device: 'PT100' or 'PT1000'
        :param resistor_ref: reference ohms
        :return:
        """
        #
        # b10000000 = 0x80
        # 0x8x to specify 'write register value'
        # 0xx0 to specify 'configuration register'
        #
        # 0b10110010 = 0xB2
        # Config Register
        # ---------------
        # bit 7: Vbias -> 1 (ON)
        # bit 6: Conversion Mode -> 0 (MANUAL)
        # bit5: 1-shot ->1 (ON)
        # bit4: 3-wire select -> 1 (3 wire config)
        # bits 3-2: fault detection cycle -> 0 (none)
        # bit 1: fault status clear -> 1 (clear any fault)
        # bit 0: 50/60 Hz filter select -> 0 (60Hz)
        #
        # 0b11010010 or 0xD2 for continuous auto conversion
        # at 60Hz (faster conversion)
        #

        # one shot
        self.writeRegister(0, 0xB2)

        # conversion time is less than 100ms
        time.sleep(.1)  # give it 100ms for conversion

        # read all registers
        out = self.readRegisters(0, 8)

        conf_reg = out[0]
        self.logger.debug("config register byte: {}".format(conf_reg))

        [rtd_msb, rtd_lsb] = [out[1], out[2]]
        rtd_ADC_Code = ((rtd_msb << 8) | rtd_lsb) >> 1

        temp_c = self.calcPTTemp(rtd_ADC_Code, device, resistor_ref)
        # print("Temperature: {temp} C".format(temp=temp_C))

        # [hft_msb, hft_lsb] = [out[3], out[4]]
        # hft = ((hft_msb << 8) | hft_lsb) >> 1
        # print("high fault threshold: {}".format(hft))

        # [lft_msb, lft_lsb] = [out[5], out[6]]
        # lft = ((lft_msb << 8) | lft_lsb) >> 1
        # print("low fault threshold: {}".format(lft))

        status = out[7]
        #
        # 10 Mohm resistor is on breakout board to help
        # detect cable faults
        # bit 7: RTD High Threshold / cable fault open
        # bit 6: RTD Low Threshold / cable fault short
        # bit 5: REFIN- > 0.85 x VBias -> must be requested
        # bit 4: REFIN- < 0.85 x VBias (FORCE- open) -> must be requested
        # bit 3: RTDIN- < 0.85 x VBias (FORCE- open) -> must be requested
        # bit 2: Overvoltage / undervoltage fault
        # bits 1,0 don't care
        # print "Status byte: %x" % status

        if (status & 0x80) == 1:
            raise FaultError("High threshold limit (Cable fault/open)")
        if (status & 0x40) == 1:
            raise FaultError("Low threshold limit (Cable fault/short)")
        if (status & 0x04) == 1:
            raise FaultError("Overvoltage or Undervoltage Error")

        return temp_c

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

    @staticmethod
    def calcPTTemp(RTD_ADC_Code, device='PT100', resistor_ref=None):
        # Reference Resistor
        if resistor_ref:
            R_REF = resistor_ref
        elif device == 'PT100':
            R_REF = 400.0
        elif device == 'PT1000':
            R_REF = 4000.0
        else:
            return

        Res0 = 100.0  # Resistance at 0 degC for 400ohm R_Ref
        a = .00390830
        b = -.000000577500

        # c = -0.00000000000418301  # for -200 <= T <= 0 (degC)
        # c = 0  # for 0 <= T <= 850 (degC)

        # print("RTD ADC Code: {}".format(RTD_ADC_Code))

        Res_RTD = (RTD_ADC_Code * R_REF) / 32768.0  # Probe Resistance
        # print("{dev} Resistance: {res} ohms".format(dev=device, res=Res_RTD))

        # Callendar-Van Dusen equation
        # Res_RTD = Res0 * (1 + a*T + b*T**2 + c*(T-100)*T**3)  # T <= -200
        # Res_RTD = Res0 + a*Res0*T + b*Res0*T**2  # T >= 0
        # (c*Res0)T**4 - (c*Res0)*100*T**3
        # + (b*Res0)*T**2 + (a*Res0)*T + (Res0 - Res_RTD) = 0

        # quadratic formula:
        # for 0 <= T <= 850 (degC)
        temp_C = -(a * Res0) + math.sqrt(a * a * Res0 * Res0 - 4 * (b * Res0) * (Res0 - Res_RTD))
        temp_C = temp_C / (2 * (b * Res0))
        # print("Callendar-Van Dusen Temp (degC > 0): {} degC".format(temp_C))

        # removing numpy.roots will greatly speed things up
        # temp_C_numpy = numpy.roots([c*Res0, -c*Res0*100, b*Res0, a*Res0, (Res0 - Res_RTD)])
        # temp_C_numpy = abs(temp_C_numpy[-1])
        # print("Solving Full Callendar-Van Dusen using numpy: {}".format(temp_C_numpy))

        if temp_C < 0:  # use straight line approximation if less than 0
            # Can also use python lib numpy to solve cubic
            # Should never get here in this application
            temp_C_line = (RTD_ADC_Code / 32.0) - 256.0
            # print("Straight Line Approx. Temp: {} degC".format(temp_C_line))
            return temp_C_line
        return temp_C


class FaultError(Exception):
    pass


if __name__ == "__main__":
    csPin = 8
    misoPin = 9
    mosiPin = 10
    clkPin = 11
    max_input = max31865_sen(csPin, misoPin, mosiPin, clkPin)
    print("Temp: {}".format(max_input.readTemp('PT100', 400)))
    max_input.cleanupGPIO()
