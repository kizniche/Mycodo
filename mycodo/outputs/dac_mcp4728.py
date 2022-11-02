# coding=utf-8
#
# dac_mcp4728.py - Output for MCP4728 digital-to-analog converter
#
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon

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
    'output_name': "{}: MCP4728".format(lazy_gettext('Digital-to-Analog Converter')),
    'output_manufacturer': 'MICROCHIP',
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
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_mcp4728', 'adafruit-circuitpython-mcp4728==1.2.0')
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
            'id': 'name',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        },
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
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.dac = None
        self.channel = {}
        self.vref = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
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

            # Set up Channels
            for channel in channels_dict:
                if self.options_channels['vref'][channel] == "internal":
                    self.channel[channel].vref = adafruit_mcp4728.Vref.INTERNAL
                else:
                    self.channel[channel].vref = adafruit_mcp4728.Vref.VDD
                self.channel[channel].gain = self.options_channels['gain'][channel]
                if (self.options_channels['state_start'][channel] == "value" and
                        self.options_channels['state_start_value'][channel]):
                    self.channel[channel].value = int(65535 * (
                        self.options_channels['state_start_value'][channel] / self.vref))

            self.dac.save_settings()
            self.output_setup = True
        except:
            self.logger.exception("Error setting up Output")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

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
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            for channel in channels_dict:
                if (self.options_channels['state_shutdown'][channel] == "value" and
                        self.options_channels['state_shutdown_value'][channel]):
                    self.channel[channel].value = int(65535 * (
                            self.options_channels['state_shutdown_value'][channel] / self.vref))

        self.running = False
