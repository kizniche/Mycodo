# coding=utf-8
import fcntl
import logging
import os
import sys
import time

import io

sys.path.append(os.path.abspath(os.path.join(os.path.realpath(__file__), '../../..')))

from mycodo.devices.base_atlas import AbstractBaseAtlasScientific
from mycodo.utils.lockfile import LockFile


class AtlasScientificI2C(AbstractBaseAtlasScientific):
    """Class for Atlas Scientific sensor communication via I2C."""

    LONG_TIMEOUT = 1.5  # the timeout needed to query readings and calibrations
    SHORT_TIMEOUT = 0.5  # timeout for regular commands
    DEFAULT_BUS = 1  # the default bus for I2C on the newer Raspberry Pis, certain older boards use bus 0
    DEFAULT_ADDRESS = 98  # the default address for the sensor
    LONG_TIMEOUT_COMMANDS = ("R", "CAL")
    SLEEP_COMMANDS = ("SLEEP", )

    def __init__(self, i2c_address=DEFAULT_ADDRESS, i2c_bus=DEFAULT_BUS, moduletype="", name=""):
        super().__init__(interface='I2C', name=f"_{i2c_bus}_{i2c_address}")

        self.lock_timeout = 10
        self.lock_file = f'/var/lock/atlas_{__name__.replace(".", "_")}_{i2c_bus}_{i2c_address}.lock'

        # open two file streams, one for reading and one for writing
        # the specific I2C channel is selected with bus
        # it is usually 1, except for older revisions where its 0
        # wb and rb indicate binary read and write
        self.logger = logging.getLogger(f"{__name__}_{i2c_bus}_{i2c_address}")

        self._address = None
        self._name = name
        self._module = moduletype
        self._long_timeout = self.LONG_TIMEOUT
        self._short_timeout = self.SHORT_TIMEOUT

        self.setup = False

        try:
            self.file_read = io.open(f"/dev/i2c-{i2c_bus}", "rb", buffering=0)
            self.file_write = io.open(f"/dev/i2c-{i2c_bus}", "wb", buffering=0)

            # initializes I2C to either a user specified or default address
            self.set_i2c_address(i2c_address)
            self.setup = True

            (board,
             revision,
             firmware_version) = self.get_board_version()

            self.logger.info(
                f"Atlas Scientific Board: {board}, Rev: {revision}, Firmware: {firmware_version}")
        except Exception as err:
            self.logger.exception(
                f"{type(self).__name__} raised an exception when initializing: {err}")

    @property
    def long_timeout(self):
        return self._long_timeout

    @property
    def short_timeout(self):
        return self._short_timeout

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @property
    def moduletype(self):
        return self._module

    def get_device_info(self):
        if self._name == "":
            return f"module: {self._module}, address: {str(self.address)}"
        else:
            return f"module: {self._module}, address: {str(self.address)}, name: {self._name}"

    def set_i2c_address(self, addr):
        # set the I2C communications to the slave specified by the address
        # The commands for I2C dev using the ioctl functions are specified in
        # the i2c-dev.h file from i2c-tools
        i2c_slave = 0x703
        fcntl.ioctl(self.file_read, i2c_slave, addr)
        fcntl.ioctl(self.file_write, i2c_slave, addr)
        self._address = addr

    def write(self, cmd):
        """Append the null character and send the command over I2C."""
        cmd += "\00"
        # self.logger.error("Atlas Scientific command being sent: '{}'".format(cmd))
        self.file_write.write(cmd.encode('latin-1'))

    @staticmethod
    def response_valid(response):
        valid = True
        error_code = None
        if len(response) > 0:
            error_code = str(response[0])
            if error_code != '1':
                valid = False
        return valid, error_code

    def read(self, num_of_bytes=50):
        """Read a specified number of bytes from I2C, then parse and display the result."""
        res = self.file_read.read(num_of_bytes)  # read from the board
        is_valid, error_code = self.response_valid(res)
        if is_valid:
            char_list = list(map(lambda x: chr(x & ~0x80), list(res)))
            return "success", str(''.join(char_list))  # convert the char list to a string and returns it
        else:
            return "error", str(res[0])

    def get_command_timeout(self, command):
        timeout = None
        if command.upper().startswith(self.LONG_TIMEOUT_COMMANDS):
            timeout = self._long_timeout
        elif not command.upper().startswith(self.SLEEP_COMMANDS):
            timeout = self.short_timeout

        return timeout

    def query(self, query_str):
        """Send command to board and read response"""
        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=self.lock_timeout):
            try:
                # write a command to the board, wait the correct timeout,
                # and read the response
                self.write(query_str)

                if query_str.upper().startswith("SLEEP"):
                    return "success", "sleep mode"

                timeout_period = self.get_command_timeout(query_str)
                time.sleep(timeout_period)

                return self.read()
            except Exception as err:
                self.logger.debug(
                    f"{type(self).__name__} raised an exception when taking a reading: {err}")
                return "error", err
            finally:
                lf.lock_release(self.lock_file)

    def close(self):
        self.file_read.close()
        self.file_write.close()

    def list_i2c_devices(self):
        """Determine the addresses of connected I2C devices."""
        prev_addr = self.address  # save the current address so we can restore it after
        i2c_devices = []
        for i in range(0, 128):
            try:
                self.set_i2c_address(i)
                self.read()
                i2c_devices.append(i)
            except IOError:
                pass
        self.set_i2c_address(prev_addr)  # restore the address we were using
        return i2c_devices

    @staticmethod
    def build_string(data):
        try:
            list_chars = []
            for each_char in data:
                try:
                    if each_char.isalnum() or each_char in [".", ","]:
                        list_chars.append(each_char)
                except:
                    pass
            return ''.join(list_chars)
        except:
            return None


def print_devices(device_list, device):
    for i in device_list:
        if i == device:
            print("--> " + i.get_device_info())
        else:
            print(" - " + i.get_device_info())


def get_devices():
    device = AtlasScientificI2C()
    device_address_list = device.list_i2c_devices()
    device_list = []

    for i in device_address_list:
        device.set_i2c_address(i)
        status, moduletype = device.query("I")
        if status == "error":
            print(f">> WARNING: device at I2C address {i} has not been identified as an EZO device and will not be queried")
            continue
        print(f">> Device at I2C address {i} has been identified as an EZO device and will be queried")
        status, name = device.query("name,?")
        device_list.append(AtlasScientificI2C(i2c_address=i, moduletype=moduletype, name=name))
    return device_list


def print_help_text():
    print(f'''
>> Atlas Scientific I2C sample code
>> Any commands entered are passed to the default target device via I2C except:
  - Help
      brings up this menu
  - List 
      lists the available I2C circuits.
      the --> indicates the target device that will receive individual commands
  - xxx:[command]
      sends the command to the device at I2C address xxx 
      and sets future communications to that address
      Ex: "102:status" will send the command status to address 102
  - all:[command]
      sends the command to all devices
  - Poll[,x.xx]
      command continuously polls all devices
      the optional argument [,x.xx] lets you set a polling time
      where x.xx is greater than the minimum {AtlasScientificI2C.LONG_TIMEOUT:.2f} second timeout.
      by default it will poll every {AtlasScientificI2C.LONG_TIMEOUT:.2f} seconds
>> Pressing ctrl-c will stop the polling
    ''')


def main():
    print_help_text()

    device_list = get_devices()

    if not device_list:
        print("No Atlas Scientific devices found")
        return

    device = device_list[0]

    print_devices(device_list, device)

    real_raw_input = vars(__builtins__).get('raw_input', input)

    while True:

        user_cmd = real_raw_input(">> Enter command: ")

        # show all the available devices
        if user_cmd.upper().strip().startswith("LIST"):
            print_devices(device_list, device)

        # print the help text
        elif user_cmd.upper().startswith("HELP"):
            print_help_text()

        # continuous polling command automatically polls the board
        elif user_cmd.upper().strip().startswith("POLL"):
            cmd_list = user_cmd.split(',')
            if len(cmd_list) > 1:
                delaytime = float(cmd_list[1])
            else:
                delaytime = device.long_timeout

            # check for polling time being too short, change it to the minimum timeout if too short
            if delaytime < device.long_timeout:
                print("Polling time is shorter than timeout, setting polling time to %0.2f" % device.long_timeout)
                delaytime = device.long_timeout
            try:
                while True:
                    print("-------press ctrl-c to stop the polling")
                    for dev in device_list:
                        dev.write("R")
                    time.sleep(delaytime)
                    for dev in device_list:
                        print(dev.read())

            except KeyboardInterrupt:  # catches the ctrl-c command, which breaks the loop above
                print("Continuous polling stopped")
                print_devices(device_list, device)

        # send a command to all the available devices
        elif user_cmd.upper().strip().startswith("ALL:"):
            cmd_list = user_cmd.split(":")
            for dev in device_list:
                dev.write(cmd_list[1])

            # figure out how long to wait before reading the response
            timeout = device_list[0].get_command_timeout(cmd_list[1].strip())
            # if we dont have a timeout, dont try to read, since it means we issued a sleep command
            if (timeout):
                time.sleep(timeout)
                for dev in device_list:
                    print(dev.read())

        # if not a special keyword, see if we change the address, and communicate with that device
        else:
            try:
                cmd_list = user_cmd.split(":")
                if (len(cmd_list) > 1):
                    addr = cmd_list[0]

                    # go through the devices to figure out if its available
                    # and swith to it if it is
                    switched = False
                    for i in device_list:
                        if (i.address == int(addr)):
                            device = i
                            switched = True
                    if (switched):
                        print(device.query(cmd_list[1]))
                    else:
                        print("No device found at address " + addr)
                else:
                    # if no address change, just send the command to the device
                    print(device.query(user_cmd))
            except IOError:
                print("Query failed \n - Address may be invalid, use list command to see available addresses")


if __name__ == '__main__':
    main()
