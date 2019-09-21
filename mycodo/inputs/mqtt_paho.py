# coding=utf-8
import datetime

from flask_babel import lazy_gettext

from mycodo.databases.models import Conversion
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import parse_measurement

# Measurements
measurements_dict = {}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MQTT_PAHO',
    'input_manufacturer': 'Mycodo',
    'input_name': 'MQTT Protocol (paho)',
    'measurements_name': 'Variable measurements',
    'measurements_dict': measurements_dict,
    'measurements_variable_amount': True,
    'measurements_use_same_timestamp': False,
    'listener': True,

    'options_enabled': [
        'custom_options',
        'measurements_select',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo'],

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt')],

    'custom_options': [
        {
            'id': 'mqtt_hostname',
            'type': 'text',
            'default_value': 'localhost',
            'required': True,
            'name': lazy_gettext('Hostname'),
            'phrase': lazy_gettext('The hostname of the MQTT server')
        },
        {
            'id': 'mqtt_port',
            'type': 'integer',
            'default_value': 1883,
            'required': True,
            'name': lazy_gettext('Port'),
            'phrase': lazy_gettext('The port of the MQTT server')
        },
        {
            'id': 'mqtt_keepalive',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'name': lazy_gettext('Keep Alive'),
            'phrase': lazy_gettext('Maximum amount of time between received signals. Set to 0 to disable.')
        },
        {
            'id': 'mqtt_clientid',
            'type': 'text',
            'default_value': 'mycodo_mqtt_client',
            'required': True,
            'name': lazy_gettext('Client ID'),
            'phrase': lazy_gettext('Unique client ID for connecting to the MQTT server')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that retrieves stored data from The Things Network """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        # Initialize custom options
        self.mqtt_hostname = None
        self.mqtt_port = None
        self.mqtt_channel = None
        self.mqtt_keepalive = None
        self.mqtt_clientid = None
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            import paho.mqtt.client as mqtt

            # Create a client instance
            self.logger.debug("Client created with ID {}".format(
                self.mqtt_clientid))
            self.client = mqtt.Client(self.mqtt_clientid)

    def callbacks_connect(self):
        """ Connect the callback functions """
        try:
            self.logger.debug("Connecting MQTT callback functions")
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect
            self.logger.debug("MQTT callback functions connected")
        except:
            self.logger.error("Unable to connect mqtt callback functions")

    def connect(self):
        """ Set up the connection to the MQTT Server """
        try:
            self.client.connect(
                self.mqtt_hostname,
                port=self.mqtt_port,
                keepalive=self.mqtt_keepalive)
            self.logger.info("Connected to {} as {}".format(
                self.mqtt_hostname, self.mqtt_clientid))
        except:
            self.logger.error("Could not connect to mqtt host: {}:{}".format(
                self.mqtt_hostname, self.mqtt_port))

    def subscribe(self):
        """ Set up the subscriptions to the proper MQTT channels to listen to """
        try:
            for channel in self.channels_measurement:
                self.client.subscribe(self.channels_measurement[channel].name)
                self.logger.debug("Subscribed to MQTT channel '{}'".format(
                    self.channels_measurement[channel].name))
        except:
            self.logger.error("Could not subscribe to MQTT channel '{}'".format(
                self.mqtt_channel))

    def on_connect(self, client, obj, flags, rc):
        self.logger.debug("Connected to '{}', rc: {}".format(
            self.mqtt_channel, rc))

    def on_subscribe(self, client, obj, mid, granted_qos):
        self.logger.debug("Subscribing to mqtt topic: {}, {}, {}".format(
            self.mqtt_channel, mid, granted_qos))

    def on_log(self, mqttc, obj, level, string):
        self.logger.info("Log: {}".format(string))

    def on_message(self, client, userdata, msg):
        datetime_utc = datetime.datetime.utcnow()
        self.logger.debug("Message received: Channel: {}, Value: {}".format(
            msg.topic, msg.payload.decode()))
        measurement = {}
        channel = None
        for each_channel in self.channels_measurement:
            if self.channels_measurement[each_channel].name == msg.topic:
                channel = each_channel

        if channel is None:
            self.logger.error("Could not determine channel for '{}'".format(msg.topic))
            return

        try:
            value = float(msg.payload.decode())
        except Exception:
            self.logger.exception("Message doesn't represent a float value.")
            return

        # Original value/unit
        measurement[channel] = {}
        measurement[channel]['measurement'] = self.channels_measurement[channel].measurement
        measurement[channel]['unit'] = self.channels_measurement[channel].unit
        measurement[channel]['value'] = value
        measurement[channel]['timestamp_utc'] = datetime_utc

        self.add_measurement_influxdb(channel, measurement)

    def add_measurement_influxdb(self, channel, measurement):
        # Convert value/unit is conversion_id present and valid
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

        if measurement:
            self.logger.debug(
                "Adding measurement to influxdb: {}".format(measurement))
            add_measurements_influxdb(
                self.unique_id,
                measurement,
                use_same_timestamp=INPUT_INFORMATION['measurements_use_same_timestamp'])

    def on_disconnect(self, client, userdata, rc=0):
        self.logger.debug("Disconnected result code {}".format(rc))

    def stop_input(self):
        """ Called when Input is deactivated """
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def listener(self):
        self.callbacks_connect()
        self.connect()
        self.subscribe()
        self.client.loop_start()
