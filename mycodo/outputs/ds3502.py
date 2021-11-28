# coding=utf-8
#
# ds3502.py - Output for DS3502
#
import math

from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput


# Measurements
measurements_dict = {
    0: {
        'measurement': 'resistance',
        'unit': 'Ohm'
    }
}

channels_dict = {
    0: {
        'types': ['value'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'ds3502',
    'output_name': "{}: DS3502".format(lazy_gettext('Digital Potentiometer')),
    'output_manufacturer': 'Maxim Integrated',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value'],

    'url_manufacturer': 'https://www.maximintegrated.com/en/products/analog/data-converters/digital-potentiometers/DS3502.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/DS3502.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/4286',

    'message': 'The DS3502 can generate a 0 - 10k Ohm resistance with 7-bit precision. This equates to 128 possible steps. A value, in Ohms, is passed to this output controller and the step value is calculated and passed to the device. Select whether to round up or down to the nearest step.',

    'options_enabled': [
        'i2c_location',
        'button_send_value'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit_Extended_Bus'),
        ('pip-pypi', 'adafruit_ds3502', 'adafruit-circuitpython-ds3502')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x28', '0x29', '0x2a', '0x2b'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'round',
            'type': 'select',
            'default_value': 'up',
            'options_select': [
                ('up', 'Up'),
                ('down', 'Down')
            ],
            'name': 'Round Step',
            'phrase': 'Round direction to the nearest step value'
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.dpot = None
        self.channel_value = None
        self.round = None

    def setup_output(self):
        import adafruit_ds3502
        from adafruit_extended_bus import ExtendedI2C

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            self.dpot = adafruit_ds3502.DS3502(
                ExtendedI2C(self.output.i2c_bus),
                address=int(str(self.output.i2c_location), 16))
        except Exception as err:
            self.logger.error("Setting up Output: {}".format(err))

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if amount > 10000:
            self.logger.error(
                "Amount cannot be greater than 10000. Value passed: {}. "
                "Setting to 10000.".format(amount))
            amount = 10000
        if amount < 0:
            self.logger.error(
                "Amount cannot be less than 0. Value passed: {}. "
                "Setting to 0.".format(amount))
            amount = 0

        if state == 'on' and None not in [amount, output_channel]:
            if amount == 0:
                step = 0
            else:
                if self.round == "up":
                    step = math.ceil((amount / 10000) * 128) - 1
                else:
                    step = math.floor((amount / 10000) * 128) - 1
            self.channel_value = amount
            self.dpot.wiper = step
        elif state == 'off' or (amount is not None and amount <= 0):
            self.channel_value = amount
            self.dpot.wiper = 0
        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Type: {ot}, Amount: {amt}".format(
                    state=state,
                    ot=output_type,
                    amt=amount))
            return

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.channel_value:
                return self.channel_value
            else:
                return False

    def is_setup(self):
        if self.dpot:
            return True
        return False
