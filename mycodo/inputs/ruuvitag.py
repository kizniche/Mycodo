# coding=utf-8
import copy
import subprocess
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.lockfile import LockFile
from mycodo.utils.system_pi import str_is_float

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
        'measurement': 'acceleration',
        'unit': 'g_force'
    },
    5: {
        'measurement': 'acceleration_x',
        'unit': 'g_force'
    },
    6: {
        'measurement': 'acceleration_y',
        'unit': 'g_force'
    },
    7: {
        'measurement': 'acceleration_z',
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
    'input_library': 'ruuvitag_sensor',
    'measurements_name': 'Acceleration/Humidity/Pressure/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://ruuvi.com/',
    'url_datasheet': 'https://ruuvi.com/files/ruuvitag-tech-spec-2019-7.pdf',

    'options_enabled': [
        'bt_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'psutil', 'psutil==5.9.0'),
        ('apt', 'bluez', 'bluez'),
        ('apt', 'bluez-hcidump', 'bluez-hcidump'),
        ('pip-pypi', 'ruuvitag_sensor', 'ruuvitag-sensor==2.0.0')
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
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.ruuvitag = None
        self.download_stored_data = None
        self.logging_interval_ms = None
        self.gadget = None
        self.connected = False
        self.connect_error = None
        self.device_information = {}
        self.initialized = False
        self.last_downloaded_timestamp = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        from ruuvitag_sensor.ruuvitag import RuuviTag

        self.ruuvitag = RuuviTag

        self.lock_file = '/var/lock/bluetooth_dev_hci{}'.format(self.input_dev.bt_adapter)
        self.location = self.input_dev.location
        self.bt_adapter = self.input_dev.bt_adapter
        self.sensor = self.ruuvitag(
            self.location,
            bt_device='hci{}'.format(self.bt_adapter))

    def get_measurement(self):
        """Obtain and return the measurements."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=3600):
            self.logger.debug("Starting measurement")
            try:
                cmd = 'timeout -k 11 10 /opt/Mycodo/env/bin/python ' \
                      '/opt/Mycodo/mycodo/inputs/scripts/ruuvitag_values.py ' \
                      '--mac_address {mac} --bt_adapter {bta}'.format(
                          mac=self.location, bta=self.bt_adapter)
                cmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                cmd_return, _ = cmd.communicate()
                cmd.wait()

                if not cmd_return:
                    self.logger.debug("Measurement command returned no data")
                    return

                values = cmd_return.decode('ascii').split(',')

                if not str_is_float(values[0]):
                    self.logger.debug("Error: Could not convert string to float: string '{}'".format(str(values[0])))
                    return

                temperature = float(str(values[0]))
                humidity = float(values[1])
                pressure = float(values[2])
                battery = float(values[3]) / 1000
                acceleration_g_force = float(values[4]) / 1000
                acceleration_x_g_force = float(values[5]) / 1000
                acceleration_y_g_force = float(values[6]) / 1000
                acceleration_z_g_force = float(values[7]) / 1000

                if battery < 1 or battery > 4:
                    self.logger.debug(
                        "Not recording measurements: "
                        "Battery outside expected range (1 < battery volts < 4): {bat}".format(bat=battery))
                    return

                if self.is_enabled(0):
                    self.value_set(0, temperature)

                if self.is_enabled(1):
                    self.value_set(1, humidity)

                if self.is_enabled(2):
                    self.value_set(2, pressure)

                if self.is_enabled(3):
                    self.value_set(3, battery)

                if self.is_enabled(4):
                    self.value_set(4, acceleration_g_force)

                if self.is_enabled(5):
                    self.value_set(5, acceleration_x_g_force)

                if self.is_enabled(6):
                    self.value_set(6, acceleration_y_g_force)

                if self.is_enabled(7):
                    self.value_set(7, acceleration_z_g_force)

                if (self.is_enabled(8) and
                        self.is_enabled(0) and
                        self.is_enabled(1)):
                    self.value_set(8, calculate_dewpoint(
                        self.value_get(0), self.value_get(1)))

                if (self.is_enabled(9) and
                        self.is_enabled(0) and
                        self.is_enabled(1)):
                    self.value_set(9, calculate_vapor_pressure_deficit(
                        self.value_get(0), self.value_get(1)))

                self.logger.debug("Completed measurement")
                return self.return_dict

            except Exception as msg:
                self.logger.debug("Error: {}".format(msg))

            finally:
                lf.lock_release(self.lock_file)
                time.sleep(1)
