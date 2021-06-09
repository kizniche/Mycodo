# coding=utf-8
#
# mqtt.py - MQTT Output module
#
from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon

measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    }
}

OUTPUT_INFORMATION = {
    'output_name_unique': 'MQTT_PAHO',
    'output_name': "MQTT Publish: {}".format(lazy_gettext('On/Off')),
    'output_manufacturer': 'Mycodo',
    'output_library': 'paho-mqtt',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_additional': 'http://www.eclipse.org/paho/',

    'interfaces': ['MYCODO'],

    'message': 'Publish "on" or "off" (or any other strings of your choosing) to an MQTT server.',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'custom_channel_options': [
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
            'default_value': 'mycodo_mqtt_client',
            'required': True,
            'name': 'Client ID',
            'phrase': 'Unique client ID for connecting to the MQTT server'
        },
        {
            'id': 'payload_on',
            'type': 'text',
            'default_value': 'on',
            'required': True,
            'name': lazy_gettext('On Payload'),
            'phrase': 'The payload to send when turned on'
        },
        {
            'id': 'payload_off',
            'type': 'text',
            'default_value': 'off',
            'required': True,
            'name': lazy_gettext('Off Payload'),
            'phrase': 'The payload to send when turned off'
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state when Mycodo starts'
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': 'Set the state when Mycodo shuts down'
        },
        {
            'id': 'command_force',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Force Command'),
            'phrase': 'Always send the command if instructed, regardless of the current state'
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': '{} ({})'.format(lazy_gettext('Current'), lazy_gettext('Amps')),
            'phrase': 'The current draw of the device being controlled'
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
            'phrase': 'Password for connecting to the server. Leave blank to disable.'
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.publish = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        import paho.mqtt.publish as publish

        self.publish = publish

        self.setup_output_variables(OUTPUT_INFORMATION)
        self.output_setup = True

        if self.options_channels['state_startup'][0] == 1:
            self.output_switch('on')
        elif self.options_channels['state_startup'][0] == 0:
            self.output_switch('off')

    def output_switch(self, state, output_type=None, amount=None, output_channel=0):
        try:
            auth_dict = None
            if self.options_channels['login'][0]:
                if not self.options_channels['password'][0]:
                    self.options_channels['password'][0] = None
                auth_dict = {
                    "username": self.options_channels['username'][0],
                    "password": self.options_channels['password'][0]
                }

            if state == 'on':
                self.publish.single(
                    self.options_channels['topic'][0],
                    self.options_channels['payload_on'][0],
                    hostname=self.options_channels['hostname'][0],
                    port=self.options_channels['port'][0],
                    client_id=self.options_channels['clientid'][0],
                    keepalive=self.options_channels['keepalive'][0],
                    auth=auth_dict)
                self.output_states[output_channel] = True
            elif state == 'off':
                self.publish.single(
                    self.options_channels['topic'][0],
                    payload=self.options_channels['payload_off'][0],
                    hostname=self.options_channels['hostname'][0],
                    port=self.options_channels['port'][0],
                    client_id=self.options_channels['clientid'][0],
                    keepalive=self.options_channels['keepalive'][0],
                    auth=auth_dict)
                self.output_states[output_channel] = False
        except Exception as e:
            self.logger.error("State change error: {}".format(e))

    def is_on(self, output_channel=0):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 1:
                self.output_switch('on')
            elif self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
        self.running = False
