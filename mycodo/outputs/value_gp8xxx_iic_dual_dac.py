# coding=utf-8
#
# value_gp8xxx_iic_dual_dac.py - Output for controlling the GP8XXX 2-channel DAC (0-10 VDC)
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
    'output_name_unique': 'OUTPUT_GP8XXX_IIC_DUAL_DAC_0_10_VDC',
    'output_name': "{}: GP8XXX (8413, 8403) 2-Channel DAC: 0-10 VDC".format(lazy_gettext('Value')),
    'output_library': 'GP8XXX-IIC',
    'output_manufacturer': 'DFRobot',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value'],

    'url_datasheet': ['https://wiki.dfrobot.com/SKU_DFR0971_2_Channel_I2C_0_10V_DAC_Module',
                      'https://wiki.dfrobot.com/SKU_DFR1073_2_Channel_15bit_I2C_to_0-10V_DAC'],

    'url_product_purchase': ['https://www.dfrobot.com/product-2613.html',
                             'https://www.dfrobot.com/product-2756.html'],

    'message': 'Output 0 to 10 VDC signal.\
                GP8403: 12bit DAC Dual Channel I2C to 0-5V/0-10V |\
                GP8413: 15bit DAC Dual Channel I2C to 0-10V',

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1'),
        ('pip-pypi', 'GP8XXX_IIC', 'GP8XXX-IIC==0.0.4')
    ],

    'options_enabled': [
        'i2c_location',
        'button_send_value'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['I2C'],
    'i2c_location': ['0x58', '0x59', '0x5A', '0x5B', '0x5C', '0x5D', '0x5E', '0x5F'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'chip_select',
            'type': 'select',
            'default_value': '0',
            'options_select': [
                ('0', 'GP8403 12-bit'),
                ('1', 'GP8413 15-bit'),
            ],
            'name': 'Device',
            'phrase': 'Select your GP8XXX device'
        }
    ],

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

        self.dac_chip = None
        self.chip_select = None
        self.i2c_addr = None
        self.bus = None

        self.setup_custom_options(OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(OutputChannel).filter(
            OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

        if not testing:
            self.try_initialize()

    def initialize(self):
        import GP8XXX_IIC

        self.setup_output_variables(OUTPUT_INFORMATION)

        if self.output.i2c_bus == '' or self.output.i2c_location == '':
            self.logger.error("I2C Bus information is missing.\nI2C: Address: %s, Bus: %s",
                              self.output.i2c_location, self.output.i2c_bus)
            return
        self.logger.debug("I2C: Address: %s, Bus: %s",
                          self.output.i2c_location, self.output.i2c_bus)

        self.i2c_addr = int(str(self.output.i2c_location), 16)
        self.bus = int(str(self.output.i2c_bus))

        try:
            if self.chip_select == '0':
                self.dac_chip = GP8XXX_IIC.GP8403(
                    bus=self.bus, i2c_addr=self.i2c_addr)
            elif self.chip_select == '1':
                self.dac_chip = GP8XXX_IIC.GP8413(
                    bus=self.bus, i2c_addr=self.i2c_addr)
            else:
                self.logger.error(
                    "No Chip selected! Choose between GP8403 or GP8413.")
                return

            timer = time.time()
            while self.dac_chip.begin():
                self.logger.error("init error")
                if time.time() - timer > 5:  # Max 5 second wait
                    self.logger.error("Could not initialize after 5 seconds")
                    return
                time.sleep(1)

            # Set start channel values
            for channel in channels_dict:
                value_volts = None

                if (self.options_channels['state_start'][channel] == "value" and self.options_channels['state_start_value'][channel]):
                    value_volts = self.options_channels['state_start_value'][channel]
                elif (self.options_channels['state_start'][channel] == "saved" and self.get_custom_option(f"saved_channel_{channel}_value") is not None):
                    value_volts = self.get_custom_option(
                        f"saved_channel_{channel}_value")

                if value_volts is not None:
                    if self.options_channels['state_start_value'][channel] > 10:
                        self.logger.error(
                            "Startup value cannot be greater than 10 VDC. Value provided: %s. Changed value to 10", value_volts)
                        value_volts = 10
                    elif self.options_channels['state_start_value'][channel] < 0:
                        self.logger.error(
                            "Startup value cannot be less than 0 VDC. Value provided: %s. Changed value to 0", value_volts)
                        value_volts = 0

                    self.logger.debug("Set DAC to value: %s VDC", value_volts)
                    self.dac_chip.set_dac_out_voltage(
                        voltage=value_volts, channel=channel)
            self.output_setup = True

        except Exception as e:
            self.logger.exception("Error setting up Output %s", e)

    def check_value(self, value_volts):
        if value_volts > 10:
            self.logger.error(
                "Value cannot be greater than 10 VDC. Value provided: %s. Changed value to 10", value_volts)
            value_volts = 10
        elif value_volts < 0:
            self.logger.error(
                "Value cannot be less than 0 VDC. Value provided: %s. Changed value to 0", value_volts)
            value_volts = 0
        return value_volts

    def output_switch(self, state, output_type=None, amount=None, output_channel=0):
        measure_dict = copy.deepcopy(measurements_dict)
        value_volts = amount

        try:
            if state == 'on' and amount is not None:
                value_volts = self.check_value(value_volts)

                self.dac_chip.set_dac_out_voltage(
                    voltage=value_volts, channel=output_channel)
                self.output_states[output_channel] = value_volts
                measure_dict[output_channel]['value'] = value_volts

                self.set_custom_option(
                    f"saved_channel_{output_channel}_value", value_volts)
            elif state == 'off':
                self.dac_chip.set_dac_out_voltage(
                    voltage=self.options_channels['off_value'][output_channel], channel=output_channel)
                if self.options_channels['off_value'][output_channel]:
                    self.output_states[output_channel] = self.options_channels['off_value'][output_channel]
                else:
                    self.output_states[output_channel] = False
                measure_dict[output_channel]['value'] = self.options_channels['off_value'][output_channel]

                self.set_custom_option(
                    f"saved_channel_{output_channel}_value", value_volts)

        except Exception as e:
            self.logger.error("State change error %s", e)
            return

        add_measurements_influxdb(self.unique_id, measure_dict)

    def is_on(self, output_channel=0):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            return self.output_states

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            for channel in channels_dict:
                value_volts = None

                if (self.options_channels['state_shutdown'][channel] == "value" and
                        self.options_channels['state_shutdown_value'][channel]):
                    value_volts = self.options_channels['state_shutdown_value'][channel]

                elif (self.options_channels['state_shutdown'][channel] == "saved" and
                      self.get_custom_option(f"saved_channel_{channel}_value") is not None):
                    value_volts = self.get_custom_option(
                        f"saved_channel_{channel}_value")

                if value_volts is not None:
                    value_volts = self.check_value(value_volts)
                    self.dac_chip.set_dac_out_voltage(
                        voltage=value_volts, channel=channel)

        self.running = False
