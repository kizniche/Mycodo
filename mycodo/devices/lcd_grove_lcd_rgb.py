# coding=utf-8
import logging
import time

from smbus2 import SMBus
from grove_rgb_lcd import *

logger = logging.getLogger("mycodo.device.lcd_grove_lcd_rgb")

class LCD_Grove_LCD_RGB:
    """Output to a Grove I2C LCD RGB display (16x2 LCD with RGB or monochrome backlight)"""

    def __init__(self, lcd_dev):
        self.logger = logging.getLogger(
            "{}_{}".format(__name__, lcd_dev.unique_id.split('-')[0]))

        self.lcd_initialized = False
        self.lcd_is_on = False

        self.i2c_address = int(lcd_dev.location, 16)
        self.i2c_bus = lcd_dev.i2c_bus
        self.lcd_x_characters = lcd_dev.x_characters
        self.lcd_y_lines = lcd_dev.y_lines

        self.LCD_WIDTH = self.lcd_x_characters  # Max characters per line
        self.I2C_ADDR = self.i2c_address

    def lcd_init(self):
        """ Initialize LCD display """
        setRGB(255,255,255)

    def lcd_backlight(self, state):
        """ Turn the backlight on or off """
        if state:
            setRGB(255,255,255)
        else:
            setRGB(0,0,0)

    def lcd_byte(self, bits, mode, backlight=None):
        """ Send byte to data pins """
        pass

    def lcd_toggle_enable(self, bits):
        """ Toggle enable """
        pass

    def lcd_string_write(self, message, line):
        """ Send strings to display """
        pass

    def lcd_write_lines(self, line_1, line_2, line_3, line_4):
        msg = ""
        if line_1:
            msg += line_1
        msg += "\n"
        if line_2:
            msg += line_2
        msg += "\n"
        if line_3:
            msg += line_3
        msg += "\n"
        if line_4:
            msg += line_4
        setText(msg)
