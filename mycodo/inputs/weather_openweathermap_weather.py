# coding=utf-8
import copy

import requests
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint

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
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    3: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    4: {
        'measurement': 'speed',
        'unit': 'm_s',
        'name': 'Wind'
    },
    5: {
        'measurement': 'direction',
        'unit': 'bearing',
        'name': 'Wind'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'OPENWEATHERMAP_CALL_WEATHER',
    'input_manufacturer': 'Weather',
    'input_name': 'OpenWeatherMap (City, Current)',
    'measurements_name': 'Humidity/Temperature/Pressure/Wind',
    'measurements_dict': measurements_dict,
    'url_additional': 'openweathermap.org',
    'measurements_rescale': False,

    'message': 'Obtain a free API key at openweathermap.org. '
               'If the city you enter does not return measurements, try another city. '
               'Note: the free API subscription is limited to 60 calls per minute',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [],
    'interfaces': ['MYCODO'],

    'custom_options': [
        {
            'id': 'api_key',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': lazy_gettext('API Key'),
            'phrase': "The API Key for this service's API"
        },
        {
            'id': 'city',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': lazy_gettext('City'),
            'phrase': "The city to acquire the weather data"
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that gets weather for a city"""
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.api_url = None
        self.api_key = None
        self.city = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        if self.api_key and self.city:
            self.api_url = "http://api.openweathermap.org/data/2.5/weather?appid={key}&units=metric&q={city}".format(
                key=self.api_key, city=self.city)
            self.logger.debug("URL: {}".format(self.api_url))

    def get_measurement(self):
        """ Gets the weather data """
        if not self.api_url:
            self.logger.error("API Key and City required")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            response = requests.get(self.api_url)
            x = response.json()
            self.logger.debug("Response: {}".format(x))

            if x["cod"] != "404":
                temperature = x["main"]["temp"]
                pressure = x["main"]["pressure"]
                humidity = x["main"]["humidity"]
                wind_speed = x["wind"]["speed"]
                wind_deg = x["wind"]["deg"]
            else:
                self.logger.error("City Not Found")
                return
        except Exception as e:
            self.logger.error("Error acquiring weather information: {}".format(e))
            return

        self.logger.debug("Temp: {}, Hum: {}, Press: {}, Wind Speed: {}, Wind Direction: {}".format(
            temperature, humidity, pressure, wind_speed, wind_deg))

        if self.is_enabled(0):
            self.value_set(0, temperature)
        if self.is_enabled(1):
            self.value_set(1, humidity)
        if self.is_enabled(2):
            self.value_set(2, pressure)

        if self.is_enabled(0) and self.is_enabled(1) and self.is_enabled(3):
            self.value_set(3, calculate_dewpoint(temperature, humidity))

        if self.is_enabled(4):
            self.value_set(4, wind_speed)
        if self.is_enabled(5):
            self.value_set(5, wind_deg)

        return self.return_dict
