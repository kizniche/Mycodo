# coding=utf-8
import logging

from mycodo.databases.models import InputMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = {
    0: {
        'measurement': 'light',
        'unit': 'full'
    },
    1: {
        'measurement': 'light',
        'unit': 'ir'
    },
    2: {
        'measurement': 'light',
        'unit': 'lux'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TSL2591',
    'input_manufacturer': 'TAOS',
    'input_name': 'TSL2591',
    'measurements_name': 'Light',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-git', 'tsl2591', 'git://github.com/maxlklaxl/python-tsl2591.git#egg=tsl2591')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x29'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TSL2591's lux """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tsl2591_sensor")
        self._measurements = None

        if not testing:
            import tsl2591
            self.logger = logging.getLogger(
                "mycodo.tsl2591_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.tsl = tsl2591.Tsl2591(i2c_bus=self.i2c_bus,
                                       sensor_address=self.i2c_address)

    def get_measurement(self):
        """ Gets the TSL2591's lux """
        return_dict = measurements_dict.copy()

        full, ir = self.tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)

        if self.is_enabled(0):
            return_dict[0]['value'] = full

        if self.is_enabled(1):
            return_dict[1]['value'] = ir

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            return_dict[2]['value'] = self.tsl.calculate_lux(
                return_dict[0]['value'], return_dict[1]['value'])

        return return_dict
