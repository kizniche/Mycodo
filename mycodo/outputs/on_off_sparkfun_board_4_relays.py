# coding=utf-8
#
# on_off_sparkfun_board_4_relays.py - Output for Sparkfun relay board with 4 relays
#
from collections import OrderedDict

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon

measurements_dict = OrderedDict()
channels_dict = OrderedDict()
for each_channel in range(4):
    measurements_dict[each_channel] = {
        'measurement': 'duration_time',
        'unit': 's'
    }
    channels_dict[each_channel] = {
        'name': f'Channel {each_channel + 1}',
        'types': ['on_off'],
        'measurements': [each_channel]
    }

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'SPARKFUN_RELAY_BOARDS_4',
    'output_name': "{}: Sparkfun Relay Board (4 Relays)".format(lazy_gettext('On/Off')),
    'output_manufacturer': 'Sparkfun',
    'output_library': 'sparkfun-qwiic-relay',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.sparkfun.com',
    'url_product_purchase': [
        'https://www.sparkfun.com/products/16833',
        'https://www.sparkfun.com/products/16566',
        # 'https://www.sparkfun.com/products/16810',
        # 'https://www.sparkfun.com/products/15093'
    ],

    'message': 'Controls the 4 relays of the relay module.',

    'options_enabled': [
        'i2c_location',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'qwiic_relay', 'sparkfun-qwiic-relay==0.0.2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x18', '0x19', '0x6D', '0x6C', '0x0A', '0x0B', '0x08', '0x09'],
    'i2c_address_editable': True,
    'i2c_address_default': '0x18',

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

        self.device = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        import qwiic_relay

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            self.logger.debug(f"I2C: Address: {self.output.i2c_location}, Bus: {self.output.i2c_bus}")
            if self.output.i2c_location:
                self.device = qwiic_relay.QwiicRelay(address=int(str(self.output.i2c_location), 16))
                self.output_setup = True

                for channel in channels_dict:
                    if self.options_channels['state_startup'][channel] == 1:
                        self.output_switch("on", output_channel=channel)
                    elif self.options_channels['state_startup'][channel] == 0:
                        self.output_switch("off", output_channel=channel)

                for channel in channels_dict:
                    if self.options_channels['trigger_functions_startup'][channel]:
                        try:
                            self.check_triggers(self.unique_id, output_channel=channel)
                        except Exception as err:
                            self.logger.error(f"Could not check Trigger for channel {channel}: {err}")
        except:
            self.logger.exception("Could not set up output")
            return

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
                self.device.set_relay_on(output_channel + 1)
                self.output_states[output_channel] = True
            elif state == 'off':
                self.device.set_relay_off(output_channel + 1)
                self.output_states[output_channel] = False

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
                    self.output_switch("on", output_channel=channel)
                elif self.options_channels['state_shutdown'][channel] == 0:
                    self.output_switch("off", output_channel=channel)
            self.logger.debug(f"List sent to device: {dict_states}")
        self.running = False
