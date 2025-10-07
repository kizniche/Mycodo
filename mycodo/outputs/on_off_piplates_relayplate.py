# coding=utf-8
#
# on_off_piplates_replayplate.py - Output for the PiPlates RelayPlate
#
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    1: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    2: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    3: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    4: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    5: {
        'measurement': 'duration_time',
        'unit': 's',
    },
    6: {
        'measurement': 'duration_time',
        'unit': 's',
    }
}

channels_dict = {
    0: {
        'name': 'Relay 1',
        'types': ['on_off'],
        'measurements': [0]
    },
    1: {
        'name': 'Relay 2',
        'types': ['on_off'],
        'measurements': [1]
    },
    2: {
        'name': 'Relay 3',
        'types': ['on_off'],
        'measurements': [2]
    },
    3: {
        'name': 'Relay 4',
        'types': ['on_off'],
        'measurements': [3]
    },
    4: {
        'name': 'Relay 5',
        'types': ['on_off'],
        'measurements': [4]
    },
    5: {
        'name': 'Relay 6',
        'types': ['on_off'],
        'measurements': [5]
    },
    6: {
        'name': 'Relay 7',
        'types': ['on_off'],
        'measurements': [6]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'OUTPUT_ON_OFF_PIPLATES_RELAYPLATE_01',
    'output_name': "{}: PiPlates RelayPlate (7-Channel board)".format(lazy_gettext('On/Off')),
    'output_manufacturer': 'PiPlates',
    'output_library': 'pi-plates',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://pi-plates.com/product/relayplate/',

    'message': 'Controls the 7 channel PiPlates RelayPlate.',

    'options_enabled': [
        'button_on',
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'piplates', 'pi-plates==10.5')
    ],

    'interfaces': ['SPI'],

    'custom_options': [
        {
            'id': 'board_address',
            'type': 'integer',
            'default_value': 0,
            'name': 'Board Address',
            'phrase': 'The address of the board you want to control'
        }
    ],

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
            'phrase': 'Set the state of the relay when Mycodo starts'
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
            'phrase': 'Set the state of the relay when Mycodo shuts down'
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

        self.board_address = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        import piplates.RELAYplate as RELAY

        self.setup_output_variables(OUTPUT_INFORMATION)

        if self.board_address is None:
            return

        self.device = RELAY

        for channel in channels_dict:
            if self.options_channels['state_startup'][channel] == 1:
                self.output_states[channel] = bool(self.options_channels['on_state'][channel])
            elif self.options_channels['state_startup'][channel] == 0:
                self.output_states[channel] = bool(not self.options_channels['on_state'][channel])
            else:
                # Default state: Off
                self.output_states[channel] = bool(not self.options_channels['on_state'][channel])

            if self.output_states[channel]:
                self.device.relayON(self.board_address, channel + 1)
            else:
                self.device.relayOFF(self.board_address, channel + 1)

        for channel in channels_dict:
            if self.options_channels['trigger_functions_startup'][channel]:
                try:
                    self.check_triggers(self.unique_id, output_channel=channel)
                except Exception as err:
                    self.logger.error(
                        "Could not check Trigger for channel {} of output {}: {}".format(
                            channel, self.unique_id, err))

        self.output_setup = True

    def output_switch(self,
                      state,
                      output_type=None,
                      amount=None,
                      duty_cycle=None,
                      output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        if output_channel is None:
            msg = "Output channel needs to be specified"
            self.logger.error(msg)
            return msg

        try:
            if state == 'on':
                self.output_states[output_channel] = bool(self.options_channels['on_state'][channel])
            elif state == 'off':
                self.output_states[output_channel] = bool(not self.options_channels['on_state'][channel])

            if self.output_states[channel]:
                self.device.relayON(self.board_address, channel + 1)
            else:
                self.device.relayOFF(self.board_address, channel + 1)

            msg = "success"
        except Exception as e:
            msg = "CH{} state change error: {}".format(output_channel, e)
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
                    self.output_states[output_channel] = bool(self.options_channels['on_state'][channel])
                elif self.options_channels['state_shutdown'][channel] == 0:
                    self.output_states[output_channel] = bool(not self.options_channels['on_state'][channel])
                else:
                    self.output_states[output_channel] = bool(not self.options_channels['on_state'][channel])

                if self.output_states[channel]:
                    self.device.relayON(self.board_address, channel + 1)
                else:
                    self.device.relayOFF(self.board_address, channel + 1)
        self.running = False
