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
        'pre_output',
        'log_level_debug'
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
        self.setup_logger(testing=testing, name=__name__, input_dev=input_dev)
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

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.locket = locket
            self.lock_file_bluetooth = '/var/lock/bluetooth_dev_hci{}'.format(input_dev.bt_adapter)
            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter

    def get_measurement(self):
        """ Obtain and return the measurements """
        self.return_dict = measurements_dict.copy()
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

            try:
                test = float(str(values[0]))
            except ValueError:
                self.logger.debug("Could not convert string to float: string '{}'".format(str(values[0])))

            if self.is_enabled(0):
                self.set_value(0, float(str(values[0])))

            if self.is_enabled(1):
                self.set_value(1, float(values[1]))

            if self.is_enabled(2):
                self.set_value(2, float(values[2]))

            if self.is_enabled(3):
                self.set_value(3, float(values[3]) / 1000)

            if self.is_enabled(4):
                self.set_value(4, float(values[4]) / 1000)

            if self.is_enabled(5):
                self.set_value(5, float(values[5]) / 1000)

            if self.is_enabled(6):
                self.set_value(6, float(values[6]) / 1000)

            if self.is_enabled(7):
                self.set_value(7, float(values[7]) / 1000)

            if (self.is_enabled(8) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                self.set_value(8, calculate_dewpoint(
                    self.get_value(0), self.get_value(1)))

            if (self.is_enabled(9) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                self.set_value(9, calculate_vapor_pressure_deficit(
                    self.get_value(0), self.get_value(1)))

        lock.release()
        os.remove(self.lock_file_bluetooth)

        return self.return_dict
