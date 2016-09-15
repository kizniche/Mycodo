# coding=utf-8

import io         # used to create file streams
import fcntl      # used to access I2C parameters like addresses
import time       # used for sleep delay and timestamps
import string     # helps parse strings
import RPi.GPIO as GPIO


class Atlas_PT1000(object):
    def __init__(self, address, bus):
        self.long_timeout = 1.5
        self._temperature = 0
        self.address = address
        self.running = True
        self.I2C_bus_number = bus

    def read_pt1000(self):
        try:
            self.file_read = io.open("/dev/i2c-"+str(self.I2C_bus_number), "rb", buffering=0)
            self.file_write = io.open("/dev/i2c-"+str(self.I2C_bus_number), "wb", buffering=0)
            self.set_i2c_address(self.address)
            temperature_string = self.query("R")
            self.close()
            # the temperature return string, if successfully read, will be
            # "Command succeeded X.XX", where X denotes the temperature
            if temperature_string[:17] != 'Command succeeded':
                return 1
            else:
                self._temperature = float(temperature_string[18:])
        except Exception as msg:
            print(msg)
            return 1

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
        res = self.file_read.read(num_of_bytes)         # read from the board
        response = filter(lambda x: x != '\x00', res)     # remove the null characters to get the response
        if ord(response[0]) == 1:             # if the response isn't an error
            # change MSB to 0 for all received characters except the first and get a list of characters
            char_list = map(lambda x: chr(ord(x) & ~0x80), list(response[1:]))
            # NOTE: having to change the MSB to 0 is a glitch in the raspberry pi, and you shouldn't have to do this!
            return "Command succeeded " + ''.join(char_list)     # convert the char list to a string and returns it
        else:
            return "Error " + str(ord(response[0]))

    def query(self, string):
        # write a command to the board, wait the correct timeout, and read the response
        self.write(string)

        # the read and calibration commands require a longer timeout
        if((string.upper().startswith("R")) or
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

    @property
    def temperature(self):
        return self._temperature

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature information.
        """
        if self.read_pt1000():
            return None
        response = {
            'temperature': float("{0:.3f}".format(self.temperature))
        }
        return response

    def stopSensor(self):
        self.running = False


if __name__ == "__main__":
    if GPIO.RPI_INFO['P1_REVISION'] in [2, 3]:
        I2C_bus_number = 1
    else:
        I2C_bus_number = 0
    pt1000 = Atlas_PT1000(102, I2C_bus_number)

    for measurement in pt1000:
        print("Temperature: {}".format(measurement['temperature']))
        time.sleep(3)
