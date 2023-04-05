# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.databases.models import Actions
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import cmd_output

ACTION_INFORMATION = {
    'name_unique': 'command',
    'name': "{}: Bash/Shell Command".format(lazy_gettext('Execute')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Execute a Linux bash shell command.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will execute the bash command.'
             'Executing <strong>self.run_action("ACTION_ID", value={"user": "mycodo", "command": "/home/pi/my_script.sh on"})</strong> will execute the action with the specified command and user.',

    'custom_options': [
        {
            'id': 'user',
            'type': 'text',
            'default_value': 'mycodo',
            'required': True,
            'name': lazy_gettext('User'),
            'phrase': lazy_gettext('The user to execute the command')
        },
        {
            'id': 'command',
            'type': 'text',
            'default_value': '/home/pi/my_script.sh on',
            'required': True,
            'name': lazy_gettext('Command'),
            'phrase': 'Command to execute'
        },
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Shell Command."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.user = None
        self.command = None

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
            command = dict_vars["value"]["command"]
        except:
            command = self.command

        try:
            user = dict_vars["value"]["user"]
        except:
            user = self.user

        dict_vars['message'] += f" Execute '{command}' as {user}."

        cmd_out, cmd_err, cmd_status = cmd_output(command, user=user)

        dict_vars['message'] += f" return out: {cmd_out}, err: {cmd_err}, status: {cmd_status}."

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
