# coding=utf-8
import datetime
import logging

import requests
from flask_babel import lazy_gettext

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import parse_measurement
from mycodo.utils.influx import write_influxdb_value

# Measurements
measurements_dict = {
    0: {
        'measurement': 'humidity',
        'unit': '%'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TTN_DATA_STORAGE',
    'input_manufacturer': 'The Things Network',
    'input_name': 'TTN Integration: Data Storage',
    'measurements_name': 'Temperature/Humidity',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'custom_options',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [],

    'interfaces': ['RPi'],

    'custom_options': [
        {
            'id': 'application_id',
            'type': 'text',
            'default_value': '',
            'name': lazy_gettext('Application ID'),
            'phrase': lazy_gettext('The Things Network Application ID')
        },
        {
            'id': 'app_api_key',
            'type': 'text',
            'default_value': '',
            'name': lazy_gettext('App API Key'),
            'phrase': lazy_gettext('The Things Network Application API Key')
        },
        {
            'id': 'device_id',
            'type': 'text',
            'default_value': '',
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

        self.unique_id = input_dev.unique_id
        self.interface = input_dev.interface
        self.period = input_dev.period

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.ttn_data_storage_{id}".format(id=input_dev.unique_id.split('-')[0]))

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
        endpoint = "https://{app}.data.thethingsnetwork.org/api/v2/query/{dev}?last={time}".format(
            app=self.application_id, dev=self.device_id, time="{}s".format(past_seconds))
        headers = {"Authorization": "key {k}".format(k=self.app_api_key)}
        response = requests.get(endpoint, headers=headers)

        try:
            for each_resp in response.json():

                # Store humidity
                measurement = self.device_measurements.filter(
                    DeviceMeasurements.channel == 0).first()
                conversion = db_retrieve_table_daemon(
                    Conversion, unique_id=measurement.conversion_id)
                datetime_ts = datetime.datetime.strptime(each_resp['time'][:-7],'%Y-%m-%dT%H:%M:%S.%f')
                measurement_single = {
                    0: {
                        'measurement': 'humidity',
                        'unit': '%',
                        'value': each_resp['humidity']
                    }
                }
                measurement_single = parse_measurement(
                    conversion,
                    measurement,
                    measurement_single,
                    measurement.channel,
                    measurement_single[0])
                write_influxdb_value(
                    self.unique_id,
                    measurement_single[0]['unit'],
                    value=measurement_single[0]['value'],
                    measure=measurement_single[0]['measurement'],
                    channel=0,
                    timestamp=datetime_ts)

                # Store temperature
                measurement = self.device_measurements.filter(
                    DeviceMeasurements.channel == 0).first()
                conversion = db_retrieve_table_daemon(
                    Conversion, unique_id=measurement.conversion_id)
                datetime_ts = datetime.datetime.strptime(each_resp['time'][:-7], '%Y-%m-%dT%H:%M:%S.%f')
                measurement_single = {
                    0: {
                        'measurement': 'temperature',
                        'unit': 'C',
                        'value': each_resp['temperature']
                    }
                }
                measurement_single = parse_measurement(
                    conversion,
                    measurement,
                    measurement_single,
                    measurement.channel,
                    measurement_single[0])
                write_influxdb_value(
                    self.unique_id,
                    measurement_single[0]['unit'],
                    value=measurement_single[0]['value'],
                    measure=measurement_single[0]['measurement'],
                    channel=0,
                    timestamp=datetime_ts)
        except:
            self.logger.exception("Error acquiring and/or storing measurements")

    def get_measurement(self):
        """ Gets the data """
        self.get_new_data(int(self.period))
