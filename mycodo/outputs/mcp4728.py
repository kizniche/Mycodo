# coding=utf-8
#
# mcp4728.py - Output for MCP4728
#
from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


def constraints_pass_positive_or_zero_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value < 0:
        all_passed = False
        errors.append("Must be zero or a positive value")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'electrical_potential',
        'unit': 'V'
    },
    1: {
        'measurement': 'electrical_potential',
        'unit': 'V'
    },
    2: {
        'measurement': 'electrical_potential',
        'unit': 'V'
    },
    3: {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }
}

channels_dict = {
    0: {
        'name': 'Channel A',
        'types': ['value'],
        'measurements': [0]
    },
    1: {
        'name': 'Channel B',
        'types': ['value'],
        'measurements': [1]
    },
    2: {
        'name': 'Channel C',
        'types': ['value'],
        'measurements': [2]
    },
    3: {
        'name': 'Channel D',
        'types': ['value'],
        'measurements': [3]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'mcp4728',
    'output_name': "MCP4728 {}: {}".format(
        lazy_gettext('Digital-to-Analog Converter'),
        lazy_gettext('Value')),
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value'],

    'url_manufacturer': 'https://www.microchip.com/wwwproducts/en/en541737',
    'url_datasheet': 'https://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/4470',

    'options_enabled': [
        'i2c_location',
        'button_send_value'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit_Extended_Bus'),
        ('pip-pypi', 'adafruit_mcp4728', 'adafruit-circuitpython-mcp4728')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x60'],
    'i2c_address_editable': True,

    'custom_options': [
        {
            'id': 'vref',
            'type': 'float',
            'default_value': 4.096,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'VREF (volts)',
            'phrase': 'Set the VREF voltage'
        }
    ],

    'custom_channel_options': [
        {
            'id': 'vref',
            'type': 'select',
            'default_value': 'internal',
            'options_select': [
                ('internal', 'Internal'),
                ('vdd', 'VDD')
            ],
            'name': 'VREF',
            'phrase': 'Select the channel VREF'
        },
        {
            'id': 'gain',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, '1X'),
                (2, '2X')
            ],
            'name': 'Gain',
            'phrase': 'Select the channel Gain'
        },
        {
            'id': 'state_start',
            'type': 'select',
            'default_value': 'saved',
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
            'default_value': 'saved',
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
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.dac = None
        self.channel = {}
        self.output_setup = False
        self.vref = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        import adafruit_mcp4728
        from adafruit_extended_bus import ExtendedI2C

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            self.dac = adafruit_mcp4728.MCP4728(
                ExtendedI2C(self.output.i2c_bus),
                address=int(str(self.output.i2c_location), 16))

            self.channel = {
                0: self.dac.channel_a,
                1: self.dac.channel_b,
                2: self.dac.channel_c,
                3: self.dac.channel_d
            }

            # Channel A
            if self.options_channels['vref'][0] == "internal":
                self.channel[0].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[0].vref = adafruit_mcp4728.Vref.VDD
            self.channel[0].gain = self.options_channels['gain'][0]
            if (self.options_channels['state_start'][0] == "value" and
                    self.options_channels['state_start_value'][0]):
                self.channel[0].value = int(65535 * (
                    self.options_channels['state_start_value'][0] / self.vref))

            # Channel B
            if self.options_channels['vref'][1] == "internal":
                self.channel[1].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[1].vref = adafruit_mcp4728.Vref.VDD
            self.channel[1].gain = self.options_channels['gain'][1]
            if (self.options_channels['state_start'][1] == "value" and
                    self.options_channels['state_start_value'][1]):
                self.channel[1].value = int(65535 * (
                    self.options_channels['state_start_value'][1] / self.vref))

            # Channel C
            if self.options_channels['vref'][2] == "internal":
                self.channel[2].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[2].vref = adafruit_mcp4728.Vref.VDD
            self.channel[2].gain = self.options_channels['gain'][2]
            if (self.options_channels['state_start'][2] == "value" and
                    self.options_channels['state_start_value'][2]):
                self.channel[2].value = int(65535 * (
                    self.options_channels['state_start_value'][2] / self.vref))

            # Channel D
            if self.options_channels['vref'][3] == "internal":
                self.channel[3].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[3].vref = adafruit_mcp4728.Vref.VDD
            self.channel[3].gain = self.options_channels['gain'][3]
            if (self.options_channels['state_start'][3] == "value" and
                    self.options_channels['state_start_value'][3]):
                self.channel[3].value = int(65535 * (
                    self.options_channels['state_start_value'][3] / self.vref))

            self.dac.save_settings()

            self.output_setup = True
        except:
            self.output_setup = False

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if state == 'on' and None not in [amount, output_channel]:
            self.channel[output_channel].value = int(65535 * (amount / self.vref))
        elif state == 'off' or (amount is not None and amount <= 0):
            self.channel[output_channel].value = 0
        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Type: {ot}, Amount: {amt}".format(
                    state=state,
                    ot=output_type,
                    amt=amount))
            return
        self.dac.save_settings()

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.channel[output_channel].value:
                return self.channel[output_channel].value
            else:
                return False

    def is_setup(self):
        if self.output_setup:
            return True
        return False

    def stop_output(self):
        """ Called when Output is stopped """
        if (self.options_channels['state_shutdown'][0] == "value" and
                self.options_channels['state_shutdown_value'][0]):
            self.channel[0].value = int(65535 * (
                    self.options_channels['state_shutdown_value'][0] / self.vref))

        if (self.options_channels['state_shutdown'][1] == "value" and
                self.options_channels['state_shutdown_value'][1]):
            self.channel[1].value = int(65535 * (
                    self.options_channels['state_shutdown_value'][1] / self.vref))

        if (self.options_channels['state_shutdown'][2] == "value" and
                self.options_channels['state_shutdown_value'][2]):
            self.channel[2].value = int(65535 * (
                    self.options_channels['state_shutdown_value'][2] / self.vref))

        if (self.options_channels['state_shutdown'][3] == "value" and
                self.options_channels['state_shutdown_value'][3]):
            self.channel[3].value = int(65535 * (
                    self.options_channels['state_shutdown_value'][3] / self.vref))

        self.running = False
