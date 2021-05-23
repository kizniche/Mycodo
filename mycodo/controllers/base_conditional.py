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

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Conditional
from mycodo.databases.utils import session_scope
from mycodo.mycodo_client import DaemonControl
from mycodo.utils.database import db_retrieve_table_daemon

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


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
        if message is None:
            message = self.message
        self.message = self.control.trigger_action(
            action_id, value=value, message=message, single_action=True)

    def condition(self, condition_id):
        return self.control.get_condition_measurement(condition_id)

    def condition_dict(self, condition_id):
        string_sets = self.control.get_condition_measurement_dict(condition_id)
        if string_sets:
            list_ts_values = []
            for each_set in string_sets.split(';'):
                ts_value = each_set.split(',')
                list_ts_values.append({'time': ts_value[0], 'value': float(ts_value[1])})
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
