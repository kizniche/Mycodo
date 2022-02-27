# coding=utf-8
import threading

from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import PID
from mycodo.databases.utils import session_scope
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'setpoint_pid',
    'name': '{}: {}: {}'.format(
        TRANSLATIONS['pid']['title'],
        lazy_gettext('Set'),
        lazy_gettext('Setpoint')),
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Set the Setpoint of a PID.'),

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will set the setpoint of the selected PID Controller. '
             'Executing <strong>self.run_action("{ACTION_ID}", value={"setpoint": 42})</strong> will set the setpoint of the PID Controller (e.g. 42). '
             'You can also specify the PID ID (e.g. value={"setpoint": 42, "pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})',

    'dependencies_module': [],

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
        },
        {
            'id': 'setpoint',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'name': lazy_gettext('Setpoint'),
            'phrase': 'The setpoint to set the PID Controller'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """
    Function Action: PID Setpoint Set
    """
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.setpoint = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        setpoint = self.setpoint
        pid_id = self.controller_id
        try:
            setpoint = float(dict_vars["value"]["setpoint"])
        except:
            self.logger.debug("No valid setpoint passed to function")
        try:
            pid_id = str(dict_vars["value"]["pid_id"])
        except:
            self.logger.debug("No valid pid_id passed to function")

        pid = db_retrieve_table_daemon(
            PID, unique_id=pid_id, entry='first')

        if not pid:
            msg = "PID Controller with ID {} doesn't exist.".format(pid_id)
            message += msg
            self.logger.error(msg)
            return message

        message += " Set Setpoint of PID {unique_id} ({id}, {name}).".format(
            unique_id=pid_id,
            id=pid.id,
            name=pid.name)
        if pid.is_activated:
            setpoint_pid = threading.Thread(
                target=self.control.pid_set,
                args=(pid.unique_id,
                      'setpoint',
                      setpoint,))
            setpoint_pid.start()
        else:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_pid = new_session.query(PID).filter(
                    PID.unique_id == pid_id).first()
                mod_pid.setpoint = setpoint
                new_session.commit()

        return message

    def is_setup(self):
        return self.action_setup
