# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'battery',
        'unit': 'percent'
    },
    1: {
        'measurement': 'electrical_conductivity',
        'unit': 'uS_cm'
    },
    2: {
        'measurement': 'light',
        'unit': 'lux'
    },
    3: {
        'measurement': 'moisture',
        'unit': 'unitless'
    },
    4: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MIFLORA',
    'input_manufacturer': 'Xiaomi',
    'input_name': 'Miflora',
    'input_library': 'miflora',
    'measurements_name': 'EC/Light/Moisture/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'bt_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libglib2.0-dev', 'libglib2.0-dev'),
        ('pip-pypi', 'miflora', 'miflora'),
        ('pip-pypi', 'btlewrap', 'btlewrap'),
        ('pip-pypi', 'bluepy', 'bluepy'),
    ],

    'interfaces': ['BT'],
    'bt_location': '00:00:00:00:00:00',
    'bt_adapter': '0'
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the Miflora's electrical
    conductivity, moisture, temperature, and light.
    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        from miflora.miflora_poller import MiFloraPoller
        from btlewrap import BluepyBackend

        self.lock_file = '/var/lock/bluetooth_dev_hci{}'.format(self.input_dev.bt_adapter)
        self.sensor = MiFloraPoller(
            self.input_dev.location,
            BluepyBackend,
            adapter='hci{}'.format(self.input_dev.bt_adapter))

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        from miflora.miflora_poller import MI_CONDUCTIVITY
        from miflora.miflora_poller import MI_MOISTURE
        from miflora.miflora_poller import MI_LIGHT
        from miflora.miflora_poller import MI_TEMPERATURE
        from miflora.miflora_poller import MI_BATTERY

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.lock_acquire(self.lock_file, timeout=3600):
            try:
                if self.is_enabled(0):
                    self.value_set(0, self.sensor.parameter_value(MI_BATTERY))

                if self.is_enabled(1):
                    self.value_set(1, self.sensor.parameter_value(MI_CONDUCTIVITY))

                if self.is_enabled(2):
                    self.value_set(2, self.sensor.parameter_value(MI_LIGHT))

                if self.is_enabled(3):
                    self.value_set(3, self.sensor.parameter_value(MI_MOISTURE))

                if self.is_enabled(4):
                    self.value_set(4, self.sensor.parameter_value(MI_TEMPERATURE))

                return self.return_dict
            finally:
                self.lock_release(self.lock_file)
