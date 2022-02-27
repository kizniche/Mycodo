# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.databases.models import Actions
from mycodo.databases.models import Input
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'clear_total_volume',
    'name': "{}: {}".format(
        lazy_gettext('Flow Meter'), lazy_gettext('Clear Total Volume')),
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Clear the total volume saved for a flow meter Input. The Input must have the Clear Total Volume option.',

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will clear the total volume for the selected flow meter Input. '
             'Executing <strong>self.run_action("{ACTION_ID}", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will clear the total volume for the flow meter Input with the specified ID (e.g. 959019d1-c1fa-41fe-a554-7be3366a9c5b).',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the flow meter Input'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """
    Function Action: Clear Total Volume
    """
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.none = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        values_set = False
        if "value" in dict_vars and dict_vars["value"] is not None:
            try:
                controller_id = dict_vars["value"]
                values_set = True
            except:
                self.logger.exception("Error setting values passed to action")

        if not values_set:
            controller_id = self.controller_id

        this_input = db_retrieve_table_daemon(
            Input, unique_id=controller_id, entry='first')

        if not this_input:
            msg = " Input not found."
            message += msg
            self.logger.error(msg)
            return message

        message += " Clear total volume of Input {unique_id} ({id}, {name}).".format(
            unique_id=controller_id,
            id=this_input.id,
            name=this_input.name)
        clear_volume = threading.Thread(
            target=self.control.custom_button,
            args=("Input", this_input.unique_id, "clear_total_volume", {},))
        clear_volume.start()

        return message

    def is_setup(self):
        return self.action_setup
