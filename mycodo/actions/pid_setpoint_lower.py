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
    'name_unique': 'setpoint_pid_lower',
    'name': "{}: {}: {}".format(TRANSLATIONS['pid']['title'], lazy_gettext('Lower'), lazy_gettext("Setpoint")),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Lower the Setpoint of a PID.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will lower the setpoint of the selected PID Controller. '
             'Executing <strong>self.run_action("ACTION_ID", value={"pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "amount": 2})</strong> will lower the setpoint of the PID with the specified ID. Don\'t forget to change the pid_id value to an actual PID ID that exists in your system.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'PID'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': 'Select the PID Controller to lower the setpoint of'
        },
        {
            'id': 'amount',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'name': lazy_gettext('Lower Setpoint'),
            'phrase': 'The amount to lower the PID setpoint by'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: PID Setpoint Lower."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.amount = None

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
            controller_id = dict_vars["value"]["pid_id"]
        except:
            controller_id = self.controller_id

        try:
            amount = dict_vars["value"]["amount"]
        except:
            amount = self.amount

        pid = db_retrieve_table_daemon(
            PID, unique_id=controller_id, entry='first')

        if not pid:
            msg = f" Error: PID Controller with ID '{controller_id}' not found."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        new_setpoint = pid.setpoint - amount
        dict_vars['message'] += f" Lower Setpoint of PID {controller_id} ({pid.name}) by {amount}, to {new_setpoint}."

        if pid.is_activated:
            setpoint_pid = threading.Thread(
                target=self.control.pid_set,
                args=(pid.unique_id,
                      'setpoint',
                      new_setpoint,))
            setpoint_pid.start()
        else:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_pid = new_session.query(PID).filter(
                    PID.unique_id == controller_id).first()
                mod_pid.setpoint = new_setpoint
                new_session.commit()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
