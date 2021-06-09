# coding=utf-8
import datetime
import time

import requests

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Conversion
from mycodo.databases.models import Input
from mycodo.databases.models import InputChannel
from mycodo.databases.utils import session_scope
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import parse_measurement

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


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
    if value > 100:
        all_passed = False
        errors.append("Number of measurements cannot exceed 100")
    return all_passed, errors, mod_input

# Measurements
measurements_dict = {}

# Channels
channels_dict = {
    0: {}
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TTN_DATA_STORAGE',
    'input_manufacturer': 'Mycodo',
    'input_name': 'TTN Integration: Data Storage',
    'input_library': 'requests',
    'measurements_name': 'Variable measurements',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,

    'message': 'This Input receives and stores measurements from the Data Storage Integration on The Things Network.',

    'measurements_variable_amount': True,
    'channel_quantity_same_as_measurements': True,
    'measurements_use_same_timestamp': False,

    'options_enabled': [
        'measurements_select',
        'period',
        'start_offset',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'requests', 'requests==2.25.1'),
    ],

    'interfaces': ['MYCODO'],

    'custom_options': [
        {
            'id': 'application_id',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': 'Application ID',
            'phrase': 'The Things Network Application ID'
        },
        {
            'id': 'app_api_key',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': 'App API Key',
            'phrase': 'The Things Network Application API Key'
        },
        {
            'id': 'device_id',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': 'Device ID',
            'phrase': 'The Things Network Device ID'
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
            'id': 'variable_name',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': 'Variable Name',
            'phrase': 'The TTN variable name'
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that retrieves stored data from The Things Network """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.first_run = True

        self.application_id = None
        self.app_api_key = None
        self.device_id = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        self.interface = self.input_dev.interface
        self.period = self.input_dev.period
        self.latest_datetime = self.input_dev.datetime

        input_channels = db_retrieve_table_daemon(
            InputChannel).filter(InputChannel.input_id == self.input_dev.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            INPUT_INFORMATION['custom_channel_options'], input_channels)

    def get_new_data(self, past_seconds):
        # Basic implementation. Future development may use more complex library to access API
        endpoint = "https://{app}.data.thethingsnetwork.org/api/v2/query/{dev}?last={time}".format(
            app=self.application_id, dev=self.device_id, time="{}s".format(int(past_seconds)))
        headers = {"Authorization": "key {k}".format(k=self.app_api_key)}
        timestamp_format = '%Y-%m-%dT%H:%M:%S.%f'

        response = requests.get(endpoint, headers=headers)
        try:
            response.json()
        except ValueError:  # No data returned
            self.logger.debug("Response Error. Response: {}. Likely there is no data to be retrieved on TTN".format(
                response.content))
            return

        for each_resp in response.json():
            if not self.running:
                break

            try:
                datetime_utc = datetime.datetime.strptime(each_resp['time'][:-7], timestamp_format)
            except Exception:
                # Sometimes the original timestamp is in milliseconds
                # instead of nanoseconds. Therefore, remove 3 less digits
                # past the decimal and try again to parse.
                try:
                    datetime_utc = datetime.datetime.strptime(each_resp['time'][:-4], timestamp_format)
                except Exception as e:
                    self.logger.error("Could not parse timestamp '{}': {}".format(each_resp['time'], e))
                    continue  # Malformed timestamp encountered. Discard measurement.

            if (not self.latest_datetime or
                    self.latest_datetime < datetime_utc):
                self.latest_datetime = datetime_utc

            measurements = {}
            for channel in self.channels_measurement:
                if (self.is_enabled(channel) and
                        self.options_channels['variable_name'][channel] in each_resp and
                        each_resp[self.options_channels['variable_name'][channel]] is not None):

                    # Original value/unit
                    measurements[channel] = {}
                    measurements[channel]['measurement'] = self.channels_measurement[channel].measurement
                    measurements[channel]['unit'] = self.channels_measurement[channel].unit
                    measurements[channel]['value'] = each_resp[self.options_channels['variable_name'][channel]]
                    measurements[channel]['timestamp_utc'] = datetime_utc

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
                                measurements[channel],
                                timestamp=datetime_utc)

                            measurements[channel]['measurement'] = meas[channel]['measurement']
                            measurements[channel]['unit'] = meas[channel]['unit']
                            measurements[channel]['value'] = meas[channel]['value']

            if measurements:
                self.logger.debug("Adding measurements to influxdb: {}".format(measurements))
                add_measurements_influxdb(
                    self.unique_id, measurements,
                    use_same_timestamp=INPUT_INFORMATION['measurements_use_same_timestamp'])
            else:
                self.logger.debug("No measurements to add to influxdb.")

        # set datetime to latest timestamp
        if self.running:
            with session_scope(MYCODO_DB_PATH) as new_session:
                mod_input = new_session.query(Input).filter(
                    Input.unique_id == self.unique_id).first()
                if not mod_input.datetime or mod_input.datetime < self.latest_datetime:
                    mod_input.datetime = self.latest_datetime
                    new_session.commit()

    def get_measurement(self):
        """ Gets the data """
        if self.first_run:
            # Get data for up to 7 days (longest Data Storage Integration
            # stores data) in the past or until last_datetime.
            seconds_seven_days = 604800  # 604800 seconds = 7 days
            seconds_download = seconds_seven_days
            start = time.time()
            self.first_run = False

            if self.latest_datetime:
                utc_now = datetime.datetime.utcnow()
                seconds_since_last = (utc_now - self.latest_datetime).total_seconds()
                if seconds_since_last < seconds_seven_days:
                    seconds_download = seconds_since_last

            if seconds_download == seconds_seven_days:
                self.logger.info(
                    "This appears to be the first data download. Downloading and parsing past 7 days of data...")
            else:
                self.logger.info("Downloading and parsing past {} seconds of data...".format(int(seconds_download)))

            self.get_new_data(seconds_download)

            if seconds_download == seconds_seven_days:
                elapsed = time.time() - start
                self.logger.info("Download and parsing completed in {} seconds.".format(int(elapsed)))
        else:
            self.get_new_data(self.period)

        return {}
