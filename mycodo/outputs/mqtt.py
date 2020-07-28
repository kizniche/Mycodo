# coding=utf-8
# mqtt.py - MQTT Output module
from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: database object, SQL object with user-saved Output options
    :param value: input value, float or int
    :return: tuple: (bool, list of strings, database object)
    """
    errors = []
    all_passed = True
    if value <= 0:  # Ensure value is positive
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

OUTPUT_INFORMATION = {
    'output_name_unique': 'MQTT_PAHO',
    'output_manufacturer': 'Mycodo',
    'output_name': "{} MQTT Publish".format(lazy_gettext('On/Off')),
    'output_library': 'paho-mqtt',
    'measurements_dict': measurements_dict,
    'url_additional': 'http://www.eclipse.org/paho/',

    'on_state_internally_handled': False,
    'output_types': ['on_off'],
    'interfaces': ['Mycodo'],

    'message': 'An output to publish "on" or "off" to an MQTT server.',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt')
    ],

    'options_enabled': [
        'on_off_state_startup',
        'on_off_state_shutdown',
        'trigger_functions_startup',
        'current_draw',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'custom_options': [
        {
            'id': 'hostname',
            'type': 'text',
            'default_value': 'localhost',
            'required': True,
            'name': lazy_gettext('Hostname'),
            'phrase': lazy_gettext('The hostname of the MQTT server')
        },
        {
            'id': 'port',
            'type': 'integer',
            'default_value': 1883,
            'required': True,
            'name': lazy_gettext('Port'),
            'phrase': lazy_gettext('The port of the MQTT server')
        },
        {
            'id': 'topic',
            'type': 'text',
            'default_value': 'paho/test/single',
            'required': True,
            'name': lazy_gettext('Topic'),
            'phrase': lazy_gettext('The topic to publish with')
        },
        {
            'id': 'keepalive',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Keep Alive'),
            'phrase': lazy_gettext('The keepalive timeout value for the client. Set to 0 to disable.')
        },
        {
            'id': 'clientid',
            'type': 'text',
            'default_value': 'mycodo_mqtt_client',
            'required': True,
            'name': lazy_gettext('Client ID'),
            'phrase': lazy_gettext('Unique client ID for connecting to the MQTT server')
        },
        {
            'id': 'payload_on',
            'type': 'text',
            'default_value': 'on',
            'required': True,
            'name': lazy_gettext('On Payload'),
            'phrase': lazy_gettext('The payload to send when turned on')
        },
        {
            'id': 'payload_off',
            'type': 'text',
            'default_value': 'off',
            'required': True,
            'name': lazy_gettext('Off Payload'),
            'phrase': lazy_gettext('The payload to send when turned off')
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.output_setup = None
        self.output_state = False

        self.hostname = None
        self.port = None
        self.topic = None
        self.keepalive = None
        self.clientid = None
        self.payload_off = None
        self.payload_on = None
        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        if not testing:
            self.initialize_output()

    def initialize_output(self):
        import paho.mqtt.publish as publish

        self.publish = publish

    def output_switch(self, state, output_type=None, amount=None):
        try:
            if state == 'on':
                self.publish.single(
                    self.topic,
                    self.payload_on,
                    hostname=self.hostname,
                    port=self.port,
                    client_id=self.clientid,
                    keepalive=self.keepalive)
                self.output_state = True
            elif state == 'off':
                self.publish.single(
                    self.topic,
                    payload=self.payload_off,
                    hostname=self.hostname,
                    port=self.port,
                    client_id=self.clientid,
                    keepalive=self.keepalive)
                self.output_state = False
        except Exception as e:
            self.logger.error("State change error: {}".format(e))

    def is_on(self):
        if self.is_setup():
            return self.output_state

    def is_setup(self):
        return self.output_setup

    def setup_output(self):
        self.output_setup = True
