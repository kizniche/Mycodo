# coding=utf-8
import logging
from collections import OrderedDict

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

# Measurements
measurements_dict = OrderedDict()
for each_channel in range(4):
    measurements_dict[each_channel] = {
        'measurement': 'electrical_potential',
        'unit': 'V'
    }

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ADS1x15',
    'input_manufacturer': 'Texas Instruments',
    'input_name': 'ADS1x15',
    'measurements_name': 'Voltage (Analog-to-Digital Converter)',
    'measurements_dict': measurements_dict,
    'measurements_rescale': True,
    'scale_from_min': -4.096,
    'scale_from_max': 4.096,

    'options_enabled': [
        'measurements_select',
        'channels_convert',
        'adc_gain',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface', 'i2c_location'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-pypi', 'Adafruit_ADS1x15', 'Adafruit_ADS1x15')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49', '0x4A', '0x4B'],
    'i2c_address_editable': False,

    'adc_gain': [(1, '1'),
                 (2, '2'),
                 (3, '3'),
                 (4, '4'),
                 (8, '8'),
                 (16, '16')]
}


class InputModule(AbstractInput):
    """ Read ADC

        Choose a gain of 1 for reading measurements from 0 to 4.09V.
        Or pick a different gain to change the range of measurements that are read:
         - 2/3 = +/-6.144V
         -   1 = +/-4.096V
         -   2 = +/-2.048V
         -   4 = +/-1.024V
         -   8 = +/-0.512V
         -  16 = +/-0.
        See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
        """
    def __init__(self, input_dev, testing=False, run_main=False):
        super(InputModule, self).__init__()
        self.setup_logger(testing=testing, name=__name__, input_dev=input_dev)
        self.run_main = run_main

        if not testing:
            import Adafruit_ADS1x15

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.adc_gain = input_dev.adc_gain
            self.adc = Adafruit_ADS1x15.ADS1115(
                address=self.i2c_address,
                busnum=self.i2c_bus)

        self.running = True

    def get_measurement(self):
        self.return_dict = measurements_dict.copy()

        for each_measure in self.device_measurements.all():
            if each_measure.is_enabled:
                self.set_value(
                    each_measure.channel,
                    self.adc.read_adc(each_measure.channel,
                                      gain=self.adc_gain) / 10000.0)

        return self.return_dict


if __name__ == "__main__":
    from types import SimpleNamespace
    settings = SimpleNamespace()
    settings.id = 1
    settings.unique_id = '0000-0000'
    settings.i2c_location = '0x48'
    settings.i2c_bus = 1
    settings.adc_gain = 1
    settings.channels = 4
    settings.run_main = True

    measurements = InputModule(settings, run_main=True).next()
    print("Measurements: {}".format(measurements))
