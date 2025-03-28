# coding=utf-8
import asyncio
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.asyncio import AsyncLoop

node_manager = None

measurements_dict = {
}

# Channels
channels_dict = {0: {}}


async def execute_at_modification_async(
    messages,
    mod_input,
    request_form,
    custom_options_dict_presave,
    custom_options_channels_dict_presave,
    custom_options_dict_postsave,
    custom_options_channels_dict_postsave,
):
    from openhydroponics.msg import EndpointClass, EndpointInputClass

    mapping = {
        EndpointInputClass.Temperature: ("temperature", "C"),
        EndpointInputClass.Humidity: ("humidity", "percent"),
        EndpointInputClass.EC: ("electrical_conductivity", "uS_cm"),
        EndpointInputClass.PH: ("ion_concentration", "pH"),
    }

    device_id = request_form.get("device_id")
    if not device_id or device_id == custom_options_dict_presave["device_id"]:
        # Device ID not changed
        return (
            messages,
            mod_input,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave,
        )

    await node_manager.init()
    node = await node_manager.request_node(device_id)
    if not node:
        messages["error"].append(f"Node {mod_input.device_id} not found")
        return (
            messages,
            mod_input,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave,
        )

    device_measurements = DeviceMeasurements.query.filter(
        DeviceMeasurements.device_id == mod_input.unique_id
    )
    channels = []
    # Update existing measurements and delete non existing ones
    for measurement in device_measurements.all():
        endpoint = node.get_endpoint(measurement.channel)
        if (
            endpoint
            and endpoint.ENDPOINT_CLASS == EndpointClass.Input
            and endpoint.INPUT_CLASS in mapping
        ):
            # Input endpoint found, update its measurement
            measurement_type, unit = mapping[endpoint.INPUT_CLASS]
            measurement.measurement = measurement_type
            measurement.unit = unit
            measurement.save()
            channels.append(measurement.channel)
            continue
        measurement.delete()

    # Add new measurements
    for endpoint in node:
        if endpoint.endpoint_id in channels:
            continue
        if endpoint.ENDPOINT_CLASS != EndpointClass.Input:
            continue
        if endpoint.INPUT_CLASS not in mapping:
            continue
        measurement_type, unit = mapping[endpoint.INPUT_CLASS]

        new_measurement = DeviceMeasurements()
        new_measurement.device_id = mod_input.unique_id
        new_measurement.measurement = measurement_type
        new_measurement.unit = unit
        new_measurement.channel = endpoint.endpoint_id
        new_measurement.save()

    return (
        messages,
        mod_input,
        custom_options_dict_postsave,
        custom_options_channels_dict_postsave,
    )


def execute_at_modification(
    messages,
    mod_input,
    request_form,
    custom_options_dict_presave,
    custom_options_channels_dict_presave,
    custom_options_dict_postsave,
    custom_options_channels_dict_postsave,
):

    return asyncio.run(
        execute_at_modification_async(
            messages,
            mod_input,
            request_form,
            custom_options_dict_presave,
            custom_options_channels_dict_presave,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave,
        )
    )


INPUT_INFORMATION = {
    "input_name_unique": "openhydroponics",
    "input_manufacturer": "OpenHydroponics",
    "input_name": "OpenHydroponics Inputs",
    "input_name_short": "OpenHydroponics",
    "measurements_name": "pH/EC/Humidity/Temperature",
    "measurements_dict": measurements_dict,
    "measurements_use_same_timestamp": True,
    "execute_at_modification": execute_at_modification,
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
            "type": "select",
            "options_select": [],
            "default_value": None,
            "required": True,
            "name": "Node",
            "phrase": "Select the openhydroponics node",
        },
    ],
}


async def populate_nodes():
    async for node in node_manager:
        INPUT_INFORMATION["custom_options"][0]["options_select"].append(
            (str(node.uuid), f"Node: {node.uuid}")
        )


try:
    from openhydroponics.node_manager import NodeManager
    node_manager = NodeManager()
    asyncio.run(populate_nodes())
except ImportError:
    # Before the dependencies are installed, this will raise an ImportError
    # Just ignore it for now
    pass


class InputModule(AbstractInput):
    """ Input module to read the Openhydroponics sneosors. """

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        # Initialize variables
        self.device_id = None
        self.options_channels = None

        self.loop = AsyncLoop()

        # Set custom option variables to defaults or user-set values
        self.setup_custom_options(INPUT_INFORMATION["custom_options"], input_dev)

        if not testing:
            self.try_initialize()

    async def async_initialize(self):
        await node_manager.init()

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
        node = await node_manager.request_node(self.device_id)
        if not node:
            self.logger.error(f"Node {self.device_id} not found")
            return None

        self.return_dict = copy.deepcopy(self.measurement_info)
        for channel in self.measurement_info:
            value, _ = node.get_endpoint_value(channel)
            if not value:
                continue
            self.value_set(channel, value)
        return self.return_dict

    def get_measurement(self):
        return self.loop.call_async(self.get_measurement_async())

    def stop_input(self):
        self.loop.stop()
