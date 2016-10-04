#!/usr/bin/python
# coding=utf-8
#
#  LCD Code used in part from:
# <http://code.activestate.com/recipes/577231-discrete-lcd-controller/>

import RPi.GPIO as GPIO
import smbus
import threading
import os
import sys
import time
import timeit

# Check for root priveileges
if not os.geteuid() == 0:
    sys.exit("Script must be executed as root")

# Change this address for the device being tested
lcd_pin = '0x26'

# Change the number of lines and characters per lines
lcd_x_characters = 16
lcd_y_lines = 2


lcd_string_line = {}
for i in range(1, lcd_y_lines+1):
    lcd_string_line[i] = ''

LCD_WIDTH = lcd_x_characters # Maximum characters per line

LCD_LINE = {}
LCD_LINE[1] = 0x80 # LCD RAM address for the 1st line
LCD_LINE[2] = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE[3] = 0x94 # LCD RAM address for the 3rd line
LCD_LINE[4] = 0xD4 # LCD RAM address for the 4th line

LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - SenLCDding command

LCD_BACKLIGHT = 0x08  # On
LCD_BACKLIGHT_OFF = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

bus = ''

# Setup I2C bus
try:
    if GPIO.RPI_REVISION == 2 or GPIO.RPI_REVISION == 3:
        I2C_bus_number = 1
    else:
        I2C_bus_number = 0
    bus = smbus.SMBus(I2C_bus_number)
except Exception as except_msg:
    print("Could not initialize I2C bus: {}".format(
        except_msg))

I2C_ADDR = int(lcd_pin, 16)


def lcd_backlight(state): # for state, 1 = on, 0 = off
    if state == 1:
        backlight_on = True
        lcd_byte(0x01, LCD_CMD, LCD_BACKLIGHT)
    elif state == 0:
        backlight_on = False
        lcd_byte(0x01, LCD_CMD, LCD_BACKLIGHT_OFF)


def lcd_init():
    """Initialize LCD display"""
    lcd_byte(0x33, LCD_CMD) # 110011 Initialise
    lcd_byte(0x32, LCD_CMD) # 110010 Initialise
    lcd_byte(0x06, LCD_CMD) # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
    lcd_byte(0x28, LCD_CMD) # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD) # 000001 Clear display
    time.sleep(E_DELAY)


def lcd_byte(bits, mode, backlight=LCD_BACKLIGHT):
    """Send byte to data pins"""
    # bits = the data
    # mode = 1 for data
    #        0 for command
    bits_high = mode | (bits & 0xF0) | backlight
    bits_low = mode | ((bits<<4) & 0xF0) | backlight
    # High bits
    bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)
    # Low bits
    bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)


def lcd_toggle_enable(bits):
    """Toggle enable"""
    time.sleep(E_DELAY)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(E_PULSE)
    bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
    time.sleep(E_DELAY)


def lcd_string_write(message, line):
    """Send string to display"""
    message = message.ljust(LCD_WIDTH," ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
      lcd_byte(ord(message[i]),LCD_CHR)


def isRunning():
    return running


def stopController():
    thread_shutdown_timer = timeit.default_timer()
    running = False

lcd_init()
lcd_string_write('   TEST  TEST   ', LCD_LINE[1]) 
lcd_string_write('      TEST      ', LCD_LINE[2])

time.sleep(2)


while 1:
    
    lcd_string_write('   TEST  1   ', LCD_LINE[1])
    time.sleep(1)

    lcd_backlight(0)
    time.sleep(1)

    lcd_string_write('   TEST  2   ', LCD_LINE[1])
    time.sleep(1)

    lcd_backlight(0)
    time.sleep(1)
