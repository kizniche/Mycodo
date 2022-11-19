# coding=utf-8
#
# on_off_kp115.py - Output for KP115
#
import asyncio
import random
import time
import traceback
from threading import Event
from threading import Thread

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
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

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'output_kasa_plugs',
    'output_name': "{}: Kasa WiFi Power Plug".format(lazy_gettext('On/Off')),
    'output_manufacturer': 'TP-Link',
    'input_library': 'python-kasa',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.kasasmart.com/us/products/smart-plugs/kasa-smart-plug-slim-energy-monitoring-kp115',

    'message': 'This output controls Kasa WiFi Power Plugs, including the KP105, KP115, KP125, KP401, HS100, HS103, HS105, HS107, and HS110. Note: if you see errors in the daemon log about the server starting, try changing the Asyncio RPC Port to another port.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'kasa', 'python-kasa==0.5.0'),
        ('pip-pypi', 'aio_msgpack_rpc', 'aio_msgpack_rpc==0.2.0')
    ],

    'interfaces': ['IP'],

    'custom_options': [
        {
            'id': 'plug_address',
            'type': 'text',
            'default_value': '0.0.0.0',
            'required': True,
            'name': TRANSLATIONS['host']['title'],
            'phrase': TRANSLATIONS['host']['phrase']
        },
        {
            'id': 'status_update_period',
            'type': 'integer',
            'default_value': 300,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'required': True,
            'name': 'Status Update (Seconds)',
            'phrase': 'The period between checking if connected and output states. 0 disables.'
        },
        {
            'id': 'asyncio_rpc_port',
            'type': 'integer',
            'default_value': 18000 + random.randint(0, 900),
            'constraints_pass': constraints_pass_positive_value,
            'required': True,
            'name': 'Asyncio RPC Port',
            'phrase': 'The port to start the asyncio RPC server. Must be unique from other Kasa Outputs.'
        }
    ],

    'custom_channel_options': [
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
            'name': "{} ({})".format(lazy_gettext('Current'), lazy_gettext('Amps')),
            'phrase': 'The current draw of the device being controlled'
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates the Kasa KP115/KP125 WiFi Power Plugs."""

    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.strip = None
        self.rpc_server_thread = None
        self.status_thread = None
        self.timer_status_check = time.time()

        self.plug_address = None
        self.status_update_period = None
        self.asyncio_rpc_port = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if not self.plug_address or self.plug_address == "0.0.0.0":
            self.logger.error("Plug address must be set")
            return

        started_evt = Event()

        loop = asyncio.new_event_loop()
        self.rpc_server_thread = Thread(
            target=self.aio_rpc_server, args=(started_evt, loop, self.logger))
        self.rpc_server_thread.start()

        started_evt.wait()  # Wait for thread to either start running or error

        for _ in range(3):  # Attempt to connect 3 times
            self.connect()
            if self.output_setup:
                break
            time.sleep(2)

        if self.output_setup:
            if self.options_channels['state_startup'][0] == 1:
                self.outlet_change(True)
            elif self.options_channels['state_startup'][0] == 0:
                self.outlet_change(False)

            if (self.options_channels['state_startup'][0] in [0, 1] and
                    self.options_channels['trigger_functions_startup'][0]):
                try:
                    self.check_triggers(self.unique_id, output_channel=0)
                except Exception as err:
                    self.logger.error(
                        f"Could not check Trigger for channel 0 of output {self.unique_id}: {err}")

            if self.status_update_period:
                self.status_thread = Thread(target=self.status_update)
                self.status_thread.start()

    def aio_rpc_server(self, started_evt, loop, logger):
        import aio_msgpack_rpc
        from kasa import SmartPlug

        class KasaServer:
            """Communicates with the Kasa power strip"""

            def __init__(self, address_):
                self.strip = None
                self.address = address_

            async def connect(self):
                try:
                    self.strip = SmartPlug(self.address)
                    await self.strip.update()
                    return 0, f'Strip {self.strip.alias}: {self.strip.hw_info}'
                except Exception:
                    return 1, str(traceback.print_exc())

            async def outlet_on(self):
                try:
                    await self.strip.turn_on()
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def outlet_off(self):
                try:
                    await self.strip.turn_off()
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def get_status(self):
                try:
                    await self.strip.update()
                    if self.strip.is_on:
                        channel_stat = True
                    else:
                        channel_stat = False
                    return 0, channel_stat
                except Exception:
                    return 1, str(traceback.print_exc())

        async def main(address, port):
            server = None
            try:
                server = await asyncio.start_server(
                    aio_msgpack_rpc.Server(KasaServer(address)),
                    host="127.0.0.1", port=port)
                started_evt.set()

                while self.running:
                    await asyncio.sleep(0.1)
            except Exception:
                logger.exception("Error starting asyncio RPC server")
                started_evt.set()
            finally:
                if server:
                    server.close()
                else:
                    logger.error("Asyncio RPC server couldn't start")

        logger.info("Starting asyncio RPC server...")

        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main(self.plug_address, self.asyncio_rpc_port))
        except Exception:
            logger.exception("Asyncio RPC server")
        except KeyboardInterrupt:
            pass

        logger.info("Asyncio RPC server ended")

    def connect(self):
        import aio_msgpack_rpc

        async def connect(port):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))
            status, msg = await client.call("connect")
            if status:
                self.logger.error(f"Connecting to power strip: Error: {msg}")
            else:
                self.logger.debug(f"Connecting to power strip: {msg}")
                self.output_setup = True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(connect(self.asyncio_rpc_port))

    def outlet_change(self, state):
        import aio_msgpack_rpc

        async def outlet_change(port, state_):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

            if state_:
                status, msg = await client.call("outlet_on")
            else:
                status, msg = await client.call("outlet_off")

            if status:
                self.logger.error(f"Switching {'ON' if state_ else 'OFF'}: Error: {msg}")
            else:
                self.output_states[0] = state
                self.logger.debug(f"Switching {'ON' if state_ else 'OFF'}: {msg}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(outlet_change(self.asyncio_rpc_port, state))

    def status_update(self):
        import aio_msgpack_rpc

        while self.running:
            if self.timer_status_check < time.time():
                while self.timer_status_check < time.time():
                    self.timer_status_check += self.status_update_period

                self.logger.debug("Checking state of outlets")

                try:
                    async def get_status(port):
                        client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

                        status, msg = await client.call("get_status")
                        if status:
                            self.logger.error(f"Status: Error: {msg}")
                        else:
                            self.logger.debug(f"Status: {msg}")
                            if msg:
                                self.output_states[0] = msg

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    asyncio.get_event_loop()
                    loop.run_until_complete(get_status(self.asyncio_rpc_port))
                except Exception as e:
                    self.logger.error(f"Could not query power strip status: {e}")

            time.sleep(1)

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        try:
            if state == 'on':
                self.outlet_change(True)
            elif state == 'off':
                self.outlet_change(False)
        except Exception as err:
            self.logger.exception(f"State change error: {err}")

    def is_on(self, output_channel=None):
        if self.is_setup():
            return self.output_states[0]

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 1:
                self.output_switch('on')
            elif self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
        self.running = False
