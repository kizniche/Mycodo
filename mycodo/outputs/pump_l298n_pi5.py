# coding=utf-8
#
# pump_l298n.py - Output for L298N DC motor controller
#
import copy
import threading
import time
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_percent
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.system_pi import cmd_output

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    1: {
        'measurement': 'volume',
        'unit': 'ml'
    },
    2: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    3: {
        'measurement': 'volume',
        'unit': 'ml'
    }
}

channels_dict = {
    0: {
        'name': 'Motor A',
        'types': ['volume', 'on_off'],
        'measurements': [0, 1]
    },
    1: {
        'name': 'Motor B',
        'types': ['volume', 'on_off'],
        'measurements': [2, 3]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'DC_MOTOR_L298N_2',
    'output_name': "{}: L298N DC Motor Controller (Pi 5)".format(lazy_gettext('Peristaltic Pump')),
    'output_manufacturer': 'STMicroelectronics',
    'output_library': 'pinctrl',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['volume', 'on_off'],

    'url_additional': 'https://www.electronicshub.org/raspberry-pi-l298n-interface-tutorial-control-dc-motor-l298n-raspberry-pi/',

    'message': 'The L298N can control 2 DC motors, and direction. If these motors control peristaltic pumps, set the Flow Rate '
               'and the output can can be instructed to dispense volumes accurately in addition to being turned on for durations.',

    'options_enabled': [
        'button_on',
        'button_send_duration',
        'button_send_volume'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['GPIO'],

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
            'id': 'pin_1',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Input Pin 1',
            'phrase': 'The Input Pin 1 of the controller (BCM numbering)'
        },
        {
            'id': 'pin_2',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Input Pin 2',
            'phrase': 'The Input Pin 2 of the controller (BCM numbering)'
        },
        {
            'id': 'use_enable',
            'type': 'bool',
            'default_value': True,
            'name': 'Use Enable Pin',
            'phrase': 'Enable the use of the Enable Pin'
        },
        {
            'id': 'pin_enable',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Enable Pin',
            'phrase': 'The Enable pin of the controller (BCM numbering)'
        },
        {
            'id': 'direction',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, 'Forward'),
                (0, 'Backward')
            ],
            'name': lazy_gettext('Direction'),
            'phrase': 'The direction to turn the motor'
        },
        {
            'id': 'flow_rate_ml_min',
            'type': 'float',
            'default_value': 150.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Volume Rate (ml/min)',
            'phrase': 'If a pump, the measured flow rate (ml/min) at the set Duty Cycle'
        },
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.driver = {}
        self.currently_dispensing = False
        self.channel_setup = {}

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        for channel in channels_dict:
            if (not self.options_channels['pin_1'][channel] or
                    not self.options_channels['pin_2'][channel] or
                    (self.options_channels['use_enable'][channel] and
                     not self.options_channels['pin_enable'][channel])):
                self.logger.error(
                    f"Cannot initialize Output channel {channel} until all options are set. "
                    "Check your configuration.")
                self.channel_setup[channel] = False
            else:
                cmd = f"pinctrl set {self.options_channels['pin_1'][channel]} op dl"
                cmd_return, cmd_error, cmd_status = cmd_output(cmd, user="root")
                self.logger.debug(
                    f"GPIO {self.options_channels['pin_1'][channel]} setup with '{cmd}': "
                    f"Status: {cmd_status}, Return: {cmd_return}, Error: {cmd_error}")

                cmd = f"pinctrl set {self.options_channels['pin_2'][channel]} op dl"
                cmd_return, cmd_error, cmd_status = cmd_output(cmd, user="root")
                self.logger.debug(
                    f"GPIO {self.options_channels['pin_2'][channel]} setup with '{cmd}': "
                    f"Status: {cmd_status}, Return: {cmd_return}, Error: {cmd_error}")

                cmd = f"pinctrl set {self.options_channels['pin_enable'][channel]} op dl"
                cmd_return, cmd_error, cmd_status = cmd_output(cmd, user="root")
                self.logger.debug(
                    f"GPIO {self.options_channels['pin_enable'][channel]} setup with '{cmd}': "
                    f"Status: {cmd_status}, Return: {cmd_return}, Error: {cmd_error}")

                self.channel_setup[channel] = True
                self.output_states[channel] = False

        self.output_setup = True

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. " \
                  "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        if not self.is_setup(channel=output_channel):
            msg = f"Error 101: Output channel {output_channel} not set up, cannot turn it on or off. " \
                  "See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        if not self.running:
            msg = "Output is not running, cannot turn it on or off."
            self.logger.error(msg)
            return msg

        if amount is not None and amount < 0:
            self.logger.error("Amount cannot be less than 0")
            return

        if state == 'on' and output_type == 'vol' and amount:
            if self.currently_dispensing:
                self.logger.debug(
                    "Pump instructed to dispense volume while it's already dispensing a volume. "
                    "Overriding current dispense with new instruction.")

            total_dispense_seconds = amount / self.options_channels['flow_rate_ml_min'][output_channel] * 60
            msg = f"Turning pump on for {total_dispense_seconds:.1f} seconds " \
                  f"to dispense {amount:.1f} ml " \
                  f"(at {self.options_channels['flow_rate_ml_min'][output_channel]:.1f} ml/min)."
            self.logger.debug(msg)

            write_db = threading.Thread(
                target=self.dispense_volume,
                args=(output_channel, amount, total_dispense_seconds,))
            write_db.start()
        elif state == 'on' and output_type == 'sec':
            if self.currently_dispensing:
                self.logger.debug(
                    "Pump instructed to turn on while it's already dispensing a volume. "
                    "Overriding current dispense with new instruction.")
            self.run(output_channel)
        elif state == 'off':
            if self.currently_dispensing:
                self.currently_dispensing = False
            self.stop(output_channel)

    def dispense_volume(self, channel, amount, total_dispense_seconds):
        """Dispense at flow rate"""
        self.currently_dispensing = True
        self.logger.debug("Output turned on")
        self.run(channel)
        timer_dispense = time.time() + total_dispense_seconds

        while time.time() < timer_dispense and self.currently_dispensing:
            time.sleep(0.01)

        self.stop(channel)
        self.currently_dispensing = False
        self.logger.debug("Output turned off")
        self.record_dispersal(channel, amount, total_dispense_seconds)

    def record_dispersal(self, channel, amount, total_on_seconds):
        measure_dict = copy.deepcopy(measurements_dict)
        measure = channels_dict[channel]['measurements']
        measure_dict[measure[0]]['value'] = total_on_seconds
        measure_dict[measure[1]]['value'] = amount
        add_measurements_influxdb(self.unique_id, measure_dict)

    def run(self, channel):
        if self.options_channels['direction'][channel]:
            self.switch_pin(self.options_channels['pin_1'][channel], True)
            self.switch_pin(self.options_channels['pin_2'][channel], False)
            self.output_states[channel] = True
        else:
            self.switch_pin(self.options_channels['pin_1'][channel], False)
            self.switch_pin(self.options_channels['pin_2'][channel], True)
            self.output_states[channel] = True

    def stop(self, channel):
        self.switch_pin(self.options_channels['pin_1'][channel], False)
        self.switch_pin(self.options_channels['pin_2'][channel], False)
        self.output_states[channel] = False

    def is_on(self, output_channel=None):
        if self.is_setup(channel=output_channel):
            return self.output_states[output_channel]

    def is_setup(self, channel=None):
        if channel is not None:
            return self.channel_setup[channel]
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        self.running = False
        for channel in channels_dict:
            if self.is_setup(channel=channel):
                self.stop(channel)

    def switch_pin(self, pin, state):
        if state:
            set_opt = "dh"
        else:
            set_opt = "dl"
        cmd = f"pinctrl set {pin} {set_opt}"
        cmd_return, cmd_error, cmd_status = cmd_output(cmd, user="root")
        state_text = 'ON' if state else 'OFF'
        self.logger.debug(
            f"GPIO {pin} set {state_text} with '{cmd}': "
            f"Status: {cmd_status}, Return: {cmd_return}, Error: {cmd_error}")
