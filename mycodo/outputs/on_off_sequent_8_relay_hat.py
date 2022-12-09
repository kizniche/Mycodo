# coding=utf-8
#
# on_off_sequent_8_relay_hat.py - Output for the 8-Relay HAT by Sequent Microsystems
#
# Code from https://github.com/SequentMicrosystems/8relind-rpi
#
from collections import OrderedDict

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = OrderedDict()
channels_dict = OrderedDict()
for each_channel in range(8):
    measurements_dict[each_channel] = {
        'measurement': 'duration_time',
        'unit': 's'
    }
    channels_dict[each_channel] = {
        'name': f'Relay {each_channel + 1}',
        'types': ['on_off'],
        'measurements': [each_channel]
    }

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'SEQUENT_HAT_8_RELAY',
    'output_name': "{}: Sequent Microsystems 8-Relay HAT for Raspberry Pi".format(lazy_gettext('On/Off')),
    'output_manufacturer': 'Sequent Microsystems',
    'output_library': 'smbus2',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://sequentmicrosystems.com',
    'url_datasheet': 'https://cdn.shopify.com/s/files/1/0534/4392/0067/files/8-RELAYS-UsersGuide.pdf?v=1642820552',
    'url_product_purchase': 'https://sequentmicrosystems.com/products/8-relays-stackable-card-for-raspberry-pi',
    'url_code': 'https://github.com/SequentMicrosystems/8relind-rpi',

    'message': 'Controls the 8 relays of the 8-relay HAT made by Sequent Microsystems. 8 of these boards can be used simultaneously, allowing 64 relays to be controlled.',

    'options_enabled': [
        'i2c_location',
        'button_on',
        'button_send_duration'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x20', '0x21', '0x22', '0x23', '0x24', '0x25', '0x26', '0x27'],
    'i2c_address_editable': False,
    'i2c_address_default': '0x20',

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
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state of the GPIO when Mycodo starts'
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
            'phrase': 'Set the state of the GPIO when Mycodo shuts down'
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
    """An output support class that operates an output"""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.device = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        import smbus2

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            self.logger.debug(f"I2C: Address: {self.output.i2c_location}, Bus: {self.output.i2c_bus}")
            if self.output.i2c_location:
                self.device = RELAYS(smbus2, self.output.i2c_bus, int(str(self.output.i2c_location), 16), self.logger)
                self.device.check()
                self.output_setup = True
        except:
            self.logger.error("Could not set up output. Check the I2C bus and address are correct.")
            return

        for channel in channels_dict:
            if self.options_channels['state_startup'][channel] == 1:
                self.output_switch("on", output_channel=channel)
            else:
                # Default state: Off
                self.output_switch("off", output_channel=channel)

        for channel in channels_dict:
            if self.options_channels['trigger_functions_startup'][channel]:
                try:
                    self.check_triggers(self.unique_id, output_channel=channel)
                except Exception as err:
                    self.logger.error(f"Could not check Trigger for channel {channel}: {err}")

    def output_switch(self,
                      state,
                      output_type=None,
                      amount=None,
                      duty_cycle=None,
                      output_channel=None):
        if output_channel is None:
            msg = "Output channel needs to be specified"
            self.logger.error(msg)
            return msg

        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        try:
            if state == 'on':
                self.device.set(output_channel + 1, self.options_channels['on_state'][output_channel])
                self.output_states[output_channel] = bool(self.options_channels['on_state'][output_channel])
            elif state == 'off':
                self.device.set(output_channel + 1, not self.options_channels['on_state'][output_channel])
                self.output_states[output_channel] = bool(not self.options_channels['on_state'][output_channel])

            msg = "success"
        except Exception as err:
            msg = f"CH{output_channel} state change error: {err}"
            self.logger.error(msg)
        return msg

    def is_on(self, output_channel=None):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel] == self.options_channels['on_state'][output_channel]

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        dict_states = {}
        if self.is_setup():
            for channel in channels_dict:
                if self.options_channels['state_shutdown'][channel] == 1:
                    self.output_switch("on", output_channel=channel)
                elif self.options_channels['state_shutdown'][channel] == 0:
                    self.output_switch("off", output_channel=channel)
        self.running = False


class RELAYS:
    """
    A Class to support the Sequent Microsystems 8-Relay HAT for the Raspberry Pi
    I2C addresses range: 0x20 - 0x27
    Relay number range: 0 - 7
    Adapted from the code at https://github.com/SequentMicrosystems/8relind-rpi
    """
    RELAY8_INPORT_REG_ADD = 0x00
    RELAY8_OUTPORT_REG_ADD = 0x01
    RELAY8_POLINV_REG_ADD = 0x02
    RELAY8_CFG_REG_ADD = 0x03
    relayMaskRemap = [0x01, 0x04, 0x40, 0x10, 0x20, 0x80, 0x08, 0x02]

    def __init__(self, smbus, bus, address, logger):
        self.address = address
        self.logger = logger
        self.bus = smbus.SMBus(bus)

    def relayToIO(self, relay):
        val = 0
        for i in range(0, 8):
            if (relay & (1 << i)) != 0:
                val = val + self.relayMaskRemap[i]
        return val

    def IOToRelay(self, iov):
        val = 0
        for i in range(0, 8):
            if (iov & self.relayMaskRemap[i]) != 0:
                val = val + (1 << i)
        return val

    def check(self):
        cfg = self.bus.read_byte_data(self.address, self.RELAY8_CFG_REG_ADD)
        if cfg != 0:
            self.bus.write_byte_data(self.address, self.RELAY8_CFG_REG_ADD, 0)
            self.bus.write_byte_data(self.address, self.RELAY8_OUTPORT_REG_ADD, 0)
        return self.bus.read_byte_data(self.address, self.RELAY8_INPORT_REG_ADD)

    def set(self, relay, value):
        if relay < 1:
            raise ValueError('Invalid relay number!')
        if relay > 8:
            raise ValueError('Invalid relay number!')

        try:
            oldVal = self.check()
        except Exception as e:
            self.bus.close()
            raise ValueError('8-relay card not detected!')

        oldVal = self.IOToRelay(oldVal)
        try:
            if value == 0:
                oldVal = oldVal & (~(1 << (relay - 1)))
                oldVal = self.relayToIO(oldVal)
                self.bus.write_byte_data(self.address, self.RELAY8_OUTPORT_REG_ADD, oldVal)
            else:
                oldVal = oldVal | (1 << (relay - 1))
                oldVal = self.relayToIO(oldVal)
                self.bus.write_byte_data(self.address, self.RELAY8_OUTPORT_REG_ADD, oldVal)
        except Exception as e:
            self.bus.close()
            raise ValueError('Fail to write relay state value!')
        self.bus.close()

    def set_all(self, value):
        if value > 255:
            raise ValueError('Invalid relay value!')
        if value < 0:
            raise ValueError('Invalid relay value!')

        try:
            oldVal = self.check()
        except Exception as e:
            self.bus.close()
            raise ValueError('8-relay card not detected!')
        value = self.relayToIO(value)
        try:
            self.bus.write_byte_data(self.address, self.RELAY8_OUTPORT_REG_ADD, value)
        except Exception as e:
            self.bus.close()
            raise ValueError('Fail to write relay state value!')
        self.bus.close()

    def get(self, relay):
        if relay < 1:
            raise ValueError('Invalid relay number!')
        if relay > 8:
            raise ValueError('Invalid relay number!')

        try:
            val = self.check()
        except Exception as e:
            self.bus.close()
            raise ValueError('8-relay card not detected!')

        val = self.IOToRelay(val)
        val = val & (1 << (relay - 1))
        self.bus.close()
        if val == 0:
            return 0
        else:
            return 1

    def get_all(self):
        try:
            val = self.check()
        except Exception as e:
            self.bus.close()
            raise ValueError('8-relay card not detected!')

        val = self.IOToRelay(val)
        self.bus.close()
        return val
