# coding=utf-8
#
# mqtt_value.py - MQTT Output module
#
import copy

from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb

measurements_dict = {
    0: {
        'measurement': 'unitless',
        'unit': 'none'
    }
}

channels_dict = {
    0: {
        'types': ['value'],
        'measurements': [0]
    }
}

OUTPUT_INFORMATION = {
    'output_name_unique': 'MQTT_PAHO_VALUE',
    'output_name': "MQTT Publish: {}".format(lazy_gettext('Value')),
    'output_library': 'paho-mqtt',
    'output_manufacturer': 'Mycodo',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value'],

    'url_additional': 'http://www.eclipse.org/paho/',

    'interfaces': ['MYCODO'],

    'message': 'Publish a value to an MQTT server.',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'options_enabled': [
        'button_send_value'
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
            'id': 'off_value',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'name': lazy_gettext('Off Value'),
            'phrase': 'The value to send when an Off command is given'
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
            'phrase': 'Password for connecting to the server.'
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

    def output_switch(self, state, output_type=None, amount=None, output_channel=0):
        measure_dict = copy.deepcopy(measurements_dict)

        try:
            auth_dict = None
            if self.options_channels['login'][0]:
                if not self.options_channels['password'][0]:
                    self.options_channels['password'][0] = None
                auth_dict = {
                    "username": self.options_channels['username'][0],
                    "password": self.options_channels['password'][0]
                }

            if state == 'on' and amount is not None:
                self.publish.single(
                    self.options_channels['topic'][0],
                    amount,
                    hostname=self.options_channels['hostname'][0],
                    port=self.options_channels['port'][0],
                    client_id=self.options_channels['clientid'][0],
                    keepalive=self.options_channels['keepalive'][0],
                    auth=auth_dict)
                self.output_states[output_channel] = amount
                measure_dict[0]['value'] = amount
            elif state == 'off':
                self.publish.single(
                    self.options_channels['topic'][0],
                    payload=self.options_channels['off_value'][0],
                    hostname=self.options_channels['hostname'][0],
                    port=self.options_channels['port'][0],
                    client_id=self.options_channels['clientid'][0],
                    keepalive=self.options_channels['keepalive'][0],
                    auth=auth_dict)
                self.output_states[output_channel] = False
                measure_dict[0]['value'] = self.options_channels['off_value'][0]
        except Exception as e:
            self.logger.error("State change error: {}".format(e))
            return

        add_measurements_influxdb(self.unique_id, measure_dict)

    def is_on(self, output_channel=0):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup
