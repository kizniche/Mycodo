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
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TH16_10_DS18B20',
    'input_manufacturer': 'Sonoff',
    'input_name': 'TH16/10 (Tasmota firmware) with DS18B20',
    'measurements_name': 'Temperature',
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.ip_address = None

        if not testing:
            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'ip_address':
                        self.ip_address = value.replace(" ", "")  # Remove spaces

    def get_measurement(self):
        self.return_dict = measurements_dict.copy()

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
                dict_data['StatusSNS']['TempUnit'],
                'C',
                dict_data['StatusSNS']['DS18B20']['Temperature'])
            self.set_value(0, temp_c, timestamp=datetime_timestmp)

        return self.return_dict
