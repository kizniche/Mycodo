# coding=utf-8
#
# waveshare_8channel_pi_relay_board_b_gpio.py - Output for Waveshare 8-Channel Raspberry Pi Relay Board B
#
from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

# Define 8 channels (0..7), each supporting on_off with the same measurement type
channels_dict = {
    0: {'types': ['on_off'], 'measurements': [0]},
    1: {'types': ['on_off'], 'measurements': [0]},
    2: {'types': ['on_off'], 'measurements': [0]},
    3: {'types': ['on_off'], 'measurements': [0]},
    4: {'types': ['on_off'], 'measurements': [0]},
    5: {'types': ['on_off'], 'measurements': [0]},
    6: {'types': ['on_off'], 'measurements': [0]},
    7: {'types': ['on_off'], 'measurements': [0]}
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'waveshare_8ch_pi_relay_board_b',
    'output_name': "{}: Waveshare 8-Channel Raspberry Pi Relay Board B (GPIO)".format(lazy_gettext('On/Off')),
    'output_library': 'RPi.GPIO',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'message': 'Each channel controls one relay on the Waveshare Relay Board B. The corresponding GPIO '
               'pin will be set HIGH (3.3V) or LOW (0V) when turned on or off, depending on the On State option.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1')
    ],

    'interfaces': ['GPIO'],

    'custom_channel_options': [
        {
            'id': 'pin',
            'type': 'integer',
            'default_value': None,  # If None, defaults for Board B will be applied at runtime per channel
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {} ({})".format(lazy_gettext('Pin'), lazy_gettext('GPIO'), lazy_gettext('BCM')),
            'phrase': lazy_gettext('The pin to control the state of')
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
            'phrase': 'Set the state when Mycodo starts'
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
            'phrase': 'Set the state when Mycodo shuts down'
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
    """Output to control Waveshare 8-Channel Raspberry Pi Relay Board B via GPIO.

    Channel -> Default BCM pin mapping (Relay 1..8):
      0->5, 1->6, 2->13, 3->16, 4->19, 5->20, 6->21, 7->26
    Users may override pins per channel in the UI. If a channel pin is None, the default mapping is used.
    """

    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)
        self.GPIO = None
        self.resolved_pins = [None] * 8  # Resolved pins per channel after applying defaults

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def _default_pin_for_channel(self, ch_idx):
        # Mapping provided by board documentation (and user confirmation)
        defaults = [5, 6, 13, 16, 19, 20, 21, 26]
        if 0 <= ch_idx < len(defaults):
            return defaults[ch_idx]
        return None

    def initialize(self):
        import RPi.GPIO as GPIO
        self.GPIO = GPIO

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            # Configure GPIO mode only once
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.setwarnings(True)

            # Resolve and set up each channel
            total_channels = len(channels_dict)
            for ch in range(total_channels):
                pin = self.options_channels['pin'][ch]
                if pin is None:
                    pin = self._default_pin_for_channel(ch)
                self.resolved_pins[ch] = pin

                if pin is None:
                    self.logger.error(f"Channel {ch}: Pin must be set (no default available)")
                    continue

                # Determine startup state for the channel
                if self.options_channels['state_startup'][ch]:
                    startup_state = self.options_channels['on_state'][ch]
                else:
                    startup_state = not self.options_channels['on_state'][ch]

                # Set up the pin and apply startup state
                self.GPIO.setup(pin, self.GPIO.OUT)
                self.GPIO.output(pin, startup_state)

                # Optionally trigger functions at startup per channel
                if self.options_channels['trigger_functions_startup'][ch]:
                    try:
                        self.check_triggers(self.unique_id, output_channel=ch)
                    except Exception as err:
                        self.logger.error(
                            "Could not check Trigger for channel {} of output {}: {}".format(
                                ch, self.unique_id, err))

                startup = 'ON' if self.options_channels['state_startup'][ch] else 'OFF'
                state = 'HIGH' if self.options_channels['on_state'][ch] else 'LOW'
                self.logger.info(
                    "Channel {ch}: setup on pin {pin} and turned {startup} (ON={state})".format(
                        ch=ch, pin=pin, startup=startup, state=state))

            self.output_setup = True
        except Exception as except_msg:
            self.logger.exception(
                "Waveshare Relay Board B output setup error: {}".format(except_msg))

    def output_switch(self, state, output_type=None, amount=None, output_channel=0):
        try:
            pin = self.resolved_pins[output_channel]
            if pin is None:
                # If not resolved yet (should not happen after initialize), try resolve now
                pin = self.options_channels['pin'][output_channel] or self._default_pin_for_channel(output_channel)
                self.resolved_pins[output_channel] = pin
            if pin is None:
                raise ValueError(f"Channel {output_channel}: Pin not set")

            if state == 'on':
                self.GPIO.output(pin, self.options_channels['on_state'][output_channel])
            elif state == 'off':
                self.GPIO.output(pin, not self.options_channels['on_state'][output_channel])
            else:
                raise ValueError(f"Unknown state '{state}'")
            msg = "success"
        except Exception as e:
            msg = "State change error: {}".format(e)
            self.logger.exception(msg)
        return msg

    def is_on(self, output_channel=0):
        if self.is_setup():
            try:
                pin = self.resolved_pins[output_channel]
                if pin is None:
                    pin = self.options_channels['pin'][output_channel] or self._default_pin_for_channel(output_channel)
                    self.resolved_pins[output_channel] = pin
                if pin is None:
                    raise ValueError(f"Channel {output_channel}: Pin not set")
                return self.options_channels['on_state'][output_channel] == self.GPIO.input(pin)
            except Exception as e:
                self.logger.error("Status check error: {}".format(e))

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            total_channels = len(channels_dict)
            for ch in range(total_channels):
                try:
                    if self.options_channels['state_shutdown'][ch] == 1:
                        self.output_switch('on', output_channel=ch)
                    elif self.options_channels['state_shutdown'][ch] == 0:
                        self.output_switch('off', output_channel=ch)
                except Exception as err:
                    self.logger.error(f"Channel {ch} shutdown handling error: {err}")
        self.running = False
