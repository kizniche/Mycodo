# coding=utf-8
#
# remote_output_pwm.py - Output for controlling a remote Mycodo PWM Output
#
import copy
import json
import time
from threading import Thread

from flask_babel import lazy_gettext
from sqlalchemy import and_

from mycodo.databases.models import DeviceMeasurements, OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb, read_influxdb_single
from mycodo.utils.system_pi import return_measurement_info

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

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'remote_output_pwm',
    'output_name': "{} Mycodo Output: {}".format(lazy_gettext('Remote'), lazy_gettext('PWM')),
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_library': 'requests',
    'output_types': ['pwm'],

    'message': 'This Output allows remote control of another Mycodo PWM Output over a network using the API.',

    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'requests', 'requests==2.31.0')
    ],

    'interfaces': ['API'],

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

    'custom_options_message': 'Enter the API key and IP/Host address of your remote Mycodo and save to populate the Remote Output dropdown selection. You will need to refresh the page after saving for the Remote Mycodo Output dropdown to populate. Configure which Remote Mycodo Output you would like to control and save again. You must select an On/Off Output Channel for this to work. Selecting a PWM, Volume, or other channel will cause an error.',

    'custom_options': [
        {
            'id': 'host',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': "Remote Mycodo Host",
            'phrase': lazy_gettext('The host or IP address of the remote Mycodo')
        },
        {
            'id': 'api_key',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': "Remote Mycodo API Key",
            'phrase': lazy_gettext('The API key of the remote Mycodo')
        },
        {
            'id': 'state_query_period',
            'type': 'integer',
            'default_value': 120,
            'name': "State Query Period (Seconds)",
            'phrase': 'How often to query the state of the output'
        }
    ],

    'custom_channel_options': [
        {
            'id': 'remote_output',
            'type': 'select_custom_choices',
            'default_value': '',
            'name': 'Remote Mycodo Output',
            'phrase': 'The Remote Mycodo Output to control'
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
            'name': "Start Duty Cycle",
            'phrase': 'The duty cycle to set at startup, if enabled'
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
            'name': "Shutdown Duty Cycle",
            'phrase': 'The duty cycle to set at shutdown, if enabled'
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
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.api_key = None
        self.host = None
        self.state_query_period = None

        self.api_output = None
        self.query_timer = 0

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if self.api_key and self.host:
            self.get_remote_output_information()
            if self.api_output:
                self.parse_remote_output_info()
            else:
                self.output_setup = False

        try:
            if self.output_setup:
                # Set up thread to query output states
                query_states = Thread(target=self.remote_state_query)
                query_states.daemon = True
                query_states.start()


                state_string = ""
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
            self.logger.exception(
                "Output was unable to be setup: {err}".format(err=except_msg))

    def remote_state_query(self):
        """Periodically query output states"""
        while self.running:
            now = time.time()

            if self.state_query_period and self.query_timer < now:
                self.get_remote_output_information()
                self.parse_output_state_info()
                self.query_timer = now + self.state_query_period

            time.sleep(1)

    def get_remote_output_information(self):
        import requests

        endpoint = 'outputs'
        url = 'https://{ip}/api/{ep}'.format(ip=self.host, ep=endpoint)
        headers = {
            'Accept': 'application/vnd.mycodo.v1+json',
            'X-API-KEY': self.api_key
        }

        response = requests.get(url, headers=headers, verify=False)
        self.logger.debug(f"Response Status: {response.status_code}")
        self.logger.debug(f"Response Headers: {response.headers}")

        try:
            response_dict = json.loads(response.text)
        except:
            response_dict = {}
        self.logger.debug(f"Response Dictionary: {response_dict}")

        if response.status_code != 200:
            self.logger.error("Response Status was not 200")
            self.api_output = None
            return

        self.api_output = response_dict

    def parse_remote_output_info(self):
        remote_output_choices = []

        if 'output devices' in self.api_output and self.api_output['output devices']:
            self.output_setup = True
            for each_out in self.api_output['output devices']:
                if ('unique_id' in each_out and
                        'output channels' in self.api_output and
                        self.api_output['output channels']):
                    for each_chan in self.api_output['output channels']:
                        if each_out["unique_id"] == each_chan["output_id"]:
                            name = f'{each_out["name"]}: [{each_out["interface"]}] CH{each_chan["channel"]}'
                            if each_chan['name']:
                                name += f': {each_chan["name"]}'
                            remote_output_choices.append(
                                (f'{each_out["unique_id"]},{each_chan["unique_id"]}', name))

        self.logger.debug(f"Remote Outputs: {remote_output_choices}")

        if self.output_setup:
            for each_chan in channels_dict:
                self.set_custom_channel_option(each_chan, "remote_output_choices", remote_output_choices)

    def parse_output_state_info(self):
        if not self.output_setup:
            self.logger.error("Output not set up, can't parse API info")
            return

        for each_chan in channels_dict:
            if ('output states' in self.api_output and
                    self.options_channels['remote_output'][each_chan] and
                    ',' in self.options_channels['remote_output'][each_chan]):
                output_unique_id = self.options_channels['remote_output'][each_chan].split(",")[0]
                channel_unique_id = self.options_channels['remote_output'][each_chan].split(",")[1]

                device_channel = self.get_channel_entry_from_id(channel_unique_id)
                if device_channel is None:
                    continue

                if (output_unique_id in self.api_output['output states'] and
                        str(device_channel) in self.api_output['output states'][output_unique_id]):
                    if self.api_output['output states'][output_unique_id][str(device_channel)]:
                        try:
                            self.output_states[each_chan] = float(
                                self.api_output['output states'][output_unique_id][str(device_channel)])
                        except:
                            self.output_states[each_chan] = None

    def send_remote_output(self, channel, state):
        import requests

        if (not self.options_channels['remote_output'][channel] or
                ',' not in self.options_channels['remote_output'][channel]):
            return

        output_unique_id = self.options_channels['remote_output'][channel].split(",")[0]
        channel_unique_id = self.options_channels['remote_output'][channel].split(",")[1]

        device_channel = self.get_channel_entry_from_id(channel_unique_id)
        if device_channel is None:
            return

        endpoint = f'outputs/{output_unique_id}'
        url = 'https://{ip}/api/{ep}'.format(ip=self.host, ep=endpoint)
        headers = {
            'Accept': 'application/vnd.mycodo.v1+json',
            'X-API-KEY': self.api_key
        }

        data = {
            "channel": device_channel,
            "duty_cycle": state
        }

        response = requests.post(url, json=data, headers=headers, verify=False)
        self.logger.debug(f"Response Status: {response.status_code}")
        self.logger.debug(f"Response Headers: {response.headers}")

        try:
            response_dict = json.loads(response.text)
        except:
            response_dict = {}
        self.logger.debug(f"Response Dictionary: {response_dict}")

        if response.status_code != 200:
            self.logger.error("Response Status was not 200")
            return

        if 'message' in response_dict and 'Success' in response_dict['message']:
            self.output_states[channel] = state
        else:
            self.logger.error("Did not receive success message from API")

    def get_channel_entry_from_id(self, channel_id):
        if not self.api_output or 'output channels' not in self.api_output:
            return

        for channel in self.api_output['output channels']:
            if channel_id == channel['unique_id']:
                return channel['channel']

        self.logger.error("Could not determine channel table.")

    def output_switch(self, state, output_type=None, amount=None, output_channel=0):
        measure_dict = copy.deepcopy(measurements_dict)

        if state == 'on':
            if self.options_channels['pwm_invert_signal'][output_channel]:
                amount = 100.0 - abs(amount)
        elif state == 'off':
            if self.options_channels['pwm_invert_signal'][output_channel]:
                amount = 100
            else:
                amount = 0

        self.send_remote_output(output_channel, amount)

        self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))

        if self.options_channels['pwm_invert_stored_signal'][output_channel]:
            amount = 100.0 - abs(amount)

        measure_dict[0]['value'] = amount
        add_measurements_influxdb(self.unique_id, measure_dict)

        return "success"

    def is_on(self, output_channel=0):
        if self.is_setup():
            try:
                return self.output_states[output_channel]
            except Exception as e:
                self.logger.error("Status check error: {}".format(e))

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            for channel in channels_dict:
                if self.options_channels['state_shutdown'][channel] == 0:
                    self.output_switch('off')
                elif self.options_channels['state_shutdown'][channel] == 'set_duty_cycle':
                    self.output_switch('on', amount=self.options_channels['shutdown_value'][channel])
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
