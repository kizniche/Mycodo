# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'create_log_line',
    'name': f"{TRANSLATIONS['create']['title']}: Daemon Log Line",
    'message': lazy_gettext('Create a log line in the daemon log.'),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will add a line to the Daemon log. '
             'Executing <strong>self.run_action("ACTION_ID", value={"log_level": "info", "log_text": "this is a log line"})</strong> will execute the action with the specified log level and log line text. If a log line text is not specified, then the action message will be used as the text.',

    'custom_options': [
        {
            'id': 'log_level',
            'type': 'select',
            'default_value': 'info',
            'required': True,
            'options_select': [
                ('info', 'Info'),
                ('warning', 'Warning'),
                ('error', 'Error'),
                ('debug', 'Debug')
            ],
            'name': 'Log Level',
            'phrase': 'The log level to insert the text into the log'
        },
        {
            'id': 'log_text',
            'type': 'text',
            'default_value': 'Log Line Text',
            'required': False,
            'name': 'Log Line Text',
            'phrase': 'The text to insert in the Daemon log'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Create Note."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.log_level = None
        self.log_text = None

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
            log_level = dict_vars["value"]["log_level"]
        except:
            log_level = self.log_level

        try:
            log_text = dict_vars["value"]["log_text"]
        except:
            log_text = self.log_text

        if not log_text:
            log_text = dict_vars['message']

        dict_vars['message'] += f" Adding text '{log_text}' to Daemon log at log level {log_level}"

        if log_level == 'info':
            self.logger.info(log_text)
        elif log_level == 'warning':
            self.logger.warning(log_text)
        elif log_level == 'error':
            self.logger.error(log_text)
        elif log_level == 'debug':
            self.logger.debug(log_text)

        if log_level != 'debug':
            self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
