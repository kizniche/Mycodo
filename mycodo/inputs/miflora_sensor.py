# coding=utf-8
import logging
import os

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

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
        ('pip-pypi', 'locket', 'locket'),
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
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.miflora")

        if not testing:
            from miflora.miflora_poller import MiFloraPoller
            from btlewrap import BluepyBackend
            import locket
            self.logger = logging.getLogger(
                "mycodo.miflora_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.locket = locket
            self.lock_file_bluetooth = '/var/lock/bluetooth_dev_hci{}'.format(input_dev.bt_adapter)
            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter
            self.poller = MiFloraPoller(self.location, BluepyBackend, adapter='hci{}'.format(self.bt_adapter))

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        from miflora.miflora_poller import MI_CONDUCTIVITY
        from miflora.miflora_poller import MI_MOISTURE
        from miflora.miflora_poller import MI_LIGHT
        from miflora.miflora_poller import MI_TEMPERATURE
        from miflora.miflora_poller import MI_BATTERY

        return_dict = measurements_dict.copy()
        lock_acquired = False

        # Set up lock
        lock = self.locket.lock_file(self.lock_file_bluetooth, timeout=1200)
        try:
            lock.acquire()
            lock_acquired = True
        except:
            self.logger.error("Could not acquire lock. Breaking for future locking.")
            os.remove(self.lock_file_bluetooth)

        if lock_acquired:
            if self.is_enabled(0):
                return_dict[0]['value'] = self.poller.parameter_value(MI_BATTERY)

            if self.is_enabled(1):
                return_dict[1]['value'] = self.poller.parameter_value(MI_CONDUCTIVITY)

            if self.is_enabled(2):
                return_dict[2]['value'] = self.poller.parameter_value(MI_LIGHT)

            if self.is_enabled(3):
                return_dict[3]['value'] = self.poller.parameter_value(MI_MOISTURE)

            if self.is_enabled(4):
                return_dict[4]['value'] = self.poller.parameter_value(MI_TEMPERATURE)

            lock.release()

        os.remove(self.lock_file_bluetooth)

        return return_dict
