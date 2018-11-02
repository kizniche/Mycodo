# coding=utf-8
import logging

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements = {
    'battery': {
        'percent': {0: {}}
    },
    'electrical_conductivity': {
        'μS_cm': {0: {}}
    },
    'light': {
        'lux': {0: {}}
    },
    'moisture': {
        'unitless': {0: {}}
    },
    'temperature': {
        'C': {0: {}}
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MIFLORA',
    'input_manufacturer': 'Xiaomi',
    'input_name': 'Miflora',
    'measurements_name': 'EC/Light/Moisture/Temperature',
    'measurements_dict': measurements,

    'options_enabled': [
        'bt_location',
        'measurements_select',
        'measurements_convert',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libglib2.0-dev', 'libglib2.0-dev'),
        ('pip-pypi', 'miflora', 'miflora'),
        ('pip-pypi', 'btlewrap', 'btlewrap'),
        ('pip-pypi', 'bluepy', 'bluepy==1.2.0'),
    ],

    'interfaces': ['BT'],
    'bt_location': '00:00:00:00:00:00',
    'bt_adapter': 'hci0'
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the Miflora's electrical
    conductivity, moisture, temperature, and light.

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.miflora")
        self._measurements = None

        if not testing:
            from miflora.miflora_poller import MiFloraPoller
            from btlewrap import BluepyBackend
            self.logger = logging.getLogger(
                "mycodo.miflora_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.input_measurements = db_retrieve_table_daemon(
                InputMeasurements).filter(
                    InputMeasurements.input_id == input_dev.unique_id).all()

            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter
            self.poller = MiFloraPoller(self.location, BluepyBackend, adapter=self.bt_adapter)

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        from miflora.miflora_poller import MI_CONDUCTIVITY
        from miflora.miflora_poller import MI_MOISTURE
        from miflora.miflora_poller import MI_LIGHT
        from miflora.miflora_poller import MI_TEMPERATURE
        from miflora.miflora_poller import MI_BATTERY

        return_dict = {
            'battery': {
                'percent': {}
            },
            'electrical_conductivity': {
                'μS_cm': {}
            },
            'light': {
                'lux': {}
            },
            'moisture': {
                'unitless': {}
            },
            'temperature': {
                'C': {}
            }
        }

        if self.is_enabled('battery', 'percent', 0):
            return_dict['battery']['percent'][0] = self.poller.parameter_value(MI_BATTERY)

        if self.is_enabled('electrical_conductivity', 'μS_cm', 0):
            return_dict['electrical_conductivity']['μS_cm'][0] = self.poller.parameter_value(MI_CONDUCTIVITY)

        if self.is_enabled('light', 'lux', 0):
            return_dict['light']['lux'][0] = self.poller.parameter_value(MI_LIGHT)

        if self.is_enabled('moisture', 'unitless', 0):
            return_dict['moisture']['unitless'][0] = self.poller.parameter_value(MI_MOISTURE)

        if self.is_enabled('temperature', 'C', 0):
            return_dict['temperature']['C'][0] = self.poller.parameter_value(MI_TEMPERATURE)

        return return_dict
