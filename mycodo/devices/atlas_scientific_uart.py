# coding=utf-8
import logging
import time

import fasteners
import os
import serial
from serial import SerialException

from mycodo.config import ATLAS_PH_LOCK_FILE


class AtlasScientificUART:
    """A Class to communicate with Atlas Scientific sensors via UART"""

    def __init__(self, serial_device, baudrate=9600):
        self.logger = logging.getLogger(
            "mycodo.device.atlas_scientific_uart_{dev}".format(dev=serial_device))
        self.setup = False
        self.serial_device = serial_device
        try:
            self.ser = serial.Serial(port=serial_device,
                                     baudrate=baudrate,
                                     timeout=0)
            self.setup = True
        except serial.SerialException as err:
            self.logger.exception(
                "{cls} raised an exception when initializing: "
                "{err}".format(cls=type(self).__name__, err=err))
            self.logger.exception('Opening serial')

    def read_line(self):
        """
        taken from the ftdi library and modified to 
        use the ezo line separator "\r"
        """
        lsl = len('\r')
        line_buffer = []
        while True:
            next_char = self.ser.read(1)
            if next_char == b'':
                break
            line_buffer.append(next_char)
            if (len(line_buffer) >= lsl and
                    line_buffer[-lsl:] == list('\r')):
                break
        return b''.join(line_buffer)

    def query(self, query_str):
        """ Send command and return reply """
        lock_file_amend = '{lf}.{dev}'.format(lf=ATLAS_PH_LOCK_FILE,
                                              dev=self.serial_device.replace("/", "-"))

        try:
            lock = fasteners.InterProcessLock(lock_file_amend)
            lock_acquired = False

            for _ in range(600):
                lock_acquired = lock.acquire(blocking=False)
                if lock_acquired:
                    break
                else:
                    time.sleep(0.1)

            if lock_acquired:
                self.send_cmd(query_str)
                time.sleep(1.3)
                response = self.read_lines()
                lock.release()
                return response
            else:
                self.logger.error("Could not acquire Atlas UART lock. Breaking lock.")

            os.remove(lock_file_amend)

        except Exception as err:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=err))
            return None

    def read_lines(self):
        """
        also taken from ftdi lib to work with modified readline function
        """
        lines = []
        try:
            while True:
                line = self.read_line()
                if not line:
                    break
                    # self.ser.flush_input()
                lines.append(line)
            return lines

        except SerialException:
            self.logger.exception('Read Lines')
            return None
        except AttributeError:
            self.logger.exception('UART device not initialized')
            return None

    def send_cmd(self, cmd):
        """
        Send command to the Atlas Sensor.
        Before sending, add Carriage Return at the end of the command.
        :param cmd:
        :return:
        """
        buf = "{cmd}\r".format(cmd=cmd)  # add carriage return
        if type(buf) is str:
            buf = buf.encode()
        try:
            self.ser.write(buf)
            return True
        except SerialException:
            self.logger.exception('Send CMD')
            return None
        except AttributeError:
            self.logger.exception('UART device not initialized')
            return None


def main():
    device_str = input("Device? (e.g. '/dev/ttyS0'): ")
    baud_str = input("Baud rate? (e.g. '9600'): ")

    device = AtlasScientificUART(device_str, baudrate=int(baud_str))

    print(">> Atlas Scientific sample code")
    print(">> Any commands entered are passed to the board via UART")
    print(">> Pressing ctrl-c will stop the polling")

    while True:
        input_str = input("Enter command: ")

        if len(input_str) == 0:
            print("Please input valid command.")
        else:
            try:
                print(device.query(input_str))
            except IOError:
                print("Send command failed\n")


if __name__ == "__main__":
    main()
