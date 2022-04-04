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
    'output_name_unique': 'kp303_0_4_2',
    'output_name': f"{lazy_gettext('On/Off')}: KP303 Kasa Smart WiFi Power Strip (python-kasa 0.4.2)",
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
            'name': 'Status Update (Sec)',
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
        self.lock_file = None
        self.lock_timeout = 10
        self.switch_wait = 0.25
        self.status_thread = None
        self.timer_status_check = time.time()

        self.plug_address = None
        self.status_update_period = None

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

        self.lock_file = f'/var/lock/kasa_{self.plug_address.replace(".", "-")}'

        try:
            asyncio.run(self.try_connect())

            if self.status_update_period:
                self.status_thread = threading.Thread(target=self.status_update)
                self.status_thread.start()

            if self.output_setup:
                for channel in channels_dict:
                    if channel not in self.output_states:
                        self.output_states[channel] = None
                    if self.options_channels['state_startup'][channel] == 1:
                        self.output_switch("on", output_channel=channel)
                    elif self.options_channels['state_startup'][channel] == 0:
                        self.output_switch("off", output_channel=channel)
                    self.logger.debug(f'Strip children: {self.strip.children[channel]}')
        except Exception as err:
            self.logger.exception(f"initialize() Error: {err}")

    async def try_connect(self):
        from kasa import SmartStrip

        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=self.lock_timeout):
            try:
                self.strip = SmartStrip(self.plug_address)
                await self.strip.update()
                self.logger.debug(f'Strip {self.strip.alias}: {self.strip.hw_info}')
                self.output_setup = True
            except Exception as err:
                self.logger.error(f"Output was unable to be setup: {err}")
            finally:
                time.sleep(self.switch_wait)
                lf.lock_release(self.lock_file)

    def change_outlet_state_try(self, channel, state):
        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=self.lock_timeout):
            try:
                loops = 4
                msg = None
                for i in range(loops):
                    try:
                        asyncio.run(self.change_outlet_state(channel, state))
                        msg = "success"
                        break
                    except Exception as err:
                        msg = "State change error: {}".format(err)
                        if i + 1 < loops:
                            time.sleep(1.5)
                return msg
            finally:
                time.sleep(self.switch_wait)
                lf.lock_release(self.lock_file)

    async def change_outlet_state(self, channel, state):
        from kasa import SmartStrip

        self.strip = SmartStrip(self.plug_address)
        await self.strip.update()
        if state:
            msg = await self.strip.children[channel].turn_on()
            self.output_states[channel] = True
        else:
            msg =  await self.strip.children[channel].turn_off()
            self.output_states[channel] = False
        await self.strip.update()

        return msg

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        msg = None
        try:
            if state == 'on':
                msg = self.change_outlet_state_try(output_channel, True)
            elif state == 'off':
                msg = self.change_outlet_state_try(output_channel, False)
        except Exception as err:
            self.logger.error(f"State change error: {err}")

        self.logger.debug(f"State change: {msg}")

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
        """Called when Output is stopped."""
        if self.is_setup():
            for channel in channels_dict:
                if self.options_channels['state_shutdown'][channel] == 1:
                    self.output_switch('on', output_channel=channel)
                elif self.options_channels['state_shutdown'][channel] == 0:
                    self.output_switch('off', output_channel=channel)
        self.running = False

    async def get_status(self):
        from kasa import SmartStrip

        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=self.lock_timeout):
            try:
                self.strip = SmartStrip(self.plug_address)
                await self.strip.update()
                for channel in channels_dict:
                    if self.strip.children[channel].is_on:
                        self.output_states[channel] = True
                    else:
                        self.output_states[channel] = False
            except Exception as err:
                self.logger.error(
                    f"get_status() raised an exception when taking a reading: {err}")
                return 'error', err
            finally:
                time.sleep(self.switch_wait)
                lf.lock_release(self.lock_file)

    def status_update(self):
        while self.running:
            if self.timer_status_check < time.time():
                while self.timer_status_check < time.time():
                    self.timer_status_check += self.status_update_period

                self.logger.debug("Checking state of outlets")

                try:
                    asyncio.run(self.get_status())
                except Exception as e:
                    self.logger.error(f"Could not query power strip status: {e}")

            time.sleep(1)
