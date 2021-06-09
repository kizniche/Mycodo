# coding=utf-8
# Input module for Sonoff TH16 or TH10.
# Requires Tasmota firmware flashed to the Sonoff's ESP8266
# https://github.com/arendst/Sonoff-Tasmota
import datetime
import json

import copy
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
    'input_library': 'requests',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://sonoff.tech/product/wifi-diy-smart-switches/th10-th16',

    'measurements_use_same_timestamp': False,

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'requests', 'requests==2.25.1')
    ],

    'custom_options': [
        {
            'id': 'ip_address',
            'type': 'text',
            'default_value': '192.168.0.100',
            'required': True,
            'name': lazy_gettext('IP Address'),
            'phrase': 'The IP address of the device'
        }
    ]
}


class InputModule(AbstractInput):
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.ip_address = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.ip_address = self.ip_address.replace(" ", "")  # Remove spaces

    def get_measurement(self):
        self.return_dict = copy.deepcopy(measurements_dict)

        url = "http://{ip}/cm?cmnd=status%2010".format(ip=self.ip_address)
        r = requests.get(url)
        str_json = r.text
        dict_data = json.loads(str_json)

        self.logger.debug("Returned Data: {}".format(dict_data))

        # Convert string to datetime object
        datetime_timestmp = datetime.datetime.strptime(dict_data['StatusSNS']['Time'], '%Y-%m-%dT%H:%M:%S')

        if 'TempUnit' in dict_data['StatusSNS'] and dict_data['StatusSNS']['TempUnit']:
            # Convert temperature to SI unit Celsius
            temp_c = convert_from_x_to_y_unit(
                dict_data['StatusSNS']['TempUnit'],
                'C',
                dict_data['StatusSNS']['AM2301']['Temperature'])
        else:
            temp_c = dict_data['StatusSNS']['AM2301']['Temperature']
        self.value_set(0, temp_c, timestamp=datetime_timestmp)

        self.value_set(1, dict_data['StatusSNS']['AM2301']['Humidity'], timestamp=datetime_timestmp)

        if self.is_enabled(2) and self.is_enabled(0) and self.is_enabled(1):
            dewpoint = calculate_dewpoint(self.value_get(0), self.value_get(1))
            self.value_set(2, dewpoint, timestamp=datetime_timestmp)

        if self.is_enabled(3) and self.is_enabled(0) and self.is_enabled(1):
            vpd = calculate_vapor_pressure_deficit(self.value_get(0), self.value_get(1))
            self.value_set(3, vpd, timestamp=datetime_timestmp)

        return self.return_dict
