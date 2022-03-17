# coding=utf-8
import logging
import os
import sys
import time

import serial
from serial import SerialException
from serial.serialutil import SerialTimeoutException

sys.path.append(os.path.abspath(os.path.join(os.path.realpath(__file__), '../../..')))

from mycodo.devices.base_atlas import AbstractBaseAtlasScientific
from mycodo.utils.lockfile import LockFile


class AtlasScientificUART(AbstractBaseAtlasScientific):
    """A Class to communicate with Atlas Scientific sensors via UART."""

    def __init__(self, serial_device, baudrate=9600):
        super().__init__(interface='UART', name=serial_device.replace("/", "_"))

        self.lock_timeout = 10
        self.lock_file = '/var/lock/atlas_UART_{}_{}.lock'.format(
            __name__.replace(".", "_"), serial_device.replace("/", "_"))

        self.logger = logging.getLogger(
            "{}_{}".format(__name__, serial_device.replace("/", "_")))

        self.setup = False
        self.serial_device = serial_device

        try:
            self.atlas_device = serial.Serial(
                port=serial_device,
                baudrate=baudrate,
                timeout=5,
                writeTimeout=5)

            cmd_return = self.send_cmd('C,0')  # Disable continuous measurements

            if cmd_return:
                (board,
                 revision,
                 firmware_version) = self.get_board_version()

                self.logger.info(
                    "Atlas Scientific Board: {brd}, Rev: {rev}, Firmware: {fw}".format(
                        brd=board,
                        rev=revision,
                        fw=firmware_version))
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
            next_char = self.atlas_device.read(1)
            if next_char in [b'', b'\r', '']:
                break
            line_buffer.append(next_char)
            if (len(line_buffer) >= lsl and
                    line_buffer[-lsl:] == list('\r')):
                break
        return b''.join(line_buffer)

    def query(self, query_str):
        """Send command and return reply."""
        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=self.lock_timeout):
            try:
                self.send_cmd(query_str)
                time.sleep(1.3)
                response = self.read_lines()
                return 'success', response
            except Exception as err:
                self.logger.exception(
                    "{cls} raised an exception when taking a reading: "
                    "{err}".format(cls=type(self).__name__, err=err))
                return "error", err
            finally:
                lf.lock_release(self.lock_file)

    def read_lines(self):
        """
        also taken from ftdi lib to work with modified readline function
        """
        lines = []
        try:
            while True:
                line = self.read_line().decode()
                if not line:
                    break
                    # self.atlas_device.flush_input()
                lines.append(line)
            return lines
        except SerialException:
            self.logger.exception('Read Lines')
            return None
        except AttributeError:
            self.logger.exception('UART device not initialized')
            return None

    def write(self, cmd):
        self.send_cmd(cmd)

    def send_cmd(self, cmd):
        """
        Send command to the Atlas Sensor.
        Before sending, add Carriage Return at the end of the command.
        :param cmd:
        :return:
        """
        buf = "{cmd}\r".format(cmd=cmd)  # add carriage return
        try:
            self.atlas_device.write(buf.encode())
            return True
        except SerialTimeoutException:
            self.logger.error("SerialTimeoutException: Write timeout. This indicates "
                              "you may not have the correct device configured.")
        except SerialException:
            self.logger.exception('Send CMD')
            return None
        except AttributeError:
            self.logger.exception('UART device not initialized')
            return None


def main():
    device_str = input("Device? (e.g. '/dev/ttyAMA1'): ")
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
