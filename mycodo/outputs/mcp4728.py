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
        'types': ['volt'],
        'measurements': [0]
    },
    1: {
        'name': 'Channel B',
        'types': ['volt'],
        'measurements': [1]
    },
    2: {
        'name': 'Channel C',
        'types': ['volt'],
        'measurements': [2]
    },
    3: {
        'name': 'Channel D',
        'types': ['volt'],
        'measurements': [3]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'mcp4728',
    'output_name': "{}: MCP4728".format(lazy_gettext('Digital-to-Analog Converter')),
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['volt'],

    'url_manufacturer': 'https://www.microchip.com/wwwproducts/en/en541737',
    'url_datasheet': 'https://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/4470',

    'options_enabled': [
        'i2c_location',
        'button_send_voltage'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'adafruit_mcp4728', 'adafruit-circuitpython-mcp4728'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit_Extended_Bus')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x60'],
    'i2c_address_editable': True,
    
    'custom_channel_options': [
        {
            'id': 'vref',
            'type': 'float',
            'default_value': 4.096,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'VREF (volts)',
            'phrase': 'Set the VREF voltage'
        },
        {
            'id': 'a_vref',
            'type': 'select',
            'default_value': 'internal',
            'options_select': [
                ('internal', 'Internal'),
                ('vdd', 'VDD')
            ],
            'name': 'Channel A VREF',
            'phrase': 'Select the VREF for channel A'
        },
        {
            'id': 'a_gain',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, '1X'),
                (2, '2X')
            ],
            'name': 'Channel A Gain',
            'phrase': 'Select the Gain for channel A'
        },
        {
            'id': 'b_vref',
            'type': 'select',
            'default_value': 'Internal',
            'options_select': [
                ('internal', 'Internal'),
                ('vdd', 'VDD')
            ],
            'name': 'Channel B VREF',
            'phrase': 'Select the VREF for channel B'
        },
        {
            'id': 'b_gain',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, '1X'),
                (2, '2X')
            ],
            'name': 'Channel B Gain',
            'phrase': 'Select the Gain for channel B'
        },
        {
            'id': 'c_vref',
            'type': 'select',
            'default_value': 'Internal',
            'options_select': [
                ('internal', 'Internal'),
                ('vdd', 'VDD')
            ],
            'name': 'Channel C VREF',
            'phrase': 'Select the VREF for channel C'
        },
        {
            'id': 'c_gain',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, '1X'),
                (2, '2X')
            ],
            'name': 'Channel C Gain',
            'phrase': 'Select the Gain for channel C'
        },
        {
            'id': 'd_vref',
            'type': 'select',
            'default_value': 'Internal',
            'options_select': [
                ('internal', 'Internal'),
                ('vdd', 'VDD')
            ],
            'name': 'Channel D VREF',
            'phrase': 'Select the VREF for channel D'
        },
        {
            'id': 'd_gain',
            'type': 'select',
            'default_value': 1,
            'options_select': [
                (1, '1X'),
                (2, '2X')
            ],
            'name': 'Channel D Gain',
            'phrase': 'Select the Gain for channel D'
        },
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
        self.a_vref = None
        self.a_gain = None
        self.b_vref = None
        self.b_gain = None
        self.c_vref = None
        self.c_gain = None
        self.d_vref = None
        self.d_gain = None

        # For testing, TODO: REMOVE
        # self.channel_state = {}
        # self.channel_state[0] = False
        # self.channel_state[1] = False
        # self.channel_state[2] = False
        # self.channel_state[3] = False

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        import adafruit_mcp4728
        from adafruit_extended_bus import ExtendedI2C

        self.setup_on_off_output(OUTPUT_INFORMATION)

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
            if self.a_vref == "internal":
                self.channel[0].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[0].vref = adafruit_mcp4728.Vref.VDD
            self.channel[0].gain = self.a_gain

            # Channel B
            if self.b_vref == "internal":
                self.channel[1].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[1].vref = adafruit_mcp4728.Vref.VDD
            self.channel[1].gain = self.b_gain

            # Channel C
            if self.c_vref == "internal":
                self.channel[2].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[2].vref = adafruit_mcp4728.Vref.VDD
            self.channel[2].gain = self.c_gain

            # Channel D
            if self.d_vref == "internal":
                self.channel[3].vref = adafruit_mcp4728.Vref.INTERNAL
            else:
                self.channel[3].vref = adafruit_mcp4728.Vref.VDD
            self.channel[3].gain = self.d_gain

            self.dac.save_settings()

            self.output_setup = True
        except:
            self.output_setup = True

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if state == 'on' and amount and output_channel is not None:
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

    # For testing, TODO: REMOVE
    # def output_switch(self, state, output_type=None, amount=None, output_channel=None):
    #     if state == 'on' and amount and output_channel is not None:
    #         self.channel_state[output_channel] = amount
    #         self.logger.error("TEST00: {}, {}, {}".format(output_type, output_channel, amount))
    #     elif (state == 'off' or (amount is not None and amount <= 0)) and output_channel is not None:
    #         self.channel_state[output_channel] = 0
    #         self.logger.error("TEST01: {}, {}, {}".format(output_type, output_channel, amount))
    #     else:
    #         self.logger.error(
    #             "Invalid parameters: State: {state}, Type: {ot}, Amount: {amt}".format(
    #                 state=state,
    #                 ot=output_type,
    #                 amt=amount))
    #         return

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.channel[output_channel].value:
                return self.channel[output_channel].value
            else:
                return False

    # For testing, TODO: REMOVE
    # def is_on(self, output_channel=None):
    #     if self.is_setup():
    #         if self.channel_state[output_channel]:
    #             self.logger.error("TEST03: {}".format(self.channel_state[output_channel]))
    #             return self.channel_state[output_channel]
    #         else:
    #             return False

    def is_setup(self):
        if self.output_setup:
            return True
        return False
