# coding=utf-8
import http.client
import logging
import urllib
from urllib.parse import urlparse

from flask_babel import lazy_gettext

from mycodo.databases.models import Actions
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'webhook',
    'name': lazy_gettext('Webhook'),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Emits a HTTP request when triggered. The first line contains a HTTP verb (GET, POST, PUT, ...) followed by a space and the URL to call. Subsequent lines are optional "name: value"-header parameters. After a blank line, the body payload to be sent follows. {{{message}}} is a placeholder that gets replaced by the message, {{{quoted_message}}} is the message in an URL safe encoding.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will run the Action.',

    'custom_options': [
        {
            'id': 'webhook',
            'type': 'multiline_text',
            'lines': 7,
            'default_value': "",
            'required': True,
            'col_width': 12,
            'name': 'Webhook Request',
            'phrase': 'HTTP request to execute'
        },
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Webhook"""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.webhook = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, message, dict_vars):
        action_string = self.webhook
        action_string = action_string.replace("{{{message}}}", message)
        action_string = action_string.replace("{{{quoted_message}}}", urllib.parse.quote_plus(message))
        lines = action_string.splitlines()

        method = "GET"

        # first line is "[<Method> ]<URL>", following lines are http request headers
        parts = lines.pop(0).split(" ", 1)
        if len(parts) == 1:
            url = parts[0]
        else:
            method = parts[0]
            url = parts[1]

        headers = []
        while len(lines) > 0:
            line = lines.pop(0)
            if line.strip() == "":
                break
            headers.append(map(str.strip, line.split(':', 1)))

        headers = dict(headers)
        parsed_url = urlparse(url)
        body = "\n".join(lines)

        path_and_query = parsed_url.path + "?" + parsed_url.query

        message += f" Webhook with method: {method}, scheme: {parsed_url.scheme}, netloc: {parsed_url.netloc}, " \
                   f"path: {path_and_query}, headers: {headers}, body: {body}."

        if parsed_url.scheme == 'http':
            conn = http.client.HTTPConnection(parsed_url.netloc)
        elif parsed_url.scheme == 'https':
            conn = http.client.HTTPSConnection(parsed_url.netloc)
        else:
            raise Exception(f"Unsupported url scheme '{parsed_url.scheme}'")

        conn.request(method, path_and_query, body, headers)
        response = conn.getresponse()
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(response.readlines())
        if 200 <= response.getcode() < 300:
            self.logger.debug(f"HTTP {response.getcode()} -> OK")
        else:
            raise Exception(f"Got HTTP {response.getcode()} response.")
        response.close()

        self.logger.debug(f"Message: {message}")

        return message

    def is_setup(self):
        return self.action_setup
