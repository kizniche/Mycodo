# coding=utf-8
import datetime
import logging
import time

from flask_babel import lazy_gettext

from mycodo.utils.influx import parse_measurement
from mycodo.utils.influx import write_influxdb_value
from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit
from mycodo.utils.database import db_retrieve_table_daemon


def constraints_pass_positive_value(value):
    """
    Check if the user input is acceptable
    :param value: float
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors


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
    'measurements_name': 'Humidity/Temperature',
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
        ('pip-pypi', 'bluepy', 'bluepy')
    ],

    'interfaces': ['BT'],
    'bt_location': '00:00:00:00:00:00',
    'bt_adapter': '0',

    'custom_options': [
        {
            'id': 'download_stored_data',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('Download Stored Data'),
            'phrase': lazy_gettext('Download the data logged to the device.')
        },
        {
            'id': 'logging_interval',
            'type': 'integer',
            'default_value': 600,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Set Logging Interval'),
            'phrase': lazy_gettext('Set the logging interval (seconds) the device will store measurements on its internal memory.')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A support class for Sensorion's SHT31 Smart Gadget

    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.sht31_smart_gadget")
        self.unique_id = input_dev.unique_id
        self._measurements = None
        self.download_stored_data = None
        self.logging_interval = None
        self.gadget = None

        if not testing:
            from mycodo.devices.sht31_smart_gadget import SHT31
            from bluepy import btle
            self.logger = logging.getLogger(
                "mycodo.sht31_smart_gadget_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'download_stored_data':
                        self.download_stored_data = bool(value)
                    elif option == 'logging_interval':
                        self.logging_interval = int(value)

            self.SHT31 = SHT31
            self.btle = btle
            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter

    def get_measurement(self):
        """ Obtain and return the measurements """
        return_dict = measurements_dict.copy()

        # Make three attempts to connect
        connected = False
        connect_error = None
        for _ in range(3):
            try:
                self.gadget = self.SHT31(addr=self.location,
                                         iface=self.bt_adapter)
                connected = True
                break
            except self.btle.BTLEException as e:
                connect_error = e
            time.sleep(0.5)

        if connected:
            if self.is_enabled(0):
                return_dict[0]['value'] = self.gadget.readTemperature()

            if self.is_enabled(1):
                return_dict[1]['value'] = self.gadget.readHumidity()

            if self.is_enabled(2):
                return_dict[2]['value'] = self.gadget.readBattery()

            if (self.is_enabled(3) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                return_dict[3]['value'] = calculate_dewpoint(
                    return_dict[0]['value'], return_dict[1]['value'])

            if (self.is_enabled(4) and
                    self.is_enabled(0) and
                    self.is_enabled(1)):
                return_dict[4]['value'] = calculate_vapor_pressure_deficit(
                    return_dict[0]['value'], return_dict[1]['value'])

            if self.download_stored_data:

                # Download stored data from the device
                self.gadget.readLoggedDataInterval()
                while True:
                    if (not self.gadget.waitForNotifications(5) or
                            not self.gadget.isLogReadoutInProgress()):
                        break  # Done reading data

                # Store logged temperatures
                measurement = self.device_measurements.filter(DeviceMeasurements.channel == 0).first()
                conversion = db_retrieve_table_daemon(Conversion, unique_id=measurement.conversion_id)
                for each_time, each_measure in self.gadget.loggedData['Temp'].items():
                    measurement_single = {
                        0: {
                            'measurement': 'temperature',
                            'unit': 'C',
                            'value': each_measure
                        }
                    }
                    measurement_single = parse_measurement(
                        conversion,
                        measurement,
                        measurement_single,
                        measurement.channel,
                        measurement_single[0])
                    write_influxdb_value(
                        self.unique_id,
                        measurement_single[0]['unit'],
                        value=measurement_single[0]['value'],
                        measure=measurement_single[0]['measurement'],
                        channel=0,
                        timestamp=datetime.datetime.utcfromtimestamp(each_time / 1000))

                # Store logged humidities
                measurement = self.device_measurements.filter(DeviceMeasurements.channel == 1).first()
                conversion = db_retrieve_table_daemon(Conversion, unique_id=measurement.conversion_id)
                for each_time, each_measure in self.gadget.loggedData['Humi'].items():
                    measurement_single = {
                        1: {
                            'measurement': 'humidity',
                            'unit': 'percent',
                            'value': each_measure
                        }
                    }
                    measurement_single = parse_measurement(
                        conversion,
                        measurement,
                        measurement_single,
                        measurement.channel,
                        measurement_single[1])
                    write_influxdb_value(
                        self.unique_id,
                        measurement_single[1]['unit'],
                        value=measurement_single[1]['value'],
                        measure=measurement_single[1]['measurement'],
                        channel=1,
                        timestamp=datetime.datetime.utcfromtimestamp(each_time / 1000))

                # Reset log and set logging interval
                self.gadget.setLoggerIntervalMs(self.logging_interval * 1000)

            self.gadget.disconnect()

            return return_dict
        else:
            self.logger.error("Could not connect: {}".format(connect_error))
