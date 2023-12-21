# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.databases.models import CustomController
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.functions import parse_function_information

ACTION_INFORMATION = {
    'name_unique': 'action_led_neopixel_flash_on',
    'name': "LED: Neopixel: {} {}".format(lazy_gettext('Flashing'), lazy_gettext('On')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Start flashing an LED in a Neopixel LED strip. Select the Neopixel LED Strip Controller, pixel number, and color.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will set the selected LED to the selected Color. '
             'Executing <strong>self.run_action("ACTION_ID", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "led": 0, "color": "10, 10, 0"})</strong> will start flashing the color of the specified LED for the Neopixel LED Strip Controller with the specified ID. Don\'t forget to change the controller_id value to an actual Controller ID that exists in your system.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Function'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the controller that modulates your neopixels'
        },
        {
            'id': 'led_number',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'name': 'LED Position',
            'phrase': 'The position of the LED on the strip'
        },
        {
            'id': 'led_color',
            'type': 'text',
            'default_value': '10, 0, 0',
            'required': True,
            'name': 'RGB Color',
            'phrase': 'The color in RGB format, each from 0 to 255 (e.g "10, 0, 0")'
        },
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Clear Total kWh."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.led_number = None
        self.led_color = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        controller_id = self.controller_id
        led_number = self.led_number
        led_color = self.led_color

        try:
            controller_id = dict_vars["value"]["controller_id"]
        except:
            pass

        try:
            led_number = dict_vars["value"]["led"]
        except:
            pass

        try:
            led_color = dict_vars["value"]["color"]
        except:
            pass

        try:
            red = int(led_color.split(',')[0])
            green = int(led_color.split(',')[1])
            blue = int(led_color.split(',')[2])
            if not (0 <= red <= 255 and 0 <= green <= 255 and 0 <= blue <= 255):
                msg = f" Error: Invalid color value(s). Must be between 0 and 255."
                dict_vars['message'] += msg
                self.logger.error(msg)
                return dict_vars
        except:
            msg = f" Error: Invalid color string: {led_color}"
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        this_function = db_retrieve_table_daemon(
            CustomController, unique_id=controller_id, entry='first')

        payload = {
            "led_number": led_number,
            "led_color": led_color
        }

        if this_function:
            functions = parse_function_information()
            if this_function.device in functions and "function_actions" in functions[this_function.device]:
                if "neopixel_flashing_on" not in functions[this_function.device]["function_actions"]:
                    msg = " Selected neopixel Function is not capable of flashing"
                    dict_vars['message'] += msg
                    self.logger.error(msg)
                    return dict_vars

                dict_vars['message'] += f" Star flashing LED {led_number} the color {led_color} of Controller with ID {controller_id} ({this_function.name})."

                start_flashing = threading.Thread(
                    target=self.control.module_function,
                    args=("Function", controller_id, "flashing_on", payload,))
                start_flashing.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
