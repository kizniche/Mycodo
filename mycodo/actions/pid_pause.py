# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.config import MYCODO_DB_PATH
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import PID
from mycodo.databases.utils import session_scope
from mycodo.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'pause_pid',
    'name': f"{TRANSLATIONS['pid']['title']}: {TRANSLATIONS['pause']['title']}",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Pause a PID.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will pause the selected PID Controller. '
             'Executing <strong>self.run_action("ACTION_ID", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong> will pause the PID Controller with the specified ID.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'PID'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the PID Controller to pause'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: PID Pause."""
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

    def run_action(self, message, dict_vars):
        try:
            controller_id = dict_vars["value"]["pid_id"]
        except:
            controller_id = self.controller_id

        pid = db_retrieve_table_daemon(
            PID, unique_id=controller_id, entry='first')

        if not pid:
            msg = f" Error: PID Controller with ID '{controller_id}' not found."
            message += msg
            self.logger.error(msg)
            return message

        message += f" Pause PID {controller_id} ({pid.name})."

        if pid.is_paused:
            message += " Notice: PID is already paused!"
        elif pid.is_activated:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_pid = new_session.query(PID).filter(
                    PID.unique_id == controller_id).first()
                mod_pid.is_paused = True
                new_session.commit()
            pause_pid = threading.Thread(
                target=self.control.pid_pause,
                args=(controller_id,))
            pause_pid.start()

        self.logger.debug(f"Message: {message}")

        return message

    def is_setup(self):
        return self.action_setup
