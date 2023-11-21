# coding=utf-8
import datetime

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Conversion
from mycodo.databases.models import InputChannel
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.actions import run_input_actions
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.inputs import parse_measurement
from mycodo.utils.utils import random_alphanumeric

# Measurements
measurements_dict = {}

# Channels
channels_dict = {
    0: {}
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MQTT_PAHO',
    'input_manufacturer': 'MQTT',
    'input_name': 'MQTT Subscribe (Value payload)',
    'input_name_short': 'MQTT Value',
    'input_library': 'paho-mqtt',
    'measurements_name': 'Variable measurements',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,

    'measurements_variable_amount': True,
    'channel_quantity_same_as_measurements': True,
    'measurements_use_same_timestamp': False,

    'message': 'A topic is subscribed to for each channel Subscription Topic and the returned '
               'payload value will be stored for that channel. Be sure you select and save the '
               'Measurement Unit for each of the channels. Once the unit has been saved, you '
               'can convert to other units in the Convert Measurement section. Warning: If using '
               'multiple MQTT Inputs or Functions, ensure the Client IDs are unique.',

    'options_enabled': [
        'measurements_select'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo'],

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'custom_options': [
        {
            'id': 'mqtt_hostname',
            'type': 'text',
            'default_value': 'localhost',
            'required': True,
            'name': TRANSLATIONS["host"]["title"],
            'phrase': TRANSLATIONS["host"]["phrase"]
        },
        {
            'id': 'mqtt_port',
            'type': 'integer',
            'default_value': 1883,
            'required': True,
            'name': TRANSLATIONS["port"]["title"],
            'phrase': TRANSLATIONS["port"]["phrase"]
        },
        {
            'id': 'mqtt_keepalive',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Keep Alive'),
            'phrase': 'Maximum amount of time between received signals. Set to 0 to disable.'
        },
        {
            'id': 'mqtt_clientid',
            'type': 'text',
            'default_value': 'client_{}'.format(random_alphanumeric(8)),
            'required': True,
            'name': 'Client ID',
            'phrase': 'Unique client ID for connecting to the server'
        },
        {
            'id': 'mqtt_login',
            'type': 'bool',
            'default_value': False,
            'name': 'Use Login',
            'phrase': 'Send login credentials'
        },
        {
            'id': 'mqtt_use_tls',
            'type': 'bool',
            'default_value': False,
            'name': 'Use TLS',
            'phrase': 'Send login credentials using TLS'
        },
        {
            'id': 'mqtt_username',
            'type': 'text',
            'default_value': 'user',
            'required': False,
            'name': lazy_gettext('Username'),
            'phrase': lazy_gettext('Username for connecting to the server')
        },
        {
            'id': 'mqtt_password',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': lazy_gettext('Password'),
            'phrase': 'Password for connecting to the server. Leave blank to disable.'
        },
        {
            'id': 'mqtt_use_websockets',
            'type': 'bool',
            'default_value': False,
            'required': False,
            'name': 'Use Websockets',
            'phrase': 'Use websockets to connect to the server.'
        }
    ],

    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        },
        {
            'id': 'subscribe_topic',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': 'Subscription Topic',
            'phrase': 'The MQTT topic to subscribe to'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that retrieves stored data from MQTT."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.log_level_debug = None
        self.client = None

        self.mqtt_hostname = None
        self.mqtt_port = None
        self.mqtt_channel = None
        self.mqtt_keepalive = None
        self.mqtt_clientid = None
        self.mqtt_login = None
        self.mqtt_use_tls = None
        self.mqtt_username = None
        self.mqtt_password = None
        self.mqtt_use_websockets = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import paho.mqtt.client as mqtt

        self.log_level_debug = self.input_dev.log_level_debug

        input_channels = db_retrieve_table_daemon(
            InputChannel).filter(InputChannel.input_id == self.input_dev.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            INPUT_INFORMATION['custom_channel_options'], input_channels)

        self.client = mqtt.Client(
            self.mqtt_clientid,
            transport='websockets' if self.mqtt_use_websockets else 'tcp')
        self.logger.debug(f"Client created with ID {self.mqtt_clientid}")
        if self.mqtt_login:
            if not self.mqtt_password:
                self.mqtt_password = None
            self.logger.debug("Sending username and password credentials")
            self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
        if self.mqtt_use_tls:
            self.client.tls_set()

    def listener(self):
        try:
            self.callbacks_connect()
            self.connect()
            self.client.loop_start()
        except:
            self.logger.exception("Input listener error")

    def callbacks_connect(self):
        """Connect the callback functions."""
        try:
            self.logger.debug("Connecting MQTT callback functions")
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.logger.debug("MQTT callback functions connected")
        except:
            self.logger.error("Unable to connect mqtt callback functions")

    def connect(self):
        """Set up the connection to the MQTT Server."""
        try:
            self.client.connect(
                self.mqtt_hostname,
                port=self.mqtt_port,
                keepalive=self.mqtt_keepalive)
            self.logger.info(f"Connected to {self.mqtt_hostname} as {self.mqtt_clientid}")
        except:
            self.logger.error(f"Could not connect to mqtt host: {self.mqtt_hostname}:{self.mqtt_port}")

    def subscribe(self):
        """Set up the subscriptions to the proper MQTT channels to listen to."""
        try:
            for channel in self.channels_measurement:
                self.logger.debug(f"Subscribing to MQTT topic '{self.channels_measurement[channel].name}'")
                self.client.subscribe(self.options_channels['subscribe_topic'][channel])
        except:
            self.logger.error(f"Could not subscribe to MQTT channel '{self.mqtt_channel}'")

    def on_connect(self, client, obj, flags, rc):
        self.logger.debug(f"Connected: {rc}")
        self.subscribe()

    def on_disconnect(self, client, userdata, rc):
        self.logger.debug(f"Disconnected: {rc}")

    def on_subscribe(self, client, obj, mid, granted_qos):
        self.logger.debug(f"Subscribed to mqtt topic: {self.mqtt_channel}, {mid}, {granted_qos}")

    def on_log(self, mqttc, obj, level, string):
        self.logger.info(f"Log: {string}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            self.logger.debug(f"Received message: topic: {msg.topic}, payload: {payload}")
        except Exception as exc:
            self.logger.error(f"Payload could not be decoded: {exc}")
            return

        datetime_utc = datetime.datetime.utcnow()
        measurement = {}
        channel = None
        for each_channel in self.channels_measurement:
            if self.options_channels['subscribe_topic'][each_channel] == msg.topic:
                self.logger.debug(f"Found channel {each_channel} with topic '{self.options_channels['subscribe_topic'][each_channel]}'")
                channel = each_channel

        if channel is None:
            self.logger.error(f"Could not determine channel for topic '{msg.topic}'")
            return

        try:
            value = float(payload)
            self.logger.debug(f"Payload represents a float: {value}")
            measurement[channel] = {}
            measurement[channel]['measurement'] = self.channels_measurement[channel].measurement
            measurement[channel]['unit'] = self.channels_measurement[channel].unit
            measurement[channel]['value'] = value
            measurement[channel]['timestamp_utc'] = datetime_utc
            measurement = self.check_conversion(channel, measurement)

            if measurement:
                message, measurement = run_input_actions(self.unique_id, "", measurement, self.log_level_debug)

                self.logger.debug(f"Adding measurement to influxdb: {measurement}")
                add_measurements_influxdb(
                    self.unique_id,
                    measurement,
                    use_same_timestamp=INPUT_INFORMATION['measurements_use_same_timestamp'])
        except Exception as err:
            self.logger.error(f"Error processing message payload '{payload}': {err}")

    def check_conversion(self, channel, measurement):
        # Convert value/unit is conversion_id present and valid
        try:
            if self.channels_conversion[channel]:
                conversion = db_retrieve_table_daemon(
                    Conversion,
                    unique_id=self.channels_measurement[channel].conversion_id)
                if conversion:
                    meas = parse_measurement(
                        self.channels_conversion[channel],
                        self.channels_measurement[channel],
                        measurement,
                        channel,
                        measurement[channel],
                        timestamp=measurement[channel]['timestamp_utc'])

                    measurement[channel]['measurement'] = meas[channel]['measurement']
                    measurement[channel]['unit'] = meas[channel]['unit']
                    measurement[channel]['value'] = meas[channel]['value']
        except:
            self.logger.exception("Checking conversion")

        return measurement

    def stop_input(self):
        """Called when Input is deactivated."""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
