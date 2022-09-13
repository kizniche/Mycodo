# coding=utf-8
import threading

from flask_babel import lazy_gettext
from mycodo.utils.functions import parse_function_information
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import CustomController
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'display_backlight_color',
    'name': "{}: {}: {}".format(TRANSLATIONS['display']['title'], lazy_gettext('Backlight'), lazy_gettext('Color')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Set the display backlight color',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will change the backlight color on the selected display. '
             'Executing <strong>self.run_action("ACTION_ID", value={"display_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "color": "255,0,0"})</strong> will change the backlight color on the controller with the specified ID and color.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Function'
            ],
            'name': lazy_gettext('Display'),
            'phrase': 'Select the display to set the backlight color'
        },
        {
            'id': 'color',
            'type': 'text',
            'default_value': '255,0,0',
            'required': False,
            'name': 'Color (RGB)',
            'phrase': 'Color as R,G,B values (e.g. "255,0,0" without quotes)'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Set the Display Backlight Color."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.color = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        try:
            controller_id = dict_vars["value"]["display_id"]
        except:
            controller_id = self.controller_id

        try:
            color = dict_vars["value"]["color"]
        except:
            color = self.color

        display = db_retrieve_table_daemon(
            CustomController, unique_id=controller_id)

        if not display:
            msg = f" Error: Display with ID '{controller_id}' not found."
            message += msg
            self.logger.error(msg)
            return message

        functions = parse_function_information()
        if (display.device not in functions or
                "function_actions" not in functions[display.device] or
                "display_backlight_color" not in functions[display.device]["function_actions"]):
            msg = " Selected display is not capable of setting the backlight color."
            message += msg
            self.logger.error(msg)
            return message

        message += f" Set display {controller_id} ({display.name}) backlight color to {color}."

        start_flashing = threading.Thread(
            target=self.control.module_function,
            args=("Function", controller_id, "display_backlight_color", {"color": color},))
        start_flashing.start()

        self.logger.debug(f"Message: {message}")

        return message

    def is_setup(self):
        return self.action_setup
