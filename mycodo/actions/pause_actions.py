# coding=utf-8
import time

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'pause_actions',
    'name': f"Actions: {TRANSLATIONS['pause']['title']}",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Set a delay between executing Actions when self.run_all_actions() is used.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will create a pause for the set duration. When <strong>self.run_all_actions()</strong> is executed, this will add a pause in the sequential execution of all actions.',

    'custom_options': [
        {
            'id': 'duration',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Duration'), lazy_gettext('Seconds')),
            'phrase': 'The duration to pause'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Pause"""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.duration = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        dict_vars['message'] += f" Pause for {self.duration} seconds."

        time.sleep(self.duration)

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
