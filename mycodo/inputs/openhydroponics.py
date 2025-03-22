# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import DeviceMeasurements, InputChannel
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.asyncio import AsyncLoop

measurements_dict = {
}

# Channels
channels_dict = {0: {}}



INPUT_INFORMATION = {
    "input_name_unique": "openhydroponics",
    "input_manufacturer": "OpenHydroponics",
    "input_name": "OpenHydroponics Inputs",
    "input_name_short": "OpenHydroponics",
    "measurements_name": "pH/EC/Humidity/Temperature",
    "measurements_dict": measurements_dict,
    "measurements_use_same_timestamp": True,
    "measurements_variable_amount": True,
    "channels_dict": channels_dict,
    'channel_quantity_same_as_measurements': True,
    "url_manufacturer": "https://openhydroponics.com/",
    "url_datasheet": "https://docs.openhydroponics.com/hardware.html",
    "url_product_purchase": [
        "https://lectronz.com/stores/mickeprag",
    ],
    "options_enabled": [],
    "options_disabled": ["interface"],
    "dependencies_module": [
        ("pip-pypi", "openhydroponics", "openhydroponics>=0.1.0"),
    ],
    "interfaces": ["CAN"],
    "custom_options": [
        {
            "id": "device_id",
            "type": "text",
            "default_value": "00000000-0000-0000-0000-000000000000",
            "required": True,
            "name": "Device Identifier",
            "phrase": "Select the device",
        },
    ],
    "custom_channel_options": [
        {
            "id": "endpoint",
            "type": "integer",
            "default_value": 0,
            "required": True,
            "name": "Endpoint",
            "phrase": "OpenHydroponics endpoint number",
        }
    ],
}


class InputModule(AbstractInput):
    """ Input module to read the Openhydroponics sneosors. """

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        # Initialize variables
        self.node_manager = None
        self.device_id = None
        self.options_channels = None

        self.loop = AsyncLoop()

        # Set custom option variables to defaults or user-set values
        self.setup_custom_options(INPUT_INFORMATION["custom_options"], input_dev)

        if not testing:
            self.try_initialize()

    async def async_initialize(self):
        from openhydroponics.node_manager import NodeManager
        self.node_manager = NodeManager()

        input_channels = db_retrieve_table_daemon(
            InputChannel).filter(InputChannel.input_id == self.input_dev.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            INPUT_INFORMATION['custom_channel_options'], input_channels)

        self.device_measurements = db_retrieve_table_daemon(
            DeviceMeasurements).filter(
            DeviceMeasurements.device_id == self.input_dev.unique_id)
        self.measurement_info = {}
        for measurement in self.device_measurements.all():
            self.measurement_info[measurement.channel] = {}
            self.measurement_info[measurement.channel]["unit"] = measurement.unit
            self.measurement_info[measurement.channel][
                "measurement"
            ] = measurement.measurement

    def initialize(self):
        self.loop.initialize()
        self.loop.call_async(self.async_initialize())

    async def get_measurement_async(self):
        if not self.device_id:
            self.logger.error("Device ID not set")
            return None
        node = await self.node_manager.request_node(self.device_id)
        if not node:
            self.logger.error(f"Node {self.device_id} not found")
            return None

        self.return_dict = copy.deepcopy(self.measurement_info)
        for channel in self.channels_measurement:
            endpoint_no = self.options_channels['endpoint'][channel]
            value, _ = node.get_endpoint_value(endpoint_no)
            if not value:
                continue
            self.value_set(channel, value)
        return self.return_dict

    def get_measurement(self):
        return self.loop.call_async(self.get_measurement_async())

    def stop_input(self):
        self.loop.stop()
