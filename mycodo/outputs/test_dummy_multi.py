# coding=utf-8
#
# pcf8574.py - Output for PCF8574
#
import datetime

from mycodo.outputs.base_output import AbstractOutput

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
    },
    7: {
        'measurement': 'duration_time',
        'unit': 's',
    }
}

outputs_dict = {
    0: {
        'types': ['on_off'],
        'measurements': [0]
    },
    1: {
        'types': ['on_off'],
        'measurements': [1]
    },
    2: {
        'types': ['on_off'],
        'measurements': [2]
    },
    3: {
        'types': ['on_off'],
        'measurements': [3]
    },
    4: {
        'types': ['on_off'],
        'measurements': [4]
    },
    5: {
        'types': ['on_off'],
        'measurements': [5]
    },
    6: {
        'types': ['on_off'],
        'measurements': [6]
    },
    7: {
        'types': ['on_off'],
        'measurements': [7]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'TEST_MULTI',
    'output_name': "TEST DUMMY MULTI",
    'output_library': '',
    'measurements_dict': measurements_dict,
    'outputs_dict': outputs_dict,
    'output_types': ['on_off'],

    'options_enabled': [
        'i2c_location',
        'on_off_state_on',
        'on_off_state_startup',
        'on_off_state_shutdown',
        'trigger_functions_startup',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x20', '0x21', '0x22', '0x23', '0x24', '0x25', '0x26', '0x27',
        '0x38', '0x39', '0x3a', '0x3b', '0x3c', '0x3d', '0x3e', '0x3f'
    ],
    'i2c_address_editable': False,
    'i2c_address_default': '0x20',
}


class OutputModule(AbstractOutput):
    """ An output support class that operates an output """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.sensor = None
        self.output_on_state = None
        self.state_startup = None
        self.state_shutdown = None

    def setup_output(self):
        self.setup_on_off_output(OUTPUT_INFORMATION)
        self.output_on_state = self.output.on_state
        self.state_startup = self.output.state_startup
        self.state_shutdown = self.output.state_shutdown
        self.output_setup = True

        for each_output_channel in self.output_states:
            if self.state_startup == '1':
                self.output_switch('on', output_channel=each_output_channel)
            elif self.state_startup == '0':
                self.output_switch('off', output_channel=each_output_channel)

    def output_switch(self,
                      state,
                      output_type=None,
                      amount=None,
                      duty_cycle=None,
                      output_channel=None):
        if output_channel is None:
            self.logger.error("Output channel needs to be specified")
            return

        try:
            if state == 'on':
                self.output_states[output_channel] = self.output_on_state
            elif state == 'off':
                self.output_states[output_channel] = not self.output_on_state
        except Exception as e:
            self.logger.error("State change error: {}".format(e))

    def is_on(self, output_channel=None):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        for each_output_channel in self.output_states:
            if self.state_shutdown == '1':
                self.output_switch('on', output_channel=each_output_channel)
            elif self.state_shutdown == '0':
                self.output_switch('off', output_channel=each_output_channel)
        self.running = False
