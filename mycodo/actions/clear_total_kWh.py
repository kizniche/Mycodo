# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.databases.models import Actions
from mycodo.databases.models import Input
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'clear_total_kwh',
    'name': "{}: {} ({})".format(lazy_gettext('Flow Meter'), lazy_gettext('Clear Total'), lazy_gettext('Kilowatt-hour')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Clear the total kWh saved for an energy meter Input. The Input must have the Clear Total kWh option. This will also clear all energy stats on the device, not just the total kWh.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will clear the total kWh for the selected energy meter Input. '
             'Executing <strong>self.run_action("ACTION_ID", value={"input_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will clear the total kWh for the energy meter Input with the specified ID. Don\'t forget to change the input_id value to an actual Input ID that exists in your system.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the energy meter Input'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Clear Total kWh."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None

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
            controller_id = dict_vars["value"]["input_id"]
        except:
            controller_id = self.controller_id

        this_input = db_retrieve_table_daemon(
            Input, unique_id=controller_id, entry='first')

        if not this_input:
            msg = f" Error: Input with ID '{controller_id}' not found."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f" Clear total kWh of Input {controller_id} ({this_input.name})."
        clear_volume = threading.Thread(
            target=self.control.module_function,
            args=("Input", this_input.unique_id, "clear_total_kwh", {},))
        clear_volume.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
