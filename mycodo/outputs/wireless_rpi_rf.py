# coding=utf-8
#
# wireless_rpi_rf.py - Output for Wireless
#
from flask_babel import lazy_gettext
from mycodo.outputs.base_output import AbstractOutput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'wireless_rpi_rf',
    'output_name': "{} 315/433 MHz".format(lazy_gettext("Wireless")),
    'output_library': 'rpi-rf',
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['on_off'],

    'message': 'This output uses a 315 or 433 MHz transmitter to turn wireless power outlets on or off. '
               'Run ~/Mycodo/mycodo/devices/wireless_rpi_rf.py with a receiver to discover the codes '
               'produced from your remote.',

    'options_enabled': [
        'gpio_pin',
        'wireless_protocol',
        'wireless_pulse_length',
        'wireless_command_on',
        'wireless_command_off',
        'command_force',
        'on_off_none_state_startup',
        'on_off_none_state_shutdown',
        'current_draw',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO'),
        ('pip-pypi', 'rpi_rf', 'rpi_rf')
    ],

    'interfaces': ['GPIO']
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.wireless_pi_switch = None
        self.Transmit433MHz = None
        self.pin = None
        self.on_command = None
        self.off_command = None
        self.protocol = None
        self.pulse_length = None
        self.output_state = None

        if not testing:
            self.initialize_output()

    def initialize_output(self):
        from mycodo.devices.wireless_rpi_rf import Transmit433MHz

        self.Transmit433MHz = Transmit433MHz

        self.pin = self.output.pin
        self.on_command = self.output.on_command
        self.off_command = self.output.off_command
        self.protocol = self.output.protocol
        self.pulse_length = self.output.pulse_length

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None):
        if state == 'on':
            self.wireless_pi_switch.transmit(int(self.on_command))
            self.output_state = True
        elif state == 'off':
            self.wireless_pi_switch.transmit(int(self.off_command))
            self.output_state = False

    def is_on(self):
        if self.is_setup():
            return self.output_state

    def is_setup(self):
        if self.wireless_pi_switch:
            return True
        return False

    def setup_output(self):
        if self.pin is None:
            self.logger.warning("Invalid pin for output: {}.".format(self.pin))
            return

        self.wireless_pi_switch = self.Transmit433MHz(
            self.pin,
            protocol=int(self.protocol),
            pulse_length=int(self.pulse_length))
        self.output_state = False
