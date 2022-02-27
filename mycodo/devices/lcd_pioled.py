# coding=utf-8
import logging
import time

import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

logger = logging.getLogger("mycodo.device.lcd_pioled")


class LCD_Pioled:
    """Output to the PiOLED I2C LCD."""

    def __init__(self, lcd_dev):
        self.logger = logging.getLogger(
            "{}_{}".format(__name__, lcd_dev.unique_id.split('-')[0]))

        self.disp = None
        self.interface = lcd_dev.interface
        self.lcd_x_characters = lcd_dev.x_characters
        self.lcd_y_lines = lcd_dev.y_lines
        self.lcd_type = lcd_dev.lcd_type

        if self.interface == 'I2C':
            if self.lcd_type == '128x32_pioled':
                self.disp = Adafruit_SSD1306.SSD1306_128_32(
                    rst=lcd_dev.pin_reset,
                    i2c_address=int(str(lcd_dev.location), 16),
                    i2c_bus=lcd_dev.i2c_bus)
            elif self.lcd_type == '128x64_pioled':
                self.disp = Adafruit_SSD1306.SSD1306_128_64(
                    rst=lcd_dev.pin_reset,
                    i2c_address=int(str(lcd_dev.location), 16),
                    i2c_bus=lcd_dev.i2c_bus)

        elif self.interface == 'SPI':
            if self.lcd_type == '128x32_pioled':
                import Adafruit_GPIO.SPI as SPI
                self.disp = Adafruit_SSD1306.SSD1306_128_32(
                    rst=lcd_dev.pin_reset,
                    dc=lcd_dev.pin_dc,
                    spi=SPI.SpiDev(lcd_dev.spi_bus, lcd_dev.spi_device))
            elif self.lcd_type == '128x64_pioled':
                import Adafruit_GPIO.SPI as SPI
                self.disp = Adafruit_SSD1306.SSD1306_128_64(
                    rst=lcd_dev.pin_reset,
                    dc=lcd_dev.pin_dc,
                    spi=SPI.SpiDev(lcd_dev.spi_bus, lcd_dev.spi_device))

        if not self.disp:
            self.logger.error("Unable to set up display. Check the LCD settings.")
        else:
            self.disp.begin()

    def lcd_init(self):
        """Initialize LCD display."""
        try:
            self.disp.clear()
            self.disp.display()
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
        """Send strings to display."""
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
        self.disp.display()
        time.sleep(0.1)

    def lcd_backlight(self, state):
        """backlight not supported."""
        pass
