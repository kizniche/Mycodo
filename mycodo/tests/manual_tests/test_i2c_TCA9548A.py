#!/usr/bin/python
# coding=utf-8
#
# Select address and channel of TCA9548A I2C multiplexer
# I2C Address: 0xYY, where YY can be 70 through 77
# Multiplexer Channel: 1 - 8
# sudo ./multiplexer_channel.py ADDRESS CHANNEL
# Example: sudo ./multiplexer_channel.py 70 1

import os
import sys
import time
import argparse

from smbus2 import SMBus

channel_byte = {
    0: 0b00000001,
    1: 0b00000010,
    2: 0b00000100,
    3: 0b00001000,
    4: 0b00010000,
    5: 0b00100000,
    6: 0b01000000,
    7: 0b10000000
}


def I2C_setup(i2c_bus, i2c_address, i2c_channel_setup):
    address = 0x70 + i2c_address % 10
    bus = SMBus(i2c_bus)
    bus.write_byte(address, i2c_channel_setup)
    time.sleep(0.1)
    print("TCA9548A I2C channel status:{}".format(bin(bus.read_byte(address))))


def menu():
    parser = argparse.ArgumentParser(description='Select channel of TCA9548A '
                                                 'I2C multiplexer')
    parser.add_argument('-a', '--address', metavar='ADDRESS', type=int,
                        help="The I2C address of the multiplexer (only last "
                             "two characters, for instance, if 0x70, enter '70'.",
                        required=True)
    parser.add_argument('-b', '--bus', metavar='BUS', type=int,
                        help="The I2C bus of the multiplexer.",
                        required=True)
    parser.add_argument('-c', '--channel', metavar='CHANNEL', type=int,
                        help="Which channel to switch to (Options: 0-7).",
                        required=True)

    args = parser.parse_args()

    I2C_setup(args.bus, args.address, channel_byte[args.channel])


if __name__ == "__main__":
    if not os.geteuid() == 0:
        print("Error: Script must be executed as root.\n")
        sys.exit(1)
    menu()
