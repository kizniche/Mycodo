# coding=utf-8
import copy
from mycodo.config_translations import TRANSLATIONS
from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'electrical_potential',
        'unit': 'V',
        'name': ''
    },
    1: {
        'measurement': 'electrical_current',
        'unit': 'A',
        'name': ''
    },
    2: {
        'measurement': 'power',
        'unit': 'W',
        'name': ''
    },
    3: {
        'measurement': 'power_apparent',
        'unit': 'va',
        'name': ''
    },
    4: {
        'measurement': 'power_reactive',
        'unit': 'var',
        'name': ''
    },
    5: {
        'measurement': 'power_factor',
        'unit': 'unitless',
        'name': ''
    },
    6: {
        'measurement': 'energy',
        'unit': 'kWh',
        'name': ''
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'tasmota_outlet_energy_monitor',
    'input_manufacturer': 'Tasmota',
    'input_name': 'Tasmota Outlet Energy Monitor (HTTP)',
    'input_name_short': 'Tasmota Energy Monitor',
    'input_library': 'requests',
    'measurements_name': 'Total Energy, Amps, Watts',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://tasmota.github.io',
    'url_product_purchase': 'https://templates.blakadder.com/plug.html',

    'message': 'This input queries the energy usage information from a WiFi outlet that is running the tasmota firmware. There are many WiFi outlets that support tasmota, and many of of those have energy monitoring capabilities. When used with an MQTT Output, you can both control your tasmota outlets as well as mionitor their energy usage.',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['HTTP'],

    'custom_options': [
        {
            'id': 'host',
            'type': 'text',
            'default_value': '192.168.0.50',
            'required': True,
            'name': TRANSLATIONS["host"]["title"],
            'phrase': TRANSLATIONS["host"]["phrase"]
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the TMP006's die and object temperatures."""
    def __init__(self, input_dev,  testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.requests = None
        self.url = None

        self.host = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import requests

        self.requests = requests

        self.url = 'http://{}/cm?cmnd=status%2010'.format(self.host)

    def get_measurement(self):
        """Get energy usage of tasmota outlet."""
        if not self.requests:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        ret_dict = self.requests.get(self.url).json()

        self.logger.debug("Request: {}".format(self.url))
        self.logger.debug("Request returned: {}".format(ret_dict))

        if "StatusSNS" in ret_dict and "ENERGY" in ret_dict["StatusSNS"]:
            if self.is_enabled(0) and "Voltage" in ret_dict["StatusSNS"]["ENERGY"]:
                self.value_set(0, ret_dict["StatusSNS"]["ENERGY"]["Voltage"])
            if self.is_enabled(1) and "Current" in ret_dict["StatusSNS"]["ENERGY"]:
                self.value_set(1, ret_dict["StatusSNS"]["ENERGY"]["Current"])
            if self.is_enabled(2) and "Power" in ret_dict["StatusSNS"]["ENERGY"]:
                self.value_set(2, ret_dict["StatusSNS"]["ENERGY"]["Power"])
            if self.is_enabled(3) and "ApparentPower" in ret_dict["StatusSNS"]["ENERGY"]:
                self.value_set(3, ret_dict["StatusSNS"]["ENERGY"]["ApparentPower"])
            if self.is_enabled(4) and "ReactivePower" in ret_dict["StatusSNS"]["ENERGY"]:
                self.value_set(4, ret_dict["StatusSNS"]["ENERGY"]["ReactivePower"])
            if self.is_enabled(5) and "Factor" in ret_dict["StatusSNS"]["ENERGY"]:
                self.value_set(5, ret_dict["StatusSNS"]["ENERGY"]["Factor"])
            if self.is_enabled(6) and "Total" in ret_dict["StatusSNS"]["ENERGY"]:
                self.value_set(6, ret_dict["StatusSNS"]["ENERGY"]["Total"])

        return self.return_dict
