#!/usr/bin/python
# coding=utf-8
import io  # used to create file streams
import fcntl  # used to access I2C parameters like addresses

import time  # used for sleep delay and timestamps
import string  # helps parse strings


class AtlasI2C:
    long_timeout = 1.5  # the timeout needed to query readings and calibrations
    short_timeout = 0.5  # timeout for regular commands
    default_bus = 1  # the default bus for I2C on the newer Raspberry Pis, certain older boards use bus 0
    default_address = 98  # the default address for the sensor

    def __init__(self, address=default_address, bus=default_bus):
        # open two file streams, one for reading and one for writing
        # the specific I2C channel is selected with bus
        # it is usually 1, except for older revisions where its 0
        # wb and rb indicate binary read and write
        self.file_read = io.open("/dev/i2c-" + str(bus), "rb", buffering=0)
        self.file_write = io.open("/dev/i2c-" + str(bus), "wb", buffering=0)

        # initializes I2C to either a user specified or default address
        self.set_i2c_address(address)

    def set_i2c_address(self, addr):
        # set the I2C communications to the slave specified by the address
        # The commands for I2C dev using the ioctl functions are specified in
        # the i2c-dev.h file from i2c-tools
        I2C_SLAVE = 0x703
        fcntl.ioctl(self.file_read, I2C_SLAVE, addr)
        fcntl.ioctl(self.file_write, I2C_SLAVE, addr)

    def write(self, cmd):
        # appends the null character and sends the string over I2C
        cmd += "\00"
        self.file_write.write(cmd)

    def read(self, num_of_bytes=31):
        # reads a specified number of bytes from I2C, then parses and displays the result
        res = self.file_read.read(num_of_bytes)  # read from the board
        response = filter(lambda x: x != '\x00', res)  # remove the null characters to get the response
        if ord(response[0]) == 1:  # if the response isn't an error
            # change MSB to 0 for all received characters except the first and get a list of characters
            char_list = map(lambda x: chr(ord(x) & ~0x80), list(response[1:]))
            # NOTE: having to change the MSB to 0 is a glitch in the raspberry pi, and you shouldn't have to do this!
            return "Command succeeded " + ''.join(char_list)  # convert the char list to a string and returns it
        else:
            return "Error " + str(ord(response[0]))

    def query(self, string):
        # write a command to the board, wait the correct timeout, and read the response
        self.write(string)

        # the read and calibration commands require a longer timeout
        if ((string.upper().startswith("R")) or
                (string.upper().startswith("CAL"))):
            time.sleep(self.long_timeout)
        elif string.upper().startswith("SLEEP"):
            return "sleep mode"
        else:
            time.sleep(self.short_timeout)

        return self.read()

    def close(self):
        self.file_read.close()
        self.file_write.close()


def main():
    device = AtlasI2C()  # creates the I2C port object, specify the address or bus if necessary

    print(">> Atlas Scientific sample code")
    print(">> Any commands entered are passed to the board via I2C except:")
    print(">> Address,xx changes the I2C address the Raspberry Pi communicates with.")
    print(">> Poll,xx.x command continuously polls the board every xx.x seconds")
    print(" where xx.x is longer than the %0.2f second timeout." % AtlasI2C.long_timeout)
    print(" Pressing ctrl-c will stop the polling")

    # main loop
    while True:
        cmd_input = input("Enter command: ")

        # address command lets you change which address the Raspberry Pi will poll
        if cmd_input.upper().startswith("ADDRESS"):
            addr = int(string.split(cmd_input, ',')[1])
            device.set_i2c_address(addr)
            print("I2C address set to " + str(addr))

        # continuous polling command automatically polls the board
        elif cmd_input.upper().startswith("POLL"):
            delaytime = float(string.split(cmd_input, ',')[1])

            # check for polling time being too short, change it to the minimum timeout if too short
            if delaytime < AtlasI2C.long_timeout:
                print("Polling time is shorter than timeout, setting polling time to %0.2f" % AtlasI2C.long_timeout)
                delaytime = AtlasI2C.long_timeout

            # get the information of the board you're polling
            info = string.split(device.query("I"), ",")[1]
            print("Polling %s sensor every %0.2f seconds, press ctrl-c to stop polling" % (info, delaytime))

            try:
                while True:
                    print(device.query("R"))
                    time.sleep(delaytime - AtlasI2C.long_timeout)
            except KeyboardInterrupt:  # catches the ctrl-c command, which breaks the loop above
                print("Continuous polling stopped")

        # if not a special keyword, pass commands straight to board
        else:
            if len(cmd_input) == 0:
                print("Please input valid command.")
            else:
                try:
                    print(device.query(cmd_input))
                except IOError:
                    print("Query failed")


if __name__ == '__main__':
    main()
