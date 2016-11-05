# coding=utf-8
import io         # used to create file streams
import fcntl      # used to access I2C parameters like addresses
import logging
import time       # used for sleep delay and timestamps
from .base_sensor import AbstractSensor


class AtlasPT1000Sensor(AbstractSensor):
    """ A sensor support class that monitors the PT1000's temperature """

    def __init__(self, address, bus):
        super(AtlasPT1000Sensor, self).__init__()
        self.short_timeout = 0.5
        self.long_timeout = 1.5
        self._temperature = 0.0
        self.address = address
        self.running = True
        self.I2C_bus_number = bus
        self.file_read = None
        self.file_write = None

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "temperature: {temp}".format(
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ Atlas_PT1000Sensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.3f}'.format(self._temperature)))

    def get_measurement(self):
        """ Gets the Atlas PT1000's temperature in Celsius """
        self.file_read = io.open("/dev/i2c-" + str(self.I2C_bus_number), "rb", buffering=0)
        self.file_write = io.open("/dev/i2c-" + str(self.I2C_bus_number), "wb", buffering=0)
        self.set_i2c_address(self.address)
        temperature_string = self.query("R")
        self.close()
        # the temperature return string, if successfully read, will be
        # "Command succeeded X.XX", where X denotes the temperature
        if temperature_string[:17] != 'Command succeeded':
            raise Exception("Sensor read failed")
        else:
            return float(temperature_string[18:])

    @property
    def temperature(self):
        """ CPU temperature in celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def read(self):
        """
        Takes a reading from the PT1000 and updates the self._temperature value

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            return  # success - no errors
        except Exception as e:
            logging.error("Unknown error in {cls}.get_measurement(): {err}".format(cls=type(self).__name__, err=e))
        return 1

    def set_i2c_address(self, address):
        # set the I2C communications to the slave specified by the address
        # The commands for I2C dev using the ioctl functions are specified in
        # the i2c-dev.h file from i2c-tools
        i2c_slave = 0x703
        fcntl.ioctl(self.file_read, i2c_slave, address)
        fcntl.ioctl(self.file_write, i2c_slave, address)

    def write(self, cmd):
        # appends the null character and sends the string over I2C
        cmd += "\00"
        self.file_write.write(cmd)

    def read_pt1000(self, num_of_bytes=31):
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
        return self.read_pt1000()

    def close(self):
        self.file_read.close()
        self.file_write.close()
