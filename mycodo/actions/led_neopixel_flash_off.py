# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.databases.models import CustomController
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.functions import parse_function_information

ACTION_INFORMATION = {
    'name_unique': 'action_led_neopixel_flash_off',
    'name': "LED: Neopixel: {} {}".format(lazy_gettext('Flashing'), lazy_gettext('Off')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Stop flashing an LED in a Neopixel LED strip. Select the Neopixel LED Strip Controller and pixel number.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will set the selected LED to the selected Color. '
             'Executing <strong>self.run_action("ACTION_ID", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "led": 0})</strong> will stop flashing the specified LED for the Neopixel LED Strip Controller with the specified ID. Don\'t forget to change the controller_id value to an actual Controller ID that exists in your system.',

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
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Clear Total kWh."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.led_number = None

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

        try:
            controller_id = dict_vars["value"]["controller_id"]
        except:
            pass

        try:
            led_number = dict_vars["value"]["led"]
        except:
            pass

        this_function = db_retrieve_table_daemon(
            CustomController, unique_id=controller_id, entry='first')

        payload = {
            "led_number": led_number
        }

        if this_function:
            functions = parse_function_information()
            if this_function.device in functions and "function_actions" in functions[this_function.device]:
                if "neopixel_flashing_off" not in functions[this_function.device]["function_actions"]:
                    msg = " Selected neopixel Function is not capable of flashing"
                    dict_vars['message'] += msg
                    self.logger.error(msg)
                    return dict_vars

                dict_vars['message'] += f"Stop flashing the LED {led_number} of Controller with ID {controller_id} ({this_function.name})."

                start_flashing = threading.Thread(
                    target=self.control.module_function,
                    args=("Function", controller_id, "flashing_off", payload,))
                start_flashing.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
