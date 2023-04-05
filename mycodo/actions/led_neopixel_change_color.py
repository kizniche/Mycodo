# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.databases.models import Output
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'action_led_neopixel_change_color',
    'name': f"LED: Neopixel RGB Strip: Change Color",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Change the color of an LED in a Neopixel LED strip. Select the Neopixel LED Strip Output.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will set the selected LED to the selected Color. '
             'Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "led": 0, "color": "10, 10, 0"})</strong> will set the color of the specified LED for the Neopixel LED Strip Output with the specified ID. Don\'t forget to change the output_id value to an actual Output ID that exists in your system.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Output'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the energy meter Input'
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
            'phrase': 'The color in RGB format, each from 0 to 255 (e.g "10, 0 0")'
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
        try:
            controller_id = dict_vars["value"]["output_id"]
        except:
            controller_id = self.controller_id

        try:
            led_number = dict_vars["value"]["led"]
        except:
            led_number = self.led_number

        try:
            led_color = dict_vars["value"]["color"]
        except:
            led_color = self.led_color

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

        this_output = db_retrieve_table_daemon(
            Output, unique_id=controller_id, entry='first')

        if not this_output:
            msg = f" Error: Output with ID '{controller_id}' not found."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        payload = {
            "led_number": led_number,
            "led_color": led_color
        }

        dict_vars['message'] += f" Set color of LED {led_number} to {led_color} for Output {controller_id} ({this_output.name})."
        clear_volume = threading.Thread(
            target=self.control.module_function,
            args=("Output", this_output.unique_id, "set_led", payload,))
        clear_volume.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
