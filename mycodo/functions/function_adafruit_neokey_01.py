# coding=utf-8
#
#  function_adafruit_neokey_01.py - Function to utilize the Adafruit Neokey
#
#  Copyright (C) 2015-2023 Kyle T. Gabriel <mycodo@kylegabriel.com>
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com
#
import threading
import time
import traceback

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import CustomController
from mycodo.databases.models import FunctionChannel
from mycodo.functions.base_function import AbstractFunction
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import write_influxdb_value

# Measurements
measurements_dict = {
    0: {
        'measurement': 'boolean',
        'unit': 'bool',
        'name': 'Key 1'
    },
    1: {
        'measurement': 'boolean',
        'unit': 'bool',
        'name': 'Key 2'
    },
    2: {
        'measurement': 'boolean',
        'unit': 'bool',
        'name': 'Key 3'
    },
    3: {
        'measurement': 'boolean',
        'unit': 'bool',
        'name': 'Key 4'
    }
}

channels_dict = {
    0: {
        'name': 'Key 1',
        'measurements': [0]
    },
    1: {
        'name': 'Key 2',
        'measurements': [1]
    },
    2: {
        'name': 'Key 3',
        'measurements': [2]
    },
    3: {
        'name': 'Key 4',
        'measurements': [3]
    }
}


def execute_at_modification(
        messages,
        mod_function,
        request_form,
        custom_options_dict_presave,
        custom_options_channels_dict_presave,
        custom_options_dict_postsave,
        custom_options_channels_dict_postsave):
    """
    This function allows you to view and modify the output and channel settings when the user clicks
    save on the user interface. Both the output and channel settings are passed to this function, as
    dictionaries. Additionally, both the pre-saved and post-saved options are available, as it's
    sometimes useful to know what settings changed and from what values. You can modify the post-saved
    options and these will be stored in the database.
    :param mod_function: The post-saved output database entry, minus the custom_options settings
    :param request_form: The requests.form object the user submitted
    :param custom_options_dict_presave: dict of pre-saved custom output options
    :param custom_options_channels_dict_presave: dict of pre-saved custom output channel options
    :param custom_options_dict_postsave: dict of post-saved custom output options
    :param custom_options_channels_dict_postsave: dict of post-saved custom output channel options
    :return:
    """
    page_refresh = False

    try:
        pass  # TODO: Add check for properly-formatted Action ID strings
    except Exception:
        messages["error"].append("execute_at_modification() Error: {}".format(traceback.print_exc()))

    return (messages,
            mod_function,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave,
            page_refresh)


FUNCTION_INFORMATION = {
    'function_name_unique': 'function_adafruit_neokey_01',
    'function_name': 'Neokey 4x1 Neopixel Keyboard (Execute Actions)',
    'function_name_short': 'Neokey 4x1 Neopixel Keyboard',
    'function_manufacturer': 'Adafruit',
    'function_library': 'adafruit-circuitpython-neokey',
    'execute_at_modification': execute_at_modification,
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,

    'message': 'This Function executes actions when a key is pressed. Add actions at the bottom of this module, then enter one or more short action IDs for each key, separated by commas. The Action ID is found next to the Action (for example, the Action "[Action 0559689e] Controller: Activate" has an Action ID of 0559689e. When entering Action ID(s), separate multiple IDs by commas (for example, "asdf1234" or "asdf1234,qwer5678,zxcv0987"). Actions will be executed in the order they are entered in the text string. Enter Action IDs to execute those actions when the key is pressed. If enable Toggling Actions, every other key press will execute Actions listed in Toggled Action IDs. The LED color of the key before being pressed, after being pressed, and while the last action is running. Color is an RGB string, with 0-255 for each color. For example, red is "255, 0, 0" and blue is "0, 0, 255".',

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_neokey', 'adafruit-circuitpython-neokey==1.1.2')
    ],

    'options_enabled': [
        'custom_options',
        'enable_actions',
        'measurements_configure'
    ],

    'function_actions': [
        'neopixel_set_color',
        'neopixel_flashing_on',
        'neopixel_flashing_off'
    ],

    'custom_options': [
        {
            'id': 'i2c_address',
            'type': 'text',
            'default_value': '0x30',
            'required': True,
            'name': TRANSLATIONS['i2c_location']['title'],
            'phrase': ''
        },
        {
            'id': 'i2c_bus',
            'type': 'integer',
            'default_value': 1,
            'required': True,
            'name': TRANSLATIONS['i2c_bus']['title'],
            'phrase': ''
        },
        {
            'id': 'key_led_brightness',
            'type': 'float',
            'default_value': 0.2,
            'required': True,
            'name': 'LED Brightness (0.0-1.0)',
            'phrase': 'The brightness of the LEDs'
        },
        {
            'id': 'led_flash_period_sec',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'name': 'LED Flash Period (Seconds)',
            'phrase': 'Set the period if the LED begins flashing'
        },
    ],

    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        },
        {
            'id': 'key_led_delay',
            'type': 'float',
            'default_value': 1.5,
            'required': True,
            'name': 'LED Delay (Seconds)',
            'phrase': 'How long to leave the LED on after the last action executes.'
        },
        {
            'id': 'key_action_ids',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': 'Action ID(s)',
            'phrase': 'Set which action(s) execute when the key is pressed. Enter one or more Action IDs, separated by commas'
        },
        {
            'id': 'enable_toggling_actions',
            'type': 'bool',
            'default_value': False,
            'required': True,
            'name': 'Enable Toggling Actions',
            'phrase': 'Alternate between executing two sets of Actions'
        },
        {
            'id': 'toggle_action_ids',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': 'Toggled Action ID(s)',
            'phrase': 'Set which action(s) execute when the key is pressed on even presses. Enter one or more Action IDs, separated by commas'
        },
        {
            'id': 'led_rest',
            'type': 'text',
            'default_value': '0, 0, 0',
            'required': True,
            'name': 'Resting LED Color (RGB)',
            'phrase': 'The RGB color while no actions are running (e.g 10, 0, 0)'
        },
        {
            'id': 'led_start',
            'type': 'text',
            'default_value': '0, 255, 0',
            'required': True,
            'name': 'Actions Running LED Color: (RGB)',
            'phrase': 'The RGB color while all but the last action is running (e.g 10, 0, 0)'
        },
        {
            'id': 'led_last',
            'type': 'text',
            'default_value': '0, 0, 255',
            'required': True,
            'name': 'Last Action LED Color (RGB)',
            'phrase': 'The RGB color while the last action is running (e.g 10, 0, 0)'
        },
        {
            'id': 'led_shutdown',
            'type': 'text',
            'default_value': '0, 0, 0',
            'required': True,
            'name': 'Shutdown LED Color (RGB)',
            'phrase': 'The RGB color when the Function is disabled (e.g 10, 0, 0)'
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.options_channels = {}
        self.neokey = None
        self.flashing = {}
        self.colorwheel = None
        self.control = None
        self.timer_flash = time.time()
        self.key_press_executing = {}
        self.toggle = {}

        # Initialize custom options
        self.i2c_address = None
        self.i2c_bus = None
        self.key_led_brightness = None
        self.led_flash_period_sec = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.try_initialize()

    def initialize(self):
        from adafruit_neokey.neokey1x4 import NeoKey1x4
        from adafruit_extended_bus import ExtendedI2C
        from rainbowio import colorwheel

        self.colorwheel = colorwheel
        self.control = DaemonControl()

        try:
            function_channels = db_retrieve_table_daemon(
                FunctionChannel).filter(FunctionChannel.function_id == self.unique_id).all()
            self.options_channels = self.setup_custom_channel_options_json(
                FUNCTION_INFORMATION['custom_channel_options'], function_channels)

            for channel in range(4):
                list_action_ids = []
                if self.options_channels['key_action_ids'][channel].replace(" ", ""):
                    for action_id in self.options_channels['key_action_ids'][channel].replace(" ", "").split(","):
                        list_action_ids.append(action_id)
                self.options_channels['key_action_ids'][channel] = list_action_ids
            self.logger.debug(f"Parsed Action IDs: {self.options_channels['key_action_ids']}")
        except:
            self.logger.exception("Parsing action IDs")

        self.logger.debug(f"Brightness: {self.key_led_brightness}")
        self.logger.debug(f"Colors: "
                          f"{self.options_channels['led_rest']}, "
                          f"{self.options_channels['led_start']}, "
                          f"{self.options_channels['led_last']}")

        try:
            self.neokey = NeoKey1x4(
                ExtendedI2C(self.i2c_bus),
                addr=int(str(self.i2c_address), 16))

            self.neokey.pixels.brightness = self.key_led_brightness

            for key in range(4):
                self.set_color({"led_number": key, "led_color": self.options_channels['led_rest'][key]})
                self.flashing[key] = {
                    "enabled": False,
                    "color": None,
                    "on": False
                }
                self.key_press_executing[key] = False
                self.toggle[key] = {
                    "enabled": self.options_channels['enable_toggling_actions'][key],
                    "toggled": False
                }
        except:
            self.logger.exception("Initializing device")

    def listener(self):
        """This function will be turned into a thread to watch for key presses."""
        while self.running:
            # Check key press
            for key in range(4):
                if not self.key_press_executing[key] and self.neokey[key]:
                    self.key_press_executing[key] = True
                    self.logger.debug(f"Key {key + 1} Pressed")
                    self.set_color({"led_number": key, "led_color": self.options_channels['led_start'][key]})

                    write_influxdb_value(
                        self.unique_id,
                        self.channels_measurement[key].unit,
                        value=1,
                        measure=self.channels_measurement[key].measurement,
                        channel=key)

                    key_thread = threading.Thread(
                        target=self.run_key_actions,
                        args=(key,))
                    key_thread.daemon = True
                    key_thread.start()

            # Check for flashing
            if self.timer_flash < time.time():
                while self.timer_flash < time.time():
                    self.timer_flash += self.led_flash_period_sec
                for key in range(4):
                    if self.flashing[key]["enabled"] and not self.key_press_executing[key]:
                        if self.flashing[key]["on"]:
                            self.flashing[key]["on"] = False
                            self.neokey.pixels[key] = 0x0  # LED off
                        else:
                            self.flashing[key]["on"] = True
                            self.set_color({"led_number": key, "led_color": self.flashing[key]["color"]})

            time.sleep(0.1)

    def stop_function(self):
        self.running = False
        for key in range(4):
            self.set_color({"led_number": key, "led_color": self.options_channels['led_shutdown'][key]})

    def run_key_actions(self, key):
        action_ids = self.options_channels['key_action_ids'][key]
        if self.toggle[key]["enabled"] and self.toggle[key]["toggled"]:
            self.toggle[key]["toggled"] = False
            action_ids = self.options_channels['toggle_action_ids'][key]
        elif self.toggle[key]["enabled"] and not self.toggle[key]["toggled"]:
            self.toggle[key]["toggled"] = True

        for i, each_id in enumerate(action_ids):
            if i == len(action_ids) - 1:
                self.set_color({"led_number": key, "led_color": self.options_channels['led_last'][key]})

            if not self.running:
                self.logger.info("Detected shutting down, stopping execution of Actions")
                self.set_color({"led_number": key, "led_color": self.options_channels['led_rest'][key]})
                return

            action = db_retrieve_table_daemon(Actions).filter(
                Actions.unique_id.startswith(each_id)).first()

            if not action:
                self.logger.error(f"Unknown Action ID: '{each_id}'")
                continue

            try:
                self.logger.debug(f"Executing Action with ID {each_id}")
                return_dict = self.control.trigger_action(
                    action.unique_id,
                    value={"message": "", "measurements_dict": {}},
                    debug=False)
                if return_dict and "message" in return_dict:
                    self.logger.debug(f"Action {each_id} return message: {return_dict['message']}")
            except:
                self.logger.exception(f"Executing Action with ID {each_id}")

        time.sleep(self.options_channels['key_led_delay'][key])
        self.set_color({"led_number": key, "led_color": self.options_channels['led_rest'][key]})
        self.key_press_executing[key] = False

    def set_color(self, dict_payload):
        if "led_number" not in dict_payload:
            self.logger.error("Missing key 'led_number'")
            return
        if "led_color" not in dict_payload:
            self.logger.error("Missing key 'led_color'")
            return

        if type(dict_payload["led_color"]) is str:
            list_color = dict_payload["led_color"].replace(" ", "").split(",")
            color_error = False
            try:
                r = int(list_color[0])
                g = int(list_color[1])
                b = int(list_color[2])
                if r < 0 or r > 255 or g < 0 or g > 255 or b < 0 or b > 255:
                    color_error = True
                self.neokey.pixels[dict_payload["led_number"]] = r << 16 | g << 8 | b  # Each 0 - 255
            except:
                color_error = True
            if color_error:
                self.logger.error(
                    "Improper RGB color format. "
                    "Must be three values, separated by commas, between 0 and 255 each. For example: 10, 0, 255")

    def flashing_on(self, dict_payload):
        if "led_number" not in dict_payload:
            self.logger.error("Missing key 'led_number'")
            return
        if "led_color" not in dict_payload:
            self.logger.error("Missing key 'led_color'")
            return
        if dict_payload["led_number"] not in self.flashing:
            self.logger.error(f'Key {dict_payload["led_number"]} does not exist')
            return

        if type(dict_payload["led_color"]) is str:
            list_color = dict_payload["led_color"].replace(" ", "").split(",")
            r = int(list_color[0])
            g = int(list_color[1])
            b = int(list_color[2])
            self.flashing[dict_payload["led_number"]]["color"] = r << 16 | g << 8 | b  # Each 0 - 255

        self.timer_flash = time.time() + self.led_flash_period_sec
        self.flashing[dict_payload["led_number"]]["enabled"] = True

    def flashing_off(self, dict_payload):
        if "led_number" not in dict_payload:
            self.logger.error("Missing key 'led_number'")
            return
        if dict_payload["led_number"] not in self.flashing:
            self.logger.error(f'Key {dict_payload["led_number"]} does not exist')
            return

        self.flashing[dict_payload["led_number"]]["enabled"] = False
        time.sleep(0.5)
        self.neokey.pixels[dict_payload["led_number"]] = 0x0  # LED off
