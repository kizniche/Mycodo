# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.utils import session_scope
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.function_actions import which_controller

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'deactivate_controller',
    'name': f"{TRANSLATIONS['controller']['title']}: {TRANSLATIONS['deactivate']['title']}",
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Deactivate a controller.'),

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will deactivate the selected Controller. '
             'Executing <strong>self.run_action("{ACTION_ID}", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong> will deactivate the controller with the specified ID.',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function',
                'Conditional',
                'PID',
                'Trigger'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the controller to deactivate'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Deactivate Controller."""
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        # Initialize custom options
        self.controller_id = None

        # Set custom options
        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        try:
            controller_id = dict_vars["value"]["controller_id"]
        except:
            controller_id = self.controller_id

        self.logger.debug(f"Finding controller with ID {controller_id}")

        (controller_type,
         controller_object,
         controller_entry) = which_controller(controller_id)

        if not controller_entry:
            msg = f" Error: Controller with ID '{controller_id}' not found."
            message += msg
            self.logger.error(msg)
            return message

        message += f" Deactivate Controller {controller_id} ({controller_entry.name})."

        if not controller_entry.is_activated:
            message += " Notice: Controller is already not active!"
        else:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_cont = new_session.query(controller_object).filter(
                    controller_object.unique_id == controller_id).first()
                mod_cont.is_activated = False
                new_session.commit()
            activate_controller = threading.Thread(
                target=self.control.controller_deactivate,
                args=(controller_id,))
            activate_controller.start()

        self.logger.debug(f"Message: {message}")

        return message

    def is_setup(self):
        return self.action_setup
