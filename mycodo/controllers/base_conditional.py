# coding=utf-8
"""
This module contains the AbstractConditional Class which acts as a template
for all Conditionals. It is not to be used directly. The AbstractConditional Class
ensures that certain methods and instance variables are included in each
Conditional.

All Conditionals should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import json

from mycodo.config import MYCODO_DB_PATH
from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.utils import session_scope
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon


class AbstractConditional:
    """
    Base Conditional class that ensures certain methods and values are present
    in Conditionals.
    """
    def __init__(self, logger, function_id, message, timeout=30):
        self.logger = logger
        self.function_id = function_id
        self.variables = {}
        self.message = message
        self.running = True
        self.control = DaemonControl(pyro_timeout=timeout)

    def run_all_actions(self, message=None):
        if message is None:
            message = self.message
        self.message = self.control.trigger_all_actions(self.function_id, message=message)

    def run_action(self, action_id, value=None, message=None):
        action = None
        full_action_id = action_id
        if len(action_id) < 36:
            action_id = action_id.replace("{", "").replace("}", "")
            with session_scope(MYCODO_DB_PATH) as new_session:
                action = new_session.query(Actions).filter(
                    Actions.unique_id.startswith(action_id)).first()
                new_session.expunge_all()
        if action:
            full_action_id = action.unique_id

        if message is None:
            message = self.message
        self.message = self.control.trigger_action(
            full_action_id, value=value, message=message)

    def condition(self, condition_id):
        full_cond_id = condition_id
        cond = None
        if len(condition_id) < 36:
            condition_id = condition_id.replace("{", "").replace("}", "")
            with session_scope(MYCODO_DB_PATH) as new_session:
                cond = new_session.query(ConditionalConditions).filter(
                    ConditionalConditions.unique_id.startswith(condition_id)).first()
                new_session.expunge_all()
        if cond:
            full_cond_id = cond.unique_id

        return self.control.get_condition_measurement(full_cond_id)

    def condition_dict(self, condition_id):
        full_cond_id = condition_id
        cond = None
        if len(condition_id) < 36:
            condition_id = condition_id.replace("{", "").replace("}", "")
            with session_scope(MYCODO_DB_PATH) as new_session:
                cond = new_session.query(ConditionalConditions).filter(
                    ConditionalConditions.unique_id.startswith(condition_id)).first()
                new_session.expunge_all()
        if cond:
            full_cond_id = cond.unique_id

        list_times_values = self.control.get_condition_measurement_dict(full_cond_id)
        if list_times_values:
            list_ts_values = []
            for time, value in list_times_values:
                list_ts_values.append({'time': time, 'value': float(value)})
            return list_ts_values
        return None

    def stop_conditional(self):
        self.running = False

    def set_custom_option(self, option, value):
        try:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_cond = new_session.query(Conditional).filter(
                    Conditional.unique_id == self.function_id).first()
                try:
                    dict_custom_options = json.loads(mod_cond.custom_options)
                except:
                    dict_custom_options = {}
                dict_custom_options[option] = value
                mod_cond.custom_options = json.dumps(dict_custom_options)
                new_session.commit()
        except Exception:
            self.logger.exception("set_custom_option")

    def get_custom_option(self, option):
        conditional = db_retrieve_table_daemon(Conditional, unique_id=self.function_id)
        try:
            dict_custom_options = json.loads(conditional.custom_options)
        except:
            dict_custom_options = {}
        if option in dict_custom_options:
            return dict_custom_options[option]
