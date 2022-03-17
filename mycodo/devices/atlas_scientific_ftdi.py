# coding=utf-8
import logging
import os
import sys
import time

import pylibftdi
from pylibftdi import Driver
from pylibftdi.device import Device
from pylibftdi.driver import FtdiError

sys.path.append(os.path.abspath(os.path.join(os.path.realpath(__file__), '../../..')))

from mycodo.devices.base_atlas import AbstractBaseAtlasScientific
from mycodo.utils.lockfile import LockFile


class AtlasScientificFTDI(AbstractBaseAtlasScientific, Device):
    """A Class to communicate with Atlas Scientific sensors via FTDI."""

    def __init__(self, serial_device):
        Device.__init__(self, mode='t', device_id=serial_device)
        super().__init__(interface='FTDI', name=serial_device.replace("/", "_"))

        self.lock_timeout = 10
        self.lock_file = '/var/lock/atlas_FTDI_{}_{}.lock'.format(
            __name__.replace(".", "_"), serial_device)

        self.logger = logging.getLogger(
            "{}_{}".format(__name__, serial_device))

        self.send_cmd("C,0")  # turn off continuous mode
        time.sleep(1)
        self.flush()

        (board,
         revision,
         firmware_version) = self.get_board_version()

        self.logger.info(
            "Atlas Scientific Board: {brd}, Rev: {rev}, Firmware: {fw}".format(
                brd=board,
                rev=revision,
                fw=firmware_version))

        self.setup = True

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
                return 'error', err
            finally:
                lf.lock_release(self.lock_file)

    def read_line(self, size=0):
        """
        taken from the ftdi library and modified to
        use the ezo line separator "\r"
        """
        lsl = len('\r')
        line_buffer = []
        while True:
            next_char = self.read(1)
            if next_char == '' or 0 < size < len(line_buffer):
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
                    break
                    # self.flush_input()
                lines.append(line)
            return lines

        except FtdiError:
            print("Failed to read from the sensor.")
            return ''

    def send_cmd(self, cmd):
        """
        Send command to the Atlas Sensor.
        Before sending, add Carriage Return at the end of the command.
        :param cmd:
        :return:
        """
        buf = cmd + "\r"  # add carriage return
        try:
            self.write(buf)
            return True
        except FtdiError:
            print("Failed to send command to the sensor.")

        return False


def get_ftdi_device_list():
    """
    return a list of lines, each a colon-separated
    vendor:product:serial summary of detected devices
    """
    dev_list = []

    for device in Driver().list_devices():
        # list_devices returns bytes rather than strings
        dev_info = map(lambda x: x, device)
        # device must always be this triple
        vendor, product, serial = dev_info
        dev_list.append(serial)
    return dev_list


if __name__ == '__main__':

    real_raw_input = vars(__builtins__).get('raw_input', input)  # used to find the correct function for python2/3

    print("\nWelcome to the Atlas Scientific Raspberry Pi FTDI Serial example.\n")
    print("    Any commands entered are passed to the board via UART except:")
    print("    Poll,xx.x command continuously polls the board every xx.x seconds")
    print("    Pressing ctrl-c will stop the polling\n")
    print("    Press enter to receive all data in buffer (for continuous mode) \n")
    print("Discovered FTDI serial numbers:")

    devices = get_ftdi_device_list()
    cnt_all = len(devices)

    # print "\nIndex:\tSerial: "
    for i in range(cnt_all):
        print("\nIndex: ", i, " Serial: ", devices[i])
    print("===================================")

    index = 0
    while True:
        index = real_raw_input("Please select a device index: ")

        try:
            dev = AtlasScientificFTDI(devices[int(index)])
            break
        except pylibftdi.FtdiError as e:
            print("Error, ", e)
            print("Please input a valid index")

    print("")
    print(">> Opened device ", devices[int(index)])
    print(">> Any commands entered are passed to the board via FTDI:")

    time.sleep(1)
    dev.flush()

    while True:
        input_val = real_raw_input("Enter command: ")

        # continuous polling command automatically polls the board
        if input_val.upper().startswith("POLL"):
            delaytime = float(input_val.split(',')[1])

            dev.send_cmd("C,0")  # turn off continuous mode
            # clear all previous data
            time.sleep(1)
            dev.flush()

            # get the information of the board you're polling
            print("Polling sensor every %0.2f seconds, press ctrl-c to stop polling" % delaytime)

            try:
                while True:
                    dev.send_cmd("R")
                    lines = dev.read_lines()
                    for line in lines:
                        # print line
                        if line[0] != '*':
                            print("Response: {}".format(line))
                    time.sleep(delaytime)

            except KeyboardInterrupt:  # catches the ctrl-c command, which breaks the loop above
                print("Continuous polling stopped")

        else:
            # pass commands straight to board
            if len(input_val) == 0:
                lines = dev.read_lines()
                for line in lines:
                    print(line)
            else:
                dev.send_cmd(input_val)
                time.sleep(1.3)
                lines = dev.read_lines()
                for line in lines:
                    print(line)
