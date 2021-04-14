import asyncio

from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    1: {
        'measurement': 'duration_time',
        'unit': 's'
    },
    2: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

channels_dict = {
    0: {
        'types': ['on_off'],
        'name': 'Outlet 1',
        'measurements': [0]
    },
    1: {
        'types': ['on_off'],
        'name': 'Outlet 2',
        'measurements': [1]
    },
    2: {
        'types': ['on_off'],
        'name': 'Outlet 3',
        'measurements': [2]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'kp303',
    'output_name': "KP303 Kasa Smart WiFi Power Strip",
    'output_manufacturer': 'TP-Link',
    'input_library': 'python-kasa',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],

    'url_manufacturer': 'https://www.tp-link.com/au/home-networking/smart-plug/kp303/',

    'message': 'This output controls the 3 outlets of the Kasa KP303 Smart WiFi Power Strip.',

    'options_enabled': [
        'button_on',
        'button_send_duration'
    ],

    'interfaces': ['MYCODO'],

    'dependencies_module': [
        ('pip-pypi', 'kasa', 'python-kasa==0.4.0.dev2')
    ],

    'custom_options': [
        {
            'id': 'plug_address',
            'type': 'text',
            'default_value': '192.168.0.50',
            'required': True,
            'name': TRANSLATIONS['host']['title'],
            'phrase': TRANSLATIONS['host']['phrase']
        }
    ],


    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': 'Outlet Name',
            'required': True,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': lazy_gettext('Set the state when Mycodo starts')
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                (1, 'On')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': lazy_gettext('Set the state when Mycodo shuts down')
        },
        {
            'id': 'trigger_functions_startup',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Trigger Functions at Startup'),
            'phrase': lazy_gettext('Whether to trigger functions when the output switches at startup')
        },
        {
            'id': 'command_force',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Force Command'),
            'phrase': lazy_gettext('Always send the command if instructed, regardless of the current state')
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Current (Amps)'),
            'phrase': lazy_gettext('The current draw of the device being controlled')
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.plug_address = None
        self.strip = None
        self.output_setup = False

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        from kasa import SmartStrip

        self.setup_output_variables(OUTPUT_INFORMATION)

        if not self.plug_address:
            self.logger.error("Plug address must be set")
        else:
            try:
                self.strip = SmartStrip(self.plug_address)
                asyncio.run(self.strip.update())
                self.output_setup = True
                self.logger.info('Strip setup with children {0}'.format(self.strip.children))
            except Exception as e:
                self.logger.exception("Output was unable to be setup {err}".format(err=e))

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            self.logger.error('Output not set up')
            return

        try:
            if state == 'on':
                asyncio.run(self.strip.children[output_channel].turn_on())
                self.output_states[output_channel] = True
            elif state == 'off':
                asyncio.run(self.strip.children[output_channel].turn_off())
                self.output_states[output_channel] = False
            msg = 'success'
        except Exception as e:
            msg = "State change error: {}".format(e)
            self.logger.exception(msg)
        return msg

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
        for channel in channels_dict:
            if self.options_channels['state_shutdown'][channel] == 1:
                self.output_switch('on', output_channel=channel)
            elif self.options_channels['state_shutdown'][channel] == 0:
                self.output_switch('off', output_channel=channel)
        self.running = False
