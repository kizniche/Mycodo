# coding=utf-8
import logging
import time

from smbus2 import SMBus

logger = logging.getLogger("mycodo.device.lcd_generic")


class LCD_Generic:
    """Output to a generic I2C LCD (16x2 and 20x4 LCD with I2C backpack)"""
    def __init__(self, lcd_dev=None, lcd_settings_dict=None):
        self.lcd_initialized = False
        self.lcd_is_on = False

        if lcd_dev:
            self.logger = logging.getLogger(
                "{}_{}".format(__name__, lcd_dev.unique_id.split('-')[0]))
            self.i2c_address = int(lcd_dev.location, 16)
            self.i2c_bus = lcd_dev.i2c_bus
            self.lcd_x_characters = lcd_dev.x_characters
            self.lcd_y_lines = lcd_dev.y_lines
        elif lcd_settings_dict:
            self.logger = logging.getLogger(
                "{}_{}".format(__name__, lcd_settings_dict["unique_id"].split('-')[0]))
            self.i2c_address = int(lcd_settings_dict["i2c_address"], 16)
            self.i2c_bus = lcd_settings_dict["i2c_bus"]
            self.lcd_x_characters = lcd_settings_dict["x_characters"]
            self.lcd_y_lines = lcd_settings_dict["y_lines"]

        self.LCD_LINE = {
            1: 0x80,
            2: 0xC0,
            3: 0x94,
            4: 0xD4
        }

        self.LCD_CHR = 1  # Mode - Sending data
        self.LCD_CMD = 0  # Mode - SenLCDding command

        self.LCD_BACKLIGHT = 0x08  # On
        self.LCD_BACKLIGHT_OFF = 0x00  # Off

        self.ENABLE = 0b00000100  # Enable bit

        # Timing constants
        self.E_PULSE = 0.0005
        self.E_DELAY = 0.0005

        self.LCD_WIDTH = self.lcd_x_characters  # Max characters per line

        # Setup I2C bus
        try:
            self.bus = SMBus(self.i2c_bus)
        except Exception as except_msg:
            self.logger.exception(
                "Could not initialize I2C bus: {err}".format(
                    err=except_msg))

        self.I2C_ADDR = self.i2c_address

    def lcd_init(self):
        """Initialize LCD display."""
        try:
            self.lcd_byte(0x33, self.LCD_CMD)  # 110011 Initialise
            self.lcd_byte(0x32, self.LCD_CMD)  # 110010 Initialise
            self.lcd_byte(0x06, self.LCD_CMD)  # 000110 Cursor move direction
            self.lcd_byte(0x0C, self.LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
            self.lcd_byte(0x28, self.LCD_CMD)  # 101000 Data length, number of lines, font size
            self.lcd_byte(0x01, self.LCD_CMD)  # 000001 Clear display
            time.sleep(self.E_DELAY)
        except Exception as err:
            self.logger.error(
                "Could not initialize LCD. Check your configuration and wiring. Error: {err}".format(err=err))

    def lcd_backlight(self, state):
        """Turn the backlight on or off."""
        if state:
            self.lcd_byte(0x01, self.LCD_CMD, self.LCD_BACKLIGHT)
        else:
            self.lcd_byte(0x01, self.LCD_CMD, self.LCD_BACKLIGHT_OFF)

    def lcd_byte(self, bits, mode, backlight=None):
        """Send byte to data pins."""
        if backlight is None:
            backlight = self.LCD_BACKLIGHT
        # bits = the data
        # mode = 1 for data
        #        0 for command
        bits_high = mode | (bits & 0xF0) | backlight
        bits_low = mode | ((bits << 4) & 0xF0) | backlight
        # High bits
        self.bus.write_byte(self.I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)
        # Low bits
        self.bus.write_byte(self.I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)

    def lcd_toggle_enable(self, bits):
        """Toggle enable"""
        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.I2C_ADDR, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.I2C_ADDR, (bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)

    def lcd_string_write(self, message, line):
        """Send strings to display."""
        line_write = self.LCD_LINE[line]
        message = message.ljust(self.LCD_WIDTH, " ")
        self.lcd_byte(line_write, self.LCD_CMD)
        for i in range(self.LCD_WIDTH):
            self.lcd_byte(ord(message[i]), self.LCD_CHR)

    def lcd_write_lines(self, line_1, line_2, line_3, line_4):
        if line_1 is not None:
            self.lcd_string_write(line_1, 1)
        if line_2 is not None:
            self.lcd_string_write(line_2, 2)
        if line_3 is not None:
            self.lcd_string_write(line_3, 3)
        if line_4 is not None:
            self.lcd_string_write(line_4, 4)
