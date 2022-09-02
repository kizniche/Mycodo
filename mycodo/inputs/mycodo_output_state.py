# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.mycodo_client import DaemonControl

# Measurements
measurements_dict = {
    0: {
        'measurement': 'boolean',
        'unit': 'bool'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MYCODO_OUTPUT_STATE',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Output State (On/Off)',
    'input_name_short': 'On/Off Output State',
    'measurements_name': 'Boolean',
    'measurements_dict': measurements_dict,

    'message': 'This Input stores a 0 (off) or 1 (on) for the selected On/Off Output.',

    'options_enabled': [
        'period'
    ],

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels',
            ],
            'name': 'On/Off Output Channel',
            'phrase': 'Select an output to measure'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that pings a server and returns 1 if it's up
    and 0 if it's down.
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.control = DaemonControl()
        self.output_device_id = None
        self.output_channel_id = None
        self.output_channel = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        self.output_channel = self.get_output_channel_from_channel_id(
            self.output_channel_id)

    def get_measurement(self):
        """Determine the output state."""
        self.return_dict = copy.deepcopy(measurements_dict)

        output_state = self.control.output_state(
            self.output_device_id, self.output_channel)

        self.logger.debug(f"Output State: {output_state}")

        if output_state == "on":
            self.value_set(0, 1)
        elif output_state == "off":
            self.value_set(0, 0)
        else:
            self.logger.error(f"Output state neither 'on' nor 'off': '{output_state}'")

        return self.return_dict
