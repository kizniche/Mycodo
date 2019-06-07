# coding=utf-8
from mycodo.inputs.base_input import AbstractInput

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
        'pre_output',
        'log_level_debug'
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            import tsl2591

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.tsl = tsl2591.Tsl2591(
                i2c_bus=self.i2c_bus,
                sensor_address=self.i2c_address)

    def get_measurement(self):
        """ Gets the TSL2591's lux """
        self.return_dict = measurements_dict.copy()

        full, ir = self.tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)

        if self.is_enabled(0):
            self.value_set(0, full)

        if self.is_enabled(1):
            self.value_set(1, ir)

        if (self.is_enabled(2) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            self.value_set(2, self.tsl.calculate_lux(
                self.value_get(0), self.value_get(1)))

        return self.return_dict
