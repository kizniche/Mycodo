# coding=utf-8
#
# Support for the Grove - LCD RGB Backlight (https://wiki.seeedstudio.com/Grove-LCD_RGB_Backlight/)
#
# The GrovePi connects the Raspberry Pi and Grove sensors.  You can learn more about GrovePi here:  http://www.dexterindustries.com/GrovePi
#
# Configuration:
#   The I2C default address of the display is 0x3e
#   The I2C default address of the backlight is 0x62
#
import logging
import time
from smbus2 import SMBus

class LCD_Grove_LCD_RGB:
    """Output to a Grove I2C LCD RGB display (16x2 LCD with RGB or monochrome backlight)"""
    def __init__(self, lcd_dev=None, lcd_settings_dict=None):
        self.lcd_initialized = False
        self.lcd_is_on = False

        if lcd_dev:
            self.logger = logging.getLogger(
                "{}_{}".format(__name__, lcd_dev.unique_id.split('-')[0]))
            self.i2c_address = int(lcd_dev.location, 16)
            self.i2c_bus = lcd_dev.i2c_bus
            self.location_backlight = int(lcd_dev.location_backlight, 16)
            self.lcd_x_characters = lcd_dev.x_characters
            self.lcd_y_lines = lcd_dev.y_lines
            self.red = 255
            self.green = 255
            self.blue = 255
        elif lcd_settings_dict:
            self.logger = logging.getLogger(
                "{}_{}".format(__name__, lcd_settings_dict["unique_id"].split('-')[0]))
            self.i2c_address = int(lcd_settings_dict["i2c_address"], 16)
            self.i2c_bus = lcd_settings_dict["i2c_bus"]
            self.location_backlight = int(lcd_settings_dict["location_backlight"], 16)
            self.lcd_x_characters = lcd_settings_dict["x_characters"]
            self.lcd_y_lines = lcd_settings_dict["y_lines"]
            self.red = lcd_settings_dict["red"]
            self.green = lcd_settings_dict["green"]
            self.blue = lcd_settings_dict["blue"]

        self.logger = logging.getLogger(
            "{}_{}".format(__name__, lcd_dev.unique_id.split('-')[0]))

        self.i2c_address_backlight = self.location_backlight
        # self.i2c_address_backlight = 0x62

        self.LCD_WIDTH = self.lcd_x_characters  # Max characters per line
        self.I2C_ADDR = self.i2c_address

        # Commands, etc
        self.LCD_CLEARDISPLAY = 0x01
        self.LCD_RETURNHOME = 0x02
        self.LCD_ENTRYMODESET = 0x04
        self.LCD_DISPLAYCONTROL = 0x08
        self.LCD_CURSORSHIFT = 0x10
        self.LCD_FUNCTIONSET = 0x20
        self.LCD_SETCGRAMADDR = 0x40
        self.LCD_SETDDRAMADDR = 0x80

        # flags for function set
        self.LCD_8BITMODE = 0x10
        self.LCD_4BITMODE = 0x00
        self.LCD_2LINE = 0x08
        self.LCD_1LINE = 0x00
        self.LCD_5x10DOTS = 0x04
        self.LCD_5x8DOTS = 0x00

        # flags for display on/off control
        self.LCD_DISPLAYON = 0x04
        self.LCD_DISPLAYOFF = 0x00
        self.LCD_CURSORON = 0x02
        self.LCD_CURSOROFF = 0x00
        self.LCD_BLINKON = 0x01
        self.LCD_BLINKOFF = 0x00

        # flags for display entry mode
        self.LCD_ENTRYRIGHT = 0x00
        self.LCD_ENTRYLEFT = 0x02
        self.LCD_ENTRYSHIFTINCREMENT = 0x01
        self.LCD_ENTRYSHIFTDECREMENT = 0x00

        # RGB backlight registers
        self.REG_MODE1 = 0x00
        self.REG_MODE2 = 0x01
        self.REG_OUTPUT = 0x08

        # Setup I2C bus
        try:
            self.bus = SMBus(self.i2c_bus)
        except Exception as except_msg:
            self.logger.exception(
                "Could not initialize I2C bus: {err}".format(
                    err=except_msg))

        # set configuration
        displayConfig = self.LCD_FUNCTIONSET
        if self.lcd_y_lines == 2:
            displayConfig = displayConfig | self.LCD_2LINE
        self.writeCommand(displayConfig)
        time.sleep(0.005)
        self.writeCommand(displayConfig)
        time.sleep(0.001)
        self.writeCommand(displayConfig)
        self.writeCommand(displayConfig)
        # set state
        displayState = self.LCD_DISPLAYCONTROL | self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF
        self.writeCommand(displayState)

        self.clearDisplay()

        # set the entry mode
        entryMode = self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT
        self.writeCommand(entryMode)

        # Initialize the backlight
        self.bus.write_byte_data(self.i2c_address_backlight, self.REG_MODE1, 0)
        # set LEDs controllable by both PWM and GRPPWM registers
        self.bus.write_byte_data(self.i2c_address_backlight, self.REG_OUTPUT, 0xff)
        # set MODE2 values
        # 0010 0000 -> 0x20  (DMBLNK to 1, ie blinky mode)
        self.bus.write_byte_data(self.i2c_address_backlight, self.REG_MODE2, 0x20)
        self.setRGB(self.red, self.green, self.blue)
        
    def writeCommand(self, cmd):
        self.bus.write_byte_data(self.i2c_address,0x80,cmd)

    def writeData(self, data):
        self.bus.write_byte_data(self.i2c_address,0x40,data)

    def setRGB(self, r, g, b):
        self.bus.write_byte_data(self.i2c_address_backlight, 4, r)
        self.bus.write_byte_data(self.i2c_address_backlight, 3, g)
        self.bus.write_byte_data(self.i2c_address_backlight, 2, b)

    def clearDisplay(self):
        self.writeCommand(self.LCD_CLEARDISPLAY) # clear display
        time.sleep(0.002)

    def setCursor(self, col, row):
        if row == 0:
            location = col | 0x80
        else:
            location = col | 0xc0
        self.writeCommand(location)
        time.sleep(0.001)

    def setText(self, text):
        self.clearDisplay()
        self.setCursor(0, 0)
        count = 0
        row = 0
        for c in text:
            if c == '\n' or count == 16:
                count = 0
                row += 1
                if row == 2:
                    break
                self.writeCommand(0xc0)
                if c == '\n':
                    continue
            count += 1
            self.writeData(ord(c))

    def lcd_init(self):
        """Clear LCD display."""
        self.clearDisplay()

    def lcd_backlight(self, state):
        """Turn the backlight on or off."""
        if state:
            self.setRGB(self.red, self.green, self.blue)
        else:
            self.setRGB(0, 0, 0)

    def display_backlight_color(self, color_tuple):
        try:
            tuple_colors = color_tuple.split(",")
            self.red = int(tuple_colors[0])
            self.green = int(tuple_colors[1])
            self.blue = int(tuple_colors[2])
            self.setRGB(self.red, self.green, self.blue)
        except:
            self.logger.error("Could not set color. Invalid color string: '{}'".format(color_tuple))

    def lcd_byte(self, bits, mode, backlight=None):
        """Send byte to data pins."""
        # bits = the data
        # mode = 1 for data
        #        0 for command
        if mode == 0:
            self.writeCommand(bits)
        else:
            self.writeData(bits)

    def lcd_toggle_enable(self, bits):
        """Toggle enable"""
        pass

    def lcd_string_write(self, message, line):
        """Send strings to display."""
        self.setCursor(0, line)
        for c in message:
            self.writeData(ord(c))

    def lcd_write_lines(self, line_1, line_2, line_3, line_4):
        msg = ""
        if line_1 is not None:
            msg += line_1
        msg += "\n"
        if line_2 is not None:
            msg += line_2
        msg += "\n"
        if line_3 is not None:
            msg += line_3
        msg += "\n"
        if line_4 is not None:
            msg += line_4
        self.setText(msg)
