# coding=utf-8
#
# on_off_color_kasa_kl125.py - Output for KL125
#
import asyncio
import copy
import random
import time
import traceback
from threading import Event
from threading import Thread

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb

# Measurements
# measurements_dict = {
# }
#
# channels_dict = {
#     0: {}
# }

measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'output_neopixel_rgb_spi',
    'output_name': f"{lazy_gettext('On/Off')}: Neopixel (WS2812) RGB Strip with Raspberry Pi",
    'output_manufacturer': 'Worldsemi',
    'input_library': 'adafruit-circuitpython-neopixel-spi',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'message': 'Control the LEDs of a light strip. This library works with the strip data pin connected to the SPI MOSI pin. Enable SPI with raspi-config, reboot, then connect the RGB strip data pin to GPIO 10 (SPI0 MOSI). This output is best used with Actions to control individual LED color and brightness.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'neopixel_spi', 'adafruit-circuitpython-neopixel-spi==1.0.0')
    ],

    'interfaces': ['SPI'],

    'custom_commands_message':
        'Control each LED of an RGB strip. Color is represented by RGB comma-separated values (red, green, blue). RGB color values can be between 0 (off) and 255 (brightest), e.g. 0, 0, 0 is completely off, 255, 255, 255 is the brightest white, and 125, 0, 0 is a mid-brightness red.',

    'custom_commands': [
        {
            'id': 'led_number',
            'type': 'integer',
            'default_value': 0,
            'name': f"LED Position",
            'phrase': 'Which LED in the strip to change'
        },
        {
            'id': 'led_color',
            'type': 'text',
            'default_value': '10, 0, 0',
            'name': f"RGB Color",
            'phrase': 'The color (e.g 10, 0 0)'
        },
        {
            'id': 'set_led',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Set')
        }
    ],

    'custom_options': [
        {
            'id': 'number_leds',
            'type': 'integer',
            'default_value': 1,
            'name': f"Number of LEDs",
            'phrase': 'How many LEDs in the string?'
        },
        {
            'id': 'on_color',
            'type': 'text',
            'default_value': "30, 30, 30",
            'name': f"On Color",
            'phrase': 'The Color when turning on, in RGB format (red, green, blue), 0 - 255 each.'
        },
    ],

    'custom_channel_options': [
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state when Mycodo starts'
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': 'Set the state when Mycodo shuts down'
        },
        {
            'id': 'trigger_functions_startup',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Trigger Functions at Startup'),
            'phrase': 'Whether to trigger functions when the output switches at startup'
        },
        {
            'id': 'command_force',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Force Command'),
            'phrase': 'Always send the command if instructed, regardless of the current state'
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates Neopixels."""

    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.rgb = None

        self.number_leds = None
        self.on_color = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        import board
        import neopixel_spi

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            red = int(self.on_color.split(",")[0])
            green = int(self.on_color.split(",")[1])
            blue = int(self.on_color.split(",")[2])
            self.on_color = (red, green, blue)
        except:
            self.on_color = (30, 30, 30)
            self.logger.error(f"Could not parse On Color: {self.on_color}")

        try:
            self.rgb = neopixel_spi.NeoPixel_SPI(board.SPI(), 7, auto_write=False, bit0=0b10000000)
            self.output_setup = True

            if self.options_channels['state_startup'][0] == 1:
                for i in range(self.number_leds):
                    self.rgb[i] = (10, 0, 0)
                    self.rgb.show()
                    time.sleep(0.01)
                for i in range(self.number_leds):
                    self.rgb[i] = (0, 10, 0)
                    self.rgb.show()
                    time.sleep(0.01)
                for i in range(self.number_leds):
                    self.rgb[i] = (0, 0, 10)
                    self.rgb.show()
                    time.sleep(0.01)
                for i in range(self.number_leds):
                    self.rgb[i] = self.on_color
                    self.rgb.show()
                    time.sleep(0.01)
                self.output_states[0] = True
            if self.options_channels['state_startup'][0] == 0:
                for i in range(self.number_leds):
                    self.rgb[i] = 0
                    self.rgb.show()
                    time.sleep(0.01)
                self.output_states[0] = False
        except Exception as err:
            self.logger.error(f"Setting up Output: {err}")

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        try:
            if state == 'on':
                for i in range(self.number_leds):
                    self.rgb[i] = self.on_color
                self.rgb.show()
                self.output_states[0] = True
            elif state == 'off':
                for i in range(self.number_leds):
                    self.rgb[i] = (0, 0, 0)
                self.rgb.show()
                self.output_states[0] = False
        except Exception as err:
            self.logger.exception(f"State change error: {err}")

    def is_on(self, output_channel=0):
        if self.is_setup():
            return self.output_states[0]

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 1:
                self.output_switch('on')
            elif self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
        self.running = False

    def change_led(self, number, color):
        self.rgb[number] = (color[0], color[1], color[2])
        self.rgb.show()

    def set_led(self, args_dict):
        if 'led_number' not in args_dict:
            self.logger.error("Cannot set without led number")
            return

        if 'led_color' not in args_dict:
            self.logger.error("Cannot set without led color")
            return

        try:
            red = int(args_dict['led_color'].split(",")[0])
            green = int(args_dict['led_color'].split(",")[1])
            blue = int(args_dict['led_color'].split(",")[2])
        except:
            msg = f"Could not parse Pixel Color: {args_dict['led_color']}"
            self.logger.error(msg)
            return msg

        self.change_led(args_dict['led_number'], (red, green, blue))

        return f"Set Pixel {args_dict['led_number']} to color {args_dict['led_color']}"
