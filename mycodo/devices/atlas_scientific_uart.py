# coding=utf-8
import logging
import serial
import RPi.GPIO as GPIO
from serial import SerialException

logger = logging.getLogger("mycodo.device.atlas_scientific_uart")


class AtlasScientificUART:
    """A Class to communicate with Atlas Scientific sensors via UART"""

    def __init__(self, serial_device=None, baudrate=9600):
        self.serial_device = serial_device
        self.baudrate = baudrate
        self.setup = True
        if serial_device is None:
            if GPIO.RPI_INFO['P1_REVISION'] == 3:
                self.serial_device = "/dev/ttyS0"
            else:
                self.serial_device = "/dev/ttyAMA0"

        try:
            self.ser = serial.Serial(port=self.serial_device,
                                     baudrate=self.baudrate,
                                     timeout=0)
        except serial.SerialException:
            self.setup = False
            logger.exception('Opening serial')

    def read_line(self):
        """
        taken from the ftdi library and modified to 
        use the ezo line separator "\r"
        """
        lsl = len('\r')
        line_buffer = []
        while True:
            next_char = self.ser.read(1)
            if next_char == '':
                break
            line_buffer.append(next_char)
            if (len(line_buffer) >= lsl and
                    line_buffer[-lsl:] == list('\r')):
                break
        return ''.join(line_buffer)

    def read_lines(self):
        """
        also taken from ftdi lib to work with modified readline function
        """
        lines = []
        try:
            while True:
                line = self.read_line()
                if not line:
                    self.ser.flush_input()
                    break
                lines.append(line)
            return lines

        except SerialException:
            logger.exception('Read Lines')
            return None

    def send_cmd(self, cmd):
        """
        Send command to the Atlas Sensor.
        Before sending, add Carriage Return at the end of the command.
        :param cmd:
        :return:
        """
        buf = "{cmd}\r".format(cmd=cmd)  # add carriage return
        try:
            self.ser.write(buf)
            return True
        except SerialException:
            logger.exception('Send CMD')
            return None
