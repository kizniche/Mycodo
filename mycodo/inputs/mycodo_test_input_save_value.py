# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Conversion
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.inputs import parse_measurement

# Measurements
measurements_dict = {}

# Channels
channels_dict = {
    0: {}
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TEST_SAVE_VALUE',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Test Input: Save your own measurement value',
    'input_name_short': 'Test: Save Value',
    'measurements_name': 'Variable measurements',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,

    'message': 'This is a simple test Input that allows you to save any value as a measurement, that will be '
               'stored in the measurement database. It can be useful for testing other parts of Mycodo, such '
               'as PIDs, Bang-Bang, and Conditional Functions, since you can be completely in '
               'control of what values the input provides to the Functions. '
               'Note 1: Select and save the Name and Measurement Unit for each channel. Once the unit has been saved, '
               'you can convert to other units in the Convert Measurement section. '
               'Note 2: Activate the Input before storing measurements.',

    'measurements_variable_amount': True,
    'channel_quantity_same_as_measurements': True,
    'do_not_run_periodically': True,

    'options_enabled': [
        'measurements_select'
    ],

    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        }
    ],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': "Enter the Value you want to store as a measurement, then press Store Measurement."
        },
        {
            'id': 'channel_measurement',
            'type': 'integer',
            'default_value': 0,
            'name': lazy_gettext('Channel'),
            'phrase': 'This is the channel to save the measurement value to'
        },
        {
            'id': 'value_measurement',
            'type': 'float',
            'default_value': 10.0,
            'name': lazy_gettext('Value'),
            'phrase': 'This is the measurement value to save for this Input'
        },
        {
            'id': 'save_measurement',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Store Measurement')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that retrieves stored data from The Things Network."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

    def initialize(self):
        pass

    def get_measurement(self):
        """Gets the data."""
        pass

    def save_measurement(self, args_dict):
        if 'channel_measurement' not in args_dict:
            self.logger.error("Cannot save measurement without a Channel")
            return
        if 'value_measurement' not in args_dict:
            self.logger.error("Cannot save measurement without a Value")
            return

        channel = args_dict['channel_measurement']
        value = args_dict['value_measurement']

        measurements = {
            channel: {
                'measurement': self.channels_measurement[channel].measurement,
                'unit': self.channels_measurement[channel].unit,
                'value': value
            }
        }

        # Convert value/unit is conversion_id present and valid
        if self.channels_conversion[channel]:
            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=self.channels_measurement[channel].conversion_id)
            if conversion:
                meas = parse_measurement(
                    self.channels_conversion[channel],
                    self.channels_measurement[channel],
                    measurements,
                    channel,
                    measurements[channel])

                measurements[channel]['measurement'] = meas[channel]['measurement']
                measurements[channel]['unit'] = meas[channel]['unit']
                measurements[channel]['value'] = meas[channel]['value']

        if measurements:
            self.logger.debug("Adding measurements to influxdb: {}".format(measurements))
            add_measurements_influxdb(self.unique_id, measurements)
        else:
            self.logger.debug("No measurements to add to influxdb.")