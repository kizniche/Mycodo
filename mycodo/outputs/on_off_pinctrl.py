# coding=utf-8
#
# on_off_pinctrl.py - Output for simple GPIO switching using pinctrl
#
from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import cmd_output

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'output_on_off_pinctrl',
    'output_name': "{}: Raspberry Pi GPIO (Pi 5)".format(lazy_gettext('On/Off')),
    'output_library': 'pinctrl',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'message': 'The specified GPIO pin will be set HIGH (3.3 volts) or LOW (0 volts) when turned '
               'on or off, depending on the On State option.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['GPIO'],

    'custom_channel_options': [
        {
            'id': 'pin',
            'type': 'integer',
            'default_value': None,
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
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        if self.options_channels['pin'][0] is None:
            self.logger.error("Pin must be set")
        else:
            try:
                if self.options_channels['state_startup'][0]:
                    startup_state = self.options_channels['on_state'][0]
                else:
                    startup_state = not self.options_channels['on_state'][0]

                if startup_state:
                    cmd = f"pinctrl set {self.options_channels['pin'][0]} op dh"
                else:
                    cmd = f"pinctrl set {self.options_channels['pin'][0]} op dl"
                cmd_return, cmd_error, cmd_status = cmd_output(cmd, user="root")
                self.logger.debug(
                    f"GPIO {self.options_channels['pin'][0]} setup with '{cmd}': "
                    f"Status: {cmd_status}, Return: {cmd_return}, Error: {cmd_error}")
                self.output_setup = True

                if self.options_channels['trigger_functions_startup'][0]:
                    try:
                        self.check_triggers(self.unique_id, output_channel=0)
                    except Exception as err:
                        self.logger.error(
                            "Could not check Trigger for channel 0 of output {}: {}".format(
                                self.unique_id, err))

                startup = 'ON' if self.options_channels['state_startup'][0] else 'OFF'
                state = 'HIGH' if self.options_channels['on_state'][0] else 'LOW'
                self.logger.info(
                    "Output setup on pin {pin} and turned {startup} (ON={state})".format(
                        pin=self.options_channels['pin'][0], startup=startup, state=state))
            except Exception as except_msg:
                self.logger.exception(
                    "Output was unable to be setup on pin {pin} with trigger={trigger}: {err}".format(
                        pin=self.options_channels['pin'][0],
                        trigger=self.options_channels['on_state'][0],
                        err=except_msg))

    def output_switch(self, state, output_type=None, amount=None, output_channel=0):
        try:
            if state == 'on':
                self.switch_pin(self.options_channels['pin'][0], self.options_channels['on_state'][output_channel])
            elif state == 'off':
                self.switch_pin(self.options_channels['pin'][0], not self.options_channels['on_state'][output_channel])

            msg = "success"
        except Exception as e:
            msg = "State change error: {}".format(e)
            self.logger.exception(msg)
        return msg

    def is_on(self, output_channel=0):
        if self.is_setup():
            try:
                cmd_return, cmd_error, cmd_status = cmd_output(
                    f"pinctrl get {self.options_channels['pin'][0]}", user="root")
                if "hi" in cmd_return.decode() and self.options_channels['on_state'][output_channel]:
                    return True
                elif "lo" in cmd_return.decode() and not self.options_channels['on_state'][output_channel]:
                    return True
                else:
                    return False
            except Exception as e:
                self.logger.exception(1)
                self.logger.error("Status check error: {}".format(e))

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 1:
                self.output_switch('on', output_channel=0)
            elif self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off', output_channel=0)
        self.running = False

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
