# coding=utf-8
import time

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import SMTP
from mycodo.function_actions.base_function_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.function_actions import check_allowed_to_email
from mycodo.utils.send_data import send_email

FUNCTION_ACTION_INFORMATION = {
    'name_unique': 'email',
    'name': 'Send Email',
    'library': None,
    'manufacturer': 'Mycodo',

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Send an email.',

    'usage': 'Executing <strong>self.run_action("{ACTION_ID}")</strong> will email the specified recipient(s) using the SMTP credentials in the system configuration. Separate multiple recipients with commas. The body of the email will be the self-generated message. Executing <strong>self.run_action("{ACTION_ID}", value="Email message here")</strong> will send an email with the specified message.',

    'dependencies_module': [],

    'custom_options': [
        {
            'id': 'email',
            'type': 'text',
            'default_value': 'email@domain.com',
            'required': True,
            'name': 'E-Mail Address',
            'phrase': 'E-mail recipient(s). Separate multiple with commas.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """
    Function Action: Send Email
    """
    def __init__(self, action_dev, testing=False):
        super(ActionModule, self).__init__(action_dev, testing=testing, name=__name__)

        self.email = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        message_send = False
        if "value" in dict_vars and dict_vars["value"]:
            try:
                message_send = str(dict_vars["value"])
            except:
                self.logger.exception("Error setting values passed to action")

        if self.email:
            if "," in self.email:
                email_recipients = self.email.split(",")
            else:
                email_recipients = [self.email]
        else:
            msg = " No recipients specified."
            self.logger.error(msg)
            message += msg
            return message

        # If the emails per hour limit has not been exceeded
        smtp_wait_timer, allowed_to_send_notice = check_allowed_to_email()
        if allowed_to_send_notice:
            message += " Email '{email}'.".format(
                email=self.email)
            if not message_send:
                message_send = message
            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            send_email(smtp.host, smtp.protocol, smtp.port,
                       smtp.user, smtp.passw, smtp.email_from,
                       email_recipients, message_send)
        else:
            self.logger.error(
                "Wait {sec:.0f} seconds to email again.".format(
                    sec=smtp_wait_timer - time.time()))

        return message

    def is_setup(self):
        return self.action_setup
