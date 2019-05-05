# coding=utf-8
# Input module for Sonoff TH16 or TH10.
# Requires Tasmota firmware flashed to the Sonoff's ESP8266
# https://github.com/arendst/Sonoff-Tasmota
import datetime
import json
import logging

import requests
from flask_babel import lazy_gettext

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    3: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TH16_10',
    'input_manufacturer': 'Sonoff',
    'input_name': 'TH16/10 (Tasmota firmware) with AM2301',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': False,

    'options_enabled': [
        'measurements_select',
        'custom_options',
        'period',
        'pre_output',
        'log_level_debug'
    ],

    'custom_options': [
        {
            'id': 'ip_address',
            'type': 'text',
            'default_value': '192.168.0.100',
            'required': True,
            'name': lazy_gettext('IP Address'),
            'phrase': lazy_gettext('The IP address of the device')
        }
    ]
}


class InputModule(AbstractInput):
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.th16_am2301")
        self.ip_address = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.th16_am2301_{id}".format(
                    id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == input_dev.unique_id)

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'ip_address':
                        self.ip_address = value.replace(" ", "")  # Remove spaces

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        return_dict = measurements_dict.copy()

        url = "http://{ip}/cm?cmnd=status%2010".format(ip=self.ip_address)
        r = requests.get(url)
        str_json = r.text

        dict_data = json.loads(str_json)

        # Convert string to datetime object
        datetime_timestmp = datetime.datetime.strptime(
            dict_data['StatusSNS']['Time'], '%Y-%m-%dT%H:%M:%S')

        # Convert temperature to SI unit Celsius
        if self.is_enabled(0):
            temp_c = convert_from_x_to_y_unit(
                'F', 'C', dict_data['StatusSNS']['AM2301']['Temperature'])
            self.set_value(return_dict, 0, temp_c, timestamp=datetime_timestmp)

        if self.is_enabled(1):
            humidity = dict_data['StatusSNS']['AM2301']['Humidity']
            self.set_value(return_dict, 1, humidity, timestamp=datetime_timestmp)

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            dewpoint = calculate_dewpoint(
                self.get_value(0), self.get_value(1))
            self.set_value(return_dict, 2, dewpoint, timestamp=datetime_timestmp)

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            vpd = calculate_vapor_pressure_deficit(
                self.get_value(0), self.get_value(1))
            self.set_value(return_dict, 3, vpd, timestamp=datetime_timestmp)

        return return_dict
