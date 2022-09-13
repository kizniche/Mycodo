# coding=utf-8
import asyncio
import copy
import json
import random
import time
import traceback
from threading import Event
from threading import Thread

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_value

# Measurements
measurements_dict = {
    0: {
        'measurement': 'electrical_potential',
        'unit': 'V',
        'name': ''
    },
    1: {
        'measurement': 'electrical_current',
        'unit': 'A',
        'name': ''
    },
    2: {
        'measurement': 'power',
        'unit': 'W',
        'name': ''
    },
    3: {
        'measurement': 'energy',
        'unit': 'kWh',
        'name': ''
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'input_kasa_energy_meter',
    'input_manufacturer': 'TP-Link',
    'input_name': 'Kasa WiFi Power Plug/Strip Energy Statistics',
    'input_name_short': 'Kasa Energy Meter',
    'input_library': 'python-kasa',
    'measurements_name': 'kilowatt hours',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.kasasmart.com/us/products/smart-plugs/kasa-smart-plug-slim-energy-monitoring-kp115',

    'message': "This measures from several Kasa power devices (plugs/strips) capable of measuring energy consumption. "
               "These include, but are not limited to the KP115 and HS600.",

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'kasa', 'python-kasa==0.5.0'),
        ('pip-pypi', 'aio_msgpack_rpc', 'aio_msgpack_rpc==0.2.0')
    ],

    'interfaces': ['IP'],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """The total kWh can be cleared with the following button or with the Clear Total kWh Function Action. This will also clear all energy stats on the device, not just the total kWh."""
        },
        {
            'id': 'clear_total_kwh',
            'type': 'button',
            'name': "{}: {}".format(lazy_gettext('Clear Total'), lazy_gettext('Kilowatt-hour'))
        }
    ],

    'custom_options': [
        {
            'id': 'device_type',
            'type': 'select',
            'default_value': '',
            'options_select': [
                ('strip', 'Power Strip'),
                ('plug', 'Power Plug')
            ],
            'name': 'Device Type',
            'phrase': 'The type of Kasa device'
        },
        {
            'id': 'plug_address',
            'type': 'text',
            'default_value': '0.0.0.0',
            'required': True,
            'name': TRANSLATIONS['host']['title'],
            'phrase': TRANSLATIONS['host']['phrase']
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
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that measures the HS300 energy stats"""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.input_setup = False
        self.plug = None
        self.rpc_server_thread = None
        self.connect_error = None

        self.device_type = None
        self.plug_address = None
        self.asyncio_rpc_port = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        if not self.plug_address or self.plug_address == "0.0.0.0":
            self.logger.error("Plug address must be set")
            return

        started_evt = Event()

        loop = asyncio.new_event_loop()
        self.rpc_server_thread = Thread(
            target=self.aio_rpc_server, args=(started_evt, loop, self.device_type, self.logger))
        self.rpc_server_thread.start()

        started_evt.wait()  # Wait for thread to either start running or error

        for _ in range(3):  # Attempt to connect 3 times
            self.connect()
            if self.input_setup:
                break
            time.sleep(2)

    def get_measurement(self):
        """Gets the humidity and temperature."""
        if not self.input_setup:
            self.logger.error(f"Input not set up")
            if self.connect_error:
                self.logger.error(self.connect_error)
            return None

        self.return_dict = copy.deepcopy(measurements_dict)

        stats = self.energy_stats()

        self.logger.debug(f"Final Stats: {stats}")

        if self.is_enabled(0) and "realtime" in stats and "voltage_mv" in stats["realtime"]:
            self.value_set(0, stats["realtime"]["voltage_mv"] / 1000)

        if self.is_enabled(1) and "realtime" in stats and "current_ma" in stats["realtime"]:
            self.value_set(1, stats["realtime"]["current_ma"] / 1000)

        if self.is_enabled(2) and "realtime" in stats and "power_mw" in stats["realtime"]:
            self.value_set(2, stats["realtime"]["power_mw"] / 1000)

        if self.is_enabled(3) and "realtime" in stats and "total_wh" in stats["realtime"]:
            self.value_set(3, stats["realtime"]["total_wh"] / 1000)

        return self.return_dict

    def aio_rpc_server(self, started_evt, loop, device_type, logger):
        import aio_msgpack_rpc

        class KasaServer:
            """Communicates with the Kasa power strip"""

            def __init__(self, address_, device_type_, logger_):
                self.plug = None
                self.address = address_
                self.device_type_ = device_type_
                self.logger_ = logger_

            async def connect(self):
                try:
                    if self.device_type_ == "plug":
                        from kasa import SmartPlug as SmartDevice
                    elif self.device_type_ == "strip":
                        from kasa import SmartStrip as SmartDevice
                    else:
                        return 1, f"Unknown device type '{self.device_type_}'. Must select either Strip or Plug."
                    self.plug = SmartDevice(self.address)
                    await self.plug.update()
                    return 0, f'Plug {self.plug.alias}: {self.plug.hw_info}'
                except Exception:
                    return 1, str(traceback.print_exc())

            async def energy_stats(self):
                try:
                    await self.plug.update()

                    return_dict = {
                        "has_emeter": json.dumps(self.plug.has_emeter)
                    }

                    if return_dict['has_emeter']:
                        features = []
                        for each_feature in self.plug.features:
                            features.append(str(each_feature))
                        return_dict["features"] = json.dumps(features)
                        return_dict["realtime"] = json.dumps(await self.plug.get_emeter_realtime())
                        return_dict["daily"] = json.dumps(await self.plug.get_emeter_daily())
                        return_dict["monthly"] = json.dumps(await self.plug.get_emeter_monthly())
                    else:
                        self.logger_.error("This device is not capable of measuring energy")

                    self.logger_.debug(f"Energy Stats: {return_dict}")

                    return 0, return_dict
                except Exception:
                    return 1, str(traceback.format_exc())

            async def clear_energy_stats(self):
                try:
                    return_dict = json.dumps(await self.plug.erase_emeter_stats())

                    self.logger_.debug(f"Clear Stats: {return_dict}")

                    return 0, return_dict
                except Exception:
                    return 1, str(traceback.format_exc())

        async def main(address, port):
            server = None
            try:
                server = await asyncio.start_server(
                    aio_msgpack_rpc.Server(KasaServer(address, device_type, logger)),
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
                self.logger.error(f"Connecting to plug: Error: {msg}")
                self.connect_error = msg
            else:
                self.logger.debug(f"Connecting to plug: {msg}")
                self.input_setup = True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(connect(self.asyncio_rpc_port))

    def energy_stats(self):
        import aio_msgpack_rpc

        return_dict = {}

        async def energy_stats(port):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))
            status, msg = await client.call("energy_stats")

            self.logger.debug(f"energy_stats() returned from rpc: {status}, {msg}")

            if type(msg) == dict:
                for key, value in msg.items():
                    try:
                        return_dict[key] = json.loads(value)
                    except:
                        return_dict[key] = None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(energy_stats(self.asyncio_rpc_port))

        return return_dict

    def clear_energy_stats(self):
        import aio_msgpack_rpc

        return_dict = {}

        async def energy_stats(port):
            client = aio_msgpack_rpc.Client(*await asyncio.open_connection("127.0.0.1", port))
            status, msg = await client.call("clear_energy_stats")

            return_dict['status'] = status
            return_dict['msg'] = msg

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop()
        loop.run_until_complete(energy_stats(self.asyncio_rpc_port))

        return return_dict

    def clear_total_kwh(self, args_dict):
        self.logger.info(f"Clear energy stats returned: {self.clear_energy_stats()}")
