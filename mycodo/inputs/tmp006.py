# coding=utf-8
import logging

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Object'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'Die'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TMP006',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'TMP006',
    'measurements_name': 'Temperature (Object/Die)',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_TMP', 'Adafruit_TMP')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x40',
        '0x41',
        '0x42',
        '0x43',
        '0x44',
        '0x45',
        '0x46',
        '0x47'
    ],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TMP006's die and object temperatures """

    def __init__(self, input_dev,  testing=False):
        super(InputModule, self).__init__()
        self.setup_logger()
        self._temperature_die = None
        self._temperature_object = None

        if not testing:
            from Adafruit_TMP import TMP006

            self.setup_logger(
                name=__name__, log_id=input_dev.unique_id.split('-')[0])

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = TMP006.TMP006(
                address=self.i2c_address,
                busnum=self.i2c_bus)

            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the TMP006's temperature in Celsius """
        self.return_dict = measurements_dict.copy()

        self.sensor.begin()

        if self.is_enabled(0):
            self.set_value(0, self.sensor.readObjTempC())

        if self.is_enabled(1):
            self.set_value(1, self.sensor.readDieTempC())

        return self.return_dict
