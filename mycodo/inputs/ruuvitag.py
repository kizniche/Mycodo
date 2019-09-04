# coding=utf-8
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

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
        ('apt', 'python3-dev', 'python3-dev'),
        ('apt', 'python3-psutil', 'python3-psutil'),
        ('apt', 'bluez', 'bluez'),
        ('apt', 'bluez-hcidump', 'bluez-hcidump'),
        ('pip-pypi', 'ruuvitag_sensor', 'ruuvitag_sensor'),
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.download_stored_data = None
        self.logging_interval_ms = None
        self.gadget = None
        self.connected = False
        self.connect_error = None
        self.device_information = {}
        self.initialized = False
        self.last_downloaded_timestamp = None

        if not testing:
            from ruuvitag_sensor.ruuvitag import RuuviTag
            self.ruuvitag = RuuviTag

            self.lock_file = '/var/lock/bluetooth_dev_hci{}'.format(
                input_dev.bt_adapter)
            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter
            self.sensor = self.ruuvitag(
                self.location,
                bt_device='hci{}'.format(self.bt_adapter))

    def get_measurement(self):
        """ Obtain and return the measurements """
        self.return_dict = measurements_dict.copy()

        self.lock_acquire(self.lock_file, timeout=3600)
        if self.locked:
            self.logger.debug("Starting measurement")
            try:
                state = self.sensor.update()
                state = self.sensor.state

                if not state:
                    self.logger.debug("Measurement command returned no data")
                    return

                battery_volts = state['battery'] / 1000
                if battery_volts < 1 or battery_volts > 4:
                    self.logger.debug(
                        "Not recording measurements: "
                        "Battery outside expected range (1 < volts < 4): "
                        "{volts}".format(volts=battery_volts))
                    return

                if self.is_enabled(0):
                    self.value_set(0, state['temperature'])

                if self.is_enabled(1):
                    self.value_set(1, state['humidity'])

                if self.is_enabled(2):
                    self.value_set(2, state['pressure'])

                if self.is_enabled(3):
                    self.value_set(3, state['battery'] / 1000)

                if self.is_enabled(4):
                    self.value_set(4, state['acceleration'] / 1000)

                if self.is_enabled(5):
                    self.value_set(5, state['acceleration_x'] / 1000)

                if self.is_enabled(6):
                    self.value_set(6, state['acceleration_y'] / 1000)

                if self.is_enabled(7):
                    self.value_set(7, state['acceleration_z'] / 1000)

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
                self.lock_release(self.lock_file)
                time.sleep(1)
