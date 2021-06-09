# coding=utf-8
#
# grove_multichannel_relay.py - Output for the Grove Multichannel Relay
#
from flask import flash
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon


def execute_at_modification(
        mod_output,
        request_form,
        custom_options_dict_presave,
        custom_options_channels_dict_presave,
        custom_options_dict_postsave,
        custom_options_channels_dict_postsave):
    """
    This function allows you to view and modify the output and channel settings when the user clicks
    save on the user interface. Both the output and channel settings are passed to this function, as
    dictionaries. Additionally, both the pre-saved and post-saved options are available, as it's
    sometimes useful to know what settings changed and from what values. You can modify the post-saved
    options and these will be stored in the database.
    :param mod_output: The post-saved output database entry, minus the custom_options settings
    :param request_form: The requests.form object the user submitted
    :param custom_options_dict_presave: dict of pre-saved custom output options
    :param custom_options_channels_dict_presave: dict of pre-saved custom output channel options
    :param custom_options_dict_postsave: dict of post-saved custom output options
    :param custom_options_channels_dict_postsave: dict of post-saved custom output channel options
    :return:
    """
    allow_saving = True
    success = []
    error = []
    for each_error in error:
        flash(each_error, 'error')
    for each_success in success:
        flash(each_success, 'success')
    return (allow_saving,
            mod_output,
            custom_options_dict_postsave,
            custom_options_channels_dict_postsave)

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

channels_dict = {
    0: {
        'name': 'Relay 1',
        'types': ['on_off'],
        'measurements': [0]
    },
    1: {
        'name': 'Relay 2',
        'types': ['on_off'],
        'measurements': [1]
    },
    2: {
        'name': 'Relay 3',
        'types': ['on_off'],
        'measurements': [2]
    },
    3: {
        'name': 'Relay 4',
        'types': ['on_off'],
        'measurements': [3]
    },
    4: {
        'name': 'Relay 5',
        'types': ['on_off'],
        'measurements': [4]
    },
    5: {
        'name': 'Relay 6',
        'types': ['on_off'],
        'measurements': [5]
    },
    6: {
        'name': 'Relay 7',
        'types': ['on_off'],
        'measurements': [6]
    },
    7: {
        'name': 'Relay 8',
        'types': ['on_off'],
        'measurements': [7]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'Grove_Multichannel_Relay',
    'output_name': "Grove Multichannel Relay (4- or 8-Channel board)",
    'output_manufacturer': 'Grove',
    'output_library': 'smbus2',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.seeedstudio.com/Grove-4-Channel-SPDT-Relay-p-3119.html',
    'url_datasheet': 'http://wiki.seeedstudio.com/Grove-4-Channel_SPDT_Relay/',
    'url_product_purchase': 'https://www.seeedstudio.com/Grove-4-Channel-SPDT-Relay-p-3119.html',

    'message': 'Controls the 4 or 8 channel Grove multichannel relay board.',

    'options_enabled': [
        'i2c_location',
        'button_on',
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2==0.4.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x11'
    ],
    'i2c_address_editable': True,
    'i2c_address_default': '0x11',

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
            'phrase': 'Set the state of the relay when Mycodo starts'
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
            'phrase': 'Set the state of the relay when Mycodo shuts down'
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
            'name': '{} ({})'.format(lazy_gettext('Current'), lazy_gettext('Amps')),
            'phrase': 'The current draw of the device being controlled'
        }
    ]
}


class OutputModule(AbstractOutput):
    """ An output support class that operates an output """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.sensor = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        import smbus2

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            self.logger.debug("I2C: Address: {}, Bus: {}".format(self.output.i2c_location, self.output.i2c_bus))
            if self.output.i2c_location:
                self.sensor = GroveMultiRelay(smbus2, self.output.i2c_bus, int(str(self.output.i2c_location), 16))
                self.output_setup = True
        except:
            self.logger.exception("Could not set up output")
            return

        dict_states = {}
        for channel in channels_dict:
            if self.options_channels['state_startup'][channel] == 1:
                dict_states[channel] = bool(self.options_channels['on_state'][channel])
            elif self.options_channels['state_startup'][channel] == 0:
                dict_states[channel] = bool(not self.options_channels['on_state'][channel])
            else:
                # Default state: Off
                dict_states[channel] = bool(not self.options_channels['on_state'][channel])

        self.logger.debug("List sent to device: {}".format(self.dict_to_list_states(dict_states)))
        try:
            self.sensor.port(self.dict_to_list_states(dict_states))
        except OSError as err:
            self.logger.error(
                "OSError: {}. Check that the device is connected properly, the correct "
                "address is selected, and you can communicate with the device.".format(err))
        self.output_states = dict_states

        for channel in channels_dict:
            if self.options_channels['trigger_functions_startup'][channel]:
                self.check_triggers(self.unique_id, output_channel=channel)

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
            msg = "Output not set up"
            self.logger.error(msg)
            return msg

        try:
            dict_states = {}
            for channel in channels_dict:
                if output_channel == channel:
                    if state == 'on':
                        dict_states[channel] = bool(self.options_channels['on_state'][channel])
                    elif state == 'off':
                        dict_states[channel] = bool(not self.options_channels['on_state'][channel])
                else:
                    dict_states[channel] = self.output_states[channel]

            self.logger.debug("List sent to device: {}".format(self.dict_to_list_states(dict_states)))
            self.sensor.port(self.dict_to_list_states(dict_states))
            self.output_states[output_channel] = dict_states[output_channel]
            msg = "success"
        except Exception as e:
            msg = "CH{} state change error: {}".format(output_channel, e)
            self.logger.error(msg)
        return msg

    def is_on(self, output_channel=None):
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel] == self.options_channels['on_state'][output_channel]

    def is_setup(self):
        return self.output_setup

    @staticmethod
    def dict_to_list_states(dict_states):
        list_states = []
        for i, _ in enumerate(dict_states):
            list_states.append(dict_states[i])
        return list_states

    def stop_output(self):
        """ Called when Output is stopped """
        dict_states = {}
        if self.is_setup():
            for channel in channels_dict:
                if self.options_channels['state_shutdown'][channel] == 1:
                    dict_states[channel] = bool(self.options_channels['on_state'][channel])
                elif self.options_channels['state_shutdown'][channel] == 0:
                    dict_states[channel] = bool(not self.options_channels['on_state'][channel])
            self.logger.debug("List sent to device: {}".format(self.dict_to_list_states(dict_states)))
            self.sensor.port(self.dict_to_list_states(dict_states))
        self.running = False


class GroveMultiRelay(object):
    """ A software representation of a single GroveMultiRelay IO expander chip """
    def __init__(self, smbus, i2c_bus, i2c_address):
        self.bus_no = i2c_bus
        self.bus = smbus.SMBus(i2c_bus)
        self.address = i2c_address

    def __repr__(self):
        return "GroveMultiRelay(i2c_bus_no=%r, address=0x%02x)" % (self.bus_no, self.address)

    def port(self, value):
        """ Set the whole port using a list """
        if not isinstance(value, list):
            raise AssertionError
        if len(value) != 8:
            raise AssertionError
        new_state = 0
        for i, val in enumerate(value):
            if val:
                new_state |= 1 << i
        self.bus.write_byte_data(self.address, 0x10, new_state)
