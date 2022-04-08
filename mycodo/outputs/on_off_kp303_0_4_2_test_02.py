# coding=utf-8
#
# on_off_kp303_0_4_2.py - Output for KP303
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
from mycodo.utils.lockfile import LockFile

# Measurements
measurements_dict = {
    key: {
        'measurement': 'duration_time',
        'unit': 's'
    }
    for key in range(3)
}

channels_dict = {
    key: {
        'types': ['on_off'],
        'name': f'Outlet {key + 1}',
        'measurements': [key]
    }
    for key in range(3)
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'kp303_0_4_2_alt_01',
    'output_name': f"{lazy_gettext('On/Off')}: KP303 Kasa 3-Outlet WiFi Power Strip (python-kasa 0.4.2, TEST #2)",
    'output_manufacturer': 'TP-Link',
    'input_library': 'python-kasa==0.4.2',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.tp-link.com/au/home-networking/smart-plug/kp303/',

    'message': 'This output controls the 3 outlets of the Kasa KP303 Smart WiFi Power Strip. This is a variant that uses the latest python-kasa library.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'kasa', 'python-kasa==0.4.2')
    ],

    'interfaces': ['IP'],

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
            'name': 'Status Update (seconds)',
            'phrase': 'The period (seconds) between checking if connected and output states. 0 disables.'
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
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.strip = None
        self.kasa_thread = None
        self.first_connect = True
        self.failed_connect_count = 0
        self.lock_file = {}
        self.lock_timeout = 10
        self.switch_wait = 0.25
        self.timer_status_check = time.time()
        self.plug_address = None
        self.status_update_period = None
        self.change_state = {key: None for key in range(len(channels_dict))}

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if not self.plug_address:
            self.logger.error("Plug address must be set")
            return

        for i in range(len(channels_dict)):
            self.lock_file[i] = f'/var/lock/kasa_{self.plug_address.replace(".", "-")}_{i}'

        self.kasa_thread = threading.Thread(target=asyncio.run, args=(self.thread_kasa(),))
        self.kasa_thread.start()

    async def thread_kasa(self):
        self.logger.debug("thread_kasa")
        while self.running:
            now = time.time()

            if not self.output_setup:
                await self.connect()

            if self.output_setup:
                for channel in range(len(channels_dict)):
                    if self.change_state[channel] is not None:
                        self.logger.info(f"change_state, channel {channel}: {self.change_state[channel]}")
                        if self.change_state[channel]:
                            await self.strip.children[channel].turn_on()
                        else:
                            await self.strip.children[channel].turn_off()
                        self.output_states[channel] = self.change_state[channel]
                        await self.strip.update()
                        self.change_state[channel] = None

                if self.timer_status_check < now:
                    while self.timer_status_check < now:
                        self.timer_status_check += self.status_update_period
                    try:
                        await self.strip.update()
                        for channel in channels_dict:
                            if self.strip.children[channel].is_on:
                                self.output_states[channel] = True
                            else:
                                self.output_states[channel] = False
                    except Exception as err:
                        self.logger.error(
                            f"get_status() raised an exception when taking a reading: {err}")

            await asyncio.sleep(0.1)

    async def connect(self):
        self.logger.debug("try_connect")
        from kasa import SmartStrip

        try:
            self.strip = SmartStrip(self.plug_address)
            await self.strip.update()
            self.logger.debug(f'Strip {self.strip.alias}: {self.strip.hw_info}')
            self.output_setup = True
            self.failed_connect_count = 0
        except Exception as err:
            self.logger.error(f"Output was unable to be setup: {err}")
            self.failed_connect_count += 1
            if self.failed_connect_count > 4:
                if self.failed_connect_count == 5:
                    self.logger.error(
                        "Failed to connect 5 times. Reducing reconnect attempt interval to 60 seconds.")
                time.sleep(60)
            else:
                time.sleep(5)
            return

        if self.first_connect:
            self.first_connect = False
            for channel in channels_dict:
                if channel not in self.output_states:
                    self.output_states[channel] = None
                if self.options_channels['state_startup'][channel] == 1:
                    await self.strip.children[channel].turn_on()
                elif self.options_channels['state_startup'][channel] == 0:
                    await self.strip.children[channel].turn_off()
                self.logger.debug(f'Strip children: {self.strip.children[channel]}')


    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        try:
            if state == 'on':
                lf = LockFile()
                if lf.lock_acquire(self.lock_file[output_channel], timeout=self.lock_timeout):
                    try:
                        now = time.time()
                        self.change_state[output_channel] = True
                        while self.change_state[output_channel] is not None and time.time() < now + 10:
                            time.sleep(0.1)
                    finally:
                        lf.lock_release(self.lock_file[output_channel])
            elif state == 'off':
                lf = LockFile()
                if lf.lock_acquire(self.lock_file[output_channel], timeout=self.lock_timeout):
                    try:
                        now = time.time()
                        self.change_state[output_channel] = False
                        while self.change_state[output_channel] is not None and time.time() < now + 10:
                            time.sleep(0.1)
                    finally:
                        lf.lock_release(self.lock_file[output_channel])
        except Exception as err:
            self.logger.exception(f"State change error: {err}")

    def is_on(self, output_channel=None):
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
            for channel in channels_dict:
                if self.options_channels['state_shutdown'][channel] == 1:
                    self.output_switch('on', output_channel=channel)
                elif self.options_channels['state_shutdown'][channel] == 0:
                    self.output_switch('off', output_channel=channel)
        self.running = False
