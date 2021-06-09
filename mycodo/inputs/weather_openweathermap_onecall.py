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
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Min'
    },
    2: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Max'
    },
    3: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    4: {
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    5: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    6: {
        'measurement': 'speed',
        'unit': 'm_s',
        'name': 'Wind'
    },
    7: {
        'measurement': 'direction',
        'unit': 'bearing',
        'name': 'Wind'
    },
    8: {
        'measurement': 'duration_time',
        'unit': 'h',
        'name': 'Hours in Future'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'OPENWEATHERMAP_CALL_ONECALL',
    'input_manufacturer': 'Weather',
    'input_name': 'OpenWeatherMap (Lat/Lon, Current/Future)',
    'measurements_name': 'Humidity/Temperature/Pressure/Wind',
    'measurements_dict': measurements_dict,
    'url_additional': 'openweathermap.org',
    'measurements_rescale': False,

    'message': 'Obtain a free API key at openweathermap.org. '
               'Notes: The free API subscription is limited to 60 calls per minute. '
               'If a Day (Future) time is selected, Minimum and Maximum temperatures are available as measurements.',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [],
    'interfaces': ['Mycodo'],

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
            'id': 'latitude',
            'type': 'float',
            'default_value': 33.441792,
            'required': True,
            'name': lazy_gettext('Latitude (decimal)'),
            'phrase': "The latitude to acquire weather data"
        },
        {
            'id': 'longitude',
            'type': 'float',
            'default_value': -94.037689,
            'required': True,
            'name': lazy_gettext('Longitude (decimal)'),
            'phrase': "The longitude to acquire weather data"
        },
        {
            'id': 'weather_time',
            'type': 'select',
            'default_value': 'current',
            'options_select': [
                ('current', 'Current (Present)'),
                ('day1', '1 Day (Future)'),
                ('day2', '2 Day (Future)'),
                ('day3', '3 Day (Future)'),
                ('day4', '4 Day (Future)'),
                ('day5', '5 Day (Future)'),
                ('day6', '6 Day (Future)'),
                ('day7', '7 Day (Future)'),
                ('hour1', '1 Hour (Future)'),
                ('hour2', '2 Hours (Future)'),
                ('hour3', '3 Hours (Future)'),
                ('hour4', '4 Hours (Future)'),
                ('hour5', '5 Hours (Future)'),
                ('hour6', '6 Hours (Future)'),
                ('hour7', '7 Hours (Future)'),
                ('hour8', '8 Hours (Future)'),
                ('hour9', '9 Hours (Future)'),
                ('hour10', '10 Hours (Future)'),
                ('hour11', '11 Hours (Future)'),
                ('hour12', '12 Hours (Future)'),
                ('hour13', '13 Hours (Future)'),
                ('hour14', '14 Hours (Future)'),
                ('hour15', '15 Hours (Future)'),
                ('hour16', '16 Hours (Future)'),
                ('hour17', '17 Hours (Future)'),
                ('hour18', '18 Hours (Future)'),
                ('hour19', '19 Hours (Future)'),
                ('hour20', '20 Hours (Future)'),
                ('hour21', '21 Hours (Future)'),
                ('hour22', '22 Hours (Future)'),
                ('hour23', '23 Hours (Future)'),
                ('hour24', '24 Hours (Future)'),
                ('hour25', '25 Hours (Future)'),
                ('hour26', '26 Hours (Future)'),
                ('hour27', '27 Hours (Future)'),
                ('hour28', '28 Hours (Future)'),
                ('hour29', '29 Hours (Future)'),
                ('hour30', '30 Hours (Future)'),
                ('hour31', '31 Hours (Future)'),
                ('hour32', '32 Hours (Future)'),
                ('hour33', '33 Hours (Future)'),
                ('hour34', '34 Hours (Future)'),
                ('hour35', '35 Hours (Future)'),
                ('hour36', '36 Hours (Future)'),
                ('hour37', '37 Hours (Future)'),
                ('hour38', '38 Hours (Future)'),
                ('hour39', '39 Hours (Future)'),
                ('hour40', '40 Hours (Future)'),
                ('hour41', '41 Hours (Future)'),
                ('hour42', '42 Hours (Future)'),
                ('hour43', '43 Hours (Future)'),
                ('hour44', '44 Hours (Future)'),
                ('hour45', '45 Hours (Future)'),
                ('hour46', '46 Hours (Future)'),
                ('hour47', '47 Hours (Future)'),
                ('hour48', '48 Hours (Future)')
            ],
            'name': lazy_gettext('Time'),
            'phrase': 'Select the time for the current or forecast weather'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that gets weather for a latitude/longitude location"""
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.api_url = None
        self.api_key = None
        self.latitude = None
        self.longitude = None
        self.weather_time = None
        self.weather_time_dict = {}

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        if self.api_key and self.latitude and self.longitude and self.weather_time:
            base_url = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units=metric&appid={key}".format(
                lat=self.latitude, lon=self.longitude, key=self.api_key)
            if self.weather_time == 'current':
                self.weather_time_dict["time"] = "current"
                self.api_url = "{base}&exclude=minutely,hourly,daily,alerts".format(base=base_url)
            elif self.weather_time.startswith("day"):
                self.weather_time_dict["time"] = "day"
                self.weather_time_dict["amount"] = int(self.weather_time.split("day")[1])
                self.api_url = "{base}&exclude=current,minutely,hourly,alerts".format(base=base_url)
            elif self.weather_time.startswith("hour"):
                self.weather_time_dict["time"] = "hour"
                self.weather_time_dict["amount"] = int(self.weather_time.split("hour")[1])
                self.api_url = "{base}&exclude=current,minutely,daily,alerts".format(base=base_url)

            self.logger.debug("URL: {}".format(self.api_url))
            self.logger.debug("Time Dict: {}".format(self.weather_time_dict))

    def get_measurement(self):
        """ Gets the weather data """
        if not self.api_url:
            self.logger.error("API Key, Latitude, and Longitude required")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            response = requests.get(self.api_url)
            x = response.json()
            self.logger.debug("Response: {}".format(x))

            if self.weather_time_dict["time"] == "current":
                if 'current' not in x:
                    self.logger.error("No response. Check your configuration.")
                    return
                temperature = x["current"]["temp"]
                pressure = x["current"]["pressure"]
                humidity = x["current"]["humidity"]
                wind_speed = x["current"]["wind_speed"]
                wind_deg = x["current"]["wind_deg"]
                if self.is_enabled(8):
                    self.value_set(8, 0)
            elif self.weather_time_dict["time"] == "hour":
                if 'hourly' not in x:
                    self.logger.error("No response. Check your configuration.")
                    return
                temperature = x["hourly"][self.weather_time_dict["amount"] - 1]["temp"]
                pressure = x["hourly"][self.weather_time_dict["amount"] - 1]["pressure"]
                humidity = x["hourly"][self.weather_time_dict["amount"] - 1]["humidity"]
                wind_speed = x["hourly"][self.weather_time_dict["amount"] - 1]["wind_speed"]
                wind_deg = x["hourly"][self.weather_time_dict["amount"] - 1]["wind_deg"]
                if self.is_enabled(8):
                    self.value_set(8, self.weather_time_dict["amount"])
            elif self.weather_time_dict["time"] == "day":
                if 'daily' not in x:
                    self.logger.error("No response. Check your configuration.")
                    return
                temperature = x["daily"][self.weather_time_dict["amount"]]["temp"]["day"]
                temperature_min = x["daily"][self.weather_time_dict["amount"]]["temp"]["min"]
                temperature_max = x["daily"][self.weather_time_dict["amount"]]["temp"]["max"]
                pressure = x["daily"][self.weather_time_dict["amount"]]["pressure"]
                humidity = x["daily"][self.weather_time_dict["amount"]]["humidity"]
                wind_speed = x["daily"][self.weather_time_dict["amount"]]["wind_speed"]
                wind_deg = x["daily"][self.weather_time_dict["amount"]]["wind_deg"]

                if self.is_enabled(1):
                    self.value_set(1, temperature_min)
                if self.is_enabled(2):
                    self.value_set(2, temperature_max)
                if self.is_enabled(8):
                    self.value_set(8, self.weather_time_dict["amount"] * 24)
            else:
                self.logger.error("Invalid weather time")
                return
        except Exception as e:
            self.logger.error("Error acquiring weather information: {}".format(e))
            return

        self.logger.debug("Temp: {}, Hum: {}, Press: {}, Wind Speed: {}, Wind Direction: {}".format(
            temperature, humidity, pressure, wind_speed, wind_deg))

        if self.is_enabled(0):
            self.value_set(0, temperature)
        if self.is_enabled(3):
            self.value_set(3, humidity)
        if self.is_enabled(4):
            self.value_set(4, pressure)

        if self.is_enabled(0) and self.is_enabled(3) and self.is_enabled(5):
            self.value_set(5, calculate_dewpoint(temperature, humidity))

        if self.is_enabled(6):
            self.value_set(6, wind_speed)
        if self.is_enabled(7):
            self.value_set(7, wind_deg)

        return self.return_dict
