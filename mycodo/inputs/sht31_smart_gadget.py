# coding=utf-8
import datetime
import time

import copy

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.influx import parse_measurement
from mycodo.utils.influx import write_influxdb_value


def constraints_pass_logging_interval(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")

    # Ensure logging interval and period options don't cause measurements to exceed device memory
    measurements_can_be_stored = 16512  # The memory of the device only permits 16512 measurements to be stored
    measurements_per_period = int(mod_input.period / value)
    if measurements_per_period > measurements_can_be_stored:
        all_passed = False
        errors.append(
            "Number of calculated measurements exceeds device memory: With a "
            "Logging Interval of {li} seconds and a download period of {per} "
            "seconds, {meas_t} measurements will be conducted, however, only "
            "{meas_a} measurements can be stored on the device. Either "
            "increase your Logging Interval or decrease the Input Period.".format(
                li=value,
                per=mod_input.period,
                meas_t=measurements_per_period,
                meas_a=measurements_can_be_stored))
    return all_passed, errors, mod_input


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
        'measurement': 'battery',
        'unit': 'percent'
    },
    3: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    4: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SHT31_SMART_GADGET',
    'input_manufacturer': 'Sensorion',
    'input_name': 'SHT31 Smart Gadget',
    'input_library': 'bluepy',
    'measurements_name': 'Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sensirion.com/en/environmental-sensors/humidity-sensors/development-kit/',

    'options_enabled': [
        'bt_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'pi-bluetooth', 'pi-bluetooth'),
        ('apt', 'libglib2.0-dev', 'libglib2.0-dev'),
        ('pip-pypi', 'bluepy', 'bluepy==1.3.0')

    ],

    'interfaces': ['BT'],
    'bt_location': '00:00:00:00:00:00',
    'bt_adapter': '0',

    'custom_options': [
        {
            'id': 'download_stored_data',
            'type': 'bool',
            'default_value': True,
            'name': 'Download Stored Data',
            'phrase': 'Download the data logged to the device.'
        },
        {
            'id': 'logging_interval',
            'type': 'integer',
            'default_value': 600,
            'required': True,
            'constraints_pass': constraints_pass_logging_interval,
            'name': 'Set Logging Interval',
            'phrase': 'Set the logging interval (seconds) the device will store measurements on its internal memory.'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A support class for Sensorion's SHT31 Smart Gadget
    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.gadget = None
        self.connected = False
        self.connect_error = None
        self.device_information = {}
        self.initialized = False
        self.last_downloaded_timestamp = None

        self.download_stored_data = None
        self.logging_interval_ms = None
        self.logging_interval = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        from mycodo.devices.sht31_smart_gadget import SHT31
        from bluepy import btle

        self.SHT31 = SHT31
        self.btle = btle

        self.logging_interval_ms = self.logging_interval * 1000
        self.log_level_debug = self.input_dev.log_level_debug
        self.location = self.input_dev.location
        self.bt_adapter = self.input_dev.bt_adapter
        self.lock_file = '/var/lock/bluetooth_dev_hci{}'.format(self.bt_adapter)

    def initialize(self):
        """Initialize the device by obtaining sensor information"""
        self.logger.debug("Input Initializing (Initialized: {})".format(self.initialized))

        if not self.initialized:
            for _ in range(3):
                if not self.running:
                    break
                try:
                    self.gadget = self.SHT31(
                        addr=self.location,
                        iface=self.bt_adapter,
                        debug=self.log_level_debug)
                    self.connected = True
                    break
                except self.btle.BTLEException as e:
                    self.connect_error = e
                time.sleep(0.1)

            if self.connect_error:
                self.logger.error("Initialize Error: {}".format(self.connect_error))

        if self.connected:
            # Fill device information dictionary
            self.device_information['manufacturer'] = self.gadget.readManufacturerNameString()
            self.device_information['model'] = self.gadget.readModelNumberString()
            self.device_information['serial_number'] = self.gadget.readSerialNumberString()
            self.device_information['device_name'] = self.gadget.readDeviceName()
            self.device_information['firmware_revision'] = self.gadget.readFirmwareRevisionString()
            self.device_information['hardware_revision'] = self.gadget.readHardwareRevisionString()
            self.device_information['software_revision'] = self.gadget.readSoftwareRevisionString()
            self.device_information['logger_interval_ms'] = self.gadget.readLoggerIntervalMs()
            self.device_information['info_timestamp'] = int(time.time() * 1000)
            self.logger.info(
                "{man}, {mod}, SN: {sn}, Name: {name}, Firmware: {fw}, "
                "Hardware: {hw}, Software: {sw}, Log Interval: {sec} sec".format(
                    man=self.device_information['manufacturer'],
                    mod=self.device_information['model'],
                    sn=self.device_information['serial_number'],
                    name=self.device_information['device_name'],
                    fw=self.device_information['firmware_revision'],
                    hw=self.device_information['hardware_revision'],
                    sw=self.device_information['software_revision'],
                    sec=self.device_information['logger_interval_ms'] / 1000))
            self.initialized = True

    def connect(self):
        # Make three attempts to connect
        self.logger.debug("Connecting")
        for _ in range(3):
            if not self.running:
                break
            try:
                self.gadget.connect(addr=self.location, iface=self.bt_adapter)
                self.connected = True
                self.connect_error = None
                self.logger.debug("Connected")
                break
            except self.btle.BTLEException as e:
                self.connect_error = e
            time.sleep(0.1)

        if not self.connected:
            self.logger.error("Could not connect: {}".format(self.connect_error))

    def disconnect(self):
        try:
            self.logger.debug("Disconnecting")
            self.gadget.disconnect()
            self.logger.debug("Disconnected")
        except self.btle.BTLEException as e:
            self.logger.error("Disconnect Error: {}".format(e))
        except Exception:
            self.logger.exception("Disconnecting")
        finally:
            self.connected = False

    def download_data(self):
        self.logger.debug("Downloading Data")
        # Clear data previously stored in dictionary
        self.gadget.loggedDataReadout = {'Temp': {}, 'Humi': {}}

        # Download stored data starting from self.gadget.newestTimeStampMs
        self.gadget.readLoggedDataInterval(
            startMs=self.gadget.newestTimeStampMs)

        while self.running:
            if (not self.gadget.waitForNotifications(5) or
                    not self.gadget.isLogReadoutInProgress()):
                break  # Done reading data

        self.logger.debug("Downloaded Data")
        self.logger.debug("Parsing/saving data")

        list_timestamps_temp = []
        list_timestamps_humi = []

        # Store logged temperature
        self.logger.debug("Storing {} temperatures".format(len(self.gadget.loggedDataReadout['Temp'])))
        for each_ts, each_measure in self.gadget.loggedDataReadout['Temp'].items():
            if not self.running:
                break

            if -40 > each_measure or each_measure > 125:
                continue  # Temperature outside acceptable range
            list_timestamps_temp.append(each_ts)

            if self.is_enabled(0):
                datetime_ts = datetime.datetime.utcfromtimestamp(each_ts / 1000)
                measurement_single = {
                    0: {
                        'measurement': 'temperature',
                        'unit': 'C',
                        'value': each_measure
                    }
                }
                measurement_single = parse_measurement(
                    self.channels_conversion[0],
                    self.channels_measurement[0],
                    measurement_single,
                    self.channels_measurement[0].channel,
                    measurement_single[0])
                write_influxdb_value(
                    self.unique_id,
                    measurement_single[0]['unit'],
                    value=measurement_single[0]['value'],
                    measure=measurement_single[0]['measurement'],
                    channel=0,
                    timestamp=datetime_ts)

        # Store logged humidity
        self.logger.debug("Storing {} humidities".format(len(self.gadget.loggedDataReadout['Humi'])))
        for each_ts, each_measure in self.gadget.loggedDataReadout['Humi'].items():
            if not self.running:
                break

            if 0 >= each_measure or each_measure > 100:
                continue  # Humidity outside acceptable range
            list_timestamps_humi.append(each_ts)

            if self.is_enabled(1):
                datetime_ts = datetime.datetime.utcfromtimestamp(each_ts / 1000)
                measurement_single = {
                    1: {
                        'measurement': 'humidity',
                        'unit': 'percent',
                        'value': each_measure
                    }
                }
                measurement_single = parse_measurement(
                    self.channels_conversion[1],
                    self.channels_measurement[1],
                    measurement_single,
                    self.channels_measurement[1].channel,
                    measurement_single[1])
                write_influxdb_value(
                    self.unique_id,
                    measurement_single[1]['unit'],
                    value=measurement_single[1]['value'],
                    measure=measurement_single[1]['measurement'],
                    channel=1,
                    timestamp=datetime_ts)

        # Find common timestamps from both temperature and humidity lists
        list_timestamps_both = list(set(list_timestamps_temp).intersection(list_timestamps_humi))

        self.logger.debug("Calculating/storing {} dewpoint and vpd".format(len(list_timestamps_both)))
        for each_ts in list_timestamps_both:
            if not self.running:
                break

            temperature = self.gadget.loggedDataReadout['Temp'][each_ts]
            humidity = self.gadget.loggedDataReadout['Humi'][each_ts]

            if (-200 > temperature or temperature > 200) or (0 > humidity or humidity > 100):
                continue  # Measurement outside acceptable range

            datetime_ts = datetime.datetime.utcfromtimestamp(each_ts / 1000)
            # Calculate and store dew point
            if self.is_enabled(3) and self.is_enabled(0) and self.is_enabled(1):
                dewpoint = calculate_dewpoint(temperature, humidity)
                measurement_single = {
                    3: {
                        'measurement': 'dewpoint',
                        'unit': 'C',
                        'value': dewpoint
                    }
                }
                measurement_single = parse_measurement(
                    self.channels_conversion[3],
                    self.channels_measurement[3],
                    measurement_single,
                    self.channels_measurement[3].channel,
                    measurement_single[3])
                write_influxdb_value(
                    self.unique_id,
                    measurement_single[3]['unit'],
                    value=measurement_single[3]['value'],
                    measure=measurement_single[3]['measurement'],
                    channel=3,
                    timestamp=datetime_ts)

            # Calculate and store vapor pressure deficit
            if self.is_enabled(4) and self.is_enabled(0) and self.is_enabled(1):
                vpd = calculate_vapor_pressure_deficit(temperature, humidity)
                measurement_single = {
                    4: {
                        'measurement': 'vapor_pressure_deficit',
                        'unit': 'Pa',
                        'value': vpd
                    }
                }
                measurement_single = parse_measurement(
                    self.channels_conversion[4],
                    self.channels_measurement[4],
                    measurement_single,
                    self.channels_measurement[4].channel,
                    measurement_single[4])
                write_influxdb_value(
                    self.unique_id,
                    measurement_single[4]['unit'],
                    value=measurement_single[4]['value'],
                    measure=measurement_single[4]['measurement'],
                    channel=4,
                    timestamp=datetime_ts)

        # Download successfully finished, set newest timestamp
        self.gadget.newestTimeStampMs = self.gadget.tmp_newestTimeStampMs
        self.logger.debug("Parsed/saved data")

    def get_device_information(self):
        if not self.initialized:
            self.initialize()

        if 'info_timestamp' in self.device_information:
            return self.device_information

    def get_measurement(self):
        """ Obtain and return the measurements """
        self.return_dict = copy.deepcopy(measurements_dict)

        if self.lock_acquire(self.lock_file, timeout=3600):
            self.logger.debug("Starting measurement")
            try:
                if not self.initialized:
                    self.initialize()

                if not self.initialized:
                    self.logger.error("Count not initialize sensor.")

                if self.initialized and not self.connected:
                    self.connect()

                if not self.connected:
                    self.logger.error("Count not connect to sensor.")

                if self.connected:
                    try:
                        # Download stored data
                        if self.download_stored_data:
                            self.download_data()
                            if not self.running:
                                return

                        # Set logging interval if not already set
                        if ('logger_interval_ms' in self.device_information
                                and self.logging_interval_ms != self.device_information['logger_interval_ms']):
                            self.set_logging_interval()

                        self.logger.debug("Acquiring present measurements")
                        # Get battery percent charge
                        if self.is_enabled(2):
                            self.value_set(2, self.gadget.readBattery())

                        # Get temperature and humidity last so their timestamp in the
                        # database will be the most accurate
                        if self.is_enabled(0):
                            self.value_set(0, self.gadget.readTemperature())

                        if self.is_enabled(1):
                            self.value_set(1, self.gadget.readHumidity())
                        self.logger.debug("Acquired present measurements")
                    except self.btle.BTLEDisconnectError:
                        self.logger.error("Disconnected")
                        return
                    except Exception:
                        self.logger.exception("Unknown Error")
                        return
                    finally:
                        self.disconnect()

                    if (self.is_enabled(3) and
                            self.is_enabled(0) and
                            self.is_enabled(1)):
                        self.value_set(3, calculate_dewpoint(
                            self.value_get(0), self.value_get(1)))

                    if (self.is_enabled(4) and
                            self.is_enabled(0) and
                            self.is_enabled(1)):
                        self.value_set(4, calculate_vapor_pressure_deficit(
                            self.value_get(0), self.value_get(1)))

                    self.logger.debug("Completed measurement")
                    return self.return_dict
                else:
                    self.logger.debug("Not connected: Not measuring")
            finally:
                self.lock_release(self.lock_file)
                time.sleep(1)

    def set_logging_interval(self):
        """Set logging interval (resets memory; set after downloading data)"""
        if not self.connected:
            self.connect()

        if self.connected:
            self.logger.debug("Setting Interval")
            self.gadget.setLoggerIntervalMs(self.logging_interval_ms)
            self.device_information['logger_interval_ms'] = self.logging_interval_ms
            self.logger.info("Set log interval: {} sec".format(self.logging_interval_ms / 1000))
