# coding=utf-8
import logging
import time

import adafruit_ssd1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from adafruit_extended_bus import ExtendedI2C

logger = logging.getLogger("mycodo.device.lcd_pioled_circuitpython")


class LCD_Pioled_Circuitpython:
    """Output to the PiOLED I2C LCD"""
    def __init__(self, lcd_dev=None, lcd_settings_dict=None):
        if lcd_dev:
            self.logger = logging.getLogger(
                "{}_{}".format(__name__, lcd_dev.unique_id.split('-')[0]))
            self.interface = lcd_dev.interface
            self.lcd_x_characters = lcd_dev.x_characters
            self.lcd_type = lcd_dev.lcd_type
            # I2C
            self.i2c_address = int(lcd_dev.location, 16)
            self.i2c_bus = lcd_dev.i2c_bus
            # SPI
            self.spi_bus = lcd_dev.spi_bus
            self.spi_device = lcd_dev.spi_device
            self.pin_dc = lcd_dev.pin_dc
            self.pin_reset = lcd_dev.pin_reset
            self.pin_cs = lcd_dev.pin_cs
        elif lcd_settings_dict:
            self.logger = logging.getLogger(
                "{}_{}".format(__name__, lcd_settings_dict["unique_id"].split('-')[0]))
            self.interface = lcd_settings_dict["interface"]
            self.lcd_x_characters = lcd_settings_dict["x_characters"]
            self.lcd_type = lcd_settings_dict["lcd_type"]
            # I2C
            self.i2c_address = int(lcd_settings_dict["i2c_address"], 16)
            self.i2c_bus = lcd_settings_dict["i2c_bus"]
            # SPI
            self.spi_bus = lcd_settings_dict["spi_bus"]
            self.spi_device = lcd_settings_dict["spi_device"]
            self.pin_dc = lcd_settings_dict["pin_dc"]
            self.pin_reset = lcd_settings_dict["pin_reset"]
            self.pin_cs = lcd_settings_dict["pin_cs"]

        self.disp = None

        if self.interface == 'I2C':
            if self.lcd_type == '128x32_pioled_circuit_python':
                self.disp = adafruit_ssd1306.SSD1306_I2C(
                    128, 32,
                    ExtendedI2C(self.i2c_bus),
                    addr=int(str(self.i2c_address), 16))
            elif self.lcd_type == '128x64_pioled_circuit_python':
                self.disp = adafruit_ssd1306.SSD1306_I2C(
                    128, 64,
                    ExtendedI2C(self.i2c_bus),
                    addr=int(str(self.i2c_address), 16))

        elif self.interface == 'SPI':
            if self.lcd_type == '128x32_pioled_circuit_python':
                import Adafruit_GPIO.SPI as SPI
                self.disp = adafruit_ssd1306.SSD1306_SPI(
                    128, 32,
                    spi=SPI.SpiDev(self.spi_bus, self.spi_device),
                    dc=self.pin_dc,
                    reset=self.pin_reset,
                    cs=self.pin_cs)
            elif self.lcd_type == '128x64_pioled_circuit_python':
                import Adafruit_GPIO.SPI as SPI
                self.disp = adafruit_ssd1306.SSD1306_SPI(
                    128, 64,
                    spi=SPI.SpiDev(self.spi_bus, self.spi_device),
                    dc=self.pin_dc,
                    reset=self.pin_reset,
                    cs=self.pin_cs)

        if not self.disp:
            self.logger.error("Unable to set up display. Check the LCD settings.")

    def lcd_init(self):
        """ Initialize LCD display """
        try:
            self.disp.fill(0)
            self.disp.show()
        except Exception as err:
            self.logger.error(
                "Could not initialize LCD. Check your configuration and wiring. Error: {err}".format(err=err))

    def lcd_write_lines(self,
                        message_line_1,
                        message_line_2,
                        message_line_3,
                        message_line_4,
                        message_line_5=None,
                        message_line_6=None,
                        message_line_7=None,
                        message_line_8=None):
        """ Send strings to display """
        x = 0
        top = -2  # padding
        font = ImageFont.load_default()

        image = Image.new('1', (self.disp.width, self.disp.height))

        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.disp.width, self.disp.height), outline=0, fill=0)

        draw.text((x, top), message_line_1, font=font, fill=255)
        draw.text((x, top + 8), message_line_2, font=font, fill=255)
        draw.text((x, top + 16), message_line_3, font=font, fill=255)
        draw.text((x, top + 24), message_line_4, font=font, fill=255)

        if message_line_5 is not None:
            draw.text((x, top + 32), message_line_5, font=font, fill=255)
        if message_line_6 is not None:
            draw.text((x, top + 40), message_line_6, font=font, fill=255)
        if message_line_7 is not None:
            draw.text((x, top + 48), message_line_7, font=font, fill=255)
        if message_line_8 is not None:
            draw.text((x, top + 54), message_line_8, font=font, fill=255)

        self.disp.image(image)
        self.disp.show()
        time.sleep(0.1)

    def lcd_backlight(self, state):
        """ backlight not supported """
        pass
