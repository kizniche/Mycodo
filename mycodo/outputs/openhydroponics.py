# coding=utf-8
import copy

from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.asyncio import AsyncLoop


loop = AsyncLoop()
loop.initialize()

measurements_dict = {
    0: {"measurement": "duration_time", "unit": "s"},
    1: {"measurement": "duty_cycle", "unit": "percent"},
}

channels_dict = {
    0: {"types": ["on_off", "pwm"], "measurements": [0, 1]},
}

# Output information
OUTPUT_INFORMATION = {
    "output_name_unique": "openhydroponics",
    "output_name": "OpenHydroponics Outputs",
    "url_manufacturer": "https://openhydroponics.com/",
    "url_datasheet": "https://docs.openhydroponics.com/hardware.html",
    "url_product_purchase": [
        "https://lectronz.com/stores/mickeprag",
    ],
    "measurements_dict": measurements_dict,
    "channels_dict": channels_dict,
    "output_types": ["on_off", "pwm"],
    "options_disabled": ["interface"],  # Show the interface (as a disabled input)
    "options_enabled": [
        "button_on",  # Shows a button to turn the output on
    ],
    "dependencies_module": [
        ("pip-pypi", "openhydroponics", "openhydroponics>=0.6.0"),
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
        {
            "id": "endpoint_id",
            "type": "integer",
            "default_value": 0,
            "required": True,
            "name": "Endpoint number",
            "phrase": "The endpoint in the node to control",
        },
    ],
}


async def populate_nodes():
    node_manager = NodeManager()
    await node_manager.init()
    async for node in node_manager:
        OUTPUT_INFORMATION["custom_options"][0]["options_select"].append(
            (str(node.uuid), f"Node: {node.uuid}")
        )
    await node_manager.deinit()


try:
    from openhydroponics.dbus import NodeManager
    from openhydroponics.base.endpoint import EndpointClass, EndpointOutputClass

    loop.call_async(populate_nodes())
except ImportError:
    # Before the dependencies are installed, this will raise an ImportError
    # Just ignore it for now
    pass


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""

    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        # Initialize custom option variables to None
        self.device_id = None
        self.node_manager = NodeManager()
        self.device_id = None
        self.value = None

        # Set custom option variables to defaults or user-set values
        self.setup_custom_options(OUTPUT_INFORMATION["custom_options"], output)

    async def async_initialize(self):
        await self.node_manager.init()
        endpoint = await self.get_endpoint()
        if endpoint:
            endpoint.on_value_changed.connect(self.on_value_changed)
        self.output_setup = True

    def initialize(self):
        loop.call_async(self.async_initialize())
        # Variables set by the user interface

        self.setup_output_variables(OUTPUT_INFORMATION)

    async def get_endpoint(self):
        node = await self.node_manager.request_node(self.device_id)
        if not node:
            self.logger.error(f"Node {self.device_id} not found")
            return None
        endpoint = node.get_endpoint(self.endpoint_id)
        if not endpoint:
            self.logger.error(f"Endpoint {self.endpoint_id} not found")
            return None
        if endpoint.ENDPOINT_CLASS != EndpointClass.Output:
            self.logger.error(f"Endpoint {self.endpoint_id} is not an output endpoint")
            self.logger.error(endpoint)
            return None
        if endpoint.OUTPUT_CLASS != EndpointOutputClass.Variable:
            self.logger.error(f"Endpoint {self.endpoint_id} is not a variable output")
            return None
        return endpoint

    def output_switch(
        self, state, output_type=None, amount=None, duty_cycle=None, output_channel=None
    ):
        """
        Set the output on, off, to an amount, or to a duty cycle
        output_type can be None, 'sec', 'vol', or 'pwm', and determines the amount's unit
        """
        return loop.call_async(
            self.output_switch_async(
                state, output_type, amount, duty_cycle, output_channel
            )
        )

    async def output_switch_async(
        self, state, output_type, amount, duty_cycle, output_channel
    ):
        endpoint = await self.get_endpoint()
        if not endpoint:
            self.logger.error(f"Endpoint {self.endpoint_id} not found")
            return

        if state == "on":
            duty = 100.0
            state = True
            if output_type == "pwm":
                duty = amount
                state = amount
            await endpoint.set(duty)
        elif state == "off":
            await endpoint.set(0.0)

    async def on_value_changed(self, new_value):
        if self.value == new_value:
            return
        self.value = new_value
        if not self.is_setup():
            return
        # Add the measurement to the database
        measure_dict = copy.deepcopy(measurements_dict)
        measure_dict[1]["value"] = new_value
        add_measurements_influxdb(self.unique_id, measure_dict)

    async def is_on_async(self, output_channel=None):
        """Code to return the state of the output."""
        endpoint = await self.get_endpoint()
        if not endpoint:
            self.logger.error(f"Endpoint {self.endpoint_id} not found")
            return
        return endpoint.value > 0.0

    def is_on(self, output_channel):
        if not self.is_setup():
            return
        return loop.call_async(self.is_on_async(output_channel))

    def is_setup(self):
        """Returns whether the output has successfully been set up."""
        return self.output_setup

    def stop_output(self):
        super().stop_output()
        loop.call_async(self.node_manager.deinit())
