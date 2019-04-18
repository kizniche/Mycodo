# coding=utf-8
import logging

import os

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
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
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    3: {
        'measurement': 'battery',
        'unit': 'V'
    },
    4: {
        'measurement': 'acceleration_g_force',
        'unit': 'g_force'
    },
    5: {
        'measurement': 'acceleration_x_g_force',
        'unit': 'g_force'
    },
    6: {
        'measurement': 'acceleration_y_g_force',
        'unit': 'g_force'
    },
    7: {
        'measurement': 'acceleration_z_g_force',
        'unit': 'g_force'
    },
    8: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    9: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'RUUVITAG',
    'input_manufacturer': 'Ruuvi',
    'input_name': 'RuuviTag',
    'measurements_name': 'Acceleration/Humidity/Pressure/Temperature',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'bt_location',
        'measurements_select',
        'custom_options',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'locket', 'locket'),
        ('apt', 'python3-dev', 'python3-dev'),
        ('apt', 'python3-psutil', 'python3-psutil'),
        ('pip-pypi', 'bleson', 'bleson'),
        ('pip-pypi', 'ruuvitag_sensor', 'git+https://github.com/ttu/ruuvitag-sensor.git@bleson-ble-communication'),
    ],

    'interfaces': ['BT'],
    'bt_location': '00:00:00:00:00:00',
    'bt_adapter': '0',
}


class InputModule(AbstractInput):
    """
    A support class for the RuuviTag

    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.ruuvitag")
        self.running = True
        self.unique_id = input_dev.unique_id
        self._measurements = None
        self.download_stored_data = None
        self.logging_interval_ms = None
        self.gadget = None
        self.connected = False
        self.connect_error = None
        self.device_information = {}
        self.initialized = False
        self.last_downloaded_timestamp = None

        if not testing:
            import locket
            self.logger = logging.getLogger(
                "mycodo.ruuvitag_{id}".format(
                    id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.locket = locket
            self.lock_file_bluetooth = '/var/lock/bluetooth_dev_hci{}'.format(input_dev.bt_adapter)
            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter

    def get_measurement(self):
        """ Obtain and return the measurements """
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
            from mycodo.utils.system_pi import cmd_output
            cmd = '/var/mycodo-root/env/bin/python ' \
                  '/var/mycodo-root/mycodo/inputs/scripts/ruuvitag_values.py ' \
                  '--mac_address {mac} --bt_adapter {bta}'.format(
                    mac=self.location, bta=self.bt_adapter)
            cmd_return, _, cmd_status = cmd_output(cmd)

            values = cmd_return.decode('ascii').split(',')

            if self.is_enabled(0):
                return_dict[0]['value'] = float(str(values[0]))

            if self.is_enabled(1):
                return_dict[1]['value'] = float(values[1])

            if self.is_enabled(2):
                return_dict[2]['value'] = float(values[2])

            if self.is_enabled(3):
                return_dict[3]['value'] = float(values[3]) / 1000

            if self.is_enabled(4):
                return_dict[4]['value'] = float(values[4]) / 1000

            if self.is_enabled(5):
                return_dict[5]['value'] = float(values[5]) / 1000

            if self.is_enabled(6):
                return_dict[6]['value'] = float(values[6]) / 1000

            if self.is_enabled(7):
                return_dict[7]['value'] = float(values[7]) / 1000

            if (self.is_enabled(8) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                return_dict[8]['value'] = calculate_dewpoint(
                    return_dict[0]['value'], return_dict[1]['value'])

            if (self.is_enabled(9) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                return_dict[9]['value'] = calculate_vapor_pressure_deficit(
                    return_dict[0]['value'], return_dict[1]['value'])

        lock.release()
        os.remove(self.lock_file_bluetooth)

        return return_dict
