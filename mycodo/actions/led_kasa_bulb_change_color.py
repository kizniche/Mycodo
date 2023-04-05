# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.databases.models import Output
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'action_led_kasa_bulb_change_color',
    'name': f"LED: Kasa RGB Bulb: Change Color",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Change the color of the LED in a Kasa RGB Bulb. Select the Kasa RGB Bulb Output.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will set the selected Kasa RGB Bulb to the selected Hue, Saturation, and Brightness. '
             'Executing <strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "hue": 10, "saturation": 50, "brightness": 25})</strong> will set the hue (0 - 360), saturation (0 - 100), and brightness (0 - 100) of the Kasa RGB Bulb Output with the specified ID. Don\'t forget to change the output_id value to an actual Output ID that exists in your system.',

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
            'id': 'hue',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Hue'), lazy_gettext('Degree')),
            'phrase': 'The hue to set, in degrees (0 - 360)'
        },
        {
            'id': 'saturation',
            'type': 'integer',
            'default_value': 50,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Saturation'), lazy_gettext('Percent')),
            'phrase': 'The saturation to set, in percent (0 - 100)'
        },
        {
            'id': 'brightness',
            'type': 'integer',
            'default_value': 50,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Brightness'), lazy_gettext('Percent')),
            'phrase': 'The brightness to set, in percent (0 - 100)'
        },
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Clear Total kWh."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.hue = None
        self.saturation = None
        self.brightness = None

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
            hue = dict_vars["value"]["hue"]
        except:
            hue = self.hue

        try:
            saturation = dict_vars["value"]["saturation"]
        except:
            saturation = self.saturation

        try:
            brightness = dict_vars["value"]["brightness"]
        except:
            brightness = self.brightness

        this_output = db_retrieve_table_daemon(
            Output, unique_id=controller_id, entry='first')

        if not this_output:
            msg = f" Error: Output with ID '{controller_id}' not found."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        payload = {
            "hsv": f"{hue}, {saturation}, {brightness}",
        }

        dict_vars['message'] += f" Set HSV to {payload['hsv']} for Output {controller_id} ({this_output.name})."
        clear_volume = threading.Thread(
            target=self.control.module_function,
            args=("Output", this_output.unique_id, "set_hsv", payload,))
        clear_volume.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
