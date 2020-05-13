# coding=utf-8
# Input module for Sonoff TH16 or TH10.
# Requires Tasmota firmware flashed to the Sonoff's ESP8266
# https://github.com/arendst/Sonoff-Tasmota
import datetime
import json

import requests
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit

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
        'period',
        'pre_output'
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

        # Initialize custom options
        self.ip_address = None
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)
        self.ip_address = self.ip_address.replace(" ", "")  # Remove spaces

    def get_measurement(self):
        self.return_dict = measurements_dict.copy()

        url = "http://{ip}/cm?cmnd=status%2010".format(ip=self.ip_address)
        r = requests.get(url)
        str_json = r.text
        dict_data = json.loads(str_json)

        self.logger.debug("Returned Data: {}".format(dict_data))

        # Convert string to datetime object
        datetime_timestmp = datetime.datetime.strptime(
            dict_data['StatusSNS']['Time'], '%Y-%m-%dT%H:%M:%S')

        # Convert temperature to SI unit Celsius
        if self.is_enabled(0):
            if ('TempUnit' in dict_data['StatusSNS'] and
                    dict_data['StatusSNS']['TempUnit']):
                temp_c = convert_from_x_to_y_unit(
                    dict_data['StatusSNS']['TempUnit'],
                    'C',
                    dict_data['StatusSNS']['AM2301']['Temperature'])
            else:
                temp_c = dict_data['StatusSNS']['AM2301']['Temperature']
            self.value_set(0, temp_c, timestamp=datetime_timestmp)

        if self.is_enabled(1):
            humidity = dict_data['StatusSNS']['AM2301']['Humidity']
            self.value_set(1, humidity, timestamp=datetime_timestmp)

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            dewpoint = calculate_dewpoint(
                self.value_get(0), self.value_get(1))
            self.value_set(2, dewpoint, timestamp=datetime_timestmp)

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            vpd = calculate_vapor_pressure_deficit(
                self.value_get(0), self.value_get(1))
            self.value_set(3, vpd, timestamp=datetime_timestmp)

        return self.return_dict
