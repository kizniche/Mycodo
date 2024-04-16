# coding=utf-8
#
# value_gp8403_dac_p8403.py - Output for controlling the GP8403 2-channel DAC (0-10 VDC)
#
import copy
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb

measurements_dict = {
    0: {
        'measurement': 'electrical_potential',
        'unit': 'V'
    },
    1: {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }
}

channels_dict = {
    0: {
        'types': ['value'],
        'measurements': [0]
    },
    1: {
        'types': ['value'],
        'measurements': [1]
    }
}

OUTPUT_INFORMATION = {
    'output_name_unique': 'OUTPUT_GP8403_DAC_0_10_VDC',
    'output_name': "{}: GP8403 2-Channel DAC: 0-10 VDC (Pi <= 4)".format(lazy_gettext('Value')),
    'output_library': 'DFRobot-GP8403, RPi.GPIO',
    'output_manufacturer': 'Mycodo',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value'],

    'url_additional': 'https://www.dfrobot.com/product-2613.html',

    'message': 'Output a 0 to 10 VDC signal.',

    'dependencies_module': [
        ('pip-pypi', 'lgpio', 'lgpio==0.2.2.0'),
        ('pip-pypi', 'DFRobot.DAC', 'DFRobot-GP8403==0.1.1')
    ],

    'options_enabled': [
        'i2c_location',
        'button_send_value'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['I2C'],
    'i2c_location': ['0x58'],
    'i2c_address_editable': True,

    'custom_channel_options': [
        {
            'id': 'state_start',
            'type': 'select',
            'default_value': 'value',
            'options_select': [
                ('saved', 'Previously-Saved State'),
                ('value', 'Specified Value')
            ],
            'name': 'Start State',
            'phrase': 'Select the channel start state'
        },
        {
            'id': 'state_start_value',
            'type': 'float',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Start Value (volts)',
            'phrase': 'If Specified Value is selected, set the start state value'
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 'value',
            'options_select': [
                ('saved', 'Previously-Saved Value'),
                ('value', 'Specified Value')
            ],
            'name': 'Shutdown State',
            'phrase': 'Select the channel shutdown state'
        },
        {
            'id': 'state_shutdown_value',
            'type': 'float',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Shutdown Value (volts)',
            'phrase': 'If Specified Value is selected, set the shutdown state value'
        },
        {
            'id': 'off_value',
            'type': 'float',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Off Value (volts)',
            'phrase': 'If Specified Value to apply when turned off'
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.GP8403 = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        from DFRobot.DAC import GP8403

        self.GP8403 = GP8403(bus=self.output.i2c_bus, addr=int(str(self.output.i2c_location), 16))

        self.setup_output_variables(OUTPUT_INFORMATION)

        timer = time.time()
        while self.GP8403.begin() != 0:
            self.logger.error("init error")
            if time.time() - timer > 5:  # Max 5 second wait
                self.logger.error("Could not initialize after 5 seconds")
                return
            time.sleep(1)

        self.GP8403.set_DAC_outrange(self.GP8403.OUTPUT_RANGE_10V)

        # Set start channel values
        for channel in channels_dict:
            value_volts = None

            if channel == 0:
                chan = self.GP8403.CHANNEL0
            elif channel == 1:
                chan = self.GP8403.CHANNEL1
            else:
                return

            if (self.options_channels['state_start'][channel] == "value" and
                    self.options_channels['state_start_value'][channel]):
                value_volts = self.options_channels['state_start_value'][channel]
            elif (self.options_channels['state_start'][channel] == "saved" and
                    self.get_custom_option(f"saved_channel_{channel}_value") is not None):
                value_volts = self.get_custom_option(f"saved_channel_{channel}_value")

            if value_volts is not None:
                if self.options_channels['state_start_value'][channel] > 10:
                    self.logger.error(f"Startup value cannot be greater than 10 VDC. Value provided: {value_volts}")
                    value = 4096
                elif self.options_channels['state_start_value'][channel] < 0:
                    self.logger.error(f"Startup value cannot be less than 0 VDC. Value provided: {value_volts}")
                    value = 0
                else:
                    value = value_volts / 10 * 4096
                self.GP8403.set_DAC_out_voltage(value, chan)

        self.output_setup = True

    def output_switch(self, state, output_type=None, amount=None, output_channel=0):
        measure_dict = copy.deepcopy(measurements_dict)

        try:
            if output_channel == 0:
                chan = self.GP8403.CHANNEL0
            elif output_channel == 1:
                chan = self.GP8403.CHANNEL1
            else:
                self.logger.error(f"Invalid channel: {output_channel}")
                return

            if state == 'on' and amount is not None:
                if amount > 10:
                    self.logger.error(f"Startup value cannot be greater than 10 VDC. Value provided: {amount}")
                    value = 4096
                elif amount < 0:
                    self.logger.error(f"Startup value cannot be less than 0 VDC. Value provided: {amount}")
                    value = 0
                else:
                    value = amount / 10 * 4096

                self.GP8403.set_DAC_out_voltage(value, chan)
                self.output_states[output_channel] = amount
                measure_dict[output_channel]['value'] = amount

                self.set_custom_option(f"saved_channel_{output_channel}_value", amount)
            elif state == 'off':
                self.GP8403.set_DAC_out_voltage(self.options_channels['off_value'][output_channel], chan)
                if self.options_channels['off_value'][output_channel]:
                    self.output_states[output_channel] = self.options_channels['off_value'][output_channel]
                else:
                    self.output_states[output_channel] = False
                measure_dict[output_channel]['value'] = self.options_channels['off_value'][output_channel]

                self.set_custom_option(f"saved_channel_{output_channel}_value", amount)
        except Exception as e:
            self.logger.error("State change error: {}".format(e))
            return

        add_measurements_influxdb(self.unique_id, measure_dict)

    def is_on(self, output_channel=0):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            for channel in channels_dict:
                value_volts = None

                if channel == 0:
                    chan = self.GP8403.CHANNEL0
                elif channel == 1:
                    chan = self.GP8403.CHANNEL1
                else:
                    continue

                if (self.options_channels['state_shutdown'][channel] == "value" and
                        self.options_channels['state_shutdown_value'][channel]):
                    value_volts = self.options_channels['state_shutdown_value'][channel]
                elif (self.options_channels['state_shutdown'][channel] == "saved" and
                      self.get_custom_option(f"saved_channel_{channel}_value") is not None):
                    value_volts = self.get_custom_option(f"saved_channel_{channel}_value")

                if value_volts is not None:
                    if value_volts > 10:
                        self.logger.error(f"Startup value cannot be greater than 10 VDC. Value provided: {value_volts}")
                        value = 4096
                    elif value_volts < 0:
                        self.logger.error(f"Startup value cannot be less than 0 VDC. Value provided: {value_volts}")
                        value = 0
                    else:
                        value = value_volts / 10 * 4096

                    self.GP8403.set_DAC_out_voltage(value, chan)

        self.running = False
