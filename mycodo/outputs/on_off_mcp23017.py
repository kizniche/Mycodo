# coding=utf-8
#
# on_off_mcp23017.py - Output for MCP23017
#
from collections import OrderedDict

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = OrderedDict()
channels_dict = OrderedDict()
for each_channel in range(16):
    measurements_dict[each_channel] = {
        'measurement': 'duration_time',
        'unit': 's'
    }
    channels_dict[each_channel] = {
        'name': f'Channel {each_channel}',
        'types': ['on_off'],
        'measurements': [each_channel]
    }

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'MCP23017',
    'output_name': "{}: MCP23017 16-Channel {}".format(lazy_gettext('On/Off'), lazy_gettext('I/O Expander')),
    'output_manufacturer': 'MICROCHIP',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.microchip.com/wwwproducts/en/MCP23017',
    'url_datasheet': 'https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf',
    'url_product_purchase': 'https://www.amazon.com/Waveshare-MCP23017-Expansion-Interface-Expands/dp/B07P2H1NZG',

    'message': 'Controls the 16 channels of the MCP23017.',

    'options_enabled': [
        'i2c_location',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_mcp230xx', 'adafruit-circuitpython-mcp230xx==2.4.6')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x20', '0x21', '0x22', '0x23', '0x24', '0x25', '0x26', '0x27', ],
    'i2c_address_editable': False,
    'i2c_address_default': '0x20',

    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state of the GPIO when Mycodo starts'
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': 'Set the state of the GPIO when Mycodo shuts down'
        },
        {
            'id': 'on_state',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, 'HIGH'),
                (0, 'LOW')
            ],
            'name': lazy_gettext('On State'),
            'phrase': 'The state of the GPIO that corresponds to an On state'
        },
        {
            'id': 'trigger_functions_startup',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Trigger Functions at Startup'),
            'phrase': 'Whether to trigger functions when the output switches at startup'
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
    """An output support class that operates an output"""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.sensor = None
        self.pins = []

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        from adafruit_mcp230xx.mcp23017 import MCP23017
        from adafruit_extended_bus import ExtendedI2C

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            self.logger.debug(f"I2C: Address: {self.output.i2c_location}, "
                              f"Bus: {self.output.i2c_bus}")
            if self.output.i2c_location:
                self.sensor = MCP23017(
                    ExtendedI2C(self.output.i2c_bus),
                    address=int(str(self.output.i2c_location), 16))
                self.output_setup = True
        except:
            self.logger.exception("Could not set up output")
            return

        for pin in range(0, 16):
            self.pins.append(self.sensor.get_pin(pin))

        for channel in channels_dict:
            if self.options_channels['state_startup'][channel] == 1:
                self.pins[channel].switch_to_output(value=bool(self.options_channels['on_state'][channel]))
                self.output_states[channel] = bool(self.options_channels['on_state'][channel])
            elif self.options_channels['state_startup'][channel] == 0:
                self.pins[channel].switch_to_output(value=bool(not self.options_channels['on_state'][channel]))
                self.output_states[channel] = bool(not self.options_channels['on_state'][channel])
            else:
                # Default state: Off
                self.pins[channel].switch_to_output(value=bool(not self.options_channels['on_state'][channel]))
                self.output_states[channel] = bool(not self.options_channels['on_state'][channel])

            if self.options_channels['trigger_functions_startup'][channel]:
                try:
                    self.check_triggers(self.unique_id, output_channel=channel)
                except Exception as err:
                    self.logger.error(
                        f"Could not check Trigger for channel {channel} of output {self.unique_id}: {err}")

    def output_switch(self,
                      state,
                      output_type=None,
                      amount=None,
                      duty_cycle=None,
                      output_channel=None):
        if output_channel is None:
            msg = "Output channel needs to be specified"
            self.logger.error(msg)
            return msg

        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        try:
            if state == 'on':
                self.pins[output_channel].value = bool(self.options_channels['on_state'][output_channel])
                self.output_states[output_channel] = bool(self.options_channels['on_state'][output_channel])
                self.logger.debug(f"Output channel {output_channel} turned ON")
            elif state == 'off':
                self.pins[output_channel].value = bool(not self.options_channels['on_state'][output_channel])
                self.output_states[output_channel] = bool(not self.options_channels['on_state'][output_channel])
                self.logger.debug(f"Output channel {output_channel} turned OFF")

            msg = "success"
        except Exception as err:
            msg = f"CH{output_channel} state change error: {err}"
            self.logger.error(msg)
        return msg

    def is_on(self, output_channel=None):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel] == self.options_channels['on_state'][output_channel]

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            for channel in channels_dict:
                if self.options_channels['state_shutdown'][channel] == 1:
                    self.pins[channel].value = bool(self.options_channels['on_state'][channel])
                elif self.options_channels['state_shutdown'][channel] == 0:
                    self.pins[channel].value = bool(not self.options_channels['on_state'][channel])
        self.running = False
