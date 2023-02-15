# coding=utf-8
import time

from mycodo.databases.models import Actions
from mycodo.databases.models import SMTP
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.actions import check_allowed_to_email
from mycodo.utils.send_data import send_email

ACTION_INFORMATION = {
    'name_unique': 'email',
    'name': 'Send Email',
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Send an email.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will email the specified recipient(s) using the SMTP credentials in the system configuration. Separate multiple recipients with commas. The body of the email will be the self-generated message. '
             'Executing <strong>self.run_action("ACTION_ID", value={"email_address": ["email1@email.com", "email2@email.com"], "message": "My message"})</strong> will send an email to the specified recipient(s) with the specified message.',

    'custom_options': [
        {
            'id': 'email',
            'type': 'text',
            'default_value': 'email@domain.com',
            'required': True,
            'name': 'E-Mail Address',
            'phrase': 'E-mail recipient(s) (separate multiple addresses with commas)'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Send Email."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.email = None

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
            email_recipients = dict_vars["value"]["email_address"]
        except:
            if "," in self.email:
                email_recipients = self.email.split(",")
            else:
                email_recipients = [self.email]

        if not email_recipients:
            msg = f" Error: No recipients specified."
            self.logger.error(msg)
            dict_vars['message'] += msg
            return dict_vars

        try:
            message_send = dict_vars["value"]["message"]
        except:
            message_send = False

        # If the emails per hour limit has not been exceeded
        smtp_wait_timer, allowed_to_send_notice = check_allowed_to_email()
        if allowed_to_send_notice:
            dict_vars['message'] += f" Email '{self.email}'."
            if not message_send:
                message_send = dict_vars['message']
            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            send_email(smtp.host, smtp.protocol, smtp.port,
                       smtp.user, smtp.passw, smtp.email_from,
                       email_recipients, message_send)
        else:
            self.logger.error(
                f"Wait {smtp_wait_timer - time.time():.0f} seconds to email again.")

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
