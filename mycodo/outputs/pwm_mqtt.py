# coding=utf-8
#
# pwm_mqtt.py - Output for publishing PWM via MQTT
#
import copy
import math

from flask_babel import lazy_gettext
from sqlalchemy import and_

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_influxdb_single
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.utils import random_alphanumeric

measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

channels_dict = {
    0: {
        'types': ['pwm'],
        'measurements': [0]
    }
}

OUTPUT_INFORMATION = {
    'output_name_unique': 'MQTT_PAHO_PWM',
    'output_name': "{}: MQTT Publish".format(lazy_gettext('PWM')),
    'output_library': 'paho-mqtt',
    'output_manufacturer': 'Mycodo',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['pwm'],

    'url_additional': 'http://www.eclipse.org/paho/',

    'message': 'Publish a PWM value to an MQTT server.',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """Set the Duty Cycle."""
        },
        {
            'id': 'duty_cycle',
            'type': 'float',
            'default_value': 0,
            'name': 'Duty Cycle',
            'phrase': 'The duty cycle to set'
        },
        {
            'id': 'set_duty_cycle',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Set Duty Cycle'
        }
    ],

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
            'default_value': 'client_{}'.format(random_alphanumeric(8)),
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
            'phrase': 'Password for connecting to the server.'
        },
        {
            'id': 'mqtt_use_websockets',
            'type': 'bool',
            'default_value': False,
            'required': False,
            'name': 'Use Websockets',
            'phrase': 'Use websockets to connect to the server.'
        },
        {
            'id': 'round_integer',
            'type': 'select',
            'default_value': 'no',
            'options_select': [
                ('no', 'No Rounding'),
                ('near', 'Round Nearest Whole'),
                ('up', 'Round Up'),
                ('down', 'Round Down')
            ],
            'name': 'Round Integer',
            'phrase': 'Round the payload value to an integer.'
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': '',
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value'),
                ('last_duty_cycle', 'Last Known Value')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state when Mycodo starts'
        },
        {
            'id': 'startup_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Startup Value'),
            'phrase': 'The value when Mycodo starts'
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': '',
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': 'Set the state when Mycodo shuts down'
        },
        {
            'id': 'shutdown_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Shutdown Value'),
            'phrase': 'The value when Mycodo shuts down'
        },
        {
            'id': 'pwm_invert_signal',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Signal'),
            'phrase': 'Invert the PWM signal'
        },
        {
            'id': 'pwm_invert_stored_signal',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Stored Signal'),
            'phrase': 'Invert the value that is saved to the measurement database'
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Current'), lazy_gettext('Amps')),
            'phrase': 'The current draw of the device being controlled'
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.publish = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        import paho.mqtt.publish as publish

        self.publish = publish

        self.setup_output_variables(OUTPUT_INFORMATION)
        self.output_setup = True

        try:
            if self.options_channels['state_startup'][0] == 0:
                self.output_switch('off')
                self.logger.info("PWM turned off (0 % duty cycle)")
            elif self.options_channels['state_startup'][0] == 'set_duty_cycle':
                self.output_switch('on', amount=self.options_channels['startup_value'][0])
                self.logger.info("PWM set to {} % duty cycle (user-specified value)".format(
                    self.options_channels['startup_value'][0]))
            elif self.options_channels['state_startup'][0] == 'last_duty_cycle':
                device_measurement = db_retrieve_table_daemon(DeviceMeasurements).filter(
                    and_(DeviceMeasurements.device_id == self.unique_id,
                         DeviceMeasurements.channel == 0)).first()

                last_measurement = None
                if device_measurement:
                    channel, unit, measurement = return_measurement_info(device_measurement, None)
                    last_measurement = read_influxdb_single(
                        self.unique_id,
                        unit,
                        channel,
                        measure=measurement,
                        value='LAST')

                if last_measurement:
                    self.logger.info(
                        "PWM set to {} % duty cycle (last known value)".format(
                            last_measurement[1]))
                    self.output_switch('on', amount=last_measurement[1])
                else:
                    self.logger.error(
                        "Output instructed at startup to be set to "
                        "the last known duty cycle, but a last known "
                        "duty cycle could not be found in the measurement "
                        "database")
        except Exception as except_msg:
            self.logger.exception("Output was unable to be setup: {err}".format(err=except_msg))

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

            if state == 'on':
                if self.options_channels['pwm_invert_signal'][0]:
                    amount = 100.0 - abs(amount)
            elif state == 'off':
                if self.options_channels['pwm_invert_signal'][0]:
                    amount = 100
                else:
                    amount = 0

            # Round before sending payload
            if self.options_channels['round_integer'][0] == "near":
                amount = int(round(amount))
            elif self.options_channels['round_integer'][0] == "up":
                amount = int(math.ceil(amount))
            elif self.options_channels['round_integer'][0] == "down":
                amount = int(math.floor(amount))

            self.publish.single(
                self.options_channels['topic'][0],
                amount,
                hostname=self.options_channels['hostname'][0],
                port=self.options_channels['port'][0],
                client_id=self.options_channels['clientid'][0],
                keepalive=self.options_channels['keepalive'][0],
                auth=auth_dict,
                transport='websockets' if self.options_channels['mqtt_use_websockets'][0] else 'tcp')

            self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))

            if self.options_channels['pwm_invert_stored_signal'][0]:
                amount = 100.0 - abs(amount)

            self.output_states[output_channel] = amount

            measure_dict[0]['value'] = float(amount)
            add_measurements_influxdb(self.unique_id, measure_dict)

            return "success"
        except Exception as e:
            self.logger.error("State change error: {}".format(e))
            return

    def is_on(self, output_channel=0):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
            elif self.options_channels['state_shutdown'][0] == 'set_duty_cycle':
                self.output_switch('on', amount=self.options_channels['shutdown_value'][0])
        self.running = False

    def set_duty_cycle(self, args_dict):
        if 'duty_cycle' not in args_dict:
            self.logger.error("Cannot set without duty cycle")
            return
        return_str = self.control.output_on(
            self.output.unique_id,
            output_type='pwm',
            amount=args_dict["duty_cycle"],
            output_channel=0)
        return f"Setting duty cycle: {return_str}"
