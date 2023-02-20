# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.databases.models import Actions
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.utils import random_alphanumeric

ACTION_INFORMATION = {
    'name_unique': 'mqtt_publish',
    'name': "MQTT: {}".format(lazy_gettext('Publish')),
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Publish a value to an MQTT server.',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will publish the saved payload text options to the MQTT server. '
             'Executing <strong>self.run_action("ACTION_ID", value={"payload": 42})</strong> will publish the specified payload (any type) to the MQTT server. '
             'You can also specify the topic (e.g. value={"topic": "my_topic", "payload": 42}). '
             'Warning: If using multiple MQTT Inputs or Functions, ensure the Client IDs are unique.',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'custom_options': [
        {
            'id': 'hostname',
            'type': 'text',
            'default_value': 'localhost',
            'required': True,
            'name': lazy_gettext('Hostname'),
            'phrase': 'The hostname of the MQTT server'
        },
        {
            'id': 'port',
            'type': 'integer',
            'default_value': 1883,
            'required': True,
            'name': lazy_gettext('Port'),
            'phrase': 'The port of the MQTT server'
        },
        {
            'id': 'topic',
            'type': 'text',
            'default_value': 'paho/test/single',
            'required': True,
            'name': 'Topic',
            'phrase': 'The topic to publish with'
        },
        {
            'id': 'payload',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': 'Payload',
            'phrase': 'The payload to publish'
        },
        {
            'id': 'payload_type',
            'type': 'select',
            'default_value': 'text',
            'required': True,
            'options_select': [
                ('text', 'Text'),
                ('integer', 'Integer'),
                ('float', 'Float/Decimal')
            ],
            'name': 'Payload Type',
            'phrase': 'The type to cast the payload'
        },
        {
            'id': 'keepalive',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': lazy_gettext('Keep Alive'),
            'phrase': 'The keepalive timeout value for the client. Set to 0 to disable.'
        },
        {
            'id': 'clientid',
            'type': 'text',
            'default_value': f'client_{random_alphanumeric(8)}',
            'required': True,
            'name': 'Client ID',
            'phrase': 'Unique client ID for connecting to the MQTT server'
        },
        {
            'id': 'login',
            'type': 'bool',
            'default_value': False,
            'name': 'Use Login',
            'phrase': 'Send login credentials'
        },
        {
            'id': 'username',
            'type': 'text',
            'default_value': 'user',
            'required': False,
            'name': lazy_gettext('Username'),
            'phrase': 'Username for connecting to the server'
        },
        {
            'id': 'password',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': lazy_gettext('Password'),
            'phrase': 'Password for connecting to the server'
        },
        {
            'id': 'mqtt_use_websockets',
            'type': 'bool',
            'default_value': False,
            'required': False,
            'name': 'Use Websockets',
            'phrase': 'Use websockets to connect to the server.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: MQTT Publish."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.publish = None

        self.hostname = None
        self.port = None
        self.topic = None
        self.payload = None
        self.payload_type = None
        self.keepalive = None
        self.clientid = None
        self.login = None
        self.username = None
        self.password = None
        self.mqtt_use_websockets = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        import paho.mqtt.publish as publish
        self.publish = publish
        self.action_setup = True

    def run_action(self, dict_vars):
        try:
            topic = dict_vars["value"]["topic"]
        except:
            topic = self.topic

        try:
            payload = dict_vars["value"]["payload"]
        except:
            payload = self.payload

            try:
                if self.payload_type == 'integer':
                    payload = int(payload)
                elif self.payload_type == 'float':
                    payload = float(payload)
            except:
                msg = f" Error: Could not cast payload as {self.payload_type}."
                self.logger.error(msg)
                dict_vars['message'] += msg
                return dict_vars

        if not payload:
            msg = f" Error: Cannot publish to MQTT server without a payload."
            self.logger.error(msg)
            dict_vars['message'] += msg
            return dict_vars

        try:
            auth_dict = None
            if self.login:
                auth_dict = {
                    "username": self.username,
                    "password": self.password
                }
            self.publish.single(
                topic,
                payload,
                hostname=self.hostname,
                port=self.port,
                client_id=self.clientid,
                keepalive=self.keepalive,
                auth=auth_dict,
                transport='websockets' if self.mqtt_use_websockets else 'tcp')
            dict_vars['message'] += f" MQTT Publish '{payload}'."
        except Exception as err:
            msg = f" Could not execute MQTT Publish: {err}"
            self.logger.error(msg)
            dict_vars['message'] += msg

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
