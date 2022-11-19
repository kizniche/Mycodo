# coding=utf-8
#
# on_off_color_kasa_kl125.py - Output for KL125
#
import asyncio
import copy
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
from mycodo.utils.influx import add_measurements_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    1: {
        'measurement': 'brightness',
        'unit': 'percent'
    },
    2: {
        'measurement': 'color_temperature',
        'unit': 'K'
    },
    3: {
        'measurement': 'hue',
        'unit': 'degree'
    },
    4: {
        'measurement': 'saturation',
        'unit': 'percent'
    }
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'name': f'Bulb',
        'measurements': [0, 1, 2, 3, 4]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'output_kasa_rgb_bulbs',
    'output_name': "{}: Kasa WiFi RGB Light Bulb".format(lazy_gettext('On/Off')),
    'output_manufacturer': 'TP-Link',
    'input_library': 'python-kasa',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.kasasmart.com/us/products/smart-lighting/kasa-smart-light-bulb-multicolor-kl125',

    'message': 'This output controls the the Kasa WiFi Light Bulbs, including the KL125, KL130, and KL135. Note: if you see errors in the daemon log about the server starting, try changing the Asyncio RPC Port to another port.',

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

    'custom_commands_message':
        'The Hue, Saturation, Brightness, and Color Temperature can be set.',

    'custom_commands': [
        {
            'id': 'brightness_transition_ms',
            'type': 'integer',
            'default_value': '0',
            'name': "Transition ({})".format(lazy_gettext('Milliseconds')),
            'phrase': 'The hsv transition period'
        },
        {
            'id': 'brightness',
            'type': 'integer',
            'default_value': '',
            'name': "{} ({})".format(lazy_gettext('Brightness'), lazy_gettext('Percent')),
            'phrase': 'The brightness to set, in percent (0 - 100)'
        },
        {
            'id': 'set_brightness',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Set')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'hue_transition_ms',
            'type': 'integer',
            'default_value': '0',
            'name': "Transition ({})".format(lazy_gettext('Milliseconds')),
            'phrase': 'The hsv transition period'
        },
        {
            'id': 'hue',
            'type': 'integer',
            'default_value': '',
            'name': "{} ({})".format(lazy_gettext('Hue'), lazy_gettext('Degree')),
            'phrase': 'The hue to set, in degrees (0 - 360)'
        },
        {
            'id': 'set_hue',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Set')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'saturation_transition_ms',
            'type': 'integer',
            'default_value': '0',
            'name': "Transition ({})".format(lazy_gettext('Milliseconds')),
            'phrase': 'The hsv transition period'
        },
        {
            'id': 'saturation',
            'type': 'integer',
            'default_value': '',
            'name': "{} ({})".format(lazy_gettext('Saturation'), lazy_gettext('Percent')),
            'phrase': 'The saturation to set, in percent (0 - 100)'
        },
        {
            'id': 'set_saturation',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Set')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'color_temperature_transition_ms',
            'type': 'integer',
            'default_value': '0',
            'name': "Transition ({})".format(lazy_gettext('Milliseconds')),
            'phrase': 'The hsv transition period'
        },
        {
            'id': 'color_temperature',
            'type': 'integer',
            'default_value': '',
            'name': "{} ({})".format(lazy_gettext('Color Temperature'), lazy_gettext('Kelvin')),
            'phrase': 'The color temperature to set, in degrees Kelvin'
        },
        {
            'id': 'set_color_temperature',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Set')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'hsv_transition_ms',
            'type': 'integer',
            'default_value': '0',
            'name': "Transition ({})".format(lazy_gettext('Milliseconds')),
            'phrase': 'The hsv transition period'
        },
        {
            'id': 'hsv',
            'type': 'text',
            'default_value': '220, 20, 45',
            'name': "HSV",
            'phrase': 'The hue, saturation, brightness to set, e.g. "200, 20, 50"'
        },
        {
            'id': 'set_hsv',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Set')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'on_transition_ms',
            'type': 'integer',
            'default_value': '1000',
            'name': "Transition ({})".format(lazy_gettext('Milliseconds')),
            'phrase': 'The transition period'
        },
        {
            'id': 'turn_on',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('On')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'off_transition_ms',
            'type': 'integer',
            'default_value': '1000',
            'name': "Transition ({})".format(lazy_gettext('Milliseconds')),
            'phrase': 'The transition period'
        },
        {
            'id': 'turn_off',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Off')
        }
    ],

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
    """An output support class that operates the Kasa KL125 WiFi Light Bulb."""

    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.bulb = None
        self.rpc_server_thread = None
        self.status_thread = None
        self.timer_status_check = time.time()

        self.plug_address = None
        self.status_update_period = None
        self.asyncio_rpc_port = None

        self.changing_state = False

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
                self.bulb_change(True)
            elif self.options_channels['state_startup'][0] == 0:
                self.bulb_change(False)

            if self.status_update_period:
                self.status_thread = Thread(target=self.status_update)
                self.status_thread.start()

        if self.options_channels['trigger_functions_startup'][0]:
            try:
                self.check_triggers(self.unique_id, output_channel=0)
            except Exception as err:
                self.logger.error(
                    f"Could not check Trigger for channel 0 of output {self.unique_id}: {err}")

    def aio_rpc_server(self, started_evt, loop, logger):
        import aio_msgpack_rpc
        from kasa import SmartBulb

        class KasaServer:
            """Communicates with the Kasa power strip"""

            def __init__(self, address_):
                self.bulb = None
                self.address = address_

                self.hue = None
                self.saturation = None
                self.brightness = None

            async def connect(self):
                try:
                    self.bulb = SmartBulb(self.address)
                    await self.bulb.update()
                    return 0, f'Bulb {self.bulb.alias}: {self.bulb.hw_info}'
                except Exception:
                    return 1, str(traceback.print_exc())

            async def bulb_on(self, transition=0):
                try:
                    await self.bulb.turn_on(transition=transition)
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def bulb_off(self, transition=0):
                try:
                    await self.bulb.turn_off(transition=transition)
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def bulb_hue(self, hue, transition_ms):
                try:
                    await self.bulb.update()
                    hsv = self.bulb.hsv
                    self.hue = hue
                    self.saturation = hsv[1]
                    self.brightness = hsv[2]
                    await self.bulb.set_hsv(hue, self.saturation, self.brightness, transition=transition_ms)
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def bulb_saturation(self, saturation, transition_ms):
                try:
                    await self.bulb.update()
                    hsv = self.bulb.hsv
                    self.hue = hsv[0]
                    self.saturation = saturation
                    self.brightness = hsv[2]
                    await self.bulb.set_hsv(hsv[0], saturation, hsv[2], transition=transition_ms)
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def bulb_brightness(self, brightness, transition_ms):
                try:
                    self.brightness = brightness
                    await self.bulb.set_brightness(brightness, transition=transition_ms)
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def bulb_hsv(self, hsv, transition_ms):
                try:
                    self.hue = hsv[0]
                    self.saturation = hsv[1]
                    self.brightness = hsv[2]
                    await self.bulb.set_hsv(hsv[0], hsv[1], hsv[2], transition=transition_ms)
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def bulb_color_temperature(self, color_temperature, transition_ms):
                try:
                    await self.bulb.set_color_temp(color_temperature, transition=transition_ms)
                    return 0, "success"
                except Exception:
                    return 1, str(traceback.print_exc())

            async def get_status(self):
                try:
                    await self.bulb.update()
                    stats = {}
                    if self.bulb.is_on:
                        stats["state"] = True
                    else:
                        stats["state"] = False
                    hsv = self.bulb.hsv
                    self.hue = hsv[0]
                    self.saturation = hsv[1]
                    self.brightness = hsv[2]
                    return 0, stats
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

    def bulb_change(self, state, transition=0):
        import aio_msgpack_rpc

        self.changing_state = True
        time.sleep(1)

        async def bulb_change(port, state_, transition_):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

            if state_:
                status, msg = await client.call("bulb_on", transition_)
            else:
                status, msg = await client.call("bulb_off", transition_)

            if status:
                self.logger.error(f"Switching {'ON' if state_ else 'OFF'}: Error: {msg}")
            else:
                self.output_states[0] = state
                self.logger.debug(f"Switching {'ON' if state_ else 'OFF'}: {msg}")

            self.changing_state = False

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(bulb_change(self.asyncio_rpc_port, state, transition))

    def bulb_hue(self, hue, transition_ms):
        import aio_msgpack_rpc

        async def bulb_hue(port, hue_, transition_ms_):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

            status, msg = await client.call("bulb_hue", hue_, transition_ms_)

            self.logger.debug(f"hue {hue_}: {msg}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(bulb_hue(self.asyncio_rpc_port, hue, transition_ms))

    def bulb_saturation(self, saturation, transition_ms):
        import aio_msgpack_rpc

        async def bulb_saturation(port, saturation_, transition_ms_):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

            status, msg = await client.call("bulb_saturation", saturation_, transition_ms_)

            self.logger.debug(f"saturation {saturation_}: {msg}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(bulb_saturation(self.asyncio_rpc_port, saturation, transition_ms))

    def bulb_brightness(self, brightness, transition_ms):
        import aio_msgpack_rpc

        async def bulb_brightness(port, brightness_, transition_ms_):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

            status, msg = await client.call("bulb_brightness", brightness_, transition_ms_)

            self.logger.debug(f"brightness {brightness_}: {msg}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(bulb_brightness(self.asyncio_rpc_port, brightness, transition_ms))

    def bulb_hsv(self, hsv, transition_ms):
        import aio_msgpack_rpc

        async def bulb_hsv(port, hsv_, transition_ms_):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

            status, msg = await client.call("bulb_hsv", hsv_, transition_ms_)

            self.logger.debug(f"hsv {hsv_}: {msg}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(bulb_hsv(self.asyncio_rpc_port, hsv, transition_ms))

    def bulb_color_temperature(self, color_temperature, transition_ms):
        import aio_msgpack_rpc

        async def bulb_color_temperature(port, color_temperature_, transition_ms_):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))

            status, msg = await client.call("bulb_color_temperature", color_temperature_, transition_ms_)

            self.logger.debug(f"color_temperature {color_temperature_}: {msg}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(bulb_color_temperature(self.asyncio_rpc_port, color_temperature, transition_ms))

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
                            self.output_states[0] = msg["state"]

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

        while self.changing_state:
            time.sleep(0.1)

        try:
            if state == 'on':
                self.bulb_change(True)
            elif state == 'off':
                self.bulb_change(False)
        except Exception as err:
            self.logger.exception(f"State change error: {err}")

    def is_on(self, output_channel=0):
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

    def set_hue(self, args_dict):
        while self.changing_state:
            time.sleep(0.1)

        if 'hue' not in args_dict:
            msg = "Cannot set hue without a value"
            self.logger.error(msg)
            return msg
        if not (0 <= args_dict['hue'] <= 360):
            msg = "Hue must be 0 - 360"
            self.logger.error(msg)
            return msg
        if not self.output_states[0]:
            msg = "Cannot set hue when bulb is off"
            self.logger.error(msg)
            return msg

        transition_ms = 0
        if 'hue_transition_ms' in args_dict:
            try:
                ms = int(args_dict['hue_transition_ms'])
                if ms > 0:
                    transition_ms = ms
            except:
                self.logger.error("Could not parse transition period")

        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[3]['value'] = args_dict['hue']
        add_measurements_influxdb(self.unique_id, measure_dict)

        self.bulb_hue(args_dict['hue'], transition_ms)
        return f"Set Hue: {args_dict['hue']}, Transition: {transition_ms} ms"

    def set_saturation(self, args_dict):
        while self.changing_state:
            time.sleep(0.1)

        if 'saturation' not in args_dict:
            msg = "Cannot set saturation without a value"
            self.logger.error(msg)
            return msg
        if not (0 <= args_dict['saturation'] <= 100):
            msg = "Saturation must be 0 - 100"
            self.logger.error(msg)
            return msg
        if not self.output_states[0]:
            msg = "Cannot set saturation when bulb is off"
            self.logger.error(msg)
            return msg

        transition_ms = 0
        if 'saturation_transition_ms' in args_dict:
            try:
                ms = int(args_dict['saturation_transition_ms'])
                if ms > 0:
                    transition_ms = ms
            except:
                self.logger.error("Could not parse transition period")

        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[4]['value'] = args_dict['saturation']
        add_measurements_influxdb(self.unique_id, measure_dict)

        self.bulb_saturation(args_dict['saturation'], transition_ms)
        return f"Set Saturation: {args_dict['saturation']} %, Transition: {transition_ms} ms"

    def set_brightness(self, args_dict):
        while self.changing_state:
            time.sleep(0.1)

        if 'brightness' not in args_dict:
            msg = "Cannot set brightness without a value"
            self.logger.error(msg)
            return msg
        if not (0 <= args_dict['brightness'] <= 100):
            msg = "Brightness must be 0 - 100"
            self.logger.error(msg)
            return msg
        if not self.output_states[0]:
            msg = "Cannot set brightness when bulb is off"
            self.logger.error(msg)
            return msg

        transition_ms = 0
        if 'brightness_transition_ms' in args_dict:
            try:
                ms = int(args_dict['brightness_transition_ms'])
                if ms > 0:
                    transition_ms = ms
            except:
                self.logger.error("Could not parse transition period")

        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[1]['value'] = args_dict['brightness']
        add_measurements_influxdb(self.unique_id, measure_dict)

        self.bulb_brightness(args_dict['brightness'], transition_ms)
        return f"Set Brightness: {args_dict['brightness']} %, Transition: {transition_ms} ms"

    def set_hsv(self, args_dict):
        while self.changing_state:
            time.sleep(0.1)

        if 'hsv' not in args_dict:
            msg = "Cannot set hsv without a value"
            self.logger.error(msg)
            return msg
        if not self.output_states[0]:
            msg = "Cannot set hsv when bulb is off"
            self.logger.error(msg)
            return msg

        try:
            list_hsv = args_dict['hsv'].split(",")
            hue = int(list_hsv[0])
            saturation = int(list_hsv[1])
            brightness = int(list_hsv[2])
        except:
            self.logger.error('Could not parse hsv. Needs to be in the format "hue, saturation, brightness", e.g. "20, 30, 100".')
            return

        transition_ms = 0
        if 'hsv_transition_ms' in args_dict:
            try:
                ms = int(args_dict['hsv_transition_ms'])
                if ms > 0:
                    transition_ms = ms
            except:
                self.logger.error("Could not parse transition period")

        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[3]['value'] = hue
        measure_dict[4]['value'] = saturation
        measure_dict[1]['value'] = brightness
        add_measurements_influxdb(self.unique_id, measure_dict)

        hsv = [hue, saturation, brightness]
        self.bulb_hsv(hsv, transition_ms)
        return f"Set HSV: {hsv} %, Transition: {transition_ms} ms"

    def set_color_temperature(self, args_dict):
        while self.changing_state:
            time.sleep(0.1)

        if 'color_temperature' not in args_dict:
            msg = "Cannot set color temperature without a value"
            self.logger.error(msg)
            return msg
        if not (2500 <= args_dict['color_temperature'] <= 6500):
            msg = "Color Temperature must be 2500 - 6500"
            self.logger.error(msg)
            return msg
        if not self.output_states[0]:
            msg = "Cannot set color temperature when bulb is off"
            self.logger.error(msg)
            return msg

        transition_ms = 0
        if 'color_temperature_transition_ms' in args_dict:
            try:
                ms = int(args_dict['color_temperature_transition_ms'])
                if ms > 0:
                    transition_ms = ms
            except:
                self.logger.error("Could not parse transition period")

        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[2]['value'] = args_dict['color_temperature']
        add_measurements_influxdb(self.unique_id, measure_dict)

        self.bulb_color_temperature(args_dict['color_temperature'], transition_ms)
        return f"Set Color Temperature: {args_dict['color_temperature']}, Transition: {transition_ms} ms"

    def turn_on(self, args_dict):
        transition_ms = 0
        if 'on_transition_ms' in args_dict:
            try:
                ms = int(args_dict['on_transition_ms'])
                if ms > 0:
                    transition_ms = ms
            except:
                self.logger.error("Could not parse transition period")

        self.bulb_change(True, transition_ms)
        return f"Turn On, Transition: {transition_ms} ms"

    def turn_off(self, args_dict):
        transition_ms = 0
        if 'off_transition_ms' in args_dict:
            try:
                ms = int(args_dict['off_transition_ms'])
                if ms > 0:
                    transition_ms = ms
            except:
                self.logger.error("Could not parse transition period")

        self.bulb_change(False, transition_ms)
        return f"Turn Off, Transition: {transition_ms} ms"
