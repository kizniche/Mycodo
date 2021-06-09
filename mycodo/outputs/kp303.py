# coding=utf-8
#
# kp303.py - Output for KP303
#
import asyncio
import threading
import time

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    1: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    2: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'name': 'Outlet 1',
        'measurements': [0]
    },
    1: {
        'types': ['on_off'],
        'name': 'Outlet 2',
        'measurements': [1]
    },
    2: {
        'types': ['on_off'],
        'name': 'Outlet 3',
        'measurements': [2]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'kp303',
    'output_name': "KP303 Kasa Smart WiFi Power Strip",
    'output_manufacturer': 'TP-Link',
    'input_library': 'python-kasa',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.tp-link.com/au/home-networking/smart-plug/kp303/',

    'message': 'This output controls the 3 outlets of the Kasa KP303 Smart WiFi Power Strip.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['MYCODO'],

    'dependencies_module': [
        ('pip-pypi', 'kasa', 'python-kasa==0.4.0.dev2')
    ],

    'custom_options': [
        {
            'id': 'plug_address',
            'type': 'text',
            'default_value': '192.168.0.50',
            'required': True,
            'name': TRANSLATIONS['host']['title'],
            'phrase': TRANSLATIONS['host']['phrase']
        },
        {
            'id': 'status_update_period',
            'type': 'integer',
            'default_value': 60,
            'constraints_pass': constraints_pass_positive_value,
            'required': True,
            'name': 'Status Update (Sec)',
            'phrase': 'The period (seconds) between checking if connected and output states.'
        }
    ],


    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': 'Outlet Name',
            'required': True,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
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
            'id': 'trigger_functions_startup',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Trigger Functions at Startup'),
            'phrase': 'Whether to trigger functions when the output switches at startup'
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
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.strip = None
        self.output_setup = False
        self.outlet_switching = False
        self.status_thread = None
        self.outlet_status_checking = False
        self.timer_status_check = time.time()

        self.plug_address = None
        self.status_update_period = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if not self.plug_address:
            self.logger.error("Plug address must be set")
            return

        try:
            self.try_connect()

            self.status_thread = threading.Thread(target=self.status_update)
            self.status_thread.start()

            if self.output_setup:
                self.logger.debug('Strip setup: {}'.format(self.strip.hw_info))
                for channel in channels_dict:
                    if self.options_channels['state_startup'][channel] == 1:
                        self.output_switch("on", output_channel=channel)
                    elif self.options_channels['state_startup'][channel] == 0:
                        self.output_switch("off", output_channel=channel)
                    self.logger.debug('Strip children: {}'.format(self.strip.children[channel]))
        except Exception as e:
            self.logger.error("setup_output() Error: {err}".format(err=e))

    def try_connect(self):
        try:
            from kasa import SmartStrip

            self.strip = SmartStrip(self.plug_address)
            asyncio.run(self.strip.update())
            self.output_setup = True
        except Exception as e:
            self.logger.error("Output was unable to be setup: {err}".format(err=e))

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            self.logger.error('Output not set up.')
            return

        while self.outlet_status_checking and self.running:
            time.sleep(0.1)

        try:
            self.outlet_switching = True
            if state == 'on':
                asyncio.run(self.strip.children[output_channel].turn_on())
                self.output_states[output_channel] = True
            elif state == 'off':
                asyncio.run(self.strip.children[output_channel].turn_off())
                self.output_states[output_channel] = False
            msg = 'success'
        except Exception as e:
            msg = "State change error: {}".format(e)
            self.logger.error(msg)
            self.output_setup = False
        finally:
            self.outlet_switching = False
        return msg

    def is_on(self, output_channel=None):
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
            for channel in channels_dict:
                if self.options_channels['state_shutdown'][channel] == 1:
                    self.output_switch('on', output_channel=channel)
                elif self.options_channels['state_shutdown'][channel] == 0:
                    self.output_switch('off', output_channel=channel)
        self.running = False

    def status_update(self):
        while self.running:
            if self.timer_status_check < time.time():

                while self.timer_status_check < time.time():
                    self.timer_status_check += self.status_update_period

                while self.outlet_switching and self.running:
                    time.sleep(0.1)
                self.outlet_status_checking = True
                self.logger.debug("Checking state of outlets")

                if not self.output_setup:
                    self.try_connect()
                    if not self.output_setup:
                        self.logger.debug("Could not connect to power strip")

                try:
                    if self.output_setup:
                        asyncio.run(self.strip.update())
                        for channel in channels_dict:
                            if self.strip.children[channel].is_on:
                                self.output_states[channel] = True
                            else:
                                self.output_states[channel] = False
                except Exception as e:
                    self.logger.debug("Could not query power strip status: {}".format(e))
                    self.output_setup = False
                finally:
                    self.outlet_status_checking = False

            time.sleep(1)
