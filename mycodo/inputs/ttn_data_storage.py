# coding=utf-8
import datetime
import logging
import time

import requests
from flask_babel import lazy_gettext

from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import Input
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

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TTN_DATA_STORAGE',
    'input_manufacturer': 'The Things Network',
    'input_name': 'TTN Integration: Data Storage',
    'measurements_name': 'Variable measurements',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'custom_options',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo'],

    'custom_options': [
        {
            'id': 'application_id',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': lazy_gettext('Application ID'),
            'phrase': lazy_gettext('The Things Network Application ID')
        },
        {
            'id': 'app_api_key',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': lazy_gettext('App API Key'),
            'phrase': lazy_gettext('The Things Network Application API Key')
        },
        {
            'id': 'device_id',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': lazy_gettext('Device ID'),
            'phrase': lazy_gettext('The Things Network Device ID')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that retrieves stored data from The Things Network """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.ttn_data_storage")

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.ttn_data_storage_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.unique_id = input_dev.unique_id
            self.interface = input_dev.interface
            self.period = input_dev.period
            self.first_run = True
            self.latest_datetime = input_dev.datetime
            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == input_dev.unique_id)

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'application_id':
                        self.application_id = value
                    elif option == 'app_api_key':
                        self.app_api_key = value
                    elif option == 'device_id':
                        self.device_id = value

    def get_new_data(self, past_seconds):
        # Basic implementation. Future development may use more complex library to access API
        endpoint = "https://{app}.data.thethingsnetwork.org/api/v2/query/{dev}?last={time}".format(
            app=self.application_id, dev=self.device_id, time="{}s".format(int(past_seconds)))
        headers = {"Authorization": "key {k}".format(k=self.app_api_key)}
        timestamp_format = '%Y-%m-%dT%H:%M:%S.%f'

        response = requests.get(endpoint, headers=headers)
        try:
            responses = response.json()
        except ValueError:  # No data returned
            self.logger.debug("Response Error. Response: {}".format(
                response.content))
            return

        for each_resp in response.json():
            if not self.running:
                break

            ts_formatted_correctly = False
            try:
                datetime_utc = datetime.datetime.strptime(
                    each_resp['time'][:-7], timestamp_format)
                ts_formatted_correctly = True
            except:
                # Sometimes the original timestamp is in milliseconds
                # instead of nanoseconds. Therefore, remove 3 less digits
                # past the decimal and try again to parse.
                try:
                    datetime_utc = datetime.datetime.strptime(
                        each_resp['time'][:-4], timestamp_format)
                    ts_formatted_correctly = True
                except:
                    self.logger.error("Could not parse timestamp: {}".format(
                        each_resp['time']))

            if not ts_formatted_correctly:
                # Malformed timestamp encountered. Discard measurement.
                continue

            if (not self.latest_datetime or
                    self.latest_datetime < datetime_utc):
                self.latest_datetime = datetime_utc

            measurements = {}
            for each_meas in self.device_measurements.all():
                if (self.is_enabled(each_meas.channel) and
                        each_meas.name in each_resp and
                        each_resp[each_meas.name] is not None):

                    # Original value/unit
                    measurements[each_meas.channel] = {}
                    measurements[each_meas.channel]['measurement'] = each_meas.measurement
                    measurements[each_meas.channel]['unit'] = each_meas.unit
                    measurements[each_meas.channel]['value'] = each_resp[each_meas.name]
                    measurements[each_meas.channel]['timestamp'] = datetime_utc

                    # Convert value/unit is conversion_id present and valid
                    if each_meas.conversion_id:
                        conversion = db_retrieve_table_daemon(
                            Conversion, unique_id=each_meas.conversion_id)
                        if conversion:
                            meas = parse_measurement(
                                conversion,
                                each_meas,
                                measurements,
                                each_meas.channel,
                                measurements[each_meas.channel])

                            measurements[each_meas.channel]['measurement'] = meas[each_meas.channel]['measurement']
                            measurements[each_meas.channel]['unit'] = meas[each_meas.channel]['unit']
                            measurements[each_meas.channel]['value'] = meas[each_meas.channel]['value']
                            measurements[each_meas.channel]['timestamp'] = datetime_utc

            add_measurements_influxdb(self.unique_id, measurements)

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
                    "This appears to be the first data download. "
                    "Downloading and parsing past 7 days of data...".format(
                        seconds_download))
            else:
                self.logger.info(
                    "Downloading and parsing past {} seconds of data...".format(
                        int(seconds_download)))

            self.get_new_data(seconds_download)

            if seconds_download == seconds_seven_days:
                elapsed = time.time() - start
                self.logger.info(
                    "Download and parsing completed in {} seconds.".format(
                        int(elapsed)))
        else:
            self.get_new_data(self.period)

        return {}
