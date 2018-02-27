#!/usr/bin/python
# coding=utf-8

import os
import sys
import time
import io
import fcntl

I2C_SLAVE = 0x0703
I2C_BUS = 1
AM2315_ADDR = 0x5c
CMD_READ = '\x03'

AM2315_READREG = 0x03


class i2c(object):
    def __init__(self, device, bus):
        self.fr = io.open('/dev/i2c-' + str(bus), 'rb', buffering=0)
        self.fw = io.open('/dev/i2c-' + str(bus), 'wb', buffering=0)
        fcntl.ioctl(self.fr, I2C_SLAVE, device)
        fcntl.ioctl(self.fw, I2C_SLAVE, device)

    def writeI2C(self, wbytes):
        self.fw.write(wbytes)

    def readI2C(self, read_bytes):
        try:
            return self.fr.read(read_bytes)
        except IOError:
            return 0

    def closeI2C(self):
        self.fw.close()
        self.fr.close()


if __name__ == '__main__':
    if not os.geteuid() == 0:
        print('Error: Script must be executed as root.\n')
        sys.exit(1)

    while True:
        am = i2c(AM2315_ADDR, I2C_BUS)
        try:
            am.writeI2C(CMD_READ)  # Send a read command to wake up
        except IOError:
            pass  # Wake generates ioError, ignore that error

        time.sleep(0.1)

        # send read command starting at zero (0) (0x00) and get four (4) (0x04)
        # registers. Which returns 8 bytes total.
        try:
            am.writeI2C(CMD_READ + '\x00\x04')
        except IOError:
            print('I/O Error 0')

        time.sleep(0.01)

        # read 8 bytes into data. Just read it. Normal smbus has some protocol
        # for waiting that the AM2315 doesnt follow.
        data = am.readI2C(8)
        am.closeI2C()

        if not data:
            print('I/O Error 1')
        else:
            new_data = []
            for i in data:
                new_data.append(ord(i))

            if new_data[0] != AM2315_READREG or new_data[1] != 4:
                print('Fail')
            else:
                humidity = (new_data[2] * 256 + new_data[3]) / 10.0
                temperature = ((new_data[4] & 0x7F) * 256 + new_data[5]) / 10.0
                if new_data[4] >> 7:
                    temperature = -temperature
                print('AM2315: {} %, {} C'.format(humidity, temperature))

        time.sleep(7)
