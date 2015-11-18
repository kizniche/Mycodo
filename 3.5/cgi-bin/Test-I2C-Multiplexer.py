#!/usr/bin/python

# Select channel of TCA9548A I2C multiplexer
# Example: sudo ./multiplexer_channel.py 1

import RPi.GPIO as GPIO
import smbus
import sys
import time

I2C_address = 0x70
if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
    I2C_bus_number = 1
else:
    I2C_bus_number = 0

def I2C_setup(i2c_channel_setup):
	bus = smbus.SMBus(I2C_bus_number)
	bus.write_byte(I2C_address,i2c_channel_setup)
	time.sleep(0.1)
	print "TCA9548A I2C channel status:", bin(bus.read_byte(I2C_address))

I2C_setup(int(sys.argv[1]))
